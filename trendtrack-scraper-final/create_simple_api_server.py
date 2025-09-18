#!/usr/bin/env python3
"""
Serveur API simple pour Trendtrack avec paid_search_traffic
"""

import sqlite3
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ajouter le chemin du projet
sys.path.append('/home/ubuntu/trendtrack-scraper-final')
from trendtrack_api import get_database_path

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS headers
        # self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if self.path == '/api/shops/with-analytics':
            self.handle_shops_with_analytics()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_shops_with_analytics(self):
        """Gérer l'endpoint /api/shops/with-analytics"""
        try:
            # Parser les paramètres de requête
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            limit = int(query_params.get('limit', [50])[0])
            page = int(query_params.get('page', [1])[0])
            offset = (page - 1) * limit
            
            # Connexion à la base de données
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Récupérer les boutiques avec pagination
            cursor.execute('''
                SELECT * FROM shops 
                ORDER BY id 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            shops = cursor.fetchall()
            
            # Pour chaque boutique, récupérer les analytics
            shops_with_analytics = []
            for shop in shops:
                shop_dict = dict(shop)
                
                # Récupérer les analytics
                cursor.execute('''
                    SELECT organic_traffic, bounce_rate, avg_visit_duration, 
                           branded_traffic, conversion_rate, paid_search_traffic, 
                           scraping_status, visits, traffic, percent_branded_traffic
                    FROM analytics 
                    WHERE shop_id = ?
                ''', (shop['id'],))
                
                analytics = cursor.fetchone()
                if analytics:
                    analytics_dict = dict(analytics)
                    shop_dict.update(analytics_dict)
                    shop_dict['analytics_scraping_status'] = analytics_dict['scraping_status']
                
                shops_with_analytics.append(shop_dict)
            
            # Compter le total
            cursor.execute('SELECT COUNT(*) as total FROM shops')
            total = cursor.fetchone()['total']
            
            conn.close()
            
            # Réponse
            response = {
                "success": True,
                "data": shops_with_analytics,
                "pagination": {
                    "page": page,
                    "pages": (total + limit - 1) // limit,
                    "total": total,
                    "limit": limit
                }
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def log_message(self, format, *args):
        """Désactiver les logs par défaut"""
        pass

def run_server(port=8000):
    """Démarrer le serveur"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"🚀 Serveur API démarré sur le port {port}")
    print(f"📊 Endpoint: http://localhost:{port}/api/shops/with-analytics")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
