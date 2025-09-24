"""
API TrendTrack - Gestion de la base SQLite (VERSION ADAPTÉE VPS)
Fonctions pour récupérer et sauvegarder les données de scraping
Adapté pour fonctionner avec la structure VPS existante
"""

def parse_date_robust(date_string):
    """Parse une date de manière robuste avec gestion des timezones"""
    if not date_string:
        return None
    
    # Nettoyer la chaîne
    date_string = str(date_string).strip()
    
    # Formats courants
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # 2025-08-05T19:40:56.053Z
        "%Y-%m-%dT%H:%M:%S.%f",   # 2025-08-05T19:40:56.053
        "%Y-%m-%d %H:%M:%S.%f",   # 2025-08-05 20:47:15.852714
        "%Y-%m-%dT%H:%M:%S",      # 2025-08-05T19:40:56
        "%Y-%m-%d %H:%M:%S",      # 2025-08-05 20:47:15
        "%Y-%m-%d",               # 2025-08-05
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            # Si pas de timezone, ajouter UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    # Si aucun format ne marche, essayer de parser et ajouter UTC
    try:
        # Essayer de parser avec dateutil si disponible
        from dateutil import parser
        dt = parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except:
        pass
    
    # Fallback: retourner None
    return None


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
    
    if vps_detected:
        # VPS Linux - utiliser la base existante
        db_path = "../trendtrack-scraper-final/data/trendtrack.db"
        return db_path
    else:
        # macOS local
        db_path = "/Users/infusion/Desktop/trendtrack-scrapper/data/trendtrack.db"
        return db_path

class TrendTrackAPI:
    """API pour interagir avec la base de données TrendTrack (adaptée VPS)"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_database_path()
        self.db_path = db_path
        self._connection = None
        self._initialize_database()
    
    def _get_connection(self):
        """Obtenir une connexion à la base de données (poolée)"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            # Optimisations pour les performances
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._connection.execute("PRAGMA cache_size=10000")
            self._connection.execute("PRAGMA temp_store=MEMORY")
        return self._connection
    
    def _close_connection(self):
        """Fermer la connexion à la base de données"""
        if self._connection:
            self._connection.close()
            self._connection = None

    
    def _initialize_database(self):
        """Initialiser la base de données - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Vérifier que les tables existent (ne pas les créer)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['shops', 'analytics']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.error(f"❌ Tables manquantes: {missing_tables}")
                raise Exception(f"Tables requises manquantes: {missing_tables}")
            

            
            # Vérifier la structure de la table shops
            cursor.execute("PRAGMA table_info(shops)")
            shops_columns = [row[1] for row in cursor.fetchall()]
            
            # Vérifier la structure de la table analytics
            cursor.execute("PRAGMA table_info(analytics)")
            analytics_columns = [row[1] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation DB: {e}")
            raise
    
    def __del__(self):
        """Destructeur pour fermer la connexion"""
        try:
            self._close_connection()
        except:
            # Ignorer les erreurs lors de la destruction (problèmes de logging)
            pass
    
    def acquire_lock(self, lock_name: str = "batch_processing", timeout: int = 30) -> bool:
        """Acquiert un lock pour éviter les conflits"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Vérifier si la table processing_locks existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processing_locks'")
            if not cursor.fetchone():
                logger.warning("⚠️  Table processing_locks non trouvée - création de la table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_locks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        lock_name TEXT UNIQUE NOT NULL,
                        process_id INTEGER,
                        acquired_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
                        expires_at TIMESTAMP
                    )
                """)
                conn.commit()
            
            # Nettoyer les locks expirés
            cursor.execute("DELETE FROM processing_locks WHERE expires_at < ?", (datetime.now(timezone.utc),))
            
            # Essayer d'acquérir le lock
            cursor.execute("""
                INSERT INTO processing_locks (lock_name, process_id, expires_at)
                VALUES (?, ?, ?)
            """, (lock_name, os.getpid(), datetime.now(timezone.utc) + timedelta(seconds=timeout)))
            
            conn.commit()
            logger.info(f"🔒 Lock acquis: {lock_name}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️  Lock déjà acquis: {lock_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur acquisition lock: {e}")
            return False
    
    def release_lock(self, lock_name: str = "batch_processing") -> bool:
        """Libère un lock"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM processing_locks WHERE lock_name = ?", (lock_name,))
            conn.commit()
            
            logger.info(f"🔓 Lock libéré: {lock_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur libération lock: {e}")
            return False
    
    def get_all_shops(self) -> List[Dict]:
        """Récupère toutes les boutiques - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Requête adaptée pour la structure VPS
            cursor.execute("""
                SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                       updated_at, creation_date, monthly_visits, monthly_revenue, live_ads,
                       page_number, scraped_at, project_source, external_id, metadata,
                       year_founded
                FROM shops 
                ORDER BY id
            """)
            
            shops = []
            for row in cursor.fetchall():
                shop = {
                    'id': row[0],
                    'name': row[1] or row[2].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] or 'Unknown',                                                                             
                    'domain': row[2] or '',
                    'shop_url': row[2] or '',  # Ajout pour compatibilité
                    'scraping_status': row[3] if row[3] is not None else '',
                    'scraping_last_update': row[4],
                    'updated_at': row[5],
                    'creation_date': row[6],
                    'monthly_visits': row[7],
                    'monthly_revenue': row[8],
                    'live_ads': row[9],
                    'page_number': row[10],
                    'scraped_at': row[11],
                    'project_source': row[12],
                    'external_id': row[13],
                    'metadata': row[14],
                    'year_founded': row[15]
                }
                shops.append(shop)
            

            return shops
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques: {e}")
            return []

    def get_shops_by_range(self, start_id: int, end_id: int, status_filter: str = None) -> List[Dict]:
        """Récupère les boutiques dans un range d'ID spécifique - POUR PARALLÉLISME"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Construire la requête avec filtres optionnels
            query = """
                SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                       creation_date, monthly_visits, monthly_revenue, live_ads,
                       page_number, scraped_at, project_source, external_id, metadata,
                       updated_at
                FROM shops 
                WHERE id BETWEEN ? AND ?
            """
            params = [start_id, end_id]
            
            # Ajouter filtre de statut si spécifié
            if status_filter:
                query += " AND scraping_status = ?"
                params.append(status_filter)
            elif status_filter == "":  # Statut vide (NULL)
                query += " AND scraping_status IS NULL"
            
            query += " ORDER BY id"
            
            cursor.execute(query, params)
            
            shops = []
            for row in cursor.fetchall():
                shop = {
                    'id': row[0],
                    'name': row[1] or row[2].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] or 'Unknown',                                                                             
                    'domain': row[2] or '',
                    'shop_url': row[2] or '',  # Ajout pour compatibilité
                    'scraping_status': row[3] if row[3] is not None else '',
                    'scraping_last_update': row[4],
                    'updated_at': row[5],
                    'creation_date': row[6],
                    'monthly_visits': row[7],
                    'monthly_revenue': row[8],
                    'live_ads': row[9],
                    'page_number': row[10],
                    'scraped_at': row[11],
                    'project_source': row[12],
                    'external_id': row[13],
                    'metadata': row[14],
                    'year_founded': row[15]
                }
                shops.append(shop)
            

            return shops
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques par range: {e}")
            return []

    def get_shops_count_by_status(self, status: str = None) -> int:
        """Compte le nombre de boutiques par statut - POUR PARALLÉLISME"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if status == "":  # Statut vide (NULL)
                cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status IS NULL")
            elif status is None:
                cursor.execute("SELECT COUNT(*) FROM shops")
            else:
                cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = ?", (status,))
            
            count = cursor.fetchone()[0]
            return count
            
        except Exception as e:
            logger.error(f"❌ Erreur comptage boutiques: {e}")
            return 0
    
    def get_shop_by_domain(self, domain: str) -> Optional[Dict]:
        """Récupère une boutique par domaine - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, shop_name, shop_url, scraping_status, scraping_last_update,
                       creation_date, monthly_visits, monthly_revenue, live_ads,
                       page_number, scraped_at, project_source, external_id, metadata,
                       updated_at
                FROM shops 
                WHERE shop_url LIKE ?
            """, (f"%{domain}%",))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1] or row[2].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] or 'Unknown',
                    'domain': row[2] or '',
                    'shop_url': row[2] or '',  # Ajout pour compatibilité
                    'scraping_status': row[3] if row[3] is not None else '',
                    'scraping_last_update': row[4],
                    'creation_date': row[5],
                    
                    'monthly_visits': row[7],
                    'monthly_revenue': row[8],
                    'live_ads': row[9],
                    'page_number': row[10],
                    'scraped_at': row[11],
                    'project_source': row[12],
                    'external_id': row[13],
                    'metadata': row[14],
                    'updated_at': row[15]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutique par domaine: {e}")
            return None
    
    def add_shop(self, domain: str, name: str = None) -> bool:
        """Ajoute une nouvelle boutique - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO shops 
                (shop_name, shop_url, scraping_status, scraping_last_update, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name or domain, domain, 'pending', datetime.now(timezone.utc), datetime.now(timezone.utc)))
            
            conn.commit()
            logger.info(f"✅ Boutique ajoutée: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout boutique: {e}")
            return False
    
    def update_shop_analytics(self, shop_id: int, analytics_data: Dict) -> bool:
        """Met à jour les analytics d'une boutique - ADAPTÉ POUR VPS"""
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
            paid_search_traffic = analytics_data.get('paid_search_traffic', '')
            traffic = analytics_data.get('traffic', '')
            percent_branded_traffic = analytics_data.get('percent_branded_traffic', '')
            
            # Déterminer le statut automatiquement
            scraping_status = analytics_data.get('scraping_status', 'completed')
            
            # Si un des champs contient "Sélecteur non trouvé" ou est vide, mettre le statut à 'partial'
            selector_not_found = 'Sélecteur non trouvé'
            required_fields = [organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, visits, traffic, percent_branded_traffic]
            
            if (any(field == selector_not_found for field in required_fields) or 
                any(field == '' or field is None for field in required_fields)):
                scraping_status = 'partial'
            
            # Mettre à jour la table analytics
            cursor.execute("""
                INSERT OR REPLACE INTO analytics 
                (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, scraping_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, scraping_status, datetime.now(timezone.utc)))
            
            # Mettre à jour le status dans la table shops
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = ?, scraping_last_update = ?
                WHERE id = ?
            """, (scraping_status, datetime.now(timezone.utc), shop_id))
            
            conn.commit()
            logger.info(f"✅ Analytics mis à jour pour shop_id {shop_id} (statut: {scraping_status})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour analytics shop_id {shop_id}: {e}")
            return False
    
    def mark_shop_failed(self, shop_id: int, error_message: str) -> bool:
        """Marque une boutique comme échouée - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = 'failed', scraping_last_update = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc), shop_id))
            
            # Enregistrer l'erreur si la table existe
            try:
                cursor.execute("""
                    INSERT INTO scraping_errors (shop_id, error_message, occurred_at)
                    VALUES (?, ?, ?)
                """, (shop_id, error_message, datetime.now(timezone.utc)))
            except:
                logger.warning("⚠️  Table scraping_errors non disponible")
            
            conn.commit()
            logger.info(f"✅ Boutique {shop_id} marquée comme échouée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur marquage échec boutique {shop_id}: {e}")
            return False
    
    def get_shop_analytics(self, shop_id: int) -> Optional[Dict]:
        """Récupère les analytics d'une boutique - ADAPTÉ POUR VPS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'organic_traffic': row[0],
                    'bounce_rate': row[1],
                    'average_visit_duration': row[2],
                    'branded_traffic': row[3],
                    'conversion_rate': row[4],
                    'paid_search_traffic': row[5],
                    'visits': row[6],
                    'traffic': row[7],
                    'percent_branded_traffic': row[8],
                    'scraping_status': row[9]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération analytics shop_id {shop_id}: {e}")
            return None
    
    def is_shop_eligible_for_scraping(self, shop: Dict) -> bool:
        """Vérifie si une boutique est éligible pour le scraping - ADAPTÉ POUR VPS"""
        try:
            # Vérifier le statut de scraping
            scraping_status = shop.get('scraping_status', 'pending')
            
            # RÈGLE PRIORITAIRE : Si statut est vide (''), la boutique est éligible peu importe la date
            if scraping_status == '':
                return True
            
            # Boutiques éligibles (sauf statut vide qui est déjà traité)
            eligible_statuses = ['pending', 'failed', 'partial']
            
            if scraping_status not in eligible_statuses:
                return False
            
            # Vérifier la dernière mise à jour (seulement pour les statuts non-vides)
            last_update = shop.get('scraping_last_update')
            if last_update:
                try:
                    last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    # Si la dernière mise à jour date de moins de 24h, ne pas rescraper
                    if datetime.now(timezone.utc) - last_update_dt < timedelta(hours=24):
                        return False
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification éligibilité: {e}")
            return False


    def record_selector_performance(self, selector_name: str, success: bool, response_time_ms: int, page_load_time_ms: int = None):
        """Enregistre les performances d'un sélecteur"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Créer la table si elle n'existe pas
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
            
            cursor.execute("""
                INSERT INTO selector_performance (selector_name, success, response_time_ms, page_load_time_ms)
                VALUES (?, ?, ?, ?)
            """, (selector_name, success, response_time_ms, page_load_time_ms))
            
            conn.commit()
            logger.info(f"📊 Performance sélecteur enregistrée: {selector_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement performance sélecteur: {e}")
            return False
    
    def get_recent_selector_performances(self, selector_name: str, limit: int = 20) -> List[Dict]:
        """Récupère les performances récentes d'un sélecteur"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT success, response_time_ms, page_load_time_ms, timestamp
                FROM selector_performance 
                WHERE selector_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (selector_name, limit))
            
            performances = []
            for row in cursor.fetchall():
                performances.append({
                    'success': row[0],
                    'response_time_ms': row[1],
                    'page_load_time_ms': row[2],
                    'timestamp': row[3]
                })
            
            return performances
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération performances sélecteur: {e}")
            return []
    
    def calculate_adaptive_timeout(self, selector_name: str, base_timeout: int = 30000) -> int:
        """Calcule un timeout adaptatif basé sur les performances historiques avec logique améliorée"""
        try:
            performances = self.get_recent_selector_performances(selector_name, limit=15)  # Augmenté à 15
            
            if not performances:
                return base_timeout
            
            # Calculer la moyenne des temps de réponse réussis
            successful_times = [p['response_time_ms'] for p in performances if p['success'] and p['response_time_ms']]
            
            if not successful_times:
                return base_timeout
            
            avg_response_time = sum(successful_times) / len(successful_times)
            
            # Calculer le taux de succès
            success_rate = sum(1 for p in performances if p['success']) / len(performances)
            
            # Logique adaptative améliorée
            if success_rate >= 0.80:  # Taux de succès élevé (80%+)
                adaptive_timeout = max(avg_response_time * 2.5, base_timeout * 0.9)
            elif success_rate >= 0.60:  # Taux de succès bon (60-79%)
                adaptive_timeout = max(avg_response_time * 3, base_timeout)
            elif success_rate >= 0.40:  # Taux de succès moyen (40-59%)
                adaptive_timeout = max(avg_response_time * 4, base_timeout * 1.2)
            elif success_rate >= 0.20:  # Taux de succès faible (20-39%)
                adaptive_timeout = max(avg_response_time * 5, base_timeout * 1.5)
            else:  # Taux de succès très faible (<20%)
                adaptive_timeout = max(avg_response_time * 6, base_timeout * 2.0)
            
            # Limites adaptées selon le type de sélecteur
            if "Traffic Analysis" in selector_name or "visits" in selector_name.lower():
                min_timeout, max_timeout = 45000, 180000  # 45s-180s pour Traffic Analysis (augmenté)
            elif "Average Visit Duration" in selector_name or "Bounce Rate" in selector_name:
                min_timeout, max_timeout = 30000, 120000   # 30s-120s pour les métriques d'engagement (augmenté)
            elif "Organic Search Traffic" in selector_name:
                min_timeout, max_timeout = 25000, 120000   # 25s-120s pour Organic Search (augmenté)
            elif "Branded Traffic" in selector_name:
                min_timeout, max_timeout = 20000, 90000   # 20s-90s pour Branded Traffic (augmenté)
            else:
                min_timeout, max_timeout = 20000, 100000   # 20s-100s par défaut (augmenté)
            
            adaptive_timeout = max(min_timeout, min(max_timeout, int(adaptive_timeout)))
            
            logger.info(f"⏱️  Timeout adaptatif pour {selector_name}: {adaptive_timeout}ms (succès: {success_rate:.2f})")
            return adaptive_timeout
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul timeout adaptatif: {e}")
            return base_timeout
    
    def get_selector_success_rate(self, selector_name: str) -> float:
        """Récupère le taux de succès récent d'un sélecteur"""
        try:
            performances = self.get_recent_selector_performances(selector_name, limit=10)
            
            if not performances:
                return 0.0
            
            success_count = sum(1 for p in performances if p['success'])
            success_rate = success_count / len(performances)
            
            return success_rate
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul taux de succès: {e}")
            return 0.0
    
    def reset_selector_performance(self):
        """Réinitialise les performances de tous les sélecteurs"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM selector_performance")
            conn.commit()
            
            logger.info("🔄 Performances des sélecteurs réinitialisées")
            return True
            
        except Exception as e:
                    logger.error(f"❌ Erreur réinitialisation performances: {e}")
        return False
    
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

# Fonctions globales pour compatibilité
def get_all_shops():
    """Fonction globale pour récupérer toutes les boutiques"""
    api = TrendTrackAPI()
    return api.get_all_shops()

def get_shops_by_range(start_id: int, end_id: int, status_filter: str = None):
    """Fonction globale pour récupérer les boutiques par range - POUR PARALLÉLISME"""
    api = TrendTrackAPI()
    return api.get_shops_by_range(start_id, end_id, status_filter)

def get_shops_count_by_status(status: str = None):
    """Fonction globale pour compter les boutiques par statut - POUR PARALLÉLISME"""
    api = TrendTrackAPI()
    return api.get_shops_count_by_status(status)

def save_results(domain: str, data: Dict):
    """Fonction globale pour sauvegarder les résultats"""
    api = TrendTrackAPI()
    shop = api.get_shop_by_domain(domain)
    if shop:
        return api.update_shop_analytics(shop['id'], data)
    return False

def get_selector_success_rate(selector_name: str) -> float:
    """Fonction globale pour récupérer le taux de succès d'un sélecteur"""
    api = TrendTrackAPI()
    return api.get_selector_success_rate(selector_name)

def reset_selector_performance():
    """Fonction globale pour réinitialiser les performances"""
    api = TrendTrackAPI()
    return api.reset_selector_performance()

# Instance globale pour compatibilité
api = TrendTrackAPI()

# Fonctions pour le parallélisme dynamique
def get_shops_with_empty_status():
    """Récupère la liste des IDs des boutiques avec statut NULL"""
    try:
        api = TrendTrackAPI()
        conn = api._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM shops WHERE scraping_status IS NULL ORDER BY id")
        results = cursor.fetchall()
        
        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"❌ Erreur récupération shops avec statut vide: {e}")
        return []

def calculate_ranges_from_ids(shop_ids, num_workers=6):
    """Calcule les ranges pour les workers basés sur les IDs réels"""
    if not shop_ids:
        return []
    
    chunk_size = len(shop_ids) // num_workers
    remainder = len(shop_ids) % num_workers
    
    ranges = []
    start_idx = 0
    
    for i in range(num_workers):
        # Ajouter un ID supplémentaire aux premiers workers si nécessaire
        current_chunk_size = chunk_size + (1 if i < remainder else 0)
        
        if current_chunk_size > 0:
            end_idx = start_idx + current_chunk_size - 1
            start_id = shop_ids[start_idx]
            end_id = shop_ids[end_idx]
            ranges.append((start_id, end_id))
            start_idx += current_chunk_size
    
    return ranges
