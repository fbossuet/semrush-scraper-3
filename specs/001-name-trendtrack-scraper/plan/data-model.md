# Data Model: Scraper SEM Parallèle

**Date**: 2025-09-16  
**Feature**: Scraper SEM Parallèle  
**Design Phase**: Phase 1 - Data Model Definition

## Entity Definitions

### 1. Website Entity

**Purpose**: Represents a target website for metric collection

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `shop_name` (TEXT): Human-readable name of the website
- `shop_url` (TEXT, UNIQUE, NOT NULL): Full URL of the website
- `scraping_status` (TEXT): Final processing status
  - Values: 'completed', 'partial', 'failed', 'na', 'pending', ''
  - Default: 'pending'
- `table_scraping_status` (TEXT): Phase 2 table extraction status
  - Values: 'table_extracted', 'failed', 'pending'
  - Default: 'pending'
- `details_scraping_status` (TEXT): Phase 3 details extraction status
  - Values: 'details_extracted', 'failed', 'pending'
  - Default: 'pending'
- `creation_date` (TEXT): ISO timestamp of record creation
- `total_products` (INTEGER): Total number of products (format: 24750)
- `monthly_visits` (INTEGER): Monthly visits data (format: 647600 for "647.6K")
- `monthly_revenue` (TEXT): Monthly revenue data (format: "597.9K$ - 1.8M$")
- `live_ads` (INTEGER): Live ads information (format: 7319)
- `live_ads_7d` (INTEGER): Live ads for last 7 days
- `live_ads_30d` (INTEGER): Live ads for last 30 days
- `aov` (NUMERIC): Average Order Value (format: 50.0)
- `page_number` (TEXT): Page number in source data
- `scraped_at` (TEXT): ISO timestamp of last successful scraping
- `project_source` (TEXT): Source of the website data
- `external_id` (TEXT): External system identifier
- `metadata` (TEXT): JSON string with additional metadata
- `year_founded` (TEXT): Year the website was founded (format: "2021", not 2021.0)
- `creation_date` (TEXT): ISO 8601 UTC timestamp of website creation (format: 2021-09-17T00:00:00.000Z)

**Validation Rules**:
- `shop_url` must be a valid URL format
- `scraping_status` must be one of the defined values
- `table_scraping_status` must be one of: 'table_extracted', 'failed', 'pending'
- `details_scraping_status` must be one of: 'details_extracted', 'failed', 'pending'
- `creation_date` must be valid ISO 8601 UTC timestamp when not null
- `scraped_at` must be valid ISO timestamp when not null

**State Transitions**:
- `pending` → `partial` (partial data collected)
- `pending` → `completed` (all data collected)
- `pending` → `failed` (scraping failed)
- `pending` → `na` (traffic too low)
- `partial` → `completed` (missing data collected)
- `partial` → `failed` (retry failed)
- `failed` → `pending` (retry after 24h)
- `completed` → `pending` (re-scrape after 24h)

### 2. Metrics Entity (Analytics Table)

**Purpose**: Stores collected performance metrics for each website

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `shop_id` (INTEGER, FOREIGN KEY): Reference to Website.id
- `organic_traffic` (TEXT): Organic search traffic count (API organic.Summary)
- `paid_search_traffic` (TEXT): Paid search traffic count (API organic.Summary)
- `visits` (TEXT): Total visits (mapped from traffic via organic.OverviewTrend)
- `bounce_rate` (TEXT): Bounce rate as decimal (API engagement)
- `avg_visit_duration` (TEXT): Average visit duration in seconds (API engagement)
- `branded_traffic` (TEXT): Branded traffic count (API organic.OverviewTrend)
- `conversion_rate` (TEXT): Conversion rate as decimal (DOM scraping)
- `percent_branded_traffic` (TEXT): Calculated percentage as decimal (branded_traffic / visits)
- `updated_at` (TEXT): ISO timestamp of last update
- `created_at` (TEXT): ISO timestamp of record creation

**Validation Rules**:
- `shop_id` must reference existing Website.id
- All metric fields must be numeric when not null
- `bounce_rate` must be between 0 and 1
- `conversion_rate` must be between 0 and 1
- `percent_branded_traffic` must be between 0 and 1
- `avg_visit_duration` must be positive number

**Calculated Fields**:
- `percent_branded_traffic` = `branded_traffic` / `visits` (when both available)

### 3. ScrapingSession Entity

**Purpose**: Represents a scraping session with multiple workers

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `session_name` (TEXT): Human-readable session name
- `status` (TEXT): Session status
  - Values: 'running', 'completed', 'failed', 'cancelled'
- `target_status` (TEXT): Target website status filter
  - Values: 'partial', 'failed', 'pending', 'all'
- `worker_count` (INTEGER): Number of parallel workers
- `websites_per_worker` (INTEGER): Websites assigned per worker
- `total_websites` (INTEGER): Total websites to process
- `processed_websites` (INTEGER): Websites processed so far
- `successful_websites` (INTEGER): Successfully processed websites
- `failed_websites` (INTEGER): Failed websites
- `started_at` (TEXT): ISO timestamp of session start
- `completed_at` (TEXT): ISO timestamp of session completion
- `created_at` (TEXT): ISO timestamp of record creation

**Validation Rules**:
- `worker_count` must be between 1 and 10
- `websites_per_worker` must be between 1 and 50
- `total_websites` must be positive
- `processed_websites` cannot exceed `total_websites`
- `successful_websites` + `failed_websites` cannot exceed `processed_websites`

### 4. Worker Entity

**Purpose**: Represents a parallel processing unit within a scraping session

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `session_id` (INTEGER, FOREIGN KEY): Reference to ScrapingSession.id
- `worker_id` (INTEGER): Worker identifier within session
- `status` (TEXT): Worker status
  - Values: 'idle', 'running', 'completed', 'failed'
- `assigned_websites` (TEXT): JSON array of website IDs
- `processed_websites` (TEXT): JSON array of processed website IDs
- `current_website_id` (INTEGER): Currently processing website ID
- `started_at` (TEXT): ISO timestamp of worker start
- `completed_at` (TEXT): ISO timestamp of worker completion
- `error_message` (TEXT): Error message if worker failed

**Validation Rules**:
- `session_id` must reference existing ScrapingSession.id
- `worker_id` must be unique within session
- `assigned_websites` must be valid JSON array
- `processed_websites` must be valid JSON array
- `current_website_id` must reference existing Website.id when not null

## Relationships

### Website ↔ Metrics (One-to-One)
- Each website can have one metrics record
- Each metrics record belongs to one website
- Foreign key: `analytics.shop_id` → `shops.id`

### ScrapingSession ↔ Worker (One-to-Many)
- Each scraping session can have multiple workers
- Each worker belongs to one scraping session
- Foreign key: `workers.session_id` → `scraping_sessions.id`

### ScrapingSession ↔ Website (Many-to-Many)
- Each scraping session processes multiple websites
- Each website can be processed in multiple sessions
- Relationship managed through Worker.assigned_websites

## Database Architecture

### Dual Database Setup
- **Production Database**: `/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db` - Live scraping operations
- **Test Database**: `/home/ubuntu/trendtrack-scraper-final/data/trendtrack_test.db` - Isolated testing environment
- **Database Switching**: Environment-based configuration for production vs testing

### Database Schema

### Shops Table
```sql
CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    shop_url TEXT UNIQUE NOT NULL,
    creation_date TEXT,
    category TEXT,
    monthly_visits INTEGER,
    monthly_revenue TEXT,
    live_ads TEXT,
    live_ads_7d INTEGER DEFAULT 0,
    live_ads_30d INTEGER DEFAULT 0,
    page_number TEXT,
    scraped_at TEXT,
    updated_at TEXT,
    project_source TEXT DEFAULT 'trendtrack',
    external_id TEXT,
    metadata TEXT,
    year_founded TEXT,
    total_products INTEGER,
    pixel_google TEXT,
    pixel_facebook TEXT,
    aov NUMERIC,
    market_us NUMERIC,
    market_uk NUMERIC,
    market_de NUMERIC,
    market_ca NUMERIC,
    market_au NUMERIC,
    market_fr NUMERIC,
    scraping_status TEXT,
    scraping_last_update TEXT
);
```

### Analytics Table
```sql
CREATE TABLE IF NOT EXISTS "analytics" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    organic_traffic TEXT,
    paid_search_traffic TEXT,
    visits TEXT,
    bounce_rate TEXT,
    avg_visit_duration TEXT,
    branded_traffic TEXT,
    conversion_rate TEXT,
    percent_branded_traffic TEXT,
    updated_at TEXT,
    created_at TEXT,
    FOREIGN KEY (shop_id) REFERENCES shops (id)
);
```

### Scraping Sessions Table
```sql
CREATE TABLE IF NOT EXISTS "scraping_sessions" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
    ended_at TIMESTAMP,
    pages_scraped INTEGER DEFAULT 0,
    shops_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    project_source TEXT DEFAULT 'trendtrack'
);
```

### Shared Projects Table
```sql
CREATE TABLE IF NOT EXISTS "shared_projects" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    project_path TEXT NOT NULL,
    api_key TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
    last_access TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

## Indexes

### Performance Indexes
```sql
-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_shops_url ON shops(shop_url);
CREATE INDEX IF NOT EXISTS idx_shops_live_ads ON shops(live_ads);
CREATE INDEX IF NOT EXISTS idx_shops_live_ads_7d ON shops(live_ads_7d);
CREATE INDEX IF NOT EXISTS idx_shops_live_ads_30d ON shops(live_ads_30d);
CREATE INDEX IF NOT EXISTS idx_shops_category ON shops(category);
CREATE INDEX IF NOT EXISTS idx_shops_scraped_at ON shops(scraped_at);
CREATE INDEX IF NOT EXISTS idx_shops_project_source ON shops(project_source);
CREATE INDEX IF NOT EXISTS idx_shops_external_id ON shops(external_id);

-- Index composites pour optimiser les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_shops_live_ads_scraped_at ON shops(live_ads DESC, scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_shops_project_live_ads ON shops(project_source, live_ads DESC);
CREATE INDEX IF NOT EXISTS idx_shops_category_live_ads ON shops(category, live_ads DESC);
CREATE INDEX IF NOT EXISTS idx_shops_updated_at ON shops(updated_at DESC);

-- Index pour les sessions de scraping
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON scraping_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_project_status ON scraping_sessions(project_source, status);

-- Index pour les projets partagés
CREATE INDEX IF NOT EXISTS idx_projects_api_key ON shared_projects(api_key);
CREATE INDEX IF NOT EXISTS idx_projects_active ON shared_projects(is_active, last_access DESC);
```

## Workflow des Statuts de Scraping

**⚠️ ATTENTION** : Cette section concerne UNIQUEMENT le scraper MVP (TKMVP).
Pour le scraper classique (TKOLD), voir `.specify/doc-tkold.md`

### Règle Fondamentale TKMVP
**Le scraper MVP TrendTrack ne met JAMAIS à jour la table `analytics`**

### Workflow des Statuts dans la Table `shops`

#### Phase 2 - Extraction des données de table
```javascript
// Fin de Phase 2 (ligne 424)
shopData.table_scraping_status = 'table_extracted';
```

#### Phase 3 - Extraction des métriques détaillées
```javascript
// Succès Phase 3 (ligne 862)
shopData.details_scraping_status = 'details_extracted';

// Échec Phase 3 - Aucune métrique (ligne 874)
shopData.scraping_status = 'failed';

// Échec Phase 3 - Exception (ligne 886)
shopData.scraping_status = 'failed';
```

#### Script Principal - Après Phase 2
```javascript
// Après sauvegarde Phase 2 (ligne 226)
await shopRepo.updateShopStatus(mappedShopData.externalId, 'table_extracted');
```

### Suppression des Mises à Jour Analytics
- **Ligne 373** : Supprimer `detailData.scraping_status` dans l'insertion analytics
- **Ligne 549** : Supprimer `analyticsData.scraping_status` dans la mise à jour analytics

## Data Formatting Module

### DataFormatter Class
Le module `src/utils/data-formatter.js` centralise tous les formats de données selon les spécifications :

#### Méthodes de Formatage
- `formatYearFounded(value)` : Retourne `{year_founded: TEXT, creation_date: ISO_STRING}`
- `formatMonthlyVisits(visitsText)` : Convertit "647.6K" → 647600 (INTEGER)
- `formatMonthlyRevenue(revenueText)` : Conserve "597.9K$ - 1.8M$" (TEXT)
- `formatLiveAds(liveAdsText)` : Extrait 7319 de "7319" (INTEGER)
- `formatCategories(categoryElements)` : Joint "Cat1|Cat2" (TEXT)
- `formatAOV(aovText)` : Convertit "1.25" → 1.25 (NUMERIC)
- `formatTotalProducts(productsText)` : Extrait 24750 de "24750 products" (INTEGER)
- `formatTimestamp(date)` : Génère timestamp ISO 8601 UTC
- `formatUrl(url)` : Valide et formate les URLs

#### Formats de Données Standardisés
- **Timestamps** : ISO 8601 UTC (`2021-09-17T00:00:00.000Z`)
- **Années** : TEXT ("2021", pas 2021.0)
- **Visites** : INTEGER (647600 pour "647.6K")
- **Revenus** : TEXT range ("597.9K$ - 1.8M$")
- **Live Ads** : INTEGER (7319)
- **AOV** : NUMERIC (1.25)
- **Produits** : INTEGER (24750)

## Data Validation Rules

### Website Status Validation
- `completed`: All 8 metrics must be present and valid
- `partial`: At least 1 metric missing or invalid
- `failed`: Scraping attempt failed
- `na`: Organic traffic < 1000
- `pending`: Not yet processed

### Metric Validation
- All numeric fields must be parseable as numbers
- Decimal fields (bounce_rate, conversion_rate, percent_branded_traffic) must be between 0 and 1
- Traffic fields must be positive integers
- Duration fields must be positive numbers

### Session Validation
- Worker count must be reasonable (1-10)
- Websites per worker must be reasonable (1-50)
- Total websites must match sum of assigned websites across workers

---
*Data model completed: 2025-09-16*
