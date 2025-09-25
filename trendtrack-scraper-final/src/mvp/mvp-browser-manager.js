/**
 * MVP Browser Manager - Solution 4
 * 
 * Gère la fermeture complète du navigateur Playwright et son redémarrage automatique.
 * Détecte les erreurs de type "Target page, context or browser has been closed"
 * et redémarre automatiquement le navigateur avec reconnexion.
 */

import { chromium } from 'playwright';

export class MVPBrowserManager {
  constructor(config) {
    this.config = config;
    this.browser = null;
    this.context = null;
    this.page = null;
    this.isRestarting = false;
    this.restartCount = 0;
    this.maxRestarts = 3; // Limite de redémarrages par session
  }

  /**
   * Détecte si l'erreur indique une fermeture du navigateur
   */
  detectBrowserClosed(error) {
    const browserClosedMessages = [
      'Target page, context or browser has been closed',
      'browser.newContext: Target page, context or browser has been closed',
      'Browser has been closed',
      'browser.close: Target page, context or browser has been closed',
      'browser.newPage: Target page, context or browser has been closed'
    ];
    
    const isBrowserClosed = browserClosedMessages.some(msg => 
      error.message && error.message.includes(msg)
    );
    
    if (isBrowserClosed) {
      console.log(`🔍 Fermeture du navigateur détectée: ${error.message}`);
    }
    
    return isBrowserClosed;
  }

  /**
   * Redémarre complètement le navigateur Playwright
   */
  async restartBrowser() {
    if (this.isRestarting) {
      console.log('⚠️ Redémarrage déjà en cours, attente...');
      return false;
    }

    if (this.restartCount >= this.maxRestarts) {
      console.log(`❌ Limite de redémarrages atteinte (${this.maxRestarts}), abandon`);
      return false;
    }

    this.isRestarting = true;
    this.restartCount++;

    try {
      console.log(`🔄 Redémarrage du navigateur (tentative ${this.restartCount}/${this.maxRestarts})...`);
      
      // Fermer le navigateur existant si possible
      if (this.browser) {
        try {
          await this.browser.close();
          console.log('✅ Navigateur existant fermé');
        } catch (error) {
          console.log('⚠️ Erreur lors de la fermeture du navigateur existant:', error.message);
        }
      }

      // Redémarrer le navigateur
      console.log('🚀 Lancement du nouveau navigateur...');
      this.browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      });

      console.log('✅ Navigateur redémarré avec succès');
      
      // Recréer le contexte
      await this.recreateContext();
      
      return true;

    } catch (error) {
      console.log(`❌ Erreur lors du redémarrage du navigateur: ${error.message}`);
      return false;
    } finally {
      this.isRestarting = false;
    }
  }

  /**
   * Recrée le contexte et la page après redémarrage
   */
  async recreateContext() {
    try {
      console.log('🔄 Recréation du contexte...');
      
      // Créer un nouveau contexte
      this.context = await this.browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1920, height: 1080 },
        locale: 'fr-FR',
        timezoneId: 'Europe/Paris'
      });

      // Créer une nouvelle page
      this.page = await this.context.newPage();
      
      // Configuration de la page
      await this.page.setDefaultTimeout(this.config.navigationTimeout);
      await this.page.setDefaultNavigationTimeout(this.config.navigationTimeout);
      
      console.log('✅ Contexte et page recréés avec succès');
      return true;

    } catch (error) {
      console.log(`❌ Erreur lors de la recréation du contexte: ${error.message}`);
      return false;
    }
  }

  /**
   * Relogge automatiquement après redémarrage
   */
  async relogin(extractor) {
    try {
      console.log('🔑 Reconnexion automatique après redémarrage...');
      
      if (!extractor || !this.page) {
        console.log('❌ Extracteur ou page non disponible pour la reconnexion');
        return false;
      }

      // Utiliser l'extracteur pour se reconnecter
      const loginSuccess = await extractor.login(this.page);
      
      if (loginSuccess) {
        console.log('✅ Reconnexion réussie');
        return true;
      } else {
        console.log('❌ Échec de la reconnexion');
        return false;
      }

    } catch (error) {
      console.log(`❌ Erreur lors de la reconnexion: ${error.message}`);
      return false;
    }
  }

  /**
   * Exécute une opération avec redémarrage automatique en cas de fermeture
   */
  async executeWithBrowserRestart(operation, extractor, contextKey = 'browser_restart') {
    let lastError = null;
    
    for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
      try {
        console.log(`🔄 Tentative ${attempt}/${this.config.maxRetries} pour ${contextKey}`);
        
        // Vérifier si le navigateur est disponible
        if (!this.browser || !this.page) {
          console.log('⚠️ Navigateur non disponible, redémarrage...');
          const restartSuccess = await this.restartBrowser();
          if (!restartSuccess) {
            throw new Error('Impossible de redémarrer le navigateur');
          }
          
          // Relogger après redémarrage
          const loginSuccess = await this.relogin(extractor);
          if (!loginSuccess) {
            throw new Error('Impossible de se reconnecter après redémarrage');
          }
        }

        // Exécuter l'opération
        const result = await operation(this.page);
        console.log(`✅ Opération réussie pour ${contextKey}`);
        return result;

      } catch (error) {
        lastError = error;
        console.log(`❌ Tentative ${attempt}/${this.config.maxRetries} échouée pour ${contextKey}: ${error.message}`);
        
        // Vérifier si c'est une fermeture de navigateur
        if (this.detectBrowserClosed(error)) {
          console.log('🔄 Fermeture du navigateur détectée, redémarrage...');
          
          const restartSuccess = await this.restartBrowser();
          if (!restartSuccess) {
            console.log('❌ Impossible de redémarrer le navigateur');
            break;
          }
          
          // Relogger après redémarrage
          const loginSuccess = await this.relogin(extractor);
          if (!loginSuccess) {
            console.log('❌ Impossible de se reconnecter après redémarrage');
            break;
          }
          
          // Pause avant retry
          const delay = this.config.retryDelay * Math.pow(2, attempt - 1);
          console.log(`⏸️ Pause de ${delay}ms avant retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          
        } else {
          // Erreur non liée au navigateur, pause normale
          const delay = this.config.retryDelay * Math.pow(2, attempt - 1);
          console.log(`⏸️ Pause de ${delay}ms avant retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    console.log(`💥 Toutes les tentatives échouées pour ${contextKey}`);
    throw lastError;
  }

  /**
   * Obtient la page actuelle
   */
  getPage() {
    return this.page;
  }

  /**
   * Obtient le contexte actuel
   */
  getContext() {
    return this.context;
  }

  /**
   * Obtient le navigateur actuel
   */
  getBrowser() {
    return this.browser;
  }

  /**
   * Ferme proprement le navigateur
   */
  async close() {
    try {
      if (this.browser) {
        await this.browser.close();
        console.log('✅ Navigateur fermé proprement');
      }
    } catch (error) {
      console.log(`⚠️ Erreur lors de la fermeture du navigateur: ${error.message}`);
    }
  }

  /**
   * Réinitialise le compteur de redémarrages
   */
  resetRestartCount() {
    this.restartCount = 0;
    console.log('🔄 Compteur de redémarrages réinitialisé');
  }
}
