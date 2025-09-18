/**
 * Scraper TrendTrack - Classe principale
 */

import { WebScraper } from './scraper.js';
import { TrendTrackExtractor } from './extractors/trendtrack-extractor.js';

export class TrendTrackScraper {
  constructor() {
    this.webScraper = new WebScraper();
    this.extractor = null;
  }

  /**
   * Initialise le scraper
   */
  async init() {
    console.log('🚀 Initialisation du scraper...');
    
    try {
      await this.webScraper.init();
      this.extractor = new TrendTrackExtractor(this.webScraper.page, this.webScraper.errorHandler);
      
      console.log('✅ Scraper initialisé');
      return true;
    } catch (error) {
      console.error('❌ Erreur initialisation:', error.message);
      return false;
    }
  }

  /**
   * Se connecte à TrendTrack
   */
  async login(email, password) {
    console.log('🔑 Connexion à TrendTrack...');
    
    try {
      const loginSuccess = await this.extractor.login(email, password);
      
      if (loginSuccess) {
        console.log('✅ Connexion réussie');
        return true;
      } else {
        console.error('❌ Échec de la connexion');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur connexion:', error.message);
      return false;
    }
  }

  /**
   * Navigue vers la page des boutiques tendances
   */
  async navigateToTrendingShops() {
    console.log('📊 Navigation vers les boutiques tendances...');
    
    try {
      const navigationSuccess = await this.extractor.navigateToTrendingShops();
      
      if (navigationSuccess) {
        console.log('✅ Navigation réussie');
        return true;
      } else {
        console.error('❌ Échec de la navigation');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur navigation:', error.message);
      return false;
    }
  }

  /**
   * Applique le tri par Live Ads
   */
  async sortByLiveAds() {
    console.log('📈 Tri par Live Ads...');
    
    try {
      const sortSuccess = await this.extractor.sortByLiveAds();
      
      if (sortSuccess) {
        console.log('✅ Tri par Live Ads appliqué');
        return true;
      } else {
        console.log('⚠️ Tri par Live Ads non appliqué, continuation...');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur tri Live Ads:', error.message);
      return false;
    }
  }

  /**
   * Scrape plusieurs pages
   * @param {number} maxPages - Nombre maximum de pages à scraper
   * @param {boolean} includeMarketData - Inclure les données de trafic par pays
   */
  async scrapeMultiplePages(maxPages = 30, includeMarketData = false) {
    console.log(`📋 Scraping de ${maxPages} pages...`);
    
    try {
      const allShopsData = await this.extractor.scrapeMultiplePages(maxPages, includeMarketData);
      
      console.log(`✅ Scraping terminé: ${allShopsData.length} boutiques extraites`);
      return allShopsData;
      
    } catch (error) {
      console.error('❌ Erreur lors du scraping:', error.message);
      return [];
    }
  }

  /**
   * Ferme le scraper
   */
  async close() {
    console.log('🔚 Fermeture du scraper...');
    
    try {
      await this.webScraper.close();
      console.log('✅ Scraper fermé');
    } catch (error) {
      console.error('❌ Erreur fermeture:', error.message);
    }
  }
} 