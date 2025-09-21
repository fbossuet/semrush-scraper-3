/**
 * Extracteur de base pour le scraper
 * Fournit les fonctionnalités communes à tous les extracteurs
 */

import { ErrorHandler } from '../utils/error-handler.js';
import { optimizationConfig } from '../config.js';

export class BaseExtractor {
  constructor(page, errorHandler) {
    this.page = page;
    this.errorHandler = errorHandler || new ErrorHandler();
  }

  /**
   * Extrait des données selon des sélecteurs
   * @param {Object} selectors - Sélecteurs CSS
   * @param {string} context - Contexte de l'extraction
   * @returns {Promise<Object>} - Données extraites
   */
  async extractData(selectors, context = 'default') {
    return this.errorHandler.handleExtraction(async () => {
      console.log(`📊 Extraction ${context}...`);
      
      const extractedData = {};
      
      for (const [key, selector] of Object.entries(selectors)) {
        console.log(`🔍 Extraction: ${key}...`);
        
        try {
          if (selector.multiple) {
            // Pour récupérer plusieurs éléments
            const attributeName = selector.attribute;
            extractedData[key] = await this.page.$$eval(selector.selector, (elements, attr) =>
              elements.map(el => {
                if (attr) {
                  return el.getAttribute(attr);
                } else {
                  return el.textContent.trim();
                }
              }).filter(text => text && text.trim())
            , attributeName);
          } else {
            // Pour récupérer un seul élément
            const element = await this.page.$(selector.selector);
            if (element) {
              if (selector.attribute) {
                extractedData[key] = await element.getAttribute(selector.attribute);
              } else {
                extractedData[key] = await element.textContent();
              }
            } else {
              extractedData[key] = null;
              console.log(`⚠️ Élément non trouvé pour: ${key}`);
            }
          }
        } catch (error) {
          console.log(`⚠️ Erreur extraction ${key}: ${error.message}`);
          extractedData[key] = null;
        }
      }
      
      console.log(`✅ Extraction ${context} terminée`);
      return extractedData;
      
    }, context, this.page.url(), optimizationConfig.interfaces[context]?.timeout || 30000);
  }

  /**
   * Extrait des données avec validation
   * @param {Object} selectors - Sélecteurs CSS
   * @param {Object} validationRules - Règles de validation
   * @param {string} context - Contexte de l'extraction
   * @returns {Promise<Object>} - Données extraites et validées
   */
  async extractWithValidation(selectors, validationRules, context = 'default') {
    const data = await this.extractData(selectors, context);
    const validation = this.validateData(data, validationRules);
    
    if (!validation.isValid) {
      return this.errorHandler.handleValidationError(validation, context);
    }
    
    return {
      success: true,
      data,
      validation,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Valide des données selon des règles
   * @param {Object} data - Données à valider
   * @param {Object} validationRules - Règles de validation
   * @returns {Object} - Résultat de validation
   */
  validateData(data, validationRules) {
    const validation = {
      isValid: true,
      errors: [],
      warnings: []
    };

    for (const [field, rules] of Object.entries(validationRules)) {
      const value = data[field];
      
      // Vérifier si le champ est requis
      if (rules.required && (!value || value.trim() === '')) {
        validation.isValid = false;
        validation.errors.push(`Champ requis manquant: ${field}`);
        continue;
      }
      
      // Vérifier le pattern si spécifié
      if (rules.pattern && value) {
        const pattern = optimizationConfig.validation.patterns[rules.pattern];
        if (pattern && !pattern.test(value)) {
          validation.isValid = false;
          validation.errors.push(`Format invalide pour ${field}: ${value}`);
        }
      }
      
      // Vérifier la longueur si spécifiée
      if (rules.minLength && value && value.length < rules.minLength) {
        validation.warnings.push(`${field} trop court: ${value.length} < ${rules.minLength}`);
      }
      
      if (rules.maxLength && value && value.length > rules.maxLength) {
        validation.warnings.push(`${field} trop long: ${value.length} > ${rules.maxLength}`);
      }
    }

    return validation;
  }

  /**
   * Extrait des métriques selon des patterns
   * @param {string} pageText - Texte de la page
   * @param {Array} metricPatterns - Patterns de métriques
   * @param {string} prefix - Préfixe pour les logs
   * @returns {Object} - Métriques extraites
   */
  extractMetrics(pageText, metricPatterns, prefix = '📊') {
    const metrics = {};
    
    for (const [metricName, pattern] of Object.entries(metricPatterns)) {
      try {
        const match = pageText.match(pattern);
        if (match) {
          metrics[metricName] = match[1] || match[0];
          console.log(`${prefix} ${metricName}: ${metrics[metricName]}`);
        } else {
          metrics[metricName] = null;
          console.log(`${prefix} ${metricName}: Non trouvé`);
        }
      } catch (error) {
        console.log(`⚠️ Erreur extraction métrique ${metricName}: ${error.message}`);
        metrics[metricName] = null;
      }
    }
    
    return metrics;
  }

  /**
   * Attend qu'un élément soit présent
   * @param {string} selector - Sélecteur CSS
   * @param {number} timeout - Timeout en millisecondes
   * @returns {Promise<boolean>} - Élément trouvé
   */
  async waitForElement(selector, timeout = 5000) {
    try {
      await this.page.waitForSelector(selector, { timeout });
      console.log(`✅ Élément trouvé: ${selector}`);
      return true;
    } catch (error) {
      console.log(`⚠️ Élément non trouvé: ${selector}`);
      return false;
    }
  }

  /**
   * Attend que plusieurs éléments soient présents
   * @param {Array} selectors - Sélecteurs CSS
   * @param {number} timeout - Timeout en millisecondes
   * @returns {Promise<Array>} - Éléments trouvés
   */
  async waitForElements(selectors, timeout = 5000) {
    const results = [];
    
    for (const selector of selectors) {
      const found = await this.waitForElement(selector, timeout);
      results.push({ selector, found });
    }
    
    return results;
  }

  /**
   * Prend une capture d'écran
   * @param {string} filename - Nom du fichier
   * @param {string} directory - Répertoire de sauvegarde
   * @returns {Promise<string>} - Chemin du fichier
   */
  async takeScreenshot(filename, directory = 'screenshots') {
    try {
      const fs = await import('fs/promises');
      await fs.mkdir(directory, { recursive: true });
      const filepath = `${directory}/${filename}`;
      
      await this.page.screenshot({ 
        path: filepath,
        fullPage: true,
        timeout: 10000
      });
      
      console.log(`📸 Screenshot sauvegardé: ${filepath}`);
      return filepath;
    } catch (error) {
      console.log(`⚠️ Erreur screenshot: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate les résultats pour l'affichage
   * @param {Object} results - Résultats à formater
   * @returns {string} - Résultats formatés
   */
  formatResults(results) {
    if (!results || !results.data) {
      return '❌ Aucune donnée disponible';
    }

    const lines = ['📋 RÉSULTATS:'];
    
    for (const [key, value] of Object.entries(results.data)) {
      if (Array.isArray(value)) {
        lines.push(`   ${key}: ${value.length} éléments`);
        value.slice(0, 3).forEach((item, index) => {
          lines.push(`     ${index + 1}. ${item}`);
        });
        if (value.length > 3) {
          lines.push(`     ... et ${value.length - 3} autres`);
        }
      } else {
        lines.push(`   ${key}: ${value || 'Non trouvé'}`);
      }
    }
    
    return lines.join('\n');
  }

  /**
   * Nettoie les données extraites
   * @param {Object} data - Données à nettoyer
   * @returns {Object} - Données nettoyées
   */
  cleanData(data) {
    const cleaned = {};
    
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'string') {
        cleaned[key] = value.trim().replace(/\s+/g, ' ');
      } else if (Array.isArray(value)) {
        cleaned[key] = value.map(item => 
          typeof item === 'string' ? item.trim().replace(/\s+/g, ' ') : item
        ).filter(item => item && item.trim());
      } else {
        cleaned[key] = value;
      }
    }
    
    return cleaned;
  }
} 