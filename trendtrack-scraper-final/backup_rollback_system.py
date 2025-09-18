#!/usr/bin/env python3
"""
Système de sauvegarde et rollback pour TrendTrack Scraper
Permet de sauvegarder et restaurer l'état du système avant modifications majeures
"""

import os
import shutil
import sqlite3
import json
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupRollbackSystem:
    """Système de sauvegarde et rollback complet"""
    
    def __init__(self, base_path: str = "/home/ubuntu/trendtrack-scraper-final"):
        self.base_path = Path(base_path)
        self.backup_dir = self.base_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Fichiers critiques à sauvegarder
        self.critical_files = [
            "smart_scraper_intelligent.py",
            "scrapers/domain_search/domain_scraper.py",
            "scrapers/traditional/smart_scraper_intelligent.py",
            "data/trendtrack.db",
            "data/trendtrack_test.db",
            "trendtrack_api.py",
            "database_manager.py",
            "domains_to_search.py"
        ]
        
        # Répertoires critiques
        self.critical_dirs = [
            "scrapers/",
            "auth/",
            "browser/",
            "config/",
            "utils/"
        ]
    
    def create_backup(self, backup_name: str = None) -> str:
        """
        Crée une sauvegarde complète du système
        
        Args:
            backup_name: Nom de la sauvegarde (optionnel)
            
        Returns:
            str: Chemin vers la sauvegarde créée
        """
        if not backup_name:
            timestamp = datetime.datetime.now(timezone.utc).isoformat()
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"🔄 Création de la sauvegarde: {backup_name}")
        
        # 1. Sauvegarder les fichiers critiques
        files_backup_dir = backup_path / "files"
        files_backup_dir.mkdir(exist_ok=True)
        
        for file_path in self.critical_files:
            source = self.base_path / file_path
            if source.exists():
                dest = files_backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                logger.info(f"  ✅ Fichier sauvegardé: {file_path}")
            else:
                logger.warning(f"  ⚠️ Fichier non trouvé: {file_path}")
        
        # 2. Sauvegarder les répertoires critiques
        dirs_backup_dir = backup_path / "directories"
        dirs_backup_dir.mkdir(exist_ok=True)
        
        for dir_path in self.critical_dirs:
            source = self.base_path / dir_path
            if source.exists():
                dest = dirs_backup_dir / dir_path
                shutil.copytree(source, dest, dirs_exist_ok=True)
                logger.info(f"  ✅ Répertoire sauvegardé: {dir_path}")
            else:
                logger.warning(f"  ⚠️ Répertoire non trouvé: {dir_path}")
        
        # 3. Sauvegarder les bases de données
        db_backup_dir = backup_path / "databases"
        db_backup_dir.mkdir(exist_ok=True)
        
        for db_file in ["trendtrack.db", "trendtrack_test.db"]:
            source_db = self.base_path / "data" / db_file
            if source_db.exists():
                dest_db = db_backup_dir / db_file
                shutil.copy2(source_db, dest_db)
                logger.info(f"  ✅ Base de données sauvegardée: {db_file}")
            else:
                logger.warning(f"  ⚠️ Base de données non trouvée: {db_file}")
        
        # 4. Créer un manifeste de la sauvegarde
        manifest = {
            "backup_name": backup_name,
            "created_at": datetime.datetime.now(timezone.utc).isoformat(),
            "base_path": str(self.base_path),
            "files_backed_up": [f for f in self.critical_files if (self.base_path / f).exists()],
            "directories_backed_up": [d for d in self.critical_dirs if (self.base_path / d).exists()],
            "databases_backed_up": [db for db in ["trendtrack.db", "trendtrack_test.db"] 
                                  if (self.base_path / "data" / db).exists()]
        }
        
        manifest_path = backup_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"✅ Sauvegarde complète créée: {backup_path}")
        return str(backup_path)
    
    def list_backups(self) -> List[Dict]:
        """Liste toutes les sauvegardes disponibles"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        backups.append(manifest)
                else:
                    # Sauvegarde sans manifeste (ancienne)
                    backups.append({
                        "backup_name": backup_dir.name,
                        "created_at": "Unknown",
                        "base_path": str(self.base_path),
                        "files_backed_up": [],
                        "directories_backed_up": [],
                        "databases_backed_up": []
                    })
        
        return sorted(backups, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def restore_backup(self, backup_name: str, confirm: bool = False) -> bool:
        """
        Restaure une sauvegarde
        
        Args:
            backup_name: Nom de la sauvegarde à restaurer
            confirm: Confirmation explicite requise
            
        Returns:
            bool: True si la restauration a réussi
        """
        if not confirm:
            logger.error("❌ Confirmation requise pour la restauration")
            return False
        
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error(f"❌ Sauvegarde non trouvée: {backup_name}")
            return False
        
        logger.info(f"🔄 Restauration de la sauvegarde: {backup_name}")
        
        try:
            # 1. Restaurer les fichiers
            files_backup_dir = backup_path / "files"
            if files_backup_dir.exists():
                for file_path in self.critical_files:
                    source = files_backup_dir / file_path
                    if source.exists():
                        dest = self.base_path / file_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        logger.info(f"  ✅ Fichier restauré: {file_path}")
            
            # 2. Restaurer les répertoires
            dirs_backup_dir = backup_path / "directories"
            if dirs_backup_dir.exists():
                for dir_path in self.critical_dirs:
                    source = dirs_backup_dir / dir_path
                    if source.exists():
                        dest = self.base_path / dir_path
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                        logger.info(f"  ✅ Répertoire restauré: {dir_path}")
            
            # 3. Restaurer les bases de données
            db_backup_dir = backup_path / "databases"
            if db_backup_dir.exists():
                for db_file in ["trendtrack.db", "trendtrack_test.db"]:
                    source_db = db_backup_dir / db_file
                    if source_db.exists():
                        dest_db = self.base_path / "data" / db_file
                        dest_db.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_db, dest_db)
                        logger.info(f"  ✅ Base de données restaurée: {db_file}")
            
            logger.info(f"✅ Restauration complète réussie: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la restauration: {e}")
            return False
    
    def create_quick_backup(self, operation_name: str) -> str:
        """
        Crée une sauvegarde rapide avant une opération
        
        Args:
            operation_name: Nom de l'opération
            
        Returns:
            str: Nom de la sauvegarde créée
        """
        timestamp = datetime.datetime.now(timezone.utc).isoformat()
        backup_name = f"quick_{operation_name}_{timestamp}"
        return self.create_backup(backup_name)
    
    def verify_backup(self, backup_name: str) -> bool:
        """
        Vérifie l'intégrité d'une sauvegarde
        
        Args:
            backup_name: Nom de la sauvegarde
            
        Returns:
            bool: True si la sauvegarde est valide
        """
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return False
        
        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            return False
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Vérifier que les fichiers existent
            files_backup_dir = backup_path / "files"
            for file_path in manifest.get('files_backed_up', []):
                if not (files_backup_dir / file_path).exists():
                    return False
            
            # Vérifier que les répertoires existent
            dirs_backup_dir = backup_path / "directories"
            for dir_path in manifest.get('directories_backed_up', []):
                if not (dirs_backup_dir / dir_path).exists():
                    return False
            
            # Vérifier que les bases de données existent
            db_backup_dir = backup_path / "databases"
            for db_file in manifest.get('databases_backed_up', []):
                if not (db_backup_dir / db_file).exists():
                    return False
            
            return True
            
        except Exception:
            return False

def main():
    """Fonction principale pour les opérations de sauvegarde/restauration"""
    import sys
    
    system = BackupRollbackSystem()
    
    if len(sys.argv) < 2:
        print("Usage: python backup_rollback_system.py <command> [args]")
        print("Commands:")
        print("  create [name]     - Créer une sauvegarde")
        print("  list             - Lister les sauvegardes")
        print("  restore <name>   - Restaurer une sauvegarde")
        print("  verify <name>    - Vérifier une sauvegarde")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        backup_path = system.create_backup(backup_name)
        print(f"✅ Sauvegarde créée: {backup_path}")
    
    elif command == "list":
        backups = system.list_backups()
        print("\n📋 Sauvegardes disponibles:")
        for backup in backups:
            print(f"  - {backup['backup_name']} ({backup['created_at']})")
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Nom de sauvegarde requis")
            return
        backup_name = sys.argv[2]
        success = system.restore_backup(backup_name, confirm=True)
        if success:
            print(f"✅ Sauvegarde restaurée: {backup_name}")
        else:
            print(f"❌ Échec de la restauration: {backup_name}")
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("❌ Nom de sauvegarde requis")
            return
        backup_name = sys.argv[2]
        is_valid = system.verify_backup(backup_name)
        if is_valid:
            print(f"✅ Sauvegarde valide: {backup_name}")
        else:
            print(f"❌ Sauvegarde invalide: {backup_name}")
    
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()

