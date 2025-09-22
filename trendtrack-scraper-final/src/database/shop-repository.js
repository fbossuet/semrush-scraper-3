/**
 * Repository pour les opérations sur les boutiques - VERSION CORRIGÉE
 */

import fs from 'fs';

export class ShopRepository {
  constructor(databaseManager) {
    this.db = databaseManager;
    this.cache = new Map();
    this.cacheTimeout = 1000; // 5 minutes
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
      
      // 1. Insérer dans la table shops avec mapping dynamique
      const shopColumns = [
        'shop_name', 'shop_url', 'scraping_status', 'scraping_last_update', 'updated_at',
        'creation_date', 'monthly_visits', 'monthly_revenue', 'live_ads', 'live_ads_7d', 'live_ads_30d', 'page_number',
        'scraped_at', 'project_source', 'external_id', 'metadata', 'year_founded',
        'total_products', 'pixel_google', 'pixel_facebook', 'aov',
        'market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr',
        'category'
      ];
      
      // Mapping dynamique des données
      const shopValues = {
        'shop_name': shopData.shopName || '',
        'shop_url': urlToSave,
        'scraping_status': shopData.scrapingStatus || null,
        'scraping_last_update': shopData.scrapingLastUpdate || null,
        'updated_at': new Date().toISOString(),
        'creation_date': shopData.creationDate || '',
        'monthly_visits': shopData.monthlyVisits || null,
        'monthly_revenue': shopData.monthlyRevenue || '',
        'live_ads': shopData.liveAds || '',
        'live_ads_7d': shopData.liveAds7d || 0,
        'live_ads_30d': shopData.liveAds30d || 0,
        'page_number': shopData.page || 1,
        'scraped_at': shopData.scrapedAt || null,
        'project_source': shopData.projectSource || 'trendtrack',
        'external_id': shopData.externalId || null,
        'metadata': shopData.metadata ? JSON.stringify(shopData.metadata) : null,
        'year_founded': shopData.yearFounded || null,
        'total_products': shopData.totalProducts || null,
        'pixel_google': shopData.pixelGoogle || "non",
        'pixel_facebook': shopData.pixelFacebook || "non",
        'aov': shopData.aov || null,
        'market_us': shopData.marketUs || null,
        'market_uk': shopData.marketUk || null,
        'market_de': shopData.marketDe || null,
        'market_ca': shopData.marketCa || null,
        'market_au': shopData.marketAu || null,
        'market_fr': shopData.marketFr || null,
        'category': shopData.category || ''
      };
      
      // Construire la requête dynamiquement
      const columnsClause = shopColumns.join(', ');
      const placeholders = shopColumns.map(() => '?').join(', ');
      const values = shopColumns.map(col => shopValues[col]);
      
      const upsertStmt = db.prepare(`
        INSERT OR REPLACE INTO shops (${columnsClause})
        VALUES (${placeholders})
      `);
      
      const result = upsertStmt.run(values);
      
      const shopId = result.lastInsertRowid;
      
      // 2. Si des données analytiques sont présentes, les insérer dans la table analytics
      if (shopData.conversionRate || shopData.organicTraffic || shopData.brandedTraffic || 
          shopData.bounceRate || shopData.averageVisitDuration) {
        
        // Mapping dynamique pour la table analytics
        const analyticsColumns = [
          'shop_id', 'organic_traffic', 'bounce_rate', 'avg_visit_duration', 'branded_traffic',
          'conversion_rate', 'scraping_status', 'updated_at', 'visits', 'traffic',
          'paid_search_traffic', 'percent_branded_traffic', 'cpc'
        ];
        
        const analyticsValues = {
          'shop_id': shopId,
          'organic_traffic': shopData.organicTraffic || null,
          'bounce_rate': shopData.bounceRate || null,
          'avg_visit_duration': shopData.averageVisitDuration || null,
          'branded_traffic': shopData.brandedTraffic || null,
          'conversion_rate': shopData.conversionRate || null,
          'scraping_status': shopData.scrapingStatus || 'completed',
          'updated_at': new Date().toISOString(),
          'visits': shopData.visits || null,
          'traffic': shopData.traffic || null,
          'paid_search_traffic': shopData.paidSearchTraffic || null,
          'percent_branded_traffic': shopData.percentBrandedTraffic || null,
          'cpc': shopData.cpc || null
        };
        
        // Construire la requête dynamiquement
        const analyticsColumnsClause = analyticsColumns.join(', ');
        const analyticsPlaceholders = analyticsColumns.map(() => '?').join(', ');
        const analyticsValuesArray = analyticsColumns.map(col => analyticsValues[col]);
        
        const analyticsStmt = db.prepare(`
          INSERT OR REPLACE INTO analytics (${analyticsColumnsClause})
          VALUES (${analyticsPlaceholders})
        `);
        
        analyticsStmt.run(analyticsValuesArray);
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
      // const cached = this._getFromCache(cacheKey);
      // if (cached) return cached;
      
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
      // const cached = this._getFromCache(cacheKey);
      // if (cached) return cached;
      
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
      // const cached = this._getFromCache(cacheKey);
      // if (cached) return cached;
      
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
   * Insère UNIQUEMENT les données du tableau (nouvelle méthode pour architecture parallèle)
   * @param {Object} shopData - Données du tableau uniquement
   * @returns {Promise<number>} - ID de la boutique insérée
   */
  async insertTableData(shopData) {
    try {
      const normalizedUrl = ShopRepository.normalizeUrl(shopData.shop_url || shopData.shopUrl);
      
      const db = this._getConnection();
      const stmt = db.prepare(`
        INSERT INTO shops (
          shop_name, shop_url, category, monthly_visits, monthly_revenue,
          total_products, live_ads_7d, live_ads_30d, scraping_status, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
      
      const params = [
        shopData.shop_name || shopData.shopName,
        normalizedUrl,
        shopData.category,
        shopData.monthly_visits || 0,
        shopData.monthly_revenue || 0,
        shopData.total_products || 0,
        shopData.live_ads_7d || 0,
        shopData.live_ads_30d || 0,
        'table_extracted',
        new Date().toISOString()
      ];
      
      const result = stmt.run(params);
      this._clearCache();
      
      console.log(`✅ Boutique insérée avec ID: ${result.lastInsertRowid}`);
      return result.lastInsertRowid;
      
    } catch (error) {
      console.error('❌ Erreur insertion données tableau:', error.message);
      throw error;
    }
  }

  /**
   * Met à jour UNIQUEMENT les données du tableau (nouvelle méthode pour architecture parallèle)
   * @param {number} id - ID de la boutique
   * @param {Object} shopData - Données du tableau
   * @returns {Promise<boolean>} - Succès de la mise à jour
   */
  async updateTableData(id, shopData) {
    try {
      const normalizedUrl = ShopRepository.normalizeUrl(shopData.shop_url || shopData.shopUrl);
      
      const db = this._getConnection();
      const stmt = db.prepare(`
        UPDATE shops SET
          shop_name = ?, shop_url = ?, category = ?, monthly_visits = ?,
          monthly_revenue = ?, total_products = ?, live_ads_7d = ?, live_ads_30d = ?,
          scraping_status = ?, last_updated = ?
        WHERE id = ?
      `);
      
      const params = [
        shopData.shop_name || shopData.shopName,
        normalizedUrl,
        shopData.category,
        shopData.monthly_visits || 0,
        shopData.monthly_revenue || 0,
        shopData.total_products || 0,
        shopData.live_ads_7d || 0,
        shopData.live_ads_30d || 0,
        'table_extracted',
        new Date().toISOString(),
        id
      ];
      
      const result = stmt.run(params);
      this._clearCache();
      
      console.log(`✅ Données tableau mises à jour pour ID: ${id}`);
      return result.changes > 0;
      
    } catch (error) {
      console.error('❌ Erreur mise à jour données tableau:', error.message);
      throw error;
    }
  }

  /**
   * Met à jour UNIQUEMENT les métriques de détail (nouvelle méthode pour architecture parallèle)
   * @param {number} id - ID de la boutique
   * @param {Object} detailData - Données de détail
   * @returns {Promise<boolean>} - Succès de la mise à jour
   */
  async updateDetailMetrics(id, detailData) {
    try {
      const db = this._getConnection();
      
      // Vérifier si c'est un échec critique
      if (detailData.scraping_status === 'failed') {
        console.log(`❌ Échec critique détecté pour ID: ${id} - marquage comme failed`);
        
        // Mettre à jour le statut à 'failed' dans la table shops
        const failedStmt = db.prepare(`
          UPDATE shops SET
            scraping_status = ?, updated_at = ?
          WHERE id = ?
        `);
        
        failedStmt.run(['failed', new Date().toISOString(), id]);
        this._clearCache();
        
        console.log(`❌ Boutique ID: ${id} marquée comme failed`);
        return false;
      }
      
      // 1. Mettre à jour les métriques dans la table analytics
      const analyticsStmt = db.prepare(`
        INSERT OR REPLACE INTO analytics (
          shop_id, organic_traffic, bounce_rate, avg_visit_duration, 
          branded_traffic, conversion_rate, scraping_status, updated_at,
          visits, traffic, paid_search_traffic, percent_branded_traffic, cpc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
      
      const analyticsParams = [
        id,
        detailData.organic_traffic || null,
        detailData.bounce_rate || null,
        detailData.avg_visit_duration || null,
        detailData.branded_traffic || null,
        detailData.conversion_rate || null,
        detailData.scraping_status || 'details_extracted',
        new Date().toISOString(),
        detailData.visits || null,
        detailData.traffic || null,
        detailData.paid_search_traffic || null,
        detailData.percent_branded_traffic || null,
        detailData.cpc || null
      ];
      
      analyticsStmt.run(analyticsParams);
      
      // 2. Mettre à jour les métriques de marché et autres dans la table shops
      const shopsStmt = db.prepare(`
        UPDATE shops SET
          market_us = ?, market_uk = ?, market_de = ?, market_ca = ?, market_au = ?, market_fr = ?,
          pixel_google = ?, pixel_facebook = ?, year_founded = ?, aov = ?,
          scraping_status = ?, updated_at = ?
        WHERE id = ?
      `);
      
      const shopsParams = [
        detailData.market_us || 0,
        detailData.market_uk || 0,
        detailData.market_de || 0,
        detailData.market_ca || 0,
        detailData.market_au || 0,
        detailData.market_fr || 0,
        detailData.pixel_google || "non",
        detailData.pixel_facebook || "non",
        detailData.year_founded || null,
        detailData.aov || null,
        detailData.scraping_status || 'details_extracted',
        new Date().toISOString(),
        id
      ];
      
      const result = shopsStmt.run(shopsParams);
      this._clearCache();
      
      console.log(`✅ Métriques de détail mises à jour pour ID: ${id}`);
      return result.changes > 0;
      
    } catch (error) {
      console.error('❌ Erreur mise à jour métriques détail:', error.message);
      
      // En cas d'erreur critique, marquer comme failed
      try {
        const db = this._getConnection();
        const failedStmt = db.prepare(`
          UPDATE shops SET
            scraping_status = ?, updated_at = ?
          WHERE id = ?
        `);
        
        failedStmt.run(['failed', new Date().toISOString(), id]);
        console.log(`❌ Boutique ID: ${id} marquée comme failed suite à une erreur`);
      } catch (updateError) {
        console.error('❌ Erreur lors du marquage failed:', updateError.message);
      }
      
      throw error;
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
            updated_at = ?
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
        new Date().toISOString(),
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
   * Trouve les boutiques par statut de scraping
   */
  async findByStatus(status) {
    try {
      const db = this._getConnection();
      const stmt = db.prepare('SELECT * FROM shops WHERE scraping_status = ?');
      const shops = stmt.all(status);
      
      // Mapper les noms de colonnes de la base vers les noms attendus par le code
      const mappedShops = shops.map(shop => ({
        id: shop.id,
        shopName: shop.shop_name,
        shopUrl: shop.shop_url,
        category: shop.category,
        monthlyVisits: shop.monthly_visits,
        monthlyRevenue: shop.monthly_revenue,
        totalProducts: shop.total_products,
        liveAds: shop.live_ads,
        creationDate: shop.creation_date,
        scraping_status: shop.scraping_status,
        last_updated: shop.last_updated
      }));
      
      console.log(`🔍 Trouvé ${mappedShops.length} boutiques avec statut: ${status}`);
      return mappedShops;
    } catch (error) {
      console.error('❌ Erreur recherche par statut:', error.message);
      return [];
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
      // const cached = this._getFromCache(cacheKey);
      // if (cached) return cached;
      
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
