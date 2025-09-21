#!/usr/bin/env python3
"""
Test de l'implémentation CPC et du système de credentials
Créé le 18 janvier 2025
"""

import asyncio
import logging
import sys
import os

# Ajouter le répertoire au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_credentials import get_api_credentials, get_credentials_dict
from api_client_refactored import APIClientRefactored

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_credentials_system():
    """Test du système de credentials"""
    print("🧪 Test 1: Système de credentials")
    
    # Test des credentials
    creds = get_api_credentials()
    creds_dict = get_credentials_dict()
    
    print(f"✅ Credentials: {creds}")
    print(f"✅ Dictionnaire: {creds_dict}")
    print(f"✅ Source: {creds.get_source()}")
    print(f"✅ Depuis environnement: {creds.is_from_environment()}")
    
    return True

async def test_api_client_cpc():
    """Test de l'API client avec récupération CPC"""
    print("\n🧪 Test 2: API Client avec CPC")
    
    try:
        # Initialiser l'API client
        api_client = APIClientRefactored()
        await api_client.initialize()
        
        # Test avec un domaine
        test_domain = "spanx.com"
        target_date = "20250115"
        
        print(f"🔍 Test avec le domaine: {test_domain}")
        
        # Récupérer toutes les métriques (incluant CPC)
        metrics = await api_client.get_all_metrics_via_api(test_domain, target_date)
        
        if metrics:
            print(f"✅ Métriques récupérées: {len(metrics)} métriques")
            
            # Vérifier les métriques de coût et CPC
            print(f"📊 Métriques de coût:")
            print(f"   - Organic Traffic Cost: {metrics.get('organic_traffic_cost', 'N/A')}")
            print(f"   - Paid Traffic Cost: {metrics.get('paid_traffic_cost', 'N/A')}")
            print(f"   - Total Traffic Cost: {metrics.get('total_traffic_cost', 'N/A')}")
            print(f"   - CPC calculé: {metrics.get('cpc', 'N/A')}")
            
            # Vérifier les métriques de trafic
            print(f"📈 Métriques de trafic:")
            print(f"   - Visits (Total Traffic): {metrics.get('visits', 'N/A')}")
            print(f"   - Organic Traffic: {metrics.get('organic_traffic', 'N/A')}")
            print(f"   - Paid Traffic: {metrics.get('paid_traffic', 'N/A')}")
            
            # Validation du calcul CPC
            paid_traffic = metrics.get('paid_traffic', 0)
            paid_traffic_cost = metrics.get('paid_traffic_cost', 0)
            cpc_calculated = metrics.get('cpc', 0)
            
            if paid_traffic > 0 and paid_traffic_cost > 0:
                expected_cpc = round(paid_traffic_cost / paid_traffic, 4)
                print(f"🧮 Validation CPC:")
                print(f"   - CPC récupéré: {cpc_calculated}")
                print(f"   - CPC attendu: {expected_cpc}")
                print(f"   - Match: {'✅' if cpc_calculated == expected_cpc else '❌'}")
            else:
                print(f"⚠️ Pas de trafic payant pour valider le CPC")
            
            return True
        else:
            print("❌ Aucune métrique récupérée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test API: {e}")
        return False
    finally:
        if 'api_client' in locals():
            await api_client.close()

async def test_production_scraper_integration():
    """Test de l'intégration avec le scraper de production"""
    print("\n🧪 Test 3: Intégration Production Scraper")
    
    try:
        # Import du scraper de production
        from production_scraper_parallel import ParallelProductionScraper
        
        # Créer une instance de test
        scraper = ParallelProductionScraper(worker_id=999)
        
        # Test de la méthode get_overview_trend_metrics_via_api
        test_domain = "spanx.com"
        
        print(f"🔍 Test de get_overview_trend_metrics_via_api avec: {test_domain}")
        
        # Initialiser le scraper (sans navigateur pour ce test)
        scraper.session_data = {'data': {}}
        
        # Simuler l'initialisation de l'API client
        scraper.api_client = APIClientRefactored()
        await scraper.api_client.initialize()
        
        # Test de la récupération des métriques
        result = await scraper.get_overview_trend_metrics_via_api(test_domain)
        
        if result:
            print(f"✅ Métriques récupérées par le scraper:")
            print(f"   - Traffic: {result.get('traffic', 'N/A')}")
            print(f"   - Branded Traffic: {result.get('branded_traffic', 'N/A')}")
            print(f"   - CPC: {result.get('cpc', 'N/A')}")
            print(f"   - Source: {result.get('source', 'N/A')}")
            
            return True
        else:
            print("❌ Aucune métrique récupérée par le scraper")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False
    finally:
        if 'scraper' in locals() and hasattr(scraper, 'api_client'):
            await scraper.api_client.close()

async def main():
    """Fonction principale de test"""
    print("🚀 Début des tests CPC et Credentials")
    print("=" * 50)
    
    results = []
    
    # Test 1: Système de credentials
    try:
        result1 = await test_credentials_system()
        results.append(("Credentials System", result1))
    except Exception as e:
        print(f"❌ Erreur test credentials: {e}")
        results.append(("Credentials System", False))
    
    # Test 2: API Client avec CPC
    try:
        result2 = await test_api_client_cpc()
        results.append(("API Client CPC", result2))
    except Exception as e:
        print(f"❌ Erreur test API client: {e}")
        results.append(("API Client CPC", False))
    
    # Test 3: Intégration Production Scraper
    try:
        result3 = await test_production_scraper_integration()
        results.append(("Production Scraper Integration", result3))
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        results.append(("Production Scraper Integration", False))
    
    # Résumé des résultats
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    total_success = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n🎯 Résultat global: {total_success}/{total_tests} tests réussis")
    
    if total_success == total_tests:
        print("🎉 Tous les tests sont passés avec succès!")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        sys.exit(1)
