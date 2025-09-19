/**
 * Schéma de la base de données TrendTrack
 */

export const SCHEMA = `
  -- Table des boutiques (adaptée pour le VPS)
  CREATE TABLE IF NOT EXISTS shops (
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

  -- Table des sessions de scraping
  CREATE TABLE IF NOT EXISTS scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
    ended_at TIMESTAMP,
    pages_scraped INTEGER DEFAULT 0,
    shops_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    project_source TEXT DEFAULT 'trendtrack'
  );

  -- Table des projets partagés
  CREATE TABLE IF NOT EXISTS shared_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    project_path TEXT NOT NULL,
    api_key TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT datetime.now(timezone.utc).isoformat(),
    last_access TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
  );

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
`;

export const QUERIES = {
  // Insérer ou mettre à jour une boutique
  UPSERT_SHOP: `
    INSERT OR REPLACE INTO shops 
    (shop_name, shop_url, creation_date, category, monthly_visits, monthly_revenue, live_ads, live_ads_7d, live_ads_30d, page_number, updated_at, project_source, external_id, metadata, year_founded, total_products, pixel_google, pixel_facebook, aov, market_us, market_uk, market_de, market_ca, market_au, market_fr, scraping_status, scraping_last_update)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,

  // Récupérer toutes les boutiques
  GET_ALL_SHOPS: `
    SELECT * FROM shops 
    ORDER BY live_ads DESC, scraped_at DESC
  `,

  // Récupérer les boutiques par projet
  GET_SHOPS_BY_PROJECT: `
    SELECT * FROM shops 
    WHERE project_source = ?
    ORDER BY live_ads DESC, scraped_at DESC
  `,

  // Récupérer les boutiques par domaine (extrait de l'URL)
  GET_SHOPS_BY_DOMAIN: `
    SELECT * FROM shops 
    WHERE shop_url LIKE ?
    ORDER BY scraped_at DESC
  `,

  // Récupérer les top boutiques par Live Ads
  GET_TOP_BY_LIVE_ADS: `
    SELECT * FROM shops 
    WHERE live_ads > 0
    ORDER BY live_ads DESC 
    LIMIT ?
  `,

  // Récupérer les boutiques par catégorie
  GET_BY_CATEGORY: `
    SELECT * FROM shops 
    WHERE category = ?
    ORDER BY live_ads DESC
  `,

  // Statistiques générales
  GET_STATS: `
    SELECT 
      COUNT(*) as total_shops,
      COUNT(DISTINCT category) as total_categories,
      COUNT(DISTINCT project_source) as total_projects,
      AVG(live_ads) as avg_live_ads,
      MAX(live_ads) as max_live_ads,
      MIN(live_ads) as min_live_ads
    FROM shops
  `,

  // Statistiques par projet
  GET_STATS_BY_PROJECT: `
    SELECT 
      project_source,
      COUNT(*) as total_shops,
      COUNT(DISTINCT category) as total_categories,
      AVG(live_ads) as avg_live_ads,
      MAX(live_ads) as max_live_ads
    FROM shops
    GROUP BY project_source
  `,

  // Créer une session de scraping
  CREATE_SESSION: `
    INSERT INTO scraping_sessions (started_at, status, project_source)
    VALUES (datetime.now(timezone.utc).isoformat(), 'running', ?)
  `,

  // Mettre à jour une session
  UPDATE_SESSION: `
    UPDATE scraping_sessions 
    SET ended_at = datetime.now(timezone.utc).isoformat(), 
        pages_scraped = ?, 
        shops_found = ?, 
        status = ?
    WHERE id = ?
  `,

  // Gestion des projets partagés
  CREATE_SHARED_PROJECT: `
    INSERT INTO shared_projects (project_name, project_path, api_key)
    VALUES (?, ?, ?)
  `,

  GET_SHARED_PROJECTS: `
    SELECT * FROM shared_projects WHERE is_active = 1
  `,

  UPDATE_PROJECT_ACCESS: `
    UPDATE shared_projects 
    SET last_access = datetime.now(timezone.utc).isoformat()
    WHERE api_key = ?
  `,

  // Recherche avancée
  SEARCH_SHOPS: `
    SELECT * FROM shops 
    WHERE (shop_name LIKE ? OR shop_url LIKE ? OR category LIKE ?)
    ORDER BY live_ads DESC
  `,

  // Récupérer les domaines uniques (extraits des URLs)
  GET_UNIQUE_DOMAINS: `
    SELECT 
      REPLACE(REPLACE(REPLACE(shop_url, 'https://', ''), 'http://', ''), 'www.', '') as domain,
      COUNT(*) as shop_count
    FROM shops 
    WHERE shop_url IS NOT NULL
    GROUP BY domain
    ORDER BY shop_count DESC
  `
}; 