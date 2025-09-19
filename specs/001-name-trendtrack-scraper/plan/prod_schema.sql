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
CREATE TABLE analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id INTEGER NOT NULL, organic_traffic TEXT, bounce_rate TEXT, avg_visit_duration TEXT, branded_traffic TEXT, conversion_rate TEXT, scraping_status TEXT DEFAULT 'completed', updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, visits TEXT, traffic TEXT, percent_branded_traffic REAL, paid_search_traffic TEXT, FOREIGN KEY (shop_id) REFERENCES shops (id));
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_scraping_status ON analytics(scraping_status);
CREATE UNIQUE INDEX idx_analytics_shop_id_unique 
                ON analytics(shop_id)
            ;
CREATE TABLE IF NOT EXISTS "shops" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT,
    shop_url TEXT UNIQUE NOT NULL,
    scraping_status TEXT,
    scraping_last_update TEXT,
    updated_at TEXT,
    creation_date TEXT,
    monthly_visits TEXT,
    monthly_revenue TEXT,
    live_ads TEXT,
    page_number TEXT,
    scraped_at TEXT,
    project_source TEXT,
    external_id TEXT,
    metadata TEXT
, year_founded TEXT);
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_scraping_last_update ON shops(scraping_last_update);
CREATE INDEX idx_shops_shop_url ON shops(shop_url);
CREATE INDEX idx_shops_url ON shops(shop_url);
CREATE INDEX idx_shops_live_ads ON shops(live_ads);
CREATE INDEX idx_shops_scraped_at ON shops(scraped_at);
CREATE INDEX idx_shops_project_source ON shops(project_source);
CREATE INDEX idx_shops_external_id ON shops(external_id);
CREATE INDEX idx_shops_live_ads_scraped_at ON shops(live_ads DESC, scraped_at DESC);
CREATE INDEX idx_shops_project_live_ads ON shops(project_source, live_ads DESC);
CREATE INDEX idx_shops_updated_at ON shops(updated_at DESC);
