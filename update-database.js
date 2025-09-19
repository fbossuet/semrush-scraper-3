/**
 * Script de mise à jour de la base de données
 * Extrait les nouvelles données de TrendTrack et les sauvegarde
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import { acquireLock, releaseLock } from './src/utils/db-lock.js';
import path from 'path';

const LOCK_FILE = path.join(process.cwd(), 'trendtrack-db.lock');
const LOG_PROGRESS_FILE = 'logs/update-progress.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

/**
 * Traite les données en lot pour optimiser les performances
 */
async function processBatch(shopRepo, shopsData, batchSize = 10) {
  const results = {
    updated: 0,
    inserted: 0,
    errors: 0,
    skipped: 0
  };

  for (let i = 0; i < shopsData.length; i += batchSize) {
    const batch = shopsData.slice(i, i + batchSize);
    
    // Traitement parallèle du lot
    const batchPromises = batch.map(async (shopData) => {
      try {
        // Vérifier si le shop existe déjà
        const existingShop = await shopRepo.getByUrl(shopData.shopUrl || shopData.shop_url);
        if (existingShop) {
          console.log(`⏭️ Shop déjà existant: ${shopData.shopName || shopData.shop_name} - Ignoré`);
          return { success: true, shopId: existingShop.id, skipped: true };
        }

        // Shop n'existe pas, on l'ajoute
        const shopId = await shopRepo.upsert(shopData);
        if (shopId) {
          return { success: true, shopId };
        } else {
          return { success: false, error: 'Échec upsert' };
        }
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    const batchResults = await Promise.all(batchPromises);
    
    batchResults.forEach(result => {
      if (result.success) {
        if (result.skipped) {
          results.skipped = (results.skipped || 0) + 1;
        } else {
          results.updated++;
        }
      } else {
        results.errors++;
        logProgress(`❌ Erreur traitement: ${result.error}`);
      }
    });

    logProgress(`📦 Lot ${Math.floor(i / batchSize) + 1}/${Math.ceil(shopsData.length / batchSize)} traité`);
  }

  return results;
}

async function updateDatabase() {
  logProgress('🔄 Mise à jour de la base de données...');

  let scraper = null;
  let extractor = null;
  let dbManager = null;
  let shopRepo = null;
  let lockAcquired = false;

  try {
    // Prendre le lock avant toute opération sur la base
    logProgress('🔒 Acquisition du lock fichier...');
    await acquireLock(LOCK_FILE);
    lockAcquired = true;

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

    // Extraction de toutes les données sur 1 page via la méthode scrapeMultiplePages
    logProgress('📋 Extraction de 1 page via scrapeMultiplePages...');
    const onlineData = await extractor.scrapeMultiplePages(1);

    // Export debug JSON
    fs.writeFileSync('export-debug.json', JSON.stringify(onlineData, null, 2));

    if (!onlineData || onlineData.length === 0) {
      logProgress('❌ Aucune donnée extraite');
      return;
    }

    logProgress(`✅ ${onlineData.length} boutiques extraites en ligne`);

    // Récupérer les données existantes pour comparaison
    logProgress('📊 Récupération des données existantes...');
    const existingShops = await shopRepo.getAllWithPagination(1000, 0);
    const existingCount = existingShops.length;

    logProgress(`📊 ${existingCount} boutiques existantes en base`);

    // Traitement optimisé en lot
    logProgress('🔄 Traitement des données en lot...');
    const startTime = new Date().toISOString();
    const batchResults = await processBatch(shopRepo, onlineData, 20);
    const endTime = new Date().toISOString();

    logProgress(`⏱️  Temps de traitement: ${endTime - startTime}ms`);

    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES:');
    logProgress('==================================================');
    logProgress(`📈 Boutiques en ligne: ${onlineData.length}`);
    logProgress(`💾 Boutiques en base: ${existingCount + batchResults.inserted}`);
    logProgress(`🆕 Nouvelles boutiques ajoutées: ${batchResults.inserted}`);
    logProgress(`🔄 Boutiques mises à jour: ${batchResults.updated}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${batchResults.skipped}`);
    logProgress(`🔄 Boutiques déjà existantes: ${existingCount}`);
    logProgress(`❌ Erreurs: ${batchResults.errors}`);
    logProgress('✅ Mise à jour de la base de données terminée !');

        } catch (error) {
    if (error.code === 'LOCK_UNAVAILABLE') {
      logProgress('❌ Base de données verrouillée par un autre processus');
      return;
    }
    
    logProgress(`❌ Erreur: ${error.message}`);
    console.error('❌ Erreur détaillée:', error);
  } finally {
    // Libérer le lock
    if (lockAcquired) {
      try {
        await releaseLock(LOCK_FILE);
        logProgress('🔓 Lock fichier libéré.');
        } catch (error) {
        logProgress(`⚠️  Erreur libération lock: ${error.message}`);
      }
    }

    // Fermer les connexions
    if (scraper) {
      try {
        await scraper.close();
        logProgress('🔚 Fermeture du scraper...');
        logProgress('✅ Scraper fermé');
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
updateDatabase().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
}); 