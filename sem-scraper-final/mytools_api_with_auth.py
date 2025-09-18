#!/usr/bin/env python3
"""
API MyTools avec authentification complète
Reproduit exactement le processus du scraper de production
"""

import asyncio
import json
import uuid
import time
import os
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MyToolsAPIWithAuth:
    def __init__(self):
        # Credentials depuis les variables d'environnement (comme le scraper de production)
        self.username = os.getenv('MYTOOLSPLAN_USERNAME')
        self.password = os.getenv('MYTOOLSPLAN_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("❌ MYTOOLSPLAN_USERNAME et MYTOOLSPLAN_PASSWORD doivent être définis dans les variables d'environnement")
        
        self.page = None
        self.browser = None
        self.context = None
        self.base_url = "https://sam.mytoolsplan.xyz"
        self.login_url = "https://app.mytoolsplan.com/login"
        self.is_authenticated = False
        
    async def init_browser(self):
        """🚀 Initialise le navigateur (exactement comme le scraper de production)"""
        if self.browser:
            return
            
        logger.info("🚀 Initialisation du navigateur...")
        
        # Configuration Xvfb comme le scraper de production
        import platform
        import subprocess
        
        system = platform.system().lower()
        if system == 'linux':
            display = os.environ.get('DISPLAY')
            if not display or display == '':
                logger.info("🖥️ Linux détecté - Configuration Xvfb...")
                try:
                    result = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.info("🖥️ Démarrage de Xvfb...")
                        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
                        os.environ['DISPLAY'] = ':99'
                    else:
                        logger.info("🖥️ Xvfb déjà en cours")
                        os.environ['DISPLAY'] = ':99'
                except FileNotFoundError:
                    logger.warning("⚠️ Xvfb non trouvé, utilisation du display par défaut")
        
        playwright = await async_playwright().start()
        
        # Utiliser launch_persistent_context comme le scraper de production
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir='./session-profile-api',
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-brotli',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--disable-extensions'
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        
        # Intercepter et bloquer localStorage.clear() (comme le scraper de production)
        await self.page.add_init_script("""
            const originalClear = Storage.prototype.clear;
            const originalSetItem = Storage.prototype.setItem;
            
            // Whitelist des clés importantes à préserver
            const protectedKeys = [
                'auth_token', 'session_id', 'user_data', 
                'csrf_token', 'api_key', 'login_state',
                'mytoolsplan_session', 'amember_session',
                'authentication_token', 'user_session'
            ];
            
            // Sauvegarde du contenu critique
            let criticalData = {};
            
            // Override clear() - empêche la suppression complète
            Storage.prototype.clear = function() {
                console.log('🚨 localStorage.clear() intercepté et bloqué');
                
                // Sauvegarde les données critiques
                protectedKeys.forEach(key => {
                    if (this.getItem(key)) {
                        criticalData[key] = this.getItem(key);
                    }
                });
                
                // Vide le localStorage
                originalClear.call(this);
                
                // Restaure les données critiques
                Object.keys(criticalData).forEach(key => {
                    this.setItem(key, criticalData[key]);
                });
            };
        """)
    
    async def authenticate(self):
        """🔐 Authentification MyToolsPlan (exactement comme le scraper de production)"""
        if self.is_authenticated:
            return True
            
        logger.info("🔐 Authentification MyToolsPlan...")
        
        try:
            # Navigation vers la page de login avec timeout réduit
            logger.info(f"🌐 Navigation vers: {self.login_url}")
            await self.page.goto(self.login_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)  # Attendre un peu moins
            
            # Remplir les champs de login
            logger.info("📝 Remplissage des champs de login...")
            await self.page.fill('input[name="amember_login"]', self.username)
            await self.page.fill('input[name="amember_pass"]', self.password)
            
            # Soumettre le formulaire
            logger.info("🚀 Soumission du formulaire...")
            try:
                await self.page.click('input[type="submit"][class="frm-submit"]')
            except:
                await self.page.evaluate('document.querySelector("form[name=\\"login\\"]").submit()')
            
            # Attendre la redirection avec timeout réduit
            await asyncio.sleep(3)
            
            # Vérifier que nous sommes sur la page membre
            current_url = self.page.url
            logger.info(f"✅ Login réussi, URL actuelle: {current_url}")
            
            if "member" not in current_url.lower():
                logger.error("❌ Login échoué - Pas sur la page membre")
                return False
            
            # Maintenant naviguer vers sam.mytoolsplan.xyz pour les requêtes API
            logger.info(f"🌐 Navigation vers API: {self.base_url}")
            await self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(1)
            
            self.is_authenticated = True
            logger.info("✅ Authentification complète réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'authentification: {e}")
            return False
    
    def calculate_date_range(self, months_back=1):
        """📅 Calcule la plage de dates pour les paramètres API"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months_back * 30)
        
        return {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dateRange': f"{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}"
        }
    
    async def get_organic_traffic(self, domain):
        """📊 Récupère le traffic organique via API"""
        logger.info(f"📊 Récupération traffic organique pour: {domain}")
        
        await self.init_browser()
        if not await self.authenticate():
            return None
        
        # Calculer les dates
        date_params = self.calculate_date_range(1)
        
        # Paramètres de base
        params = {
            "dateType": "daily",
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "global": True,
            **date_params
        }
        
        logger.info(f"🎯 Paramètres API: {params}")
        
        try:
            # Requête API OverviewTrend
            result = await self.page.evaluate("""
                async (data) => {
                    try {
                        console.log('🚀 Envoi requête OverviewTrend...');
                        const response = await fetch('/dpa/rpc', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'include',
                            body: JSON.stringify({
                                id: new Date().toISOString(),
                                jsonrpc: "2.0",
                                method: "organic.OverviewTrend",
                                params: {
                                    request_id: crypto.randomUUID(),
                                    args: data.params,
                                    userId: data.credentials.userId,
                                    apiKey: data.credentials.apiKey
                                }
                            })
                        });
                        
                        console.log('📊 Status:', response.status);
                        
                        if (!response.ok) {
                            const text = await response.text();
                            console.log('❌ Erreur HTTP:', text);
                            return { error: `HTTP ${response.status}: ${text}` };
                        }
                        
                        const result = await response.json();
                        console.log('📊 Réponse OverviewTrend:', result);
                        return result;
                    } catch (error) {
                        console.log('❌ Erreur fetch:', error);
                        return { error: error.toString() };
                    }
                }
            """, {
                'params': params,
                'credentials': {
                    'userId': 26931056,
                    'apiKey': '943cfac719badc2ca14126e08b8fe44f'
                }
            })
            
            logger.info(f"📊 Réponse brute: {json.dumps(result, indent=2)}")
            
            if result.get('error'):
                logger.error(f"❌ Erreur API: {result['error']}")
                return None
            
            # Parser les résultats
            if result.get('result'):
                latest = result['result'][-1] if result['result'] else {}
                parsed_data = {
                    'domain': domain,
                    'organic_traffic': latest.get('organicTraffic', 0),
                    'paid_traffic': latest.get('adwordsTraffic', 0),
                    'organic_positions': latest.get('organicPositions', 0),
                    'paid_positions': latest.get('adwordsPositions', 0),
                    'date': latest.get('date', ''),
                    'total_data_points': len(result['result'])
                }
                logger.info(f"✅ Données parsées: {json.dumps(parsed_data, indent=2)}")
                return parsed_data
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Erreur get_organic_traffic: {e}')
            return None
    
    async def get_summary_metrics(self, domain):
        """📈 Récupère les métriques de résumé via API"""
        logger.info(f"📈 Récupération métriques résumé pour: {domain}")
        
        await self.init_browser()
        if not await self.authenticate():
            return None
        
        # Calculer les dates
        date_params = self.calculate_date_range(1)
        
        # Paramètres de base
        params = {
            "dateType": "daily",
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "global": True,
            **date_params
        }
        
        try:
            # Requête API Summary
            result = await self.page.evaluate("""
                async (data) => {
                    try {
                        console.log('🚀 Envoi requête Summary...');
                        const response = await fetch('/dpa/rpc', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'include',
                            body: JSON.stringify({
                                id: new Date().toISOString(),
                                jsonrpc: "2.0",
                                method: "organic.Summary",
                                params: {
                                    request_id: crypto.randomUUID(),
                                    args: data.params,
                                    userId: data.credentials.userId,
                                    apiKey: data.credentials.apiKey
                                }
                            })
                        });
                        
                        console.log('📈 Status:', response.status);
                        
                        if (!response.ok) {
                            const text = await response.text();
                            console.log('❌ Erreur HTTP:', text);
                            return { error: `HTTP ${response.status}: ${text}` };
                        }
                        
                        const result = await response.json();
                        console.log('📈 Réponse Summary:', result);
                        return result;
                    } catch (error) {
                        console.log('❌ Erreur fetch:', error);
                        return { error: error.toString() };
                    }
                }
            """, {
                'params': params,
                'credentials': {
                    'userId': 26931056,
                    'apiKey': '943cfac719badc2ca14126e08b8fe44f'
                }
            })
            
            logger.info(f"📈 Réponse Summary brute: {json.dumps(result, indent=2)}")
            
            if result.get('error'):
                logger.error(f"❌ Erreur Summary API: {result['error']}")
                return None
            
            return result.get('result', {})
            
        except Exception as e:
            logger.error(f'❌ Erreur get_summary_metrics: {e}')
            return None
    
    async def close(self):
        """🔒 Ferme le navigateur"""
        if self.context:
            await self.context.close()
            logger.info("🔒 Navigateur fermé")

# Instance globale
_global_api_instance = None

async def get_api_instance():
    """Récupère l'instance globale (réutilisable)"""
    global _global_api_instance
    if _global_api_instance is None:
        _global_api_instance = MyToolsAPIWithAuth()
    return _global_api_instance

async def get_organic_traffic(domain):
    """Fonction simple pour récupérer le traffic organique"""
    api = await get_api_instance()
    return await api.get_organic_traffic(domain)

async def get_summary_metrics(domain):
    """Fonction simple pour récupérer les métriques de résumé"""
    api = await get_api_instance()
    return await api.get_summary_metrics(domain)

# Test principal
async def test_api_with_auth():
    """🧪 Test principal de l'API avec authentification"""
    print("🧪 TEST API MYTOOLS AVEC AUTHENTIFICATION")
    print("=" * 50)
    
    api = MyToolsAPIWithAuth()
    
    try:
        # Test avec un domaine simple
        test_domain = "apple.com"
        
        print(f"\n📊 Test 1: Traffic organique pour {test_domain}")
        traffic_result = await api.get_organic_traffic(test_domain)
        
        if traffic_result:
            print("✅ Test traffic organique réussi!")
            print(f"   Données: {json.dumps(traffic_result, indent=2)}")
        else:
            print("❌ Test traffic organique échoué!")
        
        print(f"\n📈 Test 2: Métriques résumé pour {test_domain}")
        summary_result = await api.get_summary_metrics(test_domain)
        
        if summary_result:
            print("✅ Test métriques résumé réussi!")
            print(f"   Données: {json.dumps(summary_result, indent=2)}")
        else:
            print("❌ Test métriques résumé échoué!")
        
        # Test avec un autre domaine
        test_domain2 = "nike.com"
        print(f"\n📊 Test 3: Traffic organique pour {test_domain2}")
        traffic_result2 = await api.get_organic_traffic(test_domain2)
        
        if traffic_result2:
            print("✅ Test traffic organique 2 réussi!")
            print(f"   Données: {json.dumps(traffic_result2, indent=2)}")
        else:
            print("❌ Test traffic organique 2 échoué!")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    
    finally:
        if api.context:
            await api.close()
        print("\n🎉 Tests terminés!")

if __name__ == "__main__":
    asyncio.run(test_api_with_auth())
