#!/usr/bin/env python3
"""
Script intelligent pour scraper les métriques manquantes sur toutes les boutiques completed
Réutilise le code existant du single worker
"""

import asyncio
import os
import time
import sqlite3
import logging
from playwright.async_api import async_playwright
import config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/sem-scraper-final/logs/smart_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartScraper:
    def __init__(self):
        self.page = None
        self.browser = None
        self.playwright = None
        
    async def setup_browser(self):
        """Configuration du navigateur - réutilise le code du single worker"""
        logger.info("🔧 Configuration du navigateur...")
        
        # Configuration Xvfb
        logger.info("🖥️ Configuration Xvfb...")
        os.system("Xvfb :107 -screen 0 1920x1080x24 > /dev/null 2>&1 &")
        time.sleep(3)
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas', '--no-first-run', '--no-zygote',
                '--disable-gpu', '--display=:107'
            ]
        )
        
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.set_default_timeout(60000)
        
        logger.info("✅ Navigateur configuré")

    async def authenticate_mytoolsplan(self):
        """Authentification MyToolsPlan - réutilise le code du single worker"""
        logger.info("🔐 Authentification MyToolsPlan...")

        try:
            # Navigation vers la page de login - même méthode que le single worker
            await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
            await self.page.wait_for_load_state('networkidle')

            # Récupérer les credentials
            username, password = config.get_mytoolsplan_credentials()

            # Remplir les champs de login - mêmes sélecteurs que le single worker
            await self.page.fill('input[name="amember_login"]', username)
            await self.page.fill('input[name="amember_pass"]', password)

            # Soumettre le formulaire - même méthode que le single worker
            try:
                await self.page.click('input[type="submit"][class="frm-submit"]')
            except:
                await self.page.evaluate('document.querySelector("form[name=\"login\"]").submit()')

            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # Vérifier que nous sommes sur la page membre
            current_url = self.page.url
            logger.info(f"✅ Login réussi, URL actuelle: {current_url}")

            if "member" not in current_url.lower():
                logger.error("❌ Login échoué - Pas sur la page membre")
                return False

            return True

        except Exception as e:
            error_msg = f"❌ Erreur lors de l'authentification: {e}"
            logger.error(error_msg)
            return False

    def get_missing_metrics(self, shop_id: int) -> dict:
        """Vérifie quelles métriques manquent pour une boutique"""
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                   conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic
            FROM analytics 
            WHERE shop_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (shop_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # Aucune donnée analytics, tout scraper
            return {
                'organic_traffic': True,
                'bounce_rate': True,
                'avg_visit_duration': True,
                'branded_traffic': True,
                'conversion_rate': True,
                'paid_search_traffic': True,
                'visits': True,
                'traffic': True,
                'percent_branded_traffic': True
            }
        
        # Vérifier quelles métriques manquent
        missing = {}
        metrics = ['organic_traffic', 'bounce_rate', 'avg_visit_duration', 'branded_traffic', 
                  'conversion_rate', 'paid_search_traffic', 'visits', 'traffic', 'percent_branded_traffic']
        
        for i, metric in enumerate(metrics):
            value = row[i]
            missing[metric] = (value is None or value == '' or value == 'null' or 
                             value == 'Sélecteur non trouvé|Erreur' or 'Erreur:' in str(value))
        
        return missing

    async def scrape_domain_overview(self, domain: str, shop_id: int):
        """Scraping du Domain Overview - réutilise le code du single worker"""
        logger.info(f"📊 Scraping Domain Overview pour {domain}")
        
        try:
            # Navigation vers Domain Overview - même URL que le single worker
            overview_url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q={domain}&date=202506"
            await self.page.goto(overview_url, wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Vérifier le titre de la page
            title = await self.page.title()
            logger.info(f"🔍 Titre de la page: {title}")
            
            # Attendre le chargement des métriques
            await self.page.wait_for_selector('div[data-at="do-summary-pt"]', timeout=10000)
            await asyncio.sleep(2)
            
            # Récupérer les métriques manquantes
            missing_metrics = self.get_missing_metrics(shop_id)
            metrics_to_scrape = {k: v for k, v in missing_metrics.items() if v}
            
            if not metrics_to_scrape:
                logger.info(f"✅ Toutes les métriques existent déjà pour {domain}")
                return
            
            logger.info(f"📊 Métriques à scraper: {list(metrics_to_scrape.keys())}")
            
            # Scraper les métriques manquantes
            scraped_metrics = {}
            
            # Organic Search Traffic
            if metrics_to_scrape.get('organic_traffic'):
                element = await self.page.query_selector('div[data-at="do-summary-ot"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                if element:
                    organic_traffic = await element.inner_text()
                    organic_traffic_clean = organic_traffic.strip().lower()
                    if organic_traffic_clean and organic_traffic_clean.endswith(('k', 'm')):
                        scraped_metrics['organic_traffic'] = organic_traffic
                        logger.info(f"✅ Organic Search Traffic: {organic_traffic}")
                    else:
                        scraped_metrics['organic_traffic'] = "na"
                        logger.warning(f"⚠️ Organic traffic invalide: '{organic_traffic}' - marqué comme 'na'")
                else:
                    scraped_metrics['organic_traffic'] = "Sélecteur non trouvé|Erreur"
                    logger.warning("❌ Sélecteur Organic Search Traffic non trouvé")
            
            # Paid Search Traffic
            if metrics_to_scrape.get('paid_search_traffic'):
                element = await self.page.query_selector('div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                if element:
                    paid_traffic = await element.inner_text()
                    paid_traffic_clean = paid_traffic.strip().lower()
                    if paid_traffic_clean and paid_traffic_clean.endswith(('k', 'm')):
                        scraped_metrics['paid_search_traffic'] = paid_traffic
                        logger.info(f"✅ Paid Search Traffic: {paid_traffic}")
                    else:
                        scraped_metrics['paid_search_traffic'] = "na"
                        logger.warning(f"⚠️ Paid traffic invalide: '{paid_traffic}' - marqué comme 'na'")
                else:
                    scraped_metrics['paid_search_traffic'] = "Sélecteur non trouvé|Erreur"
                    logger.warning("❌ Sélecteur Paid Search Traffic non trouvé")
            
            # Average Visit Duration
            if metrics_to_scrape.get('avg_visit_duration'):
                element = await self.page.query_selector('div[data-at="do-summary-avd"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                if element:
                    avg_duration = await element.inner_text()
                    scraped_metrics['avg_visit_duration'] = avg_duration
                    logger.info(f"✅ Average Visit Duration: {avg_duration}")
                else:
                    scraped_metrics['avg_visit_duration'] = "Sélecteur non trouvé|Erreur"
                    logger.warning("❌ Sélecteur Average Visit Duration non trouvé")
            
            # Bounce Rate
            if metrics_to_scrape.get('bounce_rate'):
                element = await self.page.query_selector('div[data-at="do-summary-br"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                if element:
                    bounce_rate = await element.inner_text()
                    scraped_metrics['bounce_rate'] = bounce_rate
                    logger.info(f"✅ Bounce Rate: {bounce_rate}")
                else:
                    scraped_metrics['bounce_rate'] = "Sélecteur non trouvé|Erreur"
                    logger.warning("❌ Sélecteur Bounce Rate non trouvé")
            
            # Mettre à jour la base de données avec les nouvelles métriques
            if scraped_metrics:
                self.update_analytics(shop_id, scraped_metrics)
                logger.info(f"💾 Analytics mis à jour pour shop_id {shop_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping Domain Overview pour {domain}: {e}")
            
            # En cas d'erreur, marquer les métriques manquantes comme "na"
            missing_metrics = self.get_missing_metrics(shop_id)
            error_metrics = {}
            
            for metric, is_missing in missing_metrics.items():
                if is_missing:
                    if "timeout" in str(e).lower():
                        error_metrics[metric] = "na"
                    else:
                        error_metrics[metric] = "Sélecteur non trouvé|Erreur"
            
            if error_metrics:
                self.update_analytics(shop_id, error_metrics)
                logger.info(f"💾 Analytics mis à jour avec valeurs d'erreur pour shop_id {shop_id}")

    def update_analytics(self, shop_id: int, new_metrics: dict):
        """Met à jour les analytics avec les nouvelles métriques"""
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        
        # Récupérer les métriques existantes
        cursor.execute("""
            SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                   conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic
            FROM analytics 
            WHERE shop_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (shop_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Fusionner avec les métriques existantes
            metrics = list(existing)
            metric_names = ['organic_traffic', 'bounce_rate', 'avg_visit_duration', 'branded_traffic', 
                          'conversion_rate', 'paid_search_traffic', 'visits', 'traffic', 'percent_branded_traffic']
            
            for i, metric_name in enumerate(metric_names):
                if metric_name in new_metrics:
                    metrics[i] = new_metrics[metric_name]
            
            # Mettre à jour
            cursor.execute("""
                INSERT OR REPLACE INTO analytics 
                (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                 conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, 
                 scraping_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (shop_id, *metrics, 'partial'))
        else:
            # Créer une nouvelle entrée
            metrics = [''] * 9  # 9 métriques
            metric_names = ['organic_traffic', 'bounce_rate', 'avg_visit_duration', 'branded_traffic', 
                          'conversion_rate', 'paid_search_traffic', 'visits', 'traffic', 'percent_branded_traffic']
            
            for i, metric_name in enumerate(metric_names):
                if metric_name in new_metrics:
                    metrics[i] = new_metrics[metric_name]
            
            cursor.execute("""
                INSERT INTO analytics 
                (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                 conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, 
                 scraping_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (shop_id, *metrics, 'partial'))
        
        conn.commit()
        conn.close()

    async def run(self):
        """Exécution principale du scraper intelligent"""
        logger.info("🚀 DÉMARRAGE SCRAPER INTELLIGENT")
        logger.info("=" * 50)
        
        try:
            # Configuration du navigateur
            await self.setup_browser()
            
            # Authentification
            if not await self.authenticate_mytoolsplan():
                logger.error("❌ Échec de l'authentification")
                return
            
            # Récupérer toutes les boutiques completed
            logger.info("📊 Récupération des boutiques completed...")
            conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, shop_url 
                FROM shops 
                WHERE scraping_status = 'completed'
                ORDER BY id
            """)
            
            shops = cursor.fetchall()
            conn.close()
            
            logger.info(f"📦 {len(shops)} boutiques completed trouvées")
            
            if not shops:
                logger.info("✅ Aucune boutique completed à traiter")
                return
            
            # Traiter chaque boutique
            for i, (shop_id, shop_url) in enumerate(shops, 1):
                logger.info(f"\n📦 Progression: {i}/{len(shops)} - {shop_url}")
                
                try:
                    # Extraire le domaine
                    domain = shop_url.replace('https://', '').replace('http://', '').split('/')[0]
                    
                    # Scraper les métriques manquantes
                    await self.scrape_domain_overview(domain, shop_id)
                    
                    # Pause entre les requêtes
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur pour {shop_url}: {e}")
            
            await self.browser.close()
            logger.info("\n🎉 Scraping intelligent terminé !")
            
        except Exception as e:
            logger.error(f"❌ Erreur générale: {e}")

async def main():
    scraper = SmartScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
