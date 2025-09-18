import sqlite3
conn = sqlite3.connect('data/trendtrack.db')
cursor = conn.cursor()

# Récupérer toutes les boutiques en pending
cursor.execute('SELECT id, shop_name FROM shops WHERE scraping_status = "pending" ORDER BY id')
pending_shops = cursor.fetchall()

print('=== DÉTAIL DES MÉTRIQUES NON-VIDES POUR CHAQUE BOUTIQUE PENDING ===')
print()

for shop_id, shop_name in pending_shops:
    print(f'🏪 {shop_name} (ID: {shop_id}):')
    
    # Récupérer les analytics
    cursor.execute('SELECT * FROM analytics WHERE shop_id = ?', (shop_id,))
    analytics = cursor.fetchone()
    
    if analytics:
        # Récupérer les noms des colonnes
        cursor.execute('PRAGMA table_info(analytics)')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Afficher les métriques non-vides
        for i, col in enumerate(columns):
            if i == 0:  # Skip shop_id
                continue
            value = analytics[i] if i < len(analytics) else None
            if value is not None and value != '':
                print(f'   ✅ {col}: {value}')
            else:
                print(f'   ❌ {col}: (vide)')
    else:
        print('   ❌ Aucune donnée analytics')
    
    print()

conn.close()
