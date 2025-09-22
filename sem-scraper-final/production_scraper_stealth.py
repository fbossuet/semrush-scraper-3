#!/usr/bin/env python3
"""
Scraper de production avec protection anti-détection avancée
Basé sur production_scraper_parallel.py mais avec toutes les protections stealth
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3
from api_credentials import get_credentials_dict
from api_client import APIClient
import config
from playwright.async_api import async_playwright
from trendtrack_api_vps_adapted import api

# Imports anti-détection
from anti_detection_config import get_stealth_browser_config, get_stealth_headers
from stealth_injections import apply_stealth_to_page
from stealth_system import stealth_system

# Configuration du logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure le logging"""
    logger = logging.getLogger()
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    # Désactiver les logs de playwright
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class StealthScraper:
    """Scraper avec protection anti-détection avancée"""
    
    def __init__(self, worker_id: int = 0):
        self.worker_id = worker_id
        self.playwright = None
        self.context = None
        self.page = None
        self.api_client = None
        self.session_data = {'data': {}}
        self.stealth_config = get_stealth_browser_config()
        self.stealth_headers = get_stealth_headers()
        
        # Configuration anti-détection
        self.request_delays = {
            'min': 2.0,  # Délai minimum entre requêtes
            'max': 5.0,  # Délai maximum entre requêtes
            'jitter': 0.5  # Variation aléatoire
        }
        
        # Rotation d'identité
        self.identity_rotation_interval = 1800  # 30 minutes
        self.last_identity_rotation = time.time()
        
        logger.info(f"🛡️ Worker {worker_id}: Scraper stealth initialisé")
    
    async def initialize(self):
        """Initialise le scraper avec protection anti-détection"""
        try:
            logger.info(f"🛡️ Worker {self.worker_id}: Initialisation avec protection anti-détection")
            
            # Initialiser Playwright
            self.playwright = await async_playwright().start()
            
            # Configuration anti-détection
            stealth_config = get_stealth_browser_config()
            
            # Lancer le navigateur avec protection anti-détection
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=f'./session-profile-stealth-{self.worker_id}',
                **stealth_config
            )
            
            # Créer une nouvelle page
            self.page = await self.context.new_page()
            
            # Appliquer les injections de discrétion
            await apply_stealth_to_page(self.page)
            
            # Configurer les headers de discrétion
            await self.page.set_extra_http_headers(self.stealth_headers)
            
            # Masquer les propriétés d'automation
            await self.page.add_init_script("""
                // Masquer les traces d'automation
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Masquer les propriétés Playwright
                delete window.__playwright;
                delete window.__pw_manual;
                delete window.__pw_original;
                
                // Masquer les propriétés Chrome d'automation
                if (window.chrome) {
                    Object.defineProperty(window.chrome, 'runtime', {
                        get: () => ({
                            onConnect: undefined,
                            onMessage: undefined,
                            connect: undefined,
                            sendMessage: undefined,
                            getManifest: () => ({ name: 'Chrome', version: '120.0.0.0' })
                        }),
                    });
                }
            """)
            
            # Initialiser l'API client
            self.api_client = APIClient()
            await self.api_client.initialize()
            
            logger.info(f"✅ Worker {self.worker_id}: Scraper stealth initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur initialisation: {e}")
            return False
    
    async def authenticate_mytoolsplan(self):
        """Authentification MyToolsPlan avec protection anti-détection"""
        try:
            logger.info(f"🔐 Worker {self.worker_id}: Authentification MyToolsPlan...")
            
            # Délai aléatoire avant authentification
            await self._random_delay('auth')
            
            # Navigation vers la page de login
            await self.page.goto("https://app.mytoolsplan.com/login", 
                               wait_until='domcontentloaded', timeout=60000)
            
            # Délai aléatoire après navigation
            await self._random_delay('page_load')
            
            # Récupérer les credentials
            from config import get_mytoolsplan_credentials
            username, password = get_mytoolsplan_credentials()
            
            # Remplir les champs avec délais humains
            await self.page.fill('input[name="amember_login"]', username)
            await self._random_delay('typing')
            
            await self.page.fill('input[name="amember_pass"]', password)
            await self._random_delay('typing')
            
            # Soumettre le formulaire
            await self.page.evaluate('document.querySelector("form[name=\\"login\\"]").submit()')
            
            # Attendre la redirection
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # Vérifier le succès du login
            current_url = self.page.url
            if "login" not in current_url and "app.mytoolsplan.com" in current_url:
                logger.info(f"✅ Worker {self.worker_id}: Authentification réussie")
                return True
            else:
                logger.error(f"❌ Worker {self.worker_id}: Échec authentification")
                return False
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur authentification: {e}")
            return False
    
    async def scrape_domain_overview(self, domain: str) -> Optional[Dict[str, str]]:
        """Scrape les données de domain overview avec protection anti-détection"""
        try:
            logger.info(f"🕷️ Worker {self.worker_id}: Scraping domain overview pour {domain}")
            
            # Délai aléatoire avant scraping
            await self._random_delay('scraping')
            
            # Rotation d'identité si nécessaire
            await self._rotate_identity_if_needed()
            
            # Navigation vers la page
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            target_date = self._calculate_target_date()
            
            # Utiliser l'API client pour récupérer les métriques
            all_metrics = await self.api_client.get_all_metrics_via_api(clean_domain, target_date)
            
            if not all_metrics:
                logger.warning(f"⚠️ Worker {self.worker_id}: Aucune métrique récupérée pour {domain}")
                return None
            
            # Extraire les métriques principales
            metrics = {
                'organic_search_traffic': str(all_metrics.get('organic_traffic', 0)),
                'paid_search_traffic': str(all_metrics.get('paid_traffic', 0)),
                'bounce_rate': str(all_metrics.get('bounce_rate', 0)),
                'avg_visit_duration': str(all_metrics.get('avg_visit_duration', 0)),
                'traffic': str(all_metrics.get('visits', 0)),
                'branded_traffic': str(all_metrics.get('traffic_branded', 0)),
                'conversion_rate': str(all_metrics.get('conversion_rate', 0)),
                'cpc': str(all_metrics.get('cpc', 0)),
                'source': 'organic.OverviewTrend API (stealth)'
            }
            
            # Stocker dans session_data
            self.session_data['data']['domain_overview'] = metrics
            
            # Délai aléatoire après scraping
            await self._random_delay('post_scraping')
            
            logger.info(f"✅ Worker {self.worker_id}: Domain overview terminé - Organic: {metrics.get('organic_search_traffic', 'N/A')}, Paid: {metrics.get('paid_search_traffic', 'N/A')}, Traffic: {metrics.get('traffic', 'N/A')}, Branded: {metrics.get('branded_traffic', 'N/A')}, CPC: {metrics.get('cpc', 'N/A')}, Conversion: {metrics.get('conversion_rate', 'N/A')}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping domain overview: {e}")
            return None
    
    async def _random_delay(self, delay_type: str = 'default'):
        """Applique un délai aléatoire pour simuler un comportement humain"""
        try:
            # Délais spécifiques selon le type
            delays = {
                'auth': (3.0, 6.0),
                'page_load': (2.0, 4.0),
                'typing': (0.5, 1.5),
                'scraping': (2.0, 5.0),
                'post_scraping': (1.0, 3.0),
                'default': (1.0, 2.0)
            }
            
            min_delay, max_delay = delays.get(delay_type, delays['default'])
            
            # Délai de base
            base_delay = random.uniform(min_delay, max_delay)
            
            # Ajouter du jitter
            jitter = random.uniform(-0.5, 0.5)
            total_delay = max(0.1, base_delay + jitter)
            
            logger.debug(f"⏳ Worker {self.worker_id}: Délai {delay_type} - {total_delay:.2f}s")
            await asyncio.sleep(total_delay)
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur délai: {e}")
    
    async def _rotate_identity_if_needed(self):
        """Rotation d'identité si nécessaire"""
        try:
            current_time = time.time()
            if current_time - self.last_identity_rotation > self.identity_rotation_interval:
                logger.info(f"🔄 Worker {self.worker_id}: Rotation d'identité")
                
                # Nouveaux headers
                self.stealth_headers = get_stealth_headers()
                await self.page.set_extra_http_headers(self.stealth_headers)
                
                # Nouveau User-Agent
                new_ua = self.stealth_headers['User-Agent']
                await self.page.set_extra_http_headers({'User-Agent': new_ua})
                
                self.last_identity_rotation = current_time
                logger.info(f"✅ Worker {self.worker_id}: Identité rotée")
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur rotation identité: {e}")
    
    def _calculate_target_date(self) -> str:
        """Calcule la date cible pour les requêtes"""
        target_date = datetime.now(timezone.utc) - timedelta(days=30)
        return target_date.strftime('%Y-%m-%d')
    
    def format_analytics_for_api(self) -> Dict[str, str]:
        """Formate les données de session pour l'API"""
        analytics_data = {
            "organic_traffic": "",
            "bounce_rate": "",
            "average_visit_duration": "",
            "branded_traffic": "",
            "conversion_rate": "",
            "paid_search_traffic": "",
            "traffic": "",
            "percent_branded_traffic": "",
            "cpc": ""
        }
        
        # Récupérer les données de domain_overview
        if 'domain_overview' in self.session_data['data']:
            domain_data = self.session_data['data']['domain_overview']
            analytics_data['organic_traffic'] = domain_data.get('organic_search_traffic', '')
            analytics_data['paid_search_traffic'] = domain_data.get('paid_search_traffic', '')
            analytics_data['bounce_rate'] = domain_data.get('bounce_rate', '')
            analytics_data['average_visit_duration'] = domain_data.get('avg_visit_duration', '')
            analytics_data['traffic'] = domain_data.get('traffic', '')
            analytics_data['branded_traffic'] = domain_data.get('branded_traffic', '')
            analytics_data['conversion_rate'] = domain_data.get('conversion_rate', '')
            analytics_data['cpc'] = domain_data.get('cpc', '')
        
        # Calculer percent_branded_traffic
        analytics_data['percent_branded_traffic'] = self._calculate_percent_branded_traffic(analytics_data)
        
        return analytics_data
    
    def _calculate_percent_branded_traffic(self, analytics_data: Dict[str, str]) -> str:
        """Calcule le pourcentage de trafic branded"""
        try:
            traffic = float(analytics_data.get('traffic', 0) or 0)
            branded_traffic = float(analytics_data.get('branded_traffic', 0) or 0)
            
            if traffic > 0:
                percent = (branded_traffic / traffic) * 100
                return f"{percent:.2f}"
            else:
                return "0.00"
        except (ValueError, ZeroDivisionError):
            return "0.00"
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info(f"✅ Worker {self.worker_id}: Nettoyage terminé")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur nettoyage: {e}")

async def main():
    """Fonction principale de test"""
    setup_logging()
    
    scraper = StealthScraper(worker_id=0)
    
    try:
        # Initialiser le scraper
        if not await scraper.initialize():
            logger.error("❌ Échec initialisation scraper")
            return
        
        # Authentifier
        if not await scraper.authenticate_mytoolsplan():
            logger.error("❌ Échec authentification")
            return
        
        # Tester le scraping
        test_domain = "example.com"
        result = await scraper.scrape_domain_overview(test_domain)
        
        if result:
            logger.info(f"✅ Test réussi: {result}")
        else:
            logger.warning("⚠️ Test échoué")
        
    except Exception as e:
        logger.error(f"❌ Erreur principale: {e}")
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
