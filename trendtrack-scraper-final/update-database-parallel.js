/**
 * Script de mise à jour PARALLÈLE de la base de données
 * Architecture en 2 phases :
 * 1. Extraction de toutes les données du tableau (sans navigation)
 * 2. Extraction parallèle des détails avec mise à jour incrémentale
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import path from 'path';

const LOG_PROGRESS_FILE = 'logs/update-progress-parallel.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

/**
 * PHASE 1: Extraction de toutes les données du tableau
 * Sans navigation vers les pages de détail
 */
async function extractTableDataOnly(extractor, pages = 5) {
  logProgress('📋 PHASE 1: Extraction des données du tableau uniquement...');
  
  const allTableData = [];
  
  for (let page = 1; page <= pages; page++) {
    logProgress(`➡️  Extraction page ${page}/${pages}...`);
    
    try {
      // Navigation vers la page
      const navSuccess = await extractor.navigateToTrendingShops(page);
      if (!navSuccess) {
        logProgress(`❌ Navigation échouée pour la page ${page}`);
        continue;
      }
      
      // Extraction des données du tableau uniquement (sans navigation vers détails)
      const pageData = await extractor.extractAllShopsData(false); // false = pas de métriques avancées
      logProgress(`✅ Page ${page}: ${pageData.length} boutiques extraites du tableau`);
      
      allTableData.push(...pageData);
      
      // Pause entre les pages
      if (page < pages) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
    } catch (error) {
      logProgress(`❌ Erreur page ${page}: ${error.message}`);
      continue;
    }
  }
  
  logProgress(`✅ PHASE 1 TERMINÉE: ${allTableData.length} boutiques extraites du tableau`);
  return allTableData;
}

/**
 * PHASE 2: Sauvegarde immédiate en base avec IDs générés
 */
async function saveTableDataToDatabase(shopRepo, tableData) {
  logProgress('💾 PHASE 2: Sauvegarde immédiate des données du tableau...');
  
  const savedShops = [];
  const batchSize = 20;
  
  for (let i = 0; i < tableData.length; i += batchSize) {
    const batch = tableData.slice(i, i + batchSize);
    
    const batchPromises = batch.map(async (shopData) => {
      try {
        // Vérifier si le shop existe déjà
        const existingShop = await shopRepo.getByUrl(shopData.shopUrl || shopData.shop_url);
        
        if (existingShop) {
          logProgress(`⏭️ Shop existant: ${shopData.shopName || shopData.shop_name} - Mise à jour`);
          // Mettre à jour les données du tableau
          await shopRepo.updateTableData(existingShop.id, shopData);
          return { ...existingShop, updated: true };
        } else {
          // Nouveau shop - insertion avec ID généré
          const shopId = await shopRepo.insertTableData(shopData);
          if (shopId) {
            const newShop = await shopRepo.getById(shopId);
            logProgress(`🆕 Nouveau shop: ${shopData.shopName || shopData.shop_name} - ID: ${shopId}`);
            return { ...newShop, updated: false };
          }
        }
      } catch (error) {
        logProgress(`❌ Erreur sauvegarde: ${error.message}`);
        return null;
      }
    });
    
    const batchResults = await Promise.all(batchPromises);
    savedShops.push(...batchResults.filter(shop => shop !== null));
    
    logProgress(`📦 Lot ${Math.floor(i / batchSize) + 1}/${Math.ceil(tableData.length / batchSize)} sauvegardé`);
  }
  
  logProgress(`✅ PHASE 2 TERMINÉE: ${savedShops.length} boutiques sauvegardées en base`);
  return savedShops;
}

/**
 * PHASE 3: Extraction parallèle des détails avec liaison par URL
 */
async function extractDetailsInParallel(extractor, savedShops, maxConcurrency = 5) {
  logProgress('🔍 PHASE 3: Extraction parallèle des détails...');
  
  const results = {
    success: 0,
    errors: 0,
    skipped: 0
  };
  
  // Traitement par lots pour éviter la surcharge
  for (let i = 0; i < savedShops.length; i += maxConcurrency) {
    const batch = savedShops.slice(i, i + maxConcurrency);
    
    const batchPromises = batch.map(async (shop) => {
      try {
        logProgress(`🔍 Extraction détails: ${shop.shop_name} (ID: ${shop.id})`);
        
        // Navigation vers la page de détail
        const detailSuccess = await extractor.navigateToShopDetail(shop.shop_url);
        if (!detailSuccess) {
          logProgress(`⚠️ Navigation détail échouée: ${shop.shop_name}`);
          return { success: false, error: 'Navigation échouée' };
        }
        
        // Extraction des détails
        const detailData = await extractor.extractShopDetails();
        
        // Retour à la page liste (sans perdre la session)
        await extractor.returnToListPage();
        
        return {
          success: true,
          shopId: shop.id,
          shopUrl: shop.shop_url,
          detailData
        };
        
      } catch (error) {
        logProgress(`❌ Erreur détails ${shop.shop_name}: ${error.message}`);
        return { success: false, error: error.message };
      }
    });
    
    const batchResults = await Promise.all(batchPromises);
    
    // Traitement des résultats du lot
    for (const result of batchResults) {
      if (result.success) {
        results.success++;
        logProgress(`✅ Détails extraits: ${result.shopUrl}`);
      } else {
        results.errors++;
        logProgress(`❌ Erreur détails: ${result.error}`);
      }
    }
    
    logProgress(`📦 Lot détails ${Math.floor(i / maxConcurrency) + 1}/${Math.ceil(savedShops.length / maxConcurrency)} traité`);
    
    // Pause entre les lots
    if (i + maxConcurrency < savedShops.length) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  logProgress(`✅ PHASE 3 TERMINÉE: ${results.success} succès, ${results.errors} erreurs`);
  return results;
}

/**
 * PHASE 4: Mise à jour incrémentale des métriques
 */
async function updateMetricsIncremental(shopRepo, detailResults) {
  logProgress('📊 PHASE 4: Mise à jour incrémentale des métriques...');
  
  const updatePromises = detailResults.map(async (result) => {
    if (result.success && result.detailData) {
      try {
        await shopRepo.updateDetailMetrics(result.shopId, result.detailData);
        logProgress(`📊 Métriques mises à jour: ${result.shopUrl}`);
        return { success: true, shopId: result.shopId };
      } catch (error) {
        logProgress(`❌ Erreur mise à jour métriques: ${error.message}`);
        return { success: false, error: error.message };
      }
    }
    return { success: false, error: 'Pas de données de détail' };
  });
  
  const updateResults = await Promise.all(updatePromises);
  const successCount = updateResults.filter(r => r.success).length;
  
  logProgress(`✅ PHASE 4 TERMINÉE: ${successCount} métriques mises à jour`);
  return updateResults;
}

/**
 * Fonction principale avec architecture parallèle
 */
async function updateDatabaseParallel() {
  logProgress('🚀 DÉMARRAGE - Architecture parallèle TrendTrack');
  
  let scraper = null;
  let extractor = null;
  let dbManager = null;
  let shopRepo = null;
  
  try {
    // Initialiser le scraper
    logProgress('🚀 Initialisation du scraper...');
    scraper = new WebScraper();
    await scraper.init();
    extractor = new TrendTrackExtractor(scraper.page, scraper.errorHandler);
    
    // Initialiser la base de données
    logProgress('🗄️ Initialisation de la base de données...');
    dbManager = new DatabaseManager();
    await dbManager.init();
    shopRepo = new ShopRepository(dbManager);
    
    // Connexion à TrendTrack
    logProgress('🔑 Connexion à TrendTrack...');
    const loginSuccess = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
    
    if (!loginSuccess) {
      logProgress('❌ Échec de la connexion');
      return;
    }
    
    // PHASE 1: Extraction des données du tableau
    const tableData = await extractTableDataOnly(extractor, 5);
    
    if (!tableData || tableData.length === 0) {
      logProgress('❌ Aucune donnée du tableau extraite');
      return;
    }
    
    // Export debug des données du tableau
    fs.writeFileSync('export-table-data.json', JSON.stringify(tableData, null, 2));
    
    // PHASE 2: Sauvegarde immédiate en base
    const savedShops = await saveTableDataToDatabase(shopRepo, tableData);
    
    if (!savedShops || savedShops.length === 0) {
      logProgress('❌ Aucune boutique sauvegardée');
      return;
    }
    
    // PHASE 3: Extraction parallèle des détails
    const detailResults = await extractDetailsInParallel(extractor, savedShops, 3);
    
    // PHASE 4: Mise à jour incrémentale des métriques
    const metricResults = await updateMetricsIncremental(shopRepo, detailResults);
    
    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES - ARCHITECTURE PARALLÈLE:');
    logProgress('==================================================');
    logProgress(`📋 Données tableau extraites: ${tableData.length}`);
    logProgress(`💾 Boutiques sauvegardées: ${savedShops.length}`);
    logProgress(`🔍 Détails extraits avec succès: ${detailResults.success}`);
    logProgress(`❌ Erreurs extraction détails: ${detailResults.errors}`);
    logProgress(`📊 Métriques mises à jour: ${metricResults.filter(r => r.success).length}`);
    logProgress('✅ Architecture parallèle terminée avec succès !');
    
  } catch (error) {
    logProgress(`❌ Erreur fatale: ${error.message}`);
    console.error('❌ Erreur détaillée:', error);
  } finally {
    // Fermer les connexions
    if (scraper) {
      try {
        await scraper.close();
        logProgress('🔚 Fermeture du scraper...');
      } catch (error) {
        logProgress(`⚠️  Erreur fermeture scraper: ${error.message}`);
      }
    }
    
    if (dbManager) {
      try {
        await dbManager.close();
        logProgress('🔒 Connexion base de données fermée');
      } catch (error) {
        logProgress(`⚠️  Erreur fermeture base: ${error.message}`);
      }
    }
  }
}

// Exécution du script
updateDatabaseParallel().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});


