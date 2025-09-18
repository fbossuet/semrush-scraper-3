/**
 * Gestionnaire d'erreurs intelligent pour le scraper
 * Gère les erreurs de navigation, de scraping et de validation
 */

import fs from 'fs/promises';
import path from 'path';
import { errorConfig } from '../config.js';

export class ErrorHandler {
  constructor() {
    this.errorLog = [];
    this.retryCount = 0;
    this.maxRetries = errorConfig.retryAttempts;
    this.retryDelay = errorConfig.retryDelay;
  }

  /**
   * Gère une extraction avec gestion d'erreurs et retry
   * @param {Function} extractionFunction - Fonction d'extraction à exécuter
   * @param {string} context - Contexte de l'extraction
   * @param {string} url - URL en cours de traitement
   * @param {number} timeout - Timeout en millisecondes
   * @returns {Promise<Object>} - Résultat de l'extraction
   */
  async handleExtraction(extractionFunction, context, url, timeout = 30000) {
    this.retryCount = 0;
    
    while (this.retryCount <= this.maxRetries) {
      try {
        console.log(`🔄 Tentative ${this.retryCount + 1}/${this.maxRetries + 1} pour ${context}`);
        
        const result = await Promise.race([
          extractionFunction(),
          this.createTimeout(timeout)
        ]);
        
        if (result) {
          console.log(`✅ Extraction réussie: ${context}`);
          return result;
        } else {
          throw new Error('Extraction retournée null/undefined');
        }
        
      } catch (error) {
        this.retryCount++;
        const errorInfo = this.formatError(error, context, url);
        
        console.log(`❌ Erreur ${context} (tentative ${this.retryCount}/${this.maxRetries + 1}): ${error.message}`);
        
        // Log de l'erreur
        this.logError(errorInfo);
        
        if (this.retryCount > this.maxRetries) {
          console.log(`💥 Échec définitif après ${this.maxRetries + 1} tentatives: ${context}`);
          return this.createErrorResult(errorInfo);
        }
        
        // Attendre avant de retenter
        if (this.retryDelay > 0) {
          console.log(`⏳ Attente ${this.retryDelay}ms avant retry...`);
          await this.sleep(this.retryDelay);
        }
      }
    }
  }

  /**
   * Crée un timeout pour éviter les blocages
   * @param {number} timeout - Timeout en millisecondes
   * @returns {Promise} - Promise qui rejette après le timeout
   */
  createTimeout(timeout) {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Timeout après ${timeout}ms`));
      }, timeout);
    });
  }

  /**
   * Formate une erreur pour le logging
   * @param {Error} error - Erreur à formater
   * @param {string} context - Contexte de l'erreur
   * @param {string} url - URL concernée
   * @returns {Object} - Erreur formatée
   */
  formatError(error, context, url) {
    return {
      timestamp: new Date().toISOString(),
      context,
      url,
      message: error.message,
      stack: error.stack,
      retryCount: this.retryCount,
      type: this.categorizeError(error)
    };
  }

  /**
   * Catégorise une erreur selon son type
   * @param {Error} error - Erreur à catégoriser
   * @returns {string} - Type d'erreur
   */
  categorizeError(error) {
    const message = error.message.toLowerCase();
    
    if (message.includes('timeout') || message.includes('navigation')) {
      return 'timeout';
    } else if (message.includes('selector') || message.includes('element')) {
      return 'selector';
    } else if (message.includes('network') || message.includes('connection')) {
      return 'network';
    } else if (message.includes('blocked') || message.includes('forbidden')) {
      return 'blocked';
    } else {
      return 'unknown';
    }
  }

  /**
   * Log une erreur
   * @param {Object} errorInfo - Informations sur l'erreur
   */
  async logError(errorInfo) {
    this.errorLog.push(errorInfo);
    
    if (errorConfig.logErrors) {
      try {
        await fs.mkdir('logs', { recursive: true });
        const logFile = `logs/errors-${new Date().toISOString().split('T')[0]}.json`;
        
        let existingLogs = [];
        try {
          const existingContent = await fs.readFile(logFile, 'utf8');
          existingLogs = JSON.parse(existingContent);
        } catch (error) {
          // Fichier n'existe pas ou vide
        }
        
        existingLogs.push(errorInfo);
        await fs.writeFile(logFile, JSON.stringify(existingLogs, null, 2));
        
      } catch (error) {
        console.log(`⚠️ Erreur lors du logging: ${error.message}`);
      }
    }
  }

  /**
   * Crée un résultat d'erreur standardisé
   * @param {Object} errorInfo - Informations sur l'erreur
   * @returns {Object} - Résultat d'erreur
   */
  createErrorResult(errorInfo) {
    return {
      success: false,
      error: errorInfo,
      data: null,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Gère les erreurs de navigation
   * @param {Error} error - Erreur de navigation
   * @param {string} url - URL concernée
   * @returns {Object} - Résultat d'erreur
   */
  handleNavigationError(error, url) {
    const errorInfo = this.formatError(error, 'navigation', url);
    console.log(`🧭 Erreur navigation: ${url} - ${error.message}`);
    this.logError(errorInfo);
    return this.createErrorResult(errorInfo);
  }

  /**
   * Gère les erreurs de scraping
   * @param {Error} error - Erreur de scraping
   * @param {string} selector - Sélecteur concerné
   * @param {string} url - URL concernée
   * @returns {Object} - Résultat d'erreur
   */
  handleScrapingError(error, selector, url) {
    const errorInfo = this.formatError(error, 'scraping', url);
    errorInfo.selector = selector;
    console.log(`🔍 Erreur scraping: ${selector} sur ${url} - ${error.message}`);
    this.logError(errorInfo);
    return this.createErrorResult(errorInfo);
  }

  /**
   * Gère les erreurs de validation
   * @param {Object} validationResult - Résultat de validation
   * @param {string} context - Contexte de validation
   * @returns {Object} - Résultat d'erreur
   */
  handleValidationError(validationResult, context) {
    const errorInfo = {
      timestamp: new Date().toISOString(),
      context: 'validation',
      message: `Validation échouée pour ${context}`,
      errors: validationResult.errors,
      warnings: validationResult.warnings
    };
    
    console.log(`⚠️ Erreur validation: ${context} - ${validationResult.errors.join(', ')}`);
    this.logError(errorInfo);
    return this.createErrorResult(errorInfo);
  }

  /**
   * Sauvegarde une capture d'écran d'erreur
   * @param {Object} page - Page Playwright
   * @param {string} context - Contexte de l'erreur
   * @param {string} url - URL concernée
   */
  async saveErrorScreenshot(page, context, url) {
    if (errorConfig.saveErrorScreenshots && page) {
      try {
        await fs.mkdir('screenshots/errors', { recursive: true });
        const timestamp = new Date().toISOString();
        const filename = `error-${context}-${timestamp}.png`;
        const filepath = `screenshots/errors/${filename}`;
        
        await page.screenshot({ path: filepath });
        console.log(`📸 Screenshot d'erreur sauvegardé: ${filepath}`);
        
      } catch (error) {
        console.log(`⚠️ Erreur sauvegarde screenshot: ${error.message}`);
      }
    }
  }

  /**
   * Pause pour éviter la surcharge
   * @param {number} ms - Millisecondes à attendre
   * @returns {Promise} - Promise qui se résout après la pause
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Affiche les statistiques d'erreurs
   */
  printErrorStats() {
    const stats = {
      total: this.errorLog.length,
      byType: {},
      byContext: {}
    };
    
    for (const error of this.errorLog) {
      // Compter par type
      stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
      
      // Compter par contexte
      stats.byContext[error.context] = (stats.byContext[error.context] || 0) + 1;
    }
    
    console.log('📊 Statistiques Erreurs:');
    console.log(`   Total: ${stats.total}`);
    console.log('   Par type:', stats.byType);
    console.log('   Par contexte:', stats.byContext);
  }

  /**
   * Nettoie les logs d'erreurs anciens
   * @param {number} daysToKeep - Nombre de jours à conserver
   */
  async cleanupOldLogs(daysToKeep = 7) {
    try {
      const logsDir = 'logs';
      const files = await fs.readdir(logsDir);
      const cutoffDate = new Date().toISOString();
      cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
      
      let deletedCount = 0;
      
      for (const file of files) {
        if (file.startsWith('errors-') && file.endsWith('.json')) {
          const filePath = path.join(logsDir, file);
          const stats = await fs.stat(filePath);
          
          if (stats.mtime < cutoffDate) {
            await fs.unlink(filePath);
            deletedCount++;
          }
        }
      }
      
      console.log(`🧹 Logs nettoyés: ${deletedCount} fichiers supprimés`);
      
    } catch (error) {
      console.log(`⚠️ Erreur nettoyage logs: ${error.message}`);
    }
  }
} 