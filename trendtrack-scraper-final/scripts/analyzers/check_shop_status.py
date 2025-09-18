#!/usr/bin/env python3

from trendtrack_api import api

def check_shop_status():
    try:
        shops = api.get_all_shops()
        
        # Compter par statut
        partial = [s for s in shops if s.get("scraping_status") == "partial"]
        completed = [s for s in shops if s.get("scraping_status") == "completed"]
        empty = [s for s in shops if s.get("scraping_status") == "empty"]
        failed = [s for s in shops if s.get("scraping_status") == "failed"]
        
        print("📊 STATUT ACTUEL DES BOUTIQUES:")
        print("=" * 50)
        print(f"   Partial: {len(partial)}")
        print(f"   Completed: {len(completed)}")
        print(f"   Empty: {len(empty)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Total: {len(shops)}")
        
        print("\n🔍 DERNIÈRES BOUTIQUES COMPLETED:")
        print("=" * 50)
        if completed:
            for i, shop in enumerate(completed[-10:], 1):
                print(f"   {i:2d}. ✅ {shop['shop_name']} ({shop['shop_url']})")
        else:
            print("   Aucune boutique completed")
            
        print("\n⚠️  BOUTIQUES PARTIAL RESTANTES:")
        print("=" * 50)
        if partial:
            for i, shop in enumerate(partial[:10], 1):
                print(f"   {i:2d}. 🔄 {shop['shop_name']} ({shop['shop_url']})")
            if len(partial) > 10:
                print(f"   ... et {len(partial) - 10} autres")
        else:
            print("   Aucune boutique partial")
            
        return len(partial), len(completed)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0, 0

if __name__ == "__main__":
    check_shop_status()
