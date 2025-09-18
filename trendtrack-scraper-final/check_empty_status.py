import sqlite3
conn = sqlite3.connect('data/trendtrack.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM shops WHERE scraping_status = ""')
count_empty = cursor.fetchone()[0]
print(f'Nombre de boutiques avec statut vide: {count_empty}')
cursor.execute('SELECT id, shop_name, scraping_status FROM shops WHERE scraping_status = ""')
results = cursor.fetchall()
for result in results:
    print(f'ID {result[0]}: {result[1]} - Status: "{result[2]}"')
conn.close()
