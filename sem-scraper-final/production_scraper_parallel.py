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
import sys
import os
sys.path.append(os.getcwd())
from typing import Dict, List, Optional
import sqlite3

# Imports pour la refactorisation
from api_client import APIClient

import config
from playwright.async_api import async_playwright
from trendtrack_api import TrendTrackAPI as api

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
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.lock_file = "scraping_lock_global.lock"
        self.lock_dir = Path("locks")
        self.lock_dir.mkdir(exist_ok=True)
        self.lock_path = self.lock_dir / self.lock_file
    
    def acquire_lock(self) -> bool:
        """Acquiert le lock global (un seul lock pour tous les workers)"""
        try:
            if self.lock_path.exists():
                # Vérifier si le lock est ancien (plus de 5 minutes)
                lock_age = time.time() - self.lock_path.stat().st_mtime
                if lock_age > 300:  # 5 minutes
                    logger.warning(f"⚠️ Worker {self.worker_id}: Lock ancien détecté, suppression...")
                    self.lock_path.unlink()
                else:
                    logger.warning(f"⚠️ Worker {self.worker_id}: Lock global déjà existant")
                    return False
            
            # Créer le lock global
            with open(self.lock_path, 'w') as f:
                f.write(f"Global Lock - Worker {self.worker_id} - {datetime.now(timezone.utc)}")
            
            logger.info(f"✅ Worker {self.worker_id}: Lock global acquis")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur acquisition lock: {e}")
            return False
    
    def release_lock(self):
        """Libère le lock global"""
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
                logger.info(f"✅ Worker {self.worker_id}: Lock global libéré")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur libération lock: {e}")
    
    def is_locked(self) -> bool:
        """Vérifie si le lock global existe"""
        return self.lock_path.exists()

class ParallelProductionScraper:
    """Scraper de production parallélisé avec session partagée"""
    
    def __init__(self, worker_id: int, max_shops: int = None):
        self.worker_id = worker_id
        self.max_shops = max_shops
        self.context = None
        self.page = None
        self.session_data = {'data': {}}
        self.metrics_found = 0
        self.metrics_not_found = 0
        self.lock_manager = LockManager(worker_id)
        
        # Initialisation de l'APIClient pour la refactorisation
        self.api_client = APIClient()
        
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
    
    async def get_organic_traffic_via_api_OLD(self, domain: str) -> Optional[Dict[str, str]]:
        """Récupère le traffic organique et payant via l'API organic.Summary"""
        try:
            
            target_date = self.calculate_target_date()
            
            # Nettoyer le domaine (enlever https://, http://, www.)
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            
            logger.info(f"🌐 Worker {self.worker_id}: Domaine nettoyé: {clean_domain}")
            
            # Navigation vers sam.mytoolsplan.xyz pour les appels API (comme dans l'ancien code qui marchait)
            logger.info(f"🌐 Worker {self.worker_id}: Navigation vers sam.mytoolsplan.xyz pour les appels API...")
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
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
    
    async def get_organic_traffic_via_api(self, domain: str) -> Optional[Dict[str, str]]:
        """
        Version refactorisée utilisant APIClient.
        MÊME LOGIQUE, MÊME FORMAT DE RETOUR que l'ancienne méthode.
        """
        try:
            
            target_date = self.calculate_target_date()
            
            # Nettoyer le domaine (enlever https://, http://, www.)
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            
            logger.info(f"🌐 Worker {self.worker_id}: Domaine nettoyé: {clean_domain}")
            
            # Utiliser APIClient au lieu du code direct
            params = self.api_client.get_organic_params(clean_domain, target_date)
            result = await self.api_client.call_rpc_api(self.page, "organic.Summary", params, self.worker_id)
            
            if not result:
                logger.info(f"❌ Worker {self.worker_id}: Aucune donnée trouvée via API")
                return None
            
            if result.get('result') and len(result['result']) > 0:
                # Chercher l'entrée USA (MÊME LOGIQUE que l'ancienne méthode)
                us_entry = None
                for entry in result['result']:
                    if entry.get('database') == 'us':
                        us_entry = entry
                        break
                
                if not us_entry:
                    us_entry = result['result'][0]
                
                organic_raw = us_entry.get('organicTraffic', 0)
                paid_raw = us_entry.get('adwordsTraffic', 0)  # Traffic payant direct
                
                # GESTION DU STATUT 'na' - MÊME LOGIQUE que l'ancienne méthode
                if organic_raw < 1000:
                    logger.info(f"⚠️ Worker {self.worker_id}: Organic Traffic < 1000 ({organic_raw}) - Statut 'na'")
                    return 'na'
                
                # TOUJOURS RETOURNER LES VALEURS RAW (BRUTES)
                logger.info(f"✅ Worker {self.worker_id}: Organic Traffic: {organic_raw}, Paid Traffic: {paid_raw}")
                
                # RETOURNER LES VALEURS BRUTES
                return {
                    'organic_search_traffic': str(organic_raw),
                    'paid_search_traffic': str(paid_raw),
                    'organic_raw': organic_raw,
                    'paid_raw': paid_raw,
                    'source': 'organic.Summary API (REFACTORISÉ - RAW)'
                }
            
            logger.info(f"❌ Worker {self.worker_id}: Aucune donnée trouvée via API")
            return None
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.Summary (REFACTORISÉ): {error}")
            return None
    
    def format_number(self, num: int) -> str:
        """Formate un nombre pour l'affichage"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)
    
    async def get_overview_trend_metrics_via_api(self, domain: str) -> Optional[Dict[str, str]]:
        """
        Récupère les métriques manquantes via l'API organic.OverviewTrend.
        Récupère: traffic (total), branded_traffic
        """
        try:
            target_date = self.calculate_target_date()
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            
            # Appel API organic.OverviewTrend
            result = await self.api_client.call_organic_overview_trend_api(self.page, clean_domain, self.worker_id, target_date)
            
            if not result:
                return None
            
            # CORRECTION: Traiter la réponse de l'API avec le bon chemin
            if result.get('data') and result['data'].get('result'):
                overview_data = result['data']['result']
                if overview_data and len(overview_data) > 0:
                    # Prendre la dernière entrée (comme dans les fichiers qui fonctionnent)
                    latest_data = overview_data[-1]
                    
                    # Extraire les métriques selon la documentation
                    traffic_raw = latest_data.get('traffic', 0)
                    branded_traffic_raw = latest_data.get('trafficBranded', 0)
                    
                    logger.info(f"✅ Worker {self.worker_id}: OverviewTrend - Traffic: {traffic_raw}, Branded: {branded_traffic_raw}")
                    
                    return {
                        'traffic': str(traffic_raw),
                        'branded_traffic': str(branded_traffic_raw),
                        'traffic_raw': traffic_raw,
                        'branded_traffic_raw': branded_traffic_raw,
                        'source': 'organic.OverviewTrend API'
                    }
            
            return None
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.OverviewTrend: {error}")
            return None
    
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
            user_data_dir='./session-profile-shared',
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
        """Authentification MyToolsPlan avec gestion des locks pour session partagée"""
        logger.info(f"🔐 Worker {self.worker_id}: Authentification MyToolsPlan...")

        # Seul le Worker 0 fait l'authentification
        if self.worker_id == 0:
            logger.info(f"🔑 Worker {self.worker_id}: Authentification principale (Worker 0)")
            
            # Acquérir le lock pour l'authentification
            if not self.lock_manager.acquire_lock():
                logger.warning(f"⚠️ Worker {self.worker_id}: Impossible d'acquérir le lock d'authentification")
                return False
            
            try:
                # Navigation vers la page de login
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=20000)  # Réduit de 30s à 20s
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
                await asyncio.sleep(1)  # Réduit de 2s à 1s

                # Vérifier que nous sommes sur la page membre
                current_url = self.page.url
                logger.info(f"✅ Worker {self.worker_id}: Login réussi, URL actuelle: {current_url}")

                if "member" not in current_url.lower():
                    logger.error(f"❌ Worker {self.worker_id}: Login échoué - Pas sur la page membre")
                    return False

                # Synchroniser les cookies avec sam.mytoolsplan.xyz
                await self.sync_cookies_with_sam()
                
                logger.info(f"✅ Worker {self.worker_id}: Authentification terminée")
                return True

            except Exception as e:
                error_msg = f"❌ Worker {self.worker_id}: Erreur lors de l'authentification: {e}"
                logger.error(error_msg)
                return False
            finally:
                # Libérer le lock après l'authentification
                self.lock_manager.release_lock()
                logger.info(f"🔓 Worker {self.worker_id}: Lock d'authentification libéré")
        
        else:
            # Les autres workers attendent que l'authentification soit terminée
            logger.info(f"⏳ Worker {self.worker_id}: Attente de l'authentification par Worker 0...")
            
            # Attendre que le lock soit libéré (authentification terminée)
            max_wait_time = 300  # 5 minutes max
            wait_time = 0
            while self.lock_manager.is_locked() and wait_time < max_wait_time:
                await asyncio.sleep(5)
                wait_time += 5
                logger.info(f"⏳ Worker {self.worker_id}: Attente authentification... ({wait_time}s)")
            
            if wait_time >= max_wait_time:
                logger.error(f"❌ Worker {self.worker_id}: Timeout attente authentification")
                return False
            
            logger.info(f"✅ Worker {self.worker_id}: Authentification terminée par Worker 0")
            return True
    
    async def sync_cookies_with_sam(self):
        """Synchronisation des cookies avec sam.mytoolsplan.xyz (optimisée)"""
        logger.info(f"🔄 Worker {self.worker_id}: Synchronisation des cookies avec sam.mytoolsplan.xyz...")
        
        try:
            # Récupérer les cookies d'authentification
            cookies = await self.context.cookies()
            auth_cookies = [c for c in cookies if c['name'] in ['amember_login', 'amember_pass_enc']]
            
            logger.info(f"📊 Worker {self.worker_id}: Cookies récupérés: {len(cookies)} cookies")
            logger.info(f"🔍 Worker {self.worker_id}: {len(auth_cookies)} cookies d'authentification identifiés")
            
            # Définir les cookies d'authentification (pas besoin de navigation supplémentaire)
            if auth_cookies:
                await self.context.add_cookies(auth_cookies)
                logger.info(f"✅ Worker {self.worker_id}: {len(auth_cookies)} cookies d'auth synchronisés")
            
            # Test de la session directement (on est déjà sur app.mytoolsplan.com/member)
            logger.info(f"🔍 Worker {self.worker_id}: Test de la session sur app.mytoolsplan.com/analytics/...")
            await self.page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=10000)  # Réduit de 15s à 10s
            # Pas d'attente supplémentaire nécessaire
            
            current_url = self.page.url
            if "analytics" in current_url:
                logger.info(f"✅ Worker {self.worker_id}: Session synchronisée avec succès sur app.mytoolsplan.com")
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
            
            # Récupération des métriques engagement via API
            engagement_metrics = await self.scrape_engagement_metrics(domain)
            
            # NOUVELLE API: Récupération des métriques manquantes via organic.OverviewTrend
            overview_trend_result = await self.get_overview_trend_metrics_via_api(domain)
            
            # Mettre à jour les métriques
            if 'domain_overview' not in self.session_data['data']:
                self.session_data['data']['domain_overview'] = {}
            
            self.session_data['data']['domain_overview']['avg_visit_duration'] = engagement_metrics.get('avg_visit_duration', '')
            self.session_data['data']['domain_overview']['bounce_rate'] = engagement_metrics.get('bounce_rate', '')
            
            # Ajouter les métriques de organic.OverviewTrend
            if overview_trend_result:
                self.session_data['data']['domain_overview']['traffic'] = overview_trend_result.get('traffic', '')
                self.session_data['data']['domain_overview']['branded_traffic'] = overview_trend_result.get('branded_traffic', '')
                logger.info(f"✅ Worker {self.worker_id}: Métriques organic.OverviewTrend récupérées")
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Échec API organic.OverviewTrend")
                self.session_data['data']['domain_overview']['traffic'] = ""
                self.session_data['data']['domain_overview']['branded_traffic'] = ""
            
            # Récupérer conversion_rate via DOM scraping (SEULE MÉTRIQUE DOM)
            conversion_rate = await self.scrape_purchase_conversion(domain)
            self.session_data['data']['domain_overview']['conversion_rate'] = conversion_rate
            
            # AFFICHAGE DES MÉTRIQUES DANS LES LOGS (SANS ENREGISTREMENT BDD)
            metrics = self.session_data['data']['domain_overview']
            logger.info(f"✅ Worker {self.worker_id}: Domain Overview terminé - Organic: {metrics.get('organic_search_traffic', 'N/A')}, Paid: {metrics.get('paid_search_traffic', 'N/A')}, Traffic: {metrics.get('traffic', 'N/A')}, Branded: {metrics.get('branded_traffic', 'N/A')}, Conversion: {metrics.get('conversion_rate', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur Domain Overview: {e}")
            return False
    
    async def scrape_organic_search(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):
        """Scraping de la page Organic Search - VÉRIFIE AVANT DE SCRAPER"""
        logger.info(f"📊 Worker {self.worker_id}: Organic Search pour {domain}")
        
        try:
            url = f"https://app.mytoolsplan.com/analytics/organic/overview/?db=us&q={domain}&searchType=domain&date={date_range}"
            
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
    
    async def scrape_engagement_metrics_OLD(self, domain: str) -> Dict[str, str]:
        """Récupère bounce_rate et average_visit_duration via l'API engagement"""
        try:
            
            # Nettoyer le domaine
            domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            
            # Navigation vers sam.mytoolsplan.xyz pour l'API engagement (comme dans l'ancien code qui marchait)
            logger.info(f"🌐 Worker {self.worker_id}: Navigation vers sam.mytoolsplan.xyz pour l'API engagement...")
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            api_url = f"/analytics/ta/targ/v2/engagement?target={domain_clean}&device_type=desktop"
            
            result = await self.page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch("{api_url}", {{
                            method: "GET",
                            headers: {{
                                "Content-Type": "application/json"
                            }}
                        }});
                        
                        if (response.ok) {{
                            const data = await response.json();
                            return {{ success: true, data: data }};
                        }} else {{
                            return {{ success: false, error: response.status }}
                        }}
                    }} catch (error) {{
                        return {{ success: false, error: error.toString() }}
                    }}
                }}
            """)
            
            if result.get("success") and result.get("data"):
                api_data = result["data"]
                
                # Vérification du code 200 (comme dans la version qui marchait)
                if api_data.get('code') == 200:
                    engagement_data = api_data.get('data', {})
                    
                    # Conversion des métriques (comme dans la version qui marchait)
                    avg_duration_seconds = engagement_data.get('totalAvgVisitDuration', 0)
                    if avg_duration_seconds:
                        avg_duration_minutes = avg_duration_seconds // 60
                        avg_duration_remaining_seconds = avg_duration_seconds % 60
                        avg_duration_formatted = f"{avg_duration_minutes:02d}:{avg_duration_remaining_seconds:02d}"
                    else:
                        avg_duration_formatted = ""
                    
                    # Pour bounce_rate, on prend la valeur décimale brute (pas de conversion en pourcentage)
                    bounce_rate = engagement_data.get("totalBounceRate", "")
                    
                    logger.info(f"✅ Worker {self.worker_id}: Engagement API - Bounce: {bounce_rate}, Duration: {avg_duration_formatted}")
                    
                    return {
                        "bounce_rate": bounce_rate,
                        "avg_visit_duration": avg_duration_formatted
                    }
                else:
                    logger.warning(f"⚠️ Worker {self.worker_id}: API engagement retourne code: {api_data.get('code')}")
                    return {
                        "bounce_rate": "",
                        "avg_visit_duration": ""
                    }
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: API engagement échouée pour {domain}")
                return {
                    "bounce_rate": "",
                    "avg_visit_duration": ""
                }
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API engagement: {e}")
            return {
                "bounce_rate": "",
                "avg_visit_duration": ""
            }
    
    async def scrape_engagement_metrics(self, domain: str) -> Dict[str, str]:
        """
        Version refactorisée utilisant APIClient.
        MÊME LOGIQUE, MÊME FORMAT DE RETOUR que l'ancienne méthode.
        """
        try:
            
            # Nettoyer le domaine (MÊME LOGIQUE que l'ancienne méthode)
            domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            
            # Utiliser APIClient au lieu du code direct
            result = await self.api_client.call_engagement_api(self.page, domain_clean, self.worker_id)
            
            if not result:
                logger.warning(f"⚠️ Worker {self.worker_id}: API engagement (REFACTORISÉ) échouée pour {domain}")
                return {
                    "bounce_rate": "",
                    "avg_visit_duration": ""
                }
            
            if result.get("success") and result.get("data"):
                api_data = result["data"]
                
                
                # Vérification du code 200 (MÊME LOGIQUE que l'ancienne méthode)
                if api_data.get('code') == 200:
                    engagement_data = api_data.get('data', {})
                    
                    
                    # RETOURNER LES VALEURS BRUTES (RAW)
                    avg_duration_seconds = engagement_data.get('totalAvgVisitDuration', 0)
                    bounce_rate = engagement_data.get("totalBounceRate", "")
                    
                    # TOUJOURS RETOURNER LES VALEURS RAW (BRUTES)
                    logger.info(f"✅ Worker {self.worker_id}: Engagement API - Bounce: {bounce_rate}, Duration: {avg_duration_seconds}")
                    
                    # RETOURNER LES VALEURS BRUTES
                    return {
                        "bounce_rate": str(bounce_rate),
                        "avg_visit_duration": str(avg_duration_seconds)
                    }
                else:
                    logger.warning(f"⚠️ Worker {self.worker_id}: API engagement (REFACTORISÉ) retourne code: {api_data.get('code')}")
                    return {
                        "bounce_rate": "",
                        "avg_visit_duration": ""
                    }
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: API engagement (REFACTORISÉ) échouée pour {domain}")
                return {
                    "bounce_rate": "",
                    "avg_visit_duration": ""
                }
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API engagement (REFACTORISÉ): {e}")
            return {
                "bounce_rate": "",
                "avg_visit_duration": ""
            }
    
    async def scrape_visits_via_api(self, domain: str) -> str:
        """
        Récupère visits via l'API organic.OverviewTrend.
        NOUVELLE MÉTHODE utilisant APIClient.
        """
        try:
            
            # Nettoyer le domaine (MÊME LOGIQUE que les autres APIs)
            domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            
            # Calculer la date cible (MÊME LOGIQUE que les autres APIs)
            target_date = self.calculate_target_date()
            logger.info(f"📅 Worker {self.worker_id}: Date calculée: {target_date}")
            
            # Utiliser APIClient pour organic.OverviewTrend
            params = self.api_client.get_visits_params(domain_clean, target_date)
            result = await self.api_client.call_rpc_api(self.page, "organic.OverviewTrend", params, self.worker_id)
            
            if not result or result.get("error"):
                logger.warning(f"⚠️ Worker {self.worker_id}: API organic.OverviewTrend (visits) échouée pour {domain}")
                return ""
            
            # Parser la réponse (structure à déterminer selon l'API)
            if result.get("result") and len(result["result"]) > 0:
                # Structure à adapter selon la réponse réelle de l'API
                visits_data = result["result"][0]  # Premier élément
                visits = visits_data.get("visits", "")
                
                logger.info(f"✅ Worker {self.worker_id}: Visits (API NOUVELLE): {visits}")
                return str(visits) if visits else ""
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Aucune donnée visits trouvée dans l'API organic.OverviewTrend")
                return ""
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.OverviewTrend (visits): {e}")
            return ""
    
    async def get_folder_id_for_domain(self, domain: str) -> Optional[str]:
        """🔍 Récupère le FID (Folder ID) pour un domaine via l'API"""
        try:
            domain_clean = domain.replace('https://', '').replace('http://', '').replace('www.', '')
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Recherche FID pour domaine: {domain_clean}")
            
            # 1. Récupérer la liste des projets/dossiers existants
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Appel API folders/selector-list...")
            projects_response = await self.page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/apis/v4-raw/folders/api/v0/folders/selector-list?limit=2000&offset=0', {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });
                        
                        if (!response.ok) {
                            return { success: false, error: `HTTP ${response.status}: ${response.statusText}` };
                        }
                        
                        const data = await response.json();
                        return { success: true, data: data };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                }
            """)
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Réponse API folders: {projects_response}")
            
            if projects_response.get('success', False):
                folders_data = projects_response.get('data', {})
                folders = folders_data.get('projects', [])
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - {len(folders)} dossiers trouvés")
                
                # Chercher un dossier existant pour ce domaine
                for folder in folders:
                    folder_domain = folder.get('domain', '').lower()
                    logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Dossier trouvé: domain='{folder_domain}', id='{folder.get('id')}'")
                    if folder_domain == domain_clean.lower() or folder_domain == domain_clean.lower().replace('www.', ''):
                        existing_fid = folder.get('id')
                        if existing_fid:
                            logger.info(f"✅ Worker {self.worker_id}: DEBUG - FID existant trouvé: {existing_fid}")
                            return str(existing_fid)
                
                # Si pas trouvé, créer un nouveau dossier
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Aucun FID existant, création d'un nouveau dossier...")
                api_data = {
                    "properties": [
                        {"name": {"value": f"Traffic Analysis - {domain_clean}"}},
                        {"domain": {"value": domain_clean}}
                    ]
                }
                
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Données création dossier: {api_data}")
                create_response = await self.page.evaluate("""
                    async (apiData) => {
                        try {
                            const response = await fetch('/apis/v4-raw/folders/api/v0/folders', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(apiData)
                            });
                            
                            if (!response.ok) {
                                return { success: false, error: `HTTP ${response.status}: ${response.statusText}` };
                            }
                            
                            const data = await response.json();
                            return { success: true, data: data };
                        } catch (error) {
                            return { success: false, error: error.message };
                        }
                    }
                """, api_data)
                
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Réponse création dossier: {create_response}")
                
                if create_response.get('success', False):
                    new_fid = create_response.get('data', {}).get('folder', {}).get('id')
                    if new_fid:
                        logger.info(f"✅ Worker {self.worker_id}: DEBUG - Nouveau FID créé: {new_fid}")
                        return str(new_fid)
                        
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Erreur API projets: {projects_response.get('error', '')}")
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur récupération FID: {e}")
            
        return None

    async def scrape_purchase_conversion(self, domain: str) -> str:
        """
        Récupère conversion_rate via DOM scraping avec FID (SEULE MÉTRIQUE DOM).
        """
        try:
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - DÉBUT scrape_purchase_conversion pour {domain}")
            
            # 1. Récupérer le FID pour ce domaine
            fid = await self.get_folder_id_for_domain(domain)
            
            if not fid:
                logger.warning(f"⚠️ Worker {self.worker_id}: Impossible de récupérer le FID pour {domain}")
                return ""
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - FID récupéré: {fid}")
            
            # 2. Navigation vers Traffic Analytics avec FID
            target_url = f"https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/?fid={fid}"
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Navigation vers: {target_url}")
            
            success = await self.navigate_with_smart_timeout(target_url, "Traffic Analytics Conversion")
            if not success:
                logger.warning(f"⚠️ Worker {self.worker_id}: DEBUG - Échec navigation vers Traffic Analytics")
                return ""
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Navigation réussie")
            
            # 3. Attendre que les métriques se chargent (React SPA)
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Attente chargement des métriques React SPA...")
            await asyncio.sleep(3)
            
            # Attendre que la page soit complètement chargée
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Attente chargement complet de la page...")
            
            # Attendre que la page soit 'complete' (pas seulement 'interactive')
            try:
                await self.page.wait_for_load_state('complete', timeout=15000)
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Page complètement chargée (complete)")
            except:
                logger.warning(f"⚠️ Worker {self.worker_id}: DEBUG - Timeout chargement complet")
            
            # Attendre que les éléments data-testid apparaissent
            try:
                await self.page.wait_for_selector('[data-testid]', timeout=10000)
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments data-testid chargés")
            except:
                logger.warning(f"⚠️ Worker {self.worker_id}: DEBUG - Timeout data-testid")
            
            # Attendre que les éléments de table se chargent de manière asynchrone
            max_attempts = 15  # Augmenté de 10 à 15
            for attempt in range(max_attempts):
                try:
                    # Vérifier si les éléments de table sont présents
                    table_elements = await self.page.evaluate("""
                        () => ({
                            rows: document.querySelectorAll('[role="row"], tr').length,
                            cells: document.querySelectorAll('[role="gridcell"], td, th').length,
                            testIds: document.querySelectorAll('[data-testid]').length,
                            pageReady: document.readyState
                        })
                    """)
                    
                    logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Tentative {attempt + 1}/{max_attempts}: rows={table_elements['rows']}, cells={table_elements['cells']}, testIds={table_elements['testIds']}, ready={table_elements['pageReady']}")
                    
                    # Si on a des éléments de table ET des data-testid, on peut continuer
                    if table_elements['rows'] > 0 and table_elements['cells'] > 0 and table_elements['testIds'] > 100:
                        logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments de table chargés asynchrone (rows: {table_elements['rows']}, cells: {table_elements['cells']})")
                        break
                    
                    # Attendre un peu plus pour le chargement asynchrone
                    await asyncio.sleep(3)  # Augmenté de 2s à 3s
                    
                except Exception as e:
                    logger.warning(f"⚠️ Worker {self.worker_id}: DEBUG - Erreur vérification éléments: {e}")
                    await asyncio.sleep(3)
            
            # Attendre encore un peu pour que les données se remplissent complètement
            await asyncio.sleep(3)  # Augmenté de 2s à 3s
            
            # 4. Scroll vers le haut de la page pour s'assurer qu'on voit le début de la table
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Scroll vers le haut de la page...")
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
            # 5. Debug: Vérifier le contenu de la page
            current_url = self.page.url
            page_title = await self.page.title()
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - URL après navigation: {current_url}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Titre de la page: {page_title}")
            
            # 5. Debug: Vérifier les éléments data-testid="value" présents
            value_elements = await self.page.query_selector_all('[data-testid="value"]')
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - {len(value_elements)} éléments data-testid='value' trouvés")
            
            # 6. Debug: Vérifier les éléments summary-cell présents
            summary_elements = await self.page.query_selector_all('[data-testid*="summary-cell"]')
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - {len(summary_elements)} éléments summary-cell trouvés")
            
            for i, elem in enumerate(summary_elements):
                try:
                    testid = await elem.get_attribute('data-testid')
                    logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Summary-cell {i+1}: {testid}")
                except:
                    pass
            
            # 7. Debug: Vérifier le contenu textuel de la page (pas HTML)
            page_text = await self.page.evaluate("() => document.body.innerText")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Contenu textuel de la page (premiers 500 chars): {page_text[:500]}")
            
            # 7.5. Debug: Vérifier les éléments DOM disponibles
            dom_debug = await self.page.evaluate("""
                () => {
                    const result = {
                        bodyExists: !!document.body,
                        tables: document.querySelectorAll('table').length,
                        divs: document.querySelectorAll('div').length,
                        spans: document.querySelectorAll('span').length,
                        allElements: document.querySelectorAll('*').length,
                        pageReady: document.readyState,
                        hasReact: !!window.React || !!document.querySelector('[data-reactroot]') || !!document.querySelector('#root'),
                        hasContent: document.body.textContent.length > 100
                    };
                    
                    // Chercher des éléments spécifiques
                    result.gridElements = document.querySelectorAll('[role="grid"]').length;
                    result.rowElements = document.querySelectorAll('[role="row"]').length;
                    result.cellElements = document.querySelectorAll('[role="gridcell"]').length;
                    result.testIdElements = document.querySelectorAll('[data-testid]').length;
                    
                    return result;
                }
            """)
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments DOM: {dom_debug}")
            
            # 7.6. Debug: Attendre plus longtemps si nécessaire
            if dom_debug.get('allElements', 0) < 10:
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Page semble vide, attente supplémentaire...")
                await asyncio.sleep(5)
                
                # Re-vérifier après attente
                dom_debug_2 = await self.page.evaluate("() => ({ allElements: document.querySelectorAll('*').length, hasContent: document.body.textContent.length > 100 })")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Après attente supplémentaire: {dom_debug_2}")
            
            # 8. Scraping Purchase Conversion via JavaScript (approche data-testid)
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Tentative scraping via JavaScript (approche table + data-testid)...")
            
            conversion_data = await self.page.evaluate(f"""
                () => {{
                    const result = {{
                        purchaseConversion: null,
                        found: false,
                        allData: [],
                        testIdElements: 0,
                        domainElements: 0,
                        tableElements: 0,
                        attempts: 0
                    }};

                    // Attendre que les éléments se chargent (simulation d'attente asynchrone)
                    const waitForElements = () => {{
                        const rowElements = document.querySelectorAll('[role="row"], tr');
                        const cellElements = document.querySelectorAll('[role="gridcell"], td, th');
                        const testIdElements = document.querySelectorAll('[data-testid]');
                        
                        return {{
                            rows: rowElements.length,
                            cells: cellElements.length,
                            testIds: testIdElements.length
                        }};
                    }};

                    // Vérifier plusieurs fois si les éléments sont chargés
                    let elements = waitForElements();
                    result.attempts = 0;
                    
                    while (result.attempts < 5 && (elements.rows === 0 || elements.cells === 0 || elements.testIds < 100)) {{
                        result.attempts++;
                        console.log(`🔍 Tentative ${{result.attempts}}/5: rows=${{elements.rows}}, cells=${{elements.cells}}, testIds=${{elements.testIds}}`);
                        
                        // Attendre un peu (simulation)
                        const start = new Date().toISOString();
                        while (new Date().toISOString() - start < 100) {{ /* attente 100ms */ }}
                        
                        elements = waitForElements();
                    }}

                    // 1. Maintenant chercher dans les éléments de table/grille
                    const rowElements = document.querySelectorAll('[role="row"], tr');
                    const cellElements = document.querySelectorAll('[role="gridcell"], td, th');
                    result.tableElements = rowElements.length + cellElements.length;

                    console.log('🔍 Éléments de table trouvés:', result.tableElements, 'rows:', rowElements.length, 'cells:', cellElements.length);

                    // 2. Chercher dans les cellules de table (priorité aux premières lignes)
                    console.log('🔍 Recherche du domaine dans les cellules de table...');
                    
                    // D'abord chercher dans les premières lignes (plus probable d'avoir le bon domaine)
                    const firstRows = Array.from(rowElements).slice(0, 5); // Premières 5 lignes
                    
                    for (const row of firstRows) {{
                        const rowText = row.textContent || '';
                        console.log('🔍 Ligne:', rowText.substring(0, 100));
                        
                        // Recherche plus flexible du domaine
                        const domainVariations = [
                            '{domain.lower()}',
                            '{domain.lower()}'.replace('.com', ''),
                            '{domain.lower()}'.replace('www.', ''),
                            '{domain.lower()}'.replace('https://', '').replace('http://', '')
                        ];
                        
                        let domainFound = false;
                        for (const variation of domainVariations) {{
                            if (rowText.toLowerCase().includes(variation)) {{
                                domainFound = true;
                                break;
                            }}
                        }}
                        
                        if (domainFound) {{
                            result.found = true;
                            result.domainElements++;
                            console.log('🎯 Ligne domaine trouvée:', rowText.substring(0, 100));

                            // Extraire toutes les cellules de cette ligne
                            const cells = row.querySelectorAll('[role="gridcell"], td, th');
                            console.log('📊 Cellules dans la ligne:', cells.length);
                            
                            for (const cell of cells) {{
                                const cellText = cell.textContent || '';
                                console.log('🔍 Cellule:', cellText);
                                
                                // Parser le texte pour trouver la conversion
                                const words = cellText.split(/\\s+/);
                                for (const word of words) {{
                                    // Pourcentages de conversion (petits %)
                                    if (word.match(/^\\d+\\.\\d+%/) && word.includes('.')) {{
                                        const rate = parseFloat(word.replace('%', '').replace(/[↑↓]/, ''));
                                        if (rate < 10 && !result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée dans cellule:', word);
                                        }}
                                    }}
                                    
                                    // Gérer les valeurs comme "< 0.01%" (chercher dans le texte complet de la cellule)
                                    if (cellText.includes('<') && cellText.includes('%')) {{
                                        // Extraire la partie avec < et %
                                        const match = cellText.match(/<[^>]*\\d+[^%]*%/);
                                        if (match && !result.purchaseConversion) {{
                                            result.purchaseConversion = match[0];
                                            console.log('✅ Conversion trouvée (format <):', match[0]);
                                        }}
                                    }}

                                    // Chercher aussi "purchase" ou "conversion" dans le texte
                                    if ((word.toLowerCase().includes('purchase') || word.toLowerCase().includes('conversion')) && word.includes('%')) {{
                                        if (!result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée par mot-clé dans cellule:', word);
                                        }}
                                    }}
                                }}
                            }}
                            
                            // Si on a trouvé le domaine, on peut s'arrêter
                            if (result.purchaseConversion) break;
                        }}
                    }}
                    
                    // 2b. Si pas trouvé par domaine, chercher dans TOUTES les cellules pour des pourcentages
                    if (!result.purchaseConversion) {{
                        console.log('🔍 Recherche dans toutes les cellules pour des pourcentages...');
                        for (const cell of cellElements) {{
                            const cellText = cell.textContent || '';
                            const words = cellText.split(/\\s+/);
                            
                            for (const word of words) {{
                                // Pourcentages de conversion (petits %)
                                if (word.match(/^\\d+\\.\\d+%/) && word.includes('.')) {{
                                    const rate = parseFloat(word.replace('%', '').replace(/[↑↓]/, ''));
                                    if (rate < 10 && !result.purchaseConversion) {{
                                        result.purchaseConversion = word;
                                        console.log('✅ Conversion trouvée dans cellule (sans domaine):', word, cellText.substring(0, 50));
                                    }}
                                }}
                            }}
                        }}
                    }}

                    // 3. Si pas trouvé, chercher dans les éléments data-testid
                    if (!result.purchaseConversion) {{
                        const testIdElements = document.querySelectorAll('[data-testid]');
                        result.testIdElements = testIdElements.length;
                        console.log('🔍 Éléments data-testid trouvés:', result.testIdElements);

                        for (const element of testIdElements) {{
                            const elementText = element.textContent || '';
                            const testId = element.getAttribute('data-testid') || '';

                            // Chercher le domaine dans le texte ou le testid
                            if (elementText.toLowerCase().includes('{domain.lower()}') || testId.toLowerCase().includes('{domain.lower()}')) {{
                                result.found = true;
                                result.domainElements++;
                                console.log('🎯 Élément data-testid domaine trouvé:', testId, elementText.substring(0, 100));

                                // Parser le texte pour trouver la conversion
                                const words = elementText.split(/\\s+/);
                                for (const word of words) {{
                                    // Pourcentages de conversion (petits %)
                                    if (word.match(/^\\d+\\.\\d+%/) && word.includes('.')) {{
                                        const rate = parseFloat(word.replace('%', '').replace(/[↑↓]/, ''));
                                        if (rate < 10 && !result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée dans data-testid:', word);
                                        }}
                                    }}

                                    // Chercher aussi "purchase" ou "conversion" dans le texte
                                    if ((word.toLowerCase().includes('purchase') || word.toLowerCase().includes('conversion')) && word.includes('%')) {{
                                        if (!result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée par mot-clé dans data-testid:', word);
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}

                    // 4. Si toujours pas trouvé, chercher dans tous les éléments
                    if (!result.purchaseConversion) {{
                        console.log('🔍 Recherche dans tous les éléments contenant le domaine...');
                        const allElements = document.querySelectorAll('*');

                        for (const element of allElements) {{
                            const elementText = element.textContent || '';

                            if (elementText.toLowerCase().includes('{domain.lower()}')) {{
                                result.found = true;
                                result.domainElements++;

                                // Parser le texte pour trouver la conversion
                                const words = elementText.split(/\\s+/);
                                for (const word of words) {{
                                    // Pourcentages de conversion (petits %)
                                    if (word.match(/^\\d+\\.\\d+%/) && word.includes('.')) {{
                                        const rate = parseFloat(word.replace('%', '').replace(/[↑↓]/, ''));
                                        if (rate < 10 && !result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée dans élément:', word);
                                        }}
                                    }}

                                    // Chercher aussi "purchase" ou "conversion" dans le texte
                                    if ((word.toLowerCase().includes('purchase') || word.toLowerCase().includes('conversion')) && word.includes('%')) {{
                                        if (!result.purchaseConversion) {{
                                            result.purchaseConversion = word;
                                            console.log('✅ Conversion trouvée par mot-clé dans élément:', word);
                                        }}
                                    }}
                                }}

                                if (result.purchaseConversion) break;
                            }}
                        }}
                    }}

                    // 5. Debug: Afficher tous les sélecteurs possibles
                    result.allSelectors = {{
                        tables: document.querySelectorAll('table').length,
                        divs: document.querySelectorAll('div').length,
                        spans: document.querySelectorAll('span').length,
                        allElements: document.querySelectorAll('*').length,
                        gridElements: document.querySelectorAll('[role="grid"]').length,
                        rowElements: document.querySelectorAll('[role="row"], tr').length,
                        cellElements: document.querySelectorAll('[role="gridcell"], td, th').length,
                        testIdElements: document.querySelectorAll('[data-testid]').length,
                        reactRoot: !!document.querySelector('[data-reactroot]'),
                        root: !!document.querySelector('#root')
                    }};

                    console.log('🔍 Tous les sélecteurs:', result.allSelectors);
                    console.log('🔍 Éléments domaine trouvés:', result.domainElements);
                    console.log('🔍 Éléments de table trouvés:', result.tableElements);

                    return result;
                }}
            """)
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Résultat JavaScript: {conversion_data}")
            
            if conversion_data.get('purchaseConversion'):
                conversion_rate_raw = conversion_data['purchaseConversion']
                logger.info(f"✅ Worker {self.worker_id}: DEBUG - Conversion Rate trouvé via table: {conversion_rate_raw}")
                
                # Extraire seulement la valeur numérique et diviser par 100
                try:
                    # Extraire le nombre (ex: "0.01" de "0.01%↓" ou "< 0.01%")
                    import re
                    number_match = re.search(r'(\d+\.?\d*)', conversion_rate_raw)
                    if number_match:
                        numeric_value = float(number_match.group(1))
                        # Diviser par 100 pour avoir la valeur décimale
                        conversion_rate = str(numeric_value / 100)
                        logger.info(f"✅ Worker {self.worker_id}: Conversion Rate converti: {conversion_rate_raw} → {conversion_rate}")
                        return conversion_rate
                    else:
                        logger.warning(f"⚠️ Worker {self.worker_id}: Impossible d'extraire le nombre de: {conversion_rate_raw}")
                        return ""
                except Exception as e:
                    logger.error(f"❌ Worker {self.worker_id}: Erreur conversion: {e}")
                    return ""
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: DEBUG - Purchase Conversion non trouvé")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Tentatives d'attente: {conversion_data.get('attempts', 0)}")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments de table: {conversion_data.get('tableElements', 0)}")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments data-testid: {conversion_data.get('testIdElements', 0)}")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments domaine: {conversion_data.get('domainElements', 0)}")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Données trouvées: {conversion_data.get('allData', [])}")
                return ""
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur DOM scraping conversion_rate: {e}")
            return ""
    
    async def scrape_conversion_rate_via_api(self, domain: str) -> str:
        """
        Récupère conversion_rate via l'API organic.OverviewTrend.
        NOUVELLE MÉTHODE utilisant APIClient.
        """
        try:
            
            # Nettoyer le domaine (MÊME LOGIQUE que les autres APIs)
            domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            
            # Calculer la date cible (MÊME LOGIQUE que les autres APIs)
            target_date = self.calculate_target_date()
            logger.info(f"📅 Worker {self.worker_id}: Date calculée: {target_date}")
            
            # Utiliser APIClient pour organic.OverviewTrend
            params = self.api_client.get_conversion_params(domain_clean, target_date)
            result = await self.api_client.call_rpc_api(self.page, "organic.OverviewTrend", params, self.worker_id)
            
            if not result or result.get("error"):
                logger.warning(f"⚠️ Worker {self.worker_id}: API organic.OverviewTrend (conversion) échouée pour {domain}")
                return ""
            
            # Parser la réponse (structure à déterminer selon l'API)
            if result.get("result") and len(result["result"]) > 0:
                # Structure à adapter selon la réponse réelle de l'API
                conversion_data = result["result"][0]  # Premier élément
                conversion_rate = conversion_data.get("conversion_rate", "")
                
                logger.info(f"✅ Worker {self.worker_id}: Conversion Rate (API NOUVELLE): {conversion_rate}")
                return str(conversion_rate) if conversion_rate else ""
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Aucune donnée conversion_rate trouvée dans l'API organic.OverviewTrend")
                return ""
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur API organic.OverviewTrend (conversion): {e}")
            return ""
    
    async def scrape_traffic_analysis(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):
        """Scraping de la page Traffic Analysis - VÉRIFIE AVANT DE SCRAPER"""
        logger.info(f"📊 Worker {self.worker_id}: Traffic Analysis pour {domain}")
        
        try:
            url = f"https://app.mytoolsplan.com/analytics/traffic/traffic-overview/?db=us&q={domain}&searchType=domain&date={date_range}"
            
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
            analytics_data['traffic'] = domain_data.get('traffic', '')
            analytics_data['branded_traffic'] = domain_data.get('branded_traffic', '')
            analytics_data['conversion_rate'] = domain_data.get('conversion_rate', '')
        
        # Calculer percent_branded_traffic selon la formule de la doc
        analytics_data['percent_branded_traffic'] = self.calculate_percent_branded_traffic(analytics_data)
        
        return analytics_data
    
    def calculate_percent_branded_traffic(self, analytics_data: Dict[str, str]) -> str:
        """Calcule le pourcentage de trafic de marque selon la formule de la doc"""
        try:
            traffic = analytics_data.get('traffic', '')
            branded_traffic = analytics_data.get('branded_traffic', '')

            if traffic and branded_traffic and traffic != "" and branded_traffic != "":
                traffic_num = self.convert_traffic_to_number(traffic)
                branded_num = self.convert_traffic_to_number(branded_traffic)

                if traffic_num > 0:
                    percent_branded = (branded_num / traffic_num) * 100
                    logger.info(f"📊 Worker {self.worker_id}: Calcul percent_branded_traffic: ({branded_num} / {traffic_num}) * 100 = {percent_branded:.2f}%")
                    return f"{percent_branded:.2f}%"
                else:
                    return "N/A"
            else:
                return "Données manquantes"
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur calcul Percent Branded Traffic: {e}")
            return "Erreur de calcul"
    
    def convert_traffic_to_number(self, traffic_str: str) -> float:
        """Convertit une valeur de traffic en nombre"""
        if not traffic_str or traffic_str == "N/A" or "non trouvé" in traffic_str.lower():
            return 0.0

        try:
            # Nettoyer la chaîne
            traffic_str = traffic_str.strip()

            if 'M' in traffic_str:
                return float(traffic_str.replace('M', '')) * 1000000
            elif 'K' in traffic_str:
                return float(traffic_str.replace('K', '')) * 1000
            else:
                return float(traffic_str)
        except (ValueError, TypeError):
            return 0.0
    
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
            
            # Synchronisation des cookies déjà faite dans authenticate_mytoolsplan()
            logger.info(f"✅ Worker {self.worker_id}: Synchronisation des cookies déjà effectuée")
            
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
                        api.update_shop_analytics(shop_id, analytics_data)
                        logger.info(f"💾 Worker {self.worker_id}: {domain} enregistré en BDD avec statut 'na'")
                    elif result:
                        # Toutes les métriques sont récupérées via les APIs dans scrape_domain_overview
                        successful_shops += 1
                        logger.info(f"✅ Worker {self.worker_id}: {domain} traité avec succès")
                        
                        # Enregistrer en BDD
                        analytics_data = self.format_analytics_for_api()
                        status = 'completed' if self.session_data['data'].get('domain_overview') else 'partial'
                        api.update_shop_analytics(shop_id, analytics_data)
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
