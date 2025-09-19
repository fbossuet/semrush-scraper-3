#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes live_ads_7d et live_ads_30d
Date: 2025-09-19
Description: Migration sécurisée avec backup automatique
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Créer une sauvegarde de la base de données"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Sauvegarde créée: {backup_path}")
    return backup_path

def check_column_exists(cursor, table_name, column_name):
    """Vérifier si une colonne existe déjà"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database(db_path):
    """Exécuter la migration"""
    print(f"🔄 Début de la migration de {db_path}")
    
    # Créer une sauvegarde
    backup_path = backup_database(db_path)
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        if check_column_exists(cursor, 'shops', 'live_ads_7d'):
            print("⚠️  La colonne live_ads_7d existe déjà")
        else:
            cursor.execute("ALTER TABLE shops ADD COLUMN live_ads_7d INTEGER DEFAULT 0")
            print("✅ Colonne live_ads_7d ajoutée")
        
        if check_column_exists(cursor, 'shops', 'live_ads_30d'):
            print("⚠️  La colonne live_ads_30d existe déjà")
        else:
            cursor.execute("ALTER TABLE shops ADD COLUMN live_ads_30d INTEGER DEFAULT 0")
            print("✅ Colonne live_ads_30d ajoutée")
        
        # Valider les changements
        conn.commit()
        
        # Vérifier la structure
        cursor.execute("PRAGMA table_info(shops)")
        columns = cursor.fetchall()
        print("\n📋 Structure de la table shops après migration:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Vérifier que les nouvelles colonnes sont présentes
        column_names = [col[1] for col in columns]
        if 'live_ads_7d' in column_names and 'live_ads_30d' in column_names:
            print("\n✅ Migration réussie ! Les colonnes live_ads_7d et live_ads_30d ont été ajoutées")
        else:
            raise Exception("❌ Échec de la migration - colonnes manquantes")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        print(f"🔄 Restauration depuis la sauvegarde: {backup_path}")
        shutil.copy2(backup_path, db_path)
        print("✅ Base de données restaurée")
        raise

if __name__ == "__main__":
    # Chemin relatif vers la base de données
    db_path = "trendtrack.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        exit(1)
    
    try:
        migrate_database(db_path)
        print("\n🎉 Migration terminée avec succès !")
    except Exception as e:
        print(f"\n💥 Migration échouée: {e}")
        exit(1)

