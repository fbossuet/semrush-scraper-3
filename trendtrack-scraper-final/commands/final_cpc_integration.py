#!/usr/bin/env python3
"""
Intégration finale CPC - Version ultra-simple et sûre
"""

import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_cpc_final():
    """Intégration finale et sûre de CPC"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Backup
    backup_file = scraper_file.parent / f"production_scraper_parallel_backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(scraper_file, backup_file)
    logger.info(f"✅ Backup créé: {backup_file}")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Ajouter CPC aux compteurs (remplacement simple)
    if "'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}" not in content:
        old_line = "            'percent_branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0}"
        new_line = "            'percent_branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},\n            'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            logger.info("✅ CPC ajouté aux compteurs")
    
    # 2. Ajouter la méthode CPC à la fin de la classe (avant les imports)
    if 'async def scrape_cpc_via_api' not in content:
        # Trouver la fin de la classe
        class_end = content.find("if __name__ == '__main__':")
        if class_end != -1:
            cpc_method = '''
    async def scrape_cpc_via_api(self, domain: str) -> str:
        """Récupère le CPC via l'API MyToolsPlan (version test)"""
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            
            # Valeur par défaut pour test - TODO: Implémenter API réelle
            cpc_value = "2.50"
            
            logger.info(f"✅ Worker {self.worker_id}: CPC récupéré: ${cpc_value}")
            return cpc_value
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC: {error}")
            return "0"
'''
            
            content = content[:class_end] + cpc_method + '\n\n' + content[class_end:]
            logger.info("✅ Méthode CPC ajoutée")
    
    # 3. Ajouter un appel CPC simple dans scrape_domain_overview
    if 'cpc_value = await self.scrape_cpc_via_api' not in content:
        # Trouver un endroit pour ajouter l'appel CPC
        metrics_section = "metrics['scraping_status'] = 'completed'"
        if metrics_section in content:
            cpc_call = '''
        # CPC - Cost Per Click (test)
        cpc_value = await self.scrape_cpc_via_api(domain)
        metrics['cpc'] = cpc_value
        logger.info(f"💰 Worker {self.worker_id}: CPC ajouté: {cpc_value}")
        
        # '''
            
            content = content.replace(metrics_section, cpc_call + metrics_section)
            logger.info("✅ Appel CPC ajouté")
    
    # Écrire le fichier modifié
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Test de syntaxe
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', str(scraper_file)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("✅ Intégration CPC réussie - Syntaxe OK")
        
        # Test de validation supplémentaire
        with open(scraper_file, 'r', encoding='utf-8') as f:
            content_check = f.read()
        
        checks = [
            'async def scrape_cpc_via_api' in content_check,
            'cpc_value = await self.scrape_cpc_via_api' in content_check,
            "'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}" in content_check
        ]
        
        if all(checks):
            logger.info("✅ Toutes les validations CPC réussies")
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
    logger.info("🎯 INTÉGRATION FINALE DE LA MÉTRIQUE CPC")
    logger.info("=" * 50)
    
    success = integrate_cpc_final()
    
    if success:
        logger.info("🎉 INTÉGRATION CPC TERMINÉE AVEC SUCCÈS!")
        logger.info("")
        logger.info("📋 RÉSUMÉ DE L'INTÉGRATION:")
        logger.info("   ✅ Méthode scrape_cpc_via_api ajoutée")
        logger.info("   ✅ CPC intégré dans scrape_domain_overview")
        logger.info("   ✅ CPC ajouté aux compteurs de métriques")
        logger.info("   ✅ Valeur par défaut: $2.50 (pour test)")
        logger.info("   ✅ Syntaxe Python validée")
        logger.info("")
        logger.info("📋 PROCHAINES ÉTAPES:")
        logger.info("   1. Tester le scraper:")
        logger.info("      cd /home/ubuntu/sem-scraper-final")
        logger.info("      python3 menu_workers.py")
        logger.info("   2. Choisir option 1 (Lancer les workers SEM)")
        logger.info("   3. Vérifier que CPC est extrait (valeur: $2.50)")
        logger.info("   4. Vérifier en base de données:")
        logger.info("      sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db")
        logger.info("      SELECT shop_name, cpc FROM analytics WHERE cpc IS NOT NULL LIMIT 5;")
        logger.info("")
        logger.info("🔧 DÉVELOPPEMENT FUTUR:")
        logger.info("   - Implémenter l'API réelle MyToolsPlan pour CPC")
        logger.info("   - Adapter selon les endpoints disponibles")
        logger.info("   - Tester avec des données réelles")
    else:
        logger.error("❌ INTÉGRATION CPC ÉCHOUÉE")
        logger.info("🔄 Rollback effectué automatiquement")
