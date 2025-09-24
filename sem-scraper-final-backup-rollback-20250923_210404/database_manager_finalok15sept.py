"""
DatabaseManager - Gestionnaire unifié pour accès base de données
Centralise tous les accès à la base SQLite via TrendTrackAPI
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin racine pour importer trendtrack_api
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from trendtrack_api import TrendTrackAPI, get_database_path

class DatabaseManager:
    """Gestionnaire unifié de base de données"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or get_database_path()
        self.api = TrendTrackAPI(self.db_path)
    
    def get_all_shops(self):
        return self.api.get_all_shops()
    
    def get_shop_by_domain(self, domain):
        return self.api.get_shop_by_domain(domain)
    
    def add_shop(self, domain, name=None):
        return self.api.add_shop(domain, name)
    
    def update_shop_analytics(self, shop_id, analytics_data):
        return self.api.update_shop_analytics(shop_id, analytics_data)
    
    def get_shops_with_analytics(self, limit=None):
        return self.api.get_all_shops_with_analytics(limit)

_db_manager = None

def get_db_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
