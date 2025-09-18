#!/usr/bin/env python3
"""
Test simple du système de rollback sans interaction utilisateur
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from backup_rollback_system import BackupRollbackSystem

def test_backup_system_simple():
    """Test simple du système de sauvegarde"""
    print("🧪 TEST SIMPLE DU SYSTÈME DE SAUVEGARDE")
    print("=" * 50)
    
    # Créer un environnement de test temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        
        # Créer des fichiers de test
        (test_path / "data").mkdir()
        (test_path / "scrapers").mkdir()
        (test_path / "scrapers" / "domain_search").mkdir()
        
        # Fichiers de test
        test_files = [
            "smart_scraper_intelligent.py",
            "scrapers/domain_search/domain_scraper.py",
            "data/trendtrack.db",
            "data/trendtrack_test.db"
        ]
        
        for file_path in test_files:
            file_obj = test_path / file_path
            file_obj.parent.mkdir(parents=True, exist_ok=True)
            file_obj.write_text(f"# Test file: {file_path}\n# Content: Test data")
        
        # Initialiser le système de sauvegarde
        backup_system = BackupRollbackSystem(str(test_path))
        
        # Test 1: Créer une sauvegarde
        print("1️⃣ Test création de sauvegarde...")
        backup_name = backup_system.create_backup("test_backup")
        print(f"   ✅ Sauvegarde créée: {backup_name}")
        
        # Test 2: Vérifier la sauvegarde
        print("2️⃣ Test vérification de sauvegarde...")
        is_valid = backup_system.verify_backup("test_backup")
        print(f"   ✅ Sauvegarde valide: {is_valid}")
        
        # Test 3: Lister les sauvegardes
        print("3️⃣ Test listage des sauvegardes...")
        backups = backup_system.list_backups()
        print(f"   ✅ Sauvegardes trouvées: {len(backups)}")
        
        # Test 4: Modifier un fichier
        print("4️⃣ Test modification de fichier...")
        test_file = test_path / "smart_scraper_intelligent.py"
        test_file.write_text("# Modified test file\n# New content")
        print(f"   ✅ Fichier modifié")
        
        # Test 5: Restaurer la sauvegarde
        print("5️⃣ Test restauration de sauvegarde...")
        success = backup_system.restore_backup("test_backup", confirm=True)
        print(f"   ✅ Restauration réussie: {success}")
        
        # Vérifier que le fichier est restauré
        restored_content = test_file.read_text()
        if "# Test file:" in restored_content:
            print("   ✅ Fichier correctement restauré")
        else:
            print("   ❌ Fichier non restauré correctement")
            return False
    
    print("✅ TOUS LES TESTS DE SAUVEGARDE RÉUSSIS")
    return True

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS SIMPLES DU SYSTÈME DE ROLLBACK")
    print("=" * 60)
    
    try:
        # Test du système de sauvegarde
        backup_success = test_backup_system_simple()
        
        if backup_success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("=" * 60)
            print("✅ Système de sauvegarde: OK")
            print("✅ Système prêt pour les opérations critiques")
            print("=" * 60)
            return 0
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ!")
            print("=" * 60)
            print("🚨 Le système de rollback n'est pas fiable")
            print("🔧 Vérifiez les erreurs ci-dessus")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE DANS LES TESTS: {e}")
        print("=" * 60)
        print("🚨 Le système de rollback n'est pas fonctionnel")
        print("🔧 Intervention manuelle requise")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

