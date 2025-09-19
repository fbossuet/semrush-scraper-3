#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connexion à la base de données
conn = sqlite3.connect('/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/trendtrack.db')
cursor = conn.cursor()

# Données de test avec types corrects
test_shops = [
    {
        'shop_name': 'TechGadget Store',
        'shop_url': 'https://techgadget-store.com',
        'monthly_visits': 150000,  # INTEGER
        'monthly_revenue': '$75,000',  # TEXT
        'live_ads': '1850',  # TEXT
        'creation_date': '2019-03-15',  # TEXT
        'category': 'Electronics',  # TEXT
        'total_products': 1850,  # INTEGER
        'pixel_google': 'UA-123456-1',  # TEXT
        'pixel_facebook': 'FB-789012',  # TEXT
        'aov': 125.50,  # NUMERIC
        'market_us': 0.65, 'market_uk': 0.15, 'market_de': 0.08, 
        'market_ca': 0.07, 'market_au': 0.03, 'market_fr': 0.02,  # NUMERIC
        'scraping_status': '',  # VIDE comme demandé
        'updated_at': datetime.now().isoformat(),
        'project_source': 'test_data'
    },
    {
        'shop_name': 'Fashion Forward',
        'shop_url': 'https://fashion-forward.com',
        'monthly_visits': 95000,  # INTEGER
        'monthly_revenue': '$45,000',  # TEXT
        'live_ads': '1120',  # TEXT
        'creation_date': '2020-07-22',  # TEXT
        'category': 'Apparel',  # TEXT
        'total_products': 1120,  # INTEGER
        'pixel_google': 'UA-654321-2',  # TEXT
        'pixel_facebook': 'FB-345678',  # TEXT
        'aov': 95.75,  # NUMERIC
        'market_us': 0.70, 'market_uk': 0.12, 'market_de': 0.06,
        'market_ca': 0.06, 'market_au': 0.04, 'market_fr': 0.02,  # NUMERIC
        'scraping_status': '',  # VIDE comme demandé
        'updated_at': datetime.now().isoformat(),
        'project_source': 'test_data'
    },
    {
        'shop_name': 'Home & Garden Plus',
        'shop_url': 'https://home-garden-plus.com',
        'monthly_visits': 75000,  # INTEGER
        'monthly_revenue': '$32,500',  # TEXT
        'live_ads': '890',  # TEXT
        'creation_date': '2021-01-10',  # TEXT
        'category': 'Home Goods',  # TEXT
        'total_products': 890,  # INTEGER
        'pixel_google': 'UA-987654-3',  # TEXT
        'pixel_facebook': 'FB-901234',  # TEXT
        'aov': 85.25,  # NUMERIC
        'market_us': 0.60, 'market_uk': 0.18, 'market_de': 0.10,
        'market_ca': 0.07, 'market_au': 0.03, 'market_fr': 0.02,  # NUMERIC
        'scraping_status': '',  # VIDE comme demandé
        'updated_at': datetime.now().isoformat(),
        'project_source': 'test_data'
    }
]

# Insertion des données
for shop in test_shops:
    cursor.execute('''
        INSERT OR REPLACE INTO shops (
            shop_name, shop_url, monthly_visits, monthly_revenue, live_ads,
            creation_date, category, total_products, pixel_google, pixel_facebook, 
            aov, market_us, market_uk, market_de, market_ca, market_au, market_fr,
            scraping_status, updated_at, project_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        shop['shop_name'], shop['shop_url'], shop['monthly_visits'], 
        shop['monthly_revenue'], shop['live_ads'], shop['creation_date'],
        shop['category'], shop['total_products'], shop['pixel_google'],
        shop['pixel_facebook'], shop['aov'], shop['market_us'], shop['market_uk'],
        shop['market_de'], shop['market_ca'], shop['market_au'], shop['market_fr'],
        shop['scraping_status'], shop['updated_at'], shop['project_source']
    ))
    print(f"✅ Boutique insérée: {shop['shop_name']}")

conn.commit()
conn.close()
print("🎉 Données de test insérées avec succès!")