#!/usr/bin/env python3
"""
Script de Démonstration des Outils de Validation
================================================

Ce script démontre l'utilisation des deux outils de validation :
1. validate_rules.py - Validation des règles de cohérence
2. identify_success.py - Identification des shops avec succès total

Usage: python3 demo_validation.py
"""

import subprocess
import sys
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
        else:
            print("❌ Erreur lors de l'exécution")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Exception lors de l'exécution: {e}")
    
    return result.returncode == 0

def main():
    """Fonction principale de démonstration"""
    print("🎯 DÉMONSTRATION DES OUTILS DE VALIDATION")
    print("=" * 60)
    print("Ce script démontre l'utilisation des outils de validation")
    print("pour analyser la cohérence des données et identifier les succès.")
    print("=" * 60)
    
    # 1. Validation des règles
    print("\n🔍 ÉTAPE 1: VALIDATION DES RÈGLES DE COHÉRENCE")
    success1 = run_script("validate_rules.py", 
                         "Validation des règles de cohérence entre tables shops et analytics")
    
    # 2. Identification des succès
    print("\n🔍 ÉTAPE 2: IDENTIFICATION DES SHOPS AVEC SUCCÈS TOTAL")
    success2 = run_script("identify_success.py", 
                         "Identification des shops scrapées avec succès total")
    
    # 3. Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
    print(f"{'='*60}")
    
    if success1 and success2:
        print("✅ Tous les scripts ont été exécutés avec succès")
        print("\n📋 FONCTIONNALITÉS DÉMONTRÉES:")
        print("  • Validation des statuts et formats des données")
        print("  • Vérification de la cohérence entre tables")
        print("  • Identification des shops avec succès total")
        print("  • Génération de rapports détaillés")
        print("  • Export des résultats vers fichiers")
        
        print("\n📄 FICHIERS GÉNÉRÉS:")
        print("  • success_analysis_*.txt - Rapport d'analyse des succès")
        
        print("\n🎯 UTILISATION PRATIQUE:")
        print("  • validate_rules.py - Vérifier la qualité des données")
        print("  • identify_success.py - Identifier les shops prêtes pour production")
        print("  • Utiliser ces scripts dans des pipelines CI/CD")
        print("  • Monitoring automatique de la qualité des données")
        
    else:
        print("❌ Certains scripts ont échoué")
        if not success1:
            print("  • validate_rules.py a échoué")
        if not success2:
            print("  • identify_success.py a échoué")
    
    print(f"\n✅ DÉMONSTRATION TERMINÉE")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
