/**
 * Module de cache intelligent pour optimiser les performances
 * Mémorise les résultats d'extraction et évite les re-extractions inutiles
 */

import fs from 'fs/promises';
import path from 'path';
import { optimizationConfig } from '../config.js';

export class CacheManager {
  constructor() {
    this.cacheDir = 'cache';
    this.cacheData = new Map();
    this.stats = {
      hits: 0,
      misses: 0,
      saves: 0,
      invalidations: 0
    };
  }

  /**
   * Initialise le cache et charge les données existantes
   */
  async initialize() {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true });
      await this.loadCache();
      console.log('✅ Cache intelligent initialisé');
    } catch (error) {
      console.log('⚠️ Cache non initialisé, utilisation en mémoire uniquement');
    }
  }

  /**
   * Génère une clé de cache pour un URL et un type de données
   * @param {string} url - URL de la page
   * @param {string} dataType - Type de données (overview, details, list)
   * @returns {string} - Clé de cache
   */
  generateCacheKey(url, dataType) {
    const cleanUrl = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
    return `${cleanUrl}_${dataType}`;
  }

  /**
   * Vérifie si des données sont disponibles en cache
   * @param {string} url - URL de la page
   * @param {string} dataType - Type de données
   * @returns {Object|null} - Données en cache ou null
   */
  async getCachedData(url, dataType) {
    const key = this.generateCacheKey(url, dataType);
    
    // Vérifier en mémoire d'abord
    if (this.cacheData.has(key)) {
      const cached = this.cacheData.get(key);
      if (this.isValid(cached)) {
        this.stats.hits++;
        console.log(`🎯 Cache HIT: ${url} (${dataType})`);
        return cached.data;
      } else {
        this.cacheData.delete(key);
        this.stats.invalidations++;
      }
    }

    // Vérifier sur disque
    try {
      const filePath = path.join(this.cacheDir, `${key}.json`);
      const fileContent = await fs.readFile(filePath, 'utf8');
      const cached = JSON.parse(fileContent);
      
      if (this.isValid(cached)) {
        this.cacheData.set(key, cached);
        this.stats.hits++;
        console.log(`🎯 Cache HIT (disque): ${url} (${dataType})`);
        return cached.data;
      } else {
        await fs.unlink(filePath);
        this.stats.invalidations++;
      }
    } catch (error) {
      // Fichier n'existe pas ou erreur de lecture
    }

    this.stats.misses++;
    console.log(`❌ Cache MISS: ${url} (${dataType})`);
    return null;
  }

  /**
   * Sauvegarde des données en cache
   * @param {string} url - URL de la page
   * @param {string} dataType - Type de données
   * @param {Object} data - Données à sauvegarder
   */
  async setCachedData(url, dataType, data) {
    const key = this.generateCacheKey(url, dataType);
    const cacheEntry = {
      url,
      dataType,
      data,
      timestamp: new Date().toISOString(),
      ttl: this.getTTL(dataType)
    };

    // Sauvegarder en mémoire
    this.cacheData.set(key, cacheEntry);

    // Sauvegarder sur disque
    try {
      const filePath = path.join(this.cacheDir, `${key}.json`);
      await fs.writeFile(filePath, JSON.stringify(cacheEntry, null, 2));
      this.stats.saves++;
      console.log(`💾 Cache SAVE: ${url} (${dataType})`);
    } catch (error) {
      console.log(`⚠️ Erreur sauvegarde cache: ${error.message}`);
    }
  }

  /**
   * Vérifie si une entrée de cache est valide
   * @param {Object} cached - Entrée de cache
   * @returns {boolean} - True si valide
   */
  isValid(cached) {
    if (!cached || !cached.timestamp || !cached.ttl) {
      return false;
    }

    const age = new Date().toISOString() - cached.timestamp;
    return age < cached.ttl;
  }

  /**
   * Récupère le TTL (Time To Live) pour un type de données
   * @param {string} dataType - Type de données
   * @returns {number} - TTL en millisecondes
   */
  getTTL(dataType) {
    const config = optimizationConfig.cache.interfaces[dataType];
    return config ? config.maxAge : 30 * 60 * 1000; // 30 minutes par défaut
  }

  /**
   * Charge le cache depuis le disque
   */
  async loadCache() {
    try {
      const files = await fs.readdir(this.cacheDir);
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const filePath = path.join(this.cacheDir, file);
            const content = await fs.readFile(filePath, 'utf8');
            const cached = JSON.parse(content);
            
            if (this.isValid(cached)) {
              const key = this.generateCacheKey(cached.url, cached.dataType);
              this.cacheData.set(key, cached);
            } else {
              // Supprimer les entrées expirées
              await fs.unlink(filePath);
            }
          } catch (error) {
            console.log(`⚠️ Erreur chargement cache ${file}: ${error.message}`);
          }
        }
      }
      
      console.log(`📦 Cache chargé: ${this.cacheData.size} entrées valides`);
    } catch (error) {
      console.log('⚠️ Erreur chargement cache:', error.message);
    }
  }

  /**
   * Nettoie le cache (supprime les entrées expirées)
   */
  async cleanup() {
    const toDelete = [];
    
    for (const [key, cached] of this.cacheData.entries()) {
      if (!this.isValid(cached)) {
        toDelete.push(key);
      }
    }
    
    for (const key of toDelete) {
      this.cacheData.delete(key);
      try {
        const filePath = path.join(this.cacheDir, `${key}.json`);
        await fs.unlink(filePath);
      } catch (error) {
        // Fichier déjà supprimé
      }
    }
    
    console.log(`🧹 Cache nettoyé: ${toDelete.length} entrées supprimées`);
  }

  /**
   * Affiche les statistiques du cache
   */
  printStats() {
    console.log('📊 Statistiques Cache:');
    console.log(`   Hits: ${this.stats.hits}`);
    console.log(`   Misses: ${this.stats.misses}`);
    console.log(`   Saves: ${this.stats.saves}`);
    console.log(`   Invalidations: ${this.stats.invalidations}`);
    console.log(`   Entrées en mémoire: ${this.cacheData.size}`);
  }

  /**
   * Vide complètement le cache
   */
  async clear() {
    this.cacheData.clear();
    this.stats = { hits: 0, misses: 0, saves: 0, invalidations: 0 };
    
    try {
      const files = await fs.readdir(this.cacheDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          await fs.unlink(path.join(this.cacheDir, file));
        }
      }
      console.log('🗑️ Cache vidé complètement');
    } catch (error) {
      console.log('⚠️ Erreur vidage cache:', error.message);
    }
  }
} 