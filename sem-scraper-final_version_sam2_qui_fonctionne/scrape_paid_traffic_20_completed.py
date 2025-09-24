#!/usr/bin/env python3
"""
Script pour scraper le Paid Search Traffic sur 20 boutiques completed seulement
"""

import asyncio
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import config
from playwright.async_api import async_playwright

def setup_logging():
    from pathlib import Path
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = log_dir / f'paid-traffic-20-completed-{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class PaidTraffic20CompletedScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.logger = setup_logging()
        
    async def setup_browser(self):
        self.logger.info("🔧 Configuration du navigateur...")
        os.system("Xvfb :103 -screen 0 1920x1080x24 > /dev/null 2>&1 &")
        time.sleep(2)
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas', '--no-first-run', '--no-zygote',
                '--disable-gpu', '--display=:103'
            ]
        )
        
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.set_default_timeout(60000)
        self.page.set_default_navigation_timeout(60000)
        
        self.logger.info("✅ Navigateur configuré")
        
    async def login_mytoolsplan(self):
        self.logger.info("🔐 Authentification MyToolsPlan...")
        
        try:
            await self.page.goto("https://app.mytoolsplan.com/login")
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)
            
            current_url = self.page.url
            if "member" in current_url:
                self.logger.info(f"✅ Déjà connecté, URL actuelle: {current_url}")
                return True
            
            self.logger.info(f"🔍 URL actuelle: {current_url}")
            self.logger.info("⏳ Attente du formulaire de login...")
            
            await self.page.wait_for_selector('input[name="email"]', timeout=30000)
            self.logger.info("✅ Formulaire de login trouvé")
            
            await self.page.fill('input[name="email"]', config.MYTOOLSPLAN_USERNAME)
            await self.page.fill('input[name="password"]', config.MYTOOLSPLAN_PASSWORD)
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_url("**/member", timeout=30000)
            
            current_url = self.page.url
            self.logger.info(f"✅ Login réussi, URL actuelle: {current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du login: {e}")
            return False
    
    async def scrape_paid_traffic_only(self, domain: str) -> Optional[str]:
        try:
            url = f"https://app.mytoolsplan.com/domain-overview/{domain}"
            await self.page.goto(url)
            await self.page.wait_for_load_state("networkidle")
            
            title = await self.page.title()
            self.logger.info(f"🔍 DEBUG - Titre de la page: {title}")
            
            if "Domain Overview" not in title:
                self.logger.warning(f"⚠️ Page non reconnue pour {domain}")
                return None
            
            self.logger.info("⏳ Attente du chargement des métriques...")
            await self.page.wait_for_timeout(1000)
            
            try:
                await self.page.wait_for_selector('div[data-at="do-summary-pt"]', timeout=10000)
                self.logger.info("✅ Métriques chargées")
            except:
                self.logger.warning("⚠️ Métriques non trouvées")
                return None
            
            try:
                paid_traffic_element = await self.page.query_selector('div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                
                if paid_traffic_element:
                    paid_traffic_text = await paid_traffic_element.text_content()
                    paid_traffic_text = paid_traffic_text.strip() if paid_traffic_text else ""
                    
                    if paid_traffic_text and paid_traffic_text.lower().endswith(('k', 'm')):
                        self.logger.info(f"✅ Paid Search Traffic: {paid_traffic_text}")
                        return paid_traffic_text
                    else:
                        self.logger.warning(f"⚠️ Paid traffic invalide: '{paid_traffic_text}' - marqué comme 'na'")
                        return "na"
                else:
                    self.logger.warning("⚠️ Sélecteur Paid Search Traffic non trouvé")
                    return "na"
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur lors du scraping Paid Search Traffic: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du scraping Domain Overview: {e}")
            return None
    
    def get_20_completed_shops(self) -> List[Dict]:
        try:
            conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT s.id, s.shop_name, s.shop_url, a.paid_search_traffic 
                FROM shops s 
                LEFT JOIN analytics a ON s.id = a.shop_id 
                WHERE s.scraping_status = 'completed'
                  AND (a.paid_search_traffic IS NULL 
                       OR a.paid_search_traffic = '' 
                       OR a.paid_search_traffic = 'null'
                       OR a.id IS NULL)
                ORDER BY s.id
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            shops = []
            
            for row in results:
                shop_id, shop_name, shop_url, paid_traffic = row
                domain = shop_url.replace('https://', '').replace('http://', '').rstrip('/')
                shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'url': shop_url,
                    'domain': domain,
                    'current_paid_traffic': paid_traffic
                })
            
            conn.close()
            return shops
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération 20 shops completed: {e}")
            return []
    
    def update_paid_traffic(self, shop_id: int, paid_traffic: str) -> bool:
        try:
            conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM analytics WHERE shop_id = ?", (shop_id,))
            result = cursor.fetchone()
            
            if result:
                cursor.execute("""
                    UPDATE analytics 
                    SET paid_search_traffic = ?, updated_at = ? 
                    WHERE shop_id = ?
                """, (paid_traffic, datetime.now(timezone.utc), shop_id))
            else:
                cursor.execute("""
                    INSERT INTO analytics (shop_id, paid_search_traffic, updated_at)
                    VALUES (?, ?, ?)
                """, (shop_id, paid_traffic, datetime.now(timezone.utc)))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Paid Search Traffic mis à jour pour shop_id {shop_id}: {paid_traffic}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur mise à jour paid traffic pour shop_id {shop_id}: {e}")
            return False
    
    async def run(self):
        try:
            self.logger.info("🚀 DÉMARRAGE SCRAPER PAID SEARCH TRAFFIC - 20 BOUTIQUES COMPLETED")
            
            await self.setup_browser()
            
            if not await self.login_mytoolsplan():
                self.logger.error("❌ Échec de l'authentification")
                return
            
            shops = self.get_20_completed_shops()
            self.logger.info(f"📊 {len(shops)} boutiques completed trouvées")
            
            if not shops:
                self.logger.info("✅ Aucune boutique completed trouvée")
                return
            
            self.logger.info("📋 BOUTIQUES À TRAITER:")
            for shop in shops:
                self.logger.info(f"   ID {shop['id']}: {shop['domain']}")
            
            success_count = 0
            total_count = len(shops)
            
            for i, shop in enumerate(shops, 1):
                self.logger.info(f"📦 Progression: {i}/{total_count}")
                self.logger.info(f"🚀 TRAITEMENT: {shop['domain']}")
                
                start_time = time.time()
                
                paid_traffic = await self.scrape_paid_traffic_only(shop['domain'])
                
                if paid_traffic is not None:
                    if self.update_paid_traffic(shop['id'], paid_traffic):
                        success_count += 1
                
                processing_time = time.time() - start_time
                self.logger.info(f"⏱️ Temps de traitement: {processing_time:.2f}s")
                
                await asyncio.sleep(2)
            
            self.logger.info(f"🎉 SCRAPING TERMINÉ")
            self.logger.info(f"📊 Résultats: {success_count}/{total_count} boutiques mises à jour")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur générale: {e}")
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    scraper = PaidTraffic20CompletedScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
