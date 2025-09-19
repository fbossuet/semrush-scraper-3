/**
 * Script d'extraction avec les SÉLECTEURS QUI FONCTIONNENT
 * Utilise exactement les mêmes sélecteurs que le scraper original
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';

const LOG_PROGRESS_FILE = 'logs/extract-table-working-selectors.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

async function extractTableWithWorkingSelectors() {
  logProgress('🚀 EXTRACTION AVEC SÉLECTEURS QUI FONCTIONNENT - Démarrage');
  
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
    
    // Navigation vers la page 1
    logProgress('📋 Navigation vers la page 1...');
    const navSuccess = await extractor.navigateToTrendingShops(1);
    if (!navSuccess) {
      logProgress('❌ Navigation échouée');
      return;
    }
    
    // Attendre que le tableau soit chargé
    await extractor.page.waitForSelector('tbody tr', { timeout: 60000 });
    
    // Récupérer toutes les lignes du tableau
    const rows = await extractor.page.locator('tbody tr').all();
    logProgress(`📊 ${rows.length} lignes trouvées dans le tableau`);
    
    const shopsData = [];
    
    // Extraire chaque ligne avec les SÉLECTEURS QUI FONCTIONNENT
    for (let i = 0; i < rows.length; i++) {
      logProgress(`🔍 Extraction ligne ${i + 1}/${rows.length}...`);
      
      try {
        const row = rows[i];
        const cells = await row.locator('td').all();
        if (cells.length < 8) {
          logProgress(`⚠️ Ligne avec seulement ${cells.length} cellules, ignorée`);
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
          logProgress(`⚠️ Erreur extraction info boutique: ${error.message}`);
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
            logProgress(`📦 Produits extraits pour ${shopData.shopName}: ${shopData.totalProducts}`);
          } else {
            shopData.totalProducts = null;
          }
        } catch (error) {
          logProgress(`⚠️ Erreur extraction produits pour ${shopData.shopName}: ${error.message}`);
          shopData.totalProducts = null;
        }
        
        // 3. EXTRACTION MÉTRIQUES DE BASE (cellules 3, 4, 5) - SÉLECTEURS QUI FONCTIONNENT
        try {
          shopData.category = (await cells[3].textContent()).trim();
          shopData.monthlyVisits = (await cells[4].textContent()).trim();
          shopData.monthlyRevenue = (await cells[5].textContent()).trim();
        } catch (error) {
          logProgress(`⚠️ Erreur extraction métriques de base: ${error.message}`);
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
          logProgress(`⚠️ Erreur extraction Live Ads: ${error.message}`);
          shopData.liveAds = '';
        }

        // Ajouter les métadonnées
        shopData.scraping_status = 'table_extracted';
        shopData.last_updated = new Date().toISOString();

        // Vérifier qu'on a au moins le nom et l'URL
        if (!shopData.shopName || !shopData.shopUrl) {
          logProgress('⚠️ Données insuffisantes pour la boutique');
          continue;
        }

        logProgress(`✅ Boutique extraite: ${shopData.shopName} (${shopData.shopUrl})`);
        shopsData.push(shopData);
        
      } catch (error) {
        logProgress(`❌ Erreur extraction ligne ${i + 1}: ${error.message}`);
        continue;
      }
      
      // Pause minimale entre les extractions
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    logProgress(`\n📊 RÉSULTATS EXTRACTION:`);
    logProgress(`✅ ${shopsData.length} boutiques extraites du tableau`);
    
    // Sauvegarde immédiate en base
    logProgress('\n💾 Sauvegarde en base...');
    
    const results = {
      inserted: 0,
      skipped: 0,
      errors: 0
    };
    
    for (const shopData of shopsData) {
      try {
        // Vérifier si le shop existe déjà
        const existingShop = await shopRepo.getByUrl(shopData.shopUrl);
        if (existingShop) {
          logProgress(`⏭️ Shop déjà existant: ${shopData.shopName} - Ignoré`);
          results.skipped++;
          continue;
        }
        
        // Shop n'existe pas, on l'ajoute
        const shopId = await shopRepo.upsert(shopData);
        if (shopId) {
          results.inserted++;
          logProgress(`🆕 Nouveau shop: ${shopData.shopName} - ID: ${shopId}`);
        } else {
          results.errors++;
          logProgress(`❌ Échec upsert: ${shopData.shopName}`);
        }
      } catch (error) {
        results.errors++;
        logProgress(`❌ Erreur traitement: ${error.message}`);
      }
    }
    
    // Export debug des données
    fs.writeFileSync('export-table-working-selectors.json', JSON.stringify(shopsData, null, 2));
    
    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES:');
    logProgress('==================================================');
    logProgress(`📋 Boutiques extraites du tableau: ${shopsData.length}`);
    logProgress(`🆕 Nouvelles boutiques ajoutées: ${results.inserted}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${results.skipped}`);
    logProgress(`❌ Erreurs: ${results.errors}`);
    logProgress('✅ Extraction avec sélecteurs qui fonctionnent terminée !');
    
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
extractTableWithWorkingSelectors().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});
