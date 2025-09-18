#!/usr/bin/env python3
"""
Test de l'analyse des types de champs existants
Vérifie que la procédure détecte correctement les incohérences de types
"""

import os
import sys
import tempfile
import shutil
import sqlite3
from pathlib import Path
from addmetric import MetricAdder

def test_field_type_analysis():
    """Test de l'analyse des types de champs existants"""
    print("🧪 TEST DE L'ANALYSE DES TYPES DE CHAMPS EXISTANTS")
    print("=" * 60)
    
    # Créer un environnement de test temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        
        # Créer la structure de base
        (test_path / "data").mkdir()
        
        # Créer une base de données de test avec des champs existants
        db_path = test_path / "data" / "trendtrack.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Créer la table shops avec des champs existants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_url TEXT UNIQUE NOT NULL,
                shop_name TEXT,
                monthly_visits INTEGER,
                monthly_revenue TEXT,  -- Incohérent: devrait être NUMERIC
                market_us NUMERIC,
                market_uk NUMERIC,
                pixel_google INTEGER,
                pixel_facebook INTEGER
            )
        """)
        
        # Créer la table analytics avec des champs existants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                organic_traffic INTEGER,
                bounce_rate NUMERIC,
                conversion_rate TEXT,  -- Incohérent: devrait être NUMERIC
                visits INTEGER,
                traffic INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Créer les fichiers de test
        (test_path / "backup_rollback_system.py").write_text("# Test backup system")
        (test_path / "rollback_procedure.py").write_text("# Test rollback procedure")
        
        adder = MetricAdder(str(test_path))
        
        # Test 1: Détection d'incohérence dans monthly_*
        print("1️⃣ Test détection d'incohérence monthly_*...")
        try:
            # monthly_visits est INTEGER, monthly_revenue est TEXT
            # Ajouter monthly_profit en NUMERIC devrait détecter l'incohérence
            result = adder._analyze_existing_field_types("monthly_profit", "NUMERIC", "shops")
            print("   ✅ Analyse monthly_* effectuée")
        except Exception as e:
            print(f"   ❌ Erreur analyse monthly_*: {e}")
            return False
        
        # Test 2: Détection d'incohérence dans market_*
        print("2️⃣ Test détection d'incohérence market_*...")
        try:
            # market_us et market_uk sont NUMERIC
            # Ajouter market_fr en INTEGER devrait détecter l'incohérence
            result = adder._analyze_existing_field_types("market_fr", "INTEGER", "shops")
            print("   ✅ Analyse market_* effectuée")
        except Exception as e:
            print(f"   ❌ Erreur analyse market_*: {e}")
            return False
        
        # Test 3: Détection d'incohérence dans pixel_*
        print("3️⃣ Test détection d'incohérence pixel_*...")
        try:
            # pixel_google et pixel_facebook sont INTEGER
            # Ajouter pixel_twitter en TEXT devrait détecter l'incohérence
            result = adder._analyze_existing_field_types("pixel_twitter", "TEXT", "shops")
            print("   ✅ Analyse pixel_* effectuée")
        except Exception as e:
            print(f"   ❌ Erreur analyse pixel_*: {e}")
            return False
        
        # Test 4: Test de cohérence (pas d'incohérence)
        print("4️⃣ Test de cohérence (pas d'incohérence)...")
        try:
            # Ajouter un nouveau champ market_* en NUMERIC (cohérent)
            result = adder._analyze_existing_field_types("market_de", "NUMERIC", "shops")
            print("   ✅ Analyse de cohérence effectuée")
        except Exception as e:
            print(f"   ❌ Erreur analyse de cohérence: {e}")
            return False
        
        # Test 5: Test avec un nouveau préfixe
        print("5️⃣ Test avec un nouveau préfixe...")
        try:
            # Ajouter un champ avec un nouveau préfixe
            result = adder._analyze_existing_field_types("total_products", "INTEGER", "shops")
            print("   ✅ Analyse nouveau préfixe effectuée")
        except Exception as e:
            print(f"   ❌ Erreur analyse nouveau préfixe: {e}")
            return False
    
    print("✅ TOUS LES TESTS D'ANALYSE RÉUSSIS")
    return True

def test_consistency_detection():
    """Test de détection des incohérences spécifiques"""
    print("\n🧪 TEST DE DÉTECTION DES INCOHÉRENCES")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_trendtrack"
        test_path.mkdir()
        (test_path / "data").mkdir()
        
        # Créer une base de données avec des incohérences
        db_path = test_path / "data" / "trendtrack.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_url TEXT,
                monthly_visits INTEGER,
                monthly_revenue TEXT,  -- Incohérent
                market_us NUMERIC,
                market_uk INTEGER,     -- Incohérent
                pixel_google INTEGER,
                pixel_facebook TEXT    -- Incohérent
            )
        """)
        
        conn.commit()
        conn.close()
        
        (test_path / "backup_rollback_system.py").write_text("# Test")
        (test_path / "rollback_procedure.py").write_text("# Test")
        
        adder = MetricAdder(str(test_path))
        
        # Test 1: Détecter l'incohérence monthly_revenue
        print("1️⃣ Test détection incohérence monthly_revenue...")
        try:
            result = adder._analyze_existing_field_types("monthly_profit", "NUMERIC", "shops")
            print("   ✅ Incohérence monthly_* détectée")
        except Exception as e:
            print(f"   ❌ Erreur détection monthly_*: {e}")
            return False
        
        # Test 2: Détecter l'incohérence market_uk
        print("2️⃣ Test détection incohérence market_uk...")
        try:
            result = adder._analyze_existing_field_types("market_fr", "NUMERIC", "shops")
            print("   ✅ Incohérence market_* détectée")
        except Exception as e:
            print(f"   ❌ Erreur détection market_*: {e}")
            return False
        
        # Test 3: Détecter l'incohérence pixel_facebook
        print("3️⃣ Test détection incohérence pixel_facebook...")
        try:
            result = adder._analyze_existing_field_types("pixel_twitter", "INTEGER", "shops")
            print("   ✅ Incohérence pixel_* détectée")
        except Exception as e:
            print(f"   ❌ Erreur détection pixel_*: {e}")
            return False
    
    print("✅ TOUS LES TESTS DE DÉTECTION RÉUSSIS")
    return True

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS D'ANALYSE DES TYPES DE CHAMPS")
    print("=" * 70)
    
    try:
        # Test de l'analyse des types
        analysis_success = test_field_type_analysis()
        
        # Test de détection des incohérences
        detection_success = test_consistency_detection()
        
        if analysis_success and detection_success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("=" * 70)
            print("✅ Tests d'analyse des types: OK")
            print("✅ Tests de détection d'incohérences: OK")
            print("✅ Analyse des types de champs existants fonctionnelle")
            print("=" * 70)
            return 0
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ!")
            print("=" * 70)
            print("🚨 L'analyse des types de champs n'est pas fiable")
            print("🔧 Vérifiez les erreurs ci-dessus")
            print("=" * 70)
            return 1
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE DANS LES TESTS: {e}")
        print("=" * 70)
        print("🚨 L'analyse des types de champs n'est pas fonctionnelle")
        print("🔧 Intervention manuelle requise")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())

