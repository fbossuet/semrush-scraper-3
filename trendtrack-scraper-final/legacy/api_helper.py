#!/usr/bin/env python3
"""
Helper script pour l'API - retourne les données JSON
"""

import sys
import json
sys.path.append('/home/ubuntu/trendtrack-scraper-final')
from trendtrack_api import TrendTrackAPI, get_database_path

def get_shops_with_analytics():
    """Récupérer toutes les boutiques avec analytics"""
    try:
        api = TrendTrackAPI(get_database_path())
        shops = api.get_all_shops_with_analytics()
        return json.dumps(shops)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    print(get_shops_with_analytics())
