#!/usr/bin/env python3
"""
API REST pour les données TrendTrack
Permet de récupérer les données avec des filtres via HTTP
"""

from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime, timezone
import logging
import subprocess
import asyncio

# Import de notre API
from trendtrack_api import TrendTrackAPI, get_database_path

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
api = TrendTrackAPI(get_database_path())

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
                    except:
                        pass
            
            if date_to:
                last_update = shop.get('scraping_last_update')
                if last_update:
                    try:
                        update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        to_date = datetime.strptime(date_to, '%Y-%m-%d')
                        if update_date > to_date:
                            continue
                    except:
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
                        'conversion_rate': ''
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
                    except:
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

if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
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


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
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


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
#!/usr/bin/env python3
"""
API REST pour les données TrendTrack
Permet de récupérer les données avec des filtres via HTTP
"""

from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime, timezone
import logging
import subprocess
import asyncio

# Import de notre API
from trendtrack_api import TrendTrackAPI, get_database_path

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
api = TrendTrackAPI(get_database_path())

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
                    except:
                        pass
            
            if date_to:
                last_update = shop.get('scraping_last_update')
                if last_update:
                    try:
                        update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        to_date = datetime.strptime(date_to, '%Y-%m-%d')
                        if update_date > to_date:
                            continue
                    except:
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
                        'conversion_rate': ''
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
        
        # Vérifier le status
        if target_shop.get('scraping_status') != 'completed':
            return {
                "error": f"status = {target_shop.get('scraping_status')}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': ''
        }
        
        analytics = api.get_shop_analytics(target_shop.get('id'))
        if analytics:
            shop_data.update({
                'organic_traffic': analytics.get('organic_traffic', ''),
                'bounce_rate': analytics.get('bounce_rate', ''),
                'avg_visit_duration': analytics.get('average_visit_duration', ''),
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
                    except:
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

if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
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
        
        # Vérifier le status
        if target_shop.get('scraping_status') != 'completed':
            return {
                "error": f"status = {target_shop.get('scraping_status')}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': ''
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


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
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
        
        # Vérifier le status
        if target_shop.get('scraping_status') != 'completed':
            return {
                "error": f"status = {target_shop.get('scraping_status')}"
            }
        
        # Récupérer les analytics
        shop_data = {
            'shop_url': target_shop.get('shop_url'),
            'organic_traffic': '',
            'bounce_rate': '',
            'avg_visit_duration': '',
            'branded_traffic': '',
            'conversion_rate': ''
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


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")


if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'API TrendTrack")
    uvicorn.run(app, host="0.0.0.0", port=8000) 