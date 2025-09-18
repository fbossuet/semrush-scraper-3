#!/usr/bin/env python3
"""
Script de sauvegarde des données de boutiques en base
Appelé depuis le scraper JavaScript TrendTrack
"""

import sys
import json
import os
from pathlib import Path

# Ajouter le chemin racine pour importer trendtrack_api
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from trendtrack_api import TrendTrackAPI

def save_shop_data(shop_data_json):
    """Sauvegarde les données d'une boutique en base"""
    try:
        # Parser les données JSON
        shop_data = json.loads(shop_data_json)
        
        # Initialiser l'API
        api = TrendTrackAPI('../trendtrack-scraper-final/data/trendtrack.db')
        
        # Préparer les données pour l'API
        shop_info = {
            'shop_name': shop_data.get('shopName', ''),
            'shop_url': shop_data.get('shopUrl', ''),
            'monthly_visits': shop_data.get('monthlyVisits', ''),
            'monthly_revenue': shop_data.get('monthlyRevenue', ''),
            'live_ads': shop_data.get('liveAds', ''),
            'creation_date': shop_data.get('creationDate', ''),
            'page_number': shop_data.get('page', ''),
            'project_source': 'trendtrack_scraper',
            'year_founded': shop_data.get('yearFounded', None)
        }
        
        # Vérifier si la boutique existe déjà
        domain = shop_info['shop_url'].replace('https://', '').replace('http://', '').replace('www.', '')
        existing_shop = api.get_shop_by_domain(domain)
        
        if existing_shop:
            print(f"⏭️ Boutique déjà existante: {shop_info['shop_name']} - Mise à jour")
            
            # Mettre à jour l'année de fondation si elle n'existe pas
            if shop_info['year_founded'] and not existing_shop.get('year_founded'):
                success = api.update_year_founded(existing_shop['id'], shop_info['year_founded'])
                if success:
                    print(f"📅 Année de fondation mise à jour: {shop_info['year_founded']}")
                    return {'status': 'updated', 'shop_id': existing_shop['id']}
                else:
                    return {'status': 'error', 'message': 'Erreur mise à jour année de fondation'}
            else:
                return {'status': 'skipped', 'shop_id': existing_shop['id']}
        else:
            # Ajouter la nouvelle boutique
            success = api.add_shop(shop_info)
            if success:
                print(f"✅ Nouvelle boutique ajoutée: {shop_info['shop_name']}")
                return {'status': 'added', 'shop_id': None}
            else:
                return {'status': 'error', 'message': 'Erreur ajout boutique'}
                
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return {'status': 'error', 'message': str(e)}

def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python3 save_shop_data.py '<json_data>'")
        sys.exit(1)
    
    shop_data_json = sys.argv[1]
    result = save_shop_data(shop_data_json)
    
    # Retourner le résultat en JSON pour le scraper JavaScript
    print(json.dumps(result))

if __name__ == "__main__":
    main()
