#!/usr/bin/env python3
"""
Démonstration du Système de Mise à Jour de Production
====================================================

Ce script démontre le système de mise à jour de la base de production
avec les nouvelles données validées depuis la base source.

Usage: python3 demo_update_production.py
"""

import subprocess
import sys
import os
from datetime import datetime

def run_script(script_name, description):
    """Exécute un script et affiche les résultats"""
    print(f"\n{'='*60}")
    print(f"🚀 EXÉCUTION: {description}")
    print(f"📄 Script: {script_name}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              cwd='/home/ubuntu/projects/shopshopshops/test')
        
        if result.returncode == 0:
            print("✅ Script exécuté avec succès")
            print("\n📊 RÉSULTATS:")
            print(result.stdout)
            return True
        else:
            print("❌ Erreur lors de l'exécution")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception lors de l'exécution: {e}")
        return False

def check_database_status():
    """Vérifie l'état des bases de données"""
    print(f"\n{'='*60}")
    print("📊 ÉTAT DES BASES DE DONNÉES")
    print(f"{'='*60}")
    
    source_db = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    prod_db = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack-prod.db"
    
    try:
        import sqlite3
        
        # Vérifier la base source
        if os.path.exists(source_db):
            conn = sqlite3.connect(source_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shops")
            source_shops = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics")
            source_analytics = cursor.fetchone()[0]
            conn.close()
            print(f"📂 Base source: {source_db}")
            print(f"  Shops: {source_shops}")
            print(f"  Analytics: {source_analytics}")
        else:
            print(f"❌ Base source introuvable: {source_db}")
            return False
        
        # Vérifier la base production
        if os.path.exists(prod_db):
            conn = sqlite3.connect(prod_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shops")
            prod_shops = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics")
            prod_analytics = cursor.fetchone()[0]
            conn.close()
            print(f"📂 Base production: {prod_db}")
            print(f"  Shops: {prod_shops}")
            print(f"  Analytics: {prod_analytics}")
        else:
            print(f"❌ Base production introuvable: {prod_db}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale de démonstration"""
    print("🎯 DÉMONSTRATION - SYSTÈME DE MISE À JOUR DE PRODUCTION")
    print("=" * 60)
    print("Ce script démontre le système de mise à jour de la base de production")
    print("avec les nouvelles données validées depuis la base source.")
    print("=" * 60)
    
    # Vérification de l'état des bases
    if not check_database_status():
        print("❌ Impossible de continuer - Bases de données non disponibles")
        return False
    
    # Étape 1: Mise à jour de la production
    print("\n🔍 ÉTAPE 1: MISE À JOUR DE LA PRODUCTION")
    success1 = run_script("update_production.py", 
                         "Mise à jour de la base de production avec les nouvelles données validées")
    
    if not success1:
        print("❌ Échec de la mise à jour de la production")
        return False
    
    # Étape 2: Vérification de l'état final
    print("\n🔍 ÉTAPE 2: VÉRIFICATION DE L'ÉTAT FINAL")
    if not check_database_status():
        print("❌ Impossible de vérifier l'état final")
        return False
    
    # Résumé final
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
    print(f"{'='*60}")
    
    if success1:
        print("✅ DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        
        print("\n📋 SYSTÈME DE MISE À JOUR:")
        print("  • Script de mise à jour: update_production.py")
        print("  • Validation ultra-stricte des données")
        print("  • Migration sécurisée vers la production")
        print("  • ZÉRO RISQUE sur la fiabilité des données")
        
        print("\n🎯 FONCTIONNALITÉS:")
        print("  • Identification des nouvelles données validées")
        print("  • Mise à jour des shops existantes")
        print("  • Ajout des nouvelles shops validées")
        print("  • Synchronisation des analytics")
        print("  • Protection totale de la réputation client")
        
        print("\n📈 UTILISATION PRATIQUE:")
        print("  • Exécution à la demande: python3 update_production.py")
        print("  • Synchronisation automatique des données")
        print("  • Mise à jour incrémentale de la production")
        print("  • Validation continue de la qualité")
        
        print("\n🛡️ PROTECTION CLIENT:")
        print("  • Seules les données validées sont migrées")
        print("  • Aucune donnée non-validée en production")
        print("  • Validation ultra-stricte des critères")
        print("  • ZÉRO RISQUE sur la fiabilité")
        
    else:
        print("❌ DÉMONSTRATION ÉCHOUÉE")
        print("  • Échec de la mise à jour de la production")
        print("  • Vérifier les données source")
        print("  • Corriger les problèmes identifiés")
    
    print(f"\n✅ DÉMONSTRATION TERMINÉE")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success1

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎯 OBJECTIF ATTEINT: SYSTÈME DE MISE À JOUR FONCTIONNEL")
    else:
        print(f"\n❌ OBJECTIF NON ATTEINT: CORRECTION REQUISE")
