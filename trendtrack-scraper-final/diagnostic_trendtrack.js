#!/usr/bin/env node
/**
 * Diagnostic de la structure HTML de TrendTrack.io
 */

import { chromium } from 'playwright';

async function diagnosticTrendTrack() {
  console.log('🔍 DIAGNOSTIC DE TRENDTRACK.IO');
  console.log('📅 Date:', new Date().toISOString());
  console.log('=' .repeat(50));
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigation vers TrendTrack.io...');
    await page.goto('https://trendtrack.io/?page=1', { 
      waitUntil: 'networkidle', 
      timeout: 30000 
    });
    
    console.log('⏳ Attente du chargement...');
    await page.waitForTimeout(5000);
    
    // Analyser la structure HTML
    const analysis = await page.evaluate(() => {
      const results = {
        title: document.title,
        url: window.location.href,
        tables: [],
        rows: [],
        shopElements: [],
        errors: []
      };
      
      try {
        // Chercher toutes les tables
        const tables = document.querySelectorAll('table');
        results.tables = Array.from(tables).map((table, index) => ({
          index,
          className: table.className,
          id: table.id,
          rows: table.querySelectorAll('tr').length
        }));
        
        // Chercher toutes les lignes
        const allRows = document.querySelectorAll('tr');
        results.rows = Array.from(allRows).map((row, index) => ({
          index,
          className: row.className,
          cells: row.querySelectorAll('td').length,
          text: row.textContent.substring(0, 100)
        }));
        
        // Chercher des éléments qui pourraient contenir des boutiques
        const shopSelectors = [
          'tbody tr',
          '.shop',
          '.store',
          '.business',
          '[class*="shop"]',
          '[class*="store"]',
          '[class*="business"]'
        ];
        
        shopSelectors.forEach(selector => {
          const elements = document.querySelectorAll(selector);
          if (elements.length > 0) {
            results.shopElements.push({
              selector,
              count: elements.length,
              firstElement: {
                className: elements[0].className,
                text: elements[0].textContent.substring(0, 200)
              }
            });
          }
        });
        
        // Chercher des liens vers des boutiques
        const links = document.querySelectorAll('a[href*="http"]');
        results.links = Array.from(links).slice(0, 10).map(link => ({
          href: link.href,
          text: link.textContent.trim(),
          className: link.className
        }));
        
      } catch (error) {
        results.errors.push(error.message);
      }
      
      return results;
    });
    
    console.log('\n📊 RÉSULTATS DU DIAGNOSTIC:');
    console.log(`📄 Titre: ${analysis.title}`);
    console.log(`🌐 URL: ${analysis.url}`);
    console.log(`📋 Tables trouvées: ${analysis.tables.length}`);
    
    if (analysis.tables.length > 0) {
      console.log('\n📋 DÉTAIL DES TABLES:');
      analysis.tables.forEach(table => {
        console.log(`  Table ${table.index}: ${table.rows} lignes, classe="${table.className}"`);
      });
    }
    
    console.log(`\n📝 Lignes trouvées: ${analysis.rows.length}`);
    if (analysis.rows.length > 0) {
      console.log('\n📝 PREMIÈRES LIGNES:');
      analysis.rows.slice(0, 5).forEach(row => {
        console.log(`  Ligne ${row.index}: ${row.cells} cellules - "${row.text}"`);
      });
    }
    
    console.log(`\n🏪 ÉLÉMENTS BOUTIQUES TROUVÉS: ${analysis.shopElements.length}`);
    analysis.shopElements.forEach(element => {
      console.log(`  ${element.selector}: ${element.count} éléments`);
      console.log(`    Premier: "${element.firstElement.text}"`);
    });
    
    console.log(`\n🔗 LIENS TROUVÉS: ${analysis.links.length}`);
    analysis.links.forEach(link => {
      console.log(`  ${link.href} - "${link.text}"`);
    });
    
    if (analysis.errors.length > 0) {
      console.log('\n❌ ERREURS:');
      analysis.errors.forEach(error => {
        console.log(`  ${error}`);
      });
    }
    
    // Prendre une capture d'écran pour diagnostic
    console.log('\n📸 Capture d\'écran...');
    await page.screenshot({ path: 'trendtrack-diagnostic.png', fullPage: true });
    console.log('✅ Capture sauvegardée: trendtrack-diagnostic.png');
    
  } catch (error) {
    console.error('❌ ERREUR DIAGNOSTIC:', error);
  } finally {
    await browser.close();
    console.log('\n✅ Diagnostic terminé');
  }
}

diagnosticTrendTrack().catch(console.error);
