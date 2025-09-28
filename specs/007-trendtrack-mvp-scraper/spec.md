# Spécification TrendTrack MVP Scraper

**Version**: V2  
**Date**: 2025-09-25  
**Statut**: Documentation officielle MVP

## 📋 Vue d'ensemble

Le **TrendTrack MVP Scraper** est une version stabilisée et robuste du scraper TrendTrack, conçue pour résoudre les problèmes de fiabilité de la version classique.

### 🎯 Objectifs MVP

- **Stabiliser** l'extraction sur 100% des boutiques de la page cible
- **Récupération automatique** des erreurs critiques (contexte/session)
- **Retries intelligents** avec backoff exponentiel
- **Persistance correcte** des données
- **Conformité stricte** aux règles du dépôt

### ⚠️ Distinction Alpha vs Production

| Version | Script Principal | Base de Données | Sauvegarde |
|---------|------------------|-----------------|------------|
| **MVP** | `update-database-mvp.js` | `trendtrack.db` | ✅ Sauvegarde |
| **Classique** | `update-database.js` | `trendtrack.db` | ✅ Sauvegarde |

---

## 🏗️ Architecture MVP

### Modules Principaux

```
src/mvp/
├── mvp-context-manager.js     # Solution 1: Gestion contextes fermés
├── mvp-session-manager.js     # Solution 3: Gestion sessions expirées
├── mvp-retry-handler.js       # Orchestration des retries
├── mvp-scraper.js            # Scraper MVP principal
└── mvp-browser-manager.js    # Solution 4: Redémarrage navigateur
```

### Script Principal

- **Fichier**: `/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/update-database-mvp.js`
- **Configuration**: MVP_CONFIG avec limites et timeouts
- **Architecture**: Intégration complète des solutions de récupération
- **Base de données**: Voir [data-model.md](plan/data-model.md) pour la structure complète

---

## 📊 Données Extraites

### Phase 1 - Table (Trending Shops)

| Champ | Sélecteur | Description |
|-------|-----------|-------------|
| `shop_name` | `div:first-child p.text-sm.font-semibold` | Nom de la boutique |
| `shop_url` | `a[href*="http"]` | URL de la boutique |
| `total_products` | `p.text-sm.font-semibold` | Nombre de produits |
| `year_founded` | `p.text-[11px]` | Année de création |
| `creation_date` | Timestamp ISO 8601 UTC | Date d'ajout |
| `external_id` | UUID via `<tr id>` | Identifiant externe |
| `live_ads` | `p.font-bold` | Publicités actives |

### Phase 3 - Détails (Page Boutique)

| Champ | Description | Type | Statut |
|-------|-------------|------|--------|
| `live_ads_7d` | Publicités 7 jours | INTEGER | ✅ Extrait |
| `live_ads_30d` | Publicités 30 jours | INTEGER | ✅ Extrait |
| `pixel_google` | Pixel Google détecté | TEXT | ✅ Extrait |
| `pixel_facebook` | Pixel Facebook détecté | TEXT | ✅ Extrait |
| `market_us` | Marché US | NUMERIC | ✅ Extrait |
| `market_uk` | Marché UK | NUMERIC | ✅ Extrait |
| `market_de` | Marché DE | NUMERIC | ✅ Extrait |
| `market_ca` | Marché CA | NUMERIC | ✅ Extrait |
| `market_au` | Marché AU | NUMERIC | ✅ Extrait |
| `market_fr` | Marché FR | NUMERIC | ✅ Extrait |

### Types de Données par Champ

| Champ | Type SQLite | Description | Exemple |
|-------|-------------|-------------|---------|
| `live_ads` | INTEGER | Publicités actives | `1`, `0`, `15` |
| `year_founded` | TEXT | Année de création | `"2020"`, `"Founded in 2018"` |
| `pixel_google` | TEXT | Pixel Google détecté | `"Google Analytics"`, `"GTM-XXXX"` |
| `market_us` | NUMERIC | Marché US | `0.45`, `0.0`, `1.0` |

---

## 🔧 Solutions Techniques

### Solution 1 - Gestion des Contextes Fermés

**Problème**: `Target page/context/browser has been closed`  
**Solution**: `MVPContextManager.executeWithContextRecovery(operation)`

```javascript
// Détection automatique et recréation transparente
const result = await MVPContextManager.executeWithContextRecovery(async () => {
    return await page.goto(url);
});
```

### Solution 3 - Gestion des Sessions Expirées

**Problème**: Session expirée (URL/login, champs password)  
**Solution**: `MVPSessionManager.executeWithSessionRecovery(operation, extractor)`

```javascript
// Détection et relogging automatique
const result = await MVPSessionManager.executeWithSessionRecovery(async () => {
    return await extractor.extractDetails(shopId);
}, extractor);
```

### Solution 4 - Redémarrage Navigateur

**Problème**: `browser.newContext: Target page, context or browser has been closed`  
**Solution**: `MVPBrowserManager.executeWithBrowserRestart(operation)`

```javascript
// Redémarrage automatique du navigateur
const result = await MVPBrowserManager.executeWithBrowserRestart(async () => {
    return await performScraping();
});
```

### Orchestration - MVPRetryHandler

**Combinaison** des 4 solutions avec backoff exponentiel :

```javascript
const result = await MVPRetryHandler.executeWithRetry(
    operation,
    contextKey,
    maxRetries = 3
);
```

---

## 📈 Politique de Retry

### Configuration

- **Max Retries**: 3 tentatives
- **Backoff**: Exponentiel (1s, 2s, 4s)
- **Retryables**: Timeouts, contexte fermé, session expirée, browser fermé
- **Non-retryables**: Auth invalide, sélecteurs invalides, mapping DB invalide

### Traitement par Lots

- **Batch Size**: 5 boutiques par lot
- **Continuité**: Ne pas interrompre les lots suivants
- **Reprise**: Mini-retry de fin de run pour les `failed`
- **Pauses**: Entre boutiques (2s) et entre lots (5s)

---

## 🗄️ Gestion Base de Données

### Tables de la Base de Données

#### Table `shops` (principale)
Le scraper MVP stocke **toutes ses données** dans la table `shops`.

#### Table `analytics` (non utilisée par MVP)
**⚠️ Important**: Le scraper MVP ne met jamais à jour la table `analytics`. Cette table est utilisée par :
- **Scraper classique** : Pour les métriques TrendTrack
- **Scraper Noxtools** : Pour les métriques SEM (visits, organic_traffic, cpc, etc.)

**Référence** : Voir [data-model.md](plan/data-model.md) pour la structure complète de la table `analytics`.

### Nouveaux Champs de Statut

| Champ | Type | Description |
|-------|------|-------------|
| `table_scraping_status` | TEXT | Statut extraction table |
| `details_scraping_status` | TEXT | Statut extraction détails |

### Workflow des Statuts

1. **Phase 2 fin**: `table_scraping_status = 'table_extracted'`
2. **Phase 3 succès**: `details_scraping_status = 'details_extracted'`
3. **Phase 3 échec**: `scraping_status = 'failed'`

### Mapping des Données

```sql
-- Phase 1: Upsert table shops
INSERT OR REPLACE INTO shops (
    shop_name, shop_url, external_id, year_founded,
    creation_date, total_products, live_ads,
    monthly_visits, monthly_revenue,
    table_scraping_status
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'table_extracted');

-- Phase 3: Update détails
UPDATE shops SET 
    live_ads_7d = ?, live_ads_30d = ?, aov = ?,
    details_scraping_status = 'details_extracted'
WHERE external_id = ?;
```

---

## 📋 Critères de Conformité

### Phase 1 - Table
- ✅ **30/30 lignes** extraites
- ✅ **30/30 external_id** générés
- ✅ **≥80% year_founded** trouvés

### Phase 3 - Détails
- ✅ **100% des shops** sélectionnés tentés
- ✅ **≥90% succès/run** (atteignable avec reprise multi-runs)
- ✅ **AOV retiré** (statut OK - plus d'extraction AOV)

### Robustesse
- ✅ **Aucune interruption** due à contexte/session
- ✅ **Récupération automatique** visible dans les logs
- ✅ **Parsing des revenus robuste** avec logique de fallback

---

---

## 🔧 Logique de Parsing des Revenus

### Gestion des Revenus Non Reconnus

Le scraper MVP implémente une logique de fallback robuste pour traiter tous les formats de revenus :

#### **1. Pattern Principal (avec suffixe K/M/B)**
```javascript
// Exemples: "597.9K$", "1.8M$", "2.5B$"
const m = t.match(/^([0-9][0-9.,]*)([kKmMbB]?)$/);
if (m) {
  // Traitement avec multiplication par suffixe
}
```

#### **2. Fallback (valeurs numériques pures)**
```javascript
// Exemples: "647649", "1234567", "1,234,567"
const numericMatch = t.match(/^([0-9][0-9.,]*)$/);
if (numericMatch) {
  // Utilisation directe de la valeur numérique
  console.log(`✅ Fallback: Valeur numérique pure extraite: "${token}" → ${base}`);
  return base;
}
```

#### **3. Gestion des Erreurs**
```javascript
// Si pas de pattern et pas de valeur numérique: retourner null
console.log(`⚠️ Valeur non reconnue (pas de pattern, pas numérique): "${token}"`);
return null;
```

### Avantages de cette Approche

- ✅ **Compatibilité totale** avec les formats existants
- ✅ **Résolution du bug** des revenus non reconnus (ex: "647649")
- ✅ **Robustesse** face aux variations de format
- ✅ **Logs détaillés** pour le debugging

---

## 🚀 Démarrage Rapide

### Prérequis
- Node.js 18+
- Playwright installé
- Base de données `trendtrack.db` configurée
- Credentials TrendTrack valides

### Lancement

```bash
cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
node update-database-mvp.js
```

### Configuration

```javascript
const MVP_CONFIG = {
    maxShopsPerRun: 100,        // Limite MVP
    maxPagesPerRun: 1,          // 1 page pour MVP
    batchSize: 5,               // 5 boutiques par lot
    maxRetries: 3,              // 3 tentatives
    navigationTimeout: 60000,   // 60s
    selectorTimeout: 15000      // 15s
};
```

---


## 📚 Références

- **Script Principal**: `/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/update-database-mvp.js`
- **Modules MVP**: `src/mvp/`
- **Base de Données**: `/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db`
- **Structure BDD**: Voir [data-model.md](plan/data-model.md)
- **Logs**: `logs/update-mvp-progress.log`
- **Documentation Classique**: `/specs/001-name-trendtrack-scraper/`
- **Documentation Noxtools**: `/specs/006-noxtools-scraper/`
