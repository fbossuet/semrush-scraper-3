#!/usr/bin/env python3
import sqlite3
import re

def standardize_errors():
    db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Standardisation des valeurs d'erreur...")
    
    # PATTERNS À REMPLACER
    error_patterns = [
        r'Sélecteur non trouvé\|Erreur',
        r'Sélecteur non trouvé: .*',
        r'Domaine non trouvé',
        r'Erreur: .*',
        r'Timeout .*',
        r'Erreur de connexion',
        r'Page non accessible'
    ]
    
    # VALEUR STANDARDISÉE
    standard_error = 'na'
    
    # MÉTRIQUES À NETTOYER
    metrics = [
        'organic_traffic', 'bounce_rate', 'avg_visit_duration',
        'branded_traffic', 'conversion_rate', 'paid_search_traffic',
        'visits', 'traffic', 'percent_branded_traffic'
    ]
    
    total_updated = 0
    
    for metric in metrics:
        print(f"  📊 Nettoyage de {metric}...")
        
        # Compter les valeurs problématiques
        cursor.execute(f"""
            SELECT COUNT(*) FROM analytics 
            WHERE {metric} LIKE '%Sélecteur non trouvé%' 
            OR {metric} LIKE '%Domaine non trouvé%'
            OR {metric} LIKE '%Erreur%'
            OR {metric} LIKE '%Timeout%'
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Remplacer toutes les erreurs par 'na'
            cursor.execute(f"""
                UPDATE analytics 
                SET {metric} = ? 
                WHERE {metric} LIKE '%Sélecteur non trouvé%' 
                OR {metric} LIKE '%Domaine non trouvé%'
                OR {metric} LIKE '%Erreur%'
                OR {metric} LIKE '%Timeout%'
            """, (standard_error,))
            
            updated = cursor.rowcount
            total_updated += updated
            print(f"    ✅ {updated} valeurs corrigées")
        else:
            print(f"    ✅ Aucune valeur problématique")
    
    # Nettoyer les champs vides (NULL ou chaînes vides)
    print("  🧹 Nettoyage des champs vides...")
    
    for metric in metrics:
        cursor.execute(f"""
            UPDATE analytics 
            SET {metric} = ? 
            WHERE {metric} IS NULL 
            OR {metric} = '' 
            OR {metric} = 'null'
        """, (standard_error,))
        
        updated = cursor.rowcount
        total_updated += updated
        print(f"    ✅ {metric}: {updated} valeurs vides → 'na'")
    
    conn.commit()
    
    print(f"\n🎯 TOTAL: {total_updated} valeurs standardisées")
    
    # VÉRIFIER LE RÉSULTAT
    print("\n🔍 Vérification des valeurs après nettoyage...")
    
    for metric in metrics:
        cursor.execute(f"""
            SELECT {metric}, COUNT(*) as count
            FROM analytics 
            GROUP BY {metric}
            ORDER BY count DESC
            LIMIT 5
        """)
        
        print(f"  📊 {metric}:")
        for value, count in cursor.fetchall():
            print(f"    '{value}': {count}")
    
    conn.close()

if __name__ == "__main__":
    standardize_errors()
