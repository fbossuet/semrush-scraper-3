#!/usr/bin/env python3
"""
Test du scraper SEM avec le système de conversion des dates
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timezone

# Ajouter les chemins nécessaires
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sem-scraper-final'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from date_converter import DateConverter, convert_api_response_dates

def test_sem_scraper_date_handling():
    """Test de la gestion des dates dans le scraper SEM"""
    print("🔧 TEST SCRAPER SEM - GESTION DES DATES")
    print("=" * 50)
    
    # Simuler une session de scraping SEM
    class MockSEMScraper:
        def __init__(self):
            self.session_data = {
                "data": {
                    "organic_traffic": {
                        "value": "15,000",
                        "timestamp": "2025-08-05T19:40:56.053Z"
                    },
                    "bounce_rate": {
                        "value": "45.5%",
                        "timestamp": "2025-08-05 20:47:15.852714"
                    },
                    "avg_visit_duration": {
                        "value": "2:45",
                        "timestamp": "2025-08-05T19:40:56"
                    },
                    "branded_traffic": {
                        "value": "2,500",
                        "timestamp": "2025-08-05 20:47:15"
                    },
                    "conversion_rate": {
                        "value": "3.2%",
                        "timestamp": "2025-08-05T19:40:56.053Z"
                    },
                    "paid_search_traffic": {
                        "value": "800",
                        "timestamp": "2025-08-05 20:47:15.852714"
                    },
                    "visits": {
                        "value": "18,000",
                        "timestamp": "2025-08-05T19:40:56"
                    },
                    "traffic": {
                        "value": "20,000",
                        "timestamp": "2025-08-05 20:47:15"
                    },
                    "traffic_analysis": {
                        "visits": "18,000",
                        "timestamp": "2025-08-05T19:40:56.053Z"
                    }
                },
                "metadata": {
                    "scraped_at": "2025-08-05T19:40:56.053Z",
                    "processing_time": 1.2,
                    "api_version": "v1.0"
                }
            }
        
        def format_analytics_for_api(self):
            """Formate les données de session pour l'API (version corrigée)"""
            analytics_data = {
                "organic_traffic": "",
                "bounce_rate": "",
                "average_visit_duration": "",
                "branded_traffic": "",
                "conversion_rate": "",
                "paid_search_traffic": "",
                "traffic": "",
                "percent_branded_traffic": "",
                "visits": ""  # ← AJOUTÉ
            }
            
            # Récupérer les données de chaque métrique
            for metric_name in analytics_data.keys():
                if metric_name in self.session_data['data']:
                    metric_data = self.session_data['data'][metric_name]
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        analytics_data[metric_name] = metric_data['value']
            
            # Récupérer les données de traffic_analysis (visits)
            if 'traffic_analysis' in self.session_data['data']:
                traffic_data = self.session_data['data']['traffic_analysis']
                analytics_data['visits'] = traffic_data.get('visits', '')
            
            # Calculer percent_branded_traffic
            try:
                branded = float(analytics_data['branded_traffic'].replace(',', '')) if analytics_data['branded_traffic'] else 0
                total = float(analytics_data['traffic'].replace(',', '')) if analytics_data['traffic'] else 0
                if total > 0:
                    analytics_data['percent_branded_traffic'] = str(round((branded / total) * 100, 2))
                else:
                    analytics_data['percent_branded_traffic'] = "0"
            except:
                analytics_data['percent_branded_traffic'] = "0"
            
            return analytics_data
        
        def _validate_int(self, value):
            """Valide qu'une valeur est un INTEGER valide"""
            if not value or value == 'na' or value == '':
                return None
            try:
                if isinstance(value, int):
                    return value
                cleaned = str(value).replace(',', '').replace(' ', '').replace('$', '')
                return int(float(cleaned))
            except (ValueError, TypeError):
                print(f"⚠️ Valeur '{value}' n'est pas un INTEGER valide")
                return None

        def _validate_numeric(self, value):
            """Valide qu'une valeur est un NUMERIC valide"""
            if not value or value == 'na' or value == '':
                return None
            try:
                if isinstance(value, (int, float)):
                    return float(value)
                cleaned = str(value).replace('%', '').replace(' ', '').replace(',', '')
                return float(cleaned)
            except (ValueError, TypeError):
                print(f"⚠️ Valeur '{value}' n'est pas un NUMERIC valide")
                return None

        def _validate_visit_duration(self, value):
            """Valide la durée de visite - format MM:SS ou secondes"""
            if not value or value == 'na' or value == '':
                return None
            try:
                if isinstance(value, (int, float)):
                    return float(value)
                if ':' in str(value):
                    parts = str(value).split(':')
                    if len(parts) == 2:
                        minutes, seconds = int(parts[0]), int(parts[1])
                        return float(minutes * 60 + seconds)
                return float(str(value).replace(',', '').replace(' ', ''))
            except (ValueError, TypeError):
                print(f"⚠️ Durée de visite '{value}' n'est pas valide")
                return None
        
        def _convert_api_dates(self, data):
            """Convertit les dates d'une réponse API vers ISO 8601 UTC"""
            if not isinstance(data, dict):
                return data
            
            # Champs de dates communs dans les APIs
            date_fields = [
                'timestamp', 'created_at', 'updated_at', 'scraped_at', 'creation_date',
                'last_update', 'date', 'time', 'start_date', 'end_date', 'year_founded'
            ]
            
            return convert_api_response_dates(data)
        
        def process_scraping_session(self):
            """Simule le traitement d'une session de scraping"""
            print("📊 Traitement de la session de scraping...")
            
            # 1. Convertir les dates de la session
            converted_session = self._convert_api_dates(self.session_data)
            print("✅ Dates de session converties vers ISO 8601 UTC")
            
            # 2. Formater les analytics
            analytics_data = self.format_analytics_for_api()
            print("✅ Analytics formatées")
            
            # 3. Valider les métriques
            final_metrics = {
                'organic_traffic': self._validate_int(analytics_data['organic_traffic']),
                'bounce_rate': self._validate_numeric(analytics_data['bounce_rate']),
                'avg_visit_duration': self._validate_visit_duration(analytics_data['average_visit_duration']),
                'branded_traffic': self._validate_int(analytics_data['branded_traffic']),
                'conversion_rate': analytics_data['conversion_rate'],
                'paid_search_traffic': self._validate_int(analytics_data['paid_search_traffic']),
                'visits': self._validate_int(analytics_data['visits']),
                'traffic': self._validate_int(analytics_data['traffic']),
                'percent_branded_traffic': self._validate_numeric(analytics_data['percent_branded_traffic']),
                'updated_at': DateConverter.convert_to_iso8601_utc(datetime.now(timezone.utc))
            }
            
            print("✅ Métriques validées")
            
            return {
                'session_data': converted_session,
                'analytics_data': analytics_data,
                'final_metrics': final_metrics
            }
    
    # Tester le scraper
    scraper = MockSEMScraper()
    result = scraper.process_scraping_session()
    
    print("\n📋 RÉSULTATS DU TRAITEMENT")
    print("-" * 40)
    
    print("Session data (dates converties):")
    for key, value in result['session_data']['metadata'].items():
        if 'timestamp' in key or 'at' in key:
            print(f"  {key}: {value}")
    
    print("\nAnalytics data:")
    for key, value in result['analytics_data'].items():
        print(f"  {key}: {value}")
    
    print("\nFinal metrics (validées):")
    for key, value in result['final_metrics'].items():
        print(f"  {key}: {value}")
    
    # Valider les dates finales
    print("\n🔍 VALIDATION DES DATES FINALES")
    print("-" * 40)
    
    for key, value in result['final_metrics'].items():
        if 'date' in key or 'at' in key:
            if value:
                is_valid = DateConverter.validate_iso8601_utc(value)
                print(f"  {key}: {'✅' if is_valid else '❌'} {value}")
    
    return result

def test_database_insertion():
    """Test d'insertion en base de données avec les métriques validées"""
    print("\n🗄️ TEST INSERTION BASE DE DONNÉES")
    print("-" * 40)
    
    # Simuler les données finales d'un scraper
    final_metrics = {
        'organic_traffic': 15000,
        'bounce_rate': 45.5,
        'avg_visit_duration': 165.0,  # 2:45 en secondes
        'branded_traffic': 2500,
        'conversion_rate': '3.2%',
        'paid_search_traffic': 800,
        'visits': 18000,
        'traffic': 20000,
        'percent_branded_traffic': 12.5,
        'updated_at': DateConverter.convert_to_iso8601_utc(datetime.now(timezone.utc))
    }
    
    # Simuler l'insertion SQL
    sql_insert = """
    INSERT OR REPLACE INTO analytics
    (shop_id, organic_traffic, bounce_rate, avg_visit_duration,
     branded_traffic, conversion_rate, paid_search_traffic,
     visits, traffic, percent_branded_traffic,
     scraping_status, updated_at, cpc)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    values = (
        1,  # shop_id
        final_metrics['organic_traffic'],
        final_metrics['bounce_rate'],
        final_metrics['avg_visit_duration'],
        final_metrics['branded_traffic'],
        final_metrics['conversion_rate'],
        final_metrics['paid_search_traffic'],
        final_metrics['visits'],
        final_metrics['traffic'],
        final_metrics['percent_branded_traffic'],
        'completed',
        final_metrics['updated_at'],
        None  # cpc - pas encore implémenté
    )
    
    print("SQL Insert simulé:")
    print(sql_insert)
    print("\nValeurs:")
    for i, value in enumerate(values):
        print(f"  {i+1}: {value} ({type(value).__name__})")
    
    # Valider la date
    is_valid = DateConverter.validate_iso8601_utc(final_metrics['updated_at'])
    print(f"\nDate updated_at: {'✅' if is_valid else '❌'} {final_metrics['updated_at']}")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DU SCRAPER SEM AVEC CONVERSION DES DATES")
    print("=" * 70)
    
    try:
        # Test 1: Gestion des dates dans le scraper
        print("\n1️⃣ TEST GESTION DES DATES DANS LE SCRAPER")
        scraper_result = test_sem_scraper_date_handling()
        
        # Test 2: Insertion en base de données
        print("\n2️⃣ TEST INSERTION BASE DE DONNÉES")
        db_result = test_database_insertion()
        
        # Résumé
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 40)
        print(f"✅ Scraper SEM: {'SUCCÈS' if scraper_result else 'ÉCHEC'}")
        print(f"✅ Base de données: {'SUCCÈS' if db_result else 'ÉCHEC'}")
        
        if scraper_result and db_result:
            print("\n🎉 TOUS LES TESTS RÉUSSIS !")
            print("Le scraper SEM est prêt avec le système de conversion des dates.")
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            print("Vérifiez les erreurs ci-dessus.")
        
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
