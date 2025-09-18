"""
API - Gestion de la base SQLite
Fonctions pour récupérer et sauvegarder les données de scraping
"""

import sqlite3
import json
import logging
import time
import threading
import platform
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Détermine le chemin de la base de données selon l'environnement"""
    import os
    # Vérifier si on est sur le VPS par la présence d'un fichier spécifique
    vps_detected = os.path.exists("/home/ubuntu")
    logger.info(f"🔍 Détection environnement: /home/ubuntu existe = {vps_detected}")
    
    if vps_detected:
        # VPS Linux
        db_path = "../trendtrack-scraper-final/data/trendtrack.db"
        logger.info(f"🌐 VPS détecté - Chemin relatif: {db_path}")
        return db_path
    else:
        # macOS local
        db_path = "/Users/infusion/Desktop/trendtrack-scrapper/data/trendtrack.db"
        logger.info(f"🍎 macOS détecté - Chemin absolu: {db_path}")
        return db_path

class TrendTrackAPI:
    """API pour interagir avec la base de données"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
        self._initialize_database()
    
    def _get_connection(self):
        """Obtenir une connexion à la base de données (poolée)"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            # Optimisations pour les performances
            self._connection.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            self._connection.execute("PRAGMA synchronous=NORMAL")  # Moins de synchronisation
            self._connection.execute("PRAGMA cache_size=10000")  # Cache plus grand
            self._connection.execute("PRAGMA temp_store=MEMORY")  # Tables temporaires en mémoire
            logger.info("✅ Connexion DB optimisée créée")
        return self._connection
    
    def _close_connection(self):
        """Fermer la connexion à la base de données"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("🔒 Connexion DB fermée")
    
    def _initialize_database(self):
        """Initialiser la base de données avec les index optimisés"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Créer les tables si elles n'existent pas
            logger.info("🔧 Création des tables...")
            
            # Table des boutiques
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_name TEXT,
                    shop_url TEXT UNIQUE NOT NULL,
                    scraping_status TEXT,
                    scraping_last_update TIMESTAMP,
                    created_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                    updated_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat()
                )
            """)
            
            # Table des analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    organic_traffic TEXT,
                    bounce_rate TEXT,
                    avg_visit_duration TEXT,
                    branded_traffic TEXT,
                    conversion_rate TEXT,
                    scraping_status TEXT DEFAULT 'completed',
                    updated_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                    FOREIGN KEY (shop_id) REFERENCES shops (id)
                )
            """)
            
            # Table des erreurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER,
                    error_message TEXT,
                    occurred_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                    FOREIGN KEY (shop_id) REFERENCES shops (id)
                )
            """)
            
            # Table des locks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_name TEXT UNIQUE NOT NULL,
                    process_id INTEGER,
                    acquired_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                    expires_at TIMESTAMP
                )
            """)
            
            # Table des performances des sélecteurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS selector_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    selector_name TEXT NOT NULL,
                    success BOOLEAN,
                    response_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                    page_load_time_ms INTEGER
                )
            """)
            
            # Créer les index pour améliorer les performances
            logger.info("🔧 Création des index optimisés...")
            
            # Index sur les colonnes fréquemment utilisées
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_shops_scraping_status 
                ON shops(scraping_status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_shops_scraping_last_update 
                ON shops(scraping_last_update)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_shops_shop_url 
                ON shops(shop_url)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analytics_shop_id 
                ON analytics(shop_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analytics_scraping_status 
                ON analytics(scraping_status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processing_locks_lock_name 
                ON processing_locks(lock_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_selector_performance_selector_name 
                ON selector_performance(selector_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_selector_performance_timestamp 
                ON selector_performance(timestamp)
            """)
            
            conn.commit()
            logger.info("✅ Tables et index optimisés créés")
            logger.info("✅ Base de données initialisée")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation DB: {e}")
    
    def __del__(self):
        """Destructeur pour fermer la connexion"""
        self._close_connection()
    
    def acquire_lock(self, lock_name: str = "batch_processing", timeout: int = 30) -> bool:
        """Acquiert un lock pour le traitement par lots"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Nettoyer les locks expirés
            cursor.execute("DELETE FROM processing_locks WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
            
            # Essayer d'acquérir le lock
            expires_at = datetime.now(timezone.utc).isoformat() + timedelta(seconds=timeout)
            cursor.execute("""
                INSERT INTO processing_locks (lock_name, process_id, acquired_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (lock_name, os.getpid(), datetime.now(timezone.utc).isoformat(), expires_at))
            
            conn.commit()
            logger.info(f"✅ Lock {lock_name} acquis")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Lock {lock_name} déjà acquis")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur acquisition lock {lock_name}: {e}")
            return False
    
    def release_lock(self, lock_name: str = "batch_processing") -> bool:
        """Libère un lock"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM processing_locks WHERE lock_name = ?", (lock_name,))
            conn.commit()
            logger.info(f"✅ Lock {lock_name} libéré")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur libération lock {lock_name}: {e}")
            return False
    
    def get_all_shops(self) -> List[Dict]:
        """Récupère toutes les boutiques de la base avec leurs analytics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.shop_name, s.shop_url, s.scraping_status, s.scraping_last_update, 
                       s.creation_date, s.category, s.monthly_visits, s.monthly_revenue, s.live_ads, 
                       s.page_number, s.scraped_at, s.updated_at, s.project_source, s.external_id, s.metadata,
                       a.organic_traffic, a.bounce_rate, a.avg_visit_duration, a.branded_traffic, a.conversion_rate, a.visits
                FROM shops s 
                LEFT JOIN analytics a ON s.id = a.shop_id 
                ORDER BY s.shop_url
            """)
            rows = cursor.fetchall()
            
            shops = []
            for row in rows:
                domain = row[2].replace('https://', '').replace('http://', '').replace('www.', '') if row[2] else ''
                shops.append({
                    'id': row[0],
                    'shop_name': row[1],
                    'shop_url': row[2],
                    'shop_domain': domain,
                    'domain': domain,  # Garder pour compatibilité
                    'name': row[1],    # Garder pour compatibilité
                    'scraping_status': row[3],
                    'scraping_last_update': row[4],
                    'creation_date': row[5],
                    'category': row[6],
                    'monthly_visits': row[7],
                    'monthly_revenue': row[8],
                    'live_ads': row[9],
                    'page_number': row[10],
                    'scraped_at': row[11],
                    'updated_at': row[12],
                    'project_source': row[13],
                    'external_id': row[14],
                    'metadata': row[15],
                    'organic_traffic': row[16],
                    'bounce_rate': row[17],
                    'average_visit_duration': row[18],
                    'branded_traffic': row[19],
                    'conversion_rate': row[20],
                    'visits': row[21]
                })
            
            logger.info(f"📊 {len(shops)} boutiques récupérées avec analytics")
            return shops
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques: {e}")
            return []
    
    def get_shop_by_domain(self, domain: str) -> Optional[Dict]:
        """Récupère une boutique par son domaine"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, domain, name FROM shops WHERE domain = ?", (domain,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'domain': row[1],
                        'name': row[2]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutique {domain}: {e}")
            return None
    
    def add_shop(self, domain: str, name: str = None) -> bool:
        """Ajoute une nouvelle boutique"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO shops (domain, name, updated_at) VALUES (?, ?, ?)",
                    (domain, name, datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
                logger.info(f"✅ Boutique ajoutée: {domain}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout boutique {domain}: {e}")
            return False
    
    def save_scraping_result(self, domain: str, date_range: str, data_type: str, data: Dict) -> bool:
        """Sauvegarde un résultat de scraping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupérer l'ID de la boutique
                shop = self.get_shop_by_domain(domain)
                shop_id = shop['id'] if shop else None
                
                cursor.execute("""
                    INSERT INTO scraping_results (shop_id, domain, date_range, data_type, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (shop_id, domain, date_range, data_type, json.dumps(data)))
                
                conn.commit()
                logger.info(f"✅ Résultat sauvegardé: {domain} - {data_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde résultat {domain}: {e}")
            return False
    
    def save_error(self, domain: str, error_type: str, error_message: str) -> bool:
        """Sauvegarde une erreur de scraping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scraping_errors (domain, error_type, error_message)
                    VALUES (?, ?, ?)
                """, (domain, error_type, error_message))
                
                conn.commit()
                logger.info(f"✅ Erreur sauvegardée: {domain} - {error_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde erreur {domain}: {e}")
            return False
    
    def get_scraping_history(self, domain: str = None, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des scrapings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if domain:
                    cursor.execute("""
                        SELECT domain, date_range, data_type, scraped_at 
                        FROM scraping_results 
                        WHERE domain = ? 
                        ORDER BY scraped_at DESC 
                        LIMIT ?
                    """, (domain, limit))
                else:
                    cursor.execute("""
                        SELECT domain, date_range, data_type, scraped_at 
                        FROM scraping_results 
                        ORDER BY scraped_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                history = []
                for row in rows:
                    history.append({
                        'domain': row[0],
                        'date_range': row[1],
                        'data_type': row[2],
                        'scraped_at': row[3]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération historique: {e}")
            return []
    
    def is_shop_eligible_for_scraping(self, shop: Dict) -> bool:
        """Vérifie si une boutique est éligible pour le scraping"""
        try:
            # Règle 1: Ne pas traiter si scraping_status est défini et non vide
            scraping_status = shop.get('scraping_status', '')
            if scraping_status:
                scraping_status = scraping_status.strip()
                if scraping_status:
                    # Règle 2: Exception si scraping_last_update > 15 jours
                    scraping_last_update = shop.get('scraping_last_update')
                    if scraping_last_update:
                        try:
                            from datetime import datetime, timezone, timedelta
                            # Convertir la date de dernière mise à jour
                            if isinstance(scraping_last_update, str):
                                last_update_date = datetime.fromisoformat(scraping_last_update.replace('Z', '+00:00'))
                            else:
                                last_update_date = datetime.fromisoformat(scraping_last_update)
                            
                            # Calculer si > 15 jours
                            current_date = datetime.now(timezone.utc).isoformat()
                            days_diff = (current_date - last_update_date).days
                            
                            if days_diff > 15:
                                logger.info(f"🔄 Boutique {shop.get('domain', 'N/A')} - Status '{scraping_status}' mais > 15 jours ({days_diff}j), retraitement autorisé")
                                return True
                            else:
                                logger.info(f"⏭️ Boutique {shop.get('domain', 'N/A')} - Status '{scraping_status}' et récent ({days_diff}j), passage")
                                return False
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur calcul date pour {shop.get('domain', 'N/A')}: {e}, passage")
                            return False
                    else:
                        logger.info(f"⏭️ Boutique {shop.get('domain', 'N/A')} - Status '{scraping_status}' sans date, passage")
                        return False
            
            # Si pas de status ou status vide, traiter
            logger.info(f"📝 Boutique {shop.get('domain', 'N/A')} - Pas de status, éligible")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification éligibilité pour {shop.get('domain', 'N/A')}: {e}")
            return False
    
    def update_shop_analytics(self, shop_id: int, analytics_data: Dict) -> bool:
        """Met à jour les analytics d'une boutique"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Préparer les données
            organic_traffic = analytics_data.get('organic_traffic', '')
            bounce_rate = analytics_data.get('bounce_rate', '')
            avg_visit_duration = analytics_data.get('average_visit_duration', '')
            branded_traffic = analytics_data.get('branded_traffic', '')
            conversion_rate = analytics_data.get('conversion_rate', '')
            visits = analytics_data.get('visits', '')
            traffic = analytics_data.get('traffic', '')
            percent_branded_traffic = analytics_data.get('percent_branded_traffic', 0.0)
            
            # Déterminer le statut automatiquement
            scraping_status = analytics_data.get('scraping_status', 'completed')
            
            # Si un des champs contient "Sélecteur non trouvé", mettre le statut à 'partial'
            selector_not_found = 'Sélecteur non trouvé'
            if (organic_traffic == selector_not_found or 
                branded_traffic == selector_not_found or 
                bounce_rate == selector_not_found or 
                avg_visit_duration == selector_not_found or 
                conversion_rate == selector_not_found or
                visits == selector_not_found or
                traffic == selector_not_found):
                scraping_status = 'partial'
            
            # Mettre à jour la table analytics
            cursor.execute("""
                INSERT OR REPLACE INTO analytics 
                (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, visits, traffic, percent_branded_traffic, scraping_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, visits, traffic, percent_branded_traffic, scraping_status, datetime.now(timezone.utc).isoformat()))
            
            # Mettre à jour le status dans la table shops
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = ?, scraping_last_update = ?
                WHERE id = ?
            """, (scraping_status, datetime.now(timezone.utc).isoformat(), shop_id))
            
            conn.commit()
            logger.info(f"✅ Analytics mis à jour pour shop_id {shop_id} (statut: {scraping_status})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour analytics shop_id {shop_id}: {e}")
            return False
    
    def mark_shop_failed(self, shop_id: int, error_message: str) -> bool:
        """Marque une boutique comme échouée"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = 'failed', scraping_last_update = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), shop_id))
            
            # Enregistrer l'erreur
            cursor.execute("""
                INSERT INTO scraping_errors (shop_id, error_message, occurred_at)
                VALUES (?, ?, ?)
            """, (shop_id, error_message, datetime.now(timezone.utc).isoformat()))
            
            conn.commit()
            logger.info(f"✅ Boutique {shop_id} marquée comme échouée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur marquage échec boutique {shop_id}: {e}")
            return False
    
    def get_shop_analytics(self, shop_id: int) -> Optional[Dict]:
        """Récupère les analytics d'une boutique depuis la table analytics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, visits, traffic, percent_branded_traffic, scraping_status,
                       paid_search_traffic
                FROM analytics 
                WHERE shop_id = ?
            """, (shop_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'organic_traffic': row[0],
                    'bounce_rate': row[1],
                    'average_visit_duration': row[2],  # Changé de avg_visit_duration
                    'branded_traffic': row[3],
                    'conversion_rate': row[4],
                    'visits': row[5],
                    'traffic': row[6],
                    'percent_branded_traffic': row[7],
                    'scraping_status': row[8],
                    'paid_search_traffic': row[9]  # ✅ Ajouté
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération analytics shop_id {shop_id}: {e}")
            return None
    
    def record_selector_performance(self, selector_name: str, success: bool, response_time_ms: int, page_load_time_ms: int = None):
        """Enregistre une performance de sélecteur"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO selector_performance (selector_name, success, response_time_ms, page_load_time_ms)
                VALUES (?, ?, ?, ?)
            """, (selector_name, success, response_time_ms, page_load_time_ms))
            
            # Nettoyer les anciennes données (garder seulement les 100 dernières par sélecteur)
            cursor.execute("""
                DELETE FROM selector_performance 
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM selector_performance 
                        WHERE selector_name = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 100
                    )
                ) AND selector_name = ?
            """, (selector_name, selector_name))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement performance sélecteur: {e}")
    
    def get_recent_selector_performances(self, selector_name: str, limit: int = 20) -> List[Dict]:
        """Récupère les performances récentes d'un sélecteur"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT success, response_time_ms, page_load_time_ms
                FROM selector_performance 
                WHERE selector_name = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (selector_name, limit))
            
            performances = []
            for row in cursor.fetchall():
                performances.append({
                    'success': bool(row[0]),
                    'response_time_ms': row[1],
                    'page_load_time_ms': row[2]
                })
            
            return performances
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération performances sélecteur: {e}")
            return []
    
    def calculate_adaptive_timeout(self, selector_name: str, base_timeout: int = 30000) -> int:
        """Calcule un timeout adaptatif basé sur l'historique des performances"""
        try:
            recent_performances = self.get_recent_selector_performances(selector_name, limit=20)
            
            if len(recent_performances) < 5:
                # Pas assez de données → timeout par défaut
                logger.debug(f"📊 Pas assez de données pour {selector_name}, timeout par défaut: {base_timeout}ms")
                return base_timeout
            
            # Calculer les statistiques
            success_count = sum(1 for p in recent_performances if p['success'])
            success_rate = success_count / len(recent_performances)
            avg_response_time = sum(p['response_time_ms'] for p in recent_performances) / len(recent_performances)
            
            # Facteurs d'ajustement
            if success_rate < 0.6:
                # Échecs fréquents → augmenter le timeout
                timeout_multiplier = 1.3
                logger.debug(f"📊 {selector_name}: Échecs fréquents ({success_rate:.2f}), augmentation timeout")
            elif success_rate > 0.85:
                # Succès fréquents → réduire le timeout
                timeout_multiplier = 0.7
                logger.debug(f"📊 {selector_name}: Succès fréquents ({success_rate:.2f}), réduction timeout")
            else:
                # Performance moyenne → ajustement modéré
                timeout_multiplier = 1.0
                logger.debug(f"📊 {selector_name}: Performance moyenne ({success_rate:.2f}), timeout standard")
            
            # Ajuster selon le temps de réponse moyen
            if avg_response_time > base_timeout * 0.6:
                # Réponses lentes → augmenter légèrement
                timeout_multiplier *= 1.1
                logger.debug(f"📊 {selector_name}: Réponses lentes ({avg_response_time:.0f}ms), augmentation légère")
            
            # Limites min/max
            min_timeout = 15000  # 15s minimum
            max_timeout = 90000  # 90s maximum
            
            adaptive_timeout = int(base_timeout * timeout_multiplier)
            final_timeout = max(min_timeout, min(adaptive_timeout, max_timeout))
            
            logger.debug(f"📊 {selector_name}: Timeout adaptatif {base_timeout}ms → {final_timeout}ms (×{timeout_multiplier:.2f})")
            return final_timeout
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul timeout adaptatif pour {selector_name}: {e}")
            return base_timeout
    
    def get_all_shops_with_analytics(self, limit: int = None) -> List[Dict]:
        """Récupère toutes les boutiques avec leurs métriques analytics"""
        try:
            all_shops = self.get_all_shops()
            shops_with_analytics = []
            
            for shop in all_shops:
                shop_with_analytics = shop.copy()
                analytics = self.get_shop_analytics(shop.get('id'))
                if analytics:
                    shop_with_analytics.update(analytics)
                shops_with_analytics.append(shop_with_analytics)
            
            # Trier par qualité des données (boutiques complètes en premier)
            shops_with_analytics.sort(key=lambda x: x.get('scraping_status', ''), reverse=True)
            
            if limit:
                shops_with_analytics = shops_with_analytics[:limit]
            
            return shops_with_analytics
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques avec analytics: {e}")
            return []

# Instance globale de l'API
api = TrendTrackAPI(get_database_path())

# Fonctions de compatibilité pour l'ancien code
def get_all_shops():
    """Récupère toutes les boutiques"""
    return api.get_all_shops()

def save_results(domain: str, data: Dict):
    """Sauvegarde les résultats pour un domaine"""
    for data_type, data_content in data.items():
        api.save_scraping_result(domain, "202506", data_type, data_content)
    return True
