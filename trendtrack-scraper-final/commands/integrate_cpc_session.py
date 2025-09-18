#!/usr/bin/env python3
"""
Intégration CPC dans session_data - Version adaptée à la structure réelle
"""

import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_cpc_session():
    """Intègre CPC dans session_data['data']['domain_overview']"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Backup
    backup_file = scraper_file.parent / f"production_scraper_parallel_backup_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(scraper_file, backup_file)
    logger.info(f"✅ Backup créé: {backup_file}")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Ajouter CPC dans les dictionnaires session_data
    replacements = [
        # Premier dictionnaire (cas 'na')
        (
            """                    self.session_data['data']['domain_overview'] = {
                        'organic_search_traffic': organic_traffic_value,
                        'paid_search_traffic': "",
                        'avg_visit_duration': "",
                        'bounce_rate': ""
                    }""",
            """                    self.session_data['data']['domain_overview'] = {
                        'organic_search_traffic': organic_traffic_value,
                        'paid_search_traffic': "",
                        'avg_visit_duration': "",
                        'bounce_rate': "",
                        'cpc': ""
                    }"""
        ),
        # Deuxième dictionnaire (succès API)
        (
            """                self.session_data['data']['domain_overview'] = {
                    'organic_search_traffic': api_result['organic_search_traffic'],
                    'paid_search_traffic': api_result['paid_search_traffic'],
                    'avg_visit_duration': "",
                    'bounce_rate': ""
                }""",
            """                self.session_data['data']['domain_overview'] = {
                    'organic_search_traffic': api_result['organic_search_traffic'],
                    'paid_search_traffic': api_result['paid_search_traffic'],
                    'avg_visit_duration': "",
                    'bounce_rate': "",
                    'cpc': ""
                }"""
        ),
        # Troisième dictionnaire (échec API)
        (
            """                self.session_data['data']['domain_overview'] = {
                    'organic_search_traffic': "",
                    'paid_search_traffic': "",
                    'avg_visit_duration': "",
                    'bounce_rate': ""
                }""",
            """                self.session_data['data']['domain_overview'] = {
                    'organic_search_traffic': "",
                    'paid_search_traffic': "",
                    'avg_visit_duration': "",
                    'bounce_rate': "",
                    'cpc': ""
                }"""
        )
    ]
    
    # Appliquer les remplacements
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            logger.info("✅ CPC ajouté dans session_data")
    
    # 2. Ajouter l'appel CPC et l'assignation dans la méthode
    # Trouver l'endroit après engagement_metrics
    engagement_line = "self.session_data['data']['domain_overview']['bounce_rate'] = engagement_metrics.get('bounce_rate', '')"
    
    if engagement_line in content:
        cpc_integration = '''
            
            # CPC - Cost Per Click
            cpc_value = await self.scrape_cpc_via_api(domain)
            self.session_data['data']['domain_overview']['cpc'] = cpc_value
            logger.info(f"💰 Worker {self.worker_id}: CPC extrait: {cpc_value}")
'''
        
        content = content.replace(engagement_line, engagement_line + cpc_integration)
        logger.info("✅ Appel CPC intégré dans scrape_domain_overview")
    
    # 3. Ajouter CPC dans les logs d'affichage
    log_section = """            logger.info(f"   🌱 Organic Search Traffic: {metrics.get('organic_search_traffic', 'N/A')}")
            logger.info(f"   💰 Paid Search Traffic: {metrics.get('paid_search_traffic', 'N/A')}")
            logger.info(f"   ⏱️ Average Visit Duration: {metrics.get('avg_visit_duration', 'N/A')}")
            logger.info(f"   📈 Bounce Rate: {metrics.get('bounce_rate', 'N/A')}")"""
    
    if log_section in content:
        cpc_log = '''
            logger.info(f"   💰 CPC: {metrics.get('cpc', 'N/A')}")'''
        
        content = content.replace(log_section, log_section + cpc_log)
        logger.info("✅ CPC ajouté dans les logs d'affichage")
    
    # Écrire le fichier modifié
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Test de syntaxe
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', str(scraper_file)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("✅ Intégration CPC session réussie - Syntaxe OK")
        
        # Vérifier que les modifications sont présentes
        with open(scraper_file, 'r', encoding='utf-8') as f:
            content_check = f.read()
        
        checks = [
            "'cpc': \"\"" in content_check,
            "cpc_value = await self.scrape_cpc_via_api" in content_check,
            "self.session_data['data']['domain_overview']['cpc']" in content_check,
            "logger.info(f\"💰 Worker {self.worker_id}: CPC extrait:" in content_check
        ]
        
        if all(checks):
            logger.info("✅ Toutes les intégrations CPC validées")
            return True
        else:
            logger.error("❌ Validations CPC échouées")
            return False
    else:
        logger.error(f"❌ Erreur de syntaxe: {result.stderr}")
        # Rollback
        shutil.copy2(backup_file, scraper_file)
        logger.info("🔄 Rollback effectué")
        return False

if __name__ == "__main__":
    logger.info("🎯 INTÉGRATION CPC DANS SESSION_DATA")
    logger.info("=" * 50)
    
    success = integrate_cpc_session()
    
    if success:
        logger.info("🎉 INTÉGRATION CPC SESSION TERMINÉE!")
        logger.info("")
        logger.info("📋 RÉSUMÉ:")
        logger.info("   ✅ CPC ajouté dans tous les dictionnaires session_data")
        logger.info("   ✅ Appel CPC intégré dans scrape_domain_overview")
        logger.info("   ✅ CPC ajouté dans les logs d'affichage")
        logger.info("   ✅ CPC sera scrapé avec toutes les autres métriques")
        logger.info("")
        logger.info("📋 WORKFLOW COMPLET:")
        logger.info("   Quand tu lances menu_workers.py → choix 1:")
        logger.info("   1. Scrape organic_search_traffic")
        logger.info("   2. Scrape paid_search_traffic") 
        logger.info("   3. Scrape avg_visit_duration")
        logger.info("   4. Scrape bounce_rate")
        logger.info("   5. 🆕 Scrape CPC (nouveau!)")
        logger.info("   6. Sauvegarde toutes les métriques en base")
        logger.info("")
        logger.info("🚀 PRÊT POUR LE TEST:")
        logger.info("   cd /home/ubuntu/sem-scraper-final")
        logger.info("   python3 menu_workers.py")
        logger.info("   # Choisir option 1")
    else:
        logger.error("❌ INTÉGRATION CPC SESSION ÉCHOUÉE")
