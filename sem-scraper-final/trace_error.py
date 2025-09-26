#!/usr/bin/env python3
"""
Script pour tracer exactement où se produit l'erreur update_shop_analytics
"""

import sys
import os
import traceback
sys.path.insert(0, os.getcwd())

# Patcher la fonction update_shop_analytics pour tracer tous les appels
from trendtrack_api import TrendTrackAPI

# Sauvegarder la fonction originale
original_update_shop_analytics = TrendTrackAPI.update_shop_analytics

def patched_update_shop_analytics(self, *args, **kwargs):
    """Version patchée qui trace tous les appels"""
    print(f"\n🔍 TRACE: update_shop_analytics appelé avec:")
    print(f"   - args: {args}")
    print(f"   - kwargs: {kwargs}")
    print(f"   - Nombre d'args: {len(args)}")
    
    # Afficher la stack trace pour voir d'où vient l'appel
    print("📍 Stack trace:")
    for line in traceback.format_stack()[-3:-1]:  # Ignorer les 2 dernières lignes (cette fonction)
        print(f"   {line.strip()}")
    
    # Vérifier si on a le bon nombre d'arguments
    if len(args) < 2:
        print(f"❌ ERREUR DÉTECTÉE: Pas assez d'arguments (attendu: 2, reçu: {len(args)})")
        raise TypeError(f"update_shop_analytics() missing 1 required positional argument: 'analytics_data'")
    
    # Appeler la fonction originale
    return original_update_shop_analytics(self, *args, **kwargs)

# Patcher la classe
TrendTrackAPI.update_shop_analytics = patched_update_shop_analytics

# Maintenant tester avec le scraper
print("=== TEST AVEC LE SCRAPER ===")
try:
    from production_scraper_parallel import ParallelProductionScraper
    
    # Créer un worker de test
    worker = ParallelProductionScraper(0)
    
    # Simuler des données de session
    worker.session_data = {
        'data': {
            'domain_overview': {
                'conversion_rate': '0.013',
                'organic_search_traffic': '1000',
                'bounce_rate': '0.5'
            }
        }
    }
    
    # Tester format_analytics_for_api
    analytics_data = worker.format_analytics_for_api()
    print(f"Analytics data: {analytics_data}")
    
    # Tester l'appel direct
    api = TrendTrackAPI()
    if analytics_data:
        api.update_shop_analytics(2595, analytics_data)
        print("✅ Appel direct réussi")
    else:
        print("⚠️ Analytics data vide")
        
except Exception as e:
    print(f"❌ Erreur pendant le test: {e}")
    print(f"Type: {type(e)}")
    traceback.print_exc()






