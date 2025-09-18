#!/usr/bin/env python3
"""
Script pour récupérer les boutiques sans année de fondation
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin racine pour importer trendtrack_api
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from trendtrack_api import TrendTrackAPI

def get_shops_without_year_founded():
    """Récupère les boutiques sans année de fondation"""
    try:
        # Initialiser l'API
        api = TrendTrackAPI('../trendtrack-scraper-final/data/trendtrack.db')
        
        # Récupérer les boutiques sans année de fondation
        shops = api.get_shops_without_year_founded(limit=100)  # Limite pour le test
        
        # Retourner les données en JSON
        print(json.dumps(shops))
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    get_shops_without_year_founded()
