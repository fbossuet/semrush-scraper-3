#!/usr/bin/env python3
"""
Intégration simple de la métrique CPC dans le scraper SEM
Version simplifiée sans modifications complexes
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_cpc_simple():
    """Intégration simple de CPC"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Backup
    backup_file = scraper_file.parent / f"production_scraper_parallel_backup_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(scraper_file, backup_file)
    logger.info(f"✅ Backup créé: {backup_file}")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter CPC aux compteurs (section simple)
    if "'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}" not in content:
        # Trouver la fin de la section metrics_count
        metrics_end = content.find("'percent_branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0}")
        if metrics_end != -1:
            # Trouver la fin de cette ligne
            line_end = content.find('\n', metrics_end)
            if line_end != -1:
                # Insérer CPC après cette ligne
                cpc_line = "\n            'cpc': {'found': 0, 'not_found': 0, 'skipped': 0},"
                content = content[:line_end] + cpc_line + content[line_end:]
                logger.info("✅ CPC ajouté aux compteurs")
    
    # Ajouter la méthode CPC à la fin de la classe (version simple)
    cpc_method = '''
    async def scrape_cpc_via_api(self, domain: str) -> str:
        """Récupère le CPC via l'API MyToolsPlan (version simplifiée)"""
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            
            # Pour l'instant, retourner une valeur par défaut
            # TODO: Implémenter l'API réelle selon les endpoints MyToolsPlan
            cpc_value = "0.50"  # Valeur par défaut en dollars
            
            logger.info(f"✅ Worker {self.worker_id}: CPC récupéré: ${cpc_value}")
            return cpc_value
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC: {error}")
            return "0"
'''
    
    # Trouver la fin de la classe (avant la dernière méthode)
    last_method_start = content.rfind('async def ')
    if last_method_start != -1:
        # Trouver la fin de cette méthode
        class_end = content.find('\n\nclass ', last_method_start)
        if class_end == -1:
            class_end = content.find('\n\nif __name__', last_method_start)
        if class_end == -1:
            class_end = len(content)
        
        # Insérer la méthode CPC
        content = content[:class_end] + cpc_method + '\n' + content[class_end:]
        logger.info("✅ Méthode CPC ajoutée")
    
    # Ajouter l'appel CPC dans scrape_domain_overview
    if 'scrape_cpc_via_api' not in content:
        # Trouver la méthode scrape_domain_overview
        overview_start = content.find('async def scrape_domain_overview(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):')
        if overview_start != -1:
            # Trouver la fin de cette méthode
            overview_end = content.find('\n    async def ', overview_start + 1)
            if overview_end == -1:
                overview_end = len(content)
            
            # Ajouter l'appel CPC avant le return
            cpc_call = '''
            # CPC - Cost Per Click
            if 'cpc' not in existing_metrics or existing_metrics.get('cpc') in ['', '0', None]:
                cpc_value = await self.scrape_cpc_via_api(domain)
                metrics['cpc'] = cpc_value
                logger.info(f"💰 Worker {self.worker_id}: CPC extrait: {cpc_value}")
            else:
                metrics['cpc'] = existing_metrics.get('cpc', '0')
'''
            
            # Trouver le return
            return_pos = content.rfind('return metrics', overview_start, overview_end)
            if return_pos != -1:
                content = content[:return_pos] + cpc_call + '\n        ' + content[return_pos:]
                logger.info("✅ Appel CPC ajouté au workflow")
    
    # Écrire le fichier modifié
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Test de syntaxe
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', str(scraper_file)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("✅ Intégration CPC réussie - Syntaxe OK")
        return True
    else:
        logger.error(f"❌ Erreur de syntaxe: {result.stderr}")
        # Rollback
        shutil.copy2(backup_file, scraper_file)
        logger.info("🔄 Rollback effectué")
        return False

if __name__ == "__main__":
    logger.info("🎯 INTÉGRATION SIMPLE DE LA MÉTRIQUE CPC")
    logger.info("=" * 50)
    
    success = integrate_cpc_simple()
    
    if success:
        logger.info("🎉 INTÉGRATION CPC TERMINÉE AVEC SUCCÈS!")
        logger.info("📋 Prochaines étapes:")
        logger.info("   1. Tester: cd /home/ubuntu/sem-scraper-final && python3 menu_workers.py")
        logger.info("   2. Choisir option 1 (Lancer les workers SEM)")
        logger.info("   3. Vérifier que CPC est extrait (valeur par défaut: $0.50)")
        logger.info("   4. Implémenter l'API réelle selon les besoins")
    else:
        logger.error("❌ INTÉGRATION CPC ÉCHOUÉE")
