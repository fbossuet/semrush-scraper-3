#!/usr/bin/env python3
"""
Scraper de production parallélisé pour MyToolsPlan avec API organic.Summary
Session partagée + Workers parallèles + Répartition équitable des boutiques
INTÉGRATION API organic.Summary pour organic_search_traffic et paid_search_traffic
"""

import asyncio
import json
import logging
import os
import random
import platform
import multiprocessing
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3

import config
from playwright.async_api import async_playwright
from trendtrack_api_vps_adapted import api

# Configuration du logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure le logging"""
    # Nettoyer les handlers existants
    logger = logging.getLogger()
    logger.handlers.clear()

    # Configurer le format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Ajouter le handler
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

    # Désactiver les logs de playwright
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class LockManager:
    """Gestionnaire de locks global pour session partagée"""
    _locks = {}
    
    @classmethod
    def get_lock(cls, name: str):
        if name not in cls._locks:
            cls._locks[name] = asyncio.Lock()
        return cls._locks[name]

class ParallelProductionScraper:
    """Scraper de production parallélisé avec session partagée"""
    
    def __init__(self, worker_id: int, max_shops: int = None):
        self.worker_id = worker_id
        self.max_shops = max_shops
        self.context = None
        self.page = None
        self.session_data = {'data': {}}
        
        # Configuration des timeouts adaptatifs
        self.selector_timeouts = {
            'organic_search_traffic': 30000,
            'paid_search_traffic': 30000,
            'avg_visit_duration': 30000,
            'bounce_rate': 30000,
            'branded_traffic': 30000,
            'conversion_rate': 30000
        }
    
    def calculate_target_date(self) -> str:
        """
        Calcule la date cible : mois en cours - 2 mois, 15 du mois
        Exemple: septembre 2025 -> juillet 2025 -> 20250715
        """
        now = datetime.now(timezone.utc)
        # Mois en cours - 2 mois
        target_month = now.month - 2
        target_year = now.year
        
        # Gérer le cas où on passe en année précédente
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # Format: YYYYMMDD avec le 15 du mois
        target_date = f"{target_year:04d}{target_month:02d}15"
        
        logger.info(f"📅 Worker {self.worker_id}: Date calculée: {target_date} (mois en cours - 2 mois, 15 du mois)")
        return target_date
    
    async def get_organic_traffic_via_api(self, domain: str) -> Optional[Dict[str, str]]:
        """Récupère le traffic organique et payant via l'API organic.Summary"""
        try:
            logger.info(f"🎯 Worker {self.worker_id}: Récupération Organic/Paid Traffic via API organic.Summary pour {domain}")
            
            target_date = self.calculate_target_date()
            
            # Nettoyer le domaine (enlever https://, http://, www.)
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            
            logger.info(f"🌐 Worker {self.worker_id}: Domaine nettoyé: {clean_domain}")
            
            # Appel API organic.Summary
            result = await self.page.evaluate("""
                async (data) => {
                    try {
                        const response = await fetch('/dpa/rpc', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                "id": Math.floor(Math.random() * 10000),
                                "jsonrpc": "2.0",
                                "method": "organic.Summary",
                                "params": {
                                    "request_id": "req_" + new Date().toISOString() + "_" + Math.random().toString(36).substring(2, 8),
                                    "report": "domain.overview",
                                    "args": {
                                        "searchItem": data.domain,
                                        "searchType": "domain", 
                                        "database": "us",
                                        "dateType": "monthly",
                                        "date": data.target_date,
                                        "dateFormat": "date"
                                    },
                                    "userId": data.credentials.userId,
                                    "apiKey": data.credentials.apiKey
                                }
                            })
                        });
                        
                        const responseText = await response.text();
                        
                        if (!response.ok) {
                            return {
                                error: `HTTP ${response.status}: ${responseText}`,
                                status: response.status
                            };
                        }
                        
                        return JSON.parse(responseText);
                        
                    } catch (error) {
                        return {
                            error: error.message,
                            type: 'fetch_error'
                        };
                    }
                }
            """, {
                'domain': clean_domain,
                'target_date': target_date,
                'credentials': {
                    'userId': 26931056,
                    'apiKey': "943cfac719badc2ca14126e08b8fe44f"
                }
            })
            
            if result.get('error'):
                logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.Summary: {result['error']}")
                return None
            
            if result.get('result') and len(result['result']) > 0:
                # Chercher l'entrée USA
                us_entry = None
                for entry in result['result']:
                    if entry.get('database') == 'us':
                        us_entry = entry
                        break
                
                if not us_entry:
                    us_entry = result['result'][0]
                
                organic_raw = us_entry.get('organicTraffic', 0)
                paid_raw = us_entry.get('adwordsTraffic', 0)  # Traffic payant direct
                
                # TEST CRITIQUE: Si organic traffic < 1000, retourner 'na'
                if organic_raw < 1000:
                    logger.warning(f"⚠️ Worker {self.worker_id}: Organic Traffic trop faible ({organic_raw} < 1000) - Status 'na'")
                    return 'na'
                
                # Utiliser les valeurs brutes (sans formatage K/M)
                organic_value = str(organic_raw)
                paid_value = str(paid_raw)
                
                logger.info(f"✅ Worker {self.worker_id}: Organic Traffic (API): {organic_value} (raw: {organic_raw})")
                logger.info(f"✅ Worker {self.worker_id}: Paid Traffic (API): {paid_value} (raw: {paid_raw})")
                
                return {
                    'organic_search_traffic': organic_value,
                    'paid_search_traffic': paid_value,
                    'organic_raw': organic_raw,
                    'paid_raw': paid_raw,
                    'source': 'organic.Summary API'
                }
            
            logger.info(f"❌ Worker {self.worker_id}: Aucune donnée trouvée via API")
            return None
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.Summary: {error}")
            return None
    
    def format_number(self, num: int) -> str:
        """Formate un nombre pour l'affichage"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)
    
    async def setup_browser(self):
        """Configuration du navigateur avec session partagée"""
        logger.info(f"🔧 Worker {self.worker_id}: Configuration du navigateur...")
        
        # Configuration Xvfb pour Linux
        if platform.system() == "Linux":
            try:
                import subprocess
                subprocess.run(["Xvfb", ":99", "-screen", "0", "1024x768x24"], 
                             check=False, capture_output=True)
                os.environ["DISPLAY"] = ":99"
                logger.info(f"🖥️ Worker {self.worker_id}: Xvfb configuré")
            except:
                logger.info(f"🖥️ Worker {self.worker_id}: Xvfb déjà en cours")
        
        playwright = await async_playwright().start()
        
        # Configuration identique au scraper de production
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir='./session-profile',
            headless=False,  # Pas de headless comme demandé
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        logger.info(f"✅ Worker {self.worker_id}: Navigateur configuré")
    
    async def authenticate_mytoolsplan(self):
        """Authentification MyToolsPlan"""
        logger.info(f"🔐 Worker {self.worker_id}: Authentification MyToolsPlan...")

        try:
            # Navigation vers la page de login
            await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
            await self.page.wait_for_load_state('networkidle')

            # Récupérer les credentials
            username, password = config.get_mytoolsplan_credentials()

            # Remplir les champs de login
            await self.page.fill('input[name="amember_login"]', username)
            await self.page.fill('input[name="amember_pass"]', password)

            # Soumettre le formulaire
            try:
                await self.page.click('input[type="submit"][class="frm-submit"]')
            except:
                await self.page.evaluate('document.querySelector("form[name=\"login\"]").submit()')

            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # Vérifier que nous sommes sur la page membre
            current_url = self.page.url
            logger.info(f"✅ Worker {self.worker_id}: Login réussi, URL actuelle: {current_url}")

            if "member" not in current_url.lower():
                logger.error(f"❌ Worker {self.worker_id}: Login échoué - Pas sur la page membre")
                return False

            return True

        except Exception as e:
            error_msg = f"❌ Worker {self.worker_id}: Erreur lors de l'authentification: {e}"
            logger.error(error_msg)
            return False
    
    async def sync_cookies_with_sam(self):
        """Synchronisation des cookies avec sam.mytoolsplan.xyz"""
        logger.info(f"🔄 Worker {self.worker_id}: Synchronisation des cookies avec sam.mytoolsplan.xyz...")
        
        try:
            # Récupérer les cookies d'authentification
            cookies = await self.context.cookies()
            auth_cookies = [c for c in cookies if c['name'] in ['amember_login', 'amember_pass_enc']]
            
            logger.info(f"📊 Worker {self.worker_id}: Cookies récupérés: {len(cookies)} cookies")
            logger.info(f"🔍 Worker {self.worker_id}: {len(auth_cookies)} cookies d'authentification identifiés")
            
            # Navigation vers sam.mytoolsplan.xyz
            logger.info(f"🌐 Worker {self.worker_id}: Navigation vers sam.mytoolsplan.xyz...")
            await self.page.goto("https://sam.mytoolsplan.xyz/", wait_until='domcontentloaded', timeout=30000)
            
            # Définir les cookies d'authentification
            if auth_cookies:
                await self.context.add_cookies(auth_cookies)
                logger.info(f"✅ Worker {self.worker_id}: {len(auth_cookies)} cookies d'auth synchronisés avec sam.mytoolsplan.xyz")
            
            # Test de la session
            logger.info(f"🔍 Worker {self.worker_id}: Test de la session sur sam.mytoolsplan.xyz/analytics/...")
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            if "analytics" in current_url:
                logger.info(f"✅ Worker {self.worker_id}: Session synchronisée avec succès sur sam.mytoolsplan.xyz")
                return True
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Session partiellement synchronisée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur synchronisation cookies: {e}")
            return False
    
    async def navigate_with_smart_timeout(self, url, description=""):
        """Navigation avec timeout adaptatif"""
        try:
            logger.info(f"🌐 Worker {self.worker_id}: Navigation vers {description}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur navigation {description}: {e}")
            return False
    
    async def validate_selector_adaptive(self, selector: str, description: str, base_timeout: int = 30000):
        """Validation de sélecteur avec timeout adaptatif"""
        try:
            adaptive_timeout = api.calculate_adaptive_timeout(description, base_timeout)
            element = await self.page.wait_for_selector(selector, timeout=adaptive_timeout)
            if element:
                logger.info(f"✅ Worker {self.worker_id}: {description} trouvé")
                return element
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: {description} non trouvé")
                return None
        except Exception as e:
            logger.warning(f"⚠️ Worker {self.worker_id}: {description} - Timeout: {e}")
            return None
    
    async def scrape_domain_overview(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):
        """Scraping de la page Domain Overview avec API organic.Summary"""
        logger.info(f"📊 Worker {self.worker_id}: Domain Overview pour {domain} (AVEC API organic.Summary)")
        
        try:
            # NOUVELLE APPROCHE: Utiliser l'API organic.Summary au lieu de naviguer vers la page
            logger.info(f"🚀 Worker {self.worker_id}: Utilisation de l'API organic.Summary (pas de navigation)")
            
            # Organic Search Traffic et Paid Search Traffic via API
            if existing_metrics and existing_metrics.get("organic_traffic") and existing_metrics.get("organic_traffic") != "na":
                logger.info(f"⏭️ Worker {self.worker_id}: Organic Traffic déjà présente: {existing_metrics.get('organic_traffic')} - SKIP")
                # Retourner True pour continuer avec les autres métriques
                return True
            else:
                # NOUVELLE LOGIQUE: Appel API organic.Summary
                api_result = await self.get_organic_traffic_via_api(domain)
                
                # GESTION DU STATUT 'na' - Même logique que le code existant
                if api_result == 'na':
                    logger.info(f"🔄 Worker {self.worker_id}: Traitement du retour 'na' pour {domain}")
                    # Récupérer la valeur organic_traffic même si elle est invalide
                    organic_traffic_value = ""
                    if 'domain_overview' in self.session_data['data']:
                        organic_traffic_value = self.session_data['data']['domain_overview'].get('organic_search_traffic', '')
                        logger.info(f"📊 Worker {self.worker_id}: Valeur organic_traffic récupérée: '{organic_traffic_value}'")
                    else:
                        logger.warning(f"⚠️ Worker {self.worker_id}: Pas de données domain_overview dans session_data")
                    
                    # Sauvegarder les données avant de retourner 'na'
                    self.session_data['data']['domain_overview'] = {
                        'organic_search_traffic': organic_traffic_value,
                        'paid_search_traffic': "",
                        'avg_visit_duration': "",
                        'bounce_rate': ""
                    }
                    
                    # Retourner 'na' pour indiquer que la boutique doit être marquée comme 'na'
                    logger.info(f"⏭️ Worker {self.worker_id}: {domain} - Organic traffic trop faible, passage à la boutique suivante")
                    return 'na'
                
                elif api_result:
                    # Métriques récupérées avec succès
                    self.session_data['data']['domain_overview'] = {
                        'organic_search_traffic': api_result['organic_search_traffic'],
                        'paid_search_traffic': api_result['paid_search_traffic'],
                        'avg_visit_duration': "",
                        'bounce_rate': ""
                    }
                    logger.info(f"✅ Worker {self.worker_id}: Métriques récupérées via API organic.Summary")
                    logger.info(f"   🌱 Organic: {api_result['organic_search_traffic']}")
                    logger.info(f"   💰 Paid: {api_result['paid_search_traffic']}")
                else:
                    # Échec de l'API
                    self.session_data['data']['domain_overview'] = {
                        'organic_search_traffic': "",
                        'paid_search_traffic': "",
                        'avg_visit_duration': "",
                        'bounce_rate': ""
                    }
                    logger.warning(f"⚠️ Worker {self.worker_id}: Échec API organic.Summary")
            
            # Autres métriques en parallèle (DOM scraping classique)
            async def scrape_avg_duration():
                if existing_metrics and existing_metrics.get("avg_visit_duration") and existing_metrics.get("avg_visit_duration") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Average Visit Duration déjà présent: {existing_metrics.get('avg_visit_duration')} - SKIP")
                    return existing_metrics.get("avg_visit_duration")
                else:
                    # Navigation vers la page pour les autres métriques
                    url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q={domain}&date={date_range}"
                    success = await self.navigate_with_smart_timeout(url, "Domain Overview (autres métriques)")
                    if not success:
                        return ""
                    
                    await asyncio.sleep(1)
                    
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.engagement_metrics.visit_duration"] span[data-ui-name="Link.Text"]',
                        "Average Visit Duration"
                    )
                    return await element.inner_text() if element else ""
            
            async def scrape_bounce_rate():
                if existing_metrics and existing_metrics.get("bounce_rate") and existing_metrics.get("bounce_rate") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Bounce Rate déjà présent: {existing_metrics.get('bounce_rate')} - SKIP")
                    return existing_metrics.get("bounce_rate")
                else:
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.engagement_metrics.bounce_rate"] span[data-ui-name="Link.Text"]',
                        "Bounce Rate"
                    )
                    return await element.inner_text() if element else ""
            
            # Exécuter en parallèle
            avg_duration, bounce_rate = await asyncio.gather(
                scrape_avg_duration(),
                scrape_bounce_rate(),
                return_exceptions=True
            )
            
            # Mettre à jour les métriques
            if 'domain_overview' not in self.session_data['data']:
                self.session_data['data']['domain_overview'] = {}
            
            self.session_data['data']['domain_overview']['avg_visit_duration'] = avg_duration if not isinstance(avg_duration, Exception) else ""
            self.session_data['data']['domain_overview']['bounce_rate'] = bounce_rate if not isinstance(bounce_rate, Exception) else ""
            
            # AFFICHAGE DES MÉTRIQUES DANS LES LOGS (SANS ENREGISTREMENT BDD)
            metrics = self.session_data['data']['domain_overview']
            logger.info(f"📊 Worker {self.worker_id}: RÉSULTATS Domain Overview pour {domain}:")
            logger.info(f"   🌱 Organic Search Traffic: {metrics.get('organic_search_traffic', 'N/A')}")
            logger.info(f"   💰 Paid Search Traffic: {metrics.get('paid_search_traffic', 'N/A')}")
            logger.info(f"   ⏱️ Average Visit Duration: {metrics.get('avg_visit_duration', 'N/A')}")
            logger.info(f"   📈 Bounce Rate: {metrics.get('bounce_rate', 'N/A')}")
            
            logger.info(f"✅ Worker {self.worker_id}: Domain Overview terminé (API + DOM)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur Domain Overview: {e}")
            return False
    
    async def scrape_organic_search(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):
        """Scraping de la page Organic Search - VÉRIFIE AVANT DE SCRAPER"""
        logger.info(f"📊 Worker {self.worker_id}: Organic Search pour {domain}")
        
        try:
            url = f"https://sam.mytoolsplan.xyz/analytics/organic/overview/?db=us&q={domain}&searchType=domain&date={date_range}"
            
            success = await self.navigate_with_smart_timeout(url, "Organic Search")
            if not success:
                return False
            
            await asyncio.sleep(1)
            
            # Branded Traffic et Paid Search Traffic en parallèle
            async def scrape_branded_traffic():
                if existing_metrics and existing_metrics.get("branded_traffic") and existing_metrics.get("branded_traffic") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Branded Traffic déjà présent: {existing_metrics.get('branded_traffic')} - SKIP")
                    return existing_metrics.get("branded_traffic")
                else:
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.summary.click_branded_traffic"] span[data-ui-name="Link.Text"]',
                        "Branded Traffic"
                    )
                    return await element.inner_text() if element else ""
            
            async def scrape_paid_search_traffic():
                if existing_metrics and existing_metrics.get("paid_search_traffic") and existing_metrics.get("paid_search_traffic") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Paid Search Traffic déjà présent: {existing_metrics.get('paid_search_traffic')} - SKIP")
                    return existing_metrics.get("paid_search_traffic")
                else:
                    # Sélecteur qui fonctionnait le 4 septembre
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.engagement_metrics.paid_search_traffic"] span[data-ui-name="Link.Text"]',
                        "Paid Search Traffic"
                    )
                    return await element.inner_text() if element else ""
            
            # Exécuter en parallèle
            branded_traffic, paid_search_traffic = await asyncio.gather(
                scrape_branded_traffic(),
                scrape_paid_search_traffic(),
                return_exceptions=True
            )
            
            metrics = {
                'branded_traffic': branded_traffic if not isinstance(branded_traffic, Exception) else "",
                'paid_search_traffic': paid_search_traffic if not isinstance(paid_search_traffic, Exception) else ""
            }
            
            # AFFICHAGE DES MÉTRIQUES DANS LES LOGS (SANS ENREGISTREMENT BDD)
            logger.info(f"📊 Worker {self.worker_id}: RÉSULTATS Organic Search pour {domain}:")
            logger.info(f"   🏷️ Branded Traffic: {metrics.get('branded_traffic', 'N/A')}")
            logger.info(f"   💰 Paid Search Traffic: {metrics.get('paid_search_traffic', 'N/A')}")
            
            self.session_data['data']['organic_search'] = metrics
            logger.info(f"✅ Worker {self.worker_id}: Organic Search terminé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur Organic Search: {e}")
            return False
    
    async def scrape_traffic_analysis(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):
        """Scraping de la page Traffic Analysis - VÉRIFIE AVANT DE SCRAPER"""
        logger.info(f"📊 Worker {self.worker_id}: Traffic Analysis pour {domain}")
        
        try:
            url = f"https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/?db=us&q={domain}&searchType=domain&date={date_range}"
            
            success = await self.navigate_with_smart_timeout(url, "Traffic Analysis")
            if not success:
                return False
            
            await asyncio.sleep(1)
            
            # Visits et Conversion Rate en parallèle
            async def scrape_visits():
                if existing_metrics and existing_metrics.get("visits") and existing_metrics.get("visits") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Visits déjà présents: {existing_metrics.get('visits')} - SKIP")
                    return existing_metrics.get("visits")
                else:
                    element = await self.validate_selector_adaptive(
                        'div[data-testid="summary-cell visits"] > div > div > div > span[data-testid="value"]',
                        "Visits"
                    )
                    return await element.inner_text() if element else ""
            
            async def scrape_conversion_rate():
                if existing_metrics and existing_metrics.get("conversion_rate") and existing_metrics.get("conversion_rate") != "na":
                    logger.info(f"⏭️ Worker {self.worker_id}: Conversion Rate déjà présent: {existing_metrics.get('conversion_rate')} - SKIP")
                    return existing_metrics.get("conversion_rate")
                else:
                    element = await self.validate_selector_adaptive(
                        'div[data-testid="summary-cell conversion"] > div > div > div > span[data-testid="value"]',
                        "Purchase Conversion"
                    )
                    return await element.inner_text() if element else ""
            
            # Exécuter en parallèle
            visits, conversion_rate = await asyncio.gather(
                scrape_visits(),
                scrape_conversion_rate(),
                return_exceptions=True
            )
            
            metrics = {
                'visits': visits if not isinstance(visits, Exception) else "",
                'conversion_rate': conversion_rate if not isinstance(conversion_rate, Exception) else ""
            }
            
            # AFFICHAGE DES MÉTRIQUES DANS LES LOGS (SANS ENREGISTREMENT BDD)
            logger.info(f"📊 Worker {self.worker_id}: RÉSULTATS Traffic Analysis pour {domain}:")
            logger.info(f"   👥 Visits: {metrics.get('visits', 'N/A')}")
            logger.info(f"   🎯 Conversion Rate: {metrics.get('conversion_rate', 'N/A')}")
            
            self.session_data['data']['traffic_analysis'] = metrics
            logger.info(f"✅ Worker {self.worker_id}: Traffic Analysis terminé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur Traffic Analysis: {e}")
            return False
    
    def format_analytics_for_api(self) -> Dict[str, str]:
        """Formate les données de session pour l'API"""
        analytics_data = {
            "organic_traffic": "",
            "bounce_rate": "",
            "average_visit_duration": "",
            "branded_traffic": "",
            "conversion_rate": "",
            "paid_search_traffic": "",
            "visits": "",
            "traffic": "",
            "percent_branded_traffic": ""
        }
        
        # Récupérer les données de domain_overview
        if 'domain_overview' in self.session_data['data']:
            domain_data = self.session_data['data']['domain_overview']
            analytics_data['organic_traffic'] = domain_data.get('organic_search_traffic', '')
            analytics_data['paid_search_traffic'] = domain_data.get('paid_search_traffic', '')
            analytics_data['bounce_rate'] = domain_data.get('bounce_rate', '')
            analytics_data['average_visit_duration'] = domain_data.get('avg_visit_duration', '')
        
        # Récupérer les données de organic_search
        if 'organic_search' in self.session_data['data']:
            organic_data = self.session_data['data']['organic_search']
            analytics_data['branded_traffic'] = organic_data.get('branded_traffic', '')
            analytics_data['percent_branded_traffic'] = organic_data.get('percent_branded_traffic', '')
        
        # Récupérer les données de traffic_analysis
        if 'traffic_analysis' in self.session_data['data']:
            traffic_data = self.session_data['data']['traffic_analysis']
            analytics_data['visits'] = traffic_data.get('visits', '')
            analytics_data['traffic'] = traffic_data.get('traffic', '')
            analytics_data['conversion_rate'] = traffic_data.get('conversion_rate', '')
        
        return analytics_data
    
    async def run_worker(self, shops: List[Dict], date_range: str) -> str:
        """Exécute le scraping pour une liste de boutiques"""
        logger = logging.getLogger(__name__)
        
        try:
            # Configuration du navigateur
            await self.setup_browser()
            logger.info(f"✅ Worker {self.worker_id}: Navigateur configuré")
            
            # Authentification
            auth_success = await self.authenticate_mytoolsplan()
            if not auth_success:
                logger.error(f"❌ Worker {self.worker_id}: Échec de l'authentification")
                return 'failed'
            
            logger.info(f"✅ Worker {self.worker_id}: Authentification réussie")
            
            # Synchronisation des cookies
            sync_success = await self.sync_cookies_with_sam()
            if not sync_success:
                logger.warning(f"⚠️ Worker {self.worker_id}: Synchronisation partielle, continuation...")
            
            logger.info(f"✅ Worker {self.worker_id}: Synchronisation des cookies terminée")
            
            # Traitement des boutiques
            successful_shops = 0
            total_shops = len(shops)
            
            for i, shop in enumerate(shops, 1):
                try:
                    domain = shop.get('domain', '')
                    shop_id = shop.get('id', '')
                    
                    logger.info(f"🎯 Worker {self.worker_id}: Traitement {i}/{total_shops} - {domain} (ID: {shop_id})")
                    
                    # Scraping du domaine
                    result = await self.scrape_domain_overview(domain, date_range)
                    
                    if result == 'na':
                        logger.info(f"ℹ️ Worker {self.worker_id}: {domain} marqué comme 'na' (organic traffic < 1000)")
                        # Enregistrer en BDD avec statut 'na'
                        analytics_data = self.format_analytics_for_api()
                        api.update_shop_analytics(shop_id, analytics_data, 'na')
                        logger.info(f"💾 Worker {self.worker_id}: {domain} enregistré en BDD avec statut 'na'")
                    elif result:
                        successful_shops += 1
                        logger.info(f"✅ Worker {self.worker_id}: {domain} traité avec succès")
                        
                        # Enregistrer en BDD
                        analytics_data = self.format_analytics_for_api()
                        status = 'completed' if self.session_data['data'].get('domain_overview') else 'partial'
                        api.update_shop_analytics(shop_id, analytics_data, status)
                        logger.info(f"💾 Worker {self.worker_id}: {domain} enregistré en BDD avec statut '{status}'")
                    else:
                        logger.warning(f"⚠️ Worker {self.worker_id}: {domain} échoué")
                        
                except Exception as e:
                    logger.error(f"❌ Worker {self.worker_id}: Erreur sur {domain}: {e}")
                    continue
            
            logger.info(f"🎉 Worker {self.worker_id}: Terminé - {successful_shops}/{total_shops} boutiques réussies")
            return 'completed'
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur générale: {e}")
            return 'failed'
        finally:
            if self.context:
                await self.context.close()
                logger.info(f"🔒 Worker {self.worker_id}: Navigateur fermé")

class ShopDistributor:
    """Distributeur de boutiques entre les workers"""
    
    def __init__(self, num_workers: int = 2):
        self.num_workers = num_workers
        self.distribution_file = Path("shop_distribution.json")
    
    def distribute_shops(self) -> Dict[int, List[Dict]]:
        """Répartit les boutiques entre les workers de manière équitable"""
        try:
            # Récupérer toutes les boutiques
            all_shops = api.get_all_shops()
            
            if not all_shops:
                logger.warning("⚠️ Aucune boutique trouvée")
                return {}
            
            # Filtrer les boutiques éligibles
            eligible_shops = [shop for shop in all_shops if api.is_shop_eligible_for_scraping(shop)]
            
            logger.info(f"📊 {len(eligible_shops)} boutiques éligibles sur {len(all_shops)} total")
            
            # Répartition équitable
            worker_shops = {}
            for i in range(self.num_workers):
                worker_shops[i] = eligible_shops[i::self.num_workers]
                logger.info(f"👷 Worker {i}: {len(worker_shops[i])} boutiques")
            
            # Sauvegarder la distribution
            distribution_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "num_workers": self.num_workers,
                "total_shops": len(all_shops),
                "eligible_shops": len(eligible_shops),
                "distribution": {
                    str(worker_id): [
                        {"id": shop["id"], "name": shop.get("shop_name", "N/A"), "url": shop.get("shop_url", "N/A")}
                        for shop in shops
                    ]
                    for worker_id, shops in worker_shops.items()
                }
            }
            
            with open(self.distribution_file, 'w') as f:
                json.dump(distribution_data, f, indent=2)
            
            logger.info(f"💾 Distribution sauvegardée: {self.distribution_file}")
            return worker_shops
            
        except Exception as e:
            logger.error(f"❌ Erreur distribution shops: {e}")
            return {}

async def run_worker_process(worker_id: int, shops: List[Dict], num_workers: int):
    """Fonction wrapper pour l'exécution en processus séparé"""
    setup_logging()
    
    async def main():
        scraper = ParallelProductionScraper(worker_id)
        return await scraper.run_worker(shops, "2025-07-01,2025-07-31")
    
    try:
        return await main()
    except Exception as e:
        logger.error(f"❌ Worker {worker_id}: Erreur processus: {e}")
        return False

async def main():
    """Fonction principale pour le scraping parallélisé"""
    setup_logging()
    logger.info("🏭 DÉMARAGE DU SCRAPER PARALLÉLISÉ AVEC API ORGANIC.SUMMARY")
    
    # Valider la configuration
    try:
        config.config.validate_credentials()
        logger.info("✅ Configuration validée")
    except ValueError as e:
        logger.error(f"❌ Erreur de configuration: {e}")
        return
    
    # Nombre de workers
    num_workers = 2
    logger.info(f"👷 Démarrage de {num_workers} workers parallèles")
    
    # Distribuer les boutiques
    distributor = ShopDistributor(num_workers)
    worker_shops = distributor.distribute_shops()
    
    if not worker_shops:
        logger.error("❌ Aucune boutique à traiter")
        return
    
    # Lancer les workers en parallèle
    tasks = []
    for worker_id, shops in worker_shops.items():
        if shops:  # Seulement si le worker a des boutiques
            task = asyncio.create_task(run_worker_process(worker_id, shops, num_workers))
            tasks.append(task)
    
    # Attendre que tous les workers terminent
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Afficher les résultats
    success_count = sum(1 for result in results if result is True)
    logger.info(f"🎉 SCRAPING PARALLÉLISÉ TERMINÉ: {success_count}/{len(tasks)} workers réussis")

if __name__ == "__main__":
    asyncio.run(main())
