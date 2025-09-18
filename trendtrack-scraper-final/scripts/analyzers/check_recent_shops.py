#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/trendtrack-scraper-final')

from trendtrack_api import api

def check_recent_shops():
    """Vérifie le statut des boutiques récemment traitées par le scraper intelligent"""
    
    # Boutiques récemment traitées selon les logs
    recent_shops = [
        "spanx.com", "shopbala.com", "ridge.com", "archiesfootwear.com",
        "blendjet.com", "gruns.co", "brighton.com", "silksilky.com",
        "meritbeauty.com", "saltandstone.com", "justaddbuoy.com",
        "jonesroadbeauty.com", "earthbreeze.com", "blackgirlvitamins.co"
    ]
    
    print("🔍 VÉRIFICATION DES BOUTIQUES RÉCEMMENT TRAITÉES:")
    print("=" * 60)
    
    # Récupérer toutes les boutiques
    shops = api.get_all_shops()
    
    # Vérifier le statut de chaque boutique récente
    for shop_url in recent_shops:
        shop = next((s for s in shops if s.get("shop_url") == shop_url), None)
        if shop:
            status = shop.get("scraping_status", "N/A")
            print(f"   {shop_url}: {status}")
        else:
            print(f"   {shop_url}: N/A (non trouvée)")
    
    print("\n📊 STATUT GLOBAL:")
    partial = [s for s in shops if s.get("scraping_status") == "partial"]
    completed = [s for s in shops if s.get("scraping_status") == "completed"]
    print(f"   🔄 Partial: {len(partial)} boutiques")
    print(f"   ✅ Completed: {len(completed)} boutiques")
    print(f"   📝 Total: {len(shops)} boutiques")

if __name__ == "__main__":
    check_recent_shops()
