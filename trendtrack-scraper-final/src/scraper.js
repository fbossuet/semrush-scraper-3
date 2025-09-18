/**
 * WebScraper - Classe de base pour le scraping web
 */

import { chromium } from 'playwright';
import { CacheManager } from './utils/cache-manager.js';
import { ErrorHandler } from './utils/error-handler.js';

export class WebScraper {
  constructor() {
    this.browser = null;
    this.page = null;
    this.cacheManager = new CacheManager();
    this.errorHandler = new ErrorHandler();
  }

  /**
   * Initialise le scraper
   */
  async init() {
    console.log('🚀 Initialisation du scraper...');
    
    try {
      // Lancer le navigateur
      this.browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      
      // Créer une nouvelle page
      this.page = await this.browser.newPage();
      
      // Configurer la page
      await this.page.setViewportSize({ width: 1920, height: 1080 });
      await this.page.setExtraHTTPHeaders({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      });
      
      console.log('✅ Scraper initialisé');
      return true;
    } catch (error) {
      console.error('❌ Erreur initialisation:', error.message);
      return false;
    }
  }

  /**
   * Ferme le scraper
   */
  async close() {
    console.log('🔚 Fermeture du scraper...');
    
    try {
      if (this.browser) {
        await this.browser.close();
      }
      console.log('✅ Scraper fermé');
    } catch (error) {
      console.error('❌ Erreur fermeture:', error.message);
    }
  }
} 