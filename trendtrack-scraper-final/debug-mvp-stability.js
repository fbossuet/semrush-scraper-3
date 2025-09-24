/**
 * SCRIPT DE DEBUG PRÉCIS - PROBLÈME DE STABILITÉ MVP
 * 
 * OBJECTIF: Identifier précisément pourquoi le scraper MVP échoue
 * sur le sélecteur 'tbody tr' alors que le scraper classique fonctionne
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import fs from 'fs';

const LOG_FILE = 'logs/debug-mvp-stability.log';

function logDebug(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log
fs.writeFileSync(LOG_FILE, '');

async function debugMVPStability() {
  logDebug('🔍 DÉBUT DEBUG STABILITÉ MVP');
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
    
    // 2. VÉRIFICATION DE LA PAGE
    logDebug('🔄 2. VÉRIFICATION DE LA PAGE');
    if (!scraper.page) {
      throw new Error('Page non créée lors de l\'initialisation');
    }
    logDebug('✅ Page disponible');
    
    // 3. INITIALISATION DE L'EXTRACTOR
    logDebug('🔧 3. INITIALISATION DE L\'EXTRACTOR');
    extractor = new TrendTrackExtractor(scraper.page);
    logDebug('✅ Extractor initialisé');
    
    // 4. CONNEXION À TRENDTRACK
    logDebug('🔑 4. CONNEXION À TRENDTRACK');
    const loginSuccess = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
    if (!loginSuccess) {
      throw new Error('Échec de la connexion');
    }
    logDebug('✅ Connexion réussie');
    
    // 5. NAVIGATION VERS LA PAGE DES BOUTIQUES
    logDebug('🌐 5. NAVIGATION VERS LA PAGE DES BOUTIQUES');
    const navSuccess = await extractor.navigateToTrendingShops();
    if (!navSuccess) {
      throw new Error('Échec de la navigation');
    }
    logDebug('✅ Navigation réussie');
    
    // 6. DEBUG PRÉCIS DE LA PAGE
    logDebug('🔍 6. DEBUG PRÉCIS DE LA PAGE');
    
    // 6.1 URL actuelle
    const currentUrl = await extractor.page.url();
    logDebug(`📍 URL actuelle: ${currentUrl}`);
    
    // 6.2 Titre de la page
    const pageTitle = await extractor.page.title();
    logDebug(`📄 Titre de la page: ${pageTitle}`);
    
    // 6.3 Taille du contenu
    const pageContent = await extractor.page.content();
    logDebug(`📊 Taille du contenu: ${pageContent.length} caractères`);
    
    // 6.4 Vérification des éléments HTML
    const hasTable = await extractor.page.locator('table').count();
    const hasTbody = await extractor.page.locator('tbody').count();
    const hasTr = await extractor.page.locator('tr').count();
    const hasTbodyTr = await extractor.page.locator('tbody tr').count();
    
    logDebug(`🔍 Éléments trouvés:`);
    logDebug(`  - table: ${hasTable}`);
    logDebug(`  - tbody: ${hasTbody}`);
    logDebug(`  - tr: ${hasTr}`);
    logDebug(`  - tbody tr: ${hasTbodyTr}`);
    
    // 6.5 Vérification des sélecteurs alternatifs
    const altSelectors = [
      'table tbody tr',
      '[role="table"] tbody tr',
      '.table tbody tr',
      'div[role="table"] tbody tr',
      'table tr',
      'tbody tr',
      'tr'
    ];
    
    logDebug('🔍 Test des sélecteurs alternatifs:');
    for (const selector of altSelectors) {
      try {
        const count = await extractor.page.locator(selector).count();
        logDebug(`  - ${selector}: ${count} éléments`);
      } catch (error) {
        logDebug(`  - ${selector}: ERREUR - ${error.message}`);
      }
    }
    
    // 6.6 Attente avec timeout progressif
    logDebug('⏱️ 6.6 TEST D\'ATTENTE AVEC TIMEOUT PROGRESSIF');
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
    
    // 6.7 Capture d'écran pour debug visuel
    logDebug('📸 6.7 CAPTURE D\'ÉCRAN POUR DEBUG VISUEL');
    await extractor.page.screenshot({ 
      path: 'debug-mvp-page.png', 
      fullPage: true 
    });
    logDebug('✅ Capture d\'écran sauvegardée: debug-mvp-page.png');
    
    // 6.8 Sauvegarde du HTML pour analyse
    logDebug('💾 6.8 SAUVEGARDE DU HTML POUR ANALYSE');
    const htmlContent = await extractor.page.content();
    fs.writeFileSync('debug-mvp-page.html', htmlContent);
    logDebug('✅ HTML sauvegardé: debug-mvp-page.html');
    
    // 6.9 Test d'extraction si le sélecteur est trouvé
    if (hasTbodyTr > 0) {
      logDebug('🎯 6.9 TEST D\'EXTRACTION DES DONNÉES');
      const rows = await extractor.page.locator('tbody tr').all();
      logDebug(`📊 ${rows.length} lignes trouvées pour extraction`);
      
      if (rows.length > 0) {
        // Test d'extraction de la première ligne
        const firstRow = rows[0];
        const rowHtml = await firstRow.innerHTML();
        logDebug(`🔍 HTML de la première ligne (${rowHtml.length} caractères):`);
        logDebug(rowHtml.substring(0, 500) + '...');
        
        // Test d'extraction des données
        try {
          const shopData = await extractor.extractShopDataFromTable(firstRow);
          logDebug('✅ Extraction réussie:');
          logDebug(JSON.stringify(shopData, null, 2));
        } catch (error) {
          logDebug(`❌ Erreur extraction: ${error.message}`);
        }
      }
    }
    
    logDebug('✅ DEBUG TERMINÉ AVEC SUCCÈS');
    
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
debugMVPStability().catch(console.error);
