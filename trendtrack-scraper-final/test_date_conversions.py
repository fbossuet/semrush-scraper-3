#!/usr/bin/env python3
"""
Script de test pour valider les conversions de dates dans les scrapers
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from date_converter import DateConverter, convert_api_response_dates

def test_date_conversions():
    print("🧪 TESTS DE CONVERSION DES DATES DANS LES SCRAPERS")
    print("=" * 60)
    
    # Tests des formats reçus des APIs
    api_test_cases = [
        # Formats MyToolsPlan
        {
            "name": "MyToolsPlan API Response",
            "data": {
                "timestamp": "2025-08-05T19:40:56.053Z",
                "created_at": "2025-08-05 20:47:15.852714",
                "updated_at": "2025-08-05T19:40:56",
                "scraped_at": "2025-08-05 20:47:15",
                "organic_traffic": 15000,
                "bounce_rate": 45.5
            }
        },
        
        # Formats TrendTrack
        {
            "name": "TrendTrack API Response",
            "data": {
                "timestamp": "2025-08-05T19:40:56.053",
                "creation_date": "2025-08-05",
                "scraped_at": "2025-08-05T19:40:56Z",
                "year_founded": "2020",
                "monthly_visits": 25000,
                "live_ads": "15"
            }
        },
        
        # Formats avec timestamps Unix
        {
            "name": "Unix Timestamp Response",
            "data": {
                "timestamp": 1691234567,
                "created_at": 1691234567890,  # JavaScript timestamp
                "updated_at": "2025-08-05",
                "scraped_at": None,
                "traffic": 10000
            }
        },
        
        # Formats mixtes
        {
            "name": "Mixed Format Response",
            "data": {
                "timestamp": "2025-08-05T19:40:56.053Z",
                "created_at": "2025-08-05 20:47:15",
                "updated_at": 1691234567,
                "scraped_at": "",
                "invalid_date": "not-a-date",
                "traffic": 5000
            }
        }
    ]
    
    # Tests des conversions individuelles
    print("\n🔍 TESTS DE CONVERSION INDIVIDUELLE")
    print("-" * 40)
    
    individual_tests = [
        "2025-08-05T19:40:56.053Z",
        "2025-08-05T19:40:56.053",
        "2025-08-05 20:47:15.852714",
        "2025-08-05T19:40:56",
        "2025-08-05 20:47:15",
        "2025-08-05",
        "1691234567",
        "1691234567890",
        None,
        "",
        "invalid_date"
    ]
    
    for test_input in individual_tests:
        result = DateConverter.convert_to_iso8601_utc(test_input)
        is_valid = DateConverter.validate_iso8601_utc(result) if result else False
        
        print(f"Input: {test_input}")
        print(f"Output: {result}")
        print(f"Valid: {is_valid}")
        print("-" * 30)
    
    # Tests des conversions de dictionnaires
    print("\n🔍 TESTS DE CONVERSION DE DICTIONNAIRES")
    print("-" * 40)
    
    for test_case in api_test_cases:
        print(f"\n📋 {test_case['name']}")
        print("Avant conversion:")
        for key, value in test_case['data'].items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        # Convertir les dates
        converted_data = convert_api_response_dates(test_case['data'])
        
        print("Après conversion:")
        for key, value in converted_data.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        # Valider les conversions
        date_fields = ['timestamp', 'created_at', 'updated_at', 'scraped_at', 'creation_date', 'year_founded']
        print("Validation:")
        for field in date_fields:
            if field in converted_data and converted_data[field]:
                is_valid = DateConverter.validate_iso8601_utc(converted_data[field])
                print(f"  {field}: {'✅' if is_valid else '❌'} {converted_data[field]}")
        
        print("-" * 50)
    
    # Tests de performance
    print("\n⚡ TESTS DE PERFORMANCE")
    print("-" * 40)
    
    import time
    
    # Test avec beaucoup de conversions
    test_data = {
        "timestamp": "2025-08-05T19:40:56.053Z",
        "created_at": "2025-08-05 20:47:15.852714",
        "updated_at": "2025-08-05T19:40:56",
        "scraped_at": "2025-08-05 20:47:15",
        "traffic": 15000
    }
    
    start_time = time.time()
    for i in range(1000):
        convert_api_response_dates(test_data)
    end_time = time.time()
    
    print(f"1000 conversions: {end_time - start_time:.4f} secondes")
    print(f"Temps moyen par conversion: {(end_time - start_time) / 1000 * 1000:.2f} ms")
    
    print("\n✅ TOUS LES TESTS TERMINÉS")

if __name__ == "__main__":
    test_date_conversions()
