import sqlite3
conn = sqlite3.connect('data/trendtrack.db')
cursor = conn.cursor()

# Compter toutes les boutiques en pending
cursor.execute('SELECT COUNT(*) FROM shops WHERE scraping_status = "pending"')
total_pending = cursor.fetchone()[0]
print(f'=== TOUTES LES BOUTIQUES EN PENDING ({total_pending} au total) ===')
print()

# Récupérer toutes les boutiques en pending
cursor.execute('SELECT id, shop_name, scraping_status FROM shops WHERE scraping_status = "pending" ORDER BY id')
pending_shops = cursor.fetchall()

print('📊 RÉSUMÉ DES MÉTRIQUES POUR TOUTES LES BOUTIQUES PENDING:')
print()

metrics_with_data = 0
metrics_empty = 0
shops_with_some_data = 0
shops_completely_empty = 0

for shop_id, shop_name, status in pending_shops:
    # Récupérer les analytics
    cursor.execute('SELECT * FROM analytics WHERE shop_id = ?', (shop_id,))
    analytics = cursor.fetchone()
    
    if analytics:
        # Récupérer les noms des colonnes
        cursor.execute('PRAGMA table_info(analytics)')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Compter les métriques non-vides
        non_empty_count = 0
        for i, col in enumerate(columns):
            if i == 0:  # Skip shop_id
                continue
            value = analytics[i] if i < len(analytics) else None
            if value is not None and value != '':
                non_empty_count += 1
                metrics_with_data += 1
            else:
                metrics_empty += 1
        
        if non_empty_count > 0:
            shops_with_some_data += 1
            print(f'✅ {shop_name} (ID: {shop_id}): {non_empty_count} métriques non-vides')
        else:
            shops_completely_empty += 1
            print(f'❌ {shop_name} (ID: {shop_id}): TOUTES les métriques vides')
    else:
        shops_completely_empty += 1
        print(f'❌ {shop_name} (ID: {shop_id}): Aucune donnée analytics')

print()
print('=== STATISTIQUES GLOBALES ===')
print(f'📊 Total boutiques pending: {total_pending}')
print(f'✅ Boutiques avec des données: {shops_with_some_data}')
print(f'❌ Boutiques complètement vides: {shops_completely_empty}')
print(f'📈 Métriques avec données: {metrics_with_data}')
print(f'📉 Métriques vides: {metrics_empty}')

conn.close()
