/**
 * Script de mise à jour PARALLÈLE CORRIGÉ de la base de données
 * Utilise exactement la même logique que le scraper qui fonctionne
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import path from 'path';

const LOG_PROGRESS_FILE = 'logs/update-progress-parallel-fixed.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

/**
 * PHASE 1: Extraction de toutes les données du tableau (sans navigation vers détails)
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
      
      // Extraction des données du tableau UNIQUEMENT (sans navigation vers détails)
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
 * PHASE 2: Sauvegarde immédiate en base
 */
async function saveTableDataToDatabase(shopRepo, tableData) {
  logProgress('💾 PHASE 2: Sauvegarde immédiate des données du tableau...');
  
  const results = {
    updated: 0,
    inserted: 0,
    errors: 0,
    skipped: 0
  };
  
  for (let i = 0; i < tableData.length; i++) {
    const shopData = tableData[i];
    
    try {
      // Vérifier si le shop existe déjà
      const existingShop = await shopRepo.getByUrl(shopData.shopUrl || shopData.shop_url);
      if (existingShop) {
        logProgress(`⏭️ Shop déjà existant: ${shopData.shopName || shopData.shop_name} - Ignoré`);
        results.skipped++;
        continue;
      }
      
      // Shop n'existe pas, on l'ajoute
      const shopId = await shopRepo.upsert(shopData);
      if (shopId) {
        results.inserted++;
        logProgress(`🆕 Nouveau shop: ${shopData.shopName || shopData.shop_name} - ID: ${shopId}`);
      } else {
        results.errors++;
        logProgress(`❌ Échec upsert: ${shopData.shopName || shopData.shop_name}`);
      }
    } catch (error) {
      results.errors++;
      logProgress(`❌ Erreur traitement: ${error.message}`);
    }
  }
  
  logProgress(`✅ PHASE 2 TERMINÉE: ${results.inserted} boutiques sauvegardées en base`);
  return results;
}

/**
 * Fonction principale avec architecture parallèle corrigée
 */
async function updateDatabaseParallelFixed() {
  logProgress('🚀 DÉMARRAGE - Architecture parallèle CORRIGÉE TrendTrack');
  
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
    
    // PHASE 1: Extraction des données du tableau uniquement
    const tableData = await extractTableDataOnly(extractor, 5);
    
    if (!tableData || tableData.length === 0) {
      logProgress('❌ Aucune donnée du tableau extraite');
      return;
    }
    
    // Export debug des données du tableau
    fs.writeFileSync('export-table-data-fixed.json', JSON.stringify(tableData, null, 2));
    
    // PHASE 2: Sauvegarde immédiate en base
    const saveResults = await saveTableDataToDatabase(shopRepo, tableData);
    
    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES - ARCHITECTURE PARALLÈLE CORRIGÉE:');
    logProgress('==================================================');
    logProgress(`📋 Données tableau extraites: ${tableData.length}`);
    logProgress(`💾 Boutiques sauvegardées: ${saveResults.inserted}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${saveResults.skipped}`);
    logProgress(`❌ Erreurs: ${saveResults.errors}`);
    logProgress('✅ Architecture parallèle corrigée terminée avec succès !');
    
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
updateDatabaseParallelFixed().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});

