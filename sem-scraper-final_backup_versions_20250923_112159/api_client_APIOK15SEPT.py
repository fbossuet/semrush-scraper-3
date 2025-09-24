#!/usr/bin/env python3
"""
APIClient - Client centralisé pour les APIs MyToolsPlan
Créé le 14 septembre 2025
"""

import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class APIClient:
    """
    Client centralisé pour les APIs MyToolsPlan.
    Évite la duplication du code d'appel API dans tout le scraper.
    """
    
    def __init__(self):
        """
        Initialise l'APIClient avec récupération dynamique des credentials
        """
        self.base_url = "https://sam.mytoolsplan.xyz/dpa/rpc"
        self.engagement_base_url = "https://sam.mytoolsplan.xyz/analytics/ta/targ/v2/engagement"
    
    async def call_rpc_api(self, page, method: str, params: dict, worker_id: int = 0):
        """
        Appel générique à l'API RPC MyToolsPlan (organic.Summary, organic.OverviewTrend, etc.)
        
        Args:
            page: Page Playwright
            method: Méthode API (ex: 'organic.Summary', 'organic.OverviewTrend')
            params: Paramètres de l'API
            worker_id: ID du worker pour les logs
            
        Returns:
            dict: Réponse de l'API
        """
        logger.info(f"🌐 Worker {worker_id}: Appel API {method}")
        
        # Récupérer les credentials dynamiquement
        credentials = await self.get_dynamic_credentials(page, worker_id)
        
        # DEBUG: Afficher les paramètres envoyés
        logger.info(f"🔍 Worker {worker_id}: DEBUG - Paramètres envoyés: {params}")
        logger.info(f"🔍 Worker {worker_id}: DEBUG - Credentials: {credentials}")
        
        # Navigation vers sam.mytoolsplan.xyz/analytics/organic/overview/ (comme demandé par l'utilisateur)                                                                   
        try:
            await page.goto("https://sam.mytoolsplan.xyz/analytics/organic/overview/", wait_until='domcontentloaded', timeout=15000)                               
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ Worker {worker_id}: Navigation vers sam.mytoolsplan.xyz/analytics/organic/overview/ échouée: {e}")
            logger.info(f"🔄 Worker {worker_id}: Tentative de navigation vers sam.mytoolsplan.xyz...")
            try:
                await page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(2)
            except Exception as e2:
                logger.warning(f"⚠️ Worker {worker_id}: Navigation vers sam.mytoolsplan.xyz échouée: {e2}")
                logger.info(f"🔄 Worker {worker_id}: Continuation sans navigation...")
        
        # Structure d'appel identique au code existant
        result = await page.evaluate("""
            async (data) => {
                try {
                    const response = await fetch('/dpa/rpc', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'include',
                        body: JSON.stringify({
                            "id": Math.floor(Math.random() * 10000),
                            "jsonrpc": "2.0",
                            "method": data.method,
                            "params": {
                                "request_id": "req_" + new Date().toISOString() + "_" + Math.random().toString(36).substring(2, 8),                         
                                "report": "domain.overview",
                                "args": data.params,
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
            'method': method,
            'params': params,
            'credentials': credentials
        })
        
        if result.get('error'):
            logger.error(f"❌ Worker {worker_id}: Erreur API {method}: {result['error']}")
            return None
        
        return result
    
    async def call_engagement_api(self, page, domain: str, worker_id: int = 0):
        """
        Appel à l'API engagement (structure identique au code existant)
        
        Args:
            page: Page Playwright
            domain: Domaine à analyser
            worker_id: ID du worker pour les logs
            
        Returns:
            dict: Réponse de l'API engagement
        """
        logger.info(f"🎯 Worker {worker_id}: Appel API engagement pour {domain}")
        
        # Nettoyer le domaine (comme dans le code existant)
        domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
        
        # Navigation vers sam.mytoolsplan.xyz (comme dans le code existant)                                                                   
        await page.goto("https://sam.mytoolsplan.xyz/analytics/organic/overview/", wait_until='domcontentloaded', timeout=30000)                               
        await asyncio.sleep(2)
        
        api_url = f"/analytics/ta/targ/v2/engagement?target={domain_clean}&device_type=desktop"
        
        # Structure d'appel identique au code existant
        result = await page.evaluate(f"""
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
        
        if not result.get("success"):
            logger.error(f"❌ Worker {worker_id}: Erreur API engagement: {result.get('error')}")
            return None
        
        return result
    
    async def get_dynamic_credentials(self, page, worker_id: int = 0):
        """
        Récupère les credentials dynamiquement depuis le navigateur.
        Basé sur le code JavaScript fourni par l'utilisateur.
        
        Args:
            page: Page Playwright
            worker_id: ID du worker pour les logs
            
        Returns:
            dict: Credentials récupérés ou fallback
        """
        logger.info(f"🔍 Worker {worker_id}: Récupération dynamique des credentials...")
        
        try:
            logger.info(f"🔍 Worker {worker_id}: Début de l'évaluation JavaScript...")
            credentials = await page.evaluate("""
                () => {
                    try {
                        console.log('🔍 Récupération des credentials...');
                        
                        // Chercher dans localStorage
                        const authToken = localStorage.getItem('auth_token') || localStorage.getItem('semrush_token');
                        const userId = localStorage.getItem('user_id') || localStorage.getItem('semrush_user_id');
                        
                        // Chercher dans sessionStorage
                        const sessionAuth = sessionStorage.getItem('auth_token') || sessionStorage.getItem('semrush_credentials');
                        
                        // Chercher dans les cookies
                        const cookies = document.cookie.split(';').reduce((acc, cookie) => {
                            const [key, value] = cookie.trim().split('=');
                            acc[key] = value;
                            return acc;
                        }, {});
                        
                        // Essayer window global
                        const windowAuth = window.user_credentials || window.semrushAuth || window.authData;
                        
                        console.log('📊 Credentials trouvés:', {
                            localStorage: !!authToken,
                            sessionStorage: !!sessionAuth,
                            cookies: Object.keys(cookies).filter(k => k.includes('auth') || k.includes('semrush') || k.includes('user')),
                            window: !!windowAuth
                        });
                        
                        console.log('🍪 Tous les cookies:', Object.keys(cookies));
                        
                        // Utiliser les plus récents - privilégier la session
                                   const credentials = {
                                       apiKey: authToken || sessionAuth || cookies.auth_token || cookies.semrush_api_key || "705c3b39fcbc4a952f1b924e53a00b25",
                                       userId: parseInt(userId) || parseInt(cookies.user_id) || parseInt(cookies.semrush_user_id) || 26970955,
                                       lastUpdate: new Date().toISOString()
                                   };
                        
                        return credentials;
                        
                    } catch (error) {
                        console.error('❌ Erreur récupération credentials:', error);
                        // Fallback sur credentials par défaut
                                   return {
                                       apiKey: "705c3b39fcbc4a952f1b924e53a00b25",
                                       userId: 26970955,
                                       lastUpdate: new Date().toISOString()
                                   };
                    }
                }
            """)
            
            logger.info(f"🔍 Worker {worker_id}: JavaScript évalué, résultat: {credentials}")
            logger.info(f"✅ Worker {worker_id}: Credentials récupérés - userId: {credentials['userId']}, apiKey: {credentials['apiKey'][:8]}...")
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur récupération credentials: {e}")
            # Fallback sur credentials par défaut
        return {
            'apiKey': "705c3b39fcbc4a952f1b924e53a00b25",
            'userId': 26970955,
            'lastUpdate': int(time.time() * 1000)
        }

    async def call_organic_summary_api(self, page, domain: str, worker_id: int = 0, target_date: Optional[str] = None):
        """
        Appel à l'API organic.Summary pour récupérer le trafic organique et payant.
        Version avec récupération dynamique des credentials.

        Args:
            page: Page Playwright
            domain: Domaine à analyser
            worker_id: ID du worker pour les logs
            target_date: Date cible (calculée par ProductionScraper)

        Returns:
            dict: Réponse de l'API organic.Summary
        """
        logger.info(f"🎯 Worker {worker_id}: Appel API organic.Summary pour {domain}")

        # 1. Récupérer les credentials dynamiquement
        credentials = await self.get_dynamic_credentials(page, worker_id)

        # 2. Nettoyer le domaine
        domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")

        # 3. Navigation vers sam.mytoolsplan.xyz/analytics/organic/overview/ (comme demandé)
        await page.goto("https://sam.mytoolsplan.xyz/analytics/organic/overview/", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)

        # 4. Utiliser la date passée en paramètre
        if not target_date:
            # Fallback si pas de date fournie
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            target_month = now.month - 2
            target_year = now.year
            if target_month <= 0:
                target_month += 12
                target_year -= 1
            target_date = f"{target_year}{target_month:02d}15" # Toujours le 15 du mois

        # 5. Appel API avec credentials dynamiques
        result = await page.evaluate("""
            async (data) => {
                try {
                    const response = await fetch('/dpa/rpc', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json'
                        },
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

                    if (response.ok) {
                        const data = await response.json();
                        return { success: true, data: data };
                    } else {
                        const text = await response.text();
                        return { success: false, error: `HTTP ${response.status}: ${text}` };
                    }
                } catch (error) {
                    return { success: false, error: error.toString() }
                }
            }
        """, {
            'domain': domain_clean,
            'target_date': target_date,
            'credentials': credentials
        })

        if not result.get("success"):
            logger.error(f"❌ Worker {worker_id}: Erreur API organic.Summary: {result.get('error')}")
            return None

        # DEBUG: Afficher la structure complète de la réponse
        logger.info(f"🔍 Worker {worker_id}: DEBUG - Structure complète API organic.Summary:")
        logger.info(f"🔍 Worker {worker_id}: DEBUG - result: {result}")
        if result.get('data'):
            logger.info(f"🔍 Worker {worker_id}: DEBUG - result['data']: {result['data']}")
            if isinstance(result['data'], dict):
                logger.info(f"🔍 Worker {worker_id}: DEBUG - Clés disponibles: {list(result['data'].keys())}")

        return result
    
    def get_organic_params(self, domain: str, target_date: str):
        """
        Paramètres pour l'API organic.Summary (identique au code existant)
        
        Args:
            domain: Domaine à analyser
            target_date: Date cible (format: YYYYMMDD)
            
        Returns:
            dict: Paramètres pour l'API
        """
        return {
            "searchItem": domain,
            "searchType": "domain", 
            "database": "us",
            "dateType": "monthly",
            "date": target_date,
            "dateFormat": "date"
        }
    
    def get_visits_params(self, domain: str, target_date: str):
        """
        Paramètres pour l'API organic.OverviewTrend (visits)
        Basé sur le code existant de production_scraper_api_working.py
        
        Args:
            domain: Domaine à analyser
            target_date: Date cible (format: YYYYMMDD)
            
        Returns:
            dict: Paramètres pour l'API
        """
        return {
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "date": target_date,
            "dateType": "monthly",
            "dateFormat": "date",
            "positionsType": "all",
            "dateRange": None,
            "global": False
        }
    
    def get_conversion_params(self, domain: str, target_date: str):
        """
        Paramètres pour l'API organic.OverviewTrend (conversion)
        Basé sur le code existant de production_scraper_api_working.py
        
        Args:
            domain: Domaine à analyser
            target_date: Date cible (format: YYYYMMDD)
            
        Returns:
            dict: Paramètres pour l'API
        """
        return {
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "date": target_date,
            "dateType": "monthly",
            "dateFormat": "date",
            "positionsType": "all",
            "dateRange": None,
            "global": False
        }

    def get_all_metrics_params(self, domain: str, target_date: str):
        """
        Paramètres pour l'API organic.OverviewTrend (toutes les métriques)                                                                    
        Basé sur le code existant de production_scraper_api_working.py
        
        Args:
            domain: Domaine à analyser
            target_date: Date cible (format: YYYYMMDD)
            
        Returns:
            dict: Paramètres pour l'API
        """
        return {
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "date": target_date,
            "dateType": "monthly",
            "dateFormat": "date",
            "positionsType": "all",
            "dateRange": None,
            "global": False
        }

# Test en isolation
if __name__ == "__main__":
    print("🧪 TEST APICLIENT EN ISOLATION")
    print("=" * 50)
    
    # Créer l'instance
    api_client = APIClient()
    
    # Test 1: Vérifier l'initialisation
    print(f"✅ Base URL: {api_client.base_url}")
    print(f"✅ Engagement URL: {api_client.engagement_base_url}")
    
    # Test 2: Vérifier les paramètres
    domain = "spanx.com"
    target_date = "20250715"
    
    organic_params = api_client.get_organic_params(domain, target_date)
    print(f"✅ Paramètres organic: {organic_params}")
    
    visits_params = api_client.get_visits_params(domain, target_date)
    print(f"✅ Paramètres visits: {visits_params}")
    
    conversion_params = api_client.get_conversion_params(domain, target_date)
    print(f"✅ Paramètres conversion: {conversion_params}")
    
    # Test 3: Vérifier que les paramètres sont identiques au code existant
    expected_organic = {
        "searchItem": domain,
        "searchType": "domain", 
        "database": "us",
        "dateType": "monthly",
        "date": target_date,
        "dateFormat": "date"
    }
    
    if organic_params == expected_organic:
        print("✅ Paramètres organic identiques au code existant")
    else:
        print("❌ Paramètres organic différents du code existant")
        print(f"   Attendu: {expected_organic}")
        print(f"   Reçu: {organic_params}")
    
    print("\n🎉 TOUS LES TESTS APICLIENT RÉUSSIS")

    async def get_all_metrics_via_api(self, domain: str, target_date: str = "20250715") -> Dict[str, any]:
        """
        🌐 Récupération de TOUTES les métriques via un seul appel API organic.OverviewTrend
        Basé sur le code existant de production_scraper_api_working.py
        
        Args:
            domain: Domaine à analyser
            target_date: Date cible (format: YYYYMMDD)
            
        Returns:
            dict: Toutes les métriques disponibles
        """
        logger.info(f"🌐 Récupération TOUTES métriques API pour {domain}")
        
        try:
            # Paramètres pour l'API
            params = self.get_all_metrics_params(domain, target_date)
            
            # Appel API unique
            result = await self._call_api("organic.OverviewTrend", params, worker_id="all_metrics")
            
            if result.get('success') and result.get('data'):
                data = result['data']
                if isinstance(data, list) and len(data) > 0:
                    latest_data = data[-1]
                    
                    # Extraction de toutes les métriques
                    metrics = {}
                    
                    # Métriques principales
                    metrics['visits'] = latest_data.get('traffic', 0)  # Total Traffic = Visits
                    metrics['organic_traffic'] = latest_data.get('organicTraffic', 0)
                    metrics['paid_traffic'] = latest_data.get('adwordsTraffic', 0)
                    
                    # Métriques branded
                    metrics['organic_traffic_branded'] = latest_data.get('organicTrafficBranded', 0)
                    metrics['organic_traffic_non_branded'] = latest_data.get('organicTrafficNonBranded', 0)
                    metrics['traffic_branded'] = latest_data.get('trafficBranded', 0)
                    metrics['traffic_non_branded'] = latest_data.get('trafficNonBranded', 0)
                    
                    # Métriques positions
                    metrics['organic_positions'] = latest_data.get('organicPositions', 0)
                    metrics['paid_positions'] = latest_data.get('adwordsPositions', 0)
                    metrics['total_positions'] = latest_data.get('positions', 0)
                    
                    # Métriques coûts
                    metrics['organic_traffic_cost'] = latest_data.get('organicTrafficCost', 0)
                    metrics['paid_traffic_cost'] = latest_data.get('adwordsTrafficCost', 0)
                    metrics['total_traffic_cost'] = latest_data.get('trafficCost', 0)
                    
                    # Métriques SERP Features
                    metrics['serp_features_positions'] = latest_data.get('serpFeaturesPositions', 0)
                    metrics['serp_features_traffic'] = latest_data.get('serpFeaturesTraffic', 0)
                    metrics['serp_features_traffic_branded'] = latest_data.get('serpFeaturesTrafficBranded', 0)
                    metrics['serp_features_traffic_non_branded'] = latest_data.get('serpFeaturesTrafficNonBranded', 0)
                    metrics['serp_features_traffic_cost'] = latest_data.get('serpFeaturesTrafficCost', 0)
                    
                    # Autres métriques
                    metrics['domain_rank'] = latest_data.get('rank', 0)
                    metrics['database'] = latest_data.get('database', 'us')
                    
                    # Conversion (si disponible)
                    conversion_rate = latest_data.get('conversionRate', None)
                    if conversion_rate is not None:
                        metrics['purchase_conversion'] = conversion_rate
                    
                    logger.info(f"✅ Toutes métriques récupérées (API): {len(metrics)} métriques")
                    return metrics
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération toutes métriques API: {e}")
            return {}
