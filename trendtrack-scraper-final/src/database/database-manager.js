import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

export class DatabaseManager {
  constructor(dbPath = './data/trendtrack.db') {
    this.dbPath = dbPath;
    this.db = null;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Initialise la connexion à la base de données
   */
  async init() {
    return true;
  }

  /**
   * Ferme la connexion à la base de données
   */
  async close() {
    return true;
  }

  /**
   * Normalise une URL
   */
  static normalizeUrl(url) {
    if (!url) return '';
    
    // Supprimer le protocole
    let normalized = url.replace(/^https?:\/\//, '');
    
    // Supprimer www.
    normalized = normalized.replace(/^www\./, '');
    
    // Supprimer le slash final
    normalized = normalized.replace(/\/$/, '');
    
    return normalized.toLowerCase();
  }

  /**
   * Obtient la connexion à la base de données
   */
  getConnection() {
    if (!this.db) {
      // Créer le répertoire si nécessaire
      const dir = path.dirname(this.dbPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      this.db = new Database(this.dbPath);
      this.db.pragma('journal_mode = WAL');
      this.db.pragma('foreign_keys = ON');
    }
    return this.db;
  }

  /**
   * Exécute une requête avec cache
   */
  async query(sql, params = []) {
    try {
      const cacheKey = this._getCacheKey(sql, params);
      const cached = this._getFromCache(cacheKey);
      if (cached) return cached;
      
      const db = this.getConnection();
      const stmt = db.prepare(sql);
      const result = stmt.all(params);
      
      this._setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('❌ Erreur requête:', error.message);
      return [];
    }
  }

  /**
   * Exécute une requête d'insertion/mise à jour
   */
  async execute(sql, params = []) {
    try {
      const db = this.getConnection();
      const stmt = db.prepare(sql);
      const result = stmt.run(params);
      this._clearCache();
      return result;
    } catch (error) {
      console.error('❌ Erreur exécution:', error.message);
      return null;
    }
  }

  /**
   * Gestion du cache
   */
  _getCacheKey(sql, params) {
    return `${sql}-${JSON.stringify(params)}`;
  }

  _getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && new Date().toISOString() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  _setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: new Date().toISOString()
    });
  }

  _clearCache() {
    this.cache.clear();
  }

  /**
   * Met à jour une boutique
   */
  async updateShop(id, shopData) {
    try {
      const stmt = this.db.db.prepare(`
        UPDATE shops 
        SET shop_name = ?, shop_url = ?, creation_date = ?, category = ?, 
            monthly_visits = ?, monthly_revenue = ?, live_ads = ?, 
            updated_at = datetime.now(timezone.utc).isoformat()
        WHERE id = ?
      `);

      const result = stmt.run([
        shopData.shopName || '',
        shopData.shopUrl || '',
        shopData.creationDate || '',
        shopData.category || '',
        shopData.monthlyVisits || '',
        shopData.monthlyRevenue || '',
        parseInt(shopData.liveAds) || 0,
        id
      ]);

      if (result.changes > 0) {
        this._clearCache();
        return true;
      }
      return false;
    } catch (error) {
      console.error('❌ Erreur mise à jour boutique:', error.message);
      return false;
    }
  }

  /**
   * Supprime une boutique
   */
  async delete(id) {
    try {
      const stmt = this.db.db.prepare('DELETE FROM shops WHERE id = ?');
      const result = stmt.run(id);
      
      if (result.changes > 0) {
        this._clearCache();
        return true;
      }
      return false;
    } catch (error) {
      console.error('❌ Erreur suppression boutique:', error.message);
      return false;
    }
  }

  /**
   * Met à jour les métriques d'analyse d'une boutique
   */
  async updateAnalytics(id, analyticsData) {
    try {
      const stmt = this.db.db.prepare(`
        INSERT OR REPLACE INTO analytics 
        (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, scraping_status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat())
      `);

      const result = stmt.run([
        id,
        analyticsData.organic_traffic || null,
        analyticsData.bounce_rate || null,
        analyticsData.average_visit_duration || null,
        analyticsData.branded_traffic || null,
        analyticsData.conversion_rate || null,
        analyticsData.scraping_status || 'completed'
      ]);

      if (result.changes > 0) {
        this._clearCache();
        return true;
      }
      return false;
    } catch (error) {
      console.error('❌ Erreur mise à jour métriques:', error.message);
      return false;
    }
  }

  /**
   * Recherche de boutiques
   */
  async search(query) {
    try {
      const cacheKey = this._getCacheKey('search', query);
      const cached = this._getFromCache(cacheKey);
      if (cached) return cached;
      
      const stmt = this.db.db.prepare(`
        SELECT * FROM shops 
        WHERE shop_name LIKE ? OR shop_url LIKE ? OR category LIKE ?
        ORDER BY live_ads DESC
      `);
      const searchTerm = `%${query}%`;
      const result = stmt.all(searchTerm, searchTerm, searchTerm);
      
      this._setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('❌ Erreur recherche:', error.message);
      return [];
    }
  }
}
