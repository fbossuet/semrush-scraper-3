#!/usr/bin/env python3
"""
Script de lancement pour le scraper intelligent
"""

import subprocess
import os
import time
from datetime import datetime, timezone

def launch_smart_scraper():
    print("🧠 LANCEMENT DU SCRAPER INTELLIGENT")
    print("=" * 50)
    
    # Arrêter les screens existants qui pourraient interférer
    print("🛑 Arrêt des screens existants...")
    subprocess.run(["screen", "-S", "smart-scraper", "-X", "quit"], 
                  capture_output=True, text=True)
    
    # Créer le nom du log avec timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"/home/ubuntu/sem-scraper-final/logs/smart-scraper-{timestamp}.log"
    
    print("🚀 Lancement du scraper intelligent...")
    
    # Lancer le scraper dans un screen
    screen_cmd = f"""
    cd /home/ubuntu/sem-scraper-final && 
    echo "=== SMART SCRAPER DÉMARRÉ À {timestamp} ===" > {log_file} && 
    python3 scrape_completed_smart.py 2>&1 | tee -a {log_file} && 
    echo "=== SMART SCRAPER TERMINÉ ===" >> {log_file}
    """
    
    subprocess.run([
        "screen", "-dmS", "smart-scraper", 
        "bash", "-c", screen_cmd
    ])
    
    print("✅ Scraper intelligent lancé avec succès")
    print(f"   📁 Log: {log_file}")
    print(f"   🖥️  Screen: smart-scraper")
    
    # Vérification des sessions
    print("\n📊 Vérification des sessions:")
    subprocess.run(["screen", "-ls"])
    
    print("\n🎉 Lancement terminé !")
    print("📝 Commandes utiles:")
    print("   screen -ls                    # Voir toutes les sessions")
    print("   screen -r smart-scraper       # Attacher au scraper")
    print("   tail -f " + log_file + "      # Suivre les logs")

if __name__ == "__main__":
    launch_smart_scraper()
