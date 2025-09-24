/**
 * MVP Session Manager - SOLUTION 3: Gestion des Sessions Expirées
 * 
 * Responsabilité: Détection et récupération automatique des sessions expirées
 * Problème résolu: Redirection vers page de login, perte de session
 */

export class MVPSessionManager {
  constructor(contextManager, config) {
    this.contextManager = contextManager;
    this.config = config;
    this.isSessionValid = false;
    this.lastSessionCheck = 0;
    this.sessionCheckInterval = 30000; // 30 secondes
  }

  /**
   * Obtient la page actuelle du contexte
   */
  get page() {
    return this.contextManager.page;
  }

  /**
   * Détecte si la session a expiré
   */
  async detectSessionExpired() {
    try {
      const currentUrl = this.page.url();
      
      // Vérifier l'URL
      if (currentUrl.includes('/login') || currentUrl.includes('/signin')) {
        console.log('🔍 Session expirée détectée via URL:', currentUrl);
        return true;
      }
      
      // Vérifier la présence d'un champ password
      const passwordField = await this.page.$('input[type="password"]');
      if (passwordField) {
        console.log('🔍 Session expirée détectée via champ password');
        return true;
      }
      
      // Vérifier le titre de la page
      const title = await this.page.title();
      if (title.toLowerCase().includes('login') || title.toLowerCase().includes('sign in')) {
        console.log('🔍 Session expirée détectée via titre:', title);
        return true;
      }
      
      // Vérifier la présence d'éléments de login
      const loginElements = await this.page.$$('button[type="submit"], input[type="email"], .login-form');
      if (loginElements.length > 0) {
        console.log('🔍 Session expirée détectée via éléments de login');
        return true;
      }
      
      return false;
      
    } catch (error) {
      console.log('⚠️ Erreur détection session:', error.message);
      return true; // En cas d'erreur, considérer comme expiré par sécurité
    }
  }

  /**
   * Effectue la connexion à TrendTrack via l'extracteur
   * NOTE: La logique de connexion est déléguée à TrendTrackExtractor
   */
  async login(extractor) {
    try {
      console.log('🔑 Connexion à TrendTrack via extracteur...');
      
      const success = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
      
      if (success) {
        this.isSessionValid = true;
        this.lastSessionCheck = Date.now();
        console.log('✅ Connexion réussie via extracteur');
        return true;
      } else {
        this.isSessionValid = false;
        console.log('❌ Connexion échouée via extracteur');
        return false;
      }
      
    } catch (error) {
      console.error('❌ Erreur de connexion via extracteur:', error.message);
      this.isSessionValid = false;
      return false;
    }
  }

  /**
   * Gère la session expirée en se reconnectant via l'extracteur
   */
  async handleSessionExpired(extractor) {
    console.log('🔄 Session expirée détectée, reconnexion via extracteur...');
    
    try {
      // Se reconnecter via l'extracteur
      const loginSuccess = await this.login(extractor);
      
      if (loginSuccess) {
        console.log('✅ Session restaurée avec succès via extracteur');
        return true;
      } else {
        console.log('❌ Échec de la restauration de session via extracteur');
        return false;
      }
      
    } catch (error) {
      console.error('❌ Erreur lors de la gestion de session expirée:', error.message);
      this.isSessionValid = false;
      return false;
    }
  }

  /**
   * Vérifie périodiquement la validité de la session
   */
  async checkSessionValidity() {
    const now = Date.now();
    
    // Vérifier seulement si assez de temps s'est écoulé
    if (now - this.lastSessionCheck < this.sessionCheckInterval) {
      return this.isSessionValid;
    }
    
    try {
      // Test simple : naviguer vers le dashboard
      const currentUrl = this.page.url();
      if (!currentUrl.includes('trendtrack.io')) {
        return false;
      }
      
      // Si on est déjà sur une page valide, vérifier qu'on n'est pas sur login
      if (await this.detectSessionExpired()) {
        this.isSessionValid = false;
        return false;
      }
      
      this.isSessionValid = true;
      this.lastSessionCheck = now;
      return true;
      
    } catch (error) {
      console.log('⚠️ Erreur vérification session:', error.message);
      this.isSessionValid = false;
      return false;
    }
  }

  /**
   * S'assure que la session est valide
   */
  async ensureSessionValid(extractor) {
    if (!this.isSessionValid || !await this.checkSessionValidity()) {
      console.log('🔄 Session non valide, reconnexion...');
      return await this.handleSessionExpired(extractor);
    }
    return true;
  }

  /**
   * Exécute une opération avec récupération automatique de session
   */
  async executeWithSessionRecovery(operation, extractor, maxRetries = 3) {
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Vérifier la validité de la session avant l'opération
        if (!await this.ensureSessionValid(extractor)) {
          throw new Error('Impossible de maintenir une session valide');
        }
        
        // Exécuter l'opération
        return await operation();
        
      } catch (error) {
        lastError = error;
        console.log(`❌ Tentative ${attempt}/${maxRetries} échouée: ${error.message}`);
        
        // Vérifier si c'est une erreur de session
        if (await this.detectSessionExpired()) {
          console.log('🔄 Erreur de session détectée, reconnexion...');
          
          if (await this.handleSessionExpired(extractor)) {
            console.log('✅ Session restaurée, retry immédiat');
            continue; // Retry immédiat après reconnexion
          } else {
            console.log('❌ Échec restauration session');
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
   * Marque la session comme invalide (par exemple après une erreur)
   */
  markSessionInvalid() {
    console.log('⚠️ Session marquée comme invalide');
    this.isSessionValid = false;
    this.lastSessionCheck = 0;
  }

  /**
   * Obtient l'état de la session
   */
  getStatus() {
    return {
      isValid: this.isSessionValid,
      lastCheck: this.lastSessionCheck,
      checkInterval: this.sessionCheckInterval,
      config: this.config
    };
  }
}
