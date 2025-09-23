// Script d'analyse HTML pour comprendre la structure TrendTrack
import { chromium } from 'playwright';

async function analyzeHTML() {
  console.log('🔍 Analyse de la structure HTML TrendTrack...');
  
  const browser = await chromium.launch({ 
    headless: true, // Mode headless pour VPS
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  
  const page = await context.newPage();
  
  try {
    const testUrl = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop-detail?url=https%3A%2F%2Fryzesuperfoods.com';
    console.log(`🔍 Navigation vers: ${testUrl}`);
    
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000); // Attendre plus longtemps
    
    // Analyser la structure HTML
    const analysis = await page.evaluate(() => {
      const results = {
        title: document.title,
        url: window.location.href,
        hasGeoSection: false,
        hasLiveAdsSection: false,
        geoElements: [],
        liveAdsElements: [],
        allTables: [],
        allFlexElements: []
      };
      
      // Chercher tous les éléments flex
      const flexElements = document.querySelectorAll('[class*="flex"]');
      results.allFlexElements = Array.from(flexElements).slice(0, 10).map(el => ({
        classes: el.className,
        text: el.textContent?.substring(0, 100),
        hasImg: !!el.querySelector('img'),
        hasFlag: !!el.querySelector('img[alt*="US"], img[alt*="GB"], img[alt*="CA"]')
      }));
      
      // Chercher tous les tableaux
      const tables = document.querySelectorAll('table, [role="table"]');
      results.allTables = Array.from(tables).map(table => ({
        tagName: table.tagName,
        role: table.getAttribute('role'),
        rows: table.querySelectorAll('tr, [role="row"]').length,
        cells: table.querySelectorAll('td, th, [role="cell"]').length
      }));
      
      // Chercher spécifiquement les éléments géographiques
      const geoSelectors = [
        '.flex.gap-2.w-full.items-center',
        '[class*="flex"][class*="gap"][class*="items-center"]',
        'img[alt*="US"], img[alt*="GB"], img[alt*="CA"]'
      ];
      
      geoSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results.hasGeoSection = true;
          results.geoElements.push({
            selector,
            count: elements.length,
            firstElement: elements[0].outerHTML.substring(0, 300)
          });
        }
      });
      
      // Chercher les éléments live ads
      const liveAdsSelectors = [
        'table tbody tr',
        '[class*="live"][class*="ads"]',
        '[class*="7d"], [class*="30d"]'
      ];
      
      liveAdsSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results.hasLiveAdsSection = true;
          results.liveAdsElements.push({
            selector,
            count: elements.length,
            firstElement: elements[0].outerHTML.substring(0, 300)
          });
        }
      });
      
      return results;
    });
    
    console.log('\n📊 ANALYSE COMPLÈTE:');
    console.log(`Title: ${analysis.title}`);
    console.log(`URL: ${analysis.url}`);
    console.log(`Géographie trouvée: ${analysis.hasGeoSection ? '✅' : '❌'}`);
    console.log(`Live ads trouvé: ${analysis.hasLiveAdsSection ? '✅' : '❌'}`);
    
    console.log('\n🌍 ÉLÉMENTS GÉOGRAPHIQUES:');
    analysis.geoElements.forEach(geo => {
      console.log(`  ${geo.selector}: ${geo.count} éléments`);
      console.log(`    ${geo.firstElement}`);
    });
    
    console.log('\n📊 ÉLÉMENTS LIVE ADS:');
    analysis.liveAdsElements.forEach(ads => {
      console.log(`  ${ads.selector}: ${ads.count} éléments`);
      console.log(`    ${ads.firstElement}`);
    });
    
    console.log('\n📋 TOUS LES TABLEAUX:');
    analysis.allTables.forEach(table => {
      console.log(`  ${table.tagName} (role: ${table.role}): ${table.rows} lignes, ${table.cells} cellules`);
    });
    
    console.log('\n🔧 ÉLÉMENTS FLEX (premiers 5):');
    analysis.allFlexElements.forEach(flex => {
      console.log(`  Classes: ${flex.classes}`);
      console.log(`  Texte: ${flex.text}`);
      console.log(`  Image: ${flex.hasImg ? '✅' : '❌'}, Drapeau: ${flex.hasFlag ? '✅' : '❌'}`);
      console.log('  ---');
    });
    
    // Pas d'attente en mode headless
    console.log('\n✅ Analyse terminée');
    
  } catch (error) {
    console.error('❌ Erreur:', error.message);
  } finally {
    await browser.close();
  }
}

analyzeHTML().catch(console.error);
