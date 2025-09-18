#!/usr/bin/env python3
"""
Scraper de production pour MyToolsPlan
Bypass Cloudflare + Scraping des métriques + Intégration TrendTrack API
"""

import asyncio
import json
import logging
import os
import random
import platform
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3
import time  # Ajout pour mesurer les performances

import config
from playwright.async_api import async_playwright
# from playwright_stealth import stealth_sync

def log_metrics_to_json(shop, analytics_data, status):
    """Log les métriques récupérées en JSON"""
    try:
        # Créer le répertoire results
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)

        # Nom du fichier avec timestamp
        timestamp = datetime.now(timezone.utc).isoformat()
        shop_id = shop.get('id', 'unknown')
        shop_name = shop.get('shop_name', 'unknown').replace(' ', '_')
        filename = f"metrics_{shop_id}_{shop_name}_{timestamp}.json"
        filepath = results_dir / filename

        # Données à logger
        log_data = {
            "shop_id": shop.get('id'),
            "shop_name": shop.get('shop_name'),
            "shop_domain": shop.get('shop_url'),
            "scraping_status": status,
            "scraping_timestamp": datetime.now(timezone.utc).isoformat(),
            "analytics_data": analytics_data
        }

        # Sauvegarder en JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Métriques sauvegardées: {filepath}")

    except Exception as e:
        logger.error(f"❌ Erreur lors du logging JSON: {e}")

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

class ProductionScraper:
    """Scraper de production MyToolsPlan avec workflow complet"""

    def __init__(self):
        """Initialisation du scraper de production"""
        self.browser = None
        self.page = None
        self.session_data = {
            'shop_url': '',
            'date_range': '',
            'data': {},
            'errors': []
        }
        # Ajout des timers de performance
        self.performance_timers = {
            'start_time': None,
            'domain_times': [],
            'batch_times': []
        }

    async def setup_browser(self):
        """Configuration du navigateur optimisée pour VPS"""
        logger.info("🔧 Configuration du navigateur pour VPS...")

        # Vérifier le namespace VPN
        namespace = os.environ.get('NETNS', 'default')
        logger.info(f"🌐 Namespace VPN actuel: {namespace}")

        # Configuration du display selon le système d'exploitation
        system = platform.system().lower()
        if system == 'linux':
            # Sur Linux, utiliser Xvfb si pas de display
            display = os.environ.get('DISPLAY')
            if not display or display == '':
                logger.info("🖥️ Linux détecté - Configuration Xvfb...")
                # Vérifier si Xvfb est déjà en cours
                import subprocess
                try:
                    result = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.info("��️ Démarrage de Xvfb...")
                        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
                        os.environ['DISPLAY'] = ':99'
                    else:
                        logger.info("🖥️ Xvfb déjà en cours")
                        os.environ['DISPLAY'] = ':99'
                except FileNotFoundError:
                    logger.warning("⚠️ Xvfb non trouvé, utilisation du display par défaut")
            else:
                logger.info(f"🖥️ Display Linux configuré: {display}")
        elif system == 'darwin':
            # Sur macOS, pas besoin de Xvfb
            logger.info("🍎 macOS détecté - Pas de Xvfb nécessaire")
        else:
            # Windows ou autre
            logger.info(f"💻 Système {system} détecté - Configuration standard")

        p = await async_playwright().start()

        # Configuration optimisée pour VPS
        self.browser = await p.chromium.launch_persistent_context(
            user_data_dir='./session-profile-production',
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--start-maximized',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--no-default-browser-check',
                '--no-experiments',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-client-side-phishing-detection',
                '--disable-component-update',
                '--disable-domain-reliability',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--memory-pressure-off',
                '--max_old_space_size=4096',
                '--disable-dev-shm-usage',
                '--disable-application-cache',
                '--disable-offline-load-stale-cache',
                '--disk-cache-size=0',
                '--media-cache-size=0'
            ],
            ignore_default_args=['--enable-automation']
        )

        self.page = await self.browser.new_page()

        # Headers HTTP avancés pour le bypass
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        })

        # Stealth avancé

        # Scripts de bypass avancés
        await self.page.add_init_script("""
            // Masquer complètement l'automatisation
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            delete navigator.__proto__.webdriver;

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });

            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });

            Object.defineProperty(navigator, 'userAgent', {
                get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            });

            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });

            const originalQuery = window.document.querySelector;
            window.document.querySelector = function(selector) {
                if (selector === '[data-testid="webdriver"]') {
                    return null;
                }
                return originalQuery.apply(this, arguments);
            };

            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) Iris(TM) Graphics 6100';
                }
                return getParameter.apply(this, arguments);
            };
        """)

        logger.info("✅ Navigateur configuré avec bypass Cloudflare")

    async def navigate_with_smart_timeout(self, url, description=""):
        """Navigation avec timeout intelligent"""
        try:
            logger.info(f"🌐 Tentative 1/3 - {description} (timeout: 30s)")

            # Utiliser domcontentloaded au lieu de networkidle pour plus de rapidité
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Attendre un peu que la page se stabilise
            await asyncio.sleep(1)  # Optimisé: réduit de 3s à 1s

            logger.info(f"✅ Navigation réussie: {description}")
            # Afficher l'URL finale
            current_url = self.page.url
            logger.info(f"🌐 URL finale: {current_url}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Timeout domcontentloaded pour {description}, continuation...")
            logger.info(f"✅ Navigation réussie: {description}")
            # Afficher l'URL finale
            current_url = self.page.url
            logger.info(f"🌐 URL finale: {current_url}")
            return False

    async def wait_for_metrics_to_load(self):
        """Attente simple pour le chargement des métriques"""
        logger.info("⏳ Attente du chargement des métriques...")
        await asyncio.sleep(1)  # Optimisé: réduit de 3s à 1s
        logger.info("✅ Métriques chargées")

    def format_analytics_for_api(self) -> Dict:
        """Formate les données scrapées pour l'API TrendTrack"""
        analytics_data = {
            "scraping_status": "completed"
        }

        # Domain Overview
        if 'domain_overview' in self.session_data['data']:
            domain_data = self.session_data['data']['domain_overview']
            analytics_data.update({
                "organic_traffic": domain_data.get('organic_search_traffic', ''),
                "bounce_rate": domain_data.get('bounce_rate', ''),
                "average_visit_duration": domain_data.get('avg_visit_duration', '')
            })

        # Organic Search
        if 'organic_search' in self.session_data['data']:
            organic_data = self.session_data['data']['organic_search']
            analytics_data["branded_traffic"] = organic_data.get('branded_traffic', '')

        # Traffic Analysis
        if 'traffic_analysis' in self.session_data['data']:
            traffic_data = self.session_data['data']['traffic_analysis']
            analytics_data.update({
                "conversion_rate": traffic_data.get('purchase_conversion', ''),
                "visits": traffic_data.get('visits', '')
            })

        # Vérifier si des métriques contiennent "Sélecteur non trouvé|Erreur" ou "Erreur" et définir le statut en conséquence
        has_missing_selectors = False
        for key, value in analytics_data.items():
            if isinstance(value, str):
                if "Sélecteur non trouvé|Erreur" in value or "Erreur" in value:
                    has_missing_selectors = True
                    logger.info(f"🔍 Métrique '{key}' contient une erreur: '{value}'")
            elif isinstance(value, dict):
                # Vérifier les métriques imbriquées (comme traffic_analysis)
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str) and ("Sélecteur non trouvé|Erreur" in sub_value or "Erreur" in sub_value):
                        has_missing_selectors = True
                        logger.info(f"🔍 Métrique '{key}.{sub_key}' contient une erreur: '{sub_value}'")

        if has_missing_selectors:
            analytics_data["scraping_status"] = "partial"
            logger.info("⚠️ Statut changé en 'partial' car des sélecteurs n'ont pas été trouvés ou des erreurs sont présentes")
        else:
            analytics_data["scraping_status"] = "completed"
            logger.info("✅ Statut défini en 'completed' car tous les sélecteurs ont été trouvés")

        return analytics_data

    async def save_error_page_content(self, error_type: str, description: str):
        """Sauvegarde le contenu de la page en cas d'erreur"""
        try:
            # Créer le répertoire logs/error_pages
            error_dir = Path('logs/error_pages')
            error_dir.mkdir(exist_ok=True)

            # Nom du fichier avec timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            filename = f"error_{error_type}_{timestamp}.txt"
            filepath = error_dir / filename

            # Récupérer le contenu de la page
            page_content = await self.page.content()
            page_text = await self.page.inner_text('body')
            current_url = self.page.url

            # Sauvegarder en TXT
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== ERREUR: {error_type} ===\n")
                f.write(f"Description: {description}\n")
                f.write(f"URL: {current_url}\n")
                f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write("=== HTML CONTENT ===\n")
                f.write(page_content)
                f.write("\n\n=== TEXT CONTENT ===\n")
                f.write(page_text)

            logger.info(f"📄 Contenu d'erreur sauvegardé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde du contenu: {e}")
            return None

    async def validate_selector(self, selector: str, description: str, timeout: int = 30000, max_retries: int = 1):
        """Valide un sélecteur en temps réel avec un seul timeout de 30s"""

        try:
            logger.info(f"🔍 Recherche de {description} (timeout: {timeout}ms)")
            element = await self.page.wait_for_selector(selector, timeout=timeout)

            if element:
                logger.info(f"✅ Sélecteur trouvé: {description}")
                return element
            else:
                logger.error(f"❌ Sélecteur non trouvé|Erreur: {description}")
                await self.save_error_page_content("selector_error", f"{description} - Sélecteur non trouvé|Erreur")
                return None

        except Exception as e:
            logger.error(f"❌ Sélecteur invalide: {description} - {e}")
            logger.error(f"   Sélecteur: {selector}")
            await self.save_error_page_content("selector_error", f"{description} - {e}")
            return None

    async def validate_selector_adaptive(self, selector: str, description: str, base_timeout: int = 30000):
        """Valide un sélecteur avec timeout adaptatif basé sur l'historique des performances"""

        import time
        start_time = time.time()

        # Vérifier si on doit réinitialiser les performances (toutes les 2 heures)
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = time.time()
        
        if time.time() - self.session_start_time > 7200:  # 2 heures
            logger.info("🔄 Réinitialisation des performances de sélecteurs (session > 2h)")
            self.session_start_time = time.time()

        # Calculer le timeout adaptatif avec limite maximum
        adaptive_timeout = api.calculate_adaptive_timeout(description, base_timeout)
        max_timeout = min(adaptive_timeout, 120000)  # Maximum 120s
        
        # Vérifier le taux de succès et appliquer une pause si nécessaire
        success_rate = api.get_selector_success_rate(description)
        if success_rate < 0.5 and success_rate > 0:  # Si taux < 50% mais pas 0
            logger.warning(f"⚠️ Taux de succès faible pour {description}: {success_rate:.2f} - Pause de récupération...")
            await asyncio.sleep(60)  # Pause de 1 minute au lieu de 5
        
        if success_rate < 0.3 and success_rate > 0:  # Si taux < 30%
            logger.warning(f"⚠️ Taux de succès très faible pour {description}: {success_rate:.2f} - Pause de récupération étendue...")
            await asyncio.sleep(120)  # Pause de 2 minutes

        try:
            logger.info(f"🔍 Recherche de {description} (timeout adaptatif: {max_timeout}ms, taux succès: {success_rate:.2f})")
            element = await self.page.wait_for_selector(selector, timeout=max_timeout)

            response_time = int((time.time() - start_time) * 1000)

            if element:
                # Enregistrer le succès
                api.record_selector_performance(description, True, response_time)
                logger.info(f"✅ Sélecteur trouvé: {description} ({response_time}ms)")
                return element
            else:
                # Enregistrer l'échec
                api.record_selector_performance(description, False, max_timeout)
                logger.error(f"❌ Sélecteur non trouvé|Erreur: {description}")
                await self.save_error_page_content("selector_error", f"{description} - Sélecteur non trouvé|Erreur")
                return None

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            # Enregistrer l'échec
            api.record_selector_performance(description, False, response_time)
            logger.error(f"❌ Sélecteur invalide: {description} - {e}")
            logger.error(f"   Sélecteur: {selector}")
            await self.save_error_page_content("selector_error", f"{description} - {e}")
            return None

    async def authenticate_mytoolsplan(self):
        """Authentification MyToolsPlan"""
        logger.info("🔐 Authentification MyToolsPlan...")

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
            logger.info(f"✅ Login réussi, URL actuelle: {current_url}")

            if "member" not in current_url.lower():
                logger.error("❌ Login échoué - Pas sur la page membre")
                return False

            return True

        except Exception as e:
            error_msg = f"❌ Erreur lors de l'authentification: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False

    async def check_and_authenticate(self):
        """Vérifie si l'utilisateur est authentifié et s'authentifie si nécessaire"""
        try:
            current_url = self.page.url
            
            # Vérifier l'URL ET le contenu de la page
            login_redirected = False
            
            # 1. Vérifier l'URL
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                login_redirected = True
                logger.info("   🔐 Redirection vers login détectée (URL)")
            
            # 2. Vérifier le contenu de la page pour le message de login
            try:
                page_content = await self.page.content()
                if "If you are a registered member, please login" in page_content:
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté dans le contenu de la page")
                elif "please login" in page_content.lower() and "registered member" in page_content.lower():
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté (variante)")
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")
            
            if login_redirected:
                logger.info("   🔐 Authentification nécessaire, authentification...")
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=30000)
                
                await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
                await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)
                
                await self.page.fill('input[name="amember_login"]', config.config.MYTOOLSPLAN_USERNAME)
                await self.page.fill('input[name="amember_pass"]', config.config.MYTOOLSPLAN_PASSWORD)
                await self.page.click('input[type="submit"]')
                
                await self.page.wait_for_url("**/member", timeout=15000)
                logger.info("   ✅ Authentification réussie")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification d'authentification: {e}")
            return False

    async def scrape_domain_overview(self, domain: str, date_range: str):
        """Scraping de la page Domain Overview"""
        logger.info(f"📊 Scraping Domain Overview pour {domain}")

        try:
            # Étape intermédiaire : navigation vers /seo/ pour réchauffer la session (DÉSACTIVÉE)
            # logger.info("   🌐 Étape intermédiaire : navigation vers /seo/...")
            # await self.page.goto("https://sam.mytoolsplan.xyz/seo/", wait_until='domcontentloaded', timeout=60000)
            # await asyncio.sleep(3)

            # Construction de l'URL
            url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q={domain}&date={date_range}"

            # Navigation
            success = await self.navigate_with_smart_timeout(url, "Domain Overview")
            if not success:
                return False

            await asyncio.sleep(1)  # Optimisé: réduit de 2-4s à 1s

            # Vérifier si on est redirigé vers login ou si la page affiche le message de login
            current_url = self.page.url

            # Vérifier l'URL ET le contenu de la page
            login_redirected = False

            # 1. Vérifier l'URL (logique existante)
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                login_redirected = True
                logger.info("   🔐 Redirection vers login détectée (URL)")

            # 2. Vérifier le contenu de la page pour le message de login
            try:
                page_content = await self.page.content()
                if "If you are a registered member, please login" in page_content:
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté dans le contenu de la page")
                elif "please login" in page_content.lower() and "registered member" in page_content.lower():
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté (variante)")
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")

            if login_redirected:
                logger.info("   🔐 Redirection vers login détectée, authentification...")
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=30000)

                await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
                await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)

                await self.page.fill('input[name="amember_login"]', config.config.MYTOOLSPLAN_USERNAME)
                await self.page.fill('input[name="amember_pass"]', config.config.MYTOOLSPLAN_PASSWORD)
                await self.page.click('input[type="submit"]')

                await self.page.wait_for_url("**/member", timeout=15000)
                logger.info("   ✅ Authentification réussie")

                # Re-navigation vers Domain Overview
                await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)  # Optimisé: réduit de 10s à 5s

            # DEBUG: Vérifier le contenu de la page avant scraping
            try:
                page_title = await self.page.title()
                logger.info(f"🔍 DEBUG - Titre de la page: {page_title}")

                # Vérifier s'il y a des éléments avec data-path
                data_path_elements = await self.page.query_selector_all('[data-path]')

                # Lister les data-path trouvés
                for i, elem in enumerate(data_path_elements[:5]):  # Limiter à 5
                    try:
                        data_path = await elem.get_attribute('data-path')
                        text_content = await elem.inner_text()
                    except:
                        pass

                # Vérifier spécifiquement le sélecteur organic traffic
                organic_elements = await self.page.query_selector_all('a[data-path="overview.summary.click_organic_search_traffic"]')

                for i, elem in enumerate(organic_elements):
                    try:
                        text_content = await elem.inner_text()
                        logger.info(f"🔍 DEBUG - Organic traffic {i+1}: '{text_content}'")
                    except:
                        pass

            except Exception as e:
                logger.warning(f"🔍 DEBUG - Erreur lors de la vérification: {e}")

            # Attendre que les métriques se chargent avec timeout intelligent
            await self.wait_for_metrics_to_load()

            # Scraping des métriques selon spécifications
            metrics = {}

            # 1. Organic Search Traffic
            element = await self.validate_selector_adaptive(
                'a[data-path="overview.summary.click_organic_search_traffic"] span[data-ui-name="Link.Text"]',
                "Organic Search Traffic",
                base_timeout=90000  # Augmenté à 90s car c'est le sélecteur critique
            )
            if element:
                organic_traffic = await element.inner_text()
                metrics['organic_search_traffic'] = organic_traffic
                logger.info(f"✅ Organic Search Traffic: {organic_traffic}")

                # Validation immédiate de l'organic traffic avec logs détaillés
                organic_traffic_clean = organic_traffic.strip().lower()
                logger.info(f"🔍 Validation organic traffic: '{organic_traffic}' -> nettoyé: '{organic_traffic_clean}'")

                if organic_traffic_clean and not organic_traffic_clean.endswith(('k', 'm')):
                    logger.warning(f"⚠️ Organic traffic invalide: '{organic_traffic}' (nettoyé: '{organic_traffic_clean}') - Status 'na' pour cette boutique")
                    logger.info(f"📝 Sauvegarde des données avant retour 'na': {metrics}")
                    # Sauvegarder les données avant de retourner 'na'
                    self.session_data['data']['domain_overview'] = metrics
                    logger.info(f"💾 Données sauvegardées dans session_data: {self.session_data['data']['domain_overview']}")
                    # Retourner un code spécial pour indiquer que la boutique doit être marquée comme 'na'
                    return 'na'
                else:
                    logger.info(f"✅ Organic traffic valide: '{organic_traffic}' se termine par 'k' ou 'm'")

                # Organic Search Traffic trouvé - utiliser des timeouts courts pour les autres métriques
                logger.info("🚀 Page chargée confirmée - utilisation de timeouts courts pour les autres métriques")

                # Scraper les autres métriques en parallèle
                async def scrape_avg_visit_duration():
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.engagement_metrics.visit_duration"] span[data-ui-name="Link.Text"]',
                        "Average Visit Duration", base_timeout=60000,
                    )
                    if element:
                        value = await element.inner_text()
                        logger.info(f"✅ Average Visit Duration: {value}")
                        return value
                    else:
                        logger.info("❌ Average Visit Duration: Sélecteur non trouvé|Erreur")
                        return "Sélecteur non trouvé|Erreur"

                async def scrape_bounce_rate():
                    element = await self.validate_selector_adaptive(
                        'a[data-path="overview.engagement_metrics.bounce_rate"] span[data-ui-name="Link.Text"]',
                        "Bounce Rate",
                        base_timeout=45000
                    )
                    if element:
                        value = await element.inner_text()
                        logger.info(f"✅ Bounce Rate: {value}")
                        return value
                    else:
                        logger.info("❌ Bounce Rate: Sélecteur non trouvé|Erreur")
                        return "Sélecteur non trouvé|Erreur"

                # 2. Paid Search Traffic (en parallèle avec les autres métriques)
                async def scrape_paid_search_traffic():
                    element = await self.validate_selector_adaptive(
                        'div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]',
                        "Paid Search Traffic",
                        base_timeout=30000  # Timeout court car page déjà chargée
                    )
                    if element:
                        paid_traffic = await element.inner_text()
                        logger.info(f"✅ Paid Search Traffic: {paid_traffic}")
                        
                        # Validation avec la même règle (k ou m)
                        paid_traffic_clean = paid_traffic.strip().lower()
                        if paid_traffic_clean and not paid_traffic_clean.endswith(('k', 'm')):
                            logger.warning(f"⚠️ Paid traffic invalide: '{paid_traffic}' - marqué comme 'na'")
                            return "na"
                        return paid_traffic
                    else:
                        logger.info("❌ Paid Search Traffic: Sélecteur non trouvé|Erreur")
                        return "Sélecteur non trouvé|Erreur"

                # Exécuter les trois scrapings en parallèle
                logger.info("🔄 Scraping parallèle des métriques...")
                avg_duration, bounce_rate, paid_traffic = await asyncio.gather(
                    scrape_avg_visit_duration(),
                    scrape_bounce_rate(),
                    scrape_paid_search_traffic(),
                    return_exceptions=True
                )

                # Gérer les exceptions
                if isinstance(avg_duration, Exception):
                    logger.error(f"❌ Erreur Average Visit Duration: {avg_duration}")
                    avg_duration = "Erreur"
                if isinstance(bounce_rate, Exception):
                    logger.error(f"❌ Erreur Bounce Rate: {bounce_rate}")
                    bounce_rate = "Erreur"
                if isinstance(paid_traffic, Exception):
                    logger.error(f"❌ Erreur Paid Search Traffic: {paid_traffic}")
                    paid_traffic = "Erreur"

                metrics['avg_visit_duration'] = avg_duration
                metrics['bounce_rate'] = bounce_rate
                metrics['paid_search_traffic'] = paid_traffic

            else:
                metrics['organic_search_traffic'] = "Sélecteur non trouvé|Erreur"

                # Organic Search Traffic NON trouvé - utiliser des timeouts normaux
                logger.info("⚠️ Page pas complètement chargée - utilisation de timeouts normaux")

                # 2. Average Visit Duration (timeout normal)
                element = await self.validate_selector_adaptive(
                    'a[data-path="overview.engagement_metrics.visit_duration"] span[data-ui-name="Link.Text"]',
                    "Average Visit Duration", base_timeout=60000
                )
                if element:
                    metrics['avg_visit_duration'] = await element.inner_text()
                    logger.info(f"✅ Average Visit Duration: {metrics['avg_visit_duration']}")
                else:
                    metrics['avg_visit_duration'] = "Sélecteur non trouvé|Erreur"

                # 3. Bounce Rate (timeout normal)
                element = await self.validate_selector_adaptive(
                    'a[data-path="overview.engagement_metrics.bounce_rate"] span[data-ui-name="Link.Text"]',
                    "Bounce Rate", base_timeout=45000
                )
                if element:
                    metrics['bounce_rate'] = await element.inner_text()
                    logger.info(f"✅ Bounce Rate: {metrics['bounce_rate']}")
                else:
                    metrics['bounce_rate'] = "Sélecteur non trouvé|Erreur"

                # 4. Paid Search Traffic (timeout normal)
                element = await self.validate_selector_adaptive(
                    'div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]',
                    "Paid Search Traffic", base_timeout=30000
                )
                if element:
                    paid_traffic = await element.inner_text()
                    # Validation avec la même règle (k ou m)
                    paid_traffic_clean = paid_traffic.strip().lower()
                    if paid_traffic_clean and not paid_traffic_clean.endswith(('k', 'm')):
                        logger.warning(f"⚠️ Paid traffic invalide: '{paid_traffic}' - marqué comme 'na'")
                        metrics['paid_search_traffic'] = "na"
                    else:
                        metrics['paid_search_traffic'] = paid_traffic
                    logger.info(f"✅ Paid Search Traffic: {metrics['paid_search_traffic']}")
                else:
                    metrics['paid_search_traffic'] = "Sélecteur non trouvé|Erreur"

            self.session_data['data']['domain_overview'] = metrics
            logger.info("✅ Scraping Domain Overview terminé")
            return True

        except Exception as e:
            error_msg = f"❌ Erreur scraping Domain Overview: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False

    async def scrape_organic_search(self, domain: str, date_range: str):
        """Scraping de la page Organic Search"""
        logger.info(f"📊 Scraping Organic Search pour {domain}")

        try:
            # Construction de l'URL
            url = f"https://sam.mytoolsplan.xyz/analytics/organic/overview/?db=us&q={domain}&searchType=domain&date={date_range}"

            # Navigation
            success = await self.navigate_with_smart_timeout(url, "Organic Search")
            if not success:
                return False

            await asyncio.sleep(1)  # Optimisé: réduit de 2-4s à 1s

            # Vérifier si on est redirigé vers login ou si la page affiche le message de login
            current_url = self.page.url

            # Vérifier l'URL ET le contenu de la page
            login_redirected = False

            # 1. Vérifier l'URL (logique existante)
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                login_redirected = True
                logger.info("   🔐 Redirection vers login détectée (URL)")

            # 2. Vérifier le contenu de la page pour le message de login et localStorage.clear()
            try:
                page_content = await self.page.content()
                
                # Détecter localStorage.clear() - on ne peut rien faire, c'est un blocage anti-bot
                if "localStorage.clear()" in page_content:
                    logger.error("   ❌ localStorage.clear() détecté - blocage anti-bot, impossible de continuer")
                    return False
                
                # Détecter les messages de login
                if "If you are a registered member, please login" in page_content:
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté dans le contenu de la page")
                elif "please login" in page_content.lower() and "registered member" in page_content.lower():
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté (variante)")
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")

            if login_redirected:
                logger.info("   🔐 Redirection vers login détectée, authentification...")
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=30000)

                await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
                await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)

                await self.page.fill('input[name="amember_login"]', config.config.MYTOOLSPLAN_USERNAME)
                await self.page.fill('input[name="amember_pass"]', config.config.MYTOOLSPLAN_PASSWORD)
                await self.page.click('input[type="submit"]')

                await self.page.wait_for_url("**/member", timeout=15000)
                logger.info("   ✅ Authentification réussie")

                # Re-navigation vers Organic Search
                await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)  # Optimisé: réduit de 10s à 5s

                        # DEBUG: Vérifier le contenu de la page avant scraping
            try:
                page_title = await self.page.title()
                logger.info(f"🔍 DEBUG - Titre de la page: {page_title}")

                # Vérifier s'il y a des éléments avec data-path
                data_path_elements = await self.page.query_selector_all('[data-path]')

                # Lister les data-path trouvés
                for i, elem in enumerate(data_path_elements[:5]):  # Limiter à 5
                    try:
                        data_path = await elem.get_attribute('data-path')
                        text_content = await elem.inner_text()
                    except:
                        pass

                # Vérifier spécifiquement le sélecteur organic traffic
                organic_elements = await self.page.query_selector_all('a[data-path="overview.summary.click_organic_search_traffic"]')

                for i, elem in enumerate(organic_elements):
                    try:
                        text_content = await elem.inner_text()
                        logger.info(f"🔍 DEBUG - Organic traffic {i+1}: '{text_content}'")
                    except:
                        pass

            except Exception as e:
                logger.warning(f"🔍 DEBUG - Erreur lors de la vérification: {e}")

            # Attendre que les métriques se chargent avec timeout intelligent
            await self.wait_for_metrics_to_load()

            # Scraping des métriques
            metrics = {}

            # Branded Traffic
            element = await self.validate_selector_adaptive(
                'div[data-at="summary-branded-traffic"] > div > div > span[data-at="summary-value"][data-ui-name="Text"]',
                "Branded Traffic",
                base_timeout=30000  # Timeout normal pour cette métrique importante
            )
            if element:
                metrics['branded_traffic'] = await element.inner_text()
                logger.info(f"✅ Branded Traffic: {metrics['branded_traffic']}")
            else:
                metrics['branded_traffic'] = "Sélecteur non trouvé|Erreur"

            self.session_data['data']['organic_search'] = metrics
            logger.info("✅ Scraping Organic Search terminé")
            return True

        except Exception as e:
            error_msg = f"❌ Erreur scraping Organic Search: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False

    async def create_traffic_folder(self, domain: str):
        """Gère la sélection/création de dossier pour l'analyse de trafic via navigation manuelle"""
        logger.info(f"📁 Gestion du dossier Traffic Analysis pour {domain}")

        try:
            # S'assurer qu'on est sur Semrush
            current_url = self.page.url
            if "sam.mytoolsplan.xyz" not in current_url:
                logger.info("   🌐 Navigation vers Semrush...")
                await self.page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(3)
                
                # Vérifier si on est bien sur Semrush
                current_url = self.page.url
                if "sam.mytoolsplan.xyz" not in current_url:
                    logger.error("   ❌ Impossible d'accéder à Semrush")
                    return False

            # Navigation manuelle vers Traffic Analytics
            logger.info("   🖱️ Navigation manuelle vers Traffic Analytics...")
            
            # Étape 1: Cliquer sur "Traffic & Market"
            traffic_market_button = await self.page.query_selector('a[aria-label="Traffic & Market"]')
            if not traffic_market_button:
                logger.error("   ❌ Bouton 'Traffic & Market' non trouvé")
                return False
                
            logger.info("   ✅ Bouton 'Traffic & Market' trouvé, clic...")
            await traffic_market_button.click()
            await asyncio.sleep(5)  # Attendre plus longtemps que la page se charge
            
            # Étape 2: Cliquer sur "Traffic Analytics" - plusieurs sélecteurs possibles
            traffic_analytics_button = await self.page.query_selector('srf-sidebar-list-item[label="Traffic Analytics"]') or \
                                      await self.page.query_selector('srf-sidebar-list-item[nav-item="tm-traffic-overview"]') or \
                                      await self.page.query_selector('srf-sidebar-list-item[data-path="navigation.sidebar.analytics.traffic.overview"]') or \
                                      await self.page.query_selector('srf-sidebar-list-item[href*="traffic-overview"]')
            if not traffic_analytics_button:
                logger.error("   ❌ Bouton 'Traffic Analytics' non trouvé")
                return False
                
            logger.info("   ✅ Bouton 'Traffic Analytics' trouvé, clic...")
            await traffic_analytics_button.click()
            await asyncio.sleep(5)  # Attendre que la page Traffic Analytics se charge
            
            # Vérifier qu'on est bien sur la page Traffic Analytics
            current_url = self.page.url
            page_title = await self.page.title()
            logger.info(f"   📍 URL après navigation: {current_url}")
            logger.info(f"   📄 Titre de la page: {page_title}")
            
            if "traffic" in current_url.lower() or "traffic" in page_title.lower():
                logger.info("   ✅ Navigation vers Traffic Analytics réussie")
                return True
            else:
                logger.error("   ❌ Navigation vers Traffic Analytics échouée")
                return False

        except Exception as e:
            logger.error(f"   ❌ Erreur lors de la navigation manuelle: {e}")
            return False

            # Étape 1: Cliquer sur le dropdown pour ouvrir la liste des dossiers
            dropdown_button = await self.validate_selector_adaptive(
                'button[data-ui-name="DropdownMenu.Trigger"]',
                "Dropdown des dossiers"
            )
            if not dropdown_button:
                logger.warning("⚠️ Dropdown des dossiers non trouvée, tentative de fallback...")
                
                # Fallback: Vérifier s'il y a un input direct pour entrer le domaine
                input_target = await self.validate_selector_adaptive(
                    'input[aria-label="Input target"][data-testid="input-0"]',
                    "Input target direct"
                )
                
                if input_target:
                    logger.info("✅ Interface directe détectée, saisie du domaine...")
                    
                    # Saisir le domaine dans l'input
                    await input_target.fill(domain)
                    logger.info(f"   📝 Domaine saisi: {domain}")
                    
                    # Cliquer sur le bouton d'analyse
                    analyze_button = await self.validate_selector_adaptive(
                        'button[data-testid="analyze-cta"][type="submit"]',
                        "Bouton d'analyse"
                    )
                    
                    if analyze_button:
                        await analyze_button.click()
                        logger.info("✅ Bouton d'analyse cliqué")
                        
                        # Attendre le rechargement de la page
                        await asyncio.sleep(5)
                        logger.info("✅ Page rechargée après analyse")
                        
                        return True
                    else:
                        logger.error("❌ Bouton d'analyse non trouvé")
                        await self.save_error_page_content("analyze_button_error", "Bouton d'analyse non trouvé")
                        return False
                else:
                    logger.error("❌ Impossible d'ouvrir le dropdown des dossiers et pas d'interface directe")
                    await self.save_error_page_content("dropdown_error", "Impossible d'ouvrir le dropdown des dossiers et pas d'interface directe")
                    return False

            await dropdown_button.click()
            await asyncio.sleep(1)  # Optimisé: réduit de 3s à 1s
            logger.info("✅ Dropdown ouvert")

            # Étape 2: Vérifier si le domaine existe déjà dans la liste
            try:
                logger.info(f"   🔍 Recherche du domaine '{domain}' dans la liste...")

                # Attendre que le contenu du dropdown soit chargé
                scroll_area = await self.validate_selector_adaptive(
                    'div[data-ui-name="ScrollArea"]',
                    "Zone de scroll du dropdown",
                    base_timeout=30000
                )
                if not scroll_area:
                    return False

                await asyncio.sleep(2)

                # Chercher tous les éléments de la liste
                list_items = await self.page.query_selector_all('div[data-test="folders-selector-list-item"]')
                logger.info(f"   📊 Nombre d'éléments trouvés: {len(list_items)}")

                domain_found = False
                found_item = None  # Stocker la référence à l'élément trouvé
                for item in list_items:
                    try:
                        # Chercher le nom du domaine dans l'élément
                        domain_text = await item.query_selector('span[data-test="folders-selector-list-item-domain"]')
                        if domain_text:
                            domain_value = await domain_text.inner_text()
                            logger.info(f"   🔍 Vérification: {domain_value}")

                            # Extraire le nom du domaine sans le protocole pour la comparaison
                            domain_name = domain.replace('https://', '').replace('http://', '')
                            if domain_value == domain_name:
                                logger.info(f"   ✅ Domaine '{domain}' trouvé dans la liste")
                                domain_found = True
                                found_item = item  # Stocker la référence
                                break
                    except Exception as e:
                        continue

                if domain_found and found_item:
                    logger.info("   ✅ Domaine trouvé, sélection du domaine...")
                    # Cliquer sur le domaine trouvé pour le sélectionner
                    await found_item.click()
                    await asyncio.sleep(2)
                    logger.info("   ✅ Domaine sélectionné, continuation...")
                    return True
                else:
                    logger.info(f"   ❌ Domaine '{domain}' non trouvé, création nécessaire...")

            except Exception as e:
                logger.error(f"❌ Erreur lors de la recherche du domaine: {e}")
                return False

            # Étape 3: Créer un nouveau dossier si le domaine n'existe pas
            create_button = await self.validate_selector_adaptive(
                'div[data-test="create-folder-button"]',
                "Bouton de création de dossier"
            )
            if not create_button:
                logger.error("❌ Bouton de création non trouvé")
                await self.save_error_page_content("create_button_error", "Bouton de création non trouvé")
                return False

            # Cliquer sur le span à l'intérieur du bouton
            create_span = await create_button.query_selector('span[data-ui-name="DropdownMenu.Item.Content"][role="button"]')
            if not create_span:
                logger.error("❌ Span de création non trouvé")
                return False

            await create_span.click()
            logger.info("✅ Bouton de création cliqué")

            # Étape 4: Attendre l'apparition du popup
            popup_input = await self.validate_selector_adaptive(
                'input[placeholder="Enter a business name"]',
                "Popup de création de dossier",
                base_timeout=60000
            )
            if not popup_input:
                logger.error("❌ Popup de création non trouvé")
                await self.save_error_page_content("popup_error", "Popup de création non trouvé")
                return False

            logger.info("✅ Popup de création détecté")

            # Étape 5: Remplir les informations du dossier
            try:
                logger.info("   📝 Remplissage des informations du dossier...")

                # Nom du dossier
                await self.page.fill('input[placeholder="Enter a business name"]', f"Traffic Analysis - {domain}")

                # URL du site
                url_input = await self.validate_selector_adaptive(
                    'input[placeholder="Enter a domain or subdomain"]',
                    "Champ URL du site"
                )
                if url_input:
                    await url_input.fill(domain)

                logger.info("✅ Informations du dossier remplies")

            except Exception as e:
                logger.error(f"❌ Erreur lors du remplissage: {e}")
                return False

            # Étape 6: Valider la création
            submit_button = await self.validate_selector(
                'button[type="submit"]',
                "Bouton de validation"
            )
            if not submit_button:
                logger.error("❌ Bouton de validation non trouvé")
                return False

            await submit_button.click()
            logger.info("✅ Validation effectuée")

            # Étape 7: Attendre la confirmation (DÉSACTIVÉE - À réactiver plus tard si nécessaire)
            # alert = await self.validate_selector(
            #     'div[role="alert"]',
            #     "Message de confirmation",
            #     timeout=30000
            # )
            # if not alert:
            #     logger.error("❌ Confirmation non trouvée")
            #     return False

            # logger.info("✅ Confirmation reçue")
            logger.info("⚠️ Vérification de confirmation désactivée - continuation...")

            # Étape 8: Attendre le rechargement de la page
            body = await self.validate_selector(
                'body',
                "Rechargement de la page",
                timeout=30000
            )
            if not body:
                logger.error("❌ Rechargement page échoué")
                return False

            await asyncio.sleep(5)
            logger.info("✅ Page rechargée")

            # Étape 3e: Sauvegarde finale du dossier
            try:
                logger.info("   💾 Sauvegarde finale du dossier...")
                save_button = await self.page.wait_for_selector(
                    'button[data-testid="list-submit"][data-ui-name="Button"][type="button"]',
                    timeout=10000
                )
                if save_button:
                    await save_button.click()
                    await asyncio.sleep(5)
                    logger.info("✅ Sauvegarde effectuée")
                else:
                    logger.warning("⚠️ Bouton de sauvegarde non trouvé, continuation...")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de la sauvegarde: {e}, continuation...")

            logger.info("✅ Gestion du dossier Traffic Analysis terminée")
            return True

        except Exception as e:
            error_msg = f"❌ Erreur lors de la gestion du dossier: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False

    async def scrape_traffic_analysis(self, domain: str):
        """Scraping de la page Traffic Analysis"""
        logger.info(f"📊 Scraping Traffic Analysis pour {domain}")

        try:
            # Étape 1: Gérer le dossier (nous met déjà sur Traffic Overview)
            folder_created = await self.create_traffic_folder(domain)
            if not folder_created:
                return False

            # On est déjà sur la page Traffic Overview, pas besoin de naviguer à nouveau
            await asyncio.sleep(1)  # Optimisé: réduit de 2s à 1s

            # Vérifier si on est redirigé vers login ou si la page affiche le message de login
            current_url = self.page.url

            # Vérifier l'URL ET le contenu de la page
            login_redirected = False

            # 1. Vérifier l'URL (logique existante)
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                login_redirected = True
                logger.info("   🔐 Redirection vers login détectée (URL)")

            # 2. Vérifier le contenu de la page pour le message de login
            try:
                page_content = await self.page.content()
                if "If you are a registered member, please login" in page_content:
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté dans le contenu de la page")
                elif "please login" in page_content.lower() and "registered member" in page_content.lower():
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté (variante)")
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")

            if login_redirected:
                logger.info("   🔐 Redirection vers login détectée, authentification...")
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded')

                await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
                await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)

                await self.page.fill('input[name="amember_login"]', config.config.MYTOOLSPLAN_USERNAME)
                await self.page.fill('input[name="amember_pass"]', config.config.MYTOOLSPLAN_PASSWORD)
                await self.page.click('input[type="submit"]')

                await self.page.wait_for_url("**/member", timeout=15000)
                logger.info("   ✅ Authentification réussie")

                # Re-navigation vers Traffic Overview
                await self.page.goto("https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/", wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)  # Optimisé: réduit de 10s à 5s

            # Attendre que les métriques se chargent
            await self.wait_for_metrics_to_load()

            # Scraping des métriques en parallèle
            async def scrape_visits():
                # Vérifier l'authentification avant de scraper
                await self.check_and_authenticate()
                
                # Chercher d'abord la ligne du domaine actuel
                domain = self.session_data.get('shop_url', '').replace('https://', '').replace('http://', '')
                domain_selector = f'div[data-crop-value*="{domain}"]'
                
                # Trouver la ligne du domaine
                domain_row = await self.page.query_selector(domain_selector)
                if not domain_row:
                    logger.error(f"❌ Ligne du domaine {domain} non trouvée")
                    return "Domaine non trouvé"
                
                # Chercher la cellule visits dans cette ligne
                visits_cell = await domain_row.query_selector('div[name="visits"] span[data-ui-name="Text"]')
                if visits_cell:
                    value = await visits_cell.inner_text()
                    logger.info(f"✅ Visits pour {domain}: {value}")
                    return value
                else:
                    logger.info("❌ Visits: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"

            async def scrape_purchase_conversion():
                # Vérifier l'authentification avant de scraper
                await self.check_and_authenticate()
                
                # Chercher d'abord la ligne du domaine actuel
                domain = self.session_data.get('shop_url', '').replace('https://', '').replace('http://', '')
                domain_selector = f'div[data-crop-value*="{domain}"]'
                
                # Trouver la ligne du domaine
                domain_row = await self.page.query_selector(domain_selector)
                if not domain_row:
                    logger.error(f"❌ Ligne du domaine {domain} non trouvée")
                    return "Domaine non trouvé"
                
                # Chercher la cellule conversion dans cette ligne
                conversion_cell = await domain_row.query_selector('div[name="conversion"] span[data-ui-name="Text"]')
                if conversion_cell:
                    value = await conversion_cell.inner_text()
                    logger.info(f"✅ Purchase Conversion pour {domain}: {value}")
                    return value
                else:
                    logger.info("❌ Purchase Conversion: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"

            # Exécuter les scrapings en parallèle
            logger.info("🔄 Scraping parallèle Traffic Analysis...")
            visits, purchase_conversion = await asyncio.gather(
                scrape_visits(),
                scrape_purchase_conversion(),
                return_exceptions=True
            )

            # Gérer les exceptions
            if isinstance(visits, Exception):
                logger.error(f"❌ Erreur Visits: {visits}")
                visits = "Erreur"
            if isinstance(purchase_conversion, Exception):
                logger.error(f"❌ Erreur Purchase Conversion: {purchase_conversion}")
                purchase_conversion = "Erreur"

            # Sauvegarder les résultats
            metrics = {
                'visits': visits,
                'purchase_conversion': purchase_conversion
            }

            self.session_data['data']['traffic_analysis'] = metrics
            logger.info("✅ Scraping Traffic Analysis terminé")
            return True

        except Exception as e:
            error_msg = f"❌ Erreur scraping Traffic Analysis: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False

    async def save_results(self):
        """Sauvegarde des résultats"""
        try:
            # Créer le répertoire results
            results_dir = Path('results')
            results_dir.mkdir(exist_ok=True)

            # Nom du fichier avec timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            filename = f"production_results_{timestamp}.json"
            filepath = results_dir / filename

            # Sauvegarder en JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)

            # Sauvegarder aussi en TXT simple selon spécifications
            txt_filename = f"production_results_{timestamp}.txt"
            txt_filepath = results_dir / txt_filename

            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== RÉSULTATS SCRAPING MYTOOLSPLAN ===\n")
                f.write(f"Date: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"Domaine: {self.session_data.get('shop_url', 'N/A')}\n")
                f.write(f"Période: {self.session_data.get('date_range', 'N/A')}\n\n")

                # Domain Overview
                if 'domain_overview' in self.session_data['data']:
                    f.write("=== DOMAIN OVERVIEW ===\n")
                    for key, value in self.session_data['data']['domain_overview'].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")

                # Organic Search
                if 'organic_search' in self.session_data['data']:
                    f.write("=== ORGANIC SEARCH ===\n")
                    for key, value in self.session_data['data']['organic_search'].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")

                # Traffic Analysis
                if 'traffic_analysis' in self.session_data['data']:
                    f.write("=== TRAFFIC ANALYSIS ===\n")
                    for key, value in self.session_data['data']['traffic_analysis'].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")

                # Erreurs
                if self.session_data['errors']:
                    f.write("=== ERREURS ===\n")
                    for error in self.session_data['errors']:
                        f.write(f"- {error}\n")

            logger.info(f"📄 Résultats sauvegardés: {filepath}")
            logger.info(f"📄 Résultats TXT sauvegardés: {txt_filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return None

    async def run_production_scraping(self, domain: str = None):
        """Exécution du scraping de production pour un domaine ou tous les domaines"""
        if domain:
            # Mode single domain (pour tests)
            logger.info(f"🚀 DÉBUT DU SCRAPING DE PRODUCTION POUR: {domain}")
            return await self._scrape_single_domain(domain)
        else:
            # Mode batch processing (production)
            logger.info("🚀 DÉBUT DU SCRAPING DE PRODUCTION BATCH")
            return await self._scrape_all_domains()

    async def _scrape_single_domain(self, domain: str):
        """Scrape un seul domaine (mode test)"""
        try:
            # Configuration du navigateur
            await self.setup_browser()

            # Authentification MyToolsPlan
            auth_success = await self.authenticate_mytoolsplan()
            if not auth_success:
                logger.error("❌ Échec de l'authentification - Arrêt du scraping")
                return False

            # Calcul de la date (mois -2)
            last_month = datetime.now(timezone.utc) - timedelta(days=60)
            date_range = last_month.strftime("%Y%m")
            logger.info(f"📅 Période de scraping: {date_range}")

            # Navigation vers sam.mytoolsplan.xyz
            logger.info("🌐 Navigation vers sam.mytoolsplan.xyz...")
            await self.page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=60000)
            logger.info("✅ Navigation vers sam.mytoolsplan.xyz terminée")

            # Attendre 3 secondes
            logger.info("⏳ Attente de 3 secondes...")
            await asyncio.sleep(3)

            # Scraping des 3 pages selon spécifications
            logger.info("📊 ÉTAPE 1: Scraping Domain Overview...")
            domain_success = await self.scrape_domain_overview(domain, date_range)

            logger.info("📊 ÉTAPE 2: Scraping Organic Search...")
            organic_success = await self.scrape_organic_search(domain, date_range)

            logger.info("📊 ÉTAPE 3: Scraping Traffic Analysis...")
            traffic_success = await self.scrape_traffic_analysis(domain)

            # Sauvegarde des résultats
            self.session_data['shop_url'] = domain
            self.session_data['date_range'] = date_range

            results_file = await self.save_results()

            if results_file:
                logger.info(f"🎉 SCRAPING DE PRODUCTION TERMINÉ AVEC SUCCÈS")
                logger.info(f"📄 Résultats sauvegardés: {results_file}")
                return True
            else:
                logger.error("❌ Erreur lors de la sauvegarde des résultats")
                return False

        except Exception as e:
            error_msg = f"❌ Erreur lors du scraping de production: {e}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
        finally:
            if hasattr(self, 'browser') and self.browser:
                await self.browser.close()
                logger.info("🎉 PRODUCTION TERMINÉE")

    async def _scrape_all_domains(self):
        """Scrape tous les domaines nécessitant un traitement par lots"""
        try:
            # Démarrer le timer global
            self.performance_timers['start_time'] = time.time()
            logger.info("🚀 DÉBUT DU SCRAPING DE PRODUCTION BATCH")

            # Récupérer toutes les boutiques
            logger.info("📊 Récupération de toutes les boutiques...")
            all_shops = api.get_all_shops()

            if not all_shops:
                logger.info("✅ Aucune boutique trouvée")
                return True

            logger.info(f"📊 {len(all_shops)} boutiques récupérées au total")

            # Configuration du navigateur une seule fois
            logger.info("🔧 Configuration du navigateur de production...")
            await self.setup_browser()

            # Authentification une seule fois
            # Calcul de la date (mois -2)
            last_month = datetime.now(timezone.utc) - timedelta(days=60)
            date_range = last_month.strftime("%Y%m")
            logger.info(f"📅 Période de scraping: {date_range}")

            auth_success = await self.authenticate_mytoolsplan()
            if not auth_success:
                logger.error("❌ Échec de l'authentification")
                return False

            # Traitement par lots
            batch_size = 8  # Optimisé: augmenté de 3 à 8 boutiques par lot
            total_success = 0
            total_error = 0

            # Acquérir le lock une seule fois pour toute la session
            logger.info("🔒 Acquisition du lock pour la session complète...")
            if not api.acquire_lock(timeout=30):
                logger.error("❌ Impossible d'acquérir le lock pour la session")
                return False

            for batch_num in range(0, len(all_shops), batch_size):
                batch_start_time = time.time()  # Timer pour ce lot
                batch = all_shops[batch_num:batch_num + batch_size]
                batch_num_display = (batch_num // batch_size) + 1
                total_batches = (len(all_shops) + batch_size - 1) // batch_size

                logger.info(f"📦 LOT {batch_num_display}/{total_batches} - Analyse de {len(batch)} boutiques...")

                # Identifier les boutiques éligibles dans ce lot
                eligible_shops = []
                for shop in batch:
                    if api.is_shop_eligible_for_scraping(shop):
                        eligible_shops.append(shop)

                logger.info(f"🎯 LOT {batch_num_display}: {len(eligible_shops)}/{len(batch)} boutiques éligibles")

                if not eligible_shops:
                    logger.info(f"⏭️ LOT {batch_num_display}: Aucune boutique éligible, passage au lot suivant")
                    continue

                # Traitement de chaque boutique éligible du lot (plus besoin d'acquérir le lock ici)
                batch_success = 0
                batch_error = 0

                for i, shop in enumerate(eligible_shops, 1):
                    domain_start_time = time.time()  # Timer pour ce domaine
                    shop_domain = shop.get('shop_url', 'N/A')
                    logger.info(f"🚀 DÉBUT TRAITEMENT: {shop.get('name', 'N/A')} ({shop_domain})")
                    try:
                        # Utiliser le domaine directement depuis l'API
                        domain = shop.get("shop_url", "N/A")

                        # Réinitialiser les données de session pour chaque domaine
                        self.session_data = {
                            'shop_url': domain,
                            'date_range': date_range,
                            'data': {},
                            'errors': []
                        }

                        # Étape intermédiaire : navigation vers /seo/ pour réchauffer la session (DÉSACTIVÉE)
                        # logger.info("   🌐 Étape intermédiaire : navigation vers /seo/...")
                        # await self.page.goto("https://sam.mytoolsplan.xyz/seo/", wait_until='domcontentloaded', timeout=60000)
                        # await asyncio.sleep(3)

                        # Navigation vers sam.mytoolsplan.xyz
                        logger.info("   🌐 Navigation vers sam.mytoolsplan.xyz...")
                        await self.page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=60000)
                        await asyncio.sleep(3)

                        # Scraping des 3 étapes
                        domain_result = await self.scrape_domain_overview(domain, date_range)

                        # Vérifier si l'organic traffic est invalide
                        if domain_result == 'na':
                            logger.info(f"🔄 Traitement du retour 'na' pour {shop.get('name', 'N/A')}")
                            # Récupérer la valeur organic_traffic même si elle est invalide
                            organic_traffic_value = ""
                            if 'domain_overview' in self.session_data['data']:
                                organic_traffic_value = self.session_data['data']['domain_overview'].get('organic_search_traffic', '')
                                logger.info(f"📊 Valeur organic_traffic récupérée: '{organic_traffic_value}'")
                            else:
                                logger.warning(f"⚠️ Pas de données domain_overview dans session_data")

                            # Marquer la boutique comme 'na' et passer à la suivante
                            analytics_data = {
                                "scraping_status": "na",
                                "organic_traffic": organic_traffic_value,
                                "bounce_rate": "",
                                "average_visit_duration": "",
                                "branded_traffic": "",
                                "conversion_rate": "",
                                "traffic_analysis": {
                                    "visits": "",
                                    "purchase_conversion": ""
                                }
                            }
                            api.update_shop_analytics(shop['id'], analytics_data)
                            logger.info("✅ " + shop.get("shop_name", "N/A") + " - Status 'na' mis à jour")
                            batch_success += 1
                            continue

                        organic_success = await self.scrape_organic_search(domain, date_range)
                        traffic_success = await self.scrape_traffic_analysis(domain)

                        # Calculer le temps pour ce domaine
                        domain_time = time.time() - domain_start_time
                        self.performance_timers['domain_times'].append({
                            'shop_url': domain,
                            'time': domain_time,
                            'success': domain_result and organic_success and traffic_success
                        })
                        logger.info(f"⏱️ Domaine {domain} traité en {domain_time:.1f}s")

                        # Sauvegarder les résultats
                        try:
                            analytics_data = self.format_analytics_for_api()

                            if domain_result and organic_success and traffic_success:
                                # Tout réussi
                                api.update_shop_analytics(shop['id'], analytics_data)
                                logger.info("✅ " + shop.get("shop_name", "N/A") + " - Métriques complètes mises à jour")
                                batch_success += 1
                            else:
                                # Partiellement réussi, marquer avec les données disponibles
                                analytics_data['scraping_status'] = 'partial'
                                analytics_data['metadata'] = json.dumps({
                                    'domain_success': domain_result,
                                    'organic_success': organic_success,
                                    'traffic_success': traffic_success,
                                    'timestamp': datetime.now(timezone.utc).isoformat()
                                })
                                api.update_shop_analytics(shop['id'], analytics_data)
                                logger.info("⚠️ " + shop.get("shop_name", "N/A") + " - Métriques partielles mises à jour")
                                batch_success += 1

                        except Exception as api_error:
                            # Erreur API, marquer comme échoué
                            error_msg = f"Erreur API: {str(api_error)}"
                            api.mark_shop_failed(shop['id'], error_msg)
                            logger.error("❌ " + shop.get("shop_name", "N/A") + " - " + error_msg)
                            batch_error += 1

                        # Pause entre les domaines
                        await asyncio.sleep(1)  # Optimisé: réduit de 2-5s à 1s

                    except Exception as e:
                        # Marquer comme échoué
                        error_msg = f"Erreur critique: {str(e)}"
                        api.mark_shop_failed(shop['id'], error_msg)

                        logger.error("❌ " + shop.get("shop_name", "N/A") + " - " + error_msg)
                        batch_error += 1

                        # Continuer avec le domaine suivant (sauf erreur critique)
                        if "réseau" in str(e).lower() or "connexion" in str(e).lower():
                            logger.error("❌ Erreur critique de connexion, arrêt du traitement")
                            break

                # Calculer le temps pour ce lot
                batch_time = time.time() - batch_start_time
                self.performance_timers['batch_times'].append({
                    'batch_num': batch_num_display,
                    'time': batch_time,
                    'shops_processed': len(eligible_shops),
                    'success': batch_success,
                    'errors': batch_error
                })
                logger.info(f"⏱️ Lot {batch_num_display} traité en {batch_time:.1f}s ({batch_success} réussis, {batch_error} échecs)")

                total_success += batch_success
                total_error += batch_error

                logger.info(f"📊 LOT {batch_num_display} TERMINÉ: {batch_success} réussis, {batch_error} échecs")

                # Pause entre les lots
                if batch_num_display < total_batches:
                    logger.info("⏳ Pause de 5s entre les lots...")  # Optimisé: réduit de 10s à 5s
                    await asyncio.sleep(5)  # Optimisé: réduit de 10s à 5s

            # Calculer les statistiques de performance
            total_time = time.time() - self.performance_timers['start_time']
            avg_domain_time = sum(d['time'] for d in self.performance_timers['domain_times']) / len(self.performance_timers['domain_times']) if self.performance_timers['domain_times'] else 0
            avg_batch_time = sum(b['time'] for b in self.performance_timers['batch_times']) / len(self.performance_timers['batch_times']) if self.performance_timers['batch_times'] else 0

            logger.info(f"🎉 TRAITEMENT TERMINÉ: {total_success} réussis, {total_error} échecs")
            logger.info(f"📊 PERFORMANCE: Total {total_time:.1f}s, Domaine moyen {avg_domain_time:.1f}s, Lot moyen {avg_batch_time:.1f}s")
            logger.info(f"📈 VITESSE: {len(self.performance_timers['domain_times'])/total_time*60:.1f} domaines/minute")

            # Libérer le lock de session
            api.release_lock()

            return True

        except Exception as e:
            error_msg = f"❌ Erreur lors du traitement batch: {e}"
            logger.error(error_msg)
            # Libérer le lock en cas d'erreur
            try:
                api.release_lock()
            except:
                pass
            return False
        finally:
            if hasattr(self, 'browser') and self.browser:
                await self.browser.close()
                logger.info("🎉 PRODUCTION TERMINÉE")

    async def add_human_interactions(self):
        """Ajoute des interactions humaines aléatoires pour éviter la détection de bot"""
        try:
            # Mouvement de souris aléatoire
            x = random.randint(100, 700)
            y = random.randint(100, 500)
            await self.page.mouse.move(x, y)
            logger.info(f"🖱️ Mouvement souris vers ({x}, {y})")
            
            # Clic aléatoire
            await self.page.mouse.down()
            await asyncio.sleep(0.1)
            await self.page.mouse.up()
            logger.info("🖱️ Clic souris")
            
            # Scroll aléatoire
            scroll_y = random.randint(-300, 300)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_y})")
            logger.info(f"📜 Scroll de {scroll_y}px")
            
            # Pause aléatoire
            pause_time = random.uniform(0.5, 2.0)
            await asyncio.sleep(pause_time)
            logger.info(f"⏸️ Pause de {pause_time:.1f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors des interactions humaines: {e}")
            return False

    async def capture_diagnostic_info(self, step_name: str):
        """Capture des informations de diagnostic à chaque étape"""
        try:
            current_url = self.page.url
            page_title = await self.page.title()
            
            # Capturer les éléments visibles importants
            diagnostic_info = {
                "step": step_name,
                "url": current_url,
                "title": page_title,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Vérifier la présence d'éléments clés
            elements_to_check = [
                ('input[name="amember_login"]', 'Login input'),
                ('input[name="amember_pass"]', 'Password input'),
                ('input[type="submit"]', 'Submit button'),
                ('button[data-ui-name="DropdownMenu.Trigger"]', 'Dropdown button'),
                ('div[data-test="folders-selector-list-item"]', 'Folder list items'),
                ('span[data-test="folders-selector-list-item-domain"]', 'Domain spans')
            ]
            
            visible_elements = []
            for selector, description in elements_to_check:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        visible_elements.append(f"{description}: {'VISIBLE' if is_visible else 'HIDDEN'}")
                    else:
                        visible_elements.append(f"{description}: NOT_FOUND")
                except Exception as e:
                    visible_elements.append(f"{description}: ERROR - {str(e)}")
            
            diagnostic_info["visible_elements"] = visible_elements
            
            # Capturer le contenu de la page (texte seulement, pas HTML)
            try:
                page_text = await self.page.evaluate("() => document.body.innerText")
                # Limiter à 500 caractères pour éviter les logs trop longs
                diagnostic_info["page_text_preview"] = page_text[:500] + "..." if len(page_text) > 500 else page_text
            except Exception as e:
                diagnostic_info["page_text_preview"] = f"ERROR: {str(e)}"
            
            # Vérifier localStorage.clear() dans le HTML
            try:
                page_content = await self.page.content()
                has_localstorage_clear = "localStorage.clear()" in page_content
                diagnostic_info["has_localstorage_clear"] = has_localstorage_clear
            except Exception as e:
                diagnostic_info["has_localstorage_clear"] = f"ERROR: {str(e)}"
            
            # Logger les informations de diagnostic
            logger.info(f"🔍 DIAGNOSTIC - {step_name}:")
            logger.info(f"   📍 URL: {current_url}")
            logger.info(f"   📄 Titre: {page_title}")
            logger.info(f"   🕒 Timestamp: {diagnostic_info['timestamp']}")
            logger.info(f"   🔍 localStorage.clear(): {diagnostic_info['has_localstorage_clear']}")
            logger.info(f"   👁️ Éléments visibles:")
            for element_info in visible_elements:
                logger.info(f"      • {element_info}")
            logger.info(f"   📝 Texte de la page: {diagnostic_info['page_text_preview']}")
            
            return diagnostic_info
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la capture de diagnostic: {e}")
            return {"step": step_name, "error": str(e)}



async def main():
    """Fonction principale de production"""
    # Configuration du logging
    setup_logging()
    logger.info("🏭 DÉMARAGE DU SCRAPER DE PRODUCTION")

    # Valider la configuration
    try:
        config.config.validate_credentials()
        logger.info("✅ Configuration validée")
    except ValueError as e:
        logger.error(f"❌ Erreur de configuration: {e}")
        return

    # Afficher la configuration
    config.config.print_config_summary()

    # Créer le scraper de production
    scraper = ProductionScraper()

    # Lancer le scraping complet (mode batch par défaut)
    success = await scraper.run_production_scraping()

    if success:
        logger.info("🎉 PRODUCTION TERMINÉE AVEC SUCCÈS")
    else:
        logger.error("❌ PRODUCTION ÉCHOUÉE")

if __name__ == "__main__":
    asyncio.run(main())
