@app.get('/shops/complete')
async def get_all_shops_complete():
    """
    Récupère toutes les boutiques avec TOUTES leurs métriques (shops + analytics)
    """
    try:
        api = TrendTrackAPI()
        shops = api.get_all_shops()
        analytics = api.get_all_analytics()
        
        # Créer un dictionnaire pour faciliter la recherche des analytics par shop_id
        analytics_by_shop = {}
        for analytic in analytics:
            shop_id = analytic['shop_id']
            if shop_id not in analytics_by_shop:
                analytics_by_shop[shop_id] = []
            analytics_by_shop[shop_id].append(analytic)
        
        # Fusionner les données
        complete_data = []
        for shop in shops:
            shop_id = shop['id']
            shop_data = shop.copy()
            shop_data['analytics'] = analytics_by_shop.get(shop_id, [])
            complete_data.append(shop_data)
        
        return {
            'success': True,
            'total_shops': len(complete_data),
            'data': complete_data
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get('/shops/complete/stats')
async def get_complete_stats():
    """
    Statistiques sur les boutiques avec métriques complètes
    """
    try:
        api = TrendTrackAPI()
        shops = api.get_all_shops()
        analytics = api.get_all_analytics()
        
        # Compter les boutiques avec analytics
        shops_with_analytics = len(set(analytic['shop_id'] for analytic in analytics))
        
        # Compter les métriques par type
        metrics_count = {}
        for analytic in analytics:
            metric_type = analytic.get('metric_type', 'unknown')
            metrics_count[metric_type] = metrics_count.get(metric_type, 0) + 1
        
        return {
            'success': True,
            'total_shops': len(shops),
            'shops_with_analytics': shops_with_analytics,
            'total_analytics': len(analytics),
            'metrics_by_type': metrics_count
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
