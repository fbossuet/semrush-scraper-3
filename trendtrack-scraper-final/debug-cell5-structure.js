/**
 * Script de debug spécifique pour analyser la structure de la 5e cellule
 * et trouver le bon sélecteur pour les visites mensuelles
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';

async function debugCell5Structure() {
  console.log('🔍 DÉBUT DEBUG STRUCTURE CELLULE 5');
  console.log('==================================================');
  
  const scraper = new WebScraper();
  const extractor = new TrendTrackExtractor();
  
  try {
    // 1. Initialisation
    console.log('🚀 1. INITIALISATION DU SCRAPER');
    await scraper.init();
    console.log('✅ Scraper initialisé');
    
    // 2. Connexion TrendTrack
    console.log('🔑 2. CONNEXION À TRENDTRACK');
    const loginSuccess = await extractor.login(scraper.page, {
      email: 'seif.alyakoob@gmail.com',
      password: 'Toulouse31!'
    });
    
    if (!loginSuccess) {
      throw new Error('Échec de la connexion TrendTrack');
    }
    console.log('✅ Connexion réussie');
    
    // 3. Navigation vers la page des boutiques
    console.log('🌐 3. NAVIGATION VERS LA PAGE DES BOUTIQUES');
    await scraper.page.goto('https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops?include=true&tab=websites&minTraffic=500000&languages=en&currencies=USD&creationCountry=US&orderBy=liveAds', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    
    await scraper.page.waitForTimeout(3000);
    console.log('✅ Navigation réussie');
    
    // 4. Attendre le tableau
    console.log('📊 4. ATTENTE DU TABLEAU');
    await scraper.page.waitForSelector('tbody tr', { timeout: 15000 });
    console.log('✅ Tableau trouvé');
    
    // 5. Analyser la première ligne
    console.log('🔍 5. ANALYSE DE LA PREMIÈRE LIGNE');
    const firstRow = await scraper.page.locator('tbody tr').first();
    const cells = await firstRow.locator('td').all();
    
    console.log(`📊 Nombre de cellules trouvées: ${cells.length}`);
    
    // 6. Analyser chaque cellule
    for (let i = 0; i < cells.length; i++) {
      console.log(`\n🔍 CELLULE ${i + 1}:`);
      
      try {
        const cellHTML = await cells[i].innerHTML();
        const cellText = await cells[i].textContent();
        
        console.log(`📄 Texte: "${cellText?.trim()}"`);
        console.log(`📏 Taille HTML: ${cellHTML.length} caractères`);
        
        // Analyser la 5e cellule en détail
        if (i === 4) {
          console.log(`\n🎯 ANALYSE DÉTAILLÉE DE LA 5E CELLULE (VISITES):`);
          console.log(`📄 HTML complet:`);
          console.log(cellHTML);
          
          // Tester différents sélecteurs
          console.log(`\n🔍 TEST DES SÉLECTEURS:`);
          
          const selectors = [
            'p.font-bold',
            'div p.font-bold',
            'div:first-child p.font-bold',
            'div div p.font-bold',
            '.font-bold',
            'p',
            'div p',
            'div div p'
          ];
          
          for (const selector of selectors) {
            try {
              const elements = await cells[i].locator(selector).all();
              console.log(`  - "${selector}": ${elements.length} éléments`);
              
              for (let j = 0; j < elements.length; j++) {
                const text = await elements[j].textContent();
                console.log(`    [${j}] "${text?.trim()}"`);
              }
            } catch (error) {
              console.log(`  - "${selector}": Erreur - ${error.message}`);
            }
          }
        }
        
      } catch (error) {
        console.log(`❌ Erreur cellule ${i + 1}: ${error.message}`);
      }
    }
    
    console.log('\n✅ DEBUG TERMINÉ AVEC SUCCÈS');
    
  } catch (error) {
    console.error('❌ Erreur:', error.message);
  } finally {
    await scraper.close();
    console.log('🧹 Scraper fermé');
  }
}

// Lancement du script
debugCell5Structure().catch(console.error);
