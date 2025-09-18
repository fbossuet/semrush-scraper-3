#!/usr/bin/env python3
"""
Script pour re-scraper toutes les métriques de traffic manquantes
Utilise les bons sélecteurs pour récupérer les vraies valeurs
"""

import sqlite3
import logging
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from production_scraper import ProductionScraper

# Charger les variables d'environnement
load_dotenv('config.env.enhanced')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'rescrape_missing_metrics_{datetime.now(timezone.utc).isoformat()}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrafficMetricsRescraper:
    def __init__(self):
        self.db_path = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
        self.scraper = None
        
        # Métriques avec leurs sélecteurs corrects
        self.traffic_metrics = {
            'organic_traffic': {
                'selector': 'div[data-at="do-summary-ot"] a[data-at="main-number"] span[data-ui-name="Link.Text"]',
                'description': 'Organic Traffic'
            },
            'visits': {
                'selector': 'div[data-testid="summary-cell visits"] > div > div > div > span[data-testid="value"][data-ui-name="Text"]',
                'description': 'Visits'
            },
            'traffic': {
                'selector': 'div[data-at="summary-branded-traffic"] > div > div > span[data-at="summary-value"][data-ui-name="Text"]',
                'description': 'Branded Traffic'
            },
            'paid_search_traffic': {
                'selector': 'div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]',
                'description': 'Paid Search Traffic'
            }
        }
        
        self.stats = {
            'total_processed': 0,
            'successfully_updated': 0,
            'failed_to_update': 0
        }

    def validate_traffic_value(self, value):
        """Valide qu'une valeur de traffic se termine par K, M ou B"""
        if not value or value in ['N/A', 'Sélecteur non trouvé', 'Erreur', 'api_not_available']:
            return False
        
        clean_value = str(value).strip().upper()
        return clean_value.endswith('K') or clean_value.endswith('M') or clean_value.endswith('B')

    def get_missing_metrics(self):
        """Récupère tous les enregistrements avec des métriques manquantes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        missing_records = []
        
        # Chercher les enregistrements avec des métriques NULL
        cursor.execute("""
            SELECT a.id, a.shop_id, s.shop_url, a.organic_traffic, a.visits, a.traffic, a.paid_search_traffic
            FROM analytics a
            JOIN shops s ON a.shop_id = s.id
            WHERE (a.organic_traffic IS NULL OR a.organic_traffic = '')
               OR (a.visits IS NULL OR a.visits = '')
               OR (a.traffic IS NULL OR a.traffic = '')
               OR (a.paid_search_traffic IS NULL OR a.paid_search_traffic = '')
        """)
        
        for record in cursor.fetchall():
            record_id, shop_id, shop_url, organic_traffic, visits, traffic, paid_search_traffic = record
            
            missing_fields = []
            
            # Vérifier chaque métrique
            for metric_name, metric_config in self.traffic_metrics.items():
                value = locals()[metric_name]  # organic_traffic, visits, traffic, paid_search_traffic
                if not value or value == '':
                    missing_fields.append({
                        'field': metric_name,
                        'selector': metric_config['selector'],
                        'description': metric_config['description']
                    })
            
            if missing_fields:
                missing_records.append({
                    'id': record_id,
                    'shop_id': shop_id,
                    'shop_url': shop_url,
                    'missing_fields': missing_fields
                })
        
        conn.close()
        return missing_records

    async def setup_browser(self):
        """Configure le navigateur Playwright"""
        self.scraper = ProductionScraper()
        await self.scraper.setup_browser()
        
        # Authentification MyToolsPlan
        auth_success = await self.scraper.authenticate_mytoolsplan()
        if not auth_success:
            raise Exception("Échec de l'authentification")
        logger.info("✅ Authentification réussie")

    async def scrape_metric(self, shop_url, selector, description):
        """Scrape une métrique spécifique pour un domaine"""
        try:
            # Nettoyer l'URL
            clean_domain = shop_url.replace('https://', '').replace('http://', '').replace('www.', '')
            
            # URL de la page analytics (format correct)
            analytics_url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q=https://{clean_domain}&date=202507"
            
            logger.info(f"🌐 Scraping {description} pour {clean_domain}")
            await self.scraper.page.goto(analytics_url, wait_until='domcontentloaded', timeout=30000)
            
            # Attendre que la page se charge
            await self.scraper.page.wait_for_timeout(5000)
            
            # Chercher l'élément
            element = await self.scraper.page.query_selector(selector)
            
            if element:
                value = await element.text_content()
                value = value.strip() if value else None
                
                if value and self.validate_traffic_value(value):
                    logger.info(f"✅ {description}: {value}")
                    return value
                else:
                    logger.warning(f"⚠️ {description}: Valeur invalide récupérée: {value}")
                    return None
            else:
                logger.warning(f"⚠️ {description}: Sélecteur non trouvé")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping {description} pour {shop_url}: {e}")
            return None

    async def rescrape_missing_metrics(self):
        """Re-scrape toutes les métriques manquantes"""
        logger.info("🔍 Recherche des métriques manquantes...")
        missing_records = self.get_missing_metrics()
        
        if not missing_records:
            logger.info("✅ Aucune métrique manquante trouvée !")
            return
        
        logger.info(f"📊 {len(missing_records)} enregistrements avec métriques manquantes trouvés")
        
        # Configuration du navigateur
        await self.setup_browser()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for record in missing_records:
                logger.info(f"\n🔧 Re-scraping de l'enregistrement ID {record['id']} - {record['shop_url']}")
                
                for missing_field in record['missing_fields']:
                    field_name = missing_field['field']
                    selector = missing_field['selector']
                    description = missing_field['description']
                    
                    logger.info(f"   📝 {description}: Re-scraping...")
                    
                    # Re-scraper la métrique
                    new_value = await self.scrape_metric(
                        record['shop_url'], 
                        selector, 
                        description
                    )
                    
                    if new_value:
                        # Mettre à jour en base
                        cursor.execute(f"""
                            UPDATE analytics 
                            SET {field_name} = ?, updated_at = datetime.now(timezone.utc).isoformat()
                            WHERE id = ?
                        """, (new_value, record['id']))
                        
                        logger.info(f"   ✅ {description}: {new_value}")
                        self.stats['successfully_updated'] += 1
                        
                    else:
                        logger.warning(f"   ⚠️ {description}: Impossible à récupérer")
                        self.stats['failed_to_update'] += 1
                
                self.stats['total_processed'] += 1
                
                # Commit après chaque enregistrement
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du re-scraping: {e}")
            conn.rollback()
        finally:
            conn.close()
            if self.scraper:
                await self.scraper.browser.close()

    def print_summary(self):
        """Affiche le résumé des opérations"""
        logger.info("\n" + "="*50)
        logger.info("📊 RÉSUMÉ DU RE-SCRAPING")
        logger.info("="*50)
        logger.info(f"Total d'enregistrements traités: {self.stats['total_processed']}")
        logger.info(f"Métriques mises à jour avec succès: {self.stats['successfully_updated']}")
        logger.info(f"Métriques impossibles à récupérer: {self.stats['failed_to_update']}")
        logger.info("="*50)

async def main():
    rescraper = TrafficMetricsRescraper()
    
    try:
        await rescraper.rescrape_missing_metrics()
        rescraper.print_summary()
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    logger.info("🚀 Démarrage du re-scraping des métriques de traffic manquantes")
    asyncio.run(main())
    logger.info("🏁 Re-scraping terminé")
