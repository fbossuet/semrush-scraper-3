#!/usr/bin/env python3
"""
Analyse rapide des boutiques avec métriques manquantes
"""

from trendtrack_api import api

def quick_analysis():
    """Analyse rapide des métriques manquantes"""
    print("🔍 ANALYSE RAPIDE DES MÉTRIQUES MANQUANTES")
    print("=" * 60)
    
    try:
        # Récupérer toutes les boutiques avec analytics
        all_shops = api.get_all_shops_with_analytics()
        print(f"📊 Total des boutiques: {len(all_shops)}")
        
        # Analyser les métriques manquantes
        shops_with_missing = []
        missing_metrics_count = {}
        
        required_metrics = [
            'organic_traffic', 'bounce_rate', 'avg_visit_duration',
            'branded_traffic', 'conversion_rate', 'paid_search_traffic'
        ]
        
        for shop in all_shops:
            missing_in_shop = []
            
            for metric in required_metrics:
                metric_value = shop.get(metric)
                
                if (metric_value is None or 
                    metric_value == "" or 
                    metric_value == "na" or
                    "Sélecteur non trouvé" in str(metric_value) or
                    "Erreur" in str(metric_value)):
                    missing_in_shop.append(metric)
                    
                    if metric not in missing_metrics_count:
                        missing_metrics_count[metric] = 0
                    missing_metrics_count[metric] += 1
            
            if missing_in_shop:
                shops_with_missing.append({
                    'id': shop['id'],
                    'name': shop['shop_name'],
                    'missing_metrics': missing_in_shop,
                    'status': shop.get('scraping_status', 'unknown')
                })
        
        # Afficher les résultats
        print(f"\n📝 Boutiques avec métriques manquantes: {len(shops_with_missing)}")
        print(f"✅ Boutiques complètes: {len(all_shops) - len(shops_with_missing)}")
        
        if missing_metrics_count:
            print(f"\n🔍 Métriques manquantes par type:")
            for metric, count in sorted(missing_metrics_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   {metric}: {count} boutiques")
        
        if shops_with_missing:
            print(f"\n📋 Exemples de boutiques avec métriques manquantes:")
            for i, shop in enumerate(shops_with_missing[:5], 1):
                print(f"   {i}. {shop['name']} (ID: {shop['id']})")
                print(f"      Statut: {shop['status']}")
                print(f"      Métriques manquantes: {', '.join(shop['missing_metrics'])}")
                print()
        
        # Statistiques par statut
        status_count = {}
        for shop in all_shops:
            status = shop.get('scraping_status', 'unknown')
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        print(f"📊 Répartition par statut:")
        for status, count in sorted(status_count.items()):
            print(f"   {status}: {count} boutiques")
        
        print(f"\n🎯 RECOMMANDATION:")
        if shops_with_missing:
            print(f"   Le scraper intelligent peut traiter {len(shops_with_missing)} boutiques")
            print(f"   pour améliorer la qualité des données.")
        else:
            print(f"   Toutes les boutiques ont des métriques complètes !")
        
        return shops_with_missing
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    quick_analysis()
