#!/usr/bin/env python3
"""
Script de debug pour analyser l'erreur update_shop_analytics
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from trendtrack_api import TrendTrackAPI

# Test de l'API
api = TrendTrackAPI()

# Test 1: Appel correct
print("=== TEST 1: Appel correct ===")
try:
    test_data = {
        "organic_traffic": "1000",
        "bounce_rate": "0.5",
        "average_visit_duration": "120"
    }
    result = api.update_shop_analytics(2595, test_data)
    print(f"✅ Appel correct réussi: {result}")
except Exception as e:
    print(f"❌ Erreur appel correct: {e}")

# Test 2: Appel avec seulement shop_id (reproduire l'erreur)
print("\n=== TEST 2: Appel avec seulement shop_id ===")
try:
    result = api.update_shop_analytics(2595)  # Manque analytics_data
    print(f"✅ Appel incorrect réussi: {result}")
except Exception as e:
    print(f"❌ Erreur appel incorrect: {e}")
    print(f"Type d'erreur: {type(e)}")

# Test 3: Appel avec analytics_data = None
print("\n=== TEST 3: Appel avec analytics_data = None ===")
try:
    result = api.update_shop_analytics(2595, None)
    print(f"✅ Appel None réussi: {result}")
except Exception as e:
    print(f"❌ Erreur appel None: {e}")

# Test 4: Vérifier la signature de la fonction
print("\n=== TEST 4: Signature de la fonction ===")
import inspect
signature = inspect.signature(api.update_shop_analytics)
print(f"Signature: {signature}")
print(f"Paramètres: {list(signature.parameters.keys())}")








