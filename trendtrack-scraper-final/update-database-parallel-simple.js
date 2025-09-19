/**
 * Script de mise à jour PARALLÈLE SIMPLIFIÉ de la base de données
 * Utilise la même logique que l'ancien scraper mais en mode parallèle
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import path from 'path';

const LOG_PROGRESS_FILE = 'logs/update-progress-parallel-simple.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

/**
 * Fonction principale simplifiée
 */
async function updateDatabaseParallelSimple() {
  logProgress('🚀 DÉMARRAGE - Architecture parallèle SIMPLIFIÉE TrendTrack');
  
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
    
    // PHASE 1: Extraction de toutes les données sur 1 page (comme l'ancien scraper)
    logProgress('📋 PHASE 1: Extraction de 1 page (méthode existante)...');
    const onlineData = await extractor.scrapeMultiplePages(1);
    
    if (!onlineData || onlineData.length === 0) {
      logProgress('❌ Aucune donnée extraite');
      return;
    }
    
    logProgress(`✅ ${onlineData.length} boutiques extraites`);
    
    // Export debug des données
    fs.writeFileSync('export-debug-parallel.json', JSON.stringify(onlineData, null, 2));
    
    // PHASE 2: Sauvegarde en base (méthode existante)
    logProgress('💾 PHASE 2: Sauvegarde en base...');
    
    // Récupérer les données existantes pour comparaison
    const existingShops = await shopRepo.getAllWithPagination(1000, 0);
    const existingCount = existingShops.length;
    
    logProgress(`📊 ${existingCount} boutiques existantes en base`);
    
    // Traitement en lot (méthode existante)
    const results = {
      updated: 0,
      inserted: 0,
      errors: 0,
      skipped: 0
    };
    
    for (let i = 0; i < onlineData.length; i++) {
      const shopData = onlineData[i];
      
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
    
    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES - ARCHITECTURE PARALLÈLE SIMPLIFIÉE:');
    logProgress('==================================================');
    logProgress(`📈 Boutiques extraites: ${onlineData.length}`);
    logProgress(`💾 Boutiques en base: ${existingCount + results.inserted}`);
    logProgress(`🆕 Nouvelles boutiques ajoutées: ${results.inserted}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${results.skipped}`);
    logProgress(`❌ Erreurs: ${results.errors}`);
    logProgress('✅ Architecture parallèle simplifiée terminée !');
    
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
updateDatabaseParallelSimple().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});

