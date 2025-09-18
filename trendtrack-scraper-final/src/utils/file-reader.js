/**
 * Gestionnaire de fichiers pour le scraper
 * Gère la lecture, écriture et validation des fichiers de données
 */

import fs from 'fs/promises';
import path from 'path';
import { optimizationConfig } from '../config.js';

export class FileReader {
  constructor() {
    this.supportedFormats = ['json', 'csv', 'txt'];
    this.encoding = 'utf8';
  }

  /**
   * Lit un fichier de données
   * @param {string} filePath - Chemin du fichier
   * @param {string} format - Format du fichier (json, csv, txt)
   * @returns {Promise<Object>} - Données lues
   */
  async readDataFile(filePath, format = 'json') {
    try {
      console.log(`📖 Lecture du fichier: ${filePath}`);
      
      if (!this.supportedFormats.includes(format)) {
        throw new Error(`Format non supporté: ${format}`);
      }
      
      const content = await fs.readFile(filePath, this.encoding);
      
      switch (format) {
        case 'json':
          return JSON.parse(content);
        case 'csv':
          return this.parseCSV(content);
        case 'txt':
          return this.parseTXT(content);
        default:
          throw new Error(`Format non géré: ${format}`);
      }
      
    } catch (error) {
      console.log(`❌ Erreur lecture fichier ${filePath}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Parse un fichier CSV
   * @param {string} content - Contenu CSV
   * @returns {Array} - Données parsées
   */
  parseCSV(content) {
    const lines = content.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      const row = {};
      
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      
      data.push(row);
    }
    
    return data;
  }

  /**
   * Parse un fichier TXT
   * @param {string} content - Contenu TXT
   * @returns {Array} - Données parsées
   */
  parseTXT(content) {
    return content.trim().split('\n').filter(line => line.trim());
  }

  /**
   * Lit une liste d'URLs depuis un fichier
   * @param {string} filePath - Chemin du fichier
   * @returns {Promise<Array>} - Liste d'URLs
   */
  async readUrlList(filePath) {
    try {
      const content = await fs.readFile(filePath, this.encoding);
      const urls = content.trim().split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'))
        .map(url => {
          // Ajouter https:// si pas de protocole
          if (!url.startsWith('http://') && !url.startsWith('https://')) {
            return `https://${url}`;
          }
          return url;
        });
      
      console.log(`📋 ${urls.length} URLs chargées depuis ${filePath}`);
      return urls;
      
    } catch (error) {
      console.log(`❌ Erreur lecture URLs ${filePath}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Valide une liste d'URLs
   * @param {Array} urls - Liste d'URLs à valider
   * @returns {Object} - Résultat de validation
   */
  validateUrls(urls) {
    const validation = {
      valid: [],
      invalid: [],
      total: urls.length
    };
    
    const urlPattern = optimizationConfig.validation.patterns.url;
    
    for (const url of urls) {
      if (urlPattern.test(url)) {
        validation.valid.push(url);
      } else {
        validation.invalid.push(url);
      }
    }
    
    console.log(`✅ Validation URLs: ${validation.valid.length} valides, ${validation.invalid.length} invalides`);
    return validation;
  }

  /**
   * Sauvegarde des données dans un fichier
   * @param {string} filePath - Chemin du fichier
   * @param {Object} data - Données à sauvegarder
   * @param {string} format - Format de sauvegarde
   * @returns {Promise<string>} - Chemin du fichier sauvegardé
   */
  async saveDataFile(filePath, data, format = 'json') {
    try {
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      
      let content;
      switch (format) {
        case 'json':
          content = JSON.stringify(data, null, 2);
          break;
        case 'csv':
          content = this.convertToCSV(data);
          break;
        case 'txt':
          content = Array.isArray(data) ? data.join('\n') : JSON.stringify(data, null, 2);
          break;
        default:
          throw new Error(`Format non supporté: ${format}`);
      }
      
      await fs.writeFile(filePath, content, this.encoding);
      console.log(`💾 Fichier sauvegardé: ${filePath}`);
      return filePath;
      
    } catch (error) {
      console.log(`❌ Erreur sauvegarde ${filePath}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Convertit des données en CSV
   * @param {Array} data - Données à convertir
   * @returns {string} - Contenu CSV
   */
  convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) {
      return '';
    }
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        if (typeof value === 'string') {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }

  /**
   * Liste les fichiers dans un répertoire
   * @param {string} directory - Répertoire à lister
   * @param {string} pattern - Pattern de filtrage (optionnel)
   * @returns {Promise<Array>} - Liste des fichiers
   */
  async listFiles(directory, pattern = null) {
    try {
      const files = await fs.readdir(directory);
      
      if (pattern) {
        const regex = new RegExp(pattern);
        return files.filter(file => regex.test(file));
      }
      
      return files;
      
    } catch (error) {
      console.log(`❌ Erreur liste fichiers ${directory}: ${error.message}`);
      return [];
    }
  }

  /**
   * Vérifie si un fichier existe
   * @param {string} filePath - Chemin du fichier
   * @returns {Promise<boolean>} - Fichier existe
   */
  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Supprime un fichier
   * @param {string} filePath - Chemin du fichier
   * @returns {Promise<boolean>} - Succès de la suppression
   */
  async deleteFile(filePath) {
    try {
      await fs.unlink(filePath);
      console.log(`🗑️ Fichier supprimé: ${filePath}`);
      return true;
    } catch (error) {
      console.log(`❌ Erreur suppression ${filePath}: ${error.message}`);
      return false;
    }
  }

  /**
   * Nettoie les fichiers anciens
   * @param {string} directory - Répertoire à nettoyer
   * @param {number} daysToKeep - Nombre de jours à conserver
   * @returns {Promise<number>} - Nombre de fichiers supprimés
   */
  async cleanupOldFiles(directory, daysToKeep = 7) {
    try {
      const files = await fs.readdir(directory);
      const cutoffDate = new Date().toISOString();
      cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
      
      let deletedCount = 0;
      
      for (const file of files) {
        const filePath = path.join(directory, file);
        const stats = await fs.stat(filePath);
        
        if (stats.mtime < cutoffDate) {
          await fs.unlink(filePath);
          deletedCount++;
        }
      }
      
      console.log(`🧹 Nettoyage fichiers: ${deletedCount} supprimés dans ${directory}`);
      return deletedCount;
      
    } catch (error) {
      console.log(`❌ Erreur nettoyage ${directory}: ${error.message}`);
      return 0;
    }
  }
} 