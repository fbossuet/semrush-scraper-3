# Modèle de Données : Scraper Noxtools

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
**Input** : Spécification de fonctionnalité depuis `/specs/006-noxtools-scraper/spec.md`

## Résumé
Modèle de données pour le scraper Noxtools, incluant les entités, relations, et intégration avec la base de données existante TrendTrack/SEM.

## Entités Principales

### 1. Shop (Boutique)
**Table existante** : `shops` (référence TrendTrack)

```sql
-- Table shops (existante, référence TrendTrack)
CREATE TABLE shops (
    id INTEGER PRIMARY KEY,
    shop_url TEXT NOT NULL,
    shop_name TEXT,
    scraping_status TEXT,  -- 'pending', 'completed', 'failed'
    details_scraping_status TEXT,  -- 'pending', 'details_extracted', 'failed'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Champs clés pour Noxtools** :
- `shop_url` : URL de la boutique (ex: "https://cakesbody.com")
- `scraping_status` : Statut du scraping principal (≠ "failed" pour éligibilité)
- `details_scraping_status` : Statut du scraping des détails (= "details_extracted" pour éligibilité)

### 2. Analytics (Métriques Noxtools)
**Table existante** : `analytics` (référence TrendTrack)

```sql
-- Table analytics (existante, référence TrendTrack)
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    scraping_status TEXT,  -- 'completed', 'partial', 'failed', NULL
    
    -- Métriques Noxtools spécifiques
    visits INTEGER,
    organic_traffic INTEGER,
    paid_search_traffic INTEGER,
    conversion_rate REAL,
    avg_visit_duration INTEGER,  -- en secondes
    bounce_rate REAL,
    cpc REAL,
    branded_traffic INTEGER,
    
    -- Métadonnées
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```

**Métriques Noxtools** :
- `visits` : Nombre total de visites
- `organic_traffic` : Trafic organique (entrancesSearchOrganic)
- `paid_search_traffic` : Trafic payant (entrancesSearchPaid)
- `conversion_rate` : Taux de conversion (purchasesPerVisit)
- `avg_visit_duration` : Durée moyenne des visites (avgVisitDuration)
- `bounce_rate` : Taux de rebond (bouncesPerVisit)
- `cpc` : Coût par clic (CPC)
- `branded_traffic` : Trafic de marque

## Relations

### Relation Shop ↔ Analytics
```sql
-- Clé étrangère : analytics.shop_id → shops.id
FOREIGN KEY (shop_id) REFERENCES shops(id)
```

**Cardinalité** : 1:N (une boutique peut avoir plusieurs enregistrements analytics)

## Critères d'Éligibilité

### Shops Éligibles pour Noxtools
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL;
```

**Conditions** :
1. `shops.scraping_status ≠ "failed"`
2. `shops.details_scraping_status = "details_extracted"`
3. `analytics.scraping_status = NULL`

## Formatage des Données

### Standards de Format
- **Nombres compacts** : "33.3K" → 33300, "1.5M" → 1500000
- **Pourcentages** : "45.6%" → 45.6
- **Durées** : "2m 30s" → 150 (secondes)
- **Dates** : 
  - Logs/Métadonnées : ISO 8601 UTC (2025-01-18T20:30:00Z)
  - Base de données : SQLite DATE (2025-01-18)

### Mapping Noxtools → Analytics
```python
NOXTOOLS_TO_ANALYTICS_MAP = {
    'visits': 'visits',
    'entrancesSearchOrganic': 'organic_traffic',
    'entrancesSearchPaid': 'paid_search_traffic',
    'purchasesPerVisit': 'conversion_rate',
    'avgVisitDuration': 'avg_visit_duration',
    'bouncesPerVisit': 'bounce_rate',
    'cpc': 'cpc',
    'branded_traffic': 'branded_traffic'
}
```

## Gestion des Statuts

### Statuts de Scraping
- **`completed`** : Toutes les métriques récupérées avec succès
- **`partial`** : Au moins une métrique manquante
- **`failed`** : Aucune métrique récupérée ou erreur critique
- **`NULL`** : Pas encore traité (éligible pour scraping)

### Logique de Classification
```python
def classify_scraping_status(metrics):
    if all_metrics_present(metrics):
        return "completed"
    elif any_metrics_present(metrics):
        return "partial"
    else:
        return "failed"
```

## Intégration avec TrendTrack

### Base de Données Partagée
- **Fichier** : `trendtrack-scraper-final/data/trendtrack.db`
- **Tables** : `shops`, `analytics` (partagées avec TrendTrack et SEM)
- **Cohérence** : Respect des contraintes FK et index existants

### Métadonnées
```python
# Métadonnées ajoutées par le scraper Noxtools
{
    'scraper_source': 'noxtools',
    'scraper_version': '1.0.0-alpha',
    'scraped_at': '2025-01-18T20:30:00Z',  # ISO 8601 UTC
    'updated_at': '2025-01-18',  # SQLite DATE
    'server_used': 'semrush3.semrush.pw'  # Serveur utilisé pour le scraping
}
```

## Contraintes et Validation

### Contraintes de Données
- **`visits`** : Entier positif ou NULL
- **`organic_traffic`** : Entier positif ou NULL
- **`paid_search_traffic`** : Entier positif ou NULL
- **`conversion_rate`** : Réel entre 0 et 1 ou NULL
- **`avg_visit_duration`** : Entier positif (secondes) ou NULL
- **`bounce_rate`** : Réel entre 0 et 1 ou NULL
- **`cpc`** : Réel positif ou NULL
- **`branded_traffic`** : Entier positif ou NULL

### Validation d'Intégrité
- **FK contrainte** : `analytics.shop_id` doit exister dans `shops.id`
- **Unicité** : Un seul enregistrement `analytics` par `shop_id` et session
- **Cohérence** : Les métriques doivent être cohérentes entre elles

## Index et Performance

### Index Recommandés
```sql
-- Index existants (TrendTrack)
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_details_status ON shops(details_scraping_status);
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);

-- Index spécifiques Noxtools
CREATE INDEX idx_analytics_scraped_at ON analytics(scraped_at);
CREATE INDEX idx_analytics_visits ON analytics(visits);
```

### Optimisations
- **Batch processing** : Traitement par lots de 5 shops
- **Rate limiting** : Token bucket pour éviter la surcharge
- **Anti-détection** : Délais aléatoires entre requêtes

## Migration et Évolution

### Version Alpha
- **Lecture seule** : Pas d'écriture en base
- **Validation** : Logs détaillés des métriques
- **Test** : Vérification des critères d'éligibilité

### Version Beta
- **Écriture** : Insertion/update des métriques
- **Formatage** : Application des standards de format
- **Validation** : Contrôles d'intégrité avant sauvegarde

### Version Finale
- **Performance** : Optimisation des requêtes
- **Parallélisation** : Workers multiples
- **Monitoring** : Métriques de performance

## Exemples d'Usage

### Requête Shops Éligibles
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL
ORDER BY s.id
LIMIT 5;
```

### Insertion Métriques
```sql
INSERT INTO analytics (
    shop_id, visits, organic_traffic, paid_search_traffic,
    conversion_rate, avg_visit_duration, bounce_rate, cpc,
    branded_traffic, scraping_status, scraped_at, updated_at
) VALUES (
    123, 15000, 8000, 2000, 0.15, 180, 0.35, 2.50, 500,
    'completed', '2025-01-18T20:30:00Z', '2025-01-18'
);
```

### Mise à Jour Statut
```sql
UPDATE analytics 
SET scraping_status = 'completed', updated_at = '2025-01-18'
WHERE shop_id = 123;
```

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
**Input** : Spécification de fonctionnalité depuis `/specs/006-noxtools-scraper/spec.md`

## Résumé
Modèle de données pour le scraper Noxtools, incluant les entités, relations, et intégration avec la base de données existante TrendTrack/SEM.

## Entités Principales

### 1. Shop (Boutique)
**Table existante** : `shops` (référence TrendTrack)

```sql
-- Table shops (existante, référence TrendTrack)
CREATE TABLE shops (
    id INTEGER PRIMARY KEY,
    shop_url TEXT NOT NULL,
    shop_name TEXT,
    scraping_status TEXT,  -- 'pending', 'completed', 'failed'
    details_scraping_status TEXT,  -- 'pending', 'details_extracted', 'failed'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Champs clés pour Noxtools** :
- `shop_url` : URL de la boutique (ex: "https://cakesbody.com")
- `scraping_status` : Statut du scraping principal (≠ "failed" pour éligibilité)
- `details_scraping_status` : Statut du scraping des détails (= "details_extracted" pour éligibilité)

### 2. Analytics (Métriques Noxtools)
**Table existante** : `analytics` (référence TrendTrack)

```sql
-- Table analytics (existante, référence TrendTrack)
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    scraping_status TEXT,  -- 'completed', 'partial', 'failed', NULL
    
    -- Métriques Noxtools spécifiques
    visits INTEGER,
    organic_traffic INTEGER,
    paid_search_traffic INTEGER,
    conversion_rate REAL,
    avg_visit_duration INTEGER,  -- en secondes
    bounce_rate REAL,
    cpc REAL,
    branded_traffic INTEGER,
    
    -- Métadonnées
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```

**Métriques Noxtools** :
- `visits` : Nombre total de visites
- `organic_traffic` : Trafic organique (entrancesSearchOrganic)
- `paid_search_traffic` : Trafic payant (entrancesSearchPaid)
- `conversion_rate` : Taux de conversion (purchasesPerVisit)
- `avg_visit_duration` : Durée moyenne des visites (avgVisitDuration)
- `bounce_rate` : Taux de rebond (bouncesPerVisit)
- `cpc` : Coût par clic (CPC)
- `branded_traffic` : Trafic de marque

## Relations

### Relation Shop ↔ Analytics
```sql
-- Clé étrangère : analytics.shop_id → shops.id
FOREIGN KEY (shop_id) REFERENCES shops(id)
```

**Cardinalité** : 1:N (une boutique peut avoir plusieurs enregistrements analytics)

## Critères d'Éligibilité

### Shops Éligibles pour Noxtools
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL;
```

**Conditions** :
1. `shops.scraping_status ≠ "failed"`
2. `shops.details_scraping_status = "details_extracted"`
3. `analytics.scraping_status = NULL`

## Formatage des Données

### Standards de Format
- **Nombres compacts** : "33.3K" → 33300, "1.5M" → 1500000
- **Pourcentages** : "45.6%" → 45.6
- **Durées** : "2m 30s" → 150 (secondes)
- **Dates** : 
  - Logs/Métadonnées : ISO 8601 UTC (2025-01-18T20:30:00Z)
  - Base de données : SQLite DATE (2025-01-18)

### Mapping Noxtools → Analytics
```python
NOXTOOLS_TO_ANALYTICS_MAP = {
    'visits': 'visits',
    'entrancesSearchOrganic': 'organic_traffic',
    'entrancesSearchPaid': 'paid_search_traffic',
    'purchasesPerVisit': 'conversion_rate',
    'avgVisitDuration': 'avg_visit_duration',
    'bouncesPerVisit': 'bounce_rate',
    'cpc': 'cpc',
    'branded_traffic': 'branded_traffic'
}
```

## Gestion des Statuts

### Statuts de Scraping
- **`completed`** : Toutes les métriques récupérées avec succès
- **`partial`** : Au moins une métrique manquante
- **`failed`** : Aucune métrique récupérée ou erreur critique
- **`NULL`** : Pas encore traité (éligible pour scraping)

### Logique de Classification
```python
def classify_scraping_status(metrics):
    if all_metrics_present(metrics):
        return "completed"
    elif any_metrics_present(metrics):
        return "partial"
    else:
        return "failed"
```

## Intégration avec TrendTrack

### Base de Données Partagée
- **Fichier** : `trendtrack-scraper-final/data/trendtrack.db`
- **Tables** : `shops`, `analytics` (partagées avec TrendTrack et SEM)
- **Cohérence** : Respect des contraintes FK et index existants

### Métadonnées
```python
# Métadonnées ajoutées par le scraper Noxtools
{
    'scraper_source': 'noxtools',
    'scraper_version': '1.0.0-alpha',
    'scraped_at': '2025-01-18T20:30:00Z',  # ISO 8601 UTC
    'updated_at': '2025-01-18',  # SQLite DATE
    'server_used': 'semrush3.semrush.pw'  # Serveur utilisé pour le scraping
}
```

## Contraintes et Validation

### Contraintes de Données
- **`visits`** : Entier positif ou NULL
- **`organic_traffic`** : Entier positif ou NULL
- **`paid_search_traffic`** : Entier positif ou NULL
- **`conversion_rate`** : Réel entre 0 et 1 ou NULL
- **`avg_visit_duration`** : Entier positif (secondes) ou NULL
- **`bounce_rate`** : Réel entre 0 et 1 ou NULL
- **`cpc`** : Réel positif ou NULL
- **`branded_traffic`** : Entier positif ou NULL

### Validation d'Intégrité
- **FK contrainte** : `analytics.shop_id` doit exister dans `shops.id`
- **Unicité** : Un seul enregistrement `analytics` par `shop_id` et session
- **Cohérence** : Les métriques doivent être cohérentes entre elles

## Index et Performance

### Index Recommandés
```sql
-- Index existants (TrendTrack)
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_details_status ON shops(details_scraping_status);
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);

-- Index spécifiques Noxtools
CREATE INDEX idx_analytics_scraped_at ON analytics(scraped_at);
CREATE INDEX idx_analytics_visits ON analytics(visits);
```

### Optimisations
- **Batch processing** : Traitement par lots de 5 shops
- **Rate limiting** : Token bucket pour éviter la surcharge
- **Anti-détection** : Délais aléatoires entre requêtes

## Migration et Évolution

### Version Alpha
- **Lecture seule** : Pas d'écriture en base
- **Validation** : Logs détaillés des métriques
- **Test** : Vérification des critères d'éligibilité

### Version Beta
- **Écriture** : Insertion/update des métriques
- **Formatage** : Application des standards de format
- **Validation** : Contrôles d'intégrité avant sauvegarde

### Version Finale
- **Performance** : Optimisation des requêtes
- **Parallélisation** : Workers multiples
- **Monitoring** : Métriques de performance

## Exemples d'Usage

### Requête Shops Éligibles
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL
ORDER BY s.id
LIMIT 5;
```

### Insertion Métriques
```sql
INSERT INTO analytics (
    shop_id, visits, organic_traffic, paid_search_traffic,
    conversion_rate, avg_visit_duration, bounce_rate, cpc,
    branded_traffic, scraping_status, scraped_at, updated_at
) VALUES (
    123, 15000, 8000, 2000, 0.15, 180, 0.35, 2.50, 500,
    'completed', '2025-01-18T20:30:00Z', '2025-01-18'
);
```

### Mise à Jour Statut
```sql
UPDATE analytics 
SET scraping_status = 'completed', updated_at = '2025-01-18'
WHERE shop_id = 123;
```
