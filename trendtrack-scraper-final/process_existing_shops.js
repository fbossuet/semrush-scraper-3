#!/usr/bin/env node
/**
 * Traitement des boutiques existantes pour ajouter year_founded
 * Utilise les données déjà en base
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';

class ExistingShopsProcessor {
  constructor() {
    this.browser = null;
    this.page = null;
    this.apiResponses = [];
  }

  async init() {
    console.log('🔧 Initialisation du navigateur...');
    this.browser = await chromium.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Intercepter les réponses API
    this.page.on('response', async (response) => {
      const url = response.url();
      if (this.isRelevantAPI(url)) {
        try {
          const data = await response.json();
          this.apiResponses.push({ url, data });
        } catch (e) {
          // Ignorer les réponses non-JSON
        }
      }
    });
  }

  isRelevantAPI(url) {
    return url.includes('api') || 
           url.includes('graphql') || 
           url.includes('data') ||
           url.includes('shop') ||
           url.includes('company');
  }

  async extractYearFounded(shopUrl) {
    try {
      console.log(`🔍 Extraction année de fondation pour: ${shopUrl}`);
      
      // Naviguer vers la boutique
      await this.page.goto(shopUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
      
      // Attendre un peu pour que les API se déclenchent
      await this.page.waitForTimeout(3000);
      
      // Chercher dans les réponses API
      let yearFromAPI = null;
      for (const response of this.apiResponses) {
        if (this.containsTargetData(response.data)) {
          yearFromAPI = this.extractYearFromData(response.data, null);
          if (yearFromAPI) break;
        }
      }
      
      // Si pas trouvé dans l'API, chercher dans le DOM
      let yearFromDOM = null;
      if (!yearFromAPI) {
        try {
          // Sélecteurs pour trouver des dates
          const dateSelectors = [
            'text=/founded/i',
            'text=/since/i', 
            'text=/established/i',
            'text=/created/i',
            'text=/started/i',
            '[class*="founded"]',
            '[class*="established"]',
            '[class*="since"]',
            'text=/©/i',
            'text=/copyright/i'
          ];
          
          for (const selector of dateSelectors) {
            try {
              const element = await this.page.locator(selector).first();
              if (await element.isVisible()) {
                const text = await element.textContent();
                const year = this.extractYearFromString(text);
                if (year) {
                  yearFromDOM = year;
                  break;
                }
              }
            } catch (e) {
              // Continuer avec le prochain sélecteur
            }
          }
        } catch (e) {
          console.log(`⚠️ Erreur extraction DOM: ${e.message}`);
        }
      }
      
      const finalYear = yearFromAPI || yearFromDOM;
      console.log(`📅 Année trouvée: ${finalYear || 'Non trouvée'}`);
      return finalYear;
      
    } catch (error) {
      console.log(`❌ Erreur extraction année pour ${shopUrl}: ${error.message}`);
      return null;
    }
  }

  containsTargetData(data) {
    if (!data || typeof data !== 'object') return false;
    return this.searchYearInObject(data, 3) !== null;
  }

  searchYearInObject(obj, maxDepth = 3) {
    if (maxDepth <= 0) return null;
    if (!obj || typeof obj !== 'object') return null;
    
    for (const [key, value] of Object.entries(obj)) {
      const keyLower = key.toLowerCase();
      if (keyLower.includes('founded') || 
          keyLower.includes('established') || 
          keyLower.includes('since') ||
          keyLower.includes('created') ||
          keyLower.includes('started')) {
        // Si la clé contient un mot-clé, chercher une année dans la valeur
        if (typeof value === 'string') {
          const year = this.extractYearFromString(value);
          if (year) return year;
        }
        if (typeof value === 'number' && this.isValidFoundingYear(value)) {
          return value.toString();
        }
      }
      
      if (typeof value === 'string') {
        const year = this.extractYearFromString(value);
        if (year) return year;
      }
      
      if (typeof value === 'object') {
        const year = this.searchYearInObject(value, maxDepth - 1);
        if (year) return year;
      }
    }
    return null;
  }

  extractYearFromData(apiData, domData) {
    // Chercher dans les données API
    if (apiData) {
      const apiYear = this.searchYearInObject(apiData, 5);
      if (apiYear) return apiYear;
    }
    
    // Chercher dans les données DOM
    if (domData) {
      const domYear = this.extractYearFromString(domData);
      if (domYear) return domYear;
    }
    
    return null;
  }

  extractYearFromString(text) {
    if (!text) return null;
    
    // Regex pour trouver des années
    const yearRegex = /\b(19|20)\d{2}\b/g;
    const matches = text.match(yearRegex);
    
    if (matches) {
      for (const match of matches) {
        const year = parseInt(match);
        if (this.isValidFoundingYear(year)) {
          return year.toString();
        }
      }
    }
    
    return null;
  }

  isValidFoundingYear(year) {
    return year >= 1800 && year <= 2025;
  }

  async updateShopYearFounded(shopId, yearFounded) {
    try {
      const pythonProcess = spawn('python3', ['update_year_founded.py', shopId.toString(), yearFounded]);
      
      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      // Attendre la fin du processus
      return new Promise((resolve, reject) => {
        pythonProcess.on('close', (code) => {
          if (code === 0) {
            try {
              const result = JSON.parse(output.trim());
              resolve(result);
            } catch (e) {
              resolve({ success: true });
            }
          } else {
            reject(new Error(`Script Python failed with code ${code}: ${errorOutput}`));
          }
        });
      });
      
    } catch (error) {
      throw error;
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

async function processExistingShops() {
  console.log('🚀 TRAITEMENT DES BOUTIQUES EXISTANTES');
  console.log('📅 Date:', new Date().toISOString());
  console.log('🎯 Objectif: Ajouter year_founded aux boutiques existantes');
  console.log('=' .repeat(60));
  
  const processor = new ExistingShopsProcessor();
  
  try {
    console.log('🔧 Initialisation du processeur...');
    await processor.init();
    
    // Récupérer les boutiques sans année de fondation
    console.log('📊 Récupération des boutiques sans année de fondation...');
    const pythonProcess = spawn('python3', ['get_shops_without_year_founded.py']);
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    const shopsData = await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const shops = JSON.parse(output.trim());
            resolve(shops);
          } catch (e) {
            reject(new Error(`Erreur parsing JSON: ${e.message}`));
          }
        } else {
          reject(new Error(`Script Python failed: ${errorOutput}`));
        }
      });
    });
    
    console.log(`📋 ${shopsData.length} boutiques à traiter`);
    
    // Traiter les premières boutiques (limite pour le test)
    const limit = Math.min(10, shopsData.length);
    console.log(`🎯 Traitement des ${limit} premières boutiques...`);
    
    const results = {
      processed: 0,
      updated: 0,
      errors: 0
    };
    
    for (let i = 0; i < limit; i++) {
      const shop = shopsData[i];
      console.log(`\n📝 Traitement ${i + 1}/${limit}: ${shop.shop_name}`);
      
      try {
        // Extraire l'année de fondation
        const yearFounded = await processor.extractYearFounded(shop.shop_url);
        
        if (yearFounded) {
          // Mettre à jour en base
          await processor.updateShopYearFounded(shop.id, yearFounded);
          console.log(`✅ Année ${yearFounded} ajoutée pour ${shop.shop_name}`);
          results.updated++;
        } else {
          console.log(`⚠️ Aucune année trouvée pour ${shop.shop_name}`);
        }
        
        results.processed++;
        
        // Pause entre les traitements
        await new Promise(resolve => setTimeout(resolve, 3000));
        
      } catch (error) {
        console.error(`❌ Erreur traitement ${shop.shop_name}:`, error.message);
        results.errors++;
      }
    }
    
    console.log(`\n📊 RÉSULTATS FINAUX:`);
    console.log(`✅ Boutiques traitées: ${results.processed}`);
    console.log(`📅 Années ajoutées: ${results.updated}`);
    console.log(`❌ Erreurs: ${results.errors}`);
    console.log(`📈 Taux de réussite: ${((results.updated / results.processed) * 100).toFixed(1)}%`);
    
    console.log('\n🎉 TRAITEMENT TERMINÉ AVEC SUCCÈS !');
    
  } catch (error) {
    console.error('❌ ERREUR LORS DU TRAITEMENT:', error);
    console.error('Stack trace:', error.stack);
  } finally {
    console.log('\n🔧 Nettoyage des ressources...');
    await processor.close();
    console.log('✅ Traitement terminé');
  }
}

// Lancer le traitement
processExistingShops().catch(console.error);
