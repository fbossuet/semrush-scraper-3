#!/usr/bin/env python3
"""
Test de production pour la recherche par domaine TrendTrack
Test avec un domaine existant et un nouveau domaine
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.domain_search.domain_scraper import DomainSearchScraper, DomainSearchIntegration

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/production_test_{datetime.now(timezone.utc).isoformat()}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def test_production_domain_search():
    """Test de production avec domaine existant et nouveau domaine"""
    
    logger.info("🚀 DÉBUT DU TEST DE PRODUCTION - RECHERCHE PAR DOMAINE")
    logger.info("=" * 80)
    
    # Domaines de test
    test_domains = [
        {
            "domain": "nike.com",
            "type": "existant",
            "description": "Domaine existant (probablement déjà en BDD)"
        },
        {
            "domain": "techstartup2024.io",
            "type": "nouveau", 
            "description": "Nouveau domaine inventé (ne devrait pas exister)"
        }
    ]
    
    # Initialiser l'intégration base de données
    db_integration = DomainSearchIntegration()
    
    # Vérifier l'état initial
    logger.info("📊 ÉTAT INITIAL DE LA BASE DE DONNÉES:")
    import sqlite3
    conn = sqlite3.connect('data/trendtrack.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM shops WHERE project_source = 'semtotrendtrack'")
    initial_count = cursor.fetchone()[0]
    logger.info(f"   - Shops avec source 'semtotrendtrack': {initial_count}")
    
    cursor.execute("SELECT COUNT(*) FROM shops WHERE shop_url LIKE '%nike.com%'")
    nike_exists = cursor.fetchone()[0]
    logger.info(f"   - Shops Nike existants: {nike_exists}")
    
    cursor.execute("SELECT COUNT(*) FROM shops WHERE shop_url LIKE '%techstartup2024.io%'")
    techstartup_exists = cursor.fetchone()[0]
    logger.info(f"   - Shops techstartup2024.io existants: {techstartup_exists}")
    
    conn.close()
    
    logger.info("")
    logger.info("🎯 DÉBUT DES TESTS DE RECHERCHE:")
    logger.info("=" * 80)
    
    results = []
    
    for i, test_case in enumerate(test_domains, 1):
        domain = test_case["domain"]
        test_type = test_case["type"]
        description = test_case["description"]
        
        logger.info(f"")
        logger.info(f"🔍 TEST {i}/2: {domain} ({test_type})")
        logger.info(f"   Description: {description}")
        logger.info("-" * 60)
        
        try:
            # Credentials TrendTrack
            credentials = {
                'email': 'seif.alyakoob@gmail.com',
                'password': 'Toulouse31!'
            }
            
            # Initialiser le scraper
            scraper = DomainSearchScraper(credentials)
            
            # Initialiser avec authentification
            if not await scraper.initialize():
                logger.error(f"❌ Échec de l'initialisation pour {domain}")
                results.append({
                    "domain": domain,
                    "type": test_type,
                    "success": False,
                    "error": "Échec initialisation"
                })
                continue
            
            # Effectuer la recherche
            logger.info(f"🎯 Recherche en cours pour {domain}...")
            result = await scraper.search_domain(domain)
            
            if result:
                logger.info(f"✅ Recherche réussie pour {domain}")
                logger.info(f"   - Statut: {result.get('scraping_status', 'N/A')}")
                logger.info(f"   - Résultat: {result.get('search_result', 'N/A')}")
                
                if result.get('search_result') == 'found':
                    logger.info(f"   - Nom du site: {result.get('site_name', 'N/A')}")
                    logger.info(f"   - Visites mensuelles: {result.get('monthly_traffic', 'N/A')}")
                    logger.info(f"   - Revenus mensuels: {result.get('monthly_revenue', 'N/A')}")
                    logger.info(f"   - Publicités: {result.get('current_ads', 'N/A')}")
                
                # Stocker le résultat
                stored = db_integration.store_domain_result(result)
                logger.info(f"   - Stocké en BDD: {'✅' if stored else '❌'}")
                
                results.append({
                    "domain": domain,
                    "type": test_type,
                    "success": True,
                    "result": result,
                    "stored": stored
                })
            else:
                logger.error(f"❌ Échec de la recherche pour {domain}")
                results.append({
                    "domain": domain,
                    "type": test_type,
                    "success": False,
                    "error": "Échec recherche"
                })
            
            # Fermer le scraper
            await scraper.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test {domain}: {e}")
            results.append({
                "domain": domain,
                "type": test_type,
                "success": False,
                "error": str(e)
            })
    
    # Vérifier l'état final
    logger.info("")
    logger.info("📊 ÉTAT FINAL DE LA BASE DE DONNÉES:")
    logger.info("=" * 80)
    
    conn = sqlite3.connect('data/trendtrack.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM shops WHERE project_source = 'semtotrendtrack'")
    final_count = cursor.fetchone()[0]
    logger.info(f"   - Shops avec source 'semtotrendtrack': {final_count} (+{final_count - initial_count})")
    
    # Vérifier les domaines testés
    for test_case in test_domains:
        domain = test_case["domain"]
        cursor.execute("SELECT shop_name, monthly_visits, monthly_revenue, live_ads, project_source FROM shops WHERE shop_url LIKE ? ORDER BY updated_at DESC LIMIT 1", (f'%{domain}%',))
        row = cursor.fetchone()
        if row:
            logger.info(f"   - {domain}: {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
        else:
            logger.info(f"   - {domain}: Non trouvé en BDD")
    
    conn.close()
    
    # Résumé des tests
    logger.info("")
    logger.info("📋 RÉSUMÉ DES TESTS:")
    logger.info("=" * 80)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    logger.info(f"✅ Tests réussis: {len(successful_tests)}/{len(results)}")
    logger.info(f"❌ Tests échoués: {len(failed_tests)}/{len(results)}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        logger.info(f"   {status} {result['domain']} ({result['type']})")
        if not result["success"]:
            logger.info(f"      Erreur: {result.get('error', 'N/A')}")
    
    logger.info("")
    logger.info("🎉 TEST DE PRODUCTION TERMINÉ")
    logger.info("=" * 80)
    
    return results

if __name__ == "__main__":
    # Créer le répertoire logs si nécessaire
    os.makedirs("logs", exist_ok=True)
    
    # Lancer le test
    asyncio.run(test_production_domain_search())


