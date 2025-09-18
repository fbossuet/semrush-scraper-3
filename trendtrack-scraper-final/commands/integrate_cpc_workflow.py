#!/usr/bin/env python3
"""
Intégration de l'appel CPC dans le workflow principal
Ajoute l'appel CPC dans scrape_domain_overview pour qu'elle soit scrapée automatiquement
"""

import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_cpc_workflow():
    """Intègre l'appel CPC dans le workflow principal"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Backup
    backup_file = scraper_file.parent / f"production_scraper_parallel_backup_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(scraper_file, backup_file)
    logger.info(f"✅ Backup créé: {backup_file}")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver la méthode scrape_domain_overview
    if 'async def scrape_domain_overview' not in content:
        logger.error("❌ Méthode scrape_domain_overview non trouvée")
        return False
    
    # Chercher l'endroit où ajouter l'appel CPC
    # On va chercher une section où les métriques sont assignées
    metrics_assignments = [
        "metrics['organic_search_traffic']",
        "metrics['paid_search_traffic']", 
        "metrics['visits']",
        "metrics['bounce_rate']",
        "metrics['average_visit_duration']",
        "metrics['branded_traffic']",
        "metrics['conversion_rate']"
    ]
    
    insertion_point = None
    insertion_context = ""
    
    # Chercher un bon endroit pour insérer l'appel CPC
    for metric in metrics_assignments:
        if metric in content:
            # Trouver la ligne avec cette métrique
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if metric in line:
                    # Insérer après cette ligne
                    insertion_point = i + 1
                    insertion_context = line
                    break
            if insertion_point:
                break
    
    if not insertion_point:
        logger.error("❌ Aucun point d'insertion trouvé dans scrape_domain_overview")
        return False
    
    # Créer l'appel CPC
    cpc_call = '''        # CPC - Cost Per Click
        if 'cpc' not in existing_metrics or existing_metrics.get('cpc') in ['', '0', None]:
            cpc_value = await self.scrape_cpc_via_api(domain)
            metrics['cpc'] = cpc_value
            logger.info(f"💰 Worker {self.worker_id}: CPC extrait: {cpc_value}")
        else:
            metrics['cpc'] = existing_metrics.get('cpc', None)
            logger.info(f"💰 Worker {self.worker_id}: CPC existant: {existing_metrics.get('cpc')}")
'''
    
    # Insérer l'appel CPC
    lines = content.split('\n')
    
    # Trouver la ligne d'insertion avec la bonne indentation
    target_line = lines[insertion_point - 1]
    indentation = len(target_line) - len(target_line.lstrip())
    
    # Ajuster l'indentation de l'appel CPC
    cpc_lines = cpc_call.split('\n')
    indented_cpc_lines = []
    for line in cpc_lines:
        if line.strip():  # Si la ligne n'est pas vide
            indented_cpc_lines.append(' ' * indentation + line)
        else:
            indented_cpc_lines.append('')
    
    # Insérer les lignes CPC
    for i, cpc_line in enumerate(indented_cpc_lines):
        lines.insert(insertion_point + i, cpc_line)
    
    # Reconstituer le contenu
    new_content = '\n'.join(lines)
    
    # Vérifier que l'appel CPC a été ajouté
    if 'cpc_value = await self.scrape_cpc_via_api' in new_content:
        logger.info("✅ Appel CPC intégré dans le workflow")
        
        # Écrire le fichier modifié
        with open(scraper_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Test de syntaxe
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', str(scraper_file)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Intégration workflow CPC réussie - Syntaxe OK")
            return True
        else:
            logger.error(f"❌ Erreur de syntaxe: {result.stderr}")
            # Rollback
            shutil.copy2(backup_file, scraper_file)
            logger.info("🔄 Rollback effectué")
            return False
    else:
        logger.error("❌ Appel CPC non trouvé après insertion")
        return False

if __name__ == "__main__":
    logger.info("🎯 INTÉGRATION CPC DANS LE WORKFLOW PRINCIPAL")
    logger.info("=" * 60)
    
    success = integrate_cpc_workflow()
    
    if success:
        logger.info("🎉 INTÉGRATION WORKFLOW CPC TERMINÉE!")
        logger.info("")
        logger.info("📋 RÉSUMÉ:")
        logger.info("   ✅ Appel CPC intégré dans scrape_domain_overview")
        logger.info("   ✅ CPC sera scrapé avec toutes les autres métriques")
        logger.info("   ✅ Gestion des métriques existantes")
        logger.info("   ✅ Logs détaillés pour CPC")
        logger.info("")
        logger.info("📋 WORKFLOW COMPLET:")
        logger.info("   Quand tu lances menu_workers.py → choix 1:")
        logger.info("   1. Scrape organic_search_traffic")
        logger.info("   2. Scrape paid_search_traffic")
        logger.info("   3. Scrape visits")
        logger.info("   4. Scrape bounce_rate")
        logger.info("   5. Scrape average_visit_duration")
        logger.info("   6. Scrape branded_traffic")
        logger.info("   7. Scrape conversion_rate")
        logger.info("   8. 🆕 Scrape CPC (nouveau!)")
        logger.info("   9. Sauvegarde toutes les métriques en base")
        logger.info("")
        logger.info("🚀 PRÊT POUR LE TEST:")
        logger.info("   cd /home/ubuntu/sem-scraper-final")
        logger.info("   python3 menu_workers.py")
        logger.info("   # Choisir option 1")
    else:
        logger.error("❌ INTÉGRATION WORKFLOW ÉCHOUÉE")
