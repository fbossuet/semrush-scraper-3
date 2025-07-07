import { chromium } from 'playwright';
import { config } from './config.js';

class WebScraper {
  constructor() {
    this.browser = null;
    this.page = null;
  }

  async init() {
    console.log('🚀 Initialisation du navigateur...');
    this.browser = await chromium.launch({
      headless: config.headless,
      slowMo: config.slowMo
    });
    
    this.page = await this.browser.newPage();
    
    // Configuration de la page
    await this.page.setViewportSize(config.viewport);
    await this.page.setUserAgent(config.userAgent);
  }

  async login(url, credentials) {
    console.log(`🔑 Connexion à ${url}...`);
    
    try {
      await this.page.goto(url);
      
      // Attendre que la page soit chargée
      await this.page.waitForLoadState('networkidle');
      
      // Exemple de connexion (à adapter selon le site)
      if (credentials.usernameSelector && credentials.passwordSelector) {
        await this.page.fill(credentials.usernameSelector, credentials.username);
        await this.page.fill(credentials.passwordSelector, credentials.password);
        
        if (credentials.submitSelector) {
          await this.page.click(credentials.submitSelector);
          await this.page.waitForLoadState('networkidle');
        }
      }
      
      console.log('✅ Connexion réussie !');
      return true;
    } catch (error) {
      console.error('❌ Erreur lors de la connexion:', error.message);
      return false;
    }
  }

  async navigateToInterface(targetUrl) {
    console.log(`🧭 Navigation vers l'interface: ${targetUrl}...`);
    
    try {
      await this.page.goto(targetUrl);
      await this.page.waitForLoadState('networkidle');
      
      console.log('✅ Navigation réussie !');
      return true;
    } catch (error) {
      console.error('❌ Erreur lors de la navigation:', error.message);
      return false;
    }
  }

  async scrapeData(selectors) {
    console.log('📊 Début du scraping des données...');
    
    try {
      const scrapedData = {};
      
      for (const [key, selector] of Object.entries(selectors)) {
        console.log(`🔍 Scraping: ${key}...`);
        
        if (selector.multiple) {
          // Pour récupérer plusieurs éléments
          scrapedData[key] = await this.page.$$eval(selector.selector, elements =>
            elements.map(el => selector.attribute ? el.getAttribute(selector.attribute) : el.textContent.trim())
          );
        } else {
          // Pour récupérer un seul élément
          const element = await this.page.$(selector.selector);
          if (element) {
            if (selector.attribute) {
              scrapedData[key] = await element.getAttribute(selector.attribute);
            } else {
              scrapedData[key] = await element.textContent();
            }
          } else {
            scrapedData[key] = null;
            console.log(`⚠️  Élément non trouvé pour: ${key}`);
          }
        }
      }
      
      console.log('✅ Scraping terminé !');
      return scrapedData;
    } catch (error) {
      console.error('❌ Erreur lors du scraping:', error.message);
      return null;
    }
  }

  async waitForElement(selector, timeout = 5000) {
    console.log(`⏳ Attente de l'élément: ${selector}...`);
    try {
      await this.page.waitForSelector(selector, { timeout });
      console.log('✅ Élément trouvé !');
      return true;
    } catch (error) {
      console.log(`⚠️  Élément non trouvé: ${selector}`);
      return false;
    }
  }

  async takeScreenshot(filename) {
    console.log(`📸 Capture d'écran: ${filename}...`);
    await this.page.screenshot({ path: `screenshots/${filename}` });
  }

  async close() {
    console.log('🔚 Fermeture du navigateur...');
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Fonction principale d'exécution
async function main() {
  const scraper = new WebScraper();
  
  try {
    await scraper.init();
    
    // Exemple d'utilisation - À personnaliser selon tes besoins
    const loginSuccess = await scraper.login(config.loginUrl, config.credentials);
    
    if (loginSuccess) {
      await scraper.navigateToInterface(config.targetUrl);
      
      // Attendre que les éléments soient chargés
      await scraper.waitForElement(config.selectors.mainContainer.selector);
      
      // Scraper les données
      const data = await scraper.scrapeData(config.selectors);
      
      // Afficher les résultats
      console.log('📋 Données récupérées:');
      console.log(JSON.stringify(data, null, 2));
      
      // Optionnel: sauvegarder une capture d'écran
      await scraper.takeScreenshot(`scraping-${Date.now()}.png`);
    }
    
  } catch (error) {
    console.error('💥 Erreur générale:', error.message);
  } finally {
    await scraper.close();
  }
}

// Exécution du script
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { WebScraper };