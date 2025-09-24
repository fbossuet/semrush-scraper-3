#!/usr/bin/env python3
"""
Script de lancement pour le scraper Paid Search Traffic uniquement
"""

import subprocess
import os
import time
from datetime import datetime, timezone

def launch_paid_traffic_scraper():
    """Lance le scraper Paid Search Traffic uniquement"""
    
    print("🚀 LANCEMENT SCRAPER PAID SEARCH TRAFFIC UNIQUEMENT")
    print("=" * 60)
    
    # Vérifier si un screen est déjà en cours
    result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
    if 'paid-traffic-scraper' in result.stdout:
        print("🛑 Arrêt du scraper existant...")
        subprocess.run(['screen', '-S', 'paid-traffic-scraper', '-X', 'quit'])
        time.sleep(2)
    
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    # Lancer le scraper dans un screen
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"logs/paid-traffic-scraper-{timestamp}.log"
    
    cmd = f"cd /home/ubuntu/sem-scraper-final && python3 scrape_paid_traffic_only.py"
    
    screen_cmd = [
        'screen', '-dmS', 'paid-traffic-scraper',
        '-L', '-Logfile', log_file,
        'bash', '-c', cmd
    ]
    
    subprocess.run(screen_cmd)
    
    print("✅ Scraper Paid Search Traffic lancé avec succès")
    print(f"   📁 Log: {log_file}")
    print(f"   🖥️  Screen: paid-traffic-scraper")
    
    # Vérification
    time.sleep(2)
    print("\n📊 Vérification des sessions:")
    subprocess.run(['screen', '-ls'])
    
    print("\n🎉 Lancement terminé !")
    print("📝 Commandes utiles:")
    print("   screen -ls                    # Voir toutes les sessions")
    print("   screen -r paid-traffic-scraper # Attacher au scraper")
    print(f"   tail -f {log_file}           # Suivre les logs")

if __name__ == "__main__":
    launch_paid_traffic_scraper()
