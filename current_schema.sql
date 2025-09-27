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
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE shops_backup(
  id INT,
  shop_name TEXT,
  shop_url TEXT,
  scraping_status TEXT,
  scraping_last_update TEXT,
  updated_at TEXT,
  creation_date TEXT,
  monthly_visits INT,
  monthly_revenue TEXT,
  live_ads TEXT,
  page_number TEXT,
  scraped_at TEXT,
  project_source TEXT,
  external_id TEXT,
  metadata TEXT,
  year_founded TEXT,
  total_products INT,
  pixel_google INT,
  pixel_facebook INT,
  aov NUM,
  market_us NUM,
  market_uk NUM,
  market_de NUM,
  market_ca NUM,
  market_au NUM,
  market_fr NUM,
  live_ads_7d INT,
  live_ads_30d INT,
  live_ads_new INT
);
CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    shop_url TEXT,
    total_products INTEGER,
    monthly_visits INTEGER,
    monthly_revenue TEXT,
    live_ads INTEGER,  -- ✅ Corrigé: INTEGER au lieu de TEXT
    aov NUMERIC,
    page_number TEXT,
    scraped_at TEXT,
    project_source TEXT,
    external_id TEXT,
    metadata TEXT,
    year_founded TEXT,  -- ✅ Correct: TEXT
    creation_date TEXT,
    scraping_status TEXT DEFAULT 'pending',
    live_ads_7d INTEGER,
    live_ads_30d INTEGER
, table_scraping_status TEXT DEFAULT 'pending', details_scraping_status TEXT DEFAULT 'pending', scraping_last_update TEXT, updated_at TEXT, pixel_google TEXT, pixel_facebook TEXT, market_us NUMERIC, market_uk NUMERIC, market_de NUMERIC, market_ca NUMERIC, market_au NUMERIC, market_fr NUMERIC, category TEXT);
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);
CREATE UNIQUE INDEX idx_analytics_shop_id_unique ON analytics(shop_id);
CREATE TABLE scraping_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER,
                    error_message TEXT,
                    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (shop_id) REFERENCES shops (id)
                );
CREATE TABLE processing_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_name TEXT UNIQUE NOT NULL,
                    process_id INTEGER,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
CREATE TABLE selector_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    selector_name TEXT NOT NULL,
                    success BOOLEAN,
                    response_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    page_load_time_ms INTEGER
                );
CREATE INDEX idx_shops_scraping_status 
                ON shops(scraping_status)
            ;
CREATE INDEX idx_shops_scraping_last_update 
                ON shops(scraping_last_update)
            ;
CREATE INDEX idx_shops_shop_url 
                ON shops(shop_url)
            ;
CREATE INDEX idx_processing_locks_lock_name 
                ON processing_locks(lock_name)
            ;
CREATE INDEX idx_selector_performance_selector_name 
                ON selector_performance(selector_name)
            ;
CREATE INDEX idx_selector_performance_timestamp 
                ON selector_performance(timestamp)
            ;
