#!/usr/bin/env python3
"""
Script de rollback pour sem-scraper-final 20250805_204410
Restaure les fichiers originaux depuis le backup
"""

import os
import shutil
from datetime import datetime, timezone

def rollback_sem_scraper():
    """Restaure sem-scraper-final depuis le backup"""
    try:
        backup_path = "sem-scraper-backups/sem-scraper-backup_20250805_204410"
        sem_scraper_path = "/home/ubuntu/sem-scraper-final"
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup non trouvé: {backup_path}")
            return False
        
        # Créer un backup de l'état actuel avant rollback
        current_backup = f"pre_rollback_sem_scraper_{datetime.now(timezone.utc).isoformat()}"
        shutil.copytree(sem_scraper_path, current_backup)
        print(f"✅ Backup de l'état actuel créé: {current_backup}")
        
        # Supprimer le répertoire actuel
        shutil.rmtree(sem_scraper_path)
        
        # Restaurer depuis le backup original
        shutil.copytree(backup_path, sem_scraper_path)
        print(f"✅ sem-scraper-final restauré depuis: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur rollback: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Début du rollback sem-scraper-final...")
    if rollback_sem_scraper():
        print("✅ Rollback terminé avec succès")
    else:
        print("❌ Échec du rollback")
