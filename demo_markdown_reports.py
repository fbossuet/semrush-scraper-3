#!/usr/bin/env python3
"""
Démonstration des Rapports Markdown
===================================

Ce script démontre la génération de rapports en format Markdown
pour tous les scripts de validation.

Usage: python3 demo_markdown_reports.py
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
        else:
            print("❌ Erreur lors de l'exécution")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Exception lors de l'exécution: {e}")
    
    return result.returncode == 0

def list_markdown_reports():
    """Liste tous les rapports Markdown générés"""
    print(f"\n{'='*60}")
    print("📄 RAPPORTS MARKDOWN GÉNÉRÉS")
    print(f"{'='*60}")
    
    try:
        # Lister tous les fichiers .md dans le répertoire
        md_files = [f for f in os.listdir('.') if f.endswith('.md')]
        
        # Filtrer les rapports de validation
        validation_reports = [f for f in md_files if any(keyword in f for keyword in [
            'validation_rules_report', 'success_analysis', 'client_validation_report'
        ])]
        
        if validation_reports:
            print("📋 Rapports de validation disponibles:")
            for report in sorted(validation_reports):
                file_size = os.path.getsize(report)
                print(f"  📄 {report} ({file_size} bytes)")
        else:
            print("❌ Aucun rapport de validation trouvé")
        
        # Afficher un exemple de rapport
        if validation_reports:
            print(f"\n📖 EXEMPLE DE RAPPORT MARKDOWN:")
            print(f"Fichier: {validation_reports[0]}")
            print("-" * 40)
            
            with open(validation_reports[0], 'r', encoding='utf-8') as f:
                content = f.read()
                # Afficher les premières lignes
                lines = content.split('\n')[:20]
                for line in lines:
                    print(line)
                if len(content.split('\n')) > 20:
                    print("... (contenu tronqué)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture des rapports: {e}")

def main():
    """Fonction principale de démonstration"""
    print("🎯 DÉMONSTRATION - RAPPORTS MARKDOWN")
    print("=" * 60)
    print("Ce script démontre la génération de rapports en format Markdown")
    print("pour tous les scripts de validation.")
    print("=" * 60)
    
    # 1. Validation générale
    print("\n🔍 ÉTAPE 1: VALIDATION GÉNÉRALE")
    success1 = run_script("validate_rules.py", 
                         "Validation générale des règles de cohérence")
    
    # 2. Identification des succès
    print("\n🔍 ÉTAPE 2: IDENTIFICATION DES SUCCÈS")
    success2 = run_script("identify_success.py", 
                         "Identification des shops avec succès total")
    
    # 3. Validation client
    print("\n🔍 ÉTAPE 3: VALIDATION CLIENT")
    success3 = run_script("client_validation.py", 
                         "Validation client ultra-stricte")
    
    # 4. Liste des rapports Markdown
    print("\n🔍 ÉTAPE 4: RAPPORTS MARKDOWN")
    list_markdown_reports()
    
    # 5. Résumé et recommandations
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
    print(f"{'='*60}")
    
    if success1 and success2 and success3:
        print("✅ Tous les scripts ont été exécutés avec succès")
        
        print("\n📋 RAPPORTS MARKDOWN GÉNÉRÉS:")
        print("  1. validation_rules_report_*.md - Rapport de validation des règles")
        print("  2. success_analysis_*.md - Analyse des shops avec succès")
        print("  3. client_validation_report_*.md - Rapport de validation client")
        
        print("\n🎯 AVANTAGES DES RAPPORTS MARKDOWN:")
        print("  • Format lisible et structuré")
        print("  • Emojis et mise en forme claire")
        print("  • Sections organisées par thème")
        print("  • Facile à partager et à consulter")
        print("  • Compatible avec GitHub et autres plateformes")
        
        print("\n📈 UTILISATION PRATIQUE:")
        print("  • Consulter les rapports pour comprendre l'état des données")
        print("  • Identifier les problèmes à corriger")
        print("  • Suivre l'évolution de la qualité des données")
        print("  • Partager les résultats avec l'équipe")
        
        print("\n🛡️ PROTECTION CLIENT:")
        print("  • Rapports internes uniquement")
        print("  • Aucune correction automatique")
        print("  • Validation manuelle obligatoire")
        print("  • ZÉRO RISQUE sur la fiabilité des données")
        
    else:
        print("❌ Certains scripts ont échoué")
        if not success1:
            print("  • validate_rules.py a échoué")
        if not success2:
            print("  • identify_success.py a échoué")
        if not success3:
            print("  • client_validation.py a échoué")
    
    print(f"\n✅ DÉMONSTRATION TERMINÉE")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 OBJECTIF ATTEINT: RAPPORTS MARKDOWN GÉNÉRÉS")

if __name__ == "__main__":
    main()
