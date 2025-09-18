#!/usr/bin/env python3
"""
Lanceur rapide et simple des workers parallèles
Interface simple pour lancer les workers selon le statut
"""

import asyncio
import sys
from launch_workers_by_status import WorkersByStatusLauncher, setup_logging

def print_banner():
    """Affiche la bannière"""
    print("🏭 LANCEUR RAPIDE WORKERS PARALLÈLES")
    print("=" * 50)
    print("🎯 Lancez les workers selon le statut des boutiques")
    print("=" * 50)

def show_menu():
    """Affiche le menu interactif"""
    print("\n📋 MENU PRINCIPAL:")
    print("1. 🆕 Boutiques vides (sans statut)")
    print("2. ⚠️ Boutiques partial (à compléter)")
    print("3. ❌ Boutiques failed (à retraiter)")
    print("4. 🌐 Toutes les boutiques éligibles")
    print("5. 📖 Aide")
    print("6. 👋 Quitter")

def get_user_choice():
    """Récupère le choix de l'utilisateur"""
    while True:
        try:
            choice = input("\nVotre choix (1-6): ").strip()
            if choice in ["1", "2", "3", "4", "5", "6"]:
                return choice
            else:
                print("❌ Choix invalide, veuillez choisir entre 1 et 6")
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            return "6"

def get_worker_config():
    """Récupère la configuration des workers"""
    print("\n⚙️ CONFIGURATION DES WORKERS:")
    
    # Nombre de workers
    while True:
        try:
            num_workers = input("👷 Nombre de workers (défaut: 2): ").strip()
            if not num_workers:
                num_workers = 2
            else:
                num_workers = int(num_workers)
                if num_workers < 1 or num_workers > 4:
                    print("❌ Nombre de workers doit être entre 1 et 4")
                    continue
            break
        except ValueError:
            print("❌ Nombre invalide")
    
    # Max boutiques par worker
    while True:
        try:
            max_per_worker = input("🔢 Max boutiques par worker (défaut: illimité): ").strip()
            if not max_per_worker:
                max_per_worker = None
            else:
                max_per_worker = int(max_per_worker)
                if max_per_worker < 1:
                    print("❌ Nombre doit être positif")
                    continue
            break
        except ValueError:
            print("❌ Nombre invalide")
    
    return num_workers, max_per_worker

async def launch_workers_interactive():
    """Lance les workers en mode interactif"""
    print_banner()
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == "6":
            print("👋 Au revoir!")
            break
        elif choice == "5":
            show_help()
            continue
        
        # Mapper le choix au statut
        status_map = {
            "1": "empty",
            "2": "partial", 
            "3": "failed",
            "4": "all"
        }
        
        status = status_map[choice]
        status_names = {
            "empty": "boutiques vides",
            "partial": "boutiques partial",
            "failed": "boutiques failed",
            "all": "toutes les boutiques éligibles"
        }
        
        print(f"\n🎯 Vous avez choisi: {status_names[status]}")
        
        # Configuration des workers
        num_workers, max_per_worker = get_worker_config()
        
        # Confirmation
        print(f"\n📋 RÉCAPITULATIF:")
        print(f"🎯 Statut: {status_names[status]}")
        print(f"👷 Workers: {num_workers}")
        if max_per_worker:
            print(f"🔢 Max par worker: {max_per_worker}")
        else:
            print("🔢 Max par worker: illimité")
        
        confirm = input("\n✅ Confirmer le lancement? (o/N): ").strip().lower()
        if confirm not in ["o", "oui", "y", "yes"]:
            print("❌ Lancement annulé")
            continue
        
        # Lancer les workers
        print(f"\n🚀 LANCEMENT DES WORKERS...")
        launcher = WorkersByStatusLauncher(status, num_workers, max_per_worker)
        success = await launcher.launch_workers()
        
        if success:
            print("\n🎉 LANCEMENT TERMINÉ AVEC SUCCÈS!")
        else:
            print("\n⚠️ LANCEMENT TERMINÉ AVEC DES ERREURS")
        
        # Proposer de relancer
        restart = input("\n🔄 Voulez-vous lancer un autre traitement? (o/N): ").strip().lower()
        if restart not in ["o", "oui", "y", "yes"]:
            print("👋 Au revoir!")
            break

def show_help():
    """Affiche l'aide"""
    print("\n📖 AIDE - LANCEUR RAPIDE WORKERS PARALLÈLES")
    print("=" * 60)
    print("🎯 OBJECTIF:")
    print("   Lancer les workers parallèles selon le statut des boutiques")
    print()
    print("📊 STATUTS DISPONIBLES:")
    print("   🆕 Empty   - Boutiques sans statut ou statut vide")
    print("   ⚠️ Partial - Boutiques avec statut 'partial' (à compléter)")
    print("   ❌ Failed  - Boutiques avec statut 'failed' (à retraiter)")
    print("   🌐 All     - Toutes les boutiques éligibles")
    print()
    print("⚙️ CONFIGURATION:")
    print("   👷 Workers - Nombre de workers parallèles (1-4)")
    print("   🔢 Max par worker - Limite le nombre de boutiques par worker")
    print()
    print("💡 CONSEILS:")
    print("   - Commencez par 'partial' pour tester")
    print("   - Utilisez 2 workers pour commencer")
    print("   - Limitez le nombre pour les tests")
    print("   - Surveillez les logs en temps réel")
    print()
    print("📁 FICHIERS GÉNÉRÉS:")
    print("   - distribution_*.json - Distribution des boutiques")
    print("   - results_*.json - Résultats du traitement")
    print("=" * 60)

def main():
    """Fonction principale"""
    setup_logging()
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            show_help()
            return
        else:
            print("❌ Arguments non supportés en mode interactif")
            print("💡 Utilisez 'python3 launch_workers_by_status.py' pour les arguments")
            return
    
    # Mode interactif
    try:
        asyncio.run(launch_workers_interactive())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
