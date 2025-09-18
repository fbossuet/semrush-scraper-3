-- ========================================
-- MISE À JOUR STRUCTURE BASE DE DONNÉES
-- ========================================
-- Date: 2025-09-18
-- Objectif: Adopter la structure finale avec types optimisés
-- Base: trendtrack.db (production)

-- ========================================
-- 1. SUPPRESSION DES TABLES EXISTANTES
-- ========================================

-- Supprimer les index d'abord
DROP INDEX IF EXISTS idx_shops_scraping_status;
DROP INDEX IF EXISTS idx_shops_scraping_last_update;
DROP INDEX IF EXISTS idx_shops_shop_url;
DROP INDEX IF EXISTS idx_shops_url;
DROP INDEX IF EXISTS idx_shops_live_ads;
DROP INDEX IF EXISTS idx_shops_scraped_at;
DROP INDEX IF EXISTS idx_shops_project_source;
DROP INDEX IF EXISTS idx_shops_external_id;
DROP INDEX IF EXISTS idx_shops_live_ads_scraped_at;
DROP INDEX IF EXISTS idx_shops_project_live_ads;
DROP INDEX IF EXISTS idx_shops_updated_at;

DROP INDEX IF EXISTS idx_analytics_shop_id;
DROP INDEX IF EXISTS idx_analytics_scraping_status;
DROP INDEX IF EXISTS idx_analytics_shop_id_unique;

-- Supprimer les tables
DROP TABLE IF EXISTS analytics;
DROP TABLE IF EXISTS shops;

-- ========================================
-- 2. CRÉATION TABLE SHOPS (STRUCTURE FINALE)
-- ========================================

CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT,
    shop_url TEXT UNIQUE NOT NULL,
    scraping_status TEXT,
    scraping_last_update TEXT,        -- ✅ ISO 8601 UTC timestamp
    updated_at TEXT,                  -- ✅ ISO 8601 UTC timestamp
    creation_date TEXT,               -- ✅ ISO 8601 UTC timestamp
    monthly_visits INTEGER,        -- ✅ OPTIMISÉ: TEXT → INTEGER
    monthly_revenue NUMERIC,       -- ✅ MODIFIÉ: TEXT → NUMERIC
    live_ads INTEGER,              -- ✅ MODIFIÉ: TEXT → INTEGER
    page_number INTEGER,           -- ✅ MODIFIÉ: TEXT → INTEGER
    scraped_at TEXT,               -- ✅ OPTIMISÉ: TIMESTAMP → TEXT
    project_source TEXT,
    external_id INTEGER,           -- ✅ MODIFIÉ: TEXT → INTEGER (si uniquement numérique)
    metadata TEXT,
    year_founded TEXT,             -- ✅ ISO 8601 UTC timestamp
    
    -- ✅ NOUVEAUX CHAMPS AJOUTÉS
    total_products INTEGER,
    pixel_google TEXT,             -- ✅ MODIFIÉ: INTEGER → TEXT
    pixel_facebook TEXT,           -- ✅ MODIFIÉ: INTEGER → TEXT
    aov NUMERIC,
    market_us NUMERIC,
    market_uk NUMERIC,
    market_de NUMERIC,
    market_ca NUMERIC,
    market_au NUMERIC,
    market_fr NUMERIC
);

-- ========================================
-- 3. CRÉATION TABLE ANALYTICS (STRUCTURE FINALE)
-- ========================================

CREATE TABLE IF NOT EXISTS "analytics" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    organic_traffic INTEGER,           -- ✅ OPTIMISÉ: TEXT → INTEGER
    bounce_rate NUMERIC,               -- ✅ OPTIMISÉ: TEXT → NUMERIC
    avg_visit_duration TEXT,           -- Format MM:SS
    branded_traffic INTEGER,           -- ✅ OPTIMISÉ: TEXT → INTEGER
    conversion_rate NUMERIC,       -- ✅ MODIFIÉ: TEXT → NUMERIC
    scraping_status TEXT DEFAULT 'completed',
    updated_at TEXT,                   -- ✅ ISO 8601 UTC timestamp
    visits INTEGER,                    -- ✅ OPTIMISÉ: TEXT → INTEGER
    traffic INTEGER,                   -- ✅ OPTIMISÉ: TEXT → INTEGER
    paid_search_traffic INTEGER,       -- ✅ OPTIMISÉ: TEXT → INTEGER
    percent_branded_traffic NUMERIC,   -- ✅ OPTIMISÉ: REAL → NUMERIC
    
    -- ✅ NOUVEAU CHAMP AJOUTÉ
    cpc NUMERIC,
    
    FOREIGN KEY (shop_id) REFERENCES shops (id)
);

-- ========================================
-- 4. RECRÉATION DES INDEX
-- ========================================

-- Index pour shops
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_scraping_last_update ON shops(scraping_last_update);
CREATE INDEX idx_shops_shop_url ON shops(shop_url);
CREATE INDEX idx_shops_live_ads ON shops(live_ads);
CREATE INDEX idx_shops_scraped_at ON shops(scraped_at);
CREATE INDEX idx_shops_project_source ON shops(project_source);
CREATE INDEX idx_shops_external_id ON shops(external_id);
CREATE INDEX idx_shops_live_ads_scraped_at ON shops(live_ads DESC, scraped_at DESC);
CREATE INDEX idx_shops_project_live_ads ON shops(project_source, live_ads DESC);
CREATE INDEX idx_shops_updated_at ON shops(updated_at DESC);

-- Index pour analytics
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);
CREATE UNIQUE INDEX idx_analytics_shop_id_unique ON analytics(shop_id);

-- ========================================
-- 5. VÉRIFICATION DE LA STRUCTURE
-- ========================================

-- Afficher la structure finale
.schema shops
.schema analytics

-- Compter les tables
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Compter les index
SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;
-- MISE À JOUR STRUCTURE BASE DE DONNÉES
-- ========================================
-- Date: 2025-09-18
-- Objectif: Adopter la structure finale avec types optimisés
-- Base: trendtrack.db (production)

-- ========================================
-- 1. SUPPRESSION DES TABLES EXISTANTES
-- ========================================

-- Supprimer les index d'abord
DROP INDEX IF EXISTS idx_shops_scraping_status;
DROP INDEX IF EXISTS idx_shops_scraping_last_update;
DROP INDEX IF EXISTS idx_shops_shop_url;
DROP INDEX IF EXISTS idx_shops_url;
DROP INDEX IF EXISTS idx_shops_live_ads;
DROP INDEX IF EXISTS idx_shops_scraped_at;
DROP INDEX IF EXISTS idx_shops_project_source;
DROP INDEX IF EXISTS idx_shops_external_id;
DROP INDEX IF EXISTS idx_shops_live_ads_scraped_at;
DROP INDEX IF EXISTS idx_shops_project_live_ads;
DROP INDEX IF EXISTS idx_shops_updated_at;

DROP INDEX IF EXISTS idx_analytics_shop_id;
DROP INDEX IF EXISTS idx_analytics_scraping_status;
DROP INDEX IF EXISTS idx_analytics_shop_id_unique;

-- Supprimer les tables
DROP TABLE IF EXISTS analytics;
DROP TABLE IF EXISTS shops;

-- ========================================
-- 2. CRÉATION TABLE SHOPS (STRUCTURE FINALE)
-- ========================================

CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT,
    shop_url TEXT UNIQUE NOT NULL,
    scraping_status TEXT,
    scraping_last_update TEXT,        -- ✅ ISO 8601 UTC timestamp
    updated_at TEXT,                  -- ✅ ISO 8601 UTC timestamp
    creation_date TEXT,               -- ✅ ISO 8601 UTC timestamp
    monthly_visits INTEGER,        -- ✅ OPTIMISÉ: TEXT → INTEGER
    monthly_revenue TEXT,
    live_ads TEXT,                 -- ✅ OPTIMISÉ: INTEGER → TEXT
    page_number TEXT,              -- ✅ OPTIMISÉ: INTEGER → TEXT
    scraped_at TEXT,               -- ✅ OPTIMISÉ: TIMESTAMP → TEXT
    project_source TEXT,
    external_id TEXT,
    metadata TEXT,
    year_founded TEXT,             -- ✅ ISO 8601 UTC timestamp
    
    -- ✅ NOUVEAUX CHAMPS AJOUTÉS
    total_products INTEGER,
    pixel_google INTEGER,
    pixel_facebook INTEGER,
    aov NUMERIC,
    market_us NUMERIC,
    market_uk NUMERIC,
    market_de NUMERIC,
    market_ca NUMERIC,
    market_au NUMERIC,
    market_fr NUMERIC
);

-- ========================================
-- 3. CRÉATION TABLE ANALYTICS (STRUCTURE FINALE)
-- ========================================

CREATE TABLE IF NOT EXISTS "analytics" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    organic_traffic INTEGER,           -- ✅ OPTIMISÉ: TEXT → INTEGER
    bounce_rate NUMERIC,               -- ✅ OPTIMISÉ: TEXT → NUMERIC
    avg_visit_duration TEXT,           -- Format MM:SS
    branded_traffic INTEGER,           -- ✅ OPTIMISÉ: TEXT → INTEGER
    conversion_rate TEXT,
    scraping_status TEXT DEFAULT 'completed',
    updated_at TEXT,                   -- ✅ ISO 8601 UTC timestamp
    visits INTEGER,                    -- ✅ OPTIMISÉ: TEXT → INTEGER
    traffic INTEGER,                   -- ✅ OPTIMISÉ: TEXT → INTEGER
    paid_search_traffic INTEGER,       -- ✅ OPTIMISÉ: TEXT → INTEGER
    percent_branded_traffic NUMERIC,   -- ✅ OPTIMISÉ: REAL → NUMERIC
    
    -- ✅ NOUVEAU CHAMP AJOUTÉ
    cpc NUMERIC,
    
    FOREIGN KEY (shop_id) REFERENCES shops (id)
);

-- ========================================
-- 4. RECRÉATION DES INDEX
-- ========================================

-- Index pour shops
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_scraping_last_update ON shops(scraping_last_update);
CREATE INDEX idx_shops_shop_url ON shops(shop_url);
CREATE INDEX idx_shops_live_ads ON shops(live_ads);
CREATE INDEX idx_shops_scraped_at ON shops(scraped_at);
CREATE INDEX idx_shops_project_source ON shops(project_source);
CREATE INDEX idx_shops_external_id ON shops(external_id);
CREATE INDEX idx_shops_live_ads_scraped_at ON shops(live_ads DESC, scraped_at DESC);
CREATE INDEX idx_shops_project_live_ads ON shops(project_source, live_ads DESC);
CREATE INDEX idx_shops_updated_at ON shops(updated_at DESC);

-- Index pour analytics
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);
CREATE UNIQUE INDEX idx_analytics_shop_id_unique ON analytics(shop_id);

-- ========================================
-- 5. VÉRIFICATION DE LA STRUCTURE
-- ========================================

-- Afficher la structure finale
.schema shops
.schema analytics

-- Compter les tables
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Compter les index
SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;


