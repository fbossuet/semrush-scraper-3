/**
 * ARCHITECTURE PARALLÈLE COMPLÈTE - TrendTrack Scraper
 * Phase 1: Extraction du tableau (fonctionne)
 * Phase 2: Extraction des détails en parallèle (nouveau)
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';

const LOG_PROGRESS_FILE = 'logs/update-database-parallel-complete.log';

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
        const shopId = await shopRepo.upsert(shopData);
        if (shopId) {
          shopsToProcess.push({ id: shopId, ...shopData });
        }
      } else {
        // Shop n'existe pas, on l'ajoute avec upsert (méthode qui fonctionne)
        const shopId = await shopRepo.upsert(shopData);
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

// PHASE 3: Extraction parallèle des détails
async function extractAndSaveDetailsInParallel(extractor, shopRepo, shopsToProcess) {
  logProgress(`🔄 PHASE 3: Extraction parallèle des détails pour ${shopsToProcess.length} boutiques...`);
  
  const batchSize = 5; // Traiter par lots de 5 boutiques en parallèle
  let processedCount = 0;
  
  for (let i = 0; i < shopsToProcess.length; i += batchSize) {
    const batch = shopsToProcess.slice(i, i + batchSize);
    logProgress(`📦 Traitement lot ${Math.floor(i/batchSize) + 1}/${Math.ceil(shopsToProcess.length/batchSize)} (${batch.length} boutiques)`);
    
    // Traiter le lot en parallèle
    const promises = batch.map(async (shop) => {
      try {
        logProgress(`🔍 Extraction détails: ${shop.shopName}`);
        
        // Navigation vers la page de détail
        const detailSuccess = await extractor.navigateToShopDetail(shop.shopUrl);
        if (!detailSuccess) {
          logProgress(`❌ Navigation échouée pour ${shop.shopName}`);
          return;
        }
        
        // Extraction des métriques détaillées
        const detailData = await extractor.extractShopDetails();
        if (detailData) {
          // Mettre à jour en base
          await shopRepo.updateDetailMetrics(shop.id, detailData);
          logProgress(`✅ Détails extraits: ${shop.shopName}`);
        } else {
          logProgress(`⚠️ Aucun détail extrait: ${shop.shopName}`);
        }
        
      } catch (error) {
        logProgress(`❌ Erreur extraction détails ${shop.shopName}: ${error.message}`);
      }
    });
    
    // Attendre que tous les détails du lot soient traités
    await Promise.all(promises);
    processedCount += batch.length;
    
    logProgress(`✅ Lot ${Math.floor(i/batchSize) + 1} terminé: ${processedCount}/${shopsToProcess.length} boutiques traitées`);
    
    // Pause entre les lots pour éviter la surcharge
    if (i + batchSize < shopsToProcess.length) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  logProgress(`✅ PHASE 3 TERMINÉE: ${processedCount} boutiques traitées en parallèle`);
}

// FONCTION PRINCIPALE
async function updateDatabaseParallel() {
  logProgress('🚀 DÉMARRAGE - Architecture parallèle COMPLÈTE TrendTrack');
  logProgress('==================================================');
  
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
    
    // PHASE 3: Extraction parallèle des détails
    await extractAndSaveDetailsInParallel(extractor, shopRepo, shopsToProcess);
    
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
