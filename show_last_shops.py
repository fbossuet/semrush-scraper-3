#!/usr/bin/env python3
"""
Script pour afficher les 50 dernières lignes ajoutées dans la table shops
"""

import sqlite3
import json
from datetime import datetime

def show_last_shops():
    """Affiche les 50 dernières boutiques ajoutées en base"""
    print("🏪 AFFICHAGE DES 50 DERNIÈRES BOUTIQUES AJOUTÉES")
    print("=" * 80)
    
    try:
        # Connexion à la base de données (VPS)
        db_path = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Requête pour récupérer les 50 dernières boutiques par ID (les plus récemment ajoutées)
        cursor.execute("""
            SELECT id, shop_name, shop_url, scraping_status, scraping_last_update, 
                   creation_date, category, monthly_visits, monthly_revenue, 
                   live_ads, page_number, scraped_at, project_source, 
                   external_id, metadata, updated_at
            FROM shops
            ORDER BY id DESC
            LIMIT 50
        """)
        
        shops = cursor.fetchall()
        
        if not shops:
            print("❌ Aucune boutique trouvée dans la base de données")
            return
        
        print(f"📊 {len(shops)} dernières boutiques trouvées:")
        print("-" * 80)
        
        for i, shop in enumerate(shops, 1):
            shop_id, shop_name, shop_url, scraping_status, scraping_last_update, \
            creation_date, category, monthly_visits, monthly_revenue, \
            live_ads, page_number, scraped_at, project_source, \
            external_id, metadata, updated_at = shop
            
            print(f"\n🔹 Boutique #{i} (ID: {shop_id})")
            print(f"   📛 Nom: {shop_name or 'N/A'}")
            print(f"   🌐 URL: {shop_url or 'N/A'}")
            print(f"   📊 Statut: {scraping_status or 'N/A'}")
            print(f"   📅 Création: {creation_date or 'N/A'}")
            print(f"   🏷️  Catégorie: {category or 'N/A'}")
            print(f"   👥 Visites mensuelles: {monthly_visits or 'N/A'}")
            print(f"   💰 Revenus mensuels: {monthly_revenue or 'N/A'}")
            print(f"   📱 Live Ads: {live_ads or 'N/A'}")
            print(f"   📄 Page: {page_number or 'N/A'}")
            print(f"   🔄 Dernière mise à jour: {scraping_last_update or 'N/A'}")
            print(f"   📝 Updated at: {updated_at or 'N/A'}")
            print(f"   🎯 Source: {project_source or 'N/A'}")
            print(f"   🆔 External ID: {external_id or 'N/A'}")
            
            if metadata:
                try:
                    metadata_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                    print(f"   📋 Métadonnées: {json.dumps(metadata_dict, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   📋 Métadonnées: {metadata}")
            
            print("-" * 40)
        
        # Statistiques supplémentaires
        print(f"\n📈 STATISTIQUES:")
        print("-" * 40)
        
        # Compter par statut
        cursor.execute("""
            SELECT scraping_status, COUNT(*) as count 
            FROM shops 
            WHERE id IN (SELECT id FROM shops ORDER BY id DESC LIMIT 50)
            GROUP BY scraping_status 
            ORDER BY count DESC
        """)
        
        status_counts = cursor.fetchall()
        print("📊 Répartition par statut (sur les 50 dernières):")
        for status, count in status_counts:
            status_display = f"'{status}'" if status else "Vide"
            print(f"   {status_display}: {count} boutiques")
        
        # Compter par catégorie
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM shops 
            WHERE id IN (SELECT id FROM shops ORDER BY id DESC LIMIT 50)
            AND category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        category_counts = cursor.fetchall()
        if category_counts:
            print("\n🏷️ Répartition par catégorie (sur les 50 dernières):")
            for category, count in category_counts:
                print(f"   {category}: {count} boutiques")
        
        conn.close()
        print(f"\n✅ Affichage terminé - {len(shops)} boutiques affichées")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'accès à la base de données: {e}")
        return False

if __name__ == "__main__":
    show_last_shops()
