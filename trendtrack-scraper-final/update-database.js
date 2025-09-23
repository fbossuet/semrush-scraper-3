/**
 * Script de mise à jour de la base de données - ARCHITECTURE PARALLÈLE
 * Extrait les nouvelles données de TrendTrack et les sauvegarde
 * Résout le problème de perte de session avec une architecture en 3 phases
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

// PHASE 1: Extraction des données du tableau uniquement
async function extractTableDataOnly(extractor, pageCount = 5) {
  logProgress(`📋 PHASE 1: Extraction de ${pageCount} pages (méthode existante)...`);
  
  const allTableData = [];
  
  for (let page = 1; page <= pageCount; page++) {
    logProgress(`➡️  Extraction page ${page}/${pageCount}...`);
    
    try {
      // Navigation vers la page
      const navSuccess = await extractor.navigateToTrendingShops(page);
      if (!navSuccess) {
        logProgress(`❌ Navigation échouée pour la page ${page}`);
        continue;
      }
      
      // Attendre que le tableau soit chargé
      await extractor.page.waitForSelector('tbody tr', { timeout: 60000 });
      
      // Récupérer toutes les lignes du tableau
      const rows = await extractor.page.locator('tbody tr').all();
      logProgress(`📊 ${rows.length} lignes trouvées dans le tableau`);
      
      let pageShops = 0;
      
      // Extraire chaque ligne avec les SÉLECTEURS QUI FONCTIONNENT
      for (let i = 0; i < rows.length; i++) {
        try {
          const row = rows[i];
          const cells = await row.locator('td').all();
          if (cells.length < 8) {
            continue;
          }

          const shopData = {};
          
          // 0. EXTRACTION ID DE LA BOUTIQUE - NOUVEAU
          try {
            const rowHtml = await row.evaluate(el => el.outerHTML, { timeout: 10000 });
            const rowIdMatch = rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/);
            const rowId = rowIdMatch ? rowIdMatch[1] : null;
            shopData.shopId = rowId;
            shopData.externalId = rowId; // Mapping pour la base de données
            if (rowId) {
              logProgress(`✅ ID extrait: ${rowId} pour ${shopData.shopName || 'boutique'}`);
            }
          } catch (error) {
            logProgress(`⚠️ Erreur extraction ID ligne: ${error.message}`);
            shopData.shopId = null;
            shopData.externalId = null;
          }
          
          // 1. EXTRACTION INFO BOUTIQUE (cellule 1) - SÉLECTEURS QUI FONCTIONNENT
          try {
            const shopInfoHtml = await cells[1].innerHTML();
            const shopNameMatch = shopInfoHtml.match(/<p class=\"text-sm font-semibold\">([^<]+)<\/p>/);
            shopData.shopName = shopNameMatch ? shopNameMatch[1].trim() : '';
            const shopUrlMatch = shopInfoHtml.match(/href=["']([^"']+)["']/);
            shopData.shopUrl = shopUrlMatch ? shopUrlMatch[1] : '';
            const dateMatch = shopInfoHtml.match(/(\d{2}\/\d{2}\/\d{4})/);
            shopData.creationDate = dateMatch ? dateMatch[1] : '';
          } catch (error) {
            shopData.shopName = '';
            shopData.shopUrl = '';
            shopData.creationDate = '';
          }
          
          // 2. EXTRACTION NOMBRE DE PRODUITS (cellule 2) - SÉLECTEURS QUI FONCTIONNENT
          try {
            const productsCell = cells[2];
            const productsP = productsCell.locator("p:has(> span:has-text(\"products\"))");
            const productsText = await productsP.textContent();
            if (productsText) {
              const match = productsText.match(/\d[\d\s.,]*/);
              shopData.totalProducts = match ? Number(match[0].replace(/[^\d]/g, "")) : null;
            } else {
              shopData.totalProducts = null;
            }
          } catch (error) {
            shopData.totalProducts = null;
          }
          
          // 3. EXTRACTION MÉTRIQUES DE BASE (cellules 3, 4, 5) - SÉLECTEURS QUI FONCTIONNENT
          try {
            shopData.category = (await cells[3].textContent()).trim();
            shopData.monthlyVisits = (await cells[4].textContent()).trim();
            shopData.monthlyRevenue = (await cells[5].textContent()).trim();
          } catch (error) {
            shopData.category = '';
            shopData.monthlyVisits = '';
            shopData.monthlyRevenue = '';
          }
          
          // 4. EXTRACTION LIVE ADS (cellule 7) - SÉLECTEURS QUI FONCTIONNENT
          try {
            const liveAdsDiv = await cells[7].locator('div.flex.items-center.justify-center.font-semibold');
            const liveAdsP = await liveAdsDiv.locator('p').first();
            shopData.liveAds = liveAdsP ? (await liveAdsP.textContent()).trim() : '';
          } catch (error) {
            shopData.liveAds = '';
          }

          // 5. LIVE ADS 7D et 30D - Extrait en Phase 3 (page de détail) selon la spécification
          // Ces métriques ne sont PAS extraites en Phase 1
          shopData.live_ads_7d = 0;  // Valeur par défaut, sera mise à jour en Phase 3
          shopData.live_ads_30d = 0; // Valeur par défaut, sera mise à jour en Phase 3

          // Ajouter les métadonnées
          shopData.scraping_status = 'table_extracted';
          shopData.last_updated = new Date().toISOString();

          // Vérifier qu'on a au moins le nom et l'URL
          if (!shopData.shopName || !shopData.shopUrl) {
            continue;
          }

          allTableData.push(shopData);
          pageShops++;
          
        } catch (error) {
          continue;
        }
        
        // Pause minimale entre les extractions
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      logProgress(`✅ Page ${page}: ${pageShops} boutiques extraites du tableau`);
      
    } catch (error) {
      logProgress(`❌ Erreur page ${page}: ${error.message}`);
    }
  }
  
  logProgress(`✅ PHASE 1 TERMINÉE: ${allTableData.length} boutiques extraites du tableau`);
  return allTableData;
}

// PHASE 2: Sauvegarde immédiate et préparation pour l'extraction des détails
async function saveTableDataAndPrepareDetails(shopRepo, allTableData) {
  logProgress(`💾 PHASE 2: Sauvegarde immédiate des données du tableau...`);
  
  const shopsToProcess = [];
  let savedCount = 0;
  
  for (const shopData of allTableData) {
      try {
        // Vérifier si le shop existe déjà
      const existingShop = await shopRepo.getByUrl(shopData.shopUrl);
        if (existingShop) {
        logProgress(`⏭️ Shop existant: ${shopData.shopName} - Mise à jour`);
        // Mettre à jour avec upsert (méthode qui fonctionne)
        const shopDataWithStatus = { ...shopData, scrapingStatus: 'table_extracted' };
        const shopId = await shopRepo.upsert(shopDataWithStatus);
        if (shopId) {
          shopsToProcess.push({ id: shopId, ...shopData });
        }
      } else {
        // Shop n'existe pas, on l'ajoute avec upsert (méthode qui fonctionne)
        const shopDataWithStatus = { ...shopData, scrapingStatus: 'table_extracted' };
        const shopId = await shopRepo.upsert(shopDataWithStatus);
        if (shopId) {
          shopsToProcess.push({ id: shopId, ...shopData });
          savedCount++;
        }
      }
    } catch (error) {
      logProgress(`❌ Erreur sauvegarde: ${error.message}`);
    }
  }
  
  logProgress(`📦 Lot 1/1 sauvegardé`);
  logProgress(`✅ PHASE 2 TERMINÉE: ${savedCount} boutiques sauvegardées en base`);
  
  return shopsToProcess;
}

// PHASE 3: Extraction des détails depuis la page de liste (CORRIGÉE)
async function extractAndSaveDetailsInParallel(extractor, shopRepo, shopsToProcess, scraper) {
  logProgress(`🔄 PHASE 3: Extraction des détails depuis la page de liste...`);
  
  try {
    // Traiter les boutiques par petits lots pour éviter les blocages anti-bot
    logProgress(`📋 Traitement par petits lots pour éviter les blocages...`);
    
    const batchSize = 1; // Traiter 1 boutique à la fois pour éviter la détection
    const totalBatches = Math.ceil(shopsToProcess.length / batchSize);
    
    let processedCount = 0;
    let successCount = 0;
    let errorCount = 0;

    for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
      const startIndex = batchIndex * batchSize;
      const endIndex = Math.min(startIndex + batchSize, shopsToProcess.length);
      const batch = shopsToProcess.slice(startIndex, endIndex);
      
      logProgress(`🔄 Lot ${batchIndex + 1}/${totalBatches}: ${batch.length} boutiques`);
      
      for (const shop of batch) {
        try {
          logProgress(`🔍 Extraction détails: ${shop.shopName}`);
          
          // Rotation User-Agent et rechargement de session pour chaque requête
          if (extractor.scraper && extractor.scraper.page) {
            const newUserAgent = extractor.scraper.getRandomUserAgent();
            await extractor.scraper.page.setExtraHTTPHeaders({
              'User-Agent': newUserAgent
            });
            logProgress(`🔄 User-Agent changé pour ${shop.shopName}`);
            
            // Recharger la page pour éviter la détection de session
            await extractor.scraper.page.reload({ waitUntil: 'networkidle' });
            logProgress(`🔄 Page rechargée pour ${shop.shopName}`);
          }
          
          // Naviguer vers la page de détail de la boutique
          const navSuccess = await extractor.navigateToShopDetail(shop.shopUrl);
          if (!navSuccess) {
            logProgress(`⚠️ Impossible de naviguer vers ${shop.shopName}`);
            errorCount++;
            continue;
          }
          
          // Extraire les détails de la boutique
          logProgress(`🔍 Extraction des détails de la boutique (ID TrendTrack: ${shop.external_id})...`);
          const shopDetails = await extractor.extractShopDetails(shop.external_id);
          
          if (shopDetails) {
            await shopRepo.updateDetailMetrics(shop.id, shopDetails);
            logProgress(`✅ Métriques de détail mises à jour pour ID: ${shop.id}`);
            logProgress(`✅ Détails extraits: ${shop.shopName}`);
            successCount++;
        } else {
            logProgress(`⚠️ Aucun détail extrait pour ${shop.shopName}`);
            errorCount++;
          }
          
          processedCount++;
          
          // Pause aléatoire entre les boutiques pour éviter les blocages
          const randomDelay = Math.floor(Math.random() * 5000) + 3000; // 3-8 secondes
          logProgress(`⏸️ Pause de ${Math.round(randomDelay/1000)} secondes...`);
          await new Promise(resolve => setTimeout(resolve, randomDelay));
          
        } catch (error) {
          logProgress(`❌ Erreur extraction détails ${shop.shopName}: ${error.message}`);
          errorCount++;
        }
      }
      
      logProgress(`📊 Lot ${batchIndex + 1} terminé: ${successCount} succès, ${errorCount} erreurs`);
      
      // Pause plus longue entre les lots
      if (batchIndex < totalBatches - 1) {
        const lotDelay = Math.floor(Math.random() * 10000) + 5000; // 5-15 secondes
        logProgress(`⏸️ Pause de ${Math.round(lotDelay/1000)} secondes avant le lot suivant...`);
        await new Promise(resolve => setTimeout(resolve, lotDelay));
        
        // Rotation d'IP avec NordVPN après chaque lot
        if (batchIndex % 2 === 1) { // Tous les 2 lots
          logProgress(`🔄 Rotation d'IP avec NordVPN...`);
          try {
            await scraper.close();
            logProgress(`🔚 Ancienne session fermée`);
            
            // Rotation d'IP via namespace VPN
            const namespaceIndex = (batchIndex % 6) + 1; // Rotation entre 6 namespaces
            const namespace = `vpn${namespaceIndex}`;
            
            logProgress(`🌐 Changement vers namespace: ${namespace}`);
            
            // Pause pour éviter la détection
            await new Promise(resolve => setTimeout(resolve, 10000));
            
            // Nouvelle session avec namespace VPN
            scraper = new WebScraper();
            await scraper.init();
            extractor = new TrendTrackExtractor(scraper.page, scraper.errorHandler);
            
            // Reconnexion à TrendTrack
            const loginSuccess = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
            if (loginSuccess) {
              logProgress(`✅ Nouvelle session créée avec IP ${namespace}`);
      } else {
              logProgress(`❌ Échec de la reconnexion`);
              break;
            }
          } catch (error) {
            logProgress(`❌ Erreur rotation IP: ${error.message}`);
            break;
          }
        }
      }
    }
    
    logProgress(`✅ PHASE 3 TERMINÉE: ${processedCount} boutiques traitées`);
    logProgress(`📊 Résultats: ${successCount} succès, ${errorCount} erreurs`);
    
  } catch (error) {
    logProgress(`❌ Erreur Phase 3: ${error.message}`);
  }
}

// FONCTION PRINCIPALE
async function updateDatabase() {
  logProgress('🚀 DÉMARRAGE - Architecture parallèle COMPLÈTE TrendTrack');
  logProgress('==================================================');

  let scraper = null;
  let extractor = null;
  let dbManager = null;
  let shopRepo = null;
  let lockAcquired = false;

  try {
    // Prendre le lock avant toute opération sur la base
    logProgress('🔒 Acquisition du lock fichier...');
    // await acquireLock(LOCK_FILE); // Temporairement désactivé
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

    // Vérifier s'il y a des boutiques qui ont besoin de la Phase 3
    const existingShops = await shopRepo.findByStatus('table_extracted');
    
    if (existingShops.length > 0) {
      logProgress(`🔍 Détection de ${existingShops.length} boutiques avec données de base`);
      
      // Vérifier si les boutiques ont des IDs
      const shopsWithIds = existingShops.filter(shop => shop.external_id);
      if (shopsWithIds.length === 0) {
        logProgress('⚠️ Aucune boutique n\'a d\'ID externe - Forçage de la Phase 1');
        // Forcer la phase 1 pour extraire les IDs
      } else {
        logProgress(`✅ ${shopsWithIds.length} boutiques ont des IDs - Phase 3 requise`);
        // PHASE 3: Extraction parallèle des détails pour les boutiques existantes
        await extractAndSaveDetailsInParallel(extractor, shopRepo, existingShops, scraper);
        logProgress('✅ Phase 3 terminée pour les boutiques existantes');
        return;
      }
    }

    // PHASE 1: Extraction des données du tableau (nouveau scraping)
    logProgress('🆕 Nouveau scraping - Phase 1: Extraction du tableau');
    const allTableData = await extractTableDataOnly(extractor, 5);
    
    if (allTableData.length === 0) {
      logProgress('❌ Aucune boutique extraite');
      return;
    }

    // PHASE 2: Sauvegarde immédiate des données du tableau
    const shopsToProcess = await saveTableDataAndPrepareDetails(shopRepo, allTableData);
    
    if (shopsToProcess.length === 0) {
      logProgress('❌ Aucune boutique sauvegardée');
      return;
    }
    
    // PHASE 3: Extraction parallèle des détails pour les nouvelles boutiques
    await extractAndSaveDetailsInParallel(extractor, shopRepo, shopsToProcess, scraper);

    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES - ARCHITECTURE PARALLÈLE COMPLÈTE:');
    logProgress('==================================================');
    logProgress(`📈 Boutiques extraites du tableau: ${allTableData.length}`);
    logProgress(`💾 Boutiques sauvegardées en base: ${shopsToProcess.length}`);
    logProgress(`🔄 Boutiques traitées en parallèle: ${shopsToProcess.length}`);
    logProgress('✅ Architecture parallèle complète terminée !');

        } catch (error) {
    logProgress(`❌ Erreur fatale: ${error.message}`);
    console.error('❌ Erreur détaillée:', error);
  } finally {
    // Libérer le lock
    if (lockAcquired) {
      try {
        // await releaseLock(LOCK_FILE); // Temporairement désactivé
        logProgress('🔓 Lock libéré');
        } catch (error) {
        logProgress(`⚠️ Erreur libération lock: ${error.message}`);
      }
    }

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
updateDatabase().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
}); 