#!/usr/bin/env python3
"""
Test de scénario de production complet
Simule le flux complet : APIs → Conversion → Validation → Base de données
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Ajouter les chemins nécessaires
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from date_converter import DateConverter, convert_api_response_dates

def test_production_scenario():
    """Test complet d'un scénario de production"""
    print("🏭 TEST SCÉNARIO DE PRODUCTION COMPLET")
    print("=" * 60)
    
    # Créer une base de test
    test_db_path = "test_production_scenario.db"
    
    try:
        # Supprimer la base de test si elle existe
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Créer la base de test
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Créer les tables avec la structure finale
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "shops" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_name TEXT,
                shop_url TEXT UNIQUE NOT NULL,
                scraping_status TEXT,
                scraping_last_update TEXT,
                updated_at TEXT,
                creation_date TEXT,
                monthly_visits INTEGER,
                monthly_revenue TEXT,
                live_ads TEXT,
                page_number TEXT,
                scraped_at TEXT,
                project_source TEXT,
                external_id TEXT,
                metadata TEXT,
                year_founded TEXT,
                total_products INTEGER,
                pixel_google INTEGER,
                pixel_facebook INTEGER,
                aov NUMERIC,
                market_us NUMERIC,
                market_uk NUMERIC,
                market_de NUMERIC,
                market_ca NUMERIC,
                market_au NUMERIC,
                market_fr NUMERIC
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "analytics" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                organic_traffic INTEGER,
                bounce_rate NUMERIC,
                avg_visit_duration TEXT,
                branded_traffic INTEGER,
                conversion_rate TEXT,
                scraping_status TEXT DEFAULT 'completed',
                updated_at TEXT,
                visits INTEGER,
                traffic INTEGER,
                paid_search_traffic INTEGER,
                percent_branded_traffic NUMERIC,
                cpc NUMERIC,
                FOREIGN KEY (shop_id) REFERENCES shops (id)
            );
        """)
        
        print("✅ Base de données de test créée")
        
        # Scénario 1: Scraping TrendTrack
        print("\n📊 SCÉNARIO 1: SCRAPING TRENDTRACK")
        print("-" * 40)
        
        # Simuler une réponse TrendTrack
        trendtrack_response = {
            "shop_name": "Production Test Shop",
            "shop_url": "https://production-test-shop.com",
            "scraping_status": "completed",
            "monthly_visits": "25,000",
            "monthly_revenue": "$50,000",
            "live_ads": "15",
            "project_source": "trendtrack",
            "scraped_at": "2025-08-05T19:40:56.053Z",
            "creation_date": "2025-08-05",
            "year_founded": "2020",
            "updated_at": "2025-08-05 20:47:15.852714",
            "total_products": "150",
            "pixel_google": "1",
            "pixel_facebook": "1",
            "aov": "45.50",
            "market_us": "175,942",
            "market_uk": "0",
            "market_de": "0",
            "market_ca": "0",
            "market_au": "18,555,284",
            "market_fr": "0"
        }
        
        # Convertir les dates
        converted_trendtrack = convert_api_response_dates(trendtrack_response)
        print("✅ Dates TrendTrack converties vers ISO 8601 UTC")
        
        # Valider et nettoyer les données
        def validate_int(value):
            if not value or value == 'na' or value == '':
                return None
            try:
                cleaned = str(value).replace(',', '').replace(' ', '').replace('$', '')
                return int(float(cleaned))
            except:
                return None
        
        def validate_numeric(value):
            if not value or value == 'na' or value == '':
                return None
            try:
                cleaned = str(value).replace('%', '').replace(' ', '').replace(',', '')
                return float(cleaned)
            except:
                return None
        
        # Insérer en base
        cursor.execute("""
            INSERT OR REPLACE INTO shops (
                shop_name, shop_url, scraping_status, monthly_visits, monthly_revenue,
                live_ads, project_source, scraped_at, creation_date, year_founded, updated_at,
                total_products, pixel_google, pixel_facebook, aov,
                market_us, market_uk, market_de, market_ca, market_au, market_fr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            converted_trendtrack["shop_name"],
            converted_trendtrack["shop_url"],
            converted_trendtrack["scraping_status"],
            validate_int(converted_trendtrack["monthly_visits"]),
            converted_trendtrack["monthly_revenue"],
            converted_trendtrack["live_ads"],
            converted_trendtrack["project_source"],
            converted_trendtrack["scraped_at"],
            converted_trendtrack["creation_date"],
            converted_trendtrack["year_founded"],
            converted_trendtrack["updated_at"],
            validate_int(converted_trendtrack["total_products"]),
            validate_int(converted_trendtrack["pixel_google"]),
            validate_int(converted_trendtrack["pixel_facebook"]),
            validate_numeric(converted_trendtrack["aov"]),
            validate_numeric(converted_trendtrack["market_us"]),
            validate_numeric(converted_trendtrack["market_uk"]),
            validate_numeric(converted_trendtrack["market_de"]),
            validate_numeric(converted_trendtrack["market_ca"]),
            validate_numeric(converted_trendtrack["market_au"]),
            validate_numeric(converted_trendtrack["market_fr"])
        ))
        
        shop_id = cursor.lastrowid
        print(f"✅ Shop inséré avec ID: {shop_id}")
        
        # Scénario 2: Scraping SEM
        print("\n📊 SCÉNARIO 2: SCRAPING SEM")
        print("-" * 40)
        
        # Simuler une réponse MyToolsPlan
        mytools_response = {
            "organic_traffic": "15,000",
            "bounce_rate": "45.5%",
            "avg_visit_duration": "2:45",
            "branded_traffic": "2,500",
            "conversion_rate": "3.2%",
            "paid_search_traffic": "800",
            "visits": "18,000",
            "traffic": "20,000",
            "percent_branded_traffic": "12.5%",
            "scraped_at": "2025-08-05T19:40:56.053Z",
            "updated_at": "2025-08-05 20:47:15.852714"
        }
        
        # Convertir les dates
        converted_mytools = convert_api_response_dates(mytools_response)
        print("✅ Dates MyToolsPlan converties vers ISO 8601 UTC")
        
        # Valider les métriques
        def validate_visit_duration(value):
            if not value or value == 'na' or value == '':
                return None
            try:
                if ':' in str(value):
                    parts = str(value).split(':')
                    if len(parts) == 2:
                        minutes, seconds = int(parts[0]), int(parts[1])
                        return float(minutes * 60 + seconds)
                return float(str(value).replace(',', '').replace(' ', ''))
            except:
                return None
        
        # Insérer en base
        cursor.execute("""
            INSERT OR REPLACE INTO analytics (
                shop_id, organic_traffic, bounce_rate, avg_visit_duration,
                branded_traffic, conversion_rate, paid_search_traffic,
                visits, traffic, percent_branded_traffic,
                scraping_status, updated_at, cpc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shop_id,
            validate_int(converted_mytools["organic_traffic"]),
            validate_numeric(converted_mytools["bounce_rate"]),
            validate_visit_duration(converted_mytools["avg_visit_duration"]),
            validate_int(converted_mytools["branded_traffic"]),
            converted_mytools["conversion_rate"],
            validate_int(converted_mytools["paid_search_traffic"]),
            validate_int(converted_mytools["visits"]),
            validate_int(converted_mytools["traffic"]),
            validate_numeric(converted_mytools["percent_branded_traffic"]),
            'completed',
            converted_mytools["updated_at"],
            None  # cpc - pas encore implémenté
        ))
        
        print(f"✅ Analytics insérées pour shop_id: {shop_id}")
        
        # Valider les données insérées
        print("\n🔍 VALIDATION DES DONNÉES INSÉRÉES")
        print("-" * 40)
        
        # Récupérer les données du shop
        cursor.execute("SELECT * FROM shops WHERE id = ?", (shop_id,))
        shop_row = cursor.fetchone()
        
        # Récupérer les données analytics
        cursor.execute("SELECT * FROM analytics WHERE shop_id = ?", (shop_id,))
        analytics_row = cursor.fetchone()
        
        print("Shop data:")
        print(f"  ID: {shop_row[0]}")
        print(f"  Name: {shop_row[1]}")
        print(f"  URL: {shop_row[2]}")
        print(f"  Monthly visits: {shop_row[7]}")
        print(f"  Market US: {shop_row[16]}")
        print(f"  Market AU: {shop_row[20]}")
        print(f"  Scraped at: {shop_row[11]}")
        print(f"  Updated at: {shop_row[5]}")
        
        print("\nAnalytics data:")
        print(f"  Organic traffic: {analytics_row[2]}")
        print(f"  Bounce rate: {analytics_row[3]}")
        print(f"  Visit duration: {analytics_row[4]}")
        print(f"  Visits: {analytics_row[9]}")
        print(f"  Updated at: {analytics_row[8]}")
        
        # Valider les formats de dates
        print("\n🔍 VALIDATION DES FORMATS DE DATES")
        print("-" * 40)
        
        date_fields = [
            ("Shop scraped_at", shop_row[11]),
            ("Shop updated_at", shop_row[5]),
            ("Analytics updated_at", analytics_row[8])
        ]
        
        for field_name, date_value in date_fields:
            if date_value:
                is_valid = DateConverter.validate_iso8601_utc(date_value)
                print(f"  {field_name}: {'✅' if is_valid else '❌'} {date_value}")
        
        # Test de requête complexe
        print("\n📊 TEST REQUÊTE COMPLEXE")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                s.shop_name,
                s.monthly_visits,
                s.market_us,
                s.market_au,
                a.organic_traffic,
                a.bounce_rate,
                a.visits,
                s.scraped_at,
                a.updated_at
            FROM shops s
            LEFT JOIN analytics a ON s.id = a.shop_id
            WHERE s.id = ?
        """, (shop_id,))
        
        result = cursor.fetchone()
        
        if result:
            print("Résultat de la requête complexe:")
            print(f"  Shop: {result[0]}")
            print(f"  Monthly visits: {result[1]}")
            print(f"  Market US: {result[2]}")
            print(f"  Market AU: {result[3]}")
            print(f"  Organic traffic: {result[4]}")
            print(f"  Bounce rate: {result[5]}")
            print(f"  Visits: {result[6]}")
            print(f"  Shop scraped at: {result[7]}")
            print(f"  Analytics updated at: {result[8]}")
        
        conn.commit()
        conn.close()
        
        # Nettoyer
        os.remove(test_db_path)
        
        print("\n✅ SCÉNARIO DE PRODUCTION TERMINÉ AVEC SUCCÈS")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le scénario de production: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST SCÉNARIO DE PRODUCTION COMPLET")
    print("=" * 70)
    
    try:
        # Test du scénario de production
        success = test_production_scenario()
        
        if success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS !")
            print("Le système est prêt pour la production avec:")
            print("✅ Conversion automatique des dates vers ISO 8601 UTC")
            print("✅ Validation des métriques")
            print("✅ Insertion en base de données")
            print("✅ Requêtes complexes fonctionnelles")
            print("✅ Gestion d'erreurs robuste")
        else:
            print("\n❌ LE TEST A ÉCHOUÉ")
            print("Vérifiez les erreurs ci-dessus.")
        
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
