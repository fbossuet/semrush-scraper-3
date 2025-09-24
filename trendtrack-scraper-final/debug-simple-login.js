/**
 * SCRIPT DE DEBUG SIMPLIFIÉ - TEST DE CONNEXION
 * 
 * OBJECTIF: Tester uniquement la connexion TrendTrack
 * pour identifier le problème de stabilité
 */

import { WebScraper } from './src/scraper.js';
import fs from 'fs';

const LOG_FILE = 'logs/debug-simple-login.log';

function logDebug(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  console.log(msg);
}

// Nettoie le fichier de log
fs.writeFileSync(LOG_FILE, '');

async function debugSimpleLogin() {
  logDebug('🔍 DÉBUT DEBUG SIMPLE LOGIN');
  logDebug('==================================================');
  
  let scraper = null;
  
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
    
    // 2. NAVIGATION VERS LA PAGE DE LOGIN
    logDebug('🌐 2. NAVIGATION VERS LA PAGE DE LOGIN');
    await scraper.page.goto('https://app.trendtrack.io/en/login', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    logDebug('✅ Page de login chargée');
    
    // 3. DEBUG DE LA PAGE DE LOGIN
    logDebug('🔍 3. DEBUG DE LA PAGE DE LOGIN');
    
    // 3.1 URL actuelle
    const currentUrl = await scraper.page.url();
    logDebug(`📍 URL actuelle: ${currentUrl}`);
    
    // 3.2 Titre de la page
    const pageTitle = await scraper.page.title();
    logDebug(`📄 Titre de la page: ${pageTitle}`);
    
    // 3.3 Vérification des champs de formulaire
    const emailField = await scraper.page.locator('input[type="email"][name="email"]').count();
    const passwordField = await scraper.page.locator('input[type="password"][name="password"]').count();
    const submitButton = await scraper.page.locator('button[type="submit"]').count();
    
    logDebug(`🔍 Champs de formulaire trouvés:`);
    logDebug(`  - Email: ${emailField}`);
    logDebug(`  - Password: ${passwordField}`);
    logDebug(`  - Submit: ${submitButton}`);
    
    // 3.4 Capture d'écran de la page de login
    logDebug('📸 3.4 CAPTURE D\'ÉCRAN DE LA PAGE DE LOGIN');
    await scraper.page.screenshot({ 
      path: 'debug-login-page.png', 
      fullPage: true 
    });
    logDebug('✅ Capture d\'écran sauvegardée: debug-login-page.png');
    
    // 3.5 Sauvegarde du HTML de la page de login
    logDebug('💾 3.5 SAUVEGARDE DU HTML DE LA PAGE DE LOGIN');
    const htmlContent = await scraper.page.content();
    fs.writeFileSync('debug-login-page.html', htmlContent);
    logDebug('✅ HTML sauvegardé: debug-login-page.html');
    
    // 4. TEST DE REMPLISSAGE DU FORMULAIRE
    logDebug('📝 4. TEST DE REMPLISSAGE DU FORMULAIRE');
    
    if (emailField > 0 && passwordField > 0) {
      logDebug('✅ Champs de formulaire trouvés, test de remplissage...');
      
      // Attendre que le formulaire soit chargé
      await scraper.page.waitForSelector('input[type="email"][name="email"]', { timeout: 60000 });
      logDebug('✅ Sélecteur email trouvé');
      
      // Attendre 3 secondes
      await scraper.page.waitForTimeout(3000);
      logDebug('✅ Attente de 3 secondes terminée');
      
      // Remplir le formulaire
      await scraper.page.fill('input[type="email"][name="email"]', 'seif.alyakoob@gmail.com');
      logDebug('✅ Email rempli');
      
      await scraper.page.fill('input[type="password"][name="password"]', 'Toulouse31!');
      logDebug('✅ Password rempli');
      
      // Attendre 2 secondes
      await scraper.page.waitForTimeout(2000);
      logDebug('✅ Attente de 2 secondes terminée');
      
      // Capture d'écran après remplissage
      await scraper.page.screenshot({ 
        path: 'debug-form-filled.png', 
        fullPage: true 
      });
      logDebug('✅ Capture d\'écran après remplissage: debug-form-filled.png');
      
      // 5. TEST DE SOUMISSION DU FORMULAIRE
      logDebug('🚀 5. TEST DE SOUMISSION DU FORMULAIRE');
      
      if (submitButton > 0) {
        await scraper.page.click('button[type="submit"]');
        logDebug('✅ Bouton submit cliqué');
        
        // Attendre la redirection
        await scraper.page.waitForTimeout(5000);
        logDebug('✅ Attente de redirection terminée');
        
        // Vérifier l'URL après soumission
        const urlAfterSubmit = await scraper.page.url();
        logDebug(`📍 URL après soumission: ${urlAfterSubmit}`);
        
        // Capture d'écran après soumission
        await scraper.page.screenshot({ 
          path: 'debug-after-submit.png', 
          fullPage: true 
        });
        logDebug('✅ Capture d\'écran après soumission: debug-after-submit.png');
        
        // Vérifier si la connexion a réussi
        if (urlAfterSubmit.includes('/login')) {
          logDebug('❌ Connexion échouée - Reste sur la page de login');
        } else {
          logDebug('✅ Connexion réussie - Redirection détectée');
        }
      } else {
        logDebug('❌ Bouton submit non trouvé');
      }
    } else {
      logDebug('❌ Champs de formulaire non trouvés');
    }
    
    logDebug('✅ DEBUG SIMPLE LOGIN TERMINÉ');
    
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
debugSimpleLogin().catch(console.error);
