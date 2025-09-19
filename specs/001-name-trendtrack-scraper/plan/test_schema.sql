CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    pages_scraped INTEGER DEFAULT 0,
    shops_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    project_source TEXT DEFAULT 'trendtrack'
  );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE shared_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    project_path TEXT NOT NULL,
    api_key TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_access TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
  );
CREATE TABLE scraping_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shop_id INTEGER,
                        domain TEXT NOT NULL,
                        date_range TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        data JSON,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (shop_id) REFERENCES shops (id)
                    );
CREATE TABLE scraping_errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT,
                        error_type TEXT,
                        error_message TEXT,
                        occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
CREATE INDEX idx_sessions_started_at ON scraping_sessions(started_at DESC);
CREATE INDEX idx_sessions_project_status ON scraping_sessions(project_source, status);
CREATE INDEX idx_projects_api_key ON shared_projects(api_key);
CREATE INDEX idx_projects_active ON shared_projects(is_active, last_access DESC);
CREATE INDEX idx_processing_locks_lock_name 
                ON processing_locks(lock_name)
            ;
CREATE INDEX idx_selector_performance_selector_name 
                ON selector_performance(selector_name)
            ;
CREATE INDEX idx_selector_performance_timestamp 
                ON selector_performance(timestamp)
            ;
CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT,
    shop_url TEXT UNIQUE NOT NULL,
    scraping_status TEXT,
    monthly_visits INTEGER,  -- TEXT → INTEGER
    monthly_revenue TEXT,
    live_ads TEXT,
    page_number TEXT,
    scraped_at TEXT,
    project_source TEXT,
    external_id TEXT,
    metadata TEXT,
    creation_date DATE,
    scraping_last_update DATE,
    year_founded DATE,
    total_products INTEGER,
    pixel_google INTEGER,
    pixel_facebook INTEGER,
    aov NUMERIC,  -- NUMERIC → decimal (gardé NUMERIC)
    market_us NUMERIC,  -- NUMERIC → decimal
    market_uk NUMERIC,
    market_de NUMERIC,
    market_ca NUMERIC,
    market_au NUMERIC,
    market_fr NUMERIC
);
CREATE TABLE IF NOT EXISTS "analytics" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    organic_traffic INTEGER,  -- TEXT → INTEGER
    bounce_rate NUMERIC,  -- TEXT → decimal (NUMERIC)
    avg_visit_duration TEXT,  -- Format MM:SS
    branded_traffic INTEGER,  -- TEXT → INTEGER
    conversion_rate TEXT,
    scraping_status TEXT DEFAULT 'completed',
    visits INTEGER,  -- TEXT → INTEGER
    traffic INTEGER,  -- TEXT → INTEGER
    paid_search_traffic INTEGER,  -- TEXT → INTEGER
    percent_branded_traffic NUMERIC,  -- NUMERIC → decimal
    cpc NUMERIC,  -- NUMERIC → decimal
    updated_at DATE,
    FOREIGN KEY (shop_id) REFERENCES "shops" (id)
);
