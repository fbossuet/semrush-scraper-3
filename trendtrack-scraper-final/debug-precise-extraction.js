/**
 * SCRIPT DE DEBUG PRÉCIS - EXTRACTION DU TABLEAU
 * 
 * OBJECTIF: Logger l'URL de scraping et le HTML lu
 * pour identifier pourquoi tbody tr n'est pas trouvé
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import fs from 'fs';

const LOG_FILE = 'logs/debug-precise-extraction.log';

function logDebug(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log
fs.writeFileSync(LOG_FILE, '');

async function debugPreciseExtraction() {
  logDebug('🔍 DÉBUT DEBUG PRÉCIS EXTRACTION');
  logDebug('==================================================');
  
  let scraper = null;
  let extractor = null;
  
  try {
    // 1. INITIALISATION DU SCRAPER
    logDebug('🚀 1. INITIALISATION DU SCRAPER');
    scraper = new WebScraper({
      headless: false, // Mode visible pour debug
      timeout: 60000,
      stealth: true
    });
    
    await scraper.init();
    logDebug('✅ Scraper initialisé');
    
    // 2. INITIALISATION DE L'EXTRACTOR
    logDebug('🔧 2. INITIALISATION DE L\'EXTRACTOR');
    extractor = new TrendTrackExtractor(scraper.page);
    logDebug('✅ Extractor initialisé');
    
    // 3. CONNEXION À TRENDTRACK
    logDebug('🔑 3. CONNEXION À TRENDTRACK');
    const loginSuccess = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
    if (!loginSuccess) {
      throw new Error('Échec de la connexion');
    }
    logDebug('✅ Connexion réussie');
    
    // 4. NAVIGATION VERS LA PAGE DES BOUTIQUES
    logDebug('🌐 4. NAVIGATION VERS LA PAGE DES BOUTIQUES');
    const navSuccess = await extractor.navigateToTrendingShops();
    if (!navSuccess) {
      throw new Error('Échec de la navigation');
    }
    logDebug('✅ Navigation réussie');
    
    // 5. DEBUG PRÉCIS DE LA PAGE
    logDebug('🔍 5. DEBUG PRÉCIS DE LA PAGE');
    
    // 5.1 URL actuelle
    const currentUrl = await extractor.page.url();
    logDebug(`📍 URL ACTUELLE: ${currentUrl}`);
    
    // 5.2 Titre de la page
    const pageTitle = await extractor.page.title();
    logDebug(`📄 TITRE DE LA PAGE: ${pageTitle}`);
    
    // 5.3 Taille du contenu HTML
    const pageContent = await extractor.page.content();
    logDebug(`📊 TAILLE DU CONTENU HTML: ${pageContent.length} caractères`);
    
    // 5.4 Sauvegarde du HTML complet
    logDebug('💾 5.4 SAUVEGARDE DU HTML COMPLET');
    fs.writeFileSync('debug-page-complete.html', pageContent);
    logDebug('✅ HTML complet sauvegardé: debug-page-complete.html');
    
    // 5.5 Vérification des éléments HTML
    const hasTable = await extractor.page.locator('table').count();
    const hasTbody = await extractor.page.locator('tbody').count();
    const hasTr = await extractor.page.locator('tr').count();
    const hasTbodyTr = await extractor.page.locator('tbody tr').count();
    
    logDebug(`🔍 ÉLÉMENTS TROUVÉS:`);
    logDebug(`  - table: ${hasTable}`);
    logDebug(`  - tbody: ${hasTbody}`);
    logDebug(`  - tr: ${hasTr}`);
    logDebug(`  - tbody tr: ${hasTbodyTr}`);
    
    // 5.6 Test des sélecteurs alternatifs
    const altSelectors = [
      'table tbody tr',
      '[role="table"] tbody tr',
      '.table tbody tr',
      'div[role="table"] tbody tr',
      'table tr',
      'tbody tr',
      'tr'
    ];
    
    logDebug('🔍 TEST DES SÉLECTEURS ALTERNATIFS:');
    for (const selector of altSelectors) {
      try {
        const count = await extractor.page.locator(selector).count();
        logDebug(`  - ${selector}: ${count} éléments`);
      } catch (error) {
        logDebug(`  - ${selector}: ERREUR - ${error.message}`);
      }
    }
    
    // 5.7 Test d'attente avec timeout progressif
    logDebug('⏱️ 5.7 TEST D\'ATTENTE AVEC TIMEOUT PROGRESSIF');
    const timeouts = [5000, 10000, 15000, 30000, 60000];
    
    for (const timeout of timeouts) {
      try {
        logDebug(`⏱️ Test avec timeout ${timeout}ms...`);
        await extractor.page.waitForSelector('tbody tr', { timeout });
        logDebug(`✅ Sélecteur trouvé avec timeout ${timeout}ms`);
        break;
      } catch (error) {
        logDebug(`❌ Timeout ${timeout}ms: ${error.message}`);
      }
    }
    
    // 5.8 Capture d'écran pour debug visuel
    logDebug('📸 5.8 CAPTURE D\'ÉCRAN POUR DEBUG VISUEL');
    await extractor.page.screenshot({ 
      path: 'debug-precise-page.png', 
      fullPage: true 
    });
    logDebug('✅ Capture d\'écran sauvegardée: debug-precise-page.png');
    
    // 5.9 Test d'extraction si le sélecteur est trouvé
    if (hasTbodyTr > 0) {
      logDebug('🎯 5.9 TEST D\'EXTRACTION DES DONNÉES');
      const rows = await extractor.page.locator('tbody tr').all();
      logDebug(`📊 ${rows.length} lignes trouvées pour extraction`);
      
      if (rows.length > 0) {
        // Test d'extraction de la première ligne
        const firstRow = rows[0];
        const rowHtml = await firstRow.innerHTML();
        logDebug(`🔍 HTML DE LA PREMIÈRE LIGNE (${rowHtml.length} caractères):`);
        logDebug(rowHtml.substring(0, 1000) + '...');
        
        // Sauvegarde du HTML de la première ligne
        fs.writeFileSync('debug-first-row.html', rowHtml);
        logDebug('✅ HTML de la première ligne sauvegardé: debug-first-row.html');
        
        // Test d'extraction des données
        try {
          const shopData = await extractor.extractShopDataFromTable(firstRow);
          logDebug('✅ EXTRACTION RÉUSSIE:');
          logDebug(JSON.stringify(shopData, null, 2));
        } catch (error) {
          logDebug(`❌ ERREUR EXTRACTION: ${error.message}`);
        }
      }
    }
    
    // 5.10 Test de la méthode extractTableDataOnly
    logDebug('🎯 5.10 TEST DE LA MÉTHODE extractTableDataOnly');
    try {
      const tableData = await extractor.extractTableDataOnly();
      logDebug(`✅ EXTRACTION TABLEAU RÉUSSIE: ${tableData.length} boutiques`);
      if (tableData.length > 0) {
        logDebug('📊 PREMIÈRE BOUTIQUE:');
        logDebug(JSON.stringify(tableData[0], null, 2));
      }
    } catch (error) {
      logDebug(`❌ ERREUR EXTRACTION TABLEAU: ${error.message}`);
    }
    
    logDebug('✅ DEBUG PRÉCIS TERMINÉ AVEC SUCCÈS');
    
  } catch (error) {
    logDebug(`❌ ERREUR CRITIQUE: ${error.message}`);
    logDebug(`📍 Stack trace: ${error.stack}`);
  } finally {
    // Nettoyage
    if (scraper) {
      try {
        await scraper.close();
        logDebug('🧹 Scraper fermé');
      } catch (error) {
        logDebug(`⚠️ Erreur fermeture scraper: ${error.message}`);
      }
    }
  }
}

// Lancement du debug
debugPreciseExtraction().catch(console.error);
