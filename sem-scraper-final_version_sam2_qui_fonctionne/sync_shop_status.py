#!/usr/bin/env python3
"""
Script pour synchroniser les statuts entre les tables shops et analytics
"""

import sqlite3
from datetime import datetime, timezone

def sync_shop_status():
    """Synchronise les statuts entre les tables shops et analytics"""
    db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 SYNCHRONISATION DES STATUTS ENTRE SHOPS ET ANALYTICS")
    print("=" * 60)
    
    # Récupérer tous les analytics avec leurs statuts
    cursor.execute("""
    SELECT shop_id, scraping_status
    FROM analytics
    """)
    analytics_status = cursor.fetchall()
    
    print(f"📊 Analytics trouvés: {len(analytics_status)}")
    
    # Compter les changements nécessaires
    updates_needed = 0
    null_to_empty = 0
    partial_updates = 0
    
    for shop_id, analytics_status_value in analytics_status:
        # Récupérer le statut actuel dans la table shops
        cursor.execute("SELECT scraping_status FROM shops WHERE id = ?", (shop_id,))
        result = cursor.fetchone()
        
        if result:
            current_shop_status = result[0]
            
            # Déterminer le nouveau statut
            if analytics_status_value is None:
                # Analytics en NULL -> shops en statut vide (NULL)
                new_status = None
                if current_shop_status != "partial":  # On garde partial si c'est déjà partial
                    updates_needed += 1
                    null_to_empty += 1
            else:
                # Analytics avec statut -> synchroniser avec shops
                new_status = analytics_status_value
                if current_shop_status != new_status:
                    updates_needed += 1
                    partial_updates += 1
            
            # Mettre à jour si nécessaire
            if new_status != current_shop_status:
                cursor.execute("""
                UPDATE shops 
                SET scraping_status = ?, scraping_last_update = ?
                WHERE id = ?
                """, (new_status, datetime.now(timezone.utc), shop_id))
                
                print(f"✅ Shop {shop_id}: {current_shop_status} -> {new_status}")
    
    # Valider les changements
    conn.commit()
    
    print(f"\n📊 RÉSUMÉ DES CHANGEMENTS:")
    print(f"   Mises à jour nécessaires: {updates_needed}")
    print(f"   NULL -> vide: {null_to_empty}")
    print(f"   Autres mises à jour: {partial_updates}")
    
    # Vérification finale
    print(f"\n🔍 VÉRIFICATION FINALE:")
    
    # Statuts dans shops
    cursor.execute("""
    SELECT 
        CASE 
            WHEN scraping_status IS NULL THEN "NULL"
            ELSE scraping_status 
        END as status,
        COUNT(*) as count
    FROM shops
    GROUP BY scraping_status
    ORDER BY count DESC
    """)
    shops_status_results = cursor.fetchall()
    
    print(f"📊 STATUTS DANS LA TABLE SHOPS:")
    for status, count in shops_status_results:
        print(f"   {status}: {count} shops")
    
    # Statuts dans analytics
    cursor.execute("""
    SELECT 
        CASE 
            WHEN scraping_status IS NULL THEN "NULL"
            ELSE scraping_status 
        END as status,
        COUNT(*) as count
    FROM analytics
    GROUP BY scraping_status
    ORDER BY count DESC
    """)
    analytics_status_results = cursor.fetchall()
    
    print(f"📊 STATUTS DANS LA TABLE ANALYTICS:")
    for status, count in analytics_status_results:
        print(f"   {status}: {count} shops")
    
    conn.close()
    print(f"\n🎉 Synchronisation terminée!")

if __name__ == "__main__":
    sync_shop_status()
