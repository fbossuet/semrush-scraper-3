/**
 * Script d'extraction UNIQUEMENT des données du tableau
 * Évite le problème de session perdue en ne naviguant pas vers les détails
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { DatabaseManager } from './src/database/database-manager.js';
import { ShopRepository } from './src/database/shop-repository.js';
import fs from 'fs';

const LOG_PROGRESS_FILE = 'logs/extract-table-only.log';

function logProgress(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PROGRESS_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log au début
fs.writeFileSync(LOG_PROGRESS_FILE, '');

async function extractTableOnly() {
  logProgress('🚀 EXTRACTION TABLEAU UNIQUEMENT - Démarrage');
  
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
    
    // Extraction des données du tableau UNIQUEMENT (sans navigation vers détails)
    logProgress('📋 Extraction des données du tableau...');
    
    // Attendre que le tableau soit chargé
    await extractor.page.waitForSelector('tbody tr', { timeout: 60000 });
    
    // Récupérer toutes les lignes du tableau
    const rows = await extractor.page.locator('tbody tr').all();
    logProgress(`📊 ${rows.length} lignes trouvées dans le tableau`);
    
    const shopsData = [];
    
    // Extraire chaque ligne SANS navigation vers les détails
    for (let i = 0; i < rows.length; i++) {
      logProgress(`🔍 Extraction ligne ${i + 1}/${rows.length}...`);
      
      try {
        const cells = await rows[i].locator('td').all();
        if (cells.length < 6) {
          logProgress('⚠️ Ligne avec seulement', cells.length, 'cellules, ignorée');
          continue;
        }

        // Extraction des données de base du tableau uniquement
        const shopData = {};
        
        // Nom de la boutique
        try {
          const nameElement = await cells[0].locator('p.text-sm.font-semibold').first();
          if (await nameElement.count() > 0) {
            shopData.shop_name = (await nameElement.textContent())?.trim();
          }
        } catch (error) {
          logProgress('⚠️ Nom de boutique non trouvé');
        }

        // URL de la boutique
        try {
          const urlElement = await cells[0].locator('a[href*="http"]').first();
          if (await urlElement.count() > 0) {
            shopData.shop_url = await urlElement.getAttribute('href');
          }
        } catch (error) {
          logProgress('⚠️ URL de boutique non trouvée');
        }

        // Catégorie
        try {
          const categoryElement = await cells[1].locator('div').first();
          if (await categoryElement.count() > 0) {
            shopData.category = (await categoryElement.textContent())?.trim();
          }
        } catch (error) {
          logProgress('⚠️ Catégorie non trouvée');
        }

        // Visites mensuelles
        try {
          const visitsElement = await cells[2].locator('p.font-bold').first();
          if (await visitsElement.count() > 0) {
            shopData.monthly_visits = extractor.parseNumber(await visitsElement.textContent());
          }
        } catch (error) {
          logProgress('⚠️ Visites mensuelles non trouvées');
        }

        // Revenus mensuels
        try {
          const revenueElement = await cells[3].locator('p.font-bold').first();
          if (await revenueElement.count() > 0) {
            shopData.monthly_revenue = extractor.parseNumber(await revenueElement.textContent());
          }
        } catch (error) {
          logProgress('⚠️ Revenus mensuels non trouvés');
        }

        // Nombre de produits
        try {
          const productsElement = await cells[4].locator('p.font-bold').first();
          if (await productsElement.count() > 0) {
            shopData.total_products = extractor.parseNumber(await productsElement.textContent());
          }
        } catch (error) {
          logProgress('⚠️ Nombre de produits non trouvé');
        }

        // Live ads 7d
        try {
          const liveAds7dElement = await cells[5].locator('p').first();
          if (await liveAds7dElement.count() > 0) {
            shopData.live_ads_7d = extractor.parseNumber(await liveAds7dElement.textContent());
          }
        } catch (error) {
          logProgress('⚠️ Live ads 7d non trouvés');
        }

        // Live ads 30d
        try {
          const liveAds30dElement = await cells[6].locator('p').first();
          if (await liveAds30dElement.count() > 0) {
            shopData.live_ads_30d = extractor.parseNumber(await liveAds30dElement.textContent());
          }
        } catch (error) {
          logProgress('⚠️ Live ads 30d non trouvés');
        }

        // Ajouter les métadonnées
        shopData.scraping_status = 'table_extracted';
        shopData.last_updated = new Date().toISOString();

        // Vérifier qu'on a au moins le nom et l'URL
        if (!shopData.shop_name || !shopData.shop_url) {
          logProgress('⚠️ Données insuffisantes pour la boutique');
          continue;
        }

        logProgress(`✅ Boutique extraite: ${shopData.shop_name} (${shopData.shop_url})`);
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
        const existingShop = await shopRepo.getByUrl(shopData.shop_url);
        if (existingShop) {
          logProgress(`⏭️ Shop déjà existant: ${shopData.shop_name} - Ignoré`);
          results.skipped++;
          continue;
        }
        
        // Shop n'existe pas, on l'ajoute
        const shopId = await shopRepo.upsert(shopData);
        if (shopId) {
          results.inserted++;
          logProgress(`🆕 Nouveau shop: ${shopData.shop_name} - ID: ${shopId}`);
        } else {
          results.errors++;
          logProgress(`❌ Échec upsert: ${shopData.shop_name}`);
        }
      } catch (error) {
        results.errors++;
        logProgress(`❌ Erreur traitement: ${error.message}`);
      }
    }
    
    // Export debug des données
    fs.writeFileSync('export-table-data.json', JSON.stringify(shopsData, null, 2));
    
    // Statistiques finales
    logProgress('\n📊 STATISTIQUES FINALES:');
    logProgress('==================================================');
    logProgress(`📋 Boutiques extraites du tableau: ${shopsData.length}`);
    logProgress(`🆕 Nouvelles boutiques ajoutées: ${results.inserted}`);
    logProgress(`⏭️ Boutiques ignorées (déjà existantes): ${results.skipped}`);
    logProgress(`❌ Erreurs: ${results.errors}`);
    logProgress('✅ Extraction tableau terminée avec succès !');
    
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
extractTableOnly().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});

