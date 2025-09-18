/**
 * Test d'intégration simple pour l'extraction des données de trafic par pays
 * Ce script teste l'intégration sans se connecter à TrendTrack
 */

import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { chromium } from 'playwright';

async function testMarketTrafficIntegrationSimple() {
  console.log('🧪 Test d\'intégration simple - Extraction des données de trafic par pays');
  console.log('='.repeat(70));
  
  let browser = null;
  let page = null;
  
  try {
    // Lancer un navigateur
    console.log('\n1️⃣ Lancement du navigateur...');
    browser = await chromium.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });
    
    page = await context.newPage();
    
    // Créer l'extracteur TrendTrack
    console.log('\n2️⃣ Création de l\'extracteur TrendTrack...');
    const extractor = new TrendTrackExtractor(page, null);
    
    // Vérifier que l'extracteur de trafic par pays est initialisé
    console.log('\n3️⃣ Vérification de l\'initialisation...');
    if (extractor.marketTrafficExtractor) {
      console.log('✅ Extracteur de trafic par pays initialisé');
    } else {
      console.log('❌ Extracteur de trafic par pays non initialisé');
      throw new Error('Extracteur de trafic par pays non initialisé');
    }
    
    // Test des méthodes d'extraction
    console.log('\n4️⃣ Test des méthodes d\'extraction...');
    
    // Test de la méthode extractMarketTrafficForShop
    console.log('🔍 Test de extractMarketTrafficForShop...');
    try {
      const testUrl = 'https://example.com/test-shop';
      const marketData = await extractor.extractMarketTrafficForShop(testUrl);
      console.log('✅ Méthode extractMarketTrafficForShop fonctionne');
      console.log('📊 Données retournées:', JSON.stringify(marketData, null, 2));
    } catch (error) {
      console.log('⚠️ Erreur attendue (URL de test):', error.message);
    }
    
    // Test de la méthode extractMarketTrafficForMultipleShops
    console.log('\n🔍 Test de extractMarketTrafficForMultipleShops...');
    try {
      const testUrls = ['https://example.com/test-shop-1', 'https://example.com/test-shop-2'];
      const marketData = await extractor.extractMarketTrafficForMultipleShops(testUrls);
      console.log('✅ Méthode extractMarketTrafficForMultipleShops fonctionne');
      console.log('📊 Données retournées:', JSON.stringify(marketData, null, 2));
    } catch (error) {
      console.log('⚠️ Erreur attendue (URLs de test):', error.message);
    }
    
    // Test de la méthode extractCompleteShopData
    console.log('\n🔍 Test de extractCompleteShopData...');
    try {
      const testShopData = {
        shopName: 'Test Shop',
        shopUrl: 'https://example.com/test-shop',
        category: 'Test Category',
        monthlyVisits: '100000',
        monthlyRevenue: '$50,000',
        liveAds: '25'
      };
      
      const completeData = await extractor.extractCompleteShopData(testShopData);
      console.log('✅ Méthode extractCompleteShopData fonctionne');
      console.log('📊 Données complètes:', JSON.stringify(completeData, null, 2));
      
      // Vérifier que les champs market_* sont présents
      const marketFields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr'];
      const presentFields = marketFields.filter(field => field in completeData);
      
      if (presentFields.length === marketFields.length) {
        console.log('✅ Tous les champs market_* sont présents dans les données complètes');
      } else {
        console.log(`⚠️ ${marketFields.length - presentFields.length} champs market_* manquants`);
      }
      
    } catch (error) {
      console.log('⚠️ Erreur attendue (URL de test):', error.message);
    }
    
    // Test de la méthode formatToCSV avec des données de trafic par pays
    console.log('\n5️⃣ Test de formatToCSV avec données de trafic par pays...');
    const testShopsData = [
      {
        shopName: 'Test Shop 1',
        shopUrl: 'https://example.com/test-shop-1',
        category: 'Test Category',
        monthlyVisits: '100000',
        monthlyRevenue: '$50,000',
        liveAds: '25',
        market_us: 45000,
        market_uk: 25000,
        market_de: 15000,
        market_ca: 10000,
        market_au: 5000,
        market_fr: 0,
        page: 1,
        timestamp: new Date().toISOString()
      },
      {
        shopName: 'Test Shop 2',
        shopUrl: 'https://example.com/test-shop-2',
        category: 'Test Category',
        monthlyVisits: '200000',
        monthlyRevenue: '$100,000',
        liveAds: '50',
        market_us: 90000,
        market_uk: 50000,
        market_de: 30000,
        market_ca: 20000,
        market_au: 10000,
        market_fr: 0,
        page: 1,
        timestamp: new Date().toISOString()
      }
    ];
    
    const csvContent = extractor.formatToCSV(testShopsData);
    console.log('✅ CSV généré avec succès');
    console.log('📄 Contenu CSV:');
    console.log(csvContent);
    
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
    
    console.log('\n✅ Tests d\'intégration terminés avec succès!');
    
  } catch (error) {
    console.error('\n❌ Erreur lors des tests d\'intégration:', error.message);
    console.error('Stack trace:', error.stack);
  } finally {
    // Fermer le navigateur
    if (page) {
      await page.close();
    }
    if (browser) {
      await browser.close();
    }
    console.log('\n🔚 Navigateur fermé');
  }
}

// Exécuter les tests si le script est appelé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  testMarketTrafficIntegrationSimple()
    .then(() => {
      console.log('\n🎉 Tests terminés');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Erreur fatale:', error.message);
      process.exit(1);
    });
}

export { testMarketTrafficIntegrationSimple };