/**
 * Scraper TrendTrack avec sauvegarde incrémentale par lots
 * Version améliorée avec BatchSaver pour une sauvegarde au fur et à mesure
 */

import { WebScraper } from './scraper.js';
import { TrendTrackExtractor } from './extractors/trendtrack-extractor.js';
import { BatchSaver } from './utils/batch-saver.js';

export class TrendTrackScraperIncremental {
  constructor(batchSize = 5, flushInterval = 30000) {
    this.webScraper = new WebScraper();
    this.extractor = null;
    
    // Initialiser le BatchSaver
    this.batchSaver = new BatchSaver(batchSize, flushInterval);
    
    console.log('TrendTrackScraperIncremental initialisé avec BatchSaver');
  }

  async init() {
    console.log('Initialisation du scraper incrémental...');
    
    try {
      await this.webScraper.init();
      this.extractor = new TrendTrackExtractor(this.webScraper.page, this.webScraper.errorHandler);
      
      console.log('Scraper incrémental initialisé');
      return true;
    } catch (error) {
      console.error('Erreur initialisation:', error.message);
      return false;
    }
  }

  async login(email, password) {
    console.log('Connexion à TrendTrack...');
    
    try {
      const loginSuccess = await this.extractor.login(email, password);
      
      if (loginSuccess) {
        console.log('Connexion réussie');
        return true;
      } else {
        console.error('Échec de la connexion');
        return false;
      }
    } catch (error) {
      console.error('Erreur connexion:', error.message);
      return false;
    }
  }

  async navigateToTrendingShops() {
    console.log('Navigation vers les boutiques tendances...');
    
    try {
      const navigationSuccess = await this.extractor.navigateToTrendingShops();
      
      if (navigationSuccess) {
        console.log('Navigation réussie');
        return true;
      } else {
        console.error('Échec de la navigation');
        return false;
      }
    } catch (error) {
      console.error('Erreur navigation:', error.message);
      return false;
    }
  }

  async sortByLiveAds() {
    console.log('Tri par Live Ads...');
    
    try {
      const sortSuccess = await this.extractor.sortByLiveAds();
      
      if (sortSuccess) {
        console.log('Tri par Live Ads appliqué');
        return true;
      } else {
        console.log('Tri par Live Ads non appliqué, continuation...');
        return false;
      }
    } catch (error) {
      console.error('Erreur tri Live Ads:', error.message);
      return false;
    }
  }

  /**
   * Scrape avec sauvegarde incrémentale par lots
   */
  async scrapeMultiplePagesWithIncrementalSave(maxPages = 3, includeMarketData = false) {
    console.log('Scraping de ' + maxPages + ' pages avec sauvegarde incrémentale...');
    
    let totalSaved = 0;
    
    for (let page = 1; page <= maxPages; page++) {
      console.log('Scraping page ' + page + '...');
      
      // Extraire les données de la page actuelle
      const pageData = await this.extractor.extractAllShopsData(includeMarketData);
      
      // Sauvegarde incrémentale par batch
      for (const shop of pageData) {
        const shopDataWithPage = {
          ...shop,
          page: page,
          scrapedAt: new Date().toISOString(),
          projectSource: 'trendtrack_incremental'
        };
        
        await this.batchSaver.add(shopDataWithPage);
        totalSaved++;
      }
      
      console.log('Page ' + page + ': ' + pageData.length + ' boutiques extraites et en cours de sauvegarde');
      
      // Vérifier s'il y a une page suivante
      if (page < maxPages) {
        const paginationInfo = await this.extractor.getPaginationInfo();
        
        if (paginationInfo.hasNextPage && page < paginationInfo.totalPages) {
          const success = await this.extractor.goToNextPage();
            console.log('Impossible d aller à la page suivante, arrêt du scraping');
            break;
          }
          
          // Attendre entre les pages
          await new Promise(resolve => setTimeout(resolve, includeMarketData ? 5000 : 2000));
        } else {
          console.log('Plus de pages disponibles');
          break;
        }
      }
    }
    
    // Flush final pour s'assurer que tout est sauvegardé
    await this.batchSaver.flush();
    
    console.log('Scraping terminé: ' + totalSaved + ' boutiques sauvegardées');
    console.log('Stats BatchSaver:', JSON.stringify(this.batchSaver.getStats()));
    
    return totalSaved;
  }

  /**
   * Ferme le scraper et flush les données restantes
   */
  async close() {
    console.log('Fermeture du scraper incrémental...');
    
    // Flush final avant fermeture
    await this.batchSaver.close();
    
    await this.webScraper.close();
    console.log('Scraper incrémental fermé');
  }

  /**
   * Retourne les statistiques du BatchSaver
   */
  getBatchStats() {
    return this.batchSaver.getStats();
  }
}
