/**
 * Script de debug pour identifier pourquoi les UUIDs ne sont pas extraits
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';

async function debugUuidExtraction() {
  console.log('🔍 DEBUG: Démarrage de l\'extraction des UUIDs...');
  
  const scraper = new WebScraper();
  const extractor = new TrendTrackExtractor(scraper.page);
  
  try {
    // Connexion
    console.log('🔐 Connexion à TrendTrack...');
    const loginSuccess = await extractor.login();
    if (!loginSuccess) {
      console.log('❌ Échec de la connexion');
      return;
    }
    
    // Navigation vers la première page
    console.log('📄 Navigation vers la page 1...');
    const navSuccess = await extractor.navigateToTrendingShops(1);
    if (!navSuccess) {
      console.log('❌ Échec de la navigation');
      return;
    }
    
    // Attendre le tableau
    await extractor.page.waitForSelector('tbody tr', { timeout: 30000 });
    
    // Récupérer les 3 premières lignes
    const rows = await extractor.page.locator('tbody tr').all();
    console.log(`📊 ${rows.length} lignes trouvées`);
    
    for (let i = 0; i < Math.min(3, rows.length); i++) {
      console.log(`\n🔍 === LIGNE ${i + 1} ===`);
      
      const row = rows[i];
      
      // 1. Vérifier l'attribut id
      const trId = await row.getAttribute('id');
      console.log(`📋 tr#id: "${trId}"`);
      
      // 2. Vérifier les attributs data-*
      const dataAttrs = await row.evaluate(el => {
        const attrs = {};
        for (let attr of el.attributes) {
          if (attr.name.startsWith('data-')) {
            attrs[attr.name] = attr.value;
          }
        }
        return attrs;
      });
      console.log(`📋 data-* attributes:`, dataAttrs);
      
      // 3. Vérifier le HTML complet de la ligne
      const rowHtml = await row.evaluate(el => el.outerHTML);
      console.log(`📋 HTML (${rowHtml.length} chars): ${rowHtml.substring(0, 500)}...`);
      
      // 4. Chercher tous les UUIDs dans le HTML
      const uuidMatches = rowHtml.match(/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g);
      console.log(`🎯 UUIDs trouvés:`, uuidMatches);
      
      // 5. Vérifier les liens href
      const hrefs = await row.evaluate(el => {
        const links = Array.from(el.querySelectorAll('a[href]'));
        return links.map(a => a.getAttribute('href'));
      });
      console.log(`🔗 hrefs trouvés:`, hrefs);
    }
    
  } catch (error) {
    console.error('❌ Erreur:', error);
  } finally {
    await scraper.close();
  }
}

debugUuidExtraction();