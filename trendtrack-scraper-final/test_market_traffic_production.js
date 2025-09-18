/**
 * Test de production pour l'extraction des données de trafic par pays
 * Ce script teste l'extraction avec de vraies données TrendTrack
 */

import { TrendTrackScraper } from './src/trendtrack-scraper.js';
import fs from 'fs';

async function testMarketTrafficProduction() {
  console.log('🧪 Test de production - Extraction des données de trafic par pays');
  console.log('='.repeat(70));
  
  const scraper = new TrendTrackScraper();
  
  try {
    // Initialiser le scraper
    console.log('\n1️⃣ Initialisation du scraper...');
    const initSuccess = await scraper.init();
    if (!initSuccess) {
      throw new Error('Échec de l\'initialisation du scraper');
    }
    
    // Se connecter à TrendTrack
    console.log('\n2️⃣ Connexion à TrendTrack...');
    const loginSuccess = await scraper.login(
      process.env.TRENDTRACK_EMAIL || 'votre-email@example.com',
      process.env.TRENDTRACK_PASSWORD || 'votre-mot-de-passe'
    );
    if (!loginSuccess) {
      throw new Error('Échec de la connexion à TrendTrack');
    }
    
    // Naviguer vers les boutiques tendances
    console.log('\n3️⃣ Navigation vers les boutiques tendances...');
    const navSuccess = await scraper.navigateToTrendingShops();
    if (!navSuccess) {
      throw new Error('Échec de la navigation vers les boutiques tendances');
    }
    
    // Test 1: Scraping simple (sans données de trafic par pays)
    console.log('\n4️⃣ Test 1: Scraping simple (sans données de trafic par pays)...');
    const simpleData = await scraper.scrapeMultiplePages(1, false);
    console.log(`✅ Scraping simple: ${simpleData.length} boutiques extraites`);
    
    if (simpleData.length > 0) {
      console.log('📊 Exemple de données simples:');
      console.log(JSON.stringify(simpleData[0], null, 2));
      
      // Test 2: Extraction des données de trafic par pays pour la première boutique
      console.log('\n5️⃣ Test 2: Extraction des données de trafic par pays...');
      const firstShop = simpleData[0];
      if (firstShop && firstShop.shopUrl) {
        console.log(`🔍 Test sur la boutique: ${firstShop.shopName}`);
        console.log(`🌐 URL: ${firstShop.shopUrl}`);
        
        try {
          const marketData = await scraper.extractor.extractMarketTrafficForShop(firstShop.shopUrl);
          console.log('✅ Données de trafic par pays extraites:');
          console.log(JSON.stringify(marketData, null, 2));
          
          // Vérifier que les champs market_* sont présents
          const marketFields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr'];
          const presentFields = marketFields.filter(field => field in marketData);
          
          if (presentFields.length === marketFields.length) {
            console.log('✅ Tous les champs market_* sont présents');
          } else {
            console.log(`⚠️ Champs manquants: ${marketFields.filter(f => !presentFields.includes(f)).join(', ')}`);
          }
          
          // Vérifier les valeurs
          const nonNullValues = marketFields.filter(field => marketData[field] !== null && marketData[field] !== undefined);
          console.log(`📊 Champs avec des valeurs: ${nonNullValues.length}/${marketFields.length}`);
          
          if (nonNullValues.length > 0) {
            console.log('🎉 Données de trafic par pays trouvées!');
            nonNullValues.forEach(field => {
              console.log(`  - ${field}: ${marketData[field]}`);
            });
          } else {
            console.log('⚠️ Aucune donnée de trafic par pays trouvée (valeurs NULL)');
          }
          
        } catch (error) {
          console.error('❌ Erreur lors de l\'extraction des données de trafic:', error.message);
        }
      } else {
        console.log('⚠️ Aucune boutique trouvée pour le test');
      }
    } else {
      console.log('⚠️ Aucune donnée extraite');
    }
    
    // Test 3: Sauvegarde des données en CSV
    console.log('\n6️⃣ Test 3: Sauvegarde des données en CSV...');
    if (simpleData.length > 0) {
      const csvContent = scraper.extractor.formatToCSV(simpleData);
      const csvPath = './test_market_traffic_production.csv';
      fs.writeFileSync(csvPath, csvContent);
      console.log(`✅ Données sauvegardées dans: ${csvPath}`);
      
      // Vérifier que le CSV contient les colonnes market_*
      const csvLines = csvContent.split('\n');
      const headerLine = csvLines[0];
      const marketColumns = ['Market US', 'Market UK', 'Market DE', 'Market CA', 'Market AU', 'Market FR'];
      const presentColumns = marketColumns.filter(column => headerLine.includes(column));
      
      if (presentColumns.length === marketColumns.length) {
        console.log('✅ Toutes les colonnes market_* sont présentes dans le CSV');
      } else {
        console.log(`⚠️ ${marketColumns.length - presentColumns.length} colonnes market_* manquantes dans le CSV`);
      }
    }
    
    console.log('\n✅ Tests de production terminés avec succès!');
    
  } catch (error) {
    console.error('\n❌ Erreur lors des tests de production:', error.message);
    console.error('Stack trace:', error.stack);
  } finally {
    // Fermer le scraper
    console.log('\n7️⃣ Fermeture du scraper...');
    await scraper.close();
  }
}

// Exécuter les tests si le script est appelé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  testMarketTrafficProduction()
    .then(() => {
      console.log('\n🎉 Tests terminés');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Erreur fatale:', error.message);
      process.exit(1);
    });
}

export { testMarketTrafficProduction };

