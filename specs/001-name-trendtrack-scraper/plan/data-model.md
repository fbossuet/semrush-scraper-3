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
- `scraping_status` (TEXT): Current processing status
  - Values: 'completed', 'partial', 'failed', 'na', 'pending', ''
  - Default: 'pending'
- `scraping_last_update` (TEXT): ISO timestamp of last scraping attempt
- `updated_at` (TEXT): ISO timestamp of last record update
- `creation_date` (TEXT): ISO timestamp of record creation
- `monthly_visits` (TEXT): Monthly visits data (if available)
- `monthly_revenue` (TEXT): Monthly revenue data (if available)
- `live_ads` (TEXT): Live ads information
- `page_number` (TEXT): Page number in source data
- `scraped_at` (TEXT): ISO timestamp of last successful scraping
- `project_source` (TEXT): Source of the website data
- `external_id` (TEXT): External system identifier
- `metadata` (TEXT): JSON string with additional metadata
- `year_founded` (TEXT): Year the website was founded

**Validation Rules**:
- `shop_url` must be a valid URL format
- `scraping_status` must be one of the defined values
- `scraping_last_update` must be valid ISO timestamp when not null
- `updated_at` must be valid ISO timestamp when not null

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
    metadata TEXT,
    year_founded TEXT
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
    session_name TEXT,
    status TEXT,
    target_status TEXT,
    worker_count INTEGER,
    websites_per_worker INTEGER,
    total_websites INTEGER,
    processed_websites INTEGER,
    successful_websites INTEGER,
    failed_websites INTEGER,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT
);
```

### Workers Table
```sql
CREATE TABLE IF NOT EXISTS "workers" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    worker_id INTEGER,
    status TEXT,
    assigned_websites TEXT,
    processed_websites TEXT,
    current_website_id INTEGER,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions (id),
    FOREIGN KEY (current_website_id) REFERENCES shops (id)
);
```

## Indexes

### Performance Indexes
```sql
CREATE INDEX idx_shops_scraping_status ON shops(scraping_status);
CREATE INDEX idx_shops_scraping_last_update ON shops(scraping_last_update);
CREATE INDEX idx_shops_shop_url ON shops(shop_url);
CREATE INDEX idx_analytics_shop_id ON analytics(shop_id);
CREATE INDEX idx_analytics_updated_at ON analytics(updated_at);
CREATE INDEX idx_workers_session_id ON workers(session_id);
CREATE INDEX idx_workers_status ON workers(status);
```

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
