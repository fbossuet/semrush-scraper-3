/**
 * Script de mise à jour PAR PAGE de la base de données
 * Extrait une page à la fois pour éviter le problème de session perdue
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import path from 'path';

const LOG_PROGRESS_FILE = 'logs/update-progress-single-page.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

/**
 * Extrait une seule page et sauvegarde immédiatement
 */
async function extractAndSaveSinglePage(pageNumber) {
  logProgress(`🚀 EXTRACTION PAGE ${pageNumber} - Démarrage`);
  
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
      return { success: false, error: 'Connexion échouée' };
    }
    
    // Navigation vers la page spécifique
    logProgress(`📋 Navigation vers la page ${pageNumber}...`);
    const navSuccess = await extractor.navigateToTrendingShops(pageNumber);
    if (!navSuccess) {
      logProgress(`❌ Navigation échouée pour la page ${pageNumber}`);
      return { success: false, error: 'Navigation échouée' };
    }
    
    // Extraction des données (sans navigation vers détails)
    logProgress(`📋 Extraction des données de la page ${pageNumber}...`);
    const pageData = await extractor.extractAllShopsData(false); // false = pas de métriques avancées
    
    if (!pageData || pageData.length === 0) {
      logProgress(`❌ Aucune donnée extraite de la page ${pageNumber}`);
      return { success: false, error: 'Aucune donnée extraite' };
    }
    
    logProgress(`✅ ${pageData.length} boutiques extraites de la page ${pageNumber}`);
    
    // Sauvegarde immédiate en base
    logProgress('💾 Sauvegarde immédiate en base...');
    const results = {
      updated: 0,
      inserted: 0,
      errors: 0,
      skipped: 0
    };
    
    for (let i = 0; i < pageData.length; i++) {
      const shopData = pageData[i];
      
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
    
    // Export debug des données
    fs.writeFileSync(`export-page-${pageNumber}.json`, JSON.stringify(pageData, null, 2));
    
    // Statistiques
    logProgress(`\n📊 STATISTIQUES PAGE ${pageNumber}:`);
    logProgress('==================================================');
    logProgress(`📋 Boutiques extraites: ${pageData.length}`);
    logProgress(`🆕 Nouvelles boutiques ajoutées: ${results.inserted}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${results.skipped}`);
    logProgress(`❌ Erreurs: ${results.errors}`);
    logProgress(`✅ Page ${pageNumber} traitée avec succès !`);
    
    return { 
      success: true, 
      extracted: pageData.length, 
      inserted: results.inserted, 
      skipped: results.skipped, 
      errors: results.errors 
    };
    
  } catch (error) {
    logProgress(`❌ Erreur fatale page ${pageNumber}: ${error.message}`);
    console.error('❌ Erreur détaillée:', error);
    return { success: false, error: error.message };
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

/**
 * Fonction principale - traite une page à la fois
 */
async function updateDatabaseSinglePage() {
  const pageNumber = process.argv[2] ? parseInt(process.argv[2]) : 1;
  
  logProgress(`🚀 DÉMARRAGE - Extraction page ${pageNumber} uniquement`);
  logProgress('==================================================');
  
  const result = await extractAndSaveSinglePage(pageNumber);
  
  if (result.success) {
    logProgress(`\n✅ SUCCÈS - Page ${pageNumber} traitée`);
    logProgress(`📊 ${result.extracted} boutiques extraites`);
    logProgress(`🆕 ${result.inserted} nouvelles boutiques ajoutées`);
    logProgress(`⏭️ ${result.skipped} boutiques ignorées`);
    logProgress(`❌ ${result.errors} erreurs`);
  } else {
    logProgress(`\n❌ ÉCHEC - Page ${pageNumber} non traitée`);
    logProgress(`Erreur: ${result.error}`);
  }
  
  logProgress('\n💡 Pour traiter une autre page, utilisez:');
  logProgress(`node update-database-single-page.js [NUMERO_PAGE]`);
  logProgress('Exemple: node update-database-single-page.js 2');
}

// Exécution du script
updateDatabaseSinglePage().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});

