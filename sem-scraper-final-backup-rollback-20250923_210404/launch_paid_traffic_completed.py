#!/usr/bin/env python3
"""
Script de lancement pour scraper le Paid Search Traffic sur toutes les boutiques completed
"""

import subprocess
import os
import time
from datetime import datetime, timezone

def launch_paid_traffic_completed():
    """Lance le scraper Paid Search Traffic sur les boutiques completed"""
    
    print("🚀 LANCEMENT SCRAPER PAID SEARCH TRAFFIC - BOUTIQUES COMPLETED")
    print("=" * 70)
    
    # Vérifier si un screen est déjà en cours
    result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
    if 'paid-traffic-completed' in result.stdout:
        print("🛑 Arrêt du scraper existant...")
        subprocess.run(['screen', '-S', 'paid-traffic-completed', '-X', 'quit'])
        time.sleep(2)
    
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    # Lancer le scraper dans un screen
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"logs/paid-traffic-completed-{timestamp}.log"
    
    cmd = f"cd /home/ubuntu/sem-scraper-final && python3 scrape_paid_traffic_only.py"
    
    screen_cmd = [
        'screen', '-dmS', 'paid-traffic-completed',
        '-L', '-Logfile', log_file,
        'bash', '-c', cmd
    ]
    
    subprocess.run(screen_cmd)
    
    print("✅ Scraper Paid Search Traffic (completed) lancé avec succès")
    print(f"   📁 Log: {log_file}")
    print(f"   🖥️  Screen: paid-traffic-completed")
    
    # Vérification
    time.sleep(2)
    print("\n📊 Vérification des sessions:")
    subprocess.run(['screen', '-ls'])
    
    print("\n🎉 Lancement terminé !")
    print("📝 Commandes utiles:")
    print("   screen -ls                    # Voir toutes les sessions")
    print("   screen -r paid-traffic-completed # Attacher au scraper")
    print(f"   tail -f {log_file}           # Suivre les logs")
    print("   python3 check_paid_traffic_status.py  # Vérifier le progrès")

if __name__ == "__main__":
    launch_paid_traffic_completed()
