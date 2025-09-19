/**
 * Test du système de sauvegarde incrémentale par lots
 */

import { TrendTrackScraperIncremental } from './trendtrack-scraper-final/src/trendtrack-scraper-incremental.js';

async function testIncrementalSaving() {
  console.log('=== TEST SYSTÈME DE SAUVEGARDE INCÉMENTALE ===');
  
  const scraper = new TrendTrackScraperIncremental(3, 10000); // Batch de 3, flush toutes les 10s
  
  try {
    // Initialiser le scraper
    console.log('\n1. Initialisation du scraper...');
    const initSuccess = await scraper.init();
      throw new Error('Échec de l initialisation du scraper');
    }
    
    // Se connecter à TrendTrack
    console.log('\n2. Connexion à TrendTrack...');
    const loginSuccess = await scraper.login(
      process.env.TRENDTRACK_EMAIL || 'votre-email@example.com',
      process.env.TRENDTRACK_PASSWORD || 'votre-mot-de-passe'
    );
      throw new Error('Échec de la connexion à TrendTrack');
    }
    
    // Naviguer vers les boutiques tendances
    console.log('\n3. Navigation vers les boutiques tendances...');
    const navSuccess = await scraper.navigateToTrendingShops();
      throw new Error('Échec de la navigation vers les boutiques tendances');
    }
    
    // Test de scraping avec sauvegarde incrémentale
    console.log('\n4. Test de scraping avec sauvegarde incrémentale...');
    const totalSaved = await scraper.scrapeMultiplePagesWithIncrementalSave(1, false);
    
    console.log('\n✅ Test terminé avec succès!');
    console.log('Boutiques sauvegardées:', totalSaved);
    
    // Afficher les stats finales
    const finalStats = scraper.getBatchStats();
    console.log('\n📊 Statistiques finales:', finalStats);
    
  } catch (error) {
    console.error('\n❌ Erreur lors du test:', error.message);
    console.error('Stack trace:', error.stack);
  } finally {
    // Fermer le scraper
    console.log('\n5. Fermeture du scraper...');
    await scraper.close();
  }
}

// Exécuter le test si le script est appelé directement
if (import.meta.url === ) {
  testIncrementalSaving()
    .then(() => {
      console.log('\n🎉 Test terminé');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Erreur fatale:', error.message);
      process.exit(1);
    });
}

export { testIncrementalSaving };
