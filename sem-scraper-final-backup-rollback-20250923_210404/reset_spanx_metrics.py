#!/usr/bin/env python3
"""
Script pour supprimer les métriques Paid Search Traffic et Organic Search Traffic pour spanx.com
"""

from trendtrack_api import TrendTrackAPI

def main():
    api = TrendTrackAPI()
    
    # Récupérer tous les shops et trouver spanx.com
    shops = api.get_all_shops()
    shop = None
    for s in shops:
        if s.get('shop_name') == 'spanx.com':
            shop = s
            break
    
    if not shop:
        print("❌ Shop spanx.com non trouvé")
        return
    
    print(f"✅ Shop trouvé: ID {shop['id']}")
    
    # Récupérer les analytics actuels
    analytics = api.get_shop_analytics(shop['id'])
    if not analytics:
        print("❌ Aucune donnée analytics trouvée")
        return
    
    print(f"📊 Valeurs actuelles:")
    print(f"   Organic Search Traffic: {analytics.get('organic_search_traffic', 'N/A')}")
    print(f"   Paid Search Traffic: {analytics.get('paid_search_traffic', 'N/A')}")
    
    # Mettre à jour en supprimant ces métriques (mettre à None)
    update_data = {
        'organic_search_traffic': None,
        'paid_search_traffic': None
    }
    
    # Mettre à jour la base de données
    success = api.update_shop_analytics(shop['id'], update_data)
    
    if success:
        print("✅ Métriques supprimées avec succès")
        
        # Vérifier la mise à jour
        updated_analytics = api.get_shop_analytics(shop['id'])
        print(f"📊 Nouvelles valeurs:")
        print(f"   Organic Search Traffic: {updated_analytics.get('organic_search_traffic', 'N/A')}")
        print(f"   Paid Search Traffic: {updated_analytics.get('paid_search_traffic', 'N/A')}")
    else:
        print("❌ Erreur lors de la suppression des métriques")

if __name__ == "__main__":
    main()
