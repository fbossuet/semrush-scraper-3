# SEM Scraper - Guide de test rapide (conforme .cursorrules / specify)

## Pré-requis
- Branch: `test`
- Lancer depuis: `/home/ubuntu/projects/shopshopshops/test`
- BDD: chemins relatifs (production: `trendtrack-scraper-final/data/trendtrack.db`)
- Xvfb installé et utilisable (headless + DISPLAY=:99)

## Vérifications initiales
```bash
cd /home/ubuntu/projects/shopshopshops/test && ./check_workspace.sh | cat
python3 database_config.py | cat
```

## Préparation des boutiques de test
- Bodycakes (domaine léger) pour vérifier le flux général
- Nike (domaine riche) pour valider `organic.Summary`

```bash
cd sem-scraper-final
# Remettre bodycakes en statut vide (créé si absent)
python3 - << 'PY'
import sqlite3, datetime
db="../trendtrack-scraper-final/data/trendtrack.db"
conn=sqlite3.connect(db);cur=conn.cursor()
cur.execute("UPDATE shops SET scraping_status='' WHERE shop_url LIKE '%bodycakes.com%'")
if cur.rowcount==0:
    cur.execute("INSERT INTO shops (shop_name, shop_url, scraping_status, project_source, creation_date, updated_at, monthly_visits, year_founded, total_products, category, live_ads_7d, live_ads_30d) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ('BodyCakes','https://bodycakes.com','', 'test', datetime.datetime.utcnow().isoformat(), datetime.datetime.utcnow().isoformat(),0,0,0,'Health & Beauty',0,0))
conn.commit(); conn.close()
PY

# Ajouter nike.com si absent (statut vide)
python3 - << 'PY'
import sqlite3, datetime
db="../trendtrack-scraper-final/data/trendtrack.db"
conn=sqlite3.connect(db);cur=conn.cursor()
cur.execute("SELECT id FROM shops WHERE shop_url LIKE '%nike.com%'")
if not cur.fetchone():
    cur.execute("INSERT INTO shops (shop_name, shop_url, scraping_status, project_source, creation_date, updated_at, monthly_visits, year_founded, total_products, category, live_ads_7d, live_ads_30d) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ('Nike','https://nike.com','', 'test', datetime.datetime.utcnow().isoformat(), datetime.datetime.utcnow().isoformat(),0,0,0,'Sportswear',0,0))
conn.commit(); conn.close()
PY
```

## Lancement des tests

### 1) Test ciblé bodycakes (statut empty)
```bash
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
python3 launch_workers_by_status.py empty --workers 1 --max-per-worker 1 > test_sem_bodycakes.log 2>&1 &
sleep 20 && tail -n 200 test_sem_bodycakes.log | cat
```
Attendus:
- Auth OK (app.mytoolsplan.com), Xvfb actif, headless=True
- organic.Summary: peut renvoyer vide pour ce domaine
- organic.OverviewTrend: traffic/branded/cpc (0 possibles)
- Conversion: via sélecteur `summary-cell conversion` (peut être `0.0`)
- Écriture statut: `partial` côté worker (statut final décidé par `trendtrack_api.py`)

### 2) Test ciblé nike (statut empty)
```bash
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
python3 launch_workers_by_status.py empty --workers 1 --max-per-worker 1 > test_sem_nike.log 2>&1 &
sleep 25 && tail -n 200 test_sem_nike.log | cat
```
Attendus:
- organic.Summary: valeurs non nulles (organic, paid)
- Engagement API: valeurs bounce/duration si accessible
- OverviewTrend: traffic, branded, cpc
- Conversion: peut rester vide selon page; si visible, parsing en décimal
- Écriture statut worker: `partial`

## Points de conformité (résumé)
- Headless activé + Xvfb (DISPLAY=:99)
- User-Agent Chrome récent
- Credentials: centralisés (`api_credentials.py`), capture dynamique (fetch/XHR) et synchro backend
- Pas de forçage de statut `completed` dans le worker
- Conversion: extraction par sélecteur stable
- Chemins BDD relatifs, logs immuables

## Nettoyage post-validation
```bash
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
rm -f test_sem_bodycakes.log test_sem_nike.log
```

Ne pas supprimer d’autres fichiers sans validation explicite.


