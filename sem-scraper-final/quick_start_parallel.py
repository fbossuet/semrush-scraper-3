#!/usr/bin/env python3
"""
Script de démarrage rapide pour le système de workers parallèles
Interface simple pour démarrer, arrêter et surveiller les workers
"""

import asyncio
import os
import sys
import time
from pathlib import Path

def print_banner():
    """Affiche la bannière du système"""
    print("=" * 80)
    print("🏭 SYSTÈME DE WORKERS PARALLÈLES - DÉMARRAGE RAPIDE")
    print("=" * 80)
    print("🎯 Scraping MyToolsPlan avec 2 workers en parallèle")
    print("🔒 Session partagée + Même IP + Répartition équitable")
    print("=" * 80)

def check_requirements():
    """Vérifie les prérequis"""
    print("🔍 Vérification des prérequis...")
    
    # Vérifier les fichiers nécessaires
    required_files = [
        "production_scraper_parallel.py",
        "launch_parallel_workers.py",
        "monitor_parallel_workers.py",
        "test_parallel_system.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False
    
    # Vérifier les répertoires
    required_dirs = ["logs", "locks", "results"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"📁 Création du répertoire: {dir_name}")
            dir_path.mkdir(exist_ok=True)
    
    print("✅ Prérequis vérifiés")
    return True

def run_tests():
    """Lance les tests du système"""
    print("\n🧪 Lancement des tests du système...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_parallel_system.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests réussis - Le système est prêt")
            return True
        else:
            print("❌ Tests échoués:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

def start_workers():
    """Démarre les workers"""
    print("\n🚀 Démarrage des workers...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "launch_parallel_workers.py", "start"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Workers démarrés avec succès")
            return True
        else:
            print("❌ Erreur lors du démarrage:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def stop_workers():
    """Arrête les workers"""
    print("\n🛑 Arrêt des workers...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "launch_parallel_workers.py", "stop"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Workers arrêtés")
            return True
        else:
            print("❌ Erreur lors de l'arrêt:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def show_status():
    """Affiche le statut des workers"""
    print("\n📊 Statut des workers...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "launch_parallel_workers.py", "status"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def start_monitoring():
    """Lance le monitoring"""
    print("\n👁️ Lancement du monitoring...")
    print("💡 Appuyez sur Ctrl+C pour quitter le monitoring")
    
    try:
        import subprocess
        subprocess.run([sys.executable, "monitor_parallel_workers.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Monitoring arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main_menu():
    """Menu principal interactif"""
    while True:
        print("\n" + "=" * 50)
        print("🎮 MENU PRINCIPAL")
        print("=" * 50)
        print("1. 🧪 Tester le système")
        print("2. 🚀 Démarrer les workers")
        print("3. 🛑 Arrêter les workers")
        print("4. 📊 Afficher le statut")
        print("5. 👁️ Monitoring en temps réel")
        print("6. 🔄 Redémarrer les workers")
        print("7. 📖 Afficher l'aide")
        print("8. 👋 Quitter")
        print("=" * 50)
        
        try:
            choice = input("Votre choix (1-8): ").strip()
            
            if choice == "1":
                if run_tests():
                    print("✅ Système prêt à être utilisé")
                else:
                    print("❌ Veuillez corriger les erreurs avant de continuer")
            
            elif choice == "2":
                if start_workers():
                    print("✅ Workers démarrés - Vous pouvez maintenant surveiller avec l'option 5")
                else:
                    print("❌ Échec du démarrage")
            
            elif choice == "3":
                if stop_workers():
                    print("✅ Workers arrêtés")
                else:
                    print("❌ Échec de l'arrêt")
            
            elif choice == "4":
                show_status()
            
            elif choice == "5":
                start_monitoring()
            
            elif choice == "6":
                print("🔄 Redémarrage des workers...")
                if stop_workers():
                    time.sleep(2)
                    if start_workers():
                        print("✅ Workers redémarrés")
                    else:
                        print("❌ Échec du redémarrage")
                else:
                    print("❌ Échec de l'arrêt")
            
            elif choice == "7":
                show_help()
            
            elif choice == "8":
                print("👋 Au revoir!")
                break
            
            else:
                print("❌ Choix invalide, veuillez choisir entre 1 et 8")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def show_help():
    """Affiche l'aide"""
    print("\n" + "=" * 60)
    print("📖 AIDE - SYSTÈME DE WORKERS PARALLÈLES")
    print("=" * 60)
    print("🎯 OBJECTIF:")
    print("   Scraper MyToolsPlan avec 2 workers en parallèle")
    print("   Session partagée + Même IP + Répartition équitable")
    print()
    print("🚀 WORKFLOW RECOMMANDÉ:")
    print("   1. Tester le système (option 1)")
    print("   2. Démarrer les workers (option 2)")
    print("   3. Surveiller en temps réel (option 5)")
    print("   4. Arrêter quand terminé (option 3)")
    print()
    print("📊 MONITORING:")
    print("   - Statut des workers (running/stopped)")
    print("   - Utilisation CPU et mémoire")
    print("   - Boutiques traitées et erreurs")
    print("   - Logs en temps réel")
    print()
    print("🔧 DÉPANNAGE:")
    print("   - Vérifiez les logs dans logs/")
    print("   - Redémarrez si nécessaire (option 6)")
    print("   - Testez le système (option 1)")
    print()
    print("📁 FICHIERS:")
    print("   - logs/ : Logs des workers")
    print("   - locks/ : Fichiers de locks")
    print("   - results/ : Résultats du scraping")
    print("=" * 60)

def main():
    """Fonction principale"""
    print_banner()
    
    # Vérifier les prérequis
    if not check_requirements():
        print("❌ Prérequis non satisfaits")
        return
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            run_tests()
        elif command == "start":
            start_workers()
        elif command == "stop":
            stop_workers()
        elif command == "status":
            show_status()
        elif command == "monitor":
            start_monitoring()
        elif command == "restart":
            stop_workers()
            time.sleep(2)
            start_workers()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Commande inconnue: {command}")
            print("💡 Commandes disponibles: test, start, stop, status, monitor, restart, help")
    else:
        # Mode interactif
        main_menu()

if __name__ == "__main__":
    main()
