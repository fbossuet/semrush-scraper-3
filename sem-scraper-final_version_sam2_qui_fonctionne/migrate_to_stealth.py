#!/usr/bin/env python3
"""
Script de migration vers le scraper stealth
Remplace production_scraper_parallel.py par production_scraper_stealth.py
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StealthMigrator:
    """Migrateur vers le scraper stealth"""
    
    def __init__(self):
        self.backup_dir = Path("backup")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.files_to_migrate = [
            "production_scraper_parallel.py",
            "global_bootstrap.py",
            "stealth_system.py"
        ]
        self.new_files = [
            "production_scraper_stealth.py",
            "anti_detection_config.py",
            "stealth_injections.py"
        ]
    
    def create_backup(self):
        """Crée une sauvegarde des fichiers existants"""
        try:
            logger.info("📦 Création de la sauvegarde")
            
            # Créer le dossier de sauvegarde
            backup_path = self.backup_dir / f"pre_stealth_{self.timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder les fichiers existants
            for file_name in self.files_to_migrate:
                source_path = Path(file_name)
                if source_path.exists():
                    dest_path = backup_path / file_name
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"✅ Sauvegardé: {file_name}")
                else:
                    logger.warning(f"⚠️ Fichier non trouvé: {file_name}")
            
            logger.info(f"✅ Sauvegarde créée: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erreur création sauvegarde: {e}")
            return None
    
    def verify_new_files(self):
        """Vérifie que tous les nouveaux fichiers existent"""
        try:
            logger.info("🔍 Vérification des nouveaux fichiers")
            
            missing_files = []
            for file_name in self.new_files:
                if not Path(file_name).exists():
                    missing_files.append(file_name)
                else:
                    logger.info(f"✅ Fichier trouvé: {file_name}")
            
            if missing_files:
                logger.error(f"❌ Fichiers manquants: {missing_files}")
                return False
            
            logger.info("✅ Tous les nouveaux fichiers sont présents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    def update_imports(self):
        """Met à jour les imports dans les fichiers existants"""
        try:
            logger.info("🔄 Mise à jour des imports")
            
            # Fichiers à mettre à jour
            files_to_update = [
                "menu_workers.py",
                "launch_workers_by_status_APIOK15SEPT.py"
            ]
            
            for file_name in files_to_update:
                file_path = Path(file_name)
                if file_path.exists():
                    # Lire le contenu
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Remplacer les imports
                    old_import = "from production_scraper_parallel import"
                    new_import = "from production_scraper_stealth import"
                    
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        
                        # Écrire le contenu modifié
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Imports mis à jour: {file_name}")
                    else:
                        logger.info(f"ℹ️ Aucun import à mettre à jour: {file_name}")
                else:
                    logger.warning(f"⚠️ Fichier non trouvé: {file_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour imports: {e}")
            return False
    
    def create_launch_script(self):
        """Crée un script de lancement pour le scraper stealth"""
        try:
            logger.info("🚀 Création du script de lancement")
            
            launch_script = """#!/usr/bin/env python3
'''
Script de lancement du scraper stealth
Remplace le scraper traditionnel par la version anti-détection
'''

import asyncio
import logging
import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.append(str(Path(__file__).parent))

from production_scraper_stealth import StealthScraper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stealth_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Fonction principale"""
    logger.info("🛡️ Lancement du scraper stealth")
    
    scraper = StealthScraper(worker_id=0)
    
    try:
        # Initialiser le scraper
        if not await scraper.initialize():
            logger.error("❌ Échec initialisation scraper")
            return False
        
        # Authentifier
        if not await scraper.authenticate_mytoolsplan():
            logger.error("❌ Échec authentification")
            return False
        
        logger.info("✅ Scraper stealth prêt")
        
        # Ici, vous pouvez ajouter la logique de scraping
        # Par exemple, récupérer les domaines à scraper depuis la base de données
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("🎉 Scraper stealth terminé avec succès")
    else:
        logger.error("💥 Scraper stealth échoué")
        sys.exit(1)
"""
            
            # Écrire le script
            with open("launch_stealth_scraper.py", 'w', encoding='utf-8') as f:
                f.write(launch_script)
            
            # Rendre le script exécutable
            os.chmod("launch_stealth_scraper.py", 0o755)
            
            logger.info("✅ Script de lancement créé: launch_stealth_scraper.py")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création script: {e}")
            return False
    
    def create_documentation(self):
        """Crée la documentation de migration"""
        try:
            logger.info("📚 Création de la documentation")
            
            doc_content = f"""# Migration vers le Scraper Stealth

## Date de migration: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Fichiers migrés

### Anciens fichiers (sauvegardés)
- `production_scraper_parallel.py` → `backup/pre_stealth_{self.timestamp}/`
- `global_bootstrap.py` → `backup/pre_stealth_{self.timestamp}/`
- `stealth_system.py` → `backup/pre_stealth_{self.timestamp}/`

### Nouveaux fichiers
- `production_scraper_stealth.py` - Scraper principal avec protection anti-détection
- `anti_detection_config.py` - Configuration anti-détection
- `stealth_injections.py` - Injections JavaScript pour masquer les traces
- `test_stealth_detection.py` - Tests de détection
- `launch_stealth_scraper.py` - Script de lancement

## Améliorations apportées

### 1. Protection anti-détection
- ✅ Mode headless forcé
- ✅ Arguments de navigateur anti-détection
- ✅ User-Agent rotation
- ✅ Headers de discrétion
- ✅ Injections JavaScript pour masquer les traces

### 2. Configuration avancée
- ✅ Rotation d'identité automatique
- ✅ Délais aléatoires entre requêtes
- ✅ Masquage des propriétés webdriver
- ✅ Masquage des propriétés Chrome d'automation
- ✅ Masquage des empreintes canvas/audio

### 3. Tests de détection
- ✅ Tests automatisés de détection
- ✅ Vérification des vulnérabilités
- ✅ Rapport de sécurité

## Utilisation

### Lancement du scraper stealth
```bash
python3 launch_stealth_scraper.py
```

### Tests de détection
```bash
python3 test_stealth_detection.py
```

### Configuration
Les paramètres anti-détection sont dans `anti_detection_config.py`

## Rollback

En cas de problème, vous pouvez restaurer l'ancienne version:
```bash
cp backup/pre_stealth_{self.timestamp}/production_scraper_parallel.py .
cp backup/pre_stealth_{self.timestamp}/global_bootstrap.py .
cp backup/pre_stealth_{self.timestamp}/stealth_system.py .
```

## Support

Pour toute question ou problème, consultez les logs dans `stealth_scraper.log`
"""
            
            # Écrire la documentation
            with open("STEALTH_MIGRATION.md", 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            logger.info("✅ Documentation créée: STEALTH_MIGRATION.md")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création documentation: {e}")
            return False
    
    def run_migration(self):
        """Exécute la migration complète"""
        try:
            logger.info("🚀 DÉMARRAGE DE LA MIGRATION VERS LE SCRAPER STEALTH")
            logger.info("=" * 60)
            
            # 1. Créer la sauvegarde
            backup_path = self.create_backup()
            if not backup_path:
                logger.error("❌ Échec création sauvegarde")
                return False
            
            # 2. Vérifier les nouveaux fichiers
            if not self.verify_new_files():
                logger.error("❌ Échec vérification nouveaux fichiers")
                return False
            
            # 3. Mettre à jour les imports
            if not self.update_imports():
                logger.error("❌ Échec mise à jour imports")
                return False
            
            # 4. Créer le script de lancement
            if not self.create_launch_script():
                logger.error("❌ Échec création script de lancement")
                return False
            
            # 5. Créer la documentation
            if not self.create_documentation():
                logger.error("❌ Échec création documentation")
                return False
            
            logger.info("=" * 60)
            logger.info("🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
            logger.info("=" * 60)
            logger.info("📁 Sauvegarde: {backup_path}")
            logger.info("🚀 Script de lancement: launch_stealth_scraper.py")
            logger.info("📚 Documentation: STEALTH_MIGRATION.md")
            logger.info("🧪 Tests: python3 test_stealth_detection.py")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur migration: {e}")
            return False

def main():
    """Fonction principale"""
    migrator = StealthMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration réussie!")
        print("🛡️ Votre scraper est maintenant protégé contre la détection")
        print("🚀 Utilisez: python3 launch_stealth_scraper.py")
    else:
        print("\n💥 Migration échouée!")
        print("❌ Consultez les logs pour plus de détails")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
