#!/usr/bin/env python3
"""
Test du système de rollback
Vérifie que la procédure de sauvegarde/restauration fonctionne correctement
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from backup_rollback_system import BackupRollbackSystem
from rollback_procedure import RollbackProcedure

def test_backup_system():
    """Test du système de sauvegarde"""
    print("🧪 TEST DU SYSTÈME DE SAUVEGARDE")
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

def test_rollback_procedure():
    """Test de la procédure de rollback"""
    print("\n🧪 TEST DE LA PROCÉDURE DE ROLLBACK")
    print("=" * 50)
    
    # Créer un environnement de test temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        
        # Créer des fichiers de test
        (test_path / "data").mkdir()
        test_file = test_path / "smart_scraper_intelligent.py"
        test_file.write_text("# Original test file\n# Original content")
        
        # Initialiser la procédure de rollback
        procedure = RollbackProcedure(str(test_path))
        
        # Test 1: Démarrer une opération
        print("1️⃣ Test démarrage d'opération...")
        backup_name = procedure.start_operation("test_operation")
        print(f"   ✅ Opération démarrée avec sauvegarde: {backup_name}")
        
        # Test 2: Modifier le fichier
        print("2️⃣ Test modification pendant opération...")
        test_file.write_text("# Modified during operation\n# New content")
        print(f"   ✅ Fichier modifié pendant l'opération")
        
        # Test 3: Rollback de l'opération
        print("3️⃣ Test rollback d'opération...")
        success = procedure.rollback_operation("Test rollback")
        print(f"   ✅ Rollback réussi: {success}")
        
        # Vérifier que le fichier est restauré
        restored_content = test_file.read_text()
        if "# Original test file" in restored_content:
            print("   ✅ Fichier correctement restauré par rollback")
        else:
            print("   ❌ Fichier non restauré correctement par rollback")
            return False
        
        # Test 4: Démarrer une nouvelle opération et la terminer
        print("4️⃣ Test opération complète...")
        backup_name = procedure.start_operation("test_complete_operation")
        test_file.write_text("# Final content\n# Operation completed")
        procedure.complete_operation("test_complete_operation")
        print(f"   ✅ Opération complétée avec succès")
    
    print("✅ TOUS LES TESTS DE ROLLBACK RÉUSSIS")
    return True

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DU SYSTÈME DE ROLLBACK")
    print("=" * 60)
    
    try:
        # Test du système de sauvegarde
        backup_success = test_backup_system()
        
        # Test de la procédure de rollback
        rollback_success = test_rollback_procedure()
        
        if backup_success and rollback_success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("=" * 60)
            print("✅ Système de sauvegarde: OK")
            print("✅ Procédure de rollback: OK")
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

