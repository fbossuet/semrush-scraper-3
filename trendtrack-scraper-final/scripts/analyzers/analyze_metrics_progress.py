#!/usr/bin/env python3

from trendtrack_api import api

def analyze_metrics_progress():
    """Analyse précise des métriques avant/après le scraping"""
    try:
        print("🔍 ANALYSE PRÉCISE DES MÉTRIQUES - AVANT/APRÈS SCRAPING")
        print("=" * 80)
        
        # Récupérer toutes les boutiques avec analytics
        all_analytics = api.get_all_shops_with_analytics()
        
        # Filtrer les boutiques partial
        partial_shops = [s for s in all_analytics if s.get("scraping_status") == "partial"]
        
        print(f"📊 Total boutiques partial: {len(partial_shops)}")
        print()
        
        # Analyser les 10 premières boutiques partial en détail
        for i, shop in enumerate(partial_shops[:10], 1):
            shop_name = shop.get("shop_name", "Unknown")
            shop_url = shop.get("shop_url", "Unknown")
            
            print(f"🔄 {i:2d}. {shop_name}")
            print(f"    URL: {shop_url}")
            
            analytics = shop.get("analytics", {})
            
            # Métriques principales (celles que le scraper unifié récupère)
            print(f"    📊 MÉTRIQUES PRINCIPALES:")
            
            organic_traffic = analytics.get("organic_traffic", "❌ Manquant")
            bounce_rate = analytics.get("bounce_rate", "❌ Manquant")
            avg_duration = analytics.get("avg_visit_duration", "❌ Manquant")
            paid_traffic = analytics.get("paid_search_traffic", "❌ Manquant")
            
            print(f"       - Organic Traffic: {organic_traffic}")
            print(f"       - Bounce Rate: {bounce_rate}")
            print(f"       - Avg Duration: {avg_duration}")
            print(f"       - Paid Traffic: {paid_traffic}")
            
            # Métriques secondaires (souvent manquantes)
            print(f"    📊 MÉTRIQUES SECONDAIRES:")
            
            branded_traffic = analytics.get("branded_traffic", "❌ Manquant")
            conversion_rate = analytics.get("conversion_rate", "❌ Manquant")
            visits = analytics.get("visits", "❌ Manquant")
            traffic = analytics.get("traffic", "❌ Manquant")
            
            print(f"       - Branded Traffic: {branded_traffic}")
            print(f"       - Conversion Rate: {conversion_rate}")
            print(f"       - Visits: {visits}")
            print(f"       - Traffic: {traffic}")
            
            # Compter les métriques présentes vs manquantes
            metrics_present = 0
            metrics_missing = 0
            
            for metric_value in [organic_traffic, bounce_rate, avg_duration, paid_traffic, 
                               branded_traffic, conversion_rate, visits, traffic]:
                if metric_value and metric_value != "❌ Manquant" and metric_value != "Sélecteur non trouvé":
                    metrics_present += 1
                else:
                    metrics_missing += 1
            
            print(f"    📈 RÉSUMÉ: {metrics_present}/8 métriques présentes, {metrics_missing}/8 manquantes")
            
            # Identifier spécifiquement ce qui manque
            missing_metrics = []
            if not organic_traffic or organic_traffic == "❌ Manquant" or organic_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Organic Traffic")
            if not bounce_rate or bounce_rate == "❌ Manquant" or bounce_rate == "Sélecteur non trouvé":
                missing_metrics.append("Bounce Rate")
            if not avg_duration or avg_duration == "❌ Manquant" or avg_duration == "Sélecteur non trouvé":
                missing_metrics.append("Avg Duration")
            if not paid_traffic or paid_traffic == "❌ Manquant" or paid_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Paid Traffic")
            if not branded_traffic or branded_traffic == "❌ Manquant" or branded_traffic == "Sélecteur non trouvé":
                missing_metrics.append("Branded Traffic")
            if not conversion_rate or conversion_rate == "❌ Manquant" or conversion_rate == "Sélecteur non trouvé":
                missing_metrics.append("Conversion Rate")
            if not visits or visits == "❌ Manquant" or visits == "Sélecteur non trouvé":
                missing_metrics.append("Visits")
            if not traffic or traffic == "❌ Manquant" or traffic == "Sélecteur non trouvé":
                missing_metrics.append("Traffic")
            
            if missing_metrics:
                print(f"    ❌ MANQUE ENCORE: {', '.join(missing_metrics)}")
            else:
                print(f"    ✅ TOUTES LES MÉTRIQUES SONT PRÉSENTES")
            
            print()
        
        # Statistiques globales sur les métriques
        print("📈 STATISTIQUES GLOBALES DES MÉTRIQUES")
        print("=" * 80)
        
        total_metrics = len(partial_shops) * 8  # 8 métriques par boutique
        present_metrics = 0
        missing_metrics = 0
        
        metric_stats = {
            "Organic Traffic": {"present": 0, "missing": 0},
            "Bounce Rate": {"present": 0, "missing": 0},
            "Avg Duration": {"present": 0, "missing": 0},
            "Paid Traffic": {"present": 0, "missing": 0},
            "Branded Traffic": {"present": 0, "missing": 0},
            "Conversion Rate": {"present": 0, "missing": 0},
            "Visits": {"present": 0, "missing": 0},
            "Traffic": {"present": 0, "missing": 0}
        }
        
        for shop in partial_shops:
            analytics = shop.get("analytics", {})
            
            # Vérifier chaque métrique
            metrics_to_check = [
                ("organic_traffic", "Organic Traffic"),
                ("bounce_rate", "Bounce Rate"),
                ("avg_visit_duration", "Avg Duration"),
                ("paid_search_traffic", "Paid Traffic"),
                ("branded_traffic", "Branded Traffic"),
                ("conversion_rate", "Conversion Rate"),
                ("visits", "Visits"),
                ("traffic", "Traffic")
            ]
            
            for db_field, metric_name in metrics_to_check:
                value = analytics.get(db_field)
                if value and value != "Sélecteur non trouvé":
                    metric_stats[metric_name]["present"] += 1
                    present_metrics += 1
                else:
                    metric_stats[metric_name]["missing"] += 1
                    missing_metrics += 1
        
        print(f"📊 TOTAL MÉTRIQUES: {total_metrics}")
        print(f"✅ PRÉSENTES: {present_metrics} ({present_metrics/total_metrics*100:.1f}%)")
        print(f"❌ MANQUANTES: {missing_metrics} ({missing_metrics/total_metrics*100:.1f}%)")
        print()
        
        print("📊 DÉTAIL PAR TYPE DE MÉTRIQUE:")
        for metric_name, stats in metric_stats.items():
            present = stats["present"]
            missing = stats["missing"]
            total = present + missing
            percentage = (present / total) * 100 if total > 0 else 0
            print(f"   - {metric_name}: {present}/{total} ({percentage:.1f}%)")
        
        return len(partial_shops)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

if __name__ == "__main__":
    analyze_metrics_progress()
