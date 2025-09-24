#!/usr/bin/env python3
"""
Script de migration pour ajouter le Paid Search Traffic
"""

import sqlite3
import os
from datetime import datetime, timezone

# Configuration
DB_PATH = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"

def backup_database():
    """Sauvegarde la base de données avant modification"""
    timestamp = datetime.now(timezone.utc).isoformat()
    backup_path = f"/home/ubuntu/trendtrack-scraper-final/data/trendtrack_backup_before_paid_traffic_{timestamp}.db"
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return None

def add_paid_search_traffic_column():
    """Ajoute la colonne paid_search_traffic à la table analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔍 Vérification de la structure actuelle...")
        
        # Vérifier si la table analytics existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics'")
        if not cursor.fetchone():
            print("❌ Table analytics n'existe pas")
            return False
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(analytics)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Colonnes existantes: {columns}")
        
        # Vérifier si la colonne paid_search_traffic existe déjà
        if 'paid_search_traffic' in columns:
            print("ℹ️ Colonne paid_search_traffic existe déjà")
            return True
        
        # Ajouter la colonne
        print("🔧 Ajout de la colonne paid_search_traffic...")
        cursor.execute("ALTER TABLE analytics ADD COLUMN paid_search_traffic TEXT")
        conn.commit()
        
        # Vérifier que la colonne a été ajoutée
        cursor.execute("PRAGMA table_info(analytics)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Nouvelles colonnes: {new_columns}")
        
        if 'paid_search_traffic' in new_columns:
            print("✅ Colonne paid_search_traffic ajoutée avec succès")
            return True
        else:
            print("❌ Erreur: colonne non ajoutée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Vérifie que la migration s'est bien passée"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier la structure finale
        cursor.execute("PRAGMA table_info(analytics)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("\n📋 VÉRIFICATION FINALE:")
        print("=" * 50)
        print(f"Colonnes de la table analytics: {columns}")
        
        # Vérifier que paid_search_traffic est présent
        if 'paid_search_traffic' in columns:
            print("✅ Migration réussie!")
            
            # Compter les enregistrements
            cursor.execute("SELECT COUNT(*) FROM analytics")
            count = cursor.fetchone()[0]
            print(f"📊 Nombre d'enregistrements analytics: {count}")
            
            return True
        else:
            print("❌ Migration échouée: colonne manquante")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Point d'entrée principal"""
    print("🚀 MIGRATION PAID SEARCH TRAFFIC")
    print("=" * 50)
    
    # Vérifier que la DB existe
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return
    
    print(f"📁 Base de données: {DB_PATH}")
    
    # 1. Sauvegarde
    print("\n1️⃣ SAUVEGARDE")
    backup_path = backup_database()
    if not backup_path:
        print("⚠️ Continuation sans sauvegarde...")
    
    # 2. Migration
    print("\n2️⃣ MIGRATION")
    success = add_paid_search_traffic_column()
    
    if success:
        # 3. Vérification
        print("\n3️⃣ VÉRIFICATION")
        verify_migration()
        
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("Vous pouvez maintenant mettre à jour le scraper et l'API")
    else:
        print("\n❌ MIGRATION ÉCHOUÉE!")
        if backup_path:
            print(f"Vous pouvez restaurer depuis: {backup_path}")

if __name__ == "__main__":
    main()
