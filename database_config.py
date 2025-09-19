#!/usr/bin/env python3
"""
Configuration des chemins de bases de données pour la branche test
"""

import os

# Répertoire de base de la branche test
TEST_BASE_DIR = "/home/ubuntu/projects/shopshopshops/test"

# Chemins des bases de données dans la branche test
DATABASE_PATHS = {
    "production": os.path.join(TEST_BASE_DIR, "trendtrack-scraper-final/data/trendtrack.db"),
    "test": os.path.join(TEST_BASE_DIR, "trendtrack-scraper-final/data/trendtrack_test.db")
}

# Configuration par défaut
DEFAULT_DATABASE = DATABASE_PATHS["production"]

def get_database_path(db_type="production"):
    """Retourne le chemin de la base de données demandée"""
    return DATABASE_PATHS.get(db_type, DEFAULT_DATABASE)

def get_all_database_paths():
    """Retourne tous les chemins de bases de données"""
    return DATABASE_PATHS

if __name__ == "__main__":
    print("Configuration des bases de données pour la branche test:")
    for db_type, path in DATABASE_PATHS.items():
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {db_type}: {path} {exists}")
