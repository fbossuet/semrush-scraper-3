/**
 * Script MVP de mise à jour de la base de données - ARCHITECTURE MVP
 * Extrait les nouvelles données de TrendTrack avec les solutions obligatoires
 * - SOLUTION 1: Gestion des contextes fermés
 * - SOLUTION 3: Gestion des sessions expirées
 * 
 * Configuration MVP:
 * - 1 page maximum
 * - 100 boutiques maximum
 * - Récupération automatique des erreurs critiques
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';
import { acquireLock, releaseLock } from './src/utils/db-lock.js';
import path from 'path';

// Import des classes MVP
import { MVPContextManager } from './src/mvp/mvp-context-manager.js';
import { MVPSessionManager } from './src/mvp/mvp-session-manager.js';
import { MVPRetryHandler } from './src/mvp/mvp-retry-handler.js';
import { MVPScraper } from './src/mvp/mvp-scraper.js';

const LOCK_FILE = path.join(process.cwd(), 'trendtrack-mvp-db.lock');
const LOG_PROGRESS_FILE = 'logs/update-mvp-progress.log';

// Configuration MVP
const MVP_CONFIG = {
  // Timeouts (basés sur les valeurs existantes)
  navigationTimeout: 60000,        // 60s (valeur existante)
  selectorTimeout: 15000,          // 15s (valeur existante)
  pageLoadTimeout: 30000,          // 30s (valeur existante)
  
  // Retry (basé sur les patterns existants)
  maxRetries: 3,                   // 3 tentatives (standard)
  retryDelay: 1000,                // 1s base delay
  retryBackoff: 'exponential',     // 1s, 2s, 3s
  
  // Pauses (basées sur les délais existants)
  pageLoadPause: 3000,             // 3s après navigation
  betweenShopsPause: 2000,         // 2s entre boutiques
  batchPause: 5000,                // 5s entre lots
  
  // Limites MVP
  maxShopsPerRun: 10000,           // Limite pour MVP
  maxPagesPerRun: 1,               // 1 page pour MVP
  batchSize: 5                     // 5 boutiques par lot
};

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

async function main() {
  logProgress('🚀 DÉMARRAGE - Architecture MVP TrendTrack');
  logProgress('==================================================');
  
  try {
    // Acquisition du lock
    logProgress('🔒 Acquisition du lock fichier...');
    await acquireLock(LOCK_FILE);
    
    // Initialisation de la base de données
    logProgress('🗄️ Initialisation de la base de données...');
    const dbManager = new DatabaseManager();
    await dbManager.init();
    const shopRepo = new ShopRepository(dbManager);
    
    // Initialisation du scraper MVP
    logProgress('🚀 Initialisation du scraper MVP...');
    const mvpScraper = new MVPScraper(MVP_CONFIG, shopRepo);
    await mvpScraper.initialize();
    
    // Vérification de l'état de la base
    const existingShops = await shopRepo.findByTableScrapingStatus('table_extracted');
    logProgress(`🔍 Trouvé ${existingShops.length} boutiques avec statut table_scraping_status: table_extracted`);
    
    if (existingShops.length === 0) {
      logProgress('🆕 Nouveau scraping MVP - Phase 1: Extraction du tableau');
      await executePhase1MVP(mvpScraper, shopRepo);
    } else {
      logProgress('🔄 Scraping MVP - Phase 3: Extraction des détails');
      await executePhase3MVP(mvpScraper, shopRepo, existingShops);
    }
    
    logProgress('✅ MVP terminé avec succès');
    
  } catch (error) {
    logProgress(`❌ Erreur MVP: ${error.message}`);
    throw error;
  } finally {
    // Libération du lock
    await releaseLock(LOCK_FILE);
  }
}

// PHASE 1 MVP: Extraction des données du tableau uniquement
async function executePhase1MVP(mvpScraper, shopRepo) {
  logProgress(`📋 PHASE 1 MVP: Extraction de ${MVP_CONFIG.maxPagesPerRun} pages...`);
  
  try {
    const allTableData = await mvpScraper.extractTableData(MVP_CONFIG.maxPagesPerRun);
    logProgress(`✅ PHASE 1 MVP TERMINÉE: ${allTableData.length} boutiques extraites du tableau`);
    
    // PHASE 2 MVP: Sauvegarde immédiate
    logProgress('💾 PHASE 2 MVP: Sauvegarde immédiate des données du tableau...');
    await saveTableDataMVP(allTableData, shopRepo);
    logProgress(`✅ PHASE 2 MVP TERMINÉE: ${allTableData.length} boutiques sauvegardées en base`);
    
    // PHASE 3 MVP: Extraction des détails
    logProgress('🔄 PHASE 3 MVP: Extraction des détails depuis la page de liste...');
    await executePhase3MVP(mvpScraper, shopRepo, allTableData);
    
  } catch (error) {
    logProgress(`❌ Erreur Phase 1 MVP: ${error.message}`);
    throw error;
  }
}

// PHASE 3 MVP: Extraction des détails avec récupération automatique
async function executePhase3MVP(mvpScraper, shopRepo, shopsToProcess) {
  logProgress(`📋 Traitement MVP par petits lots pour éviter les blocages...`);
  
  // Filtrer les boutiques avec UUID valide
  const validShops = shopsToProcess.filter(shop => shop.external_id && shop.external_id !== 'undefined');
  logProgress(`🔍 ${validShops.length} boutiques avec UUID valide à traiter`);
  
  if (validShops.length === 0) {
    logProgress('⚠️ Aucune boutique avec UUID valide trouvée');
    return;
  }
  
  // Limiter à la configuration MVP
  const limitedShops = validShops.slice(0, MVP_CONFIG.maxShopsPerRun);
  logProgress(`🎯 Limitation MVP: ${limitedShops.length} boutiques à traiter`);
  
  const batches = [];
  for (let i = 0; i < limitedShops.length; i += MVP_CONFIG.batchSize) {
    batches.push(limitedShops.slice(i, i + MVP_CONFIG.batchSize));
  }
  
  let totalSuccess = 0;
  let totalErrors = 0;
  let allFailedShops = []; // Collecter toutes les boutiques en échec
  
  for (const [batchIndex, batch] of batches.entries()) {
    logProgress(`🔄 Lot ${batchIndex + 1}/${batches.length}: ${batch.length} boutiques`);
    
    const batchResult = await mvpScraper.processBatch(batch);
    totalSuccess += batchResult.success;
    totalErrors += batchResult.failed;
    
    // Collecter les boutiques en échec pour mini-retry
    if (batchResult.failedShops && batchResult.failedShops.length > 0) {
      allFailedShops = allFailedShops.concat(batchResult.failedShops);
    }
    
    logProgress(`📊 Lot ${batchIndex + 1} terminé: ${batchResult.success} succès, ${batchResult.failed} erreurs`);
    
    // Pause entre les lots
    if (batchIndex < batches.length - 1) {
      logProgress(`⏸️ Pause de ${MVP_CONFIG.batchPause / 1000} secondes avant le lot suivant...`);
      await new Promise(resolve => setTimeout(resolve, MVP_CONFIG.batchPause));
    }
  }
  
  // MINI-RETRY GLOBAL DES BOUTIQUES EN ÉCHEC (V2)
  if (allFailedShops.length > 0) {
    logProgress(`🔄 MINI-RETRY GLOBAL: ${allFailedShops.length} boutiques en échec`);
    
    const miniRetryResult = await mvpScraper.miniRetryFailedShops(allFailedShops, 1);
    totalSuccess += miniRetryResult.success;
    totalErrors += miniRetryResult.failed;
    
    logProgress(`📊 Mini-retry terminé: ${miniRetryResult.success} succès supplémentaires, ${miniRetryResult.failed} échecs persistants`);
  }
  
  const successRate = (totalSuccess / limitedShops.length) * 100;
  logProgress(`🎯 RÉSULTAT FINAL MVP V2: ${totalSuccess}/${limitedShops.length} boutiques (${successRate.toFixed(1)}% de succès)`);
  
  if (successRate >= 90) {
    logProgress('✅ MVP V2 VALIDÉ: Taux de succès >90%');
  } else {
    logProgress(`⚠️ MVP V2 À AMÉLIORER: Taux de succès ${successRate.toFixed(1)}% < 90%`);
  }
}

// Sauvegarde des données du tableau (Phase 2 MVP)
async function saveTableDataMVP(tableData, shopRepo) {
  const batchSize = MVP_CONFIG.batchSize; // Utiliser la configuration MVP
  const batches = [];
  
  for (let i = 0; i < tableData.length; i += batchSize) {
    batches.push(tableData.slice(i, i + batchSize));
  }
  
  for (const [batchIndex, batch] of batches.entries()) {
    logProgress(`📦 Lot ${batchIndex + 1}/${batches.length} sauvegardé`);
    
    for (const shopData of batch) {
      try {
        // Mapping correct des champs pour la sauvegarde
        const mappedShopData = {
          shopName: shopData.shop_name,
          shopUrl: shopData.shop_url,
          category: shopData.category,
          // monthlyVisits: shopData.monthly_visits, // Supprimé comme demandé
          totalProducts: shopData.total_products,
          yearFounded: shopData.year_founded,
          // liveAds7d et liveAds30d: extraits UNIQUEMENT en Phase 3, pas en Phase 1
          // Pas de métrique live_ads en Phase 1 selon la spécification
          scrapingStatus: shopData.scraping_status,
          projectSource: 'trendtrack',
          externalId: shopData.external_id // UUID obligatoire, pas de fallback sur l'ID de base
        };
        
        await shopRepo.upsert(mappedShopData);
        // Le statut table_scraping_status est déjà défini dans mappedShopData
      } catch (error) {
        logProgress(`❌ Erreur sauvegarde ${shopData.shop_name}: ${error.message}`);
      }
    }
  }
}

// Gestion des signaux pour arrêt propre
process.on('SIGINT', async () => {
  logProgress('🛑 Arrêt demandé par l\'utilisateur...');
  await releaseLock(LOCK_FILE);
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logProgress('🛑 Arrêt demandé par le système...');
  await releaseLock(LOCK_FILE);
  process.exit(0);
});

// Lancement du script
main().catch(error => {
  logProgress(`💥 Erreur fatale: ${error.message}`);
  process.exit(1);
});
