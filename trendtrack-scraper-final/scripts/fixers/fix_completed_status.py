#!/usr/bin/env python3
"""
Script pour corriger le statut des shops qui ont toutes les métriques
et les marquer en "completed" au lieu de "partial"
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_completed_status():
    """Corrige le statut des shops avec toutes les métriques"""
    
    # Connexion à la base de données
    conn = sqlite3.connect('../trendtrack-scraper-final/data/trendtrack.db')
    cursor = conn.cursor()
    
    # Récupérer tous les shops avec leurs analytics
    cursor.execute("""
        SELECT s.id, s.shop_name, s.shop_url, s.scraping_status,
               a.organic_traffic, a.bounce_rate, a.avg_visit_duration,
               a.branded_traffic, a.conversion_rate, a.paid_search_traffic, s.live_ads
        FROM shops s
        LEFT JOIN analytics a ON s.id = a.shop_id
        WHERE s.scraping_status = 'partial'
    """)
    
    shops = cursor.fetchall()
    logger.info(f"📊 {len(shops)} shops avec statut 'partial' trouvés")
    
    # Métriques principales à vérifier
    main_metrics = [
        'organic_traffic', 'bounce_rate', 'average_visit_duration',
        'branded_traffic', 'conversion_rate', 'paid_search_traffic', 'live_ads'
    ]
    
    completed_count = 0
    updated_shops = []
    
    for shop in shops:
        shop_id, shop_name, shop_url, status, organic_traffic, bounce_rate, avg_duration, branded_traffic, conversion_rate, paid_traffic, live_ads = shop
        
        # Vérifier si toutes les métriques principales sont présentes
        metrics_values = [organic_traffic, bounce_rate, avg_duration, branded_traffic, conversion_rate, paid_traffic, live_ads]
        
        has_all_metrics = True
        for value in metrics_values:
            if not value or value == '' or value == 'na':
                has_all_metrics = False
                break
        
        if has_all_metrics:
            # Mettre à jour le statut en "completed"
            cursor.execute("""
                UPDATE shops 
                SET scraping_status = 'completed', 
                    scraping_last_update = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), shop_id))
            
            completed_count += 1
            updated_shops.append({
                'id': shop_id,
                'name': shop_name,
                'url': shop_url
            })
            
            logger.info(f"✅ Shop {shop_id} ({shop_url}) - Statut mis à jour en 'completed'")
    
    # Valider les changements
    conn.commit()
    conn.close()
    
    logger.info(f"🎯 RÉSULTAT: {completed_count} shops mis à jour en 'completed'")
    
    if updated_shops:
        logger.info("📋 SHOPS MIS À JOUR:")
        for i, shop in enumerate(updated_shops[:10]):  # Afficher les 10 premiers
            logger.info(f"  {i+1}. ID: {shop['id']}, URL: {shop['url']}")
        
        if len(updated_shops) > 10:
            logger.info(f"  ... et {len(updated_shops) - 10} autres")

if __name__ == "__main__":
    logger.info("🚀 DÉBUT DE LA CORRECTION DES STATUTS")
    fix_completed_status()
    logger.info("✅ CORRECTION TERMINÉE")
