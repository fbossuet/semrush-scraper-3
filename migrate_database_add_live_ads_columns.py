#!/usr/bin/env python3
"""
Migration pour ajouter les colonnes live_ads_7d et live_ads_30d à la table shops
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Ajoute les colonnes live_ads_7d et live_ads_30d à la table shops"""
    
    # Chemin vers la base de données (à adapter selon votre configuration)
    db_paths = [
        "trendtrack.db",
        "test_trendtrack.db",
        "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/trendtrack.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"🔄 Migration de la base de données: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Vérifier si les colonnes existent déjà
                cursor.execute("PRAGMA table_info(shops)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Ajouter live_ads_7d si elle n'existe pas
                if 'live_ads_7d' not in columns:
                    cursor.execute("ALTER TABLE shops ADD COLUMN live_ads_7d NUMERIC")
                    print("✅ Colonne live_ads_7d ajoutée")
                else:
                    print("ℹ️ Colonne live_ads_7d existe déjà")
                
                # Ajouter live_ads_30d si elle n'existe pas
                if 'live_ads_30d' not in columns:
                    cursor.execute("ALTER TABLE shops ADD COLUMN live_ads_30d NUMERIC")
                    print("✅ Colonne live_ads_30d ajoutée")
                else:
                    print("ℹ️ Colonne live_ads_30d existe déjà")
                
                conn.commit()
                conn.close()
                
                print(f"✅ Migration terminée pour {db_path}")
                
            except Exception as e:
                print(f"❌ Erreur migration {db_path}: {e}")
        else:
            print(f"⚠️ Base de données non trouvée: {db_path}")

if __name__ == "__main__":
    print("🔄 Migration des colonnes live_ads_7d et live_ads_30d...")
    migrate_database()
    print("🎉 Migration terminée !")