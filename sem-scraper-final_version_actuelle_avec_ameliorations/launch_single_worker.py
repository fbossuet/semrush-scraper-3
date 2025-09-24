#!/usr/bin/env python3
"""
Script de lancement pour le single worker
Version simplifiée sans rotation d'IP
"""

import subprocess
import time
import os
from datetime import datetime, timezone

def launch_single_worker():
    """Lance le single worker dans un screen"""
    screen_name = "single-worker"
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"/home/ubuntu/sem-scraper-final/logs/single-worker-{timestamp}.log"
    
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs("/home/ubuntu/sem-scraper-final/logs", exist_ok=True)
    
    # Commande pour lancer le worker
    cmd = f"cd /home/ubuntu/sem-scraper-final && python3 production_scraper_single.py"
    
    # Lancer dans un screen avec logging
    screen_cmd = f"screen -dmS {screen_name} bash -c 'echo \"=== SINGLE WORKER DÉMARRÉ À {timestamp} ===\" > {log_file}; {cmd} 2>&1 | tee -a {log_file}; echo \"=== SINGLE WORKER TERMINÉ ===\" >> {log_file}; exec bash'"
    
    print(f"🚀 Lancement du single worker...")
    print(f"   📁 Log: {log_file}")
    print(f"   🖥️  Screen: {screen_name}")
    
    result = subprocess.run(screen_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Single worker lancé avec succès")
        return True
    else:
        print(f"❌ Erreur lors du lancement: {result.stderr}")
        return False

def check_screen_sessions():
    """Vérifie les sessions screen actives"""
    try:
        result = subprocess.run("screen -ls", shell=True, capture_output=True, text=True)
        print("📊 Sessions screen actives:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des sessions: {e}")

def main():
    """Fonction principale"""
    print("🏭 LANCEMENT DU SINGLE WORKER")
    print("=" * 40)
    
    # Vérifier qu'on est sur le VPS
    if not os.path.exists('/home/ubuntu'):
        print("❌ Ce script doit être exécuté sur le VPS")
        return
    
    # Arrêter les workers existants
    print("🛑 Arrêt des workers existants...")
    subprocess.run("pkill -f production_scraper.py", shell=True)
    subprocess.run("pkill -f production_scraper_single.py", shell=True)
    time.sleep(2)
    
    # Lancer le single worker
    print("🚀 Lancement du single worker...")
    if launch_single_worker():
        print("✅ Single worker lancé avec succès")
    else:
        print("❌ Échec du lancement")
        return
    
    # Afficher les sessions screen
    print("\n📊 Vérification des sessions:")
    check_screen_sessions()
    
    print("\n🎉 Lancement terminé !")
    print("📝 Commandes utiles:")
    print("   screen -ls                    # Voir toutes les sessions")
    print("   screen -r single-worker       # Attacher au worker")
    print("   python3 monitor_single_worker.py  # Monitoring")

if __name__ == "__main__":
    main()
