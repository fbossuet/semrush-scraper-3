# MODIFICATIONS À APPLIQUER AUX FICHIERS EXISTANTS

## 1. PRODUCTION_SCRAPER_PARALLEL_*.PY

### A. DÉSACTIVATION DU SYSTÈME DE LOCKS

**Rechercher la classe `LockManager` et remplacer par :**

```python
class LockManager:
    def acquire_lock(self) -> bool:
        logger.info(f"🔓 Worker {self.worker_id}: Système de locks désactivé - accès libre")
        return True
    
    def release_lock(self):
        logger.info(f"🔓 Worker {self.worker_id}: Système de locks désactivé - libération ignorée")
    
    def is_locked(self) -> bool:
        return False
```

### B. AJOUT DES MÉTRIQUES LIVE_ADS

**Dans la méthode `__init__`, ajouter dans `self.metrics_count` :**

```python
# P0: Variations Live Ads
'live_ads_7d': {'found': 0, 'not_found': 0, 'skipped': 0},
'live_ads_30d': {'found': 0, 'not_found': 0, 'skipped': 0},
```

### C. NOUVELLE MÉTHODE POUR LIVE ADS

**Ajouter cette méthode après `scrape_market_traffic` :**

```python
async def scrape_live_ads_progression(self, domain: str) -> dict:
    """
    Récupère les variations de Live Ads (live_ads_7d, live_ads_30d)
    """
    try:
        logger.info(f"📊 Worker {self.worker_id}: Récupération progression Live Ads pour {domain}")
        import subprocess
        import json
        script_path = os.path.join(os.getcwd(), "live_ads_progression_extractor.py")
        result = subprocess.run([
            "python3", script_path, f"https://{domain}"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                progression_data = json.loads(result.stdout)
                logger.info(f"✅ Worker {self.worker_id}: Progression Live Ads récupérée: {progression_data}")
                return progression_data
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Worker {self.worker_id}: Erreur parsing JSON progression Live Ads")
                return {}
        else:
            logger.warning(f"⚠️ Worker {self.worker_id}: Erreur script progression Live Ads: {result.stderr}")
            return {}
    except Exception as e:
        logger.error(f"❌ Worker {self.worker_id}: Erreur progression Live Ads: {e}")
        return {}
```

### D. INTÉGRATION DANS LE PROCESSUS DE SCRAPING

**Dans la méthode principale de scraping, ajouter après l'extraction du trafic par pays :**

```python
# 3. P0: Progression Live Ads (7d et 30d)
progression_data = await self.scrape_live_ads_progression(domain)
if progression_data:
    for progression_key, progression_value in progression_data.items():
        if progression_key in ['live_ads_7d', 'live_ads_30d'] and progression_value is not None:
            setattr(self, progression_key, str(progression_value))
            logger.info(f"✅ Worker {self.worker_id}: {progression_key}: {progression_value}%")
```

### E. CORRECTION CHEMIN MARKET_TRAFFIC_EXTRACTOR

**Remplacer le chemin vers `market_traffic_extractor.py` par :**

```python
# Utiliser le fichier local corrigé
script_path = os.path.join(os.getcwd(), "market_traffic_extractor.py")
```

---

## 2. UPDATE-DATABASE.JS

### DÉSACTIVATION DU SYSTÈME DE LOCKS

**Commenter les imports de locks :**

```javascript
// import { acquireLock, releaseLock } from './src/utils/db-lock.js'; // DÉSACTIVÉ
// const LOCK_FILE = path.join(process.cwd(), 'trendtrack-db.lock'); // DÉSACTIVÉ
```

**Remplacer la logique d'acquisition de lock par :**

```javascript
// Système de locks désactivé
logProgress('🔓 Système de locks désactivé - accès libre à la base de données');
lockAcquired = true;
```

**Remplacer la logique de libération de lock par :**

```javascript
// Système de locks désactivé
if (lockAcquired) {
  logProgress('🔓 Système de locks désactivé - libération ignorée');
}
```

---

## 3. TRENDTRACK-EXTRACTOR_*.JS

### AJOUT EXTRACTION PRODUITS

**Ajouter après l'extraction de `liveAds` :**

```javascript
// 🆕 Extraction directe du nombre de produits (colonne 2)
try {
  const productsCell = cells[2]; // 3ème colonne (index 2)
  const productsP = productsCell.locator('p:has(> span:has-text("products"))');
  const productsText = await productsP.textContent();
  if (productsText) {
    const match = productsText.match(/\d[\d\s.,]*/);
    shopData.totalProducts = match ? Number(match[0].replace(/[^\d]/g, "")) : null;
    console.log(`📦 Produits extraits pour ${shopData.shopName}: ${shopData.totalProducts}`);
  } else {
    shopData.totalProducts = null;
  }
} catch (error) {
  console.error(`⚠️ Erreur extraction produits pour ${shopData.shopName}:`, error.message);
  shopData.totalProducts = null;
}
```

---

## 4. MIGRATION BASE DE DONNÉES

### EXÉCUTER LA MIGRATION

```bash
# Dans votre environnement VPS
python3 migrate_database_add_live_ads_columns.py
```

### VÉRIFIER LA MIGRATION

```sql
-- Vérifier que les colonnes ont été ajoutées
PRAGMA table_info(shops);
```

---

## 5. TESTS DE VALIDATION

### EXÉCUTER LES TESTS

```bash
# Tester les corrections
python3 test_corrections.py

# Tester la logique d'extraction
python3 test_market_traffic_logic.py

# Créer une base de test
python3 create_test_db_with_live_ads.py
```

---

## 6. INSTALLATION DÉPENDANCES

### INSTALLER PLAYWRIGHT

```bash
# Installer Playwright
pip install playwright

# Installer les navigateurs
playwright install
```

---

## 7. STRUCTURE FINALE ATTENDUE

```
trendtrack-scraper-final/
├── data/
│   └── trendtrack.db (avec colonnes live_ads_7d, live_ads_30d)
├── market_traffic_extractor.py (NOUVEAU)
├── utils-dom.js (NOUVEAU)
├── live_ads_progression_extractor.py (NOUVEAU)
├── migrate_database_add_live_ads_columns.py (NOUVEAU)
├── test_corrections.py (NOUVEAU)
├── test_market_traffic_logic.py (NOUVEAU)
├── create_test_db_with_live_ads.py (NOUVEAU)
├── production_scraper_parallel_*.py (MODIFIÉ)
├── update-database.js (MODIFIÉ)
└── trendtrack-extractor_*.js (MODIFIÉ)
```

---

## 8. ORDRE D'APPLICATION

1. **Copier les nouveaux fichiers** dans votre projet VPS
2. **Exécuter la migration** de la base de données
3. **Modifier les scrapers** avec les corrections
4. **Modifier update-database.js** avec la désactivation des locks
5. **Modifier les extracteurs TrendTrack** avec l'extraction produits
6. **Installer Playwright** si pas déjà fait
7. **Tester les modifications**
8. **Lancer un test en production**

---

**Note importante :** Toutes ces modifications ont été testées et validées dans l'environnement de développement. Adaptez les chemins selon votre structure VPS.