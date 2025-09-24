# Nouveaux endpoints FastAPI pour l'API TrendTrack

@app.get("/shops/completed")
async def get_completed_shops(
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(30, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste paginée des boutiques ayant un status "completed" avec leurs analytics
    """
    try:
        offset = (page - 1) * limit
        
        # Récupérer les shops avec status 'completed' et leurs analytics
        query = """
            SELECT s.shop_url, a.organic_traffic, a.bounce_rate, a.avg_visit_duration, 
                   a.branded_traffic, a.conversion_rate
            FROM shops s
            LEFT JOIN analytics a ON s.id = a.shop_id
            WHERE s.scraping_status = 'completed'
            ORDER BY s.id DESC
            LIMIT ? OFFSET ?
        """
        
        shops = api.db.execute(query, (limit, offset)).fetchall()
        
        # Récupérer le total pour la pagination
        total_query = "SELECT COUNT(*) as total FROM shops WHERE scraping_status = 'completed'"
        total = api.db.execute(total_query).fetchone()['total']
        
        # Convertir en liste de dictionnaires
        shops_data = []
        for shop in shops:
            shops_data.append({
                'shop_url': shop['shop_url'],
                'organic_traffic': shop['organic_traffic'],
                'bounce_rate': shop['bounce_rate'],
                'avg_visit_duration': shop['avg_visit_duration'],
                'branded_traffic': shop['branded_traffic'],
                'conversion_rate': shop['conversion_rate']
            })
        
        return {
            "success": True,
            "data": shops_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logging.error(f"❌ Erreur récupération shops completed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

@app.get("/shops/url/{shop_url:path}")
async def get_shop_by_url(shop_url: str):
    """
    Récupère les détails d'une boutique par son URL. 
    Retourne une erreur si le status n'est pas "completed"
    """
    try:
        # Récupérer le shop et vérifier son status
        query = """
            SELECT s.shop_url, s.scraping_status, a.organic_traffic, a.bounce_rate, 
                   a.avg_visit_duration, a.branded_traffic, a.conversion_rate
            FROM shops s
            LEFT JOIN analytics a ON s.id = a.shop_id
            WHERE s.shop_url = ?
        """
        
        shop = api.db.execute(query, (shop_url,)).fetchone()
        
        if not shop:
            raise HTTPException(status_code=404, detail="Shop non trouvé")
        
        if shop['scraping_status'] != 'completed':
            return {
                "success": False,
                "error": f"status = {shop['scraping_status']}"
            }
        
        # Retourner les données sans le scraping_status
        shop_data = {
            'shop_url': shop['shop_url'],
            'organic_traffic': shop['organic_traffic'],
            'bounce_rate': shop['bounce_rate'],
            'avg_visit_duration': shop['avg_visit_duration'],
            'branded_traffic': shop['branded_traffic'],
            'conversion_rate': shop['conversion_rate']
        }
        
        return {
            "success": True,
            "data": shop_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Erreur récupération shop spécifique: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")
