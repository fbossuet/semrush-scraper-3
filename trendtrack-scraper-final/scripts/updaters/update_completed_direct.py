#!/usr/bin/env python3
"""
Script pour mettre à jour directement les shops avec toutes les métriques en statut "completed"
"""

import sqlite3
import requests
import json
import logging
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_completed_shops_direct():
    """Met à jour directement les shops avec toutes les métriques en statut completed"""
    
    # Récupérer les données de l'API
    try:
        response = requests.get('http://localhost:3000/api/shops/with-analytics')
        response.raise_for_status()
        data = response.json()
        shops = data['data']
        logger.info(f"📊 {len(shops)} shops récupérés de l'API")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données: {e}")
        return
    
    # Métriques principales à vérifier
    main_metrics = [
        'organic_traffic', 'bounce_rate', 'average_visit_duration',
        'branded_traffic', 'conversion_rate', 'paid_search_traffic', 'live_ads'
    ]
    
    # Identifier les shops avec toutes les métriques
    complete_shops = []
    for shop in shops:
        has_all_metrics = True
        for metric in main_metrics:
            value = shop.get(metric, '')
            if not value or value == '' or value == 'na':
                has_all_metrics = False
                break
        
        if has_all_metrics and shop.get('scraping_status') == 'partial':
            complete_shops.append(shop)
    
    logger.info(f"🎯 {len(complete_shops)} shops à mettre à jour en 'completed'")
    
    if not complete_shops:
        logger.info("✅ Aucun shop à mettre à jour")
        return
    
    # Connexion directe à la base de données
    db_path = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        for shop in complete_shops:
            shop_id = shop['id']
            try:
                # Mettre à jour le statut directement
                cursor.execute("""
                    UPDATE shops 
                    SET scraping_status = 'completed', 
                        scraping_last_update = datetime('now')
                    WHERE id = ?
                """, (shop_id,))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    logger.info(f"✅ Shop {shop_id} ({shop['domain']}) - Statut mis à jour en 'completed'")
                else:
                    logger.warning(f"⚠️ Shop {shop_id} non trouvé dans la base")
                    
            except Exception as e:
                logger.error(f"❌ Erreur shop {shop_id}: {e}")
        
        conn.commit()
        logger.info(f"🎯 RÉSULTAT: {updated_count}/{len(complete_shops)} shops mis à jour")
        
    except Exception as e:
        logger.error(f"❌ Erreur base de données: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("🚀 DÉBUT DE LA MISE À JOUR DIRECTE DES STATUTS")
    update_completed_shops_direct()
    logger.info("✅ MISE À JOUR TERMINÉE")
