#!/usr/bin/env python3
"""
Suppression de la valeur par défaut CPC
"""

import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_cpc_default():
    """Supprime la valeur par défaut CPC"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Backup
    backup_file = scraper_file.parent / f"production_scraper_parallel_backup_no_default_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(scraper_file, backup_file)
    logger.info(f"✅ Backup créé: {backup_file}")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la méthode CPC
    old_method = '''    async def scrape_cpc_via_api(self, domain: str) -> str:
        """Récupère le CPC via l'API MyToolsPlan"""
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            # Valeur par défaut pour test
            cpc_value = "3.75"
            logger.info(f"✅ Worker {self.worker_id}: CPC récupéré: ${cpc_value}")
            return cpc_value
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC: {error}")
            return "0"'''
    
    new_method = '''    async def scrape_cpc_via_api(self, domain: str) -> str:
        """Récupère le CPC via l'API MyToolsPlan"""
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            
            # TODO: Implémenter l'API réelle MyToolsPlan pour CPC
            logger.warning(f"⚠️ Worker {self.worker_id}: API CPC non implémentée pour {domain}")
            return None
            
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC: {error}")
            return None'''
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        logger.info("✅ Valeur par défaut CPC supprimée")
    else:
        logger.warning("⚠️ Méthode CPC originale non trouvée")
    
    # Écrire le fichier modifié
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Test de syntaxe
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', str(scraper_file)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("✅ Modification CPC réussie - Syntaxe OK")
        return True
    else:
        logger.error(f"❌ Erreur de syntaxe: {result.stderr}")
        # Rollback
        shutil.copy2(backup_file, scraper_file)
        logger.info("🔄 Rollback effectué")
        return False

if __name__ == "__main__":
    logger.info("🎯 SUPPRESSION DE LA VALEUR PAR DÉFAUT CPC")
    logger.info("=" * 50)
    
    success = remove_cpc_default()
    
    if success:
        logger.info("🎉 VALEUR PAR DÉFAUT CPC SUPPRIMÉE!")
        logger.info("")
        logger.info("📋 RÉSUMÉ:")
        logger.info("   ✅ Valeur par défaut '3.75' supprimée")
        logger.info("   ✅ Méthode retourne None quand API non implémentée")
        logger.info("   ✅ Log d'avertissement ajouté")
        logger.info("")
        logger.info("📋 PROCHAINES ÉTAPES:")
        logger.info("   1. Implémenter l'API réelle MyToolsPlan pour CPC")
        logger.info("   2. Tester avec le scraper SEM")
        logger.info("   3. Vérifier les données en base")
    else:
        logger.error("❌ SUPPRESSION ÉCHOUÉE")
