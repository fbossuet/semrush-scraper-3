/**
 * Repository pour les opérations sur les boutiques - VERSION CORRIGÉE
 */

import fs from 'fs';

export class ShopRepository {
  constructor(databaseManager) {
    this.db = databaseManager;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Normalise une URL de boutique pour comparaison stricte
   */
  static normalizeUrl(url) {
    if (!url) return '';
    return url
      .replace(/^https?:\/\//, '')
      .replace(/^www\./, '')
      .replace(/\/$/, '')
      .toLowerCase();
  }

  /**
   * Gestion du cache
   */
  _getCacheKey(method, ...args) {
    return `${method}:${JSON.stringify(args)}`;
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
   * Obtient la connexion à la base de données
   */
  _getConnection() {
    return this.db.getConnection();
  }

  /**
   * Crée ou met à jour une boutique
   */
  async upsert(shopData) {
    try {
      let urlToSave = shopData.shopUrl || '';
      if (!urlToSave.startsWith('http')) urlToSave = 'https://' + urlToSave;
      urlToSave = urlToSave.replace(/\/$/, '');
      
      const db = this._getConnection();
      
      // 1. Insérer dans la table shops
      const upsertStmt = db.prepare(`
        INSERT OR REPLACE INTO shops
          (shop_name, shop_url, creation_date, category, monthly_visits, monthly_revenue, live_ads, page_number, updated_at, project_source, external_id, metadata, scraping_status, scraping_last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat(), ?, ?, ?, ?, ?)
      `);
      
      const result = upsertStmt.run([
        shopData.shopName || '',
        urlToSave,
        shopData.creationDate || '',
        shopData.category || '',
        shopData.monthlyVisits || '',
        shopData.monthlyRevenue || '',
        parseInt(shopData.liveAds) || 0,
        shopData.page || 1,
        shopData.projectSource || 'trendtrack',
        shopData.externalId || null,
        shopData.metadata ? JSON.stringify(shopData.metadata) : null,
        shopData.scrapingStatus || null,
        shopData.scrapingLastUpdate || null
      ]);
      
      const shopId = result.lastInsertRowid;
      
      // 2. Si des données analytiques sont présentes, les insérer dans la table analytics
      if (shopData.conversionRate || shopData.organicTraffic || shopData.brandedTraffic || 
          shopData.bounceRate || shopData.averageVisitDuration) {
        
        const analyticsStmt = db.prepare(`
          INSERT OR REPLACE INTO analytics 
          (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, scraping_status, updated_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat())
        `);
        
        analyticsStmt.run([
          shopId,
          shopData.organicTraffic || null,
          shopData.bounceRate || null,
          shopData.averageVisitDuration || null,
          shopData.brandedTraffic || null,
          shopData.conversionRate || null,
          shopData.scrapingStatus || 'completed'
        ]);
      }
      
      this._clearCache();
      return shopId;
    } catch (error) {
      console.error('❌ Erreur upsert:', error.message);
      return null;
    }
  }

  /**
   * Récupère toutes les boutiques avec pagination
   */
  async getAllWithPagination(limit = 100, offset = 0) {
    try {
      const cacheKey = this._getCacheKey('getAllWithPagination', limit, offset);
      const cached = this._getFromCache(cacheKey);
      if (cached) return cached;
      
      const db = this._getConnection();
      const stmt = db.prepare(`
        SELECT * FROM shops 
        ORDER BY updated_at DESC 
        LIMIT ? OFFSET ?
      `);
      
      const result = stmt.all(limit, offset);
      this._setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('❌ Erreur récupération avec pagination:', error.message);
      return [];
    }
  }

  /**
   * Récupère une boutique par ID
   */
  async getById(id) {
    try {
      const cacheKey = this._getCacheKey('getById', id);
      const cached = this._getFromCache(cacheKey);
      if (cached) return cached;
      
      const db = this._getConnection();
      const stmt = db.prepare('SELECT * FROM shops WHERE id = ?');
      const result = stmt.get(id);
      
      this._setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('❌ Erreur récupération par ID:', error.message);
      return null;
    }
  }

  /**
   * Récupère une boutique par URL
   */
  async getByUrl(url) {
    try {
      const normalizedUrl = ShopRepository.normalizeUrl(url);
      const cacheKey = this._getCacheKey('getByUrl', normalizedUrl);
      const cached = this._getFromCache(cacheKey);
      if (cached) return cached;
      
      const db = this._getConnection();
      const stmt = db.prepare(`
        SELECT * FROM shops 
        WHERE LOWER(REPLACE(REPLACE(shop_url, 'https://', ''), 'http://', '')) = ?
      `);
      const result = stmt.get(normalizedUrl);
      
      this._setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('❌ Erreur récupération par URL:', error.message);
      return null;
    }
  }

  /**
   * Met à jour une boutique
   */
  async update(id, shopData) {
    try {
      const db = this._getConnection();
      const stmt = db.prepare(`
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
      const db = this._getConnection();
      const stmt = db.prepare('DELETE FROM shops WHERE id = ?');
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
      const db = this._getConnection();
      const stmt = db.prepare(`
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
      
      const db = this._getConnection();
      const stmt = db.prepare(`
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
