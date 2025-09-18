#!/usr/bin/env python3
"""
Script d'audit complet de la base de données
Analyse toutes les tables et identifie tous les problèmes
"""

import sqlite3
import requests
import json
from collections import Counter

def audit_database():
    print("🔍 AUDIT COMPLET DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    # Connexion à la base
    db_path = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. ANALYSE DES TABLES
        print("📊 1. ANALYSE DES TABLES")
        print("-" * 40)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} lignes")
        
        print()
        
        # 2. ANALYSE DE LA TABLE SHOPS
        print("🏪 2. ANALYSE DE LA TABLE SHOPS")
        print("-" * 40)
        
        # Statuts par boutique
        cursor.execute("""
            SELECT scraping_status, COUNT(*) as count 
            FROM shops 
            GROUP BY scraping_status 
            ORDER BY count DESC
        """)
        
        status_counts = cursor.fetchall()
        print("📊 Répartition par statut:")
        for status, count in status_counts:
            status_display = f"'{status}'" if status else "Vide"
            print(f"  {status_display}: {count} boutiques")
        
        # Boutiques sans statut
        cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status IS NULL OR scraping_status = ''")
        no_status = cursor.fetchone()[0]
        if no_status > 0:
            print(f"  ⚠️  Boutiques sans statut: {no_status}")
        
        print()
        
        # 3. ANALYSE DE LA TABLE ANALYTICS
        print("📈 3. ANALYSE DE LA TABLE ANALYTICS")
        print("-" * 40)
        
        # Compter les entrées par boutique
        cursor.execute("""
            SELECT shop_id, COUNT(*) as entries 
            FROM analytics 
            GROUP BY shop_id 
            ORDER BY entries DESC
        """)
        
        entries_per_shop = cursor.fetchall()
        print("📊 Entrées par boutique:")
        
        duplicate_shops = []
        for shop_id, entries in entries_per_shop:
            if entries > 1:
                duplicate_shops.append((shop_id, entries))
                print(f"  Shop {shop_id}: {entries} entrées (DOUBLONS!)")
        
        if not duplicate_shops:
            print("  ✅ Aucun doublon détecté")
        
        # Total des entrées
        cursor.execute("SELECT COUNT(*) FROM analytics")
        total_analytics = cursor.fetchone()[0]
        print(f"  Total entrées analytics: {total_analytics}")
        
        print()
        
        # 4. ANALYSE DES MÉTRIQUES MANQUANTES
        print("🎯 4. ANALYSE DES MÉTRIQUES MANQUANTES")
        print("-" * 40)
        
        # Récupérer toutes les boutiques avec leurs analytics
        cursor.execute("""
            SELECT s.id, s.shop_name, s.scraping_status,
                   a.organic_traffic, a.bounce_rate, a.avg_visit_duration,
                   a.branded_traffic, a.conversion_rate, a.paid_search_traffic,
                   a.visits, a.traffic, a.percent_branded_traffic
            FROM shops s
            LEFT JOIN (
                SELECT shop_id, 
                       MAX(organic_traffic) as organic_traffic,
                       MAX(bounce_rate) as bounce_rate,
                       MAX(avg_visit_duration) as avg_visit_duration,
                       MAX(branded_traffic) as branded_traffic,
                       MAX(conversion_rate) as conversion_rate,
                       MAX(paid_search_traffic) as paid_search_traffic,
                       MAX(visits) as visits,
                       MAX(traffic) as traffic,
                       MAX(percent_branded_traffic) as percent_branded_traffic
                FROM analytics 
                GROUP BY shop_id
            ) a ON s.id = a.shop_id
            ORDER BY s.id
        """)
        
        shops_data = cursor.fetchall()
        
        # Analyser les métriques manquantes
        metrics = ['organic_traffic', 'bounce_rate', 'avg_visit_duration', 
                  'branded_traffic', 'conversion_rate', 'paid_search_traffic', 
                  'visits', 'traffic', 'percent_branded_traffic']
        
        missing_counts = {metric: 0 for metric in metrics}
        total_shops = len(shops_data)
        
        for shop_data in shops_data:
            for i, metric in enumerate(metrics):
                value = shop_data[3 + i]  # Les métriques commencent à l'index 3
                if not value or value == '' or value == 'null' or value == 'None':
                    missing_counts[metric] += 1
        
        print("📊 Métriques manquantes (après déduplication):")
        for metric, count in missing_counts.items():
            percentage = count / total_shops * 100
            print(f"  {metric}: {count}/{total_shops} ({percentage:.1f}%)")
        
        print()
        
        # 5. ANALYSE DES INCOHÉRENCES
        print("⚠️  5. ANALYSE DES INCOHÉRENCES")
        print("-" * 40)
        
        issues = []
        
        # Boutiques avec statut "partial" mais aucune métrique
        cursor.execute("""
            SELECT s.id, s.shop_name, s.scraping_status
            FROM shops s
            LEFT JOIN (
                SELECT shop_id, 
                       MAX(organic_traffic) as organic_traffic,
                       MAX(paid_search_traffic) as paid_search_traffic
                FROM analytics 
                GROUP BY shop_id
            ) a ON s.id = a.shop_id
            WHERE s.scraping_status = 'partial' 
            AND (a.organic_traffic IS NULL OR a.organic_traffic = '')
            AND (a.paid_search_traffic IS NULL OR a.paid_search_traffic = '')
        """)
        
        partial_no_metrics = cursor.fetchall()
        if partial_no_metrics:
            issues.append(f"Boutiques 'partial' sans métriques: {len(partial_no_metrics)}")
            print(f"  ❌ Boutiques 'partial' sans métriques: {len(partial_no_metrics)}")
        
        # Boutiques avec statut "failed" mais des métriques
        cursor.execute("""
            SELECT s.id, s.shop_name, s.scraping_status
            FROM shops s
            LEFT JOIN (
                SELECT shop_id, 
                       MAX(organic_traffic) as organic_traffic
                FROM analytics 
                GROUP BY shop_id
            ) a ON s.id = a.shop_id
            WHERE s.scraping_status = 'failed' 
            AND a.organic_traffic IS NOT NULL 
            AND a.organic_traffic != ''
        """)
        
        failed_with_metrics = cursor.fetchall()
        if failed_with_metrics:
            issues.append(f"Boutiques 'failed' avec métriques: {len(failed_with_metrics)}")
            print(f"  ❌ Boutiques 'failed' avec métriques: {len(failed_with_metrics)}")
        
        # Boutiques avec statut "na" (problématique)
        cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = 'na'")
        na_count = cursor.fetchone()[0]
        if na_count > 0:
            issues.append(f"Boutiques avec statut 'na': {na_count}")
            print(f"  ⚠️  Boutiques avec statut 'na': {na_count}")
        
        if not issues:
            print("  ✅ Aucune incohérence majeure détectée")
        
        print()
        
        # 6. RECOMMANDATIONS
        print("💡 6. RECOMMANDATIONS")
        print("-" * 40)
        
        if duplicate_shops:
            print("  🔧 NETTOYER LES DOUBLONS:")
            print("    - Supprimer les entrées en double dans analytics")
            print("    - Garder seulement la dernière entrée par boutique")
        
        if na_count > 0:
            print("  🔧 TRAITER LES STATUTS 'na':")
            print("    - Identifier pourquoi ces boutiques ont ce statut")
            print("    - Les reclasser en 'pending' ou 'partial'")
        
        if partial_no_metrics:
            print("  🔧 CORRIGER LES 'partial' SANS MÉTRIQUES:")
            print("    - Reclasser en 'pending' ou 'failed'")
            print("    - Ou relancer le scraping sur ces boutiques")
        
        print()
        print("  📊 STATISTIQUES GLOBALES:")
        print(f"    - Total boutiques: {total_shops}")
        print(f"    - Total entrées analytics: {total_analytics}")
        print(f"    - Entrées dupliquées: {sum(entries for _, entries in duplicate_shops)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'audit: {e}")

if __name__ == "__main__":
    audit_database()
