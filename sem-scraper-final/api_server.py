#!/usr/bin/env python3
"""
API REST pour les données TrendTrack
Permet de récupérer les données avec des filtres via HTTP
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging

# Import de notre API
from trendtrack_api import TrendTrackAPI

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="TrendTrack API",
    description="""
    API pour récupérer et mettre à jour les données de scraping TrendTrack
    
    ## Endpoints GET (Lecture)
    - `/shops` - Récupérer toutes les boutiques
    - `/shops/with-analytics` - Récupérer les boutiques avec leurs métriques
    - `/shops/filter` - Récupérer les boutiques avec filtres
    - `/shops/{shop_id}` - Récupérer une boutique par ID
    - `/analytics/{shop_id}` - Récupérer les analytics d'une boutique
    - `/stats` - Statistiques générales
    
    ## Endpoints POST (Écriture - SEM-Scraper)
    - `/update-shop-analytics` - Met à jour les analytics d'une boutique
    - `/mark-shop-failed` - Marque une boutique comme échouée
    - `/record-selector-performance` - Enregistre les performances d'un sélecteur
    - `/get-selector-performances` - Récupère les performances récentes d'un sélecteur
    - `/calculate-adaptive-timeout` - Calcule un timeout adaptatif
    """,
    version="1.0.0"
)

# Ajouter CORS pour permettre les requêtes depuis n'importe où
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les endpoints POST
class AnalyticsUpdateRequest(BaseModel):
    """
    Modèle pour la mise à jour des analytics d'une boutique
    """
    shop_id: int = Field(..., description="ID de la boutique à mettre à jour")
    analytics_data: Dict[str, Any] = Field(..., description="Données analytics à sauvegarder", example={
        "organic_traffic": "1,234",
        "bounce_rate": "45.2%",
        "average_visit_duration": "2m 30s",
        "branded_traffic": "567",
        "conversion_rate": "3.2%",
        "visits": "5,678",
        "scraping_status": "completed"
    })

class ShopFailureRequest(BaseModel):
    """
    Modèle pour marquer une boutique comme échouée
    """
    shop_id: int = Field(..., description="ID de la boutique à marquer comme échouée")
    error_message: str = Field(..., description="Message d'erreur décrivant l'échec", example="Timeout lors du scraping des métriques Traffic Analysis")

class SelectorPerformanceRequest(BaseModel):
    """
    Modèle pour enregistrer les performances d'un sélecteur
    """
    selector_name: str = Field(..., description="Nom du sélecteur CSS", example="Métriques Traffic Analysis")
    success: bool = Field(..., description="Si le sélecteur a été trouvé avec succès")
    response_time_ms: int = Field(..., description="Temps de réponse en millisecondes", ge=0)
    page_load_time_ms: Optional[int] = Field(None, description="Temps de chargement de la page en ms", ge=0)

class SelectorPerformanceQuery(BaseModel):
    """
    Modèle pour récupérer les performances d'un sélecteur
    """
    selector_name: str = Field(..., description="Nom du sélecteur CSS", example="Métriques Traffic Analysis")
    limit: Optional[int] = Field(20, description="Nombre maximum de performances à récupérer", ge=1, le=100)

class AdaptiveTimeoutRequest(BaseModel):
    """
    Modèle pour calculer un timeout adaptatif
    """
    selector_name: str = Field(..., description="Nom du sélecteur CSS", example="Métriques Traffic Analysis")
    base_timeout: Optional[int] = Field(30000, description="Timeout de base en millisecondes", ge=1000, le=300000)

# Initialiser l'API TrendTrack
api = TrendTrackAPI()

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "TrendTrack API",
        "version": "1.0.0",
        "endpoints": {
            "shops": "/shops - Récupérer toutes les boutiques",
            "shops_filtered": "/shops/filter - Récupérer les boutiques avec filtres (inclut include_analytics)",
            "shop_by_id": "/shops/{shop_id} - Récupérer une boutique par ID",
            "analytics": "/analytics/{shop_id} - Récupérer les analytics d'une boutique",
            "stats": "/stats - Statistiques générales"
        }
    }

@app.get("/shops")
async def get_all_shops():
    """Récupérer toutes les boutiques"""
    try:
        shops = api.get_all_shops()
        return {
            "success": True,
            "count": len(shops),
            "data": shops
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shops/with-analytics")
async def get_all_shops_with_analytics():
    """Récupérer toutes les boutiques avec leurs métriques analytics"""
    try:
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            analytics = api.get_shop_analytics(shop.get('id'))
            if analytics:
                shop_with_analytics.update(analytics)
            shops_with_analytics.append(shop_with_analytics)
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shops/filter")
async def get_filtered_shops(
    status: Optional[str] = Query(None, description="Filtrer par status (completed, na, partial, failed)"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Nombre maximum de résultats"),
    domain: Optional[str] = Query(None, description="Filtrer par domaine"),
    include_analytics: Optional[bool] = Query(True, description="Inclure les métriques analytics (organic_traffic, bounce_rate, etc.)")
):
    """
    Récupérer les boutiques avec filtres
    
    **Paramètres disponibles :**
    - `status` : Filtrer par statut de scraping (completed, na, partial, failed)
    - `date_from` : Date de début au format YYYY-MM-DD
    - `date_to` : Date de fin au format YYYY-MM-DD
    - `limit` : Limiter le nombre de résultats
    - `domain` : Filtrer par nom de domaine
    - `include_analytics` : Si true, inclut les métriques détaillées (organic_traffic, bounce_rate, average_visit_duration, branded_traffic, conversion_rate)
    
    **Exemples d'utilisation :**
    - `/shops/filter?status=partial` : Toutes les boutiques avec statut partial
    - `/shops/filter?status=partial&include_analytics=true` : Boutiques partial avec métriques
    - `/shops/filter?status=partial&limit=5&include_analytics=true` : 5 premières boutiques partial avec métriques
    
    **Exemple de réponse sans analytics :**
    ```json
    {
      "success": true,
      "count": 1,
      "data": [
        {
          "id": 427,
          "domain": "armra.com",
          "name": "ARMRA",
          "scraping_status": "partial",
          "scraping_last_update": "2025-08-04 13:07:59"
        }
      ]
    }
    ```
    
    **Exemple de réponse avec analytics :**
    ```json
    {
      "success": true,
      "count": 1,
      "data": [
        {
          "id": 427,
          "domain": "armra.com",
          "name": "ARMRA",
          "scraping_status": "partial",
          "scraping_last_update": "2025-08-04 13:07:59",
          "organic_traffic": "Sélecteur non trouvé",
          "bounce_rate": "45.2%",
          "average_visit_duration": "2m 15s",
          "branded_traffic": "12.5k",
          "conversion_rate": "3.2%"
        }
      ]
    }
    ```
    """
    try:
        all_shops = api.get_all_shops()
        filtered_shops = []
        
        for shop in all_shops:
            # Filtre par status
            if status:
                shop_status = shop.get('scraping_status', '')
                if shop_status != status:
                    continue
            
            # Filtre par domaine
            if domain:
                shop_domain = shop.get('domain', '')
                if domain.lower() not in shop_domain.lower():
                    continue
            
            # Filtre par date
            if date_from:
                last_update = shop.get('scraping_last_update')
                if last_update:
                    try:
                        update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        from_date = datetime.strptime(date_from, '%Y-%m-%d')
                        if update_date < from_date:
                            continue
                    except Exception:
                        pass
            
            if date_to:
                last_update = shop.get('scraping_last_update')
                if last_update:
                    try:
                        update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        to_date = datetime.strptime(date_to, '%Y-%m-%d')
                        if update_date > to_date:
                            continue
                    except Exception:
                        pass
            
            # Ajouter les analytics si demandé
            if include_analytics:
                shop_with_analytics = shop.copy()
                analytics = api.get_shop_analytics(shop.get('id'))
                if analytics:
                    shop_with_analytics.update(analytics)
                else:
                    # Ajouter des champs vides si pas d'analytics
                    shop_with_analytics.update({
                        'organic_traffic': '',
                        'bounce_rate': '',
                        'avg_visit_duration': '',
                        'branded_traffic': '',
                        'conversion_rate': '',
                        'paid_search_traffic': ''
                    })
                filtered_shops.append(shop_with_analytics)
            else:
                filtered_shops.append(shop)
        
        # Limiter les résultats
        if limit:
            filtered_shops = filtered_shops[:limit]
        
        return {
            "success": True,
            "count": len(filtered_shops),
            "filters_applied": {
                "status": status,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "domain": domain,
                "include_analytics": include_analytics
            },
            "data": filtered_shops
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur filtrage boutiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shops/completed")
async def get_completed_shops(
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(30, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste paginée des boutiques ayant un status "completed" avec leurs analytics
    """
    try:
        # Récupérer toutes les boutiques et filtrer par status 'completed'
        all_shops = api.get_all_shops()
        completed_shops = [shop for shop in all_shops if shop.get('scraping_status') == 'completed']
        
        # Pagination
        total = len(completed_shops)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_shops = completed_shops[start_idx:end_idx]
        
        # Ajouter les analytics pour chaque shop
        shops_data = []
        for shop in paginated_shops:
            shop_data = {
                'shop_url': shop.get('shop_url'),
                'organic_traffic': '',
                'bounce_rate': '',
                'avg_visit_duration': '',
                'branded_traffic': '',
                'conversion_rate': ''
            }
            
            # Récupérer les analytics
            analytics = api.get_shop_analytics(shop.get('id'))
            if analytics:
                shop_data.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'avg_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', '')
                })
            
            shops_data.append(shop_data)
        
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
        logger.error(f"❌ Erreur récupération shops completed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


@app.get("/shops/url/{shop_url:path}")
async def get_shop_by_url(shop_url: str):
    """
    Récupère les informations d'une boutique spécifique par son URL
    """
    try:
        # Récupérer toutes les boutiques et chercher par URL
        all_shops = api.get_all_shops()
        target_shop = None
        
        for shop in all_shops:
            if shop.get('shop_url') == shop_url:
                target_shop = shop
                break
        
        if not target_shop:
            raise HTTPException(status_code=404, detail=f"Boutique avec URL {shop_url} non trouvée")
        
        # Vérifier le status - accepter 'completed' et 'partial'
        status = target_shop.get('scraping_status')
        if status not in ['completed', 'partial']:
            return {
                "error": f"status = {status}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': '',
            'paid_search_traffic': ''
        }
        
        analytics = api.get_shop_analytics(target_shop.get('id'))
        if analytics:
            shop_data.update({
                'organic_traffic': analytics.get('organic_traffic', ''),
                'bounce_rate': analytics.get('bounce_rate', ''),
                'avg_visit_duration': analytics.get('average_visit_duration', ''),
                'branded_traffic': analytics.get('branded_traffic', ''),
                'conversion_rate': analytics.get('conversion_rate', ''),
                'paid_search_traffic': analytics.get('paid_search_traffic', '')
            })
        
        return {
            "success": True,
            "data": shop_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération shop par URL {shop_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


@app.get("/shops/{shop_id}")
async def get_shop_by_id(shop_id: int):
    """Récupérer une boutique par ID"""
    try:
        all_shops = api.get_all_shops()
        
        for shop in all_shops:
            if shop.get('id') == shop_id:
                return {
                    "success": True,
                    "data": shop
                }
        
        raise HTTPException(status_code=404, detail=f"Boutique avec ID {shop_id} non trouvée")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutique {shop_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{shop_id}")
async def get_shop_analytics(shop_id: int):
    """
    Récupérer les analytics détaillées d'une boutique
    
    **Métriques disponibles :**
    - `organic_traffic` : Trafic organique (ex: "12.5k", "Sélecteur non trouvé")
    - `bounce_rate` : Taux de rebond (ex: "45.2%", "Sélecteur non trouvé")
    - `average_visit_duration` : Durée moyenne de visite (ex: "2m 15s", "Sélecteur non trouvé")
    - `branded_traffic` : Trafic de marque (ex: "8.3k", "Sélecteur non trouvé")
    - `conversion_rate` : Taux de conversion (ex: "3.2%", "Sélecteur non trouvé")
    - `scraping_status` : Statut du scraping (completed, partial, na, failed)
    
    **Exemple de réponse :**
    ```json
    {
      "success": true,
      "shop_id": 427,
      "data": {
        "organic_traffic": "12.5k",
        "bounce_rate": "45.2%",
        "average_visit_duration": "2m 15s",
        "branded_traffic": "8.3k",
        "conversion_rate": "3.2%",
        "scraping_status": "partial"
      }
    }
    ```
    """
    try:
        analytics = api.get_shop_analytics(shop_id)
        
        if analytics:
            return {
                "success": True,
                "shop_id": shop_id,
                "data": analytics
            }
        else:
            raise HTTPException(status_code=404, detail=f"Analytics pour la boutique {shop_id} non trouvées")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération analytics {shop_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Récupérer les statistiques générales"""
    try:
        all_shops = api.get_all_shops()
        
        # Compter par status
        status_counts = {}
        total_shops = len(all_shops)
        
        for shop in all_shops:
            status = shop.get('scraping_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_shops": total_shops,
                "status_distribution": status_counts,
                "completion_rate": (status_counts.get('completed', 0) / total_shops * 100) if total_shops > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul statistiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def transform_shop_data(shop_data):
    """
    Transforme les données d'une boutique pour l'API selon la structure finale demandée
    Applique les transformations * 100 pour les champs de pourcentage
    """
    if not shop_data:
        return shop_data
    
    # Champs à multiplier par 100 (pourcentages stockés en décimales)
    percentage_fields = ['conversion_rate', 'percent_branded_traffic', 'bounce_rate']
    
    # Créer la structure finale avec les champs dans l'ordre demandé
    final_data = {
        'id': shop_data.get('id'),
        'shop_name': shop_data.get('shop_name'),
        'shop_url': shop_data.get('shop_url'),
        'category': shop_data.get('category', 'peu importe'),  # Valeur par défaut si manquante
        'monthly_visits': shop_data.get('monthly_visits'),
        'year_founded': shop_data.get('year_founded'),
        'total_products': shop_data.get('total_products'),
        'aov': shop_data.get('aov'),
        'pixel_google': shop_data.get('pixel_google'),
        'pixel_facebook': shop_data.get('pixel_facebook'),
        'organic_traffic': shop_data.get('organic_traffic'),
        'bounce_rate': shop_data.get('bounce_rate'),
        'avg_visit_duration': shop_data.get('average_visit_duration'),  # Utiliser average_visit_duration
        'visits': shop_data.get('visits'),
        'branded_traffic': shop_data.get('branded_traffic'),
        'percent_branded_traffic': shop_data.get('percent_branded_traffic'),
        'paid_search_traffic': shop_data.get('paid_search_traffic'),
        'cpc': shop_data.get('cpc'),
        'conversion_rate': shop_data.get('conversion_rate'),
        'market_us': shop_data.get('market_us'),
        'market_uk': shop_data.get('market_uk'),
        'market_de': shop_data.get('market_de'),
        'market_ca': shop_data.get('market_ca'),
        'market_au': shop_data.get('market_au'),
                'market_fr': shop_data.get('market_fr'),
        "live_ads": shop_data.get("live_ads")  # Champ ajouté à la fin
    
    }
    # Appliquer les transformations * 100 pour les champs de pourcentage
    for field in percentage_fields:
        if field in final_data and final_data[field] is not None:
            try:
                # Convertir en float, multiplier par 100, et arrondir à 2 décimales
                original_value = float(final_data[field])
                transformed_value = round(original_value * 100, 2)
                final_data[field] = transformed_value
            except (ValueError, TypeError):
                # Si la conversion échoue, garder la valeur originale
                pass
    
    return final_data

@app.get('/test/shops/with-analytics-ordered')
async def get_test_shops_with_analytics_ordered(since: Optional[str] = Query(None, description="Date de début (ISO 8601)")):
    """
    Endpoint de TEST - Récupère toutes les boutiques avec leurs métriques analytics depuis la base de production
    Triées par qualité des données (completed > partial > na > failed)
    
    Structure de retour :
    - id, shop_name, shop_url, category
    - monthly_visits, year_founded, total_products, aov
    - pixel_google, pixel_facebook
    - organic_traffic, bounce_rate, avg_visit_duration, visits
    - branded_traffic, percent_branded_traffic, paid_search_traffic, cpc, conversion_rate
    - market_us, market_uk, market_de, market_ca, market_au, market_fr',
    """
    try:
        # Utiliser la base de production
        test_api = TrendTrackAPI()
        shops = test_api.get_all_shops()
        
        # Filtrer par date si spécifiée
        if since:
            try:
                from datetime import datetime
                since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered_shops = []
                for shop in shops:
                    last_update = shop.get('scraping_last_update')
                    if last_update:
                        try:
                            update_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                            if update_date >= since_date:
                                filtered_shops.append(shop)
                        except Exception:
                            # Si la date n'est pas valide, inclure la boutique
                            filtered_shops.append(shop)
                    else:
                        # Si pas de date, inclure la boutique
                        filtered_shops.append(shop)
                shops = filtered_shops
            except Exception as e:
                # Si erreur de parsing de date, ignorer le filtre
                pass
        
        # Récupérer les analytics pour chaque boutique
        shops_with_analytics = []
        for shop in shops:
            shop_with_analytics = shop.copy()
            analytics = test_api.get_shop_analytics(shop.get('id'))
            if analytics:
                shop_with_analytics.update(analytics)
            
            # Appliquer les transformations de données
            shop_with_analytics = transform_shop_data(shop_with_analytics)
            shops_with_analytics.append(shop_with_analytics)
        
        # Trier par qualité des données (completed > partial > na > failed)
        def sort_key(shop):
            status = shop.get('scraping_status', '')
            if status == 'completed':
                return 0
            elif status == 'partial':
                return 1
            elif status == 'na':
                return 2
            elif status == 'failed':
                return 3
            else:
                return 4
        
        shops_with_analytics.sort(key=sort_key)
        
        return {
            'success': True,
            'environment': 'PRODUCTION',
            'database': 'trendtrack.db',
            'count': len(shops_with_analytics),
            'since': since,
            'data': shops_with_analytics
        }
    except Exception as e:
        logger.error(f"❌ Erreur endpoint test: {e}")
        return {'success': False, 'error': str(e), 'environment': 'PRODUCTION'}

@app.get("/export/csv")
async def export_to_csv(
    status: Optional[str] = Query(None, description="Filtrer par status"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Nombre maximum de résultats")
):
    """Exporter les données en CSV"""
    try:
        import csv
        import io
        
        # Récupérer les données filtrées
        all_shops = api.get_all_shops()
        filtered_shops = []
        
        for shop in all_shops:
            if status and shop.get('scraping_status') != status:
                continue
            if date_from:
                last_update = shop.get('scraping_last_update')
                if last_update:
                    try:
                        update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        from_date = datetime.strptime(date_from, '%Y-%m-%d')
                        if update_date < from_date:
                            continue
                    except Exception:
                        pass
            filtered_shops.append(shop)
        
        if limit:
            filtered_shops = filtered_shops[:limit]
        
        # Créer le CSV
        output = io.StringIO()
        if filtered_shops:
            writer = csv.DictWriter(output, fieldnames=filtered_shops[0].keys())
            writer.writeheader()
            writer.writerows(filtered_shops)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            "success": True,
            "count": len(filtered_shops),
            "csv_data": csv_content
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur export CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/test-paid-traffic/{shop_id}")
async def test_paid_traffic(shop_id: int):
    """Test endpoint pour paid_search_traffic"""
    try:
        # Test direct de la méthode Python
        from trendtrack_api import api
        result = api.get_shop_analytics(shop_id)
        
        if result:
            return {
                "success": True,
                "shop_id": shop_id,
                "paid_search_traffic": result.get('paid_search_traffic'),
                "all_data": result
            }
        else:
            return {
                "success": False,
                "error": "Aucune donnée trouvée"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8001) 
@app.get("/shops/completed")
async def get_completed_shops(
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(30, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste paginée des boutiques ayant un status "completed" avec leurs analytics
    """
    try:
        # Récupérer toutes les boutiques et filtrer par status 'completed'
        all_shops = api.get_all_shops()
        completed_shops = [shop for shop in all_shops if shop.get('scraping_status') == 'completed']
        
        # Pagination
        total = len(completed_shops)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_shops = completed_shops[start_idx:end_idx]
        
        # Ajouter les analytics pour chaque shop
        shops_data = []
        for shop in paginated_shops:
            shop_data = {
                'shop_url': shop.get('shop_url'),
                'organic_traffic': '',
                'bounce_rate': '',
                'avg_visit_duration': '',
                'branded_traffic': '',
                'conversion_rate': ''
            }
            
            # Récupérer les analytics
            analytics = api.get_shop_analytics(shop.get('id'))
            if analytics:
                shop_data.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'avg_visit_duration': analytics.get('avg_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', '')
                })
            
            shops_data.append(shop_data)
        
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
        logger.error(f"❌ Erreur récupération shops completed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


@app.get("/shops/url/{shop_url:path}")
async def get_shop_by_url(shop_url: str):
    """
    Récupère les informations d'une boutique spécifique par son URL
    """
    try:
        # Récupérer toutes les boutiques et chercher par URL
        all_shops = api.get_all_shops()
        target_shop = None
        
        for shop in all_shops:
            if shop.get('shop_url') == shop_url:
                target_shop = shop
                break
        
        if not target_shop:
            raise HTTPException(status_code=404, detail=f"Boutique avec URL {shop_url} non trouvée")
        
        # Vérifier le status - accepter 'completed' et 'partial'
        status = target_shop.get('scraping_status')
        if status not in ['completed', 'partial']:
            return {
                "error": f"status = {status}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': '',
            'paid_search_traffic': ''
        }
        
        analytics = api.get_shop_analytics(target_shop.get('id'))
        if analytics:
            shop_data.update({
                'organic_traffic': analytics.get('organic_traffic', ''),
                'bounce_rate': analytics.get('bounce_rate', ''),
                'avg_visit_duration': analytics.get('avg_visit_duration', ''),
                'branded_traffic': analytics.get('branded_traffic', ''),
                'conversion_rate': analytics.get('conversion_rate', '')
            })
        
        return {
            "success": True,
            "data": shop_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération shop par URL {shop_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


# ============================================================================
# ENDPOINTS POST POUR SEM-SCRAPER-FINAL
# ============================================================================

@app.post("/update-shop-analytics")
async def update_shop_analytics_endpoint(request: AnalyticsUpdateRequest):
    """
    Met à jour les analytics d'une boutique
    
    **Utilisé par** : sem-scraper-final pour sauvegarder les données scrapées
    
    **Paramètres** :
    - `shop_id` : ID de la boutique dans la base de données
    - `analytics_data` : Dictionnaire contenant les métriques scrapées
    
    **Métriques supportées** :
    - `organic_traffic` : Trafic organique (ex: "1,234")
    - `bounce_rate` : Taux de rebond (ex: "45.2%")
    - `average_visit_duration` : Durée moyenne de visite (ex: "2m 30s")
    - `branded_traffic` : Trafic de marque (ex: "567")
    - `conversion_rate` : Taux de conversion (ex: "3.2%")
    - `visits` : Nombre de visites (ex: "5,678")
    - `scraping_status` : Statut du scraping ("completed", "partial", "failed")
    
    **Retour** :
    - `success` : Boolean indiquant le succès de l'opération
    - `message` : Message de confirmation
    - `shop_id` : ID de la boutique mise à jour
    """
    try:
        success = api.update_shop_analytics(request.shop_id, request.analytics_data)
        if success:
            return {
                "success": True,
                "message": f"Analytics mis à jour pour shop_id {request.shop_id}",
                "shop_id": request.shop_id
            }
        else:
            raise HTTPException(status_code=500, detail="Échec de la mise à jour des analytics")
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mark-shop-failed")
async def mark_shop_failed_endpoint(request: ShopFailureRequest):
    """
    Marque une boutique comme échouée
    
    **Utilisé par** : sem-scraper-final quand le scraping échoue
    
    **Paramètres** :
    - `shop_id` : ID de la boutique à marquer comme échouée
    - `error_message` : Message d'erreur décrivant la raison de l'échec
    
    **Actions effectuées** :
    - Met à jour le statut de la boutique à "failed"
    - Enregistre le message d'erreur dans la table scraping_errors
    - Met à jour la date de dernière tentative
    
    **Retour** :
    - `success` : Boolean indiquant le succès de l'opération
    - `message` : Message de confirmation
    - `shop_id` : ID de la boutique marquée comme échouée
    """
    try:
        success = api.mark_shop_failed(request.shop_id, request.error_message)
        if success:
            return {
                "success": True,
                "message": f"Boutique {request.shop_id} marquée comme échouée",
                "shop_id": request.shop_id
            }
        else:
            raise HTTPException(status_code=500, detail="Échec du marquage de la boutique")
    except Exception as e:
        logger.error(f"❌ Erreur marquage échec boutique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record-selector-performance")
async def record_selector_performance_endpoint(request: SelectorPerformanceRequest):
    """
    Enregistre les performances d'un sélecteur
    
    **Utilisé par** : sem-scraper-final pour optimiser les timeouts adaptatifs
    
    **Paramètres** :
    - `selector_name` : Nom du sélecteur CSS (ex: "Métriques Traffic Analysis")
    - `success` : Boolean indiquant si le sélecteur a été trouvé
    - `response_time_ms` : Temps de réponse en millisecondes
    - `page_load_time_ms` : Temps de chargement de la page (optionnel)
    
    **Actions effectuées** :
    - Enregistre la performance dans la table selector_performance
    - Permet de calculer les timeouts adaptatifs futurs
    - Améliore la fiabilité du scraping
    
    **Retour** :
    - `success` : Boolean indiquant le succès de l'opération
    - `message` : Message de confirmation
    - `selector_name` : Nom du sélecteur enregistré
    """
    try:
        success = api.record_selector_performance(
            request.selector_name, 
            request.success, 
            request.response_time_ms,
            request.page_load_time_ms
        )
        if success:
            return {
                "success": True,
                "message": f"Performance sélecteur '{request.selector_name}' enregistrée",
                "selector_name": request.selector_name
            }
        else:
            raise HTTPException(status_code=500, detail="Échec de l'enregistrement de la performance")
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement performance sélecteur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-selector-performances")
async def get_selector_performances_endpoint(request: SelectorPerformanceQuery):
    """
    Récupère les performances récentes d'un sélecteur
    
    **Utilisé par** : sem-scraper-final pour calculer les timeouts adaptatifs
    
    **Paramètres** :
    - `selector_name` : Nom du sélecteur CSS (ex: "Métriques Traffic Analysis")
    - `limit` : Nombre maximum de performances à récupérer (défaut: 20, max: 100)
    
    **Retour** :
    - `success` : Boolean indiquant le succès de l'opération
    - `selector_name` : Nom du sélecteur demandé
    - `count` : Nombre de performances récupérées
    - `data` : Liste des performances avec :
      - `success` : Boolean (succès/échec)
      - `response_time_ms` : Temps de réponse
      - `page_load_time_ms` : Temps de chargement de page
      - `timestamp` : Date/heure de la performance
    """
    try:
        performances = api.get_recent_selector_performances(request.selector_name, request.limit)
        return {
            "success": True,
            "selector_name": request.selector_name,
            "count": len(performances),
            "data": performances
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération performances sélecteur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-adaptive-timeout")
async def calculate_adaptive_timeout_endpoint(request: AdaptiveTimeoutRequest):
    """
    Calcule un timeout adaptatif basé sur les performances historiques
    
    **Utilisé par** : sem-scraper-final pour optimiser les temps d'attente
    
    **Paramètres** :
    - `selector_name` : Nom du sélecteur CSS (ex: "Métriques Traffic Analysis")
    - `base_timeout` : Timeout de base en millisecondes (défaut: 30000, max: 300000)
    
    **Logique de calcul** :
    - Analyse les 15 dernières performances du sélecteur
    - Calcule le taux de succès et le temps de réponse moyen
    - Ajuste le timeout selon le type de sélecteur :
      - Traffic Analysis : 45s-180s
      - Engagement metrics : 30s-120s
      - Organic Search : 25s-120s
      - Branded Traffic : 20s-90s
    
    **Retour** :
    - `success` : Boolean indiquant le succès de l'opération
    - `selector_name` : Nom du sélecteur
    - `base_timeout` : Timeout de base fourni
    - `adaptive_timeout` : Timeout calculé adaptativement
    """
    try:
        timeout = api.calculate_adaptive_timeout(request.selector_name, request.base_timeout)
        return {
            "success": True,
            "selector_name": request.selector_name,
            "base_timeout": request.base_timeout,
            "adaptive_timeout": timeout
        }
    except Exception as e:
        logger.error(f"❌ Erreur calcul timeout adaptatif: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/test-paid-traffic/{shop_id}")
async def test_paid_traffic(shop_id: int):
    """Test endpoint pour paid_search_traffic"""
    try:
        # Test direct de la méthode Python
        from trendtrack_api import api
        result = api.get_shop_analytics(shop_id)
        
        if result:
            return {
                "success": True,
                "shop_id": shop_id,
                "paid_search_traffic": result.get('paid_search_traffic'),
                "all_data": result
            }
        else:
            return {
                "success": False,
                "error": "Aucune donnée trouvée"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8001) 
@app.get("/shops/completed")
async def get_completed_shops(
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(30, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste paginée des boutiques ayant un status "completed" avec leurs analytics
    """
    try:
        # Récupérer toutes les boutiques et filtrer par status 'completed'
        all_shops = api.get_all_shops()
        completed_shops = [shop for shop in all_shops if shop.get('scraping_status') == 'completed']
        
        # Pagination
        total = len(completed_shops)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_shops = completed_shops[start_idx:end_idx]
        
        # Ajouter les analytics pour chaque shop
        shops_data = []
        for shop in paginated_shops:
            shop_data = {
                'shop_url': shop.get('shop_url'),
                'organic_traffic': '',
                'bounce_rate': '',
                'avg_visit_duration': '',
                'branded_traffic': '',
                'conversion_rate': ''
            }
            
            # Récupérer les analytics
            analytics = api.get_shop_analytics(shop.get('id'))
            if analytics:
                shop_data.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'avg_visit_duration': analytics.get('avg_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', '')
                })
            
            shops_data.append(shop_data)
        
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
        logger.error(f"❌ Erreur récupération shops completed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


@app.get("/shops/url/{shop_url:path}")
async def get_shop_by_url(shop_url: str):
    """
    Récupère les informations d'une boutique spécifique par son URL
    """
    try:
        # Récupérer toutes les boutiques et chercher par URL
        all_shops = api.get_all_shops()
        target_shop = None
        
        for shop in all_shops:
            if shop.get('shop_url') == shop_url:
                target_shop = shop
                break
        
        if not target_shop:
            raise HTTPException(status_code=404, detail=f"Boutique avec URL {shop_url} non trouvée")
        
        # Vérifier le status - accepter 'completed' et 'partial'
        status = target_shop.get('scraping_status')
        if status not in ['completed', 'partial']:
            return {
                "error": f"status = {status}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': '',
            'paid_search_traffic': ''
        }
        
        analytics = api.get_shop_analytics(target_shop.get('id'))
        if analytics:
            shop_data.update({
                'organic_traffic': analytics.get('organic_traffic', ''),
                'bounce_rate': analytics.get('bounce_rate', ''),
                'avg_visit_duration': analytics.get('avg_visit_duration', ''),
                'branded_traffic': analytics.get('branded_traffic', ''),
                'conversion_rate': analytics.get('conversion_rate', '')
            })
        
        return {
            "success": True,
            "data": shop_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération shop par URL {shop_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/test-paid-traffic/{shop_id}")
async def test_paid_traffic(shop_id: int):
    """Test endpoint pour paid_search_traffic"""
    try:
        # Test direct de la méthode Python
        from trendtrack_api import api
        result = api.get_shop_analytics(shop_id)
        
        if result:
            return {
                "success": True,
                "shop_id": shop_id,
                "paid_search_traffic": result.get('paid_search_traffic'),
                "all_data": result
            }
        else:
            return {
                "success": False,
                "error": "Aucune donnée trouvée"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)



@app.get("/analytics-complete")
async def get_all_shops_with_analytics_complete():
    """Récupérer toutes les boutiques avec leurs métriques analytics - VERSION QUI FONCTIONNE"""
    try:
        # Récupérer toutes les boutiques
        all_shops = api.get_all_shops()
        shops_with_analytics = []
        
        print(f"🔍 Traitement de {len(all_shops)} boutiques...")
        
        for shop in all_shops:
            shop_with_analytics = shop.copy()
            
            # Récupérer les analytics avec la méthode qui fonctionne
            shop_id = shop.get('id')
            analytics = api.get_shop_analytics(shop_id)
            
            if analytics:
                # Mettre à jour avec TOUTES les métriques, y compris paid_search_traffic
                shop_with_analytics.update({
                    'organic_traffic': analytics.get('organic_traffic', ''),
                    'bounce_rate': analytics.get('bounce_rate', ''),
                    'average_visit_duration': analytics.get('average_visit_duration', ''),
                    'branded_traffic': analytics.get('branded_traffic', ''),
                    'conversion_rate': analytics.get('conversion_rate', ''),
                    'paid_search_traffic': analytics.get('paid_search_traffic', ''),  # INCLUS !
                    'visits': analytics.get('visits', ''),
                    'traffic': analytics.get('traffic', ''),
                    'percent_branded_traffic': analytics.get('percent_branded_traffic', ''),
                    'scraping_status': analytics.get('scraping_status', '')
                })
            else:
                # Valeurs par défaut si pas d'analytics
                shop_with_analytics.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',  # INCLUS !
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_with_analytics.append(shop_with_analytics)
        
        print(f"✅ {len(shops_with_analytics)} boutiques traitées avec succès")
        
        return {
            "success": True,
            "count": len(shops_with_analytics),
            "data": shops_with_analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques avec analytics v2: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")




@app.get("/analytics-direct")
async def get_all_shops_with_analytics_direct():
    """Récupérer toutes les boutiques avec analytics - ACCÈS DIRECT À LA BASE"""
    try:
        import sqlite3
        from datetime import datetime
        
        # Connexion directe à la base
        import os
        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, "trendtrack-scraper-final", "data", "trendtrack.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les boutiques
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id
        """)
        
        shops_data = []
        for row in cursor.fetchall():
            shop = {
                'id': row[0],
                'name': row[1],
                'shop_url': row[2],
                'scraping_status': row[3],
                'scraping_last_update': row[4],
                'creation_date': row[5],
                'category': row[6],
                'monthly_visits': row[7],
                'monthly_revenue': row[8],
                'live_ads': row[9],
                'page_number': row[10],
                'scraped_at': row[11],
                'project_source': row[12],
                'external_id': row[13],
                'metadata': row[14],
                'updated_at': row[15]
            }
            
            # Récupérer les analytics directement
            cursor.execute("""
                SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
                       conversion_rate, paid_search_traffic, visits, traffic, 
                       percent_branded_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (shop['id'],))
            
            analytics_row = cursor.fetchone()
            if analytics_row:
                shop.update({
                    'organic_traffic': analytics_row[0] or '',
                    'bounce_rate': analytics_row[1] or '',
                    'average_visit_duration': analytics_row[2] or '',
                    'branded_traffic': analytics_row[3] or '',
                    'conversion_rate': analytics_row[4] or '',
                    'paid_search_traffic': analytics_row[5] or '',  # DIRECT !
                    'visits': analytics_row[6] or '',
                    'traffic': analytics_row[7] or '',
                    'percent_branded_traffic': analytics_row[8] or '',
                    'scraping_status': analytics_row[9] or ''
                })
            else:
                shop.update({
                    'organic_traffic': '',
                    'bounce_rate': '',
                    'average_visit_duration': '',
                    'branded_traffic': '',
                    'conversion_rate': '',
                    'paid_search_traffic': '',
                    'visits': '',
                    'traffic': '',
                    'percent_branded_traffic': '',
                    'scraping_status': ''
                })
            
            shops_data.append(shop)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(shops_data),
            "data": shops_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur accès direct base: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8001) 

@app.get("/shops/complete")
async def get_all_shops_complete():
    """Récupérer TOUTES les boutiques avec TOUTES les métriques (shops + analytics)"""
    try:
        # Récupérer toutes les boutiques de la table shops
        all_shops = api.get_all_shops()
        shops_complete = []
        
        logger.info(f"🔍 Traitement de {len(all_shops)} boutiques avec toutes les métriques...")
        
        for shop in all_shops:
            shop_complete = shop.copy()
            
            # Récupérer les métriques analytics
            analytics = api.get_shop_analytics(shop.get("id"))
            if analytics:
                shop_complete.update(analytics)
            
            shops_complete.append(shop_complete)
        
        # Trier par qualité des données (boutiques complètes en premier)
        shops_complete.sort(key=lambda x: x.get("scraping_status", ""), reverse=True)
        
        return {
            "success": True,
            "count": len(shops_complete),
            "message": f"Récupération de {len(shops_complete)} boutiques avec toutes les métriques",
            "data": shops_complete
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération boutiques complètes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shops/complete/stats")
async def get_complete_stats():
    """Statistiques complètes sur toutes les métriques disponibles"""
    try:
        all_shops = api.get_all_shops()
        
        stats = {
            "total_shops": len(all_shops),
            "metrics_breakdown": {
                "shops_table": {
                    "shop_name": len([s for s in all_shops if s.get("shop_name")]),
                    "shop_url": len([s for s in all_shops if s.get("shop_url")]),
                    "monthly_visits": len([s for s in all_shops if s.get("monthly_visits")]),
                    "monthly_revenue": len([s for s in all_shops if s.get("monthly_revenue")]),
                    "live_ads": len([s for s in all_shops if s.get("live_ads")]),
                    "creation_date": len([s for s in all_shops if s.get("creation_date")]),
                    "year_founded": len([s for s in all_shops if s.get("year_founded")]),
                    "scraping_status": len([s for s in all_shops if s.get("scraping_status")])
                },
                "analytics_table": {
                    "organic_traffic": 0,
                    "bounce_rate": 0,
                    "avg_visit_duration": 0,
                    "branded_traffic": 0,
                    "conversion_rate": 0,
                    "visits": 0,
                    "traffic": 0,
                    "percent_branded_traffic": 0,
                    "paid_search_traffic": 0
                }
            }
        }
        
        # Compter les métriques analytics
        for shop in all_shops:
            analytics = api.get_shop_analytics(shop.get("id"))
            if analytics:
                for metric in stats["metrics_breakdown"]["analytics_table"]:
                    if analytics.get(metric):
                        stats["metrics_breakdown"]["analytics_table"][metric] += 1
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul statistiques complètes: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
@app.get('/test/shops/with-analytics')
async def get_test_shops_with_analytics():
    """
    Endpoint de TEST - Récupère toutes les boutiques avec leurs métriques depuis la base de test
    """
    try:
        # Utiliser la base de test
        test_api = TrendTrackAPI("trendtrack-scraper-final/data/trendtrack_test.db")
        shops = test_api.get_all_shops()
        analytics = test_api.get_all_analytics()
        
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
            'environment': 'TEST',
            'database': 'trendtrack_test.db',
            'total_shops': len(complete_data),
            'total_analytics': len(analytics),
            'data': complete_data
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'environment': 'TEST'}

@app.get('/test/shops/stats')
async def get_test_stats():
    """
    Endpoint de TEST - Statistiques sur la base de test
    """
    try:
        test_api = TrendTrackAPI("trendtrack-scraper-final/data/trendtrack_test.db")
        shops = test_api.get_all_shops()
        analytics = test_api.get_all_analytics()
        
        # Compter les boutiques avec analytics
        shops_with_analytics = len(set(analytic['shop_id'] for analytic in analytics))
        
        # Compter les métriques par type
        metrics_count = {}
        for analytic in analytics:
            metric_type = analytic.get('metric_type', 'unknown')
            metrics_count[metric_type] = metrics_count.get(metric_type, 0) + 1
        
        return {
            'success': True,
            'environment': 'TEST',
            'database': 'trendtrack_test.db',
            'total_shops': len(shops),
            'shops_with_analytics': shops_with_analytics,
            'total_analytics': len(analytics),
            'metrics_by_type': metrics_count
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'environment': 'TEST'}
