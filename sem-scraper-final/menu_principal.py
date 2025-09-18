#!/usr/bin/env python3
"""
Menu principal TrendTrack - Interface utilisateur
"""

import os
import sys
import subprocess
from pathlib import Path

def clear_screen():
    """Effacer l'écran"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_menu():
    """Afficher le menu principal"""
    print("=" * 80)
    print("🏪 TRENDTRACK - MENU PRINCIPAL")
    print("=" * 80)
    print()
    print("📋 OPTIONS DISPONIBLES:")
    print()
    print("   1. 📥 Import SEM")
    print("   2. 🔍 Vérifier le statut des boutiques")
    print("   3. 🚀 Lancer le scraper")
    print("   4. 📊 Voir les statistiques")
    print("   5. 🔧 Maintenance base de données")
    print("   6. 📁 Gestion des fichiers")
    print("   7. ❌ Quitter")
    print()
    print("=" * 80)

def run_import_sem():
    """Lancer le script d'import SEM"""
    print("📥 Lancement de l'import SEM...")
    try:
        subprocess.run([sys.executable, "import_sem.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
    except FileNotFoundError:
        print("❌ Script import_sem.py non trouvé")
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def check_shop_status():
    """Vérifier le statut des boutiques"""
    print("🔍 Vérification du statut des boutiques...")
    try:
        subprocess.run([sys.executable, "check_empty_status.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
    except FileNotFoundError:
        print("❌ Script check_empty_status.py non trouvé")
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def launch_scraper():
    """Lancer le scraper"""
    print("🚀 Lancement du scraper...")
    print("⚠️ Attention: Cette opération peut prendre du temps")
    confirm = input("Êtes-vous sûr de vouloir continuer? (y/N): ").strip().lower()
    
    if confirm == 'y':
        try:
            subprocess.run([sys.executable, "production_scraper.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'exécution: {e}")
        except FileNotFoundError:
            print("❌ Script production_scraper.py non trouvé")
    else:
        print("❌ Lancement annulé")
    
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def show_statistics():
    """Afficher les statistiques"""
    print("📊 Statistiques du système...")
    try:
        # Vérifier la taille de la base de données
        db_path = "/home/ubuntu/sem-scraper-final/data/trendtrack.db"
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            print(f"📁 Taille base de données: {size_mb:.2f} MB")
        else:
            print("❌ Base de données non trouvée")
        
        # Vérifier les fichiers d'import
        imports_dir = "/home/ubuntu/sem-scraper-final/imports"
        if os.path.exists(imports_dir):
            csv_files = [f for f in os.listdir(imports_dir) if f.endswith('.csv')]
            print(f"📥 Fichiers d'import disponibles: {len(csv_files)}")
        else:
            print("📁 Répertoire imports non créé")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def database_maintenance():
    """Maintenance de la base de données"""
    print("🔧 Maintenance de la base de données...")
    print("⚠️ Fonctionnalité en développement")
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def file_management():
    """Gestion des fichiers"""
    print("📁 Gestion des fichiers...")
    print("⚠️ Fonctionnalité en développement")
    input("\n⏸️ Appuyez sur Entrée pour continuer...")

def main():
    """Fonction principale du menu"""
    while True:
        clear_screen()
        show_menu()
        
        try:
            choice = input("🎯 Choisissez une option (1-7): ").strip()
            
            if choice == '1':
                run_import_sem()
            elif choice == '2':
                check_shop_status()
            elif choice == '3':
                launch_scraper()
            elif choice == '4':
                show_statistics()
            elif choice == '5':
                database_maintenance()
            elif choice == '6':
                file_management()
            elif choice == '7':
                print("👋 Au revoir!")
                break
            else:
                print("❌ Option invalide. Choisissez entre 1 et 7.")
                input("\n⏸️ Appuyez sur Entrée pour continuer...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            input("\n⏸️ Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()
