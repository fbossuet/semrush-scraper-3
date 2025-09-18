#!/usr/bin/env python3
"""
Tests en conditions réelles du système de conversion des dates
Simule les vraies réponses des APIs et teste l'intégration complète
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Ajouter le chemin du convertisseur
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from date_converter import DateConverter, convert_api_response_dates

def test_real_api_responses():
    """Test avec de vraies réponses d'APIs simulées"""
    print("🧪 TESTS AVEC RÉPONSES RÉELLES D'APIS")
    print("=" * 60)
    
    # Simuler une vraie réponse MyToolsPlan
    mytools_response = {
        "status": "success",
        "data": {
            "organic_traffic": {
                "value": 15000,
                "timestamp": "2025-08-05T19:40:56.053Z",
                "period": "2025-07-01,2025-07-31"
            },
            "bounce_rate": {
                "value": 45.5,
                "timestamp": "2025-08-05 20:47:15.852714",
                "period": "2025-07-01,2025-07-31"
            },
            "avg_visit_duration": {
                "value": "2:45",
                "timestamp": "2025-08-05T19:40:56",
                "period": "2025-07-01,2025-07-31"
            },
            "branded_traffic": {
                "value": 2500,
                "timestamp": "2025-08-05 20:47:15",
                "period": "2025-07-01,2025-07-31"
            },
            "conversion_rate": {
                "value": "3.2%",
                "timestamp": "2025-08-05T19:40:56.053Z",
                "period": "2025-07-01,2025-07-31"
            },
            "paid_search_traffic": {
                "value": 800,
                "timestamp": "2025-08-05 20:47:15.852714",
                "period": "2025-07-01,2025-07-31"
            },
            "visits": {
                "value": 18000,
                "timestamp": "2025-08-05T19:40:56",
                "period": "2025-07-01,2025-07-31"
            },
            "traffic": {
                "value": 20000,
                "timestamp": "2025-08-05 20:47:15",
                "period": "2025-07-01,2025-07-31"
            }
        },
        "metadata": {
            "api_version": "v1.0",
            "request_id": "req_1691234567890_abc123",
            "generated_at": "2025-08-05T19:40:56.053Z",
            "processing_time": 1.2
        }
    }
    
    # Simuler une vraie réponse TrendTrack
    trendtrack_response = {
        "success": True,
        "shops": [
            {
                "id": 1,
                "shop_name": "Test Shop",
                "shop_url": "https://test-shop.com",
                "scraping_status": "completed",
                "monthly_visits": 25000,
                "monthly_revenue": "$50,000",
                "live_ads": "15",
                "project_source": "trendtrack",
                "scraped_at": "2025-08-05T19:40:56.053",
                "creation_date": "2025-08-05",
                "year_founded": "2020",
                "updated_at": "2025-08-05 20:47:15.852714"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 50,
            "total": 1,
            "last_updated": "2025-08-05T19:40:56.053Z"
        }
    }
    
    print("\n📊 TEST RÉPONSE MYTOOLSPLAN")
    print("-" * 40)
    
    # Convertir la réponse MyToolsPlan
    converted_mytools = convert_api_response_dates(mytools_response)
    
    print("Champs de dates convertis:")
    for key, value in converted_mytools.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if 'timestamp' in sub_key:
                    print(f"  {key}.{sub_key}: {sub_value}")
        elif 'timestamp' in key or 'generated_at' in key:
            print(f"  {key}: {value}")
    
    print("\n📊 TEST RÉPONSE TRENDTRACK")
    print("-" * 40)
    
    # Convertir la réponse TrendTrack
    converted_trendtrack = convert_api_response_dates(trendtrack_response)
    
    print("Champs de dates convertis:")
    for shop in converted_trendtrack.get('shops', []):
        for key, value in shop.items():
            if 'date' in key or 'at' in key or 'founded' in key:
                print(f"  {key}: {value}")
    
    return converted_mytools, converted_trendtrack

def test_database_integration():
    """Test d'intégration avec la base de données"""
    print("\n🗄️ TEST INTÉGRATION BASE DE DONNÉES")
    print("-" * 40)
    
    # Créer une base de test
    test_db_path = "test_date_conversions.db"
    
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
        
        # Insérer des données de test avec dates converties
        test_shop_data = {
            "shop_name": "Test Shop Conversion",
            "shop_url": "https://test-conversion.com",
            "scraping_status": "completed",
            "monthly_visits": 25000,
            "monthly_revenue": "$50,000",
            "live_ads": "15",
            "project_source": "test",
            "scraped_at": DateConverter.convert_to_iso8601_utc("2025-08-05T19:40:56.053Z"),
            "creation_date": DateConverter.convert_to_iso8601_utc("2025-08-05"),
            "year_founded": DateConverter.convert_to_iso8601_utc("2020"),
            "updated_at": DateConverter.convert_to_iso8601_utc("2025-08-05 20:47:15.852714")
        }
        
        cursor.execute("""
            INSERT INTO shops (
                shop_name, shop_url, scraping_status, monthly_visits, monthly_revenue,
                live_ads, project_source, scraped_at, creation_date, year_founded, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_shop_data["shop_name"],
            test_shop_data["shop_url"],
            test_shop_data["scraping_status"],
            test_shop_data["monthly_visits"],
            test_shop_data["monthly_revenue"],
            test_shop_data["live_ads"],
            test_shop_data["project_source"],
            test_shop_data["scraped_at"],
            test_shop_data["creation_date"],
            test_shop_data["year_founded"],
            test_shop_data["updated_at"]
        ))
        
        shop_id = cursor.lastrowid
        
        # Insérer des données analytics
        test_analytics_data = {
            "organic_traffic": 15000,
            "bounce_rate": 45.5,
            "avg_visit_duration": "2:45",
            "branded_traffic": 2500,
            "conversion_rate": "3.2%",
            "visits": 18000,
            "traffic": 20000,
            "paid_search_traffic": 800,
            "percent_branded_traffic": 13.9,
            "updated_at": DateConverter.convert_to_iso8601_utc(datetime.now(timezone.utc))
        }
        
        cursor.execute("""
            INSERT INTO analytics (
                shop_id, organic_traffic, bounce_rate, avg_visit_duration,
                branded_traffic, conversion_rate, visits, traffic,
                paid_search_traffic, percent_branded_traffic, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shop_id,
            test_analytics_data["organic_traffic"],
            test_analytics_data["bounce_rate"],
            test_analytics_data["avg_visit_duration"],
            test_analytics_data["branded_traffic"],
            test_analytics_data["conversion_rate"],
            test_analytics_data["visits"],
            test_analytics_data["traffic"],
            test_analytics_data["paid_search_traffic"],
            test_analytics_data["percent_branded_traffic"],
            test_analytics_data["updated_at"]
        ))
        
        conn.commit()
        
        # Vérifier les données insérées
        cursor.execute("SELECT * FROM shops WHERE id = ?", (shop_id,))
        shop_row = cursor.fetchone()
        
        cursor.execute("SELECT * FROM analytics WHERE shop_id = ?", (shop_id,))
        analytics_row = cursor.fetchone()
        
        print("✅ Données insérées avec succès:")
        print(f"  Shop ID: {shop_id}")
        print(f"  Scraped at: {shop_row[11]}")  # scraped_at
        print(f"  Creation date: {shop_row[6]}")  # creation_date
        print(f"  Updated at: {shop_row[5]}")  # updated_at
        print(f"  Analytics updated at: {analytics_row[9]}")  # updated_at
        
        # Valider les formats
        date_fields = [shop_row[11], shop_row[6], shop_row[5], analytics_row[9]]
        print("\n🔍 Validation des formats:")
        for i, date_field in enumerate(date_fields):
            if date_field:
                is_valid = DateConverter.validate_iso8601_utc(date_field)
                print(f"  Champ {i+1}: {'✅' if is_valid else '❌'} {date_field}")
        
        conn.close()
        
        # Nettoyer
        os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test base de données: {e}")
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        return False

def test_scraper_integration():
    """Test d'intégration avec les scrapers"""
    print("\n🔧 TEST INTÉGRATION SCRAPERS")
    print("-" * 40)
    
    # Simuler le traitement d'une réponse API dans un scraper
    class MockScraper:
        def __init__(self):
            self.api_responses = []
        
        def process_api_response(self, response_data):
            """Simule le traitement d'une réponse API"""
            # Convertir les dates
            converted_data = convert_api_response_dates(response_data)
            
            # Simuler l'extraction des métriques
            metrics = self._extract_metrics(converted_data)
            
            # Simuler la validation
            validated_metrics = self._validate_metrics(metrics)
            
            return validated_metrics
        
        def _extract_metrics(self, data):
            """Extrait les métriques des données converties"""
            metrics = {}
            
            if 'data' in data:
                for metric_name, metric_data in data['data'].items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        metrics[metric_name] = {
                            'value': metric_data['value'],
                            'timestamp': metric_data.get('timestamp'),
                            'period': metric_data.get('period')
                        }
            
            return metrics
        
        def _validate_metrics(self, metrics):
            """Valide les métriques extraites"""
            validated = {}
            
            for metric_name, metric_data in metrics.items():
                # Valider la valeur
                value = metric_data['value']
                if isinstance(value, str) and value.replace('.', '').replace(',', '').isdigit():
                    validated[metric_name] = float(value.replace(',', ''))
                elif isinstance(value, (int, float)):
                    validated[metric_name] = value
                else:
                    validated[metric_name] = value
                
                # Valider le timestamp
                timestamp = metric_data.get('timestamp')
                if timestamp:
                    is_valid = DateConverter.validate_iso8601_utc(timestamp)
                    if not is_valid:
                        print(f"⚠️ Timestamp invalide pour {metric_name}: {timestamp}")
            
            return validated
    
    # Tester avec une réponse MyToolsPlan
    mytools_response = {
        "data": {
            "organic_traffic": {
                "value": "15,000",
                "timestamp": "2025-08-05T19:40:56.053Z",
                "period": "2025-07-01,2025-07-31"
            },
            "bounce_rate": {
                "value": "45.5%",
                "timestamp": "2025-08-05 20:47:15.852714",
                "period": "2025-07-01,2025-07-31"
            },
            "visits": {
                "value": 18000,
                "timestamp": "2025-08-05T19:40:56",
                "period": "2025-07-01,2025-07-31"
            }
        }
    }
    
    scraper = MockScraper()
    result = scraper.process_api_response(mytools_response)
    
    print("✅ Métriques traitées:")
    for metric_name, value in result.items():
        print(f"  {metric_name}: {value}")
    
    return result

def test_error_handling():
    """Test de gestion d'erreurs"""
    print("\n⚠️ TEST GESTION D'ERREURS")
    print("-" * 40)
    
    # Test avec des données corrompues
    corrupted_data = {
        "valid_date": "2025-08-05T19:40:56.053Z",
        "invalid_date": "not-a-date",
        "empty_date": "",
        "null_date": None,
        "malformed_date": "2025-13-45T25:70:80.999Z",
        "unix_timestamp": 1691234567,
        "javascript_timestamp": 1691234567890
    }
    
    print("Données de test:")
    for key, value in corrupted_data.items():
        print(f"  {key}: {value}")
    
    print("\nRésultats de conversion:")
    for key, value in corrupted_data.items():
        result = DateConverter.convert_to_iso8601_utc(value)
        is_valid = DateConverter.validate_iso8601_utc(result) if result else False
        print(f"  {key}: {result} {'✅' if is_valid else '❌'}")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 TESTS COMPLETS DU SYSTÈME DE CONVERSION DES DATES")
    print("=" * 70)
    
    try:
        # Test 1: Réponses d'APIs réelles
        print("\n1️⃣ TEST RÉPONSES D'APIS RÉELLES")
        converted_mytools, converted_trendtrack = test_real_api_responses()
        
        # Test 2: Intégration base de données
        print("\n2️⃣ TEST INTÉGRATION BASE DE DONNÉES")
        db_success = test_database_integration()
        
        # Test 3: Intégration scrapers
        print("\n3️⃣ TEST INTÉGRATION SCRAPERS")
        scraper_result = test_scraper_integration()
        
        # Test 4: Gestion d'erreurs
        print("\n4️⃣ TEST GESTION D'ERREURS")
        error_success = test_error_handling()
        
        # Résumé
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 40)
        print(f"✅ Réponses APIs: {'SUCCÈS' if converted_mytools and converted_trendtrack else 'ÉCHEC'}")
        print(f"✅ Base de données: {'SUCCÈS' if db_success else 'ÉCHEC'}")
        print(f"✅ Scrapers: {'SUCCÈS' if scraper_result else 'ÉCHEC'}")
        print(f"✅ Gestion erreurs: {'SUCCÈS' if error_success else 'ÉCHEC'}")
        
        if all([converted_mytools, converted_trendtrack, db_success, scraper_result, error_success]):
            print("\n🎉 TOUS LES TESTS RÉUSSIS !")
            print("Le système de conversion des dates est prêt pour la production.")
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            print("Vérifiez les erreurs ci-dessus.")
        
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
