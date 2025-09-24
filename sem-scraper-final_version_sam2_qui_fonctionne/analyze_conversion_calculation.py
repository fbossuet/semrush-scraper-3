#!/usr/bin/env python3
"""
Analyse pour calculer la conversion à partir des données disponibles
"""

import asyncio
import logging
from production_scraper_api_integrated import ProductionScraper

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_conversion_calculation():
    """🔍 Analyse pour calculer la conversion"""
    
    scraper = ProductionScraper()
    
    try:
        # Initialiser le navigateur
        await scraper.setup_browser()
        
        # Authentifier
        await scraper.authenticate_mytoolsplan()
        
        print("=" * 80)
        print("🔍 ANALYSE CALCUL CONVERSION")
        print("=" * 80)
        
        domain = "spanx.com"
        
        # Naviguer vers sam.mytoolsplan.xyz pour l'API
        await scraper.page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        
        # Paramètres API
        params = {
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "date": "20250715",
            "dateType": "monthly",
            "dateFormat": "date",
            "positionsType": "all",
            "dateRange": None,
            "global": False
        }
        
        # Appel API
        result = await scraper.page.evaluate("""
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
                            id: new Date().toISOString(),
                            jsonrpc: "2.0",
                            method: "organic.OverviewTrend",
                            params: {
                                request_id: crypto.randomUUID(),
                                report: "domain.overview",
                                args: data.params,
                                userId: data.credentials.userId,
                                apiKey: data.credentials.apiKey
                            }
                        })
                    });
                    
                    if (!response.ok) {
                        const text = await response.text();
                        return { error: `HTTP ${response.status}: ${text}` };
                    }
                    
                    const responseText = await response.text();
                    let jsonResponse;
                    try {
                        jsonResponse = JSON.parse(responseText);
                    } catch (e) {
                        return { error: 'JSON parse error', raw: responseText };
                    }
                    
                    return {
                        status: response.status,
                        parsed: jsonResponse
                    };
                } catch (error) {
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
        
        if result.get('parsed', {}).get('result'):
            data = result['parsed']['result']
            print(f"📊 Analyse de {len(data)} entrées")
            
            if data:
                latest = data[-1]
                print(f"\n📅 Dernière entrée ({latest.get('date', 'N/A')}):")
                
                # Analyser les métriques disponibles pour calculer la conversion
                traffic_total = latest.get('traffic', 0)
                organic_traffic = latest.get('organicTraffic', 0)
                paid_traffic = latest.get('adwordsTraffic', 0)
                traffic_cost = latest.get('trafficCost', 0)
                
                print(f"\n📊 MÉTRIQUES DISPONIBLES:")
                print(f"   Traffic Total: {traffic_total:,}")
                print(f"   Organic Traffic: {organic_traffic:,}")
                print(f"   Paid Traffic: {paid_traffic:,}")
                print(f"   Traffic Cost: ${traffic_cost:,}")
                
                # Essayer différents calculs de conversion possibles
                print(f"\n🧮 CALCULS CONVERSION POSSIBLES:")
                
                # 1. Conversion basée sur le coût vs traffic
                if traffic_total > 0 and traffic_cost > 0:
                    cost_per_visit = traffic_cost / traffic_total
                    print(f"   1. Coût par visite: ${cost_per_visit:.4f}")
                
                # 2. Ratio organic vs paid
                if organic_traffic > 0 and paid_traffic > 0:
                    organic_ratio = organic_traffic / (organic_traffic + paid_traffic) * 100
                    paid_ratio = paid_traffic / (organic_traffic + paid_traffic) * 100
                    print(f"   2. Ratio Organic: {organic_ratio:.1f}%")
                    print(f"   3. Ratio Paid: {paid_ratio:.1f}%")
                
                # 3. Analyser les intentions (commercial, transactionnel, etc.)
                commercial_traffic = latest.get('intentCommercialTraffic', 0)
                transactional_traffic = latest.get('intentTransactionalTraffic', 0)
                navigational_traffic = latest.get('intentNavigationalTraffic', 0)
                
                print(f"\n🎯 TRAFFIC PAR INTENTION:")
                print(f"   Commercial: {commercial_traffic:,}")
                print(f"   Transactionnel: {transactional_traffic:,}")
                print(f"   Navigationnel: {navigational_traffic:,}")
                
                if traffic_total > 0:
                    commercial_rate = commercial_traffic / traffic_total * 100
                    transactional_rate = transactional_traffic / traffic_total * 100
                    navigational_rate = navigational_traffic / traffic_total * 100
                    
                    print(f"\n📈 TAUX PAR INTENTION:")
                    print(f"   Commercial: {commercial_rate:.1f}%")
                    print(f"   Transactionnel: {transactional_rate:.1f}%")
                    print(f"   Navigationnel: {navigational_rate:.1f}%")
                    
                    # Le taux transactionnel pourrait être proche de la conversion
                    print(f"\n💡 HYPOTHÈSE:")
                    print(f"   Le taux transactionnel ({transactional_rate:.1f}%) pourrait être")
                    print(f"   une approximation du taux de conversion!")
                
                # 4. Vérifier s'il y a des champs cachés ou mal nommés
                print(f"\n🔍 CHAMPS NUMÉRIQUES SUSPECTS:")
                for key, value in latest.items():
                    if isinstance(value, (int, float)) and value > 0 and value < 100:
                        if any(word in key.lower() for word in ['rate', 'ratio', 'percent', 'conversion']):
                            print(f"   🎯 {key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
    
    finally:
        # Fermer le navigateur si disponible
        if hasattr(scraper, 'browser') and scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_conversion_calculation())
