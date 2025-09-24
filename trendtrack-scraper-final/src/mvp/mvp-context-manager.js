/**
 * MVP Context Manager - SOLUTION 1: Gestion des Contextes Fermés
 * 
 * Responsabilité: Détection et récupération automatique des contextes fermés
 * Problème résolu: "Target page, context or browser has been closed"
 */

export class MVPContextManager {
  constructor(browser, config) {
    this.browser = browser;
    this.config = config;
    this.context = null;
    this.page = null;
    this.isContextHealthy = true;
  }

  /**
   * Crée un nouveau contexte avec configuration optimale
   */
  async createContext() {
    try {
      console.log('🔄 Création d\'un nouveau contexte...');
      
      this.context = await this.browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1920, height: 1080 },
        locale: 'en-US',
        timezoneId: 'America/New_York',
        extraHTTPHeaders: {
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate, br',
          'DNT': '1',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1'
        }
      });

      this.page = await this.context.newPage();
      this.isContextHealthy = true;
      
      console.log('✅ Contexte créé avec succès');
      return { context: this.context, page: this.page };
      
    } catch (error) {
      console.error('❌ Erreur création contexte:', error.message);
      throw error;
    }
  }

  /**
   * Détecte si l'erreur est due à un contexte fermé
   */
  detectContextClosed(error) {
    const contextClosedMessages = [
      'Target page, context or browser has been closed',
      'context has been closed',
      'browser has been closed',
      'page has been closed',
      'Protocol error (Target.setDiscoverTargets): Target closed'
    ];
    
    return contextClosedMessages.some(msg => 
      error.message.toLowerCase().includes(msg.toLowerCase())
    );
  }

  /**
   * Recrée un nouveau contexte en cas de fermeture
   */
  async recreateContext() {
    console.log('🔄 Contexte fermé détecté, recréation...');
    
    try {
      // Fermer l'ancien contexte s'il existe
      if (this.context) {
        try {
          await this.context.close();
        } catch (closeError) {
          console.log('⚠️ Erreur fermeture ancien contexte (normal):', closeError.message);
        }
      }
      
      // Créer un nouveau contexte
      await this.createContext();
      this.isContextHealthy = true;
      
      console.log('✅ Contexte recréé avec succès');
      return true;
      
    } catch (error) {
      console.error('❌ Erreur recréation contexte:', error.message);
      this.isContextHealthy = false;
      return false;
    }
  }

  /**
   * Vérifie la santé du contexte
   */
  async checkContextHealth() {
    if (!this.context || !this.page) {
      return false;
    }
    
    try {
      // Test simple pour vérifier que le contexte fonctionne
      await this.page.evaluate(() => document.title, { timeout: 5000 });
      this.isContextHealthy = true;
      return true;
    } catch (error) {
      console.log('⚠️ Contexte non sain détecté:', error.message);
      this.isContextHealthy = false;
      return false;
    }
  }

  /**
   * S'assure que le contexte est vivant et fonctionnel
   */
  async ensureContextAlive() {
    if (!this.isContextHealthy || !await this.checkContextHealth()) {
      console.log('🔄 Contexte non sain, recréation...');
      return await this.recreateContext();
    }
    return true;
  }

  /**
   * Exécute une opération avec récupération automatique du contexte
   */
  async executeWithContextRecovery(operation, maxRetries = 3) {
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Vérifier la santé du contexte avant l'opération
        if (!await this.ensureContextAlive()) {
          throw new Error('Impossible de maintenir un contexte sain');
        }
        
        // Exécuter l'opération
        return await operation();
        
      } catch (error) {
        lastError = error;
        console.log(`❌ Tentative ${attempt}/${maxRetries} échouée: ${error.message}`);
        
        // Vérifier si c'est une erreur de contexte fermé
        if (this.detectContextClosed(error)) {
          console.log('🔄 Erreur de contexte fermé détectée, recréation...');
          
          if (await this.recreateContext()) {
            console.log('✅ Contexte recréé, retry immédiat');
            continue; // Retry immédiat après recréation
          } else {
            console.log('❌ Échec recréation contexte');
            break;
          }
        }
        
        // Pour les autres erreurs, attendre avant retry
        if (attempt < maxRetries) {
          const delay = this.config.retryDelay * attempt;
          console.log(`⏸️ Attente ${delay}ms avant retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError || new Error('Toutes les tentatives ont échoué');
  }

  /**
   * Ferme proprement le contexte
   */
  async close() {
    try {
      if (this.context) {
        await this.context.close();
        console.log('✅ Contexte fermé proprement');
      }
    } catch (error) {
      console.log('⚠️ Erreur fermeture contexte:', error.message);
    } finally {
      this.context = null;
      this.page = null;
      this.isContextHealthy = false;
    }
  }

  /**
   * Obtient l'état du contexte
   */
  getStatus() {
    return {
      hasContext: !!this.context,
      hasPage: !!this.page,
      isHealthy: this.isContextHealthy,
      config: this.config
    };
  }
}

