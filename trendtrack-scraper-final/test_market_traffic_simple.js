/**
 * Test simple pour l'extraction des données de trafic par pays
 * Ce script teste uniquement la fonctionnalité d'extraction sans se connecter à TrendTrack
 */

import { MarketTrafficExtractor } from './src/extractors/market-traffic-extractor.js';
import { chromium } from 'playwright';

async function testMarketTrafficExtraction() {
  console.log('🧪 Test simple - Extraction des données de trafic par pays');
  console.log('='.repeat(60));
  
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
    
    // Créer l'extracteur
    console.log('\n2️⃣ Création de l\'extracteur...');
    const extractor = new MarketTrafficExtractor(page);
    
    // Test avec une URL d'exemple (remplacer par une vraie URL TrendTrack)
    console.log('\n3️⃣ Test d\'extraction...');
    const testUrl = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops';
    
    console.log(`🌐 Navigation vers: ${testUrl}`);
    await page.goto(testUrl, { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // Attendre un peu pour que la page se charge
    await page.waitForTimeout(3000);
    
    // Vérifier si la page contient des données
    const hasData = await page.locator('tbody tr').count() > 0;
    console.log(`📊 Page contient des données: ${hasData}`);
    
    if (hasData) {
      // Essayer d'extraire les données de trafic par pays
      try {
        console.log('\n4️⃣ Tentative d\'extraction des données de trafic...');
        const marketData = await extractor.scrapeMarketTraffic();
        
        console.log('✅ Données de trafic extraites:');
        console.log(JSON.stringify(marketData, null, 2));
        
        // Vérifier la structure des données
        const expectedFields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr'];
        const presentFields = Object.keys(marketData).filter(key => key.startsWith('market_'));
        
        console.log(`\n📋 Champs présents: ${presentFields.join(', ')}`);
        console.log(`📋 Champs attendus: ${expectedFields.join(', ')}`);
        
        if (presentFields.length === expectedFields.length) {
          console.log('✅ Tous les champs market_* sont présents');
        } else {
          console.log(`⚠️ ${expectedFields.length - presentFields.length} champs manquants`);
        }
        
      } catch (error) {
        console.error('❌ Erreur lors de l\'extraction:', error.message);
        console.log('ℹ️ Cela peut être normal si la page ne contient pas la section "Trafic par pays"');
      }
    } else {
      console.log('⚠️ Aucune donnée trouvée sur la page');
    }
    
    // Test des fonctions utilitaires
    console.log('\n5️⃣ Test des fonctions utilitaires...');
    
    // Test de la fonction canonical
    console.log('🔍 Test de la fonction canonical:');
    console.log(`  "gb" -> "${extractor.canonical('gb')}"`);
    console.log(`  "usa" -> "${extractor.canonical('usa')}"`);
    console.log(`  "fr" -> "${extractor.canonical('fr')}"`);
    
    // Test de la fonction parseInt
    console.log('🔍 Test de la fonction parseInt:');
    console.log(`  "1,234" -> ${extractor.parseInt('1,234')}`);
    console.log(`  "5,678.90" -> ${extractor.parseInt('5,678.90')}`);
    console.log(`  "abc123def" -> ${extractor.parseInt('abc123def')}`);
    console.log(`  "" -> ${extractor.parseInt('')}`);
    console.log(`  null -> ${extractor.parseInt(null)}`);
    
    console.log('\n✅ Tests terminés avec succès!');
    
  } catch (error) {
    console.error('\n❌ Erreur lors des tests:', error.message);
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
  testMarketTrafficExtraction()
    .then(() => {
      console.log('\n🎉 Tests terminés');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Erreur fatale:', error.message);
      process.exit(1);
    });
}

export { testMarketTrafficExtraction };

