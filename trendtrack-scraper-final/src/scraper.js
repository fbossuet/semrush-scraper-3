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
    this.userAgents = [
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ];
  }

  /**
   * Génère un délai aléatoire pour éviter la détection
   */
  async randomDelay(min = 1000, max = 3000) {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  /**
   * Sélectionne un User-Agent aléatoire
   */
  getRandomUserAgent() {
    return this.userAgents[Math.floor(Math.random() * this.userAgents.length)];
  }

  /**
   * Initialise le scraper avec configuration stealth
   */
  async init() {
    console.log('🚀 Initialisation du scraper...');
    
    try {
      // Lancer le navigateur avec options stealth
      this.browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-blink-features=AutomationControlled',
          '--disable-features=VizDisplayCompositor',
          '--disable-web-security',
          '--disable-features=TranslateUI',
          '--disable-ipc-flooding-protection',
          '--no-first-run',
          '--no-default-browser-check',
          '--disable-default-apps',
          '--disable-popup-blocking',
          '--disable-extensions',
          '--disable-plugins',
          '--disable-images',
          '--disable-javascript',
          '--disable-plugins-discovery',
          '--disable-preconnect',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding'
        ]
      });
      
      // Créer une nouvelle page
      this.page = await this.browser.newPage();
      
      // Configuration stealth avancée
      await this.page.setViewportSize({ 
        width: 1920 + Math.floor(Math.random() * 100), 
        height: 1080 + Math.floor(Math.random() * 100) 
      });
      
      // User-Agent aléatoire
      const userAgent = this.getRandomUserAgent();
      await this.page.setExtraHTTPHeaders({
        'User-Agent': userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
      });
      
      // Masquer les propriétés de détection
      await this.page.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
          get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
          get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
          runtime: {},
        };
      });
      
      console.log('✅ Scraper initialisé avec configuration stealth');
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