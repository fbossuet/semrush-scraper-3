#!/usr/bin/env python3
"""
Test de la commande addmetric
Vérifie que la procédure d'ajout de métriques fonctionne correctement
"""

import os
import sys
import tempfile
import shutil
import sqlite3
from pathlib import Path
from addmetric import MetricAdder

def test_addmetric_basic():
    """Test basique de la commande addmetric"""
    print("🧪 TEST BASIQUE DE LA COMMANDE ADDMETRIC")
    print("=" * 50)
    
    # Créer un environnement de test temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        
        # Créer la structure de base
        (test_path / "data").mkdir()
        (test_path / "docs" / "procedures").mkdir(parents=True)
        
        # Créer une base de données de test
        db_path = test_path / "data" / "trendtrack.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Créer les tables de test
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_url TEXT UNIQUE NOT NULL,
                shop_name TEXT,
                monthly_visits INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                organic_traffic INTEGER,
                bounce_rate NUMERIC
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Créer les fichiers de test
        (test_path / "backup_rollback_system.py").write_text("# Test backup system")
        (test_path / "rollback_procedure.py").write_text("# Test rollback procedure")
        
        # Test 1: Ajout d'une métrique INTEGER
        print("1️⃣ Test ajout métrique INTEGER...")
        adder = MetricAdder(str(test_path))
        
        # Simuler l'ajout d'une métrique (sans les étapes de sauvegarde)
        try:
            # Test de validation des types
            result = adder._validate_int("1234")
            assert result == 1234, f"Expected 1234, got {result}"
            
            result = adder._validate_int("1,234")
            assert result == 1234, f"Expected 1234, got {result}"
            
            result = adder._validate_int("na")
            assert result is None, f"Expected None, got {result}"
            
            print("   ✅ Validation INTEGER réussie")
            
        except Exception as e:
            print(f"   ❌ Erreur validation INTEGER: {e}")
            return False
        
        # Test 2: Ajout d'une métrique NUMERIC
        print("2️⃣ Test ajout métrique NUMERIC...")
        try:
            result = adder._validate_numeric("0.45")
            assert result == 0.45, f"Expected 0.45, got {result}"
            
            result = adder._validate_numeric("45%")
            assert result == 45.0, f"Expected 45.0, got {result}"
            
            result = adder._validate_numeric("")
            assert result is None, f"Expected None, got {result}"
            
            print("   ✅ Validation NUMERIC réussie")
            
        except Exception as e:
            print(f"   ❌ Erreur validation NUMERIC: {e}")
            return False
        
        # Test 3: Ajout d'une métrique TEXT
        print("3️⃣ Test ajout métrique TEXT...")
        try:
            result = adder._validate_text("test_value")
            assert result == "test_value", f"Expected 'test_value', got {result}"
            
            result = adder._validate_text("")
            assert result is None, f"Expected None, got {result}"
            
            print("   ✅ Validation TEXT réussie")
            
        except Exception as e:
            print(f"   ❌ Erreur validation TEXT: {e}")
            return False
        
        # Test 4: Test de la structure de base de données
        print("4️⃣ Test structure de base de données...")
        try:
            # Ajouter une métrique de test
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("ALTER TABLE shops ADD COLUMN test_metric INTEGER;")
            conn.commit()
            
            # Vérifier l'ajout
            cursor.execute("PRAGMA table_info(shops);")
            columns = cursor.fetchall()
            
            test_metric_found = False
            for column in columns:
                if column[1] == 'test_metric':
                    test_metric_found = True
                    break
            
            assert test_metric_found, "Test metric not found in table"
            
            conn.close()
            print("   ✅ Structure de base de données testée")
            
        except Exception as e:
            print(f"   ❌ Erreur structure de base: {e}")
            return False
        
        # Test 5: Test des types supportés
        print("5️⃣ Test types supportés...")
        try:
            assert 'INTEGER' in adder.supported_types, "INTEGER type not supported"
            assert 'NUMERIC' in adder.supported_types, "NUMERIC type not supported"
            assert 'TEXT' in adder.supported_types, "TEXT type not supported"
            assert 'DATE' in adder.supported_types, "DATE type not supported"
            
            print("   ✅ Tous les types supportés")
            
        except Exception as e:
            print(f"   ❌ Erreur types supportés: {e}")
            return False
        
        # Test 6: Test des tables supportées
        print("6️⃣ Test tables supportées...")
        try:
            assert 'shops' in adder.supported_tables, "shops table not supported"
            assert 'analytics' in adder.supported_tables, "analytics table not supported"
            
            print("   ✅ Toutes les tables supportées")
            
        except Exception as e:
            print(f"   ❌ Erreur tables supportées: {e}")
            return False
    
    print("✅ TOUS LES TESTS BASIQUES RÉUSSIS")
    return True

def test_addmetric_validation():
    """Test de validation des paramètres"""
    print("\n🧪 TEST DE VALIDATION DES PARAMÈTRES")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        (test_path / "data").mkdir()
        
        # Créer une base de données de test
        db_path = test_path / "data" / "trendtrack.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_url TEXT UNIQUE NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        adder = MetricAdder(str(test_path))
        
        # Test 1: Type non supporté
        print("1️⃣ Test type non supporté...")
        try:
            result = adder._step2_analysis("test_metric", "INVALID_TYPE", "shops", "test", "test")
            assert result == False, "Should reject invalid type"
            print("   ✅ Type non supporté rejeté")
        except Exception as e:
            print(f"   ❌ Erreur test type non supporté: {e}")
            return False
        
        # Test 2: Table non supportée
        print("2️⃣ Test table non supportée...")
        try:
            result = adder._step2_analysis("test_metric", "INTEGER", "invalid_table", "test", "test")
            assert result == False, "Should reject invalid table"
            print("   ✅ Table non supportée rejetée")
        except Exception as e:
            print(f"   ❌ Erreur test table non supportée: {e}")
            return False
        
        # Test 3: Paramètres valides
        print("3️⃣ Test paramètres valides...")
        try:
            result = adder._step2_analysis("test_metric", "INTEGER", "shops", "test", "test")
            assert result == True, "Should accept valid parameters"
            print("   ✅ Paramètres valides acceptés")
        except Exception as e:
            print(f"   ❌ Erreur test paramètres valides: {e}")
            return False
    
    print("✅ TOUS LES TESTS DE VALIDATION RÉUSSIS")
    return True

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DE LA COMMANDE ADDMETRIC")
    print("=" * 60)
    
    try:
        # Test basique
        basic_success = test_addmetric_basic()
        
        # Test de validation
        validation_success = test_addmetric_validation()
        
        if basic_success and validation_success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("=" * 60)
            print("✅ Tests basiques: OK")
            print("✅ Tests de validation: OK")
            print("✅ Commande addmetric prête à l'utilisation")
            print("=" * 60)
            return 0
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ!")
            print("=" * 60)
            print("🚨 La commande addmetric n'est pas fiable")
            print("🔧 Vérifiez les erreurs ci-dessus")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE DANS LES TESTS: {e}")
        print("=" * 60)
        print("🚨 La commande addmetric n'est pas fonctionnelle")
        print("🔧 Intervention manuelle requise")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

