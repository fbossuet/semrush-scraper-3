#!/usr/bin/env python3
"""
Scraper Intelligent Simplifié - Version de Test
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import config
from playwright.async_api import async_playwright
from trendtrack_api import api

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_smart_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleSmartScraper:
    """
    Scraper intelligent simplifié pour tester la connexion
    """
    
    def __init__(self):
        self.performance_timers = {
            'start_time': time.time(),
            'shops_processed': 0,
            'shops_success': 0,
            'shops_failed': 0
        }
        
    async def run(self):
        """Point d'entrée principal"""
        logger.info("🚀 DÉMARRAGE DU SCRAPER INTELLIGENT SIMPLIFIÉ")
        logger.info("=" * 60)
        
        try:
            async with async_playwright() as playwright:
                # Configuration du navigateur
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
                )
                
                # Création du contexte
                context = await browser.new_context()
                page = await context.new_page()
                
                # Test de connexion
                if await self.test_connection(page):
                    logger.info("✅ Connexion réussie - Test de scraping d'une boutique")
                    
                    # Récupérer une boutique de test
                    test_shop = await self.get_test_shop()
                    if test_shop:
                        await self.test_scrape_shop(page, test_shop)
                    else:
                        logger.info("ℹ️ Aucune boutique de test disponible")
                else:
                    logger.error("❌ Échec de la connexion - Arrêt du scraper")
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"🚨 Erreur critique: {e}")
            raise
    
    async def test_connection(self, page) -> bool:
        """Test de la connexion à MyToolsPlan"""
        try:
            logger.info("🔐 Test de connexion en cours...")
            
            # Essayer différentes URLs de connexion
            login_urls = [
                config.MYTOOLSPLAN_LOGIN_URL,
                "https://app.mytoolsplan.com/login",
                "https://app.mytoolsplan.com/signin",
                "https://app.mytoolsplan.com/auth"
            ]
            
            for url in login_urls:
                logger.info(f"🌐 Test de l'URL: {url}")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(5)
                    
                    # Vérifier si la page contient des éléments de connexion
                    page_content = await page.content()
                    
                    if len(page_content) > 1000:  # Page chargée
                        logger.info(f"✅ Page chargée: {page.url}")
                        logger.info(f"📄 Taille du contenu: {len(page_content)} caractères")
                        
                        # Chercher des éléments de connexion
                        inputs = await page.query_selector_all('input')
                        buttons = await page.query_selector_all('button')
                        forms = await page.query_selector_all('form')
                        
                        logger.info(f"🔍 Éléments trouvés: {len(inputs)} inputs, {len(buttons)} boutons, {len(forms)} formulaires")
                        
                        if inputs or buttons or forms:
                            logger.info("✅ Éléments de connexion détectés")
                            
                            # Essayer de se connecter
                            if await self.attempt_login(page):
                                logger.info("✅ Connexion réussie!")
                                return True
                            else:
                                logger.warning("⚠️ Connexion échouée, essai de l'URL suivante")
                        else:
                            logger.warning("⚠️ Aucun élément de connexion trouvé, essai de l'URL suivante")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur avec l'URL {url}: {e}")
                    continue
            
            logger.error("❌ Aucune URL de connexion n'a fonctionné")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de connexion: {e}")
            return False
    
    async def attempt_login(self, page) -> bool:
        """Tente de se connecter"""
        try:
            logger.info("🔐 Tentative de connexion...")
            
            # Attendre que la page soit complètement chargée
            await asyncio.sleep(3)
            
            # Essayer différents sélecteurs pour l'email/username
            email_selectors = [
                'input[name="email"]',
                'input[name="username"]',
                'input[type="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]',
                'input[id*="email" i]',
                'input[id*="username" i]',
                'input[class*="email" i]',
                'input[class*="username" i]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        logger.info(f"✅ Champ email trouvé: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                logger.error("❌ Aucun champ email trouvé")
                return False
            
            # Essayer différents sélecteurs pour le mot de passe
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                'input[id*="password" i]',
                'input[class*="password" i]'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        logger.info(f"✅ Champ mot de passe trouvé: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                logger.error("❌ Aucun champ mot de passe trouvé")
                return False
            
            # Saisir les identifiants
            await email_input.fill(config.MYTOOLSPLAN_USERNAME)
            await password_input.fill(config.MYTOOLSPLAN_PASSWORD)
            
            logger.info("✅ Identifiants saisis")
            
            # Essayer différents sélecteurs pour le bouton de connexion
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Connexion")',
                'input[type="submit"]',
                'button[class*="login" i]',
                'button[class*="submit" i]'
            ]
            
            login_button = None
            for selector in button_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        logger.info(f"✅ Bouton de connexion trouvé: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                logger.error("❌ Aucun bouton de connexion trouvé")
                return False
            
            # Cliquer sur le bouton de connexion
            await login_button.click()
            logger.info("✅ Bouton de connexion cliqué")
            
            # Attendre la redirection
            await asyncio.sleep(5)
            
            # Vérifier si on est connecté
            current_url = page.url
            if "dashboard" in current_url or "projects" in current_url or "app" in current_url:
                logger.info(f"✅ Connexion réussie! URL actuelle: {current_url}")
                return True
            else:
                logger.warning(f"⚠️ Connexion échouée, URL actuelle: {current_url}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la tentative de connexion: {e}")
            return False
    
    async def get_test_shop(self) -> Optional[Dict]:
        """Récupère une boutique de test"""
        try:
            all_shops = api.get_all_shops_with_analytics()
            if all_shops:
                # Prendre la première boutique avec des métriques manquantes
                for shop in all_shops:
                    if self.has_missing_metrics(shop):
                        logger.info(f"✅ Boutique de test trouvée: {shop['shop_name']}")
                        return shop
            
            logger.warning("⚠️ Aucune boutique de test disponible")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de la boutique de test: {e}")
            return None
    
    def has_missing_metrics(self, shop: Dict) -> bool:
        """Vérifie si une boutique a des métriques manquantes"""
        required_metrics = [
            'organic_traffic', 'bounce_rate', 'avg_visit_duration',
            'branded_traffic', 'conversion_rate', 'paid_search_traffic'
        ]
        
        for metric in required_metrics:
            metric_value = shop.get(metric)
            if (metric_value is None or 
                metric_value == "" or 
                metric_value == "na" or
                "Sélecteur non trouvé" in str(metric_value) or
                "Erreur" in str(metric_value)):
                return True
        
        return False
    
    async def test_scrape_shop(self, page, shop: Dict):
        """Test de scraping d'une boutique"""
        try:
            logger.info(f"🧪 Test de scraping pour: {shop['shop_name']}")
            
            # Navigation vers la boutique
            await page.goto(shop['shop_url'], wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)
            
            logger.info(f"✅ Page de la boutique chargée: {page.url}")
            
            # Test simple : vérifier si la page contient des métriques
            page_content = await page.content()
            logger.info(f"📄 Contenu de la page: {len(page_content)} caractères")
            
            # Chercher des éléments de métriques
            metric_elements = await page.query_selector_all('[class*="metric"], [class*="traffic"], [class*="rate"]')
            logger.info(f"🔍 Éléments de métriques trouvés: {len(metric_elements)}")
            
            if metric_elements:
                logger.info("✅ Éléments de métriques détectés - Scraping possible!")
            else:
                logger.warning("⚠️ Aucun élément de métrique détecté")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de scraping: {e}")

async def main():
    """Fonction principale"""
    scraper = SimpleSmartScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
