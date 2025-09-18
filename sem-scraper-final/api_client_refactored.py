#!/usr/bin/env python3
"""
🌐 APICLIENT REFACTORISÉ - UN SEUL APPEL POUR TOUTES LES MÉTRIQUES
Version optimisée qui utilise un seul appel organic.OverviewTrend
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIClientRefactored:
    """
    🌐 Client API refactorisé pour récupérer toutes les métriques en un seul appel
    """
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.credentials_manager = None
    
    async def initialize(self):
        """🚀 Initialisation du navigateur et des credentials"""
        try:
            # Import dynamique pour éviter les erreurs
            from credentials_manager import CredentialsManager
            
            self.credentials_manager = CredentialsManager()
            await self.credentials_manager.initialize()
            
            # Lancement du navigateur
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            
            logger.info("✅ APIClientRefactored initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation APIClientRefactored: {e}")
            raise
    
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
    
    async def _call_api(self, method: str, params: Dict[str, Any], worker_id: str = "api") -> Dict[str, Any]:
        """
        Appel API générique avec headers corrects
        
        Args:
            method: Méthode API à appeler
            params: Paramètres de l'API
            worker_id: Identifiant du worker pour les logs
            
        Returns:
            dict: Réponse de l'API
        """
        logger.info(f"🌐 Worker {worker_id}: Appel API {method}")
        
        # Navigation vers sam.mytoolsplan.xyz (comme dans le code existant)
        await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        
        # Récupération des credentials
        credentials = await self.credentials_manager.get_credentials()
        
        # Structure d'appel identique au code existant avec headers corrects
        result = await self.page.evaluate("""
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
                    
                    if (!response.ok) {
                        return { error: `HTTP ${response.status}: ${response.statusText}` };
                    }
                    
                    const result = await response.json();
                    
                    if (result.error) {
                        return { error: result.error };
                    }
                    
                    return { success: true, data: result.result };
                    
                } catch (error) {
                    return { error: error.toString() };
                }
            }
        """, {
            'method': method,
            'params': params,
            'credentials': credentials
        })
        
        if result.get('error'):
            logger.error(f"❌ Erreur API {method}: {result['error']}")
            return {}
        
        logger.info(f"✅ API {method} réussie")
        return result
    
    async def get_all_metrics_via_api(self, domain: str, target_date: str = "20250715") -> Dict[str, Any]:
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
    
    async def close(self):
        """🔒 Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
            logger.info("🔒 Navigateur fermé")

# Test en isolation
async def test_refactored_api():
    """🧪 Test de l'APIClient refactorisé"""
    print("🧪 TEST APICLIENT REFACTORISÉ")
    print("=" * 50)
    
    client = APIClientRefactored()
    
    try:
        # Initialisation
        await client.initialize()
        
        # Test sur un domaine
        domain = "spanx.com"
        metrics = await client.get_all_metrics_via_api(domain)
        
        if metrics:
            print(f"✅ Métriques récupérées pour {domain}:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Aucune métrique récupérée pour {domain}")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_refactored_api())
