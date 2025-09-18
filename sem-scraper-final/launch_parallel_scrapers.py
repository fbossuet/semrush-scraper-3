#!/usr/bin/env python3
"""
Script orchestrateur pour lancer les scrapers SEM en parallèle
Calcule automatiquement les ranges et lance 4 workers simultanément
"""

import subprocess
import time
import sys
import os
from datetime import datetime, timezone

def get_shops_count():
    """Récupère le nombre de boutiques avec statut vide"""
    try:
        # Importer l'API
        sys.path.append('/home/ubuntu/sem-scraper-final')
        from trendtrack_api import get_shops_count_by_status
        
        count = get_shops_count_by_status("")  # Statut vide (NULL)
        return count
    except Exception as e:
        print(f"❌ Erreur lors du comptage: {e}")
        return 0

def get_max_shop_id():
    """Récupère l'ID maximum des boutiques"""
    try:
        import sqlite3
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM shops")
        max_id = cursor.fetchone()[0]
        conn.close()
        return max_id or 0
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'ID max: {e}")
        return 0

def get_shops_with_empty_status():
    """Récupère les IDs des boutiques avec statut vide"""
    try:
        import sqlite3
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM shops WHERE scraping_status IS NULL ORDER BY id")
        shop_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return shop_ids
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des IDs: {e}")
        return []

def calculate_ranges_from_ids(shop_ids, num_workers=6):
    """Calcule les ranges d'IDs pour les workers basés sur les IDs réels"""
    if not shop_ids:
        return []
    
    # Diviser les IDs en ranges pour 6 workers
    chunk_size = len(shop_ids) // num_workers
    remainder = len(shop_ids) % num_workers
    
    ranges = []
    start_idx = 0
    
    for i in range(num_workers):
        # Ajouter un ID supplémentaire aux premiers workers si nécessaire
        current_chunk_size = chunk_size + (1 if i < remainder else 0)
        
        if current_chunk_size > 0:
            end_idx = start_idx + current_chunk_size - 1
            start_id = shop_ids[start_idx]
            end_id = shop_ids[end_idx]
            ranges.append((start_id, end_id))
            start_idx += current_chunk_size
    
    return ranges

def calculate_ranges(total_shops, num_workers=4):
    """Calcule les ranges pour chaque worker - DÉPRÉCIÉ"""
    shops_per_worker = total_shops // num_workers
    remainder = total_shops % num_workers
    
    ranges = []
    current_id = 1
    
    for i in range(num_workers):
        # Ajouter une boutique supplémentaire aux premiers workers si nécessaire
        worker_shops = shops_per_worker + (1 if i < remainder else 0)
        
        if worker_shops > 0:
            end_id = current_id + worker_shops - 1
            ranges.append((current_id, end_id))
            current_id = end_id + 1
    
    return ranges

def launch_worker(worker_id, start_id, end_id):
    """Lance un worker dans un screen séparé avec logging amélioré"""
    screen_name = f"sem-scraper-worker-{worker_id}"
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"/home/ubuntu/sem-scraper-final/logs/sem-prod-worker{worker_id}-{timestamp}.log"
    
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs("/home/ubuntu/sem-scraper-final/logs", exist_ok=True)
    
    # Commande pour lancer le worker avec logging détaillé
    cmd = f"cd /home/ubuntu/sem-scraper-final && python3 production_scraper.py --start-id {start_id} --end-id {end_id} --worker-id {worker_id}"
    
    # Lancer dans un screen avec logging complet
    screen_cmd = f"screen -dmS {screen_name} bash -c 'echo \"=== WORKER {worker_id} DÉMARRÉ À {timestamp} ===\" > {log_file}; {cmd} 2>&1 | tee -a {log_file}; echo \"=== WORKER {worker_id} TERMINÉ ===\" >> {log_file}; exec bash'"
    
    print(f"🚀 Lancement du worker {worker_id} (ID {start_id}-{end_id})...")
    print(f"   📁 Log: {log_file}")
    print(f"   🖥️  Screen: {screen_name}")
    
    result = subprocess.run(screen_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Worker {worker_id} lancé avec succès")
        return True
    else:
        print(f"❌ Erreur lors du lancement du worker {worker_id}: {result.stderr}")
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
    print("🏭 ORCHESTRATEUR DE SCRAPERS PARALLÈLES")
    print("=" * 50)
    
    # Vérifier qu'on est sur le VPS
    if not os.path.exists('/home/ubuntu'):
        print("❌ Ce script doit être exécuté sur le VPS")
        return
    
    # Récupérer les IDs des boutiques avec statut vide en temps réel
    print("📊 Calcul des statistiques en temps réel...")
    shop_ids = get_shops_with_empty_status()
    
    if not shop_ids:
        print("✅ Aucune boutique avec statut vide à traiter")
        return
    
    total_shops = len(shop_ids)
    min_id = shop_ids[0]
    max_id = shop_ids[-1]
    
    print(f"📈 Boutiques avec statut vide: {total_shops}")
    print(f"📈 ID range: {min_id} à {max_id}")
    
    if not shop_ids:
        print("❌ Aucune boutique avec statut vide trouvée")
        return
    
    print(f"📋 {len(shop_ids)} IDs récupérés (de {shop_ids[0]} à {shop_ids[-1]})")
    
    # Calculer les ranges basés sur les IDs réels
    print("\n🔧 Calcul des ranges pour 6 workers...")
    ranges = calculate_ranges_from_ids(shop_ids, 6)
    
    print("📋 Ranges calculés:")
    for i, (start_id, end_id) in enumerate(ranges, 1):
        # Compter le nombre de boutiques dans ce range
        count_in_range = len([id for id in shop_ids if start_id <= id <= end_id])
        print(f"   Worker {i}: ID {start_id}-{end_id} ({count_in_range} boutiques)")
    
    # Demander confirmation
    print(f"\n⚠️  ATTENTION: Cela va lancer 4 scrapers simultanément")
    response = input("Continuer ? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Annulé")
        return
    
    # Arrêter les scrapers existants
    print("\n🛑 Arrêt des scrapers existants...")
    subprocess.run("pkill -f production_scraper.py", shell=True)
    time.sleep(2)
    
    # Lancer les workers
    print("\n🚀 Lancement des workers...")
    for i, (start_id, end_id) in enumerate(ranges, 1):
        launch_worker(i, start_id, end_id)
        time.sleep(1)  # Petit délai entre les lancements
    
    print(f"\n✅ {len(ranges)}/{len(ranges)} workers lancés")
    
    # Afficher les sessions screen
    print("\n📊 Vérification des sessions:")
    check_screen_sessions()
    
    print("\n🎉 Orchestration terminée !")
    print("📝 Commandes utiles:")
    print("   screen -ls                    # Voir toutes les sessions")
    print("   screen -r sem-scraper-worker-1 # Attacher au worker 1")
    print("   screen -r sem-scraper-worker-2 # Attacher au worker 2")
    print("   screen -r sem-scraper-worker-3 # Attacher au worker 3")
    print("   screen -r sem-scraper-worker-4 # Attacher au worker 4")

if __name__ == "__main__":
    main()
