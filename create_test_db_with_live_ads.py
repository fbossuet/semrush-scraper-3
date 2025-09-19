#!/usr/bin/env python3
"""
Création d'une base de données de test avec les nouvelles colonnes live_ads_7d et live_ads_30d
"""

import sqlite3
import os
from datetime import datetime

def create_test_database_with_live_ads():
    """Crée une base de données de test avec les nouvelles colonnes"""
    db_path = "test_trendtrack_with_live_ads.db"
    
    # Supprimer la base existante si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Créer la table shops avec les nouvelles colonnes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT NOT NULL,
            shop_url TEXT NOT NULL,
            monthly_visits INTEGER,
            monthly_revenue TEXT,
            live_ads TEXT,
            creation_date TEXT,
            category TEXT,
            total_products INTEGER,
            pixel_google TEXT,
            pixel_facebook TEXT,
            aov NUMERIC,
            market_us NUMERIC,
            market_uk NUMERIC,
            market_de NUMERIC,
            market_ca NUMERIC,
            market_au NUMERIC,
            market_fr NUMERIC,
            live_ads_7d NUMERIC,
            live_ads_30d NUMERIC,
            scraping_status TEXT,
            updated_at TEXT,
            project_source TEXT
        )
    ''')
    
    # Insérer des données de test avec les nouvelles colonnes
    test_shops = [
        {
            'shop_name': 'Test Shop Live Ads',
            'shop_url': 'https://test-shop-live-ads.com',
            'monthly_visits': 100000,
            'monthly_revenue': '$50,000',
            'live_ads': '500',
            'creation_date': '2020-01-01',
            'category': 'Electronics',
            'total_products': 1000,
            'pixel_google': 'UA-123456-1',
            'pixel_facebook': 'FB-789012',
            'aov': 100.00,
            'market_us': 0.60,
            'market_uk': 0.20,
            'market_de': 0.10,
            'market_ca': 0.05,
            'market_au': 0.03,
            'market_fr': 0.02,
            'live_ads_7d': 15.5,  # +15.5% sur 7 jours
            'live_ads_30d': -8.2,  # -8.2% sur 30 jours
            'scraping_status': '',
            'updated_at': datetime.now().isoformat(),
            'project_source': 'test_data'
        }
    ]
    
    for shop in test_shops:
        cursor.execute('''
            INSERT INTO shops (
                shop_name, shop_url, monthly_visits, monthly_revenue, live_ads,
                creation_date, category, total_products, pixel_google, pixel_facebook, 
                aov, market_us, market_uk, market_de, market_ca, market_au, market_fr,
                live_ads_7d, live_ads_30d, scraping_status, updated_at, project_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            shop['shop_name'], shop['shop_url'], shop['monthly_visits'], 
            shop['monthly_revenue'], shop['live_ads'], shop['creation_date'],
            shop['category'], shop['total_products'], shop['pixel_google'],
            shop['pixel_facebook'], shop['aov'], shop['market_us'], shop['market_uk'],
            shop['market_de'], shop['market_ca'], shop['market_au'], shop['market_fr'],
            shop['live_ads_7d'], shop['live_ads_30d'], shop['scraping_status'], 
            shop['updated_at'], shop['project_source']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de données de test créée: {db_path}")
    return db_path

def test_database_with_live_ads(db_path):
    """Teste la base de données avec les nouvelles colonnes"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier que les nouvelles colonnes existent
        cursor.execute("PRAGMA table_info(shops)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'live_ads_7d' in columns and 'live_ads_30d' in columns:
            print("✅ Nouvelles colonnes live_ads_7d et live_ads_30d trouvées")
            
            # Afficher un exemple
            cursor.execute("SELECT shop_name, live_ads, live_ads_7d, live_ads_30d FROM shops LIMIT 1")
            example = cursor.fetchone()
            if example:
                print(f"✅ Exemple: {example[0]} - Live Ads: {example[1]} - 7d: {example[2]}% - 30d: {example[3]}%")
        else:
            print("❌ Nouvelles colonnes non trouvées")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur test base de données: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Création de la base de données de test avec live_ads_7d et live_ads_30d...")
    
    # Créer la base de test
    db_path = create_test_database_with_live_ads()
    
    # Tester la base
    success = test_database_with_live_ads(db_path)
    
    if success:
        print("🎉 Base de données de test créée avec succès !")
    else:
        print("❌ Erreur lors de la création de la base de données de test !")