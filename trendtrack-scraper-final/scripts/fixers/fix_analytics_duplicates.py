#!/usr/bin/env python3
"""
Script pour nettoyer les doublons dans la table analytics et corriger la structure
"""

import sqlite3
from datetime import datetime, timezone
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_analytics_duplicates():
    """Nettoie les doublons et corrige la structure de la table analytics"""
    
    print("🔧 CORRECTION DES DOUBLONS DANS LA TABLE ANALYTICS")
    print("=" * 60)
    
    try:
        # Connexion à la base
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        
        print("\n📊 ANALYSE DE LA SITUATION ACTUELLE:")
        
        # Compter les entrées totales
        cursor.execute("SELECT COUNT(*) FROM analytics")
        total_entries = cursor.fetchone()[0]
        print(f"   Total des entrées: {total_entries}")
        
        # Compter les boutiques uniques
        cursor.execute("SELECT COUNT(DISTINCT shop_id) FROM analytics")
        unique_shops = cursor.fetchone()[0]
        print(f"   Boutiques uniques: {unique_shops}")
        
        # Compter les doublons
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT shop_id, COUNT(*) as count 
                FROM analytics 
                GROUP BY shop_id 
                HAVING COUNT(*) > 1
            )
        """)
        shops_with_duplicates = cursor.fetchone()[0]
        print(f"   Boutiques avec doublons: {shops_with_duplicates}")
        
        # Calculer l'espace perdu
        wasted_entries = total_entries - unique_shops
        print(f"   Entrées perdues (doublons): {wasted_entries}")
        
        print("\n🧹 PHASE 1: NETTOYAGE DES DOUBLONS")
        
        # Identifier les doublons pour chaque boutique
        cursor.execute("""
            SELECT shop_id, COUNT(*) as count 
            FROM analytics 
            GROUP BY shop_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        total_cleaned = 0
        
        for shop_id, count in duplicates:
            print(f"   Boutique {shop_id}: {count} entrées → nettoyage...")
            
            # Récupérer toutes les entrées pour cette boutique
            cursor.execute("""
                SELECT id, updated_at, paid_search_traffic, organic_traffic, scraping_status
                FROM analytics 
                WHERE shop_id = ? 
                ORDER BY updated_at DESC
            """, (shop_id,))
            
            entries = cursor.fetchall()
            
            # Garder la première entrée (la plus récente) et supprimer les autres
            if entries:
                keep_id = entries[0][0]  # ID de la première entrée (la plus récente)
                
                # Supprimer les autres entrées
                cursor.execute("""
                    DELETE FROM analytics 
                    WHERE shop_id = ? AND id != ?
                """, (shop_id, keep_id))
                
                deleted_count = cursor.rowcount
                total_cleaned += deleted_count
                print(f"      ✅ {deleted_count} doublons supprimés, gardé ID {keep_id}")
        
        print(f"\n✅ NETTOYAGE TERMINÉ: {total_cleaned} doublons supprimés")
        
        print("\n🔧 PHASE 2: CORRECTION DE LA STRUCTURE")
        
        # Vérifier la structure actuelle
        cursor.execute("PRAGMA table_info(analytics)")
        columns = cursor.fetchall()
        
        print("   Structure actuelle de la table analytics:")
        for col in columns:
            print(f"      - {col[1]} ({col[2]}) - PK: {col[5]}")
        
        # Ajouter une contrainte unique sur shop_id si elle n'existe pas
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX idx_analytics_shop_id_unique 
                ON analytics(shop_id)
            """)
            print("   ✅ Contrainte unique ajoutée sur shop_id")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("   ℹ️ Contrainte unique sur shop_id déjà existante")
            else:
                print(f"   ⚠️ Erreur lors de l'ajout de la contrainte: {e}")
        
        # Vérifier le résultat final
        print("\n📊 VÉRIFICATION FINALE:")
        
        cursor.execute("SELECT COUNT(*) FROM analytics")
        final_total = cursor.fetchone()[0]
        print(f"   Total des entrées après nettoyage: {final_total}")
        
        cursor.execute("SELECT COUNT(DISTINCT shop_id) FROM analytics")
        final_unique = cursor.fetchone()[0]
        print(f"   Boutiques uniques après nettoyage: {final_unique}")
        
        space_saved = total_entries - final_total
        print(f"   Espace libéré: {space_saved} entrées supprimées")
        
        # Valider qu'il n'y a plus de doublons
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT shop_id, COUNT(*) as count 
                FROM analytics 
                GROUP BY shop_id 
                HAVING COUNT(*) > 1
            )
        """)
        remaining_duplicates = cursor.fetchone()[0]
        
        if remaining_duplicates == 0:
            print("   ✅ Aucun doublon restant - Nettoyage réussi!")
        else:
            print(f"   ⚠️ {remaining_duplicates} boutiques ont encore des doublons")
        
        # Commit des changements
        conn.commit()
        print("\n💾 Changements sauvegardés dans la base")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_analytics_duplicates()
