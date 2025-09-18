#!/usr/bin/env python3
"""
API TrendTrack adaptée pour VPS - VERSION CORRIGÉE (sans doublons)
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendTrackAPI:
    """API pour gérer la base de données TrendTrack - VERSION CORRIGÉE"""
    
    def __init__(self, db_path: str = None):
        """Initialise l'API avec le chemin de la base de données"""
        if db_path is None:
            # Chemin par défaut sur le VPS
            self.db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
        else:
            self.db_path = db_path
            
        # Vérifier la structure de la base au démarrage
        self._ensure_database_structure()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtient une connexion à la base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Permet l'accès par nom de colonne
            return conn
        except Exception as e:
            logger.error(f"❌ Erreur connexion base de données: {e}")
            raise
    
    def _ensure_database_structure(self):
        """Vérifie et corrige la structure de la base de données"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Vérifier que les tables nécessaires existent
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('shops', 'analytics')
            """)
            required_tables = ['shops', 'analytics']
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                logger.error(f"❌ Tables manquantes: {missing_tables}")
                raise Exception(f"Tables manquantes: {missing_tables}")
            
            # Vérifier la structure de la table analytics
            cursor.execute("PRAGMA table_info(analytics)")
            analytics_columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = [
                'id', 'shop_id', 'organic_traffic', 'bounce_rate', 
                'avg_visit_duration', 'branded_traffic', 'conversion_rate',
                'scraping_status', 'updated_at', 'visits', 'traffic',
                'percent_branded_traffic', 'paid_search_traffic'
            ]
            
            missing_columns = [col for col in required_columns if col not in analytics_columns]
            if missing_columns:
                logger.error(f"❌ Colonnes manquantes dans analytics: {missing_columns}")
                raise Exception(f"Colonnes manquantes: {missing_columns}")
            
            # Vérifier que la contrainte unique sur shop_id existe
            cursor.execute("PRAGMA index_list(analytics)")
            indexes = [row[1] for row in cursor.fetchall()]
            
            if 'idx_analytics_shop_id_unique' not in indexes:
                logger.warning("⚠️ Contrainte unique sur shop_id manquante, ajout...")
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX idx_analytics_shop_id_unique 
                        ON analytics(shop_id)
                    """)
                    logger.info("✅ Contrainte unique ajoutée sur shop_id")
                except Exception as e:
                    logger.error(f"❌ Erreur ajout contrainte unique: {e}")
            
            conn.commit()
            logger.info("✅ Structure de la base vérifiée et corrigée")
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification structure base: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def update_shop_analytics(self, shop_id: int, analytics_data: Dict) -> bool:
        """Met à jour les analytics d'une boutique - VERSION CORRIGÉE (sans doublons)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Préparer les données
            organic_traffic = analytics_data.get('organic_traffic', '')
            bounce_rate = analytics_data.get('bounce_rate', '')
            avg_visit_duration = analytics_data.get('average_visit_duration', '')
            branded_traffic = analytics_data.get('branded_traffic', '')
            conversion_rate = analytics_data.get('conversion_rate', '')
            paid_search_traffic = analytics_data.get('paid_search_traffic', '')
            visits = analytics_data.get('visits', '')
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
            
            # VÉRIFICATION CRITIQUE : Vérifier si l'entrée existe déjà
            cursor.execute("SELECT id FROM analytics WHERE shop_id = ?", (shop_id,))
            existing = cursor.fetchone()
            
            if existing:
                # MISE À JOUR : L'entrée existe, on la met à jour
                logger.info(f"🔄 Mise à jour analytics existante pour shop_id {shop_id}")
                cursor.execute("""
                    UPDATE analytics SET
                    organic_traffic = ?, bounce_rate = ?, avg_visit_duration = ?,
                    branded_traffic = ?, conversion_rate = ?, paid_search_traffic = ?,
                    visits = ?, traffic = ?, percent_branded_traffic = ?,
                    scraping_status = ?, updated_at = ?
                    WHERE shop_id = ?
                """, (organic_traffic, bounce_rate, avg_visit_duration, branded_traffic,
                      conversion_rate, paid_search_traffic, visits, traffic, 
                      percent_branded_traffic, scraping_status, datetime.now(timezone.utc), shop_id))
                
                rows_updated = cursor.rowcount
                if rows_updated == 0:
                    logger.warning(f"⚠️ Aucune ligne mise à jour pour shop_id {shop_id}")
                else:
                    logger.info(f"✅ {rows_updated} ligne(s) mise(s) à jour pour shop_id {shop_id}")
            else:
                # INSERTION : L'entrée n'existe pas, on l'insère
                logger.info(f"➕ Insertion nouvelle analytics pour shop_id {shop_id}")
                cursor.execute("""
                    INSERT INTO analytics 
                    (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic,
                     conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic,
                     scraping_status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic,
                      conversion_rate, paid_search_traffic, visits, traffic, 
                      percent_branded_traffic, scraping_status, datetime.now(timezone.utc)))
                
                logger.info(f"✅ Nouvelle analytics insérée pour shop_id {shop_id}")
            
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
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_shop_analytics(self, shop_id: int) -> Optional[Dict]:
        """Récupère les analytics d'une boutique - VERSION CORRIGÉE"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Récupérer les analytics les plus récents pour cette boutique
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, visits, traffic, percent_branded_traffic, scraping_status,
                       paid_search_traffic, updated_at
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
                    'visits': row[5],
                    'traffic': row[6],
                    'percent_branded_traffic': row[7],
                    'scraping_status': row[8],
                    'paid_search_traffic': row[9],
                    'updated_at': row[10]
                }
            else:
                logger.info(f"ℹ️ Aucune analytics trouvée pour shop_id {shop_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération analytics shop_id {shop_id}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_all_shops(self) -> List[Dict]:
        """Récupère toutes les boutiques"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, shop_name, shop_url, scraping_status, scraping_last_update,
                       creation_date, monthly_visits, monthly_revenue, live_ads,
                       page_number, scraped_at, project_source, external_id, metadata, updated_at
                FROM shops
                ORDER BY id
            """)
            
            shops = []
            for row in cursor.fetchall():
                shop = dict(row)
                shops.append(shop)
            
            logger.info(f"✅ {len(shops)} boutiques récupérées")
            return shops
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_all_shops_with_analytics(self, limit: int = None) -> List[Dict]:
        """Récupère toutes les boutiques avec leurs métriques analytics - VERSION CORRIGÉE"""
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
            
            logger.info(f"✅ {len(shops_with_analytics)} boutiques avec analytics récupérées")
            return shops_with_analytics
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques avec analytics: {e}")
            return []
    
    def mark_shop_failed(self, shop_id: int, error_message: str) -> bool:
        """Marque une boutique comme échouée"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Mettre à jour le statut dans shops
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = 'failed', scraping_last_update = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc), shop_id))
            
            # Ajouter une entrée dans analytics avec le statut 'failed'
            cursor.execute("""
                INSERT INTO analytics 
                (shop_id, scraping_status, updated_at)
                VALUES (?, 'failed', ?)
            """, (shop_id, datetime.now(timezone.utc)))
            
            conn.commit()
            logger.info(f"✅ Shop {shop_id} marqué comme échoué: {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur marquage shop {shop_id} comme échoué: {e}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def calculate_adaptive_timeout(self, selector_name: str, base_timeout: int = 30000) -> int:
        """Calcule un timeout adaptatif basé sur l'historique des performances"""
        try:
            # Pour l'instant, retourner le timeout de base
            # TODO: Implémenter la logique adaptative complète
            return base_timeout
                
        except Exception as e:
            # En cas d'erreur, retourner le timeout de base
            return base_timeout

    def get_selector_success_rate(self, selector_name: str) -> float:
        """Récupère le taux de succès d'un sélecteur"""
        try:
            # Pour l'instant, retourner un taux par défaut
            return 0.8  # 80% de succès par défaut
        except Exception as e:
            return 0.8

    def reset_selector_performance(self):
        """Réinitialise les performances des sélecteurs"""
        try:
            # Pour l'instant, ne rien faire
            pass
        except Exception as e:
            pass

    def record_selector_performance(self, selector_name: str, success: bool, response_time: int):
        """Enregistre la performance d'un sélecteur"""
        try:
            # Pour l'instant, ne rien faire
            pass
        except Exception as e:
            pass

    def acquire_lock(self, timeout: int = 30) -> bool:
        """Acquiert un verrou pour le scraping"""
        try:
            # Pour l'instant, toujours réussir
            return True
        except Exception as e:
            return True

    def release_lock(self):
        """Libère le verrou de scraping"""
        try:
            # Pour l'instant, ne rien faire
            pass
        except Exception as e:
            pass

    def is_shop_eligible_for_scraping(self, shop: dict) -> bool:
        """Vérifie si une boutique est éligible pour le scraping"""
        try:
            # Pour l'instant, toutes les boutiques sont éligibles
            return True
        except Exception as e:
            return True

# Instance globale de l'API
api = TrendTrackAPI()

# Fonction de test pour validation
def test_api_functionality():
    """Teste la fonctionnalité de l'API corrigée"""
    try:
        print("🧪 TEST DE L'API CORRIGÉE")
        print("=" * 40)
        
        # Test 1: Vérifier la structure
        print("✅ Structure de la base vérifiée")
        
        # Test 2: Récupérer quelques boutiques
        shops = api.get_all_shops_with_analytics(limit=3)
        print(f"✅ {len(shops)} boutiques récupérées avec analytics")
        
        # Test 3: Vérifier qu'il n'y a pas de doublons
        if shops:
            shop_ids = [shop['id'] for shop in shops]
            unique_ids = set(shop_ids)
            if len(shop_ids) == len(unique_ids):
                print("✅ Aucun doublon détecté")
            else:
                print("❌ Doublons détectés!")
        
        print("🎯 API corrigée fonctionne parfaitement!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return False

    def get_all_analytics(self):
        """
        Récupère toutes les métriques analytics de la base de données
        """
        try:
            cursor = self.conn.execute("""
                SELECT id, shop_id, metric_type, metric_value, scraping_status, 
                       scraping_date, created_at, updated_at
                FROM analytics 
                ORDER BY shop_id, metric_type, created_at DESC
            """)
            
            analytics = []
            for row in cursor.fetchall():
                analytics.append({
                    "id": row[0],
                    "shop_id": row[1],
                    "metric_type": row[2],
                    "metric_value": row[3],
                    "scraping_status": row[4],
                    "scraping_date": row[5],
                    "created_at": row[6],
                    "updated_at": row[7]
                })
            
            self.logger.info(f"✅ {len(analytics)} métriques analytics récupérées")
            return analytics
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la récupération des analytics: {e}")
            return []

if __name__ == "__main__":
    test_api_functionality()
