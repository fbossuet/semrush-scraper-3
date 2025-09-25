/**
 * MVP Retry Handler - Retry intelligent avec récupération automatique
 * 
 * Responsabilité: Gestion des retry avec récupération des erreurs critiques
 * Intègre les solutions MVP 1, 3 et 4 (Browser Restart)
 */

import { MVPBrowserManager } from './mvp-browser-manager.js';

export class MVPRetryHandler {
  constructor(contextManager, sessionManager, extractor, config) {
    this.contextManager = contextManager;
    this.sessionManager = sessionManager;
    this.extractor = extractor;
    this.config = config;
    this.browserManager = new MVPBrowserManager(config);
    this.errorCounts = new Map();
    this.lastErrorTime = new Map();
  }

  /**
   * Exécute une opération avec retry intelligent et récupération automatique
   */
  async executeWithRetry(operation, context = 'default', maxRetries = null) {
    const retries = maxRetries || this.config.maxRetries;
    let lastError = null;
    
    console.log(`🔄 Exécution avec retry (max ${retries} tentatives) pour contexte: ${context}`);
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        // Exécuter l'opération avec récupération automatique
        return await this.executeWithRecovery(operation, context);
        
      } catch (error) {
        lastError = error;
        console.log(`❌ Tentative ${attempt}/${retries} échouée pour ${context}: ${error.message}`);
        
        // Enregistrer l'erreur
        this.recordError(context, error);
        
        // Déterminer si on doit retry
        if (!this.shouldRetry(error, attempt, retries)) {
          console.log(`🛑 Arrêt des retry pour ${context}: ${error.message}`);
          break;
        }
        
        // Attendre avant le prochain essai
        if (attempt < retries) {
          const delay = this.calculateRetryDelay(attempt);
          console.log(`⏸️ Attente ${delay}ms avant retry ${attempt + 1}/${retries}...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    console.log(`💥 Toutes les tentatives échouées pour ${context}`);
    throw lastError || new Error(`Toutes les tentatives ont échoué pour ${context}`);
  }

  /**
   * Exécute une opération avec récupération automatique des erreurs critiques
   */
  async executeWithRecovery(operation, context = 'default') {
    try {
      return await operation();
      
    } catch (error) {
      console.log(`🔍 Analyse de l'erreur pour ${context}: ${error.message}`);
      
      // SOLUTION 4: Gestion de la fermeture du navigateur (PRIORITÉ)
      if (this.browserManager.detectBrowserClosed(error)) {
        console.log('🔄 Fermeture du navigateur détectée, redémarrage...');
        
        try {
          const result = await this.browserManager.executeWithBrowserRestart(
            operation, 
            this.extractor, 
            context
          );
          console.log('✅ Navigateur redémarré, opération réussie');
          return result;
        } catch (restartError) {
          console.log(`❌ Échec du redémarrage du navigateur: ${restartError.message}`);
          throw restartError;
        }
      }
      
      // SOLUTION 1: Gestion des contextes fermés
      if (this.contextManager.detectContextClosed(error)) {
        console.log('🔄 Erreur de contexte fermé détectée, récupération...');
        
        if (await this.contextManager.recreateContext()) {
          console.log('✅ Contexte recréé, retry immédiat');
          // Retry immédiat après recréation du contexte
          return await operation();
        } else {
          throw new Error('Impossible de recréer le contexte');
        }
      }
      
      // SOLUTION 3: Gestion des sessions expirées
      if (await this.sessionManager.detectSessionExpired()) {
        console.log('🔄 Erreur de session expirée détectée, récupération...');
        
        if (await this.sessionManager.handleSessionExpired(this.extractor)) {
          console.log('✅ Session restaurée, retry immédiat');
          // Retry immédiat après restauration de session
          return await operation();
        } else {
          throw new Error('Impossible de restaurer la session');
        }
      }
      
      // Autres erreurs : propagation
      throw error;
    }
  }

  /**
   * Détermine si une erreur doit être retry
   */
  shouldRetry(error, attempt, maxRetries) {
    // Ne pas retry si c'est la dernière tentative
    if (attempt >= maxRetries) {
      return false;
    }
    
    // Ne pas retry pour certaines erreurs fatales
    const nonRetryableErrors = [
      'Authentication failed',
      'Invalid credentials',
      'Access denied',
      'Forbidden',
      'Unauthorized',
      'Not found',
      '404'
    ];
    
    const errorMessage = error.message.toLowerCase();
    if (nonRetryableErrors.some(msg => errorMessage.includes(msg.toLowerCase()))) {
      console.log(`🛑 Erreur non retryable: ${error.message}`);
      return false;
    }
    
    // Retry pour les erreurs temporaires
    const retryableErrors = [
      'Timeout',
      'Network error',
      'Connection refused',
      'Connection reset',
      'ECONNRESET',
      'ENOTFOUND',
      'Target page, context or browser has been closed',
      'Navigation timeout',
      'Selector timeout',
      'Element not found',
      'Page crashed'
    ];
    
    const shouldRetry = retryableErrors.some(msg => errorMessage.includes(msg.toLowerCase()));
    if (shouldRetry) {
      console.log(`🔄 Erreur retryable: ${error.message}`);
    }
    
    return shouldRetry;
  }

  /**
   * Calcule le délai de retry avec backoff exponentiel
   */
  calculateRetryDelay(attempt) {
    const baseDelay = this.config.retryDelay;
    
    if (this.config.retryBackoff === 'exponential') {
      // Backoff exponentiel : 1s, 2s, 4s, 8s...
      return Math.min(baseDelay * Math.pow(2, attempt - 1), 10000);
    } else if (this.config.retryBackoff === 'linear') {
      // Backoff linéaire : 1s, 2s, 3s, 4s...
      return baseDelay * attempt;
    } else {
      // Délai fixe
      return baseDelay;
    }
  }

  /**
   * Enregistre une erreur pour le monitoring
   */
  recordError(context, error) {
    const key = `${context}:${error.constructor.name}`;
    const count = this.errorCounts.get(key) || 0;
    this.errorCounts.set(key, count + 1);
    this.lastErrorTime.set(key, Date.now());
    
    console.log(`📊 Erreur enregistrée: ${key} (${count + 1} occurrences)`);
  }

  /**
   * Gère les erreurs de contexte fermé
   */
  async handleContextClosed() {
    console.log('🔄 Gestion spécifique: Contexte fermé');
    
    try {
      const success = await this.contextManager.recreateContext();
      if (success) {
        console.log('✅ Contexte fermé géré avec succès');
        return true;
      } else {
        console.log('❌ Échec de la gestion du contexte fermé');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur lors de la gestion du contexte fermé:', error.message);
      return false;
    }
  }

  /**
   * Gère les erreurs de session expirée
   */
  async handleSessionExpired() {
    console.log('🔄 Gestion spécifique: Session expirée');
    
    try {
      const success = await this.sessionManager.handleSessionExpired(this.extractor);
      if (success) {
        console.log('✅ Session expirée gérée avec succès');
        return true;
      } else {
        console.log('❌ Échec de la gestion de la session expirée');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur lors de la gestion de la session expirée:', error.message);
      return false;
    }
  }

  /**
   * Obtient les statistiques d'erreurs
   */
  getErrorStats() {
    return {
      errorCounts: Object.fromEntries(this.errorCounts),
      lastErrorTimes: Object.fromEntries(this.lastErrorTime),
      config: this.config
    };
  }

  /**
   * Réinitialise les statistiques d'erreurs
   */
  resetStats() {
    this.errorCounts.clear();
    this.lastErrorTime.clear();
    console.log('📊 Statistiques d\'erreurs réinitialisées');
  }
}
