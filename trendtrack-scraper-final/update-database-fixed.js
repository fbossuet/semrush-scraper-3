/**
 * Script de mise à jour de la base de données - VERSION CORRIGÉE
 * Extrait les nouvelles données de TrendTrack et les sauvegarde
 * ADAPTÉ pour la structure VPS sans modifier la DB existante
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
 * Adapte les données extraites au format attendu par upsert
 */
function adaptShopData(rawShopData) {
  return {
    shopName: rawShopData.shopName || '',
    shopUrl: rawShopData.shopUrl || '',
    creationDate: rawShopData.creationDate || '',
    category: rawShopData.category || '',
    monthlyVisits: rawShopData.monthlyVisits || '',
    monthlyRevenue: rawShopData.monthlyRevenue || '',
    liveAds: parseInt(rawShopData.liveAds) || 0,
    page: rawShopData.rowIndex || 1,
    projectSource: 'trendtrack',
    externalId: null,
    metadata: JSON.stringify({
      timestamp: rawShopData.timestamp,
      rowIndex: rawShopData.rowIndex,
      originalData: rawShopData
    }),
    scrapingStatus: 'active',
    scrapingLastUpdate: new Date().toISOString(),
    // Données analytiques (optionnelles - non extraites par le scraper actuel)
    conversionRate: rawShopData.conversionRate || null,
    organicTraffic: rawShopData.organicTraffic || null,
    brandedTraffic: rawShopData.brandedTraffic || null,
    bounceRate: rawShopData.bounceRate || null,
    averageVisitDuration: rawShopData.averageVisitDuration || null
  };
}

/**
 * Traite les données en lot pour optimiser les performances
 */
async function processBatch(shopRepo, shopsData, batchSize = 10) {
  const results = {
    updated: 0,
    inserted: 0,
    errors: 0
  };

  for (let i = 0; i < shopsData.length; i += batchSize) {
    const batch = shopsData.slice(i, i + batchSize);
    
    // Traitement parallèle du lot
    const batchPromises = batch.map(async (rawShopData) => {
      try {
        // Adapter les données au format attendu
        const adaptedShopData = adaptShopData(rawShopData);
        
        const shopId = await shopRepo.upsert(adaptedShopData);
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
        results.updated++;
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
  logProgress('🔄 Mise à jour de la base de données (VERSION CORRIGÉE)...');

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
    logProgress('🗄️ Récupération des données existantes...');
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

    // Extraction de toutes les données sur les 3 premières pages via le paramètre page dans l'URL
    logProgress('📋 Extraction des 3 premières pages via paramètre URL...');
    let onlineData = [];
    
    // Traitement séquentiel des pages pour éviter les conflits de navigation
    for (let page = 1; page <= 3; page++) {
      logProgress(`➡️  Scraping page ${page}...`);
      const navSuccess = await extractor.navigateToTrendingShops(page);
      if (!navSuccess) {
        logProgress(`❌ Navigation échouée pour la page ${page}`);
        continue; // Continuer avec la page suivante au lieu d'arrêter
      }
      const pageData = await extractor.extractAllShopsData();
      logProgress(`✅ Page ${page} : ${pageData.length} boutiques extraites`);
      onlineData = onlineData.concat(pageData);
      
      // Pause entre les pages pour éviter les conflits
      if (page < 3) {
        logProgress(`⏳ Pause entre les pages...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

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

    // Traitement optimisé en lot avec adaptation des données
    logProgress('🔄 Traitement des données en lot (avec adaptation)...');
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