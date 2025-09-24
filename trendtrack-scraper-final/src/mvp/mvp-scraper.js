/**
 * MVP Scraper - Orchestrateur principal MVP
 * 
 * Responsabilité: Coordination des solutions MVP et orchestration du scraping
 * Intègre: ContextManager, SessionManager, RetryHandler
 */

import { WebScraper } from '../scraper.js';
import { TrendTrackExtractor } from '../extractors/trendtrack-extractor.js';
import { MVPContextManager } from './mvp-context-manager.js';
import { MVPSessionManager } from './mvp-session-manager.js';
import { MVPRetryHandler } from './mvp-retry-handler.js';

export class MVPScraper {
  constructor(config, shopRepository = null) {
    this.config = config;
    this.browser = null;
    this.contextManager = null;
    this.sessionManager = null;
    this.retryHandler = null;
    this.extractor = null;
    this.shopRepository = shopRepository;
    this.isInitialized = false;
  }

  /**
   * Initialise le scraper MVP avec tous les composants
   */
  async initialize() {
    try {
      console.log('🚀 Initialisation du scraper MVP...');
      
      // 1. Créer le scraper de base
      this.browser = new WebScraper();
      await this.browser.init();
      
      // 2. Créer le gestionnaire de contexte
      this.contextManager = new MVPContextManager(this.browser.browser, this.config);
      await this.contextManager.createContext();
      
      // 3. Créer le gestionnaire de session
      this.sessionManager = new MVPSessionManager(this.contextManager, this.config);
      
      // 4. Créer l'extracteur TrendTrack
      this.extractor = new TrendTrackExtractor(
        this.contextManager.page, 
        this.browser.errorHandler
      );
      
      // 5. Créer le gestionnaire de retry
      this.retryHandler = new MVPRetryHandler(
        this.contextManager, 
        this.sessionManager, 
        this.extractor,
        this.config
      );
      
      // 6. Connexion initiale à TrendTrack
      await this.initialLogin();
      
      this.isInitialized = true;
      console.log('✅ Scraper MVP initialisé avec succès');
      
    } catch (error) {
      console.error('❌ Erreur initialisation scraper MVP:', error.message);
      throw error;
    }
  }

  /**
   * Connexion initiale à TrendTrack avec retry
   */
  async initialLogin() {
    console.log('🔑 Connexion initiale à TrendTrack...');
    
    const loginOperation = async () => {
      return await this.extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
    };
    
    try {
      const success = await this.retryHandler.executeWithRetry(
        loginOperation, 
        'initial_login', 
        3
      );
      
      if (success) {
        console.log('✅ Connexion initiale réussie');
        this.sessionManager.isSessionValid = true;
      } else {
        throw new Error('Échec de la connexion initiale');
      }
      
    } catch (error) {
      console.error('❌ Échec connexion initiale:', error.message);
      throw error;
    }
  }

  /**
   * Extrait les données du tableau (Phase 1 MVP)
   */
  async extractTableData(maxPages = 1) {
    console.log(`📋 Extraction Phase 1 MVP: ${maxPages} pages`);
    
    const extractOperation = async () => {
      // 1. D'abord naviguer vers la page des boutiques
      console.log('🌐 Navigation vers la page des boutiques...');
      await this.contextManager.page.goto('https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops?include=true&tab=websites&minTraffic=500000&languages=en&currencies=USD&creationCountry=US&orderBy=liveAds', {
        waitUntil: 'domcontentloaded',
        timeout: this.config.navigationTimeout
      });
      
      await this.contextManager.page.waitForTimeout(this.config.pageLoadPause);
      console.log('✅ Navigation vers la page des boutiques réussie');
      
      // 2. Ensuite extraire les données du tableau
      return await this.extractor.extractTableDataOnly();
    };
    
    try {
      const tableData = await this.retryHandler.executeWithRetry(
        extractOperation,
        'extract_table_data',
        3
      );
      
      console.log(`✅ Phase 1 MVP réussie: ${tableData.length} boutiques extraites`);
      return tableData;
      
    } catch (error) {
      console.error('❌ Échec Phase 1 MVP:', error.message);
      throw error;
    }
  }

  /**
   * Traite un lot de boutiques (Phase 3 MVP)
   */
  async processBatch(shops) {
    console.log(`🔄 Traitement lot MVP: ${shops.length} boutiques`);
    
    const batchResult = {
      success: 0,
      failed: 0,
      errors: []
    };
    
    for (const shop of shops) {
      try {
        console.log(`🔍 Extraction détails: ${shop.shopName}`);
        
        const success = await this.processShop(shop);
        
        if (success) {
          batchResult.success++;
          console.log(`✅ Détails extraits: ${shop.shopName}`);
        } else {
          batchResult.failed++;
          batchResult.errors.push({
            shopName: shop.shopName,
            error: 'Extraction échouée'
          });
          console.log(`❌ Échec extraction: ${shop.shopName}`);
        }
        
        // Pause entre les boutiques
        if (shops.indexOf(shop) < shops.length - 1) {
          await new Promise(resolve => setTimeout(resolve, this.config.betweenShopsPause));
        }
        
      } catch (error) {
        batchResult.failed++;
        batchResult.errors.push({
          shopName: shop.shopName,
          error: error.message
        });
        console.log(`❌ Erreur traitement ${shop.shopName}: ${error.message}`);
      }
    }
    
    console.log(`📊 Lot terminé: ${batchResult.success} succès, ${batchResult.failed} erreurs`);
    return batchResult;
  }

  /**
   * Traite une boutique individuelle avec récupération automatique
   */
  async processShop(shop) {
    const processOperation = async () => {
      // Navigation vers la page de détail
      const navSuccess = await this.navigateToShopDetail(shop.external_id);
      if (!navSuccess) {
        throw new Error(`Échec navigation vers ${shop.shopName}`);
      }
      
      // Extraction des détails
      const details = await this.extractShopDetails(shop.external_id);
      if (!details) {
        throw new Error(`Échec extraction détails pour ${shop.shopName}`);
      }
      
      // Sauvegarde des détails (utiliser l'ID de la base, pas l'external_id)
      await this.saveShopDetails(shop.id, details);
      
      return true;
    };
    
    try {
      return await this.retryHandler.executeWithRetry(
        processOperation,
        `shop_${shop.external_id}`,
        3
      );
      
    } catch (error) {
      console.log(`❌ Échec traitement ${shop.shopName}: ${error.message}`);
      return false;
    }
  }

  /**
   * Navigation vers la page de détail d'une boutique
   */
  async navigateToShopDetail(shopId) {
    const navOperation = async () => {
      const detailUrl = `https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${shopId}`;
      
      console.log(`🔍 Navigation vers la page de détail (UUID): ${shopId}`);
      console.log(`🔍 URL de détail TrendTrack: ${detailUrl}`);
      
      await this.contextManager.page.goto(detailUrl, {
        waitUntil: 'domcontentloaded',
        timeout: this.config.navigationTimeout
      });
      
      await this.contextManager.page.waitForTimeout(this.config.pageLoadPause);
      
      // Vérifier qu'on n'est pas sur une page de login
      const isLogin = await this.sessionManager.detectSessionExpired();
      if (isLogin) {
        throw new Error('Redirection vers la page de login détectée');
      }
      
      console.log('✅ Navigation vers page de détail réussie');
      return true;
    };
    
    return await this.retryHandler.executeWithRetry(
      navOperation,
      `navigation_${shopId}`,
      3
    );
  }

  /**
   * Extraction des détails d'une boutique
   */
  async extractShopDetails(shopId) {
    const extractOperation = async () => {
      try {
        console.log(`🔍 Extraction des détails de la boutique (ID: ${shopId})...`);
        
        // Attendre que la page soit chargée (sélecteur pour page de détail)
        await this.contextManager.page.waitForSelector('.flex.items-center.gap-2', { 
          timeout: this.config.selectorTimeout 
        });
        
        console.log('✅ Page de détail chargée');
        
        // Extraction des pixels via API TrendTrack
        console.log(`🔍 Extraction des pixels via API TrendTrack...`);
        console.log(`📊 Extraction pixels (API) pour: ${shopId}`);
        
        const pixelGoogle = await this.extractor.extractPixel('google');
        const pixelFacebook = await this.extractor.extractPixel('facebook');
        
        if (pixelGoogle) {
          console.log('✅ Pixel Google détecté via API');
        }
        if (pixelFacebook) {
          console.log('✅ Pixel Facebook détecté via API');
        }
        
        console.log(`✅ Pixels extraits pour ${shopId}: Google=${pixelGoogle ? 'oui' : 'non'}, Facebook=${pixelFacebook ? 'oui' : 'non'}`);
        
        // Extraction des données géographiques via DOM
        console.log('🌍 Extraction des données géographiques via DOM...');
        console.log('🌍 Extraction des données géographiques via scraping DOM...');
        
        const geoData = await this.extractor.extractGeoDataViaDOM();
        
        // Extraction des métriques live_ads_7d et live_ads_30d
        console.log('🔍 Extraction live_ads_7d (Phase 3 - .flex.items-center.gap-2)...');
        const liveAds7d = await this.extractor.extractLiveAds7d();
        console.log(`📊 Live ads 7d extrait (Phase 3): ${liveAds7d}`);
        
        console.log('🔍 Extraction live_ads_30d (Phase 3 - .flex.items-center.gap-2)...');
        const liveAds30d = await this.extractor.extractLiveAds30d();
        console.log(`📊 Live ads 30d extrait (Phase 3): ${liveAds30d}`);
        
        // Extraction AOV
        console.log('🔍 Extraction AOV (Phase 3)...');
        const aov = await this.extractor.extractAOV();
        console.log(`📊 AOV extrait (Phase 3): ${aov}`);
        
        console.log('✅ Détails de la boutique extraits');
        
        return {
          pixelGoogle: pixelGoogle ? 'oui' : 'non',
          pixelFacebook: pixelFacebook ? 'oui' : 'non',
          liveAds7d: liveAds7d || 0,
          liveAds30d: liveAds30d || 0,
          aov: aov || null,
          ...geoData,
          lastUpdated: new Date().toISOString()
        };
        
      } catch (error) {
        console.log(`❌ Erreur extraction détails ${shopId}: ${error.message}`);
        throw error;
      }
    };
    
    return await this.retryHandler.executeWithRetry(
      extractOperation,
      `extract_details_${shopId}`,
      3
    );
  }

  /**
   * Sauvegarde des détails d'une boutique
   */
  async saveShopDetails(shopId, details) {
    console.log(`💾 Sauvegarde des détails pour la boutique ${shopId}`);
    console.log(`📊 Détails à sauvegarder:`, details);
    
    try {
      // Préparer les données pour la sauvegarde
      const detailData = {
        // Métriques de marché
        market_us: details.market_us || 0,
        market_uk: details.market_uk || 0,
        market_de: details.market_de || 0,
        market_ca: details.market_ca || 0,
        market_au: details.market_au || 0,
        market_fr: details.market_fr || 0,
        
        // Pixels
        pixel_google: details.pixelGoogle || "non",
        pixel_facebook: details.pixelFacebook || "non",
        
        // Métriques live ads
        live_ads_7d: details.liveAds7d || 0,
        live_ads_30d: details.liveAds30d || 0,
        
        // AOV
        aov: details.aov || null,
        
        // Statut
        scraping_status: 'details_extracted',
        updated_at: new Date().toISOString()
      };
      
      // Utiliser ShopRepository pour sauvegarder
      if (this.shopRepository) {
        const success = await this.shopRepository.updateDetailMetrics(shopId, detailData);
        
        if (success) {
          console.log(`✅ Détails sauvegardés pour la boutique ${shopId}`);
          return true;
        } else {
          console.log(`❌ Échec sauvegarde pour la boutique ${shopId}`);
          return false;
        }
      } else {
        console.log(`❌ ShopRepository non disponible pour la boutique ${shopId}`);
        return false;
      }
      
    } catch (error) {
      console.error(`❌ Erreur sauvegarde détails boutique ${shopId}:`, error.message);
      return false;
    }
  }

  /**
   * Ferme proprement le scraper MVP
   */
  async close() {
    try {
      console.log('🔄 Fermeture du scraper MVP...');
      
      if (this.contextManager) {
        await this.contextManager.close();
      }
      
      if (this.browser) {
        await this.browser.close();
      }
      
      this.isInitialized = false;
      console.log('✅ Scraper MVP fermé proprement');
      
    } catch (error) {
      console.error('❌ Erreur fermeture scraper MVP:', error.message);
    }
  }

  /**
   * Obtient l'état du scraper MVP
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      contextStatus: this.contextManager ? this.contextManager.getStatus() : null,
      sessionStatus: this.sessionManager ? this.sessionManager.getStatus() : null,
      errorStats: this.retryHandler ? this.retryHandler.getErrorStats() : null,
      config: this.config
    };
  }
}
