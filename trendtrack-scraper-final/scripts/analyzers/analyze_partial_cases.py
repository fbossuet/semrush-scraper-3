#!/usr/bin/env python3

from trendtrack_api import api

def analyze_partial_cases():
    """Analyse les cas où Organic Search Details était déjà présente"""
    try:
        shops = api.get_all_shops()
        
        print("🔍 ANALYSE DES CAS PARTIAL AVEC ORGANIC SEARCH DÉJÀ PRÉSENT")
        print("=" * 80)
        
        # Récupérer toutes les boutiques avec analytics
        all_analytics = api.get_all_shops_with_analytics()
        
        # Filtrer les boutiques partial
        partial_shops = [s for s in all_analytics if s.get("scraping_status") == "partial"]
        
        print(f"📊 Total boutiques partial: {len(partial_shops)}")
        print()
        
        # Analyser chaque boutique partial
        for i, shop in enumerate(partial_shops[:20], 1):  # Limiter à 20 pour la lisibilité
            shop_name = shop.get("shop_name", "Unknown")
            shop_url = shop.get("shop_url", "Unknown")
            
            print(f"🔄 {i:2d}. {shop_name}")
            print(f"    URL: {shop_url}")
            
            # Vérifier les métriques présentes et manquantes
            analytics = shop.get("analytics", {})
            
            # Métriques principales
            organic_traffic = analytics.get("organic_traffic", "❌ Manquant")
            bounce_rate = analytics.get("bounce_rate", "❌ Manquant")
            avg_duration = analytics.get("avg_visit_duration", "❌ Manquant")
            paid_traffic = analytics.get("paid_search_traffic", "❌ Manquant")
            
            # Métriques secondaires (souvent manquantes)
            branded_traffic = analytics.get("branded_traffic", "❌ Manquant")
            conversion_rate = analytics.get("conversion_rate", "❌ Manquant")
            visits = analytics.get("visits", "❌ Manquant")
            traffic = analytics.get("traffic", "❌ Manquant")
            
            print(f"    📊 Métriques principales:")
            print(f"       - Organic Traffic: {organic_traffic}")
            print(f"       - Bounce Rate: {bounce_rate}")
            print(f"       - Avg Duration: {avg_duration}")
            print(f"       - Paid Traffic: {paid_traffic}")
            
            print(f"    📊 Métriques secondaires:")
            print(f"       - Branded Traffic: {branded_traffic}")
            print(f"       - Conversion Rate: {conversion_rate}")
            print(f"       - Visits: {visits}")
            print(f"       - Traffic: {traffic}")
            
            # Identifier les métriques manquantes
            missing_metrics = []
            if organic_traffic == "❌ Manquant" or organic_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Organic Traffic")
            if bounce_rate == "❌ Manquant" or bounce_rate == "Sélecteur non trouvé":
                missing_metrics.append("Bounce Rate")
            if avg_duration == "❌ Manquant" or avg_duration == "Sélecteur non trouvé":
                missing_metrics.append("Avg Duration")
            if paid_traffic == "❌ Manquant" or paid_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Paid Traffic")
            if branded_traffic == "❌ Manquant" or branded_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Branded Traffic")
            if conversion_rate == "❌ Manquant" or conversion_rate == "Sélecteur non trouvé":
                missing_metrics.append("Conversion Rate")
            if visits == "❌ Manquant" or visits == "Sélecteur non trouvé":
                missing_metrics.append("Visits")
            if traffic == "❌ Manquant" or traffic == "Sélecteur non trouvé":
                missing_metrics.append("Traffic")
            
            if missing_metrics:
                print(f"    ❌ Métriques manquantes: {', '.join(missing_metrics)}")
            else:
                print(f"    ✅ Toutes les métriques sont présentes")
            
            print()
            
            if i >= 20:
                print(f"... et {len(partial_shops) - 20} autres boutiques partial")
                break
        
        # Statistiques globales
        print("📈 STATISTIQUES GLOBALES")
        print("=" * 80)
        
        # Compter les métriques manquantes par type
        missing_stats = {
            "Organic Traffic": 0,
            "Bounce Rate": 0,
            "Avg Duration": 0,
            "Paid Traffic": 0,
            "Branded Traffic": 0,
            "Conversion Rate": 0,
            "Visits": 0,
            "Traffic": 0
        }
        
        for shop in partial_shops:
            analytics = shop.get("analytics", {})
            
            if not analytics.get("organic_traffic") or analytics.get("organic_traffic") == "Sélecteur non trouvé":
                missing_stats["Organic Traffic"] += 1
            if not analytics.get("bounce_rate") or analytics.get("bounce_rate") == "Sélecteur non trouvé":
                missing_stats["Bounce Rate"] += 1
            if not analytics.get("avg_visit_duration") or analytics.get("avg_visit_duration") == "Sélecteur non trouvé":
                missing_stats["Avg Duration"] += 1
            if not analytics.get("paid_search_traffic") or analytics.get("paid_search_traffic") == "Sélecteur non trouvé":
                missing_stats["Paid Traffic"] += 1
            if not analytics.get("branded_traffic") or analytics.get("branded_traffic") == "Sélecteur non trouvé":
                missing_stats["Branded Traffic"] += 1
            if not analytics.get("conversion_rate") or analytics.get("conversion_rate") == "Sélecteur non trouvé":
                missing_stats["Conversion Rate"] += 1
            if not analytics.get("visits") or analytics.get("visits") == "Sélecteur non trouvé":
                missing_stats["Visits"] += 1
            if not analytics.get("traffic") or analytics.get("traffic") == "Sélecteur non trouvé":
                missing_stats["Traffic"] += 1
        
        print("📊 Métriques manquantes par type (sur les boutiques partial):")
        for metric, count in missing_stats.items():
            percentage = (count / len(partial_shops)) * 100
            print(f"   - {metric}: {count}/{len(partial_shops)} ({percentage:.1f}%)")
        
        return len(partial_shops)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

if __name__ == "__main__":
    analyze_partial_cases()
