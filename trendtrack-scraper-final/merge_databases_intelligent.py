#!/usr/bin/env python3
"""
Script de merge intelligent entre la base actuelle et le backup du 28 août
- Garde la structure actuelle (avec paid_search_traffic)
- Récupère toutes les données historiques du backup
- Préserve les données récentes si elles existent
"""

import sqlite3
import logging
from datetime import datetime, timezone
import shutil

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/merge_databases_{datetime.now(timezone.utc).isoformat()}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMerger:
    def __init__(self):
        self.current_db = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
        self.backup_db = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack_backup_before_paid_traffic_20250828_074636.db'
        self.stats = {
            'shops_updated': 0,
            'analytics_updated': 0,
            'shops_preserved': 0,
            'analytics_preserved': 0,
            'errors': 0
        }

    def backup_current_db(self):
        """Sauvegarde de la base actuelle avant merge"""
        timestamp = datetime.now(timezone.utc).isoformat()
        backup_path = f'/home/ubuntu/trendtrack-scraper-final/data/trendtrack_backup_before_merge_{timestamp}.db'
        shutil.copy2(self.current_db, backup_path)
        logger.info(f"✅ Sauvegarde créée: {backup_path}")
        return backup_path

    def analyze_databases(self):
        """Analyse des deux bases de données"""
        logger.info("🔍 ANALYSE DES BASES DE DONNÉES")
        
        # Base actuelle
        conn_current = sqlite3.connect(self.current_db)
        cursor_current = conn_current.cursor()
        
        cursor_current.execute("SELECT COUNT(*) FROM shops")
        current_shops = cursor_current.fetchone()[0]
        
        cursor_current.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = 'completed'")
        current_completed = cursor_current.fetchone()[0]
        
        cursor_current.execute("SELECT COUNT(*) FROM analytics WHERE organic_traffic IS NOT NULL AND organic_traffic != 'N/A' AND organic_traffic != ''")
        current_organic = cursor_current.fetchone()[0]
        
        conn_current.close()
        
        # Base backup
        conn_backup = sqlite3.connect(self.backup_db)
        cursor_backup = conn_backup.cursor()
        
        cursor_backup.execute("SELECT COUNT(*) FROM shops")
        backup_shops = cursor_backup.fetchone()[0]
        
        cursor_backup.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = 'completed'")
        backup_completed = cursor_backup.fetchone()[0]
        
        cursor_backup.execute("SELECT COUNT(*) FROM analytics WHERE organic_traffic IS NOT NULL AND organic_traffic != 'N/A' AND organic_traffic != ''")
        backup_organic = cursor_backup.fetchone()[0]
        
        conn_backup.close()
        
        logger.info(f"📊 BASE ACTUELLE:")
        logger.info(f"   - Shops: {current_shops}")
        logger.info(f"   - Completed: {current_completed}")
        logger.info(f"   - Organic Traffic: {current_organic}")
        
        logger.info(f"📊 BASE BACKUP (28 août):")
        logger.info(f"   - Shops: {backup_shops}")
        logger.info(f"   - Completed: {backup_completed}")
        logger.info(f"   - Organic Traffic: {backup_organic}")
        
        return {
            'current': {'shops': current_shops, 'completed': current_completed, 'organic': current_organic},
            'backup': {'shops': backup_shops, 'completed': backup_completed, 'organic': backup_organic}
        }

    def merge_shops_data(self):
        """Merge des données de la table shops"""
        logger.info("🔄 MERGE DES DONNÉES SHOPS")
        
        conn_current = sqlite3.connect(self.current_db)
        conn_backup = sqlite3.connect(self.backup_db)
        
        cursor_current = conn_current.cursor()
        cursor_backup = conn_backup.cursor()
        
        # Récupérer toutes les shops du backup
        cursor_backup.execute("""
            SELECT id, shop_url, shop_name, scraping_status, creation_date, updated_at
            FROM shops
        """)
        backup_shops = cursor_backup.fetchall()
        
        for shop_id, shop_url, shop_name, scraping_status, creation_date, updated_at in backup_shops:
            # Vérifier si la shop existe dans la base actuelle
            cursor_current.execute("SELECT id, scraping_status FROM shops WHERE shop_url = ?", (shop_url,))
            existing_shop = cursor_current.fetchone()
            
            if existing_shop:
                current_id, current_status = existing_shop
                # Si la shop existe, on garde la version actuelle sauf si elle est moins complète
                if current_status == 'completed' and scraping_status != 'completed':
                    # Garder la version actuelle (completed)
                    self.stats['shops_preserved'] += 1
                    logger.debug(f"   ✅ Shop préservée: {shop_url} (status: {current_status})")
                elif current_status != 'completed' and scraping_status == 'completed':
                    # Mettre à jour avec la version du backup (completed)
                    cursor_current.execute("""
                        UPDATE shops 
                        SET scraping_status = ?, updated_at = ?
                        WHERE id = ?
                    """, (scraping_status, updated_at, current_id))
                    self.stats['shops_updated'] += 1
                    logger.info(f"   🔄 Shop mise à jour: {shop_url} (status: {scraping_status})")
                else:
                    # Garder la version actuelle
                    self.stats['shops_preserved'] += 1
            else:
                # Shop n'existe pas, l'ajouter
                cursor_current.execute("""
                    INSERT INTO shops (shop_url, shop_name, scraping_status, creation_date, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (shop_url, shop_name, scraping_status, creation_date, updated_at))
                self.stats['shops_updated'] += 1
                logger.info(f"   ➕ Shop ajoutée: {shop_url}")
        
        conn_current.commit()
        conn_current.close()
        conn_backup.close()

    def merge_analytics_data(self):
        """Merge des données de la table analytics"""
        logger.info("🔄 MERGE DES DONNÉES ANALYTICS")
        
        conn_current = sqlite3.connect(self.current_db)
        conn_backup = sqlite3.connect(self.backup_db)
        
        cursor_current = conn_current.cursor()
        cursor_backup = conn_backup.cursor()
        
        # Récupérer toutes les analytics du backup
        cursor_backup.execute("""
            SELECT shop_id, organic_traffic, bounce_rate, avg_visit_duration, 
                   branded_traffic, conversion_rate, scraping_status, updated_at, 
                   visits, traffic, percent_branded_traffic
            FROM analytics
        """)
        backup_analytics = cursor_backup.fetchall()
        
        for (shop_id, organic_traffic, bounce_rate, avg_visit_duration, 
             branded_traffic, conversion_rate, scraping_status, updated_at, 
             visits, traffic, percent_branded_traffic) in backup_analytics:
            
            # Vérifier si l'analytics existe dans la base actuelle
            cursor_current.execute("SELECT shop_id FROM analytics WHERE shop_id = ?", (shop_id,))
            existing_analytics = cursor_current.fetchone()
            
            if existing_analytics:
                # Analytics existe, vérifier si on doit mettre à jour
                cursor_current.execute("""
                    SELECT organic_traffic, bounce_rate, avg_visit_duration, 
                           branded_traffic, conversion_rate, paid_search_traffic
                    FROM analytics WHERE shop_id = ?
                """, (shop_id,))
                current_data = cursor_current.fetchone()
                
                if current_data:
                    current_organic, current_bounce, current_duration, current_branded, current_conversion, current_paid = current_data
                    
                    # Vérifier si les données actuelles sont vides ou moins complètes
                    should_update = False
                    
                    # Si organic_traffic est vide dans la base actuelle mais pas dans le backup
                    if (not current_organic or current_organic == 'N/A' or current_organic == '') and organic_traffic:
                        should_update = True
                    
                    # Si bounce_rate est vide dans la base actuelle mais pas dans le backup
                    if (not current_bounce or current_bounce == 'N/A' or current_bounce == '') and bounce_rate:
                        should_update = True
                    
                    # Si avg_visit_duration est vide dans la base actuelle mais pas dans le backup
                    if (not current_duration or current_duration == 'N/A' or current_duration == '') and avg_visit_duration:
                        should_update = True
                    
                    if should_update:
                        # Mettre à jour avec les données du backup, en gardant paid_search_traffic
                        cursor_current.execute("""
                            UPDATE analytics 
                            SET organic_traffic = ?, bounce_rate = ?, avg_visit_duration = ?,
                                branded_traffic = ?, conversion_rate = ?, updated_at = ?,
                                visits = ?, traffic = ?, percent_branded_traffic = ?
                            WHERE shop_id = ?
                        """, (organic_traffic, bounce_rate, avg_visit_duration, 
                              branded_traffic, conversion_rate, updated_at,
                              visits, traffic, percent_branded_traffic, shop_id))
                        self.stats['analytics_updated'] += 1
                        logger.info(f"   🔄 Analytics mises à jour pour shop_id: {shop_id}")
                    else:
                        self.stats['analytics_preserved'] += 1
                        logger.debug(f"   ✅ Analytics préservées pour shop_id: {shop_id}")
            else:
                # Analytics n'existe pas, l'ajouter (sans paid_search_traffic pour l'instant)
                cursor_current.execute("""
                    INSERT INTO analytics (shop_id, organic_traffic, bounce_rate, avg_visit_duration,
                                         branded_traffic, conversion_rate, scraping_status, updated_at,
                                         visits, traffic, percent_branded_traffic, paid_search_traffic)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """, (shop_id, organic_traffic, bounce_rate, avg_visit_duration,
                      branded_traffic, conversion_rate, scraping_status, updated_at,
                      visits, traffic, percent_branded_traffic))
                self.stats['analytics_updated'] += 1
                logger.info(f"   ➕ Analytics ajoutées pour shop_id: {shop_id}")
        
        conn_current.commit()
        conn_current.close()
        conn_backup.close()

    def verify_merge(self):
        """Vérification du merge"""
        logger.info("🔍 VÉRIFICATION DU MERGE")
        
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        
        # Statistiques finales
        cursor.execute("SELECT COUNT(*) FROM shops")
        total_shops = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = 'completed'")
        completed_shops = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE organic_traffic IS NOT NULL AND organic_traffic != 'N/A' AND organic_traffic != ''")
        organic_traffic = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE paid_search_traffic IS NOT NULL AND paid_search_traffic != 'N/A' AND paid_search_traffic != ''")
        paid_search = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"📊 RÉSULTATS FINAUX:")
        logger.info(f"   - Total Shops: {total_shops}")
        logger.info(f"   - Completed Shops: {completed_shops}")
        logger.info(f"   - Organic Traffic: {organic_traffic}")
        logger.info(f"   - Paid Search: {paid_search}")
        
        return {
            'total_shops': total_shops,
            'completed_shops': completed_shops,
            'organic_traffic': organic_traffic,
            'paid_search': paid_search
        }

    def print_summary(self):
        """Affichage du résumé"""
        logger.info("\n" + "="*60)
        logger.info("📊 RÉSUMÉ DU MERGE INTELLIGENT")
        logger.info("="*60)
        logger.info(f"Shops mises à jour: {self.stats['shops_updated']}")
        logger.info(f"Shops préservées: {self.stats['shops_preserved']}")
        logger.info(f"Analytics mises à jour: {self.stats['analytics_updated']}")
        logger.info(f"Analytics préservées: {self.stats['analytics_preserved']}")
        logger.info(f"Erreurs: {self.stats['errors']}")
        logger.info("="*60)

    def run_merge(self):
        """Exécution du merge complet"""
        logger.info("🚀 DÉMARRAGE DU MERGE INTELLIGENT")
        
        try:
            # 1. Sauvegarde
            backup_path = self.backup_current_db()
            
            # 2. Analyse
            analysis = self.analyze_databases()
            
            # 3. Merge shops
            self.merge_shops_data()
            
            # 4. Merge analytics
            self.merge_analytics_data()
            
            # 5. Vérification
            final_stats = self.verify_merge()
            
            # 6. Résumé
            self.print_summary()
            
            logger.info("✅ MERGE TERMINÉ AVEC SUCCÈS!")
            return True
            
        except Exception as e:
            logger.error(f"❌ ERREUR LORS DU MERGE: {e}")
            self.stats['errors'] += 1
            return False

if __name__ == "__main__":
    merger = DatabaseMerger()
    success = merger.run_merge()
    exit(0 if success else 1)
