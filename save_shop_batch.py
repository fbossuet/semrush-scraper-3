"""
Script Python pour sauvegarder une boutique via le BatchSaver
Appelé par le système de sauvegarde incrémentale par lots
"""

import sys
import json
import sqlite3
from datetime import datetime

def save_shop_batch():
    try:
        # Récupérer les données depuis l'argument
        if len(sys.argv) < 2:
            result = {
                'status': 'error',
                'message': 'Aucune donnée fournie'
            }
            print(json.dumps(result))
            return
        
        shop_data = json.loads(sys.argv[1])
        
        # Connexion à la base de données
        db_path = 'trendtrack-scraper-final/data/trendtrack.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Requête d'insertion avec upsert
        insert_query = """
        INSERT OR REPLACE INTO shops (
            shop_name, shop_url, scraping_status, scraping_last_update, updated_at,
            creation_date, monthly_visits, monthly_revenue, live_ads, page_number,
            scraped_at, project_source, external_id, metadata, year_founded,
            total_products, pixel_google, pixel_facebook, aov,
            market_us, market_uk, market_de, market_ca, market_au, market_fr, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Préparer les valeurs
        values = (
            shop_data.get('shopName', ''),
            shop_data.get('shopUrl', ''),
            'completed',  # Status de scraping
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            shop_data.get('creationDate', ''),
            shop_data.get('monthlyVisits'),
            shop_data.get('monthlyRevenue', ''),
            shop_data.get('liveAds', ''),
            shop_data.get('page', 1),
            shop_data.get('scrapedAt', datetime.now().isoformat()),
            'trendtrack',
            None,
            json.dumps({'batch_saved': True, 'timestamp': datetime.now().isoformat()}),
            shop_data.get('yearFounded'),
            shop_data.get('totalProducts'),
            shop_data.get('pixelGoogle'),
            shop_data.get('pixelFacebook'),
            shop_data.get('aov'),
            shop_data.get('marketUs'),
            shop_data.get('marketUk'),
            shop_data.get('marketDe'),
            shop_data.get('marketCa'),
            shop_data.get('marketAu'),
            shop_data.get('marketFr'),
            shop_data.get('category', '')
        )
        
        # Exécuter l'insertion
        cursor.execute(insert_query, values)
        shop_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        result = {
            'status': 'success',
            'message': 'Boutique sauvegardée avec succès',
            'shop_id': shop_id,
            'shop_name': shop_data.get('shopName', 'Unknown')
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        result = {
            'status': 'error',
            'message': f'Erreur sauvegarde: {str(e)}'
        }
        print(json.dumps(result))
        sys.exit(1)

if __name__ == '__main__':
    save_shop_batch()
