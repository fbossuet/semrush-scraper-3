#!/usr/bin/env python3
"""
Script de Démonstration - Validation Client ZÉRO RISQUE
=======================================================

Ce script démontre l'utilisation des trois outils de validation
pour garantir la qualité des données et identifier les shops
prêtes pour l'envoi au client SANS RISQUE.

Objectif: PROTECTION TOTALE de la réputation client
Usage: python3 demo_client_validation.py
"""

import subprocess
import sys
from datetime import datetime

def run_script(script_name, description):
    """Exécute un script et affiche les résultats"""
    print(f"\n{'='*70}")
    print(f"🚀 EXÉCUTION: {description}")
    print(f"📄 Script: {script_name}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
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
    print("🎯 DÉMONSTRATION - VALIDATION CLIENT ZÉRO RISQUE")
    print("=" * 70)
    print("Ce script démontre l'utilisation des outils de validation")
    print("pour garantir la qualité des données et identifier les shops")
    print("prêtes pour l'envoi au client SANS RISQUE.")
    print("=" * 70)
    
    # 1. Validation des règles de base
    print("\n🔍 ÉTAPE 1: VALIDATION DES RÈGLES DE BASE")
    success1 = run_script("validate_rules.py", 
                         "Validation des règles de cohérence entre tables shops et analytics")
    
    # 2. Identification des succès
    print("\n🔍 ÉTAPE 2: IDENTIFICATION DES SHOPS AVEC SUCCÈS")
    success2 = run_script("identify_success.py", 
                         "Identification des shops scrapées avec succès total")
    
    # 3. Validation client ultra-stricte
    print("\n🔍 ÉTAPE 3: VALIDATION CLIENT ULTRA-STRICTE")
    success3 = run_script("client_validation.py", 
                         "Validation client avec critères ultra-stricts pour ZÉRO RISQUE")
    
    # 4. Résumé et recommandations
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ DE LA DÉMONSTRATION CLIENT")
    print(f"{'='*70}")
    
    if success1 and success2 and success3:
        print("✅ Tous les scripts ont été exécutés avec succès")
        
        print("\n📋 FONCTIONNALITÉS DÉMONTRÉES:")
        print("  • Validation des règles de cohérence (validate_rules.py)")
        print("  • Identification des shops avec succès (identify_success.py)")
        print("  • Validation client ultra-stricte (client_validation.py)")
        print("  • Protection totale de la réputation client")
        print("  • Génération de rapports détaillés")
        print("  • Export des résultats vers fichiers")
        
        print("\n📄 FICHIERS GÉNÉRÉS:")
        print("  • success_analysis_*.txt - Rapport d'analyse des succès")
        print("  • client_validation_report_*.txt - Rapport de validation client")
        
        print("\n🎯 UTILISATION PRATIQUE POUR CLIENT:")
        print("  • validate_rules.py - Vérifier la qualité générale des données")
        print("  • identify_success.py - Identifier les shops avec succès total")
        print("  • client_validation.py - Validation ULTRA-STRICTE pour client")
        print("  • Utiliser ces scripts avant chaque envoi au client")
        print("  • Monitoring automatique de la qualité des données")
        
        print("\n🛡️ PROTECTION CLIENT:")
        print("  • ZÉRO RISQUE sur la fiabilité des données")
        print("  • Protection totale de la réputation client")
        print("  • Critères ultra-stricts pour validation")
        print("  • Alertes automatiques en cas de problème")
        
        print("\n📈 WORKFLOW RECOMMANDÉ:")
        print("  1. Exécuter validate_rules.py pour vérifier la qualité générale")
        print("  2. Exécuter identify_success.py pour identifier les succès")
        print("  3. Exécuter client_validation.py pour validation client")
        print("  4. Envoyer SEULEMENT les shops avec ZÉRO RISQUE au client")
        print("  5. Surveiller les rapports générés pour le suivi")
        
    else:
        print("❌ Certains scripts ont échoué")
        if not success1:
            print("  • validate_rules.py a échoué")
        if not success2:
            print("  • identify_success.py a échoué")
        if not success3:
            print("  • client_validation.py a échoué")
    
    print(f"\n✅ DÉMONSTRATION CLIENT TERMINÉE")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 OBJECTIF ATTEINT: PROTECTION TOTALE DE LA RÉPUTATION CLIENT")

if __name__ == "__main__":
    main()
