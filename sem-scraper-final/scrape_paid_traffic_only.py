#!/usr/bin/env python3
"""
Script spécialisé pour scraper uniquement le Paid Search Traffic
sur les boutiques qui n'en ont pas encore
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

# Configuration du logging
def setup_logging():
    """Configure le logging pour le scraper"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = log_dir / f'paid-traffic-only-{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class PaidTrafficScraper:
    """Scraper spécialisé pour le Paid Search Traffic uniquement"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.logger = setup_logging()
        
    async def setup_browser(self):
        """Configure le navigateur Playwright"""
        self.logger.info("🔧 Configuration du navigateur...")
        
        # Configuration Xvfb pour VPS
        self.logger.info("🖥️ Configuration Xvfb...")
        os.system("Xvfb :101 -screen 0 1920x1080x24 > /dev/null 2>&1 &")
        time.sleep(2)
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--display=:101'
            ]
        )
        
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Configuration des timeouts
        self.page.set_default_timeout(60000)
        self.page.set_default_navigation_timeout(60000)
        
        self.logger.info("✅ Navigateur configuré")
        
    async def login_mytoolsplan(self):
        """Authentification MyToolsPlan"""
        self.logger.info("🔐 Authentification MyToolsPlan...")
        
        try:
            await self.page.goto("https://app.mytoolsplan.com/login")
            await self.page.wait_for_load_state("networkidle")
            
            # Remplir les credentials
            await self.page.fill('input[name="amember_login"]', config.MYTOOLSPLAN_USERNAME)
            await self.page.fill('input[name="amember_pass"]', config.MYTOOLSPLAN_PASSWORD)
            
            # Cliquer sur le bouton de connexion
            await self.page.click('input[type="submit"][class="frm-submit"]')
            
            # Attendre la redirection
            await self.page.wait_for_url("**/member", timeout=30000)
            
            current_url = self.page.url
            self.logger.info(f"✅ Login réussi, URL actuelle: {current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du login: {e}")
            return False
    
    async def scrape_paid_traffic_only(self, domain: str) -> Optional[str]:
        """Scrape uniquement le Paid Search Traffic pour un domaine"""
        try:
            # Aller sur la page Domain Overview
            url = f"https://app.mytoolsplan.com/domain-overview/{domain}"
            await self.page.goto(url)
            await self.page.wait_for_load_state("networkidle")
            
            # Vérifier le titre de la page
            title = await self.page.title()
            self.logger.info(f"🔍 DEBUG - Titre de la page: {title}")
            
            if "Domain Overview" not in title:
                self.logger.warning(f"⚠️ Page non reconnue pour {domain}")
                return None
            
            # Attendre le chargement des métriques
            self.logger.info("⏳ Attente du chargement des métriques...")
            await self.page.wait_for_timeout(1000)
            
            # Vérifier si les métriques sont chargées
            try:
                await self.page.wait_for_selector('div[data-at="do-summary-pt"]', timeout=10000)
                self.logger.info("✅ Métriques chargées")
            except:
                self.logger.warning("⚠️ Métriques non trouvées")
                return None
            
            # Scraper uniquement le Paid Search Traffic
            try:
                paid_traffic_element = await self.page.query_selector('div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                
                if paid_traffic_element:
                    paid_traffic_text = await paid_traffic_element.text_content()
                    paid_traffic_text = paid_traffic_text.strip() if paid_traffic_text else ""
                    
                    # Validation : doit contenir 'K' ou 'M'
                    if paid_traffic_text and ('K' in paid_traffic_text or 'M' in paid_traffic_text):
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
    
    def get_shops_without_paid_traffic(self) -> List[Dict]:
        """Récupère les boutiques completed qui n'ont pas de paid_search_traffic"""
        try:
            conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
            cursor = conn.cursor()
            
            # Récupérer les boutiques completed sans paid_search_traffic
            cursor.execute("""
                SELECT s.id, s.shop_name, s.shop_url, a.paid_search_traffic 
                FROM shops s 
                LEFT JOIN analytics a ON s.id = a.shop_id 
                WHERE s.scraping_status = 'completed'
                  AND (a.paid_search_traffic IS NULL 
                       OR a.paid_search_traffic = '' 
                       OR a.paid_search_traffic = 'null'
                       OR a.id IS NULL)
                ORDER BY s.id
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
            self.logger.error(f"❌ Erreur récupération shops sans paid traffic: {e}")
            return []
    
    def update_paid_traffic(self, shop_id: int, paid_traffic: str) -> bool:
        """Met à jour uniquement le paid_search_traffic dans la base"""
        try:
            conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
            cursor = conn.cursor()
            
            # Vérifier si l'entrée analytics existe
            cursor.execute("SELECT id FROM analytics WHERE shop_id = ?", (shop_id,))
            result = cursor.fetchone()
            
            if result:
                # Mettre à jour l'entrée existante
                cursor.execute("""
                    UPDATE analytics 
                    SET paid_search_traffic = ?, updated_at = ? 
                    WHERE shop_id = ?
                """, (paid_traffic, datetime.now(timezone.utc), shop_id))
            else:
                # Créer une nouvelle entrée
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
        """Lance le scraping du Paid Search Traffic uniquement"""
        try:
            self.logger.info("🚀 DÉMARRAGE SCRAPER PAID SEARCH TRAFFIC UNIQUEMENT")
            
            # Configuration du navigateur
            await self.setup_browser()
            
            # Authentification
            if not await self.login_mytoolsplan():
                self.logger.error("❌ Échec de l'authentification")
                return
            
            # Récupérer les boutiques sans paid_search_traffic
            shops = self.get_shops_without_paid_traffic()
            self.logger.info(f"📊 {len(shops)} boutiques sans Paid Search Traffic trouvées")
            
            if not shops:
                self.logger.info("✅ Toutes les boutiques ont déjà un Paid Search Traffic")
                return
            
            # Traitement des boutiques
            success_count = 0
            total_count = len(shops)
            
            for i, shop in enumerate(shops, 1):
                self.logger.info(f"📦 Progression: {i}/{total_count}")
                self.logger.info(f"🚀 TRAITEMENT: {shop['domain']}")
                
                start_time = time.time()
                
                # Scraper le Paid Search Traffic
                paid_traffic = await self.scrape_paid_traffic_only(shop['domain'])
                
                if paid_traffic is not None:
                    # Mettre à jour la base
                    if self.update_paid_traffic(shop['id'], paid_traffic):
                        success_count += 1
                
                # Temps de traitement
                processing_time = time.time() - start_time
                self.logger.info(f"⏱️ Temps de traitement: {processing_time:.2f}s")
                
                # Pause entre les requêtes
                await asyncio.sleep(2)
            
            # Résumé final
            self.logger.info(f"🎉 SCRAPING TERMINÉ")
            self.logger.info(f"📊 Résultats: {success_count}/{total_count} boutiques mises à jour")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur générale: {e}")
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """Fonction principale"""
    scraper = PaidTrafficScraper()
    await scraper.run()

if __name__ == "__main__":
    from pathlib import Path
    asyncio.run(main())
