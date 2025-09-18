#!/usr/bin/env python3
"""
Script pour mettre à jour l'année de fondation d'une boutique
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin racine pour importer trendtrack_api
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from trendtrack_api import TrendTrackAPI

def update_year_founded(shop_id, year_founded):
    """Met à jour l'année de fondation d'une boutique"""
    try:
        # Initialiser l'API
        api = TrendTrackAPI('../trendtrack-scraper-final/data/trendtrack.db')
        
        # Mettre à jour l'année de fondation
        success = api.update_year_founded(int(shop_id), year_founded)
        
        if success:
            result = {'status': 'success', 'message': f'Année {year_founded} mise à jour pour boutique {shop_id}'}
        else:
            result = {'status': 'error', 'message': 'Erreur lors de la mise à jour'}
        
        # Retourner le résultat en JSON
        print(json.dumps(result))
        
    except Exception as e:
        result = {'status': 'error', 'message': str(e)}
        print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({'status': 'error', 'message': 'Usage: python3 update_year_founded.py <shop_id> <year_founded>'}))
        sys.exit(1)
    
    shop_id = sys.argv[1]
    year_founded = sys.argv[2]
    update_year_founded(shop_id, year_founded)
