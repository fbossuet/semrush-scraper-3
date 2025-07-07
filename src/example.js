import { WebScraper } from './scraper.js';

// Configuration personnalisée pour un site spécifique
const customConfig = {
  headless: false,
  slowMo: 200,
  viewport: { width: 1920, height: 1080 },
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  
  // Remplace ces URLs par celles de ton site cible
  loginUrl: 'https://monsite.com/login',
  targetUrl: 'https://monsite.com/data-page',
  
  credentials: {
    username: 'mon_username',
    password: 'mon_password',
    usernameSelector: 'input[name="email"]', // Adapte ces sélecteurs
    passwordSelector: 'input[name="password"]',
    submitSelector: 'button[type="submit"]'
  },
  
  selectors: {
    // Personnalise ces sélecteurs selon ton site
    mainContainer: {
      selector: '.data-container',
      multiple: false
    },
    productNames: {
      selector: '.product-name',
      multiple: true
    },
    prices: {
      selector: '.price',
      multiple: true
    },
    links: {
      selector: '.product-link',
      attribute: 'href',
      multiple: true
    }
  }
};

async function runCustomScraper() {
  const scraper = new WebScraper();
  
  try {
    // Initialiser avec la configuration personnalisée
    await scraper.init();
    
    // Étape 1: Se connecter
    console.log('🔑 Étape 1: Connexion...');
    const loginSuccess = await scraper.login(customConfig.loginUrl, customConfig.credentials);
    
    if (!loginSuccess) {
      throw new Error('Échec de la connexion');
    }
    
    // Étape 2: Naviguer vers l'interface cible
    console.log('🧭 Étape 2: Navigation...');
    await scraper.navigateToInterface(customConfig.targetUrl);
    
    // Étape 3: Attendre le chargement des données
    console.log('⏳ Étape 3: Attente du chargement...');
    await scraper.waitForElement(customConfig.selectors.mainContainer.selector);
    
    // Étape 4: Scraper les données
    console.log('📊 Étape 4: Extraction des données...');
    const data = await scraper.scrapeData(customConfig.selectors);
    
    // Étape 5: Traitement des données
    console.log('✨ Données extraites:');
    console.log(JSON.stringify(data, null, 2));
    
    // Optionnel: Sauvegarder les données dans un fichier
    // const fs = await import('fs/promises');
    // await fs.writeFile(`data-${Date.now()}.json`, JSON.stringify(data, null, 2));
    
    // Prendre une capture d'écran finale
    await scraper.takeScreenshot(`final-${Date.now()}.png`);
    
  } catch (error) {
    console.error('💥 Erreur:', error.message);
  } finally {
    await scraper.close();
  }
}

// Exemple avec navigation complexe
async function advancedScrapingExample() {
  const scraper = new WebScraper();
  
  try {
    await scraper.init();
    
    // Connexion
    await scraper.login(customConfig.loginUrl, customConfig.credentials);
    
    // Navigation multi-étapes
    console.log('🚀 Navigation avancée...');
    
    // Aller à la première page
    await scraper.navigateToInterface('https://monsite.com/dashboard');
    
    // Cliquer sur un menu ou bouton
    await scraper.page.click('.menu-item[data-target="data"]');
    await scraper.page.waitForLoadState('networkidle');
    
    // Naviguer vers une sous-page
    await scraper.page.click('.sub-menu-data');
    await scraper.waitForElement('.data-table');
    
    // Scraper avec pagination
    let allData = [];
    let pageNumber = 1;
    
    while (await scraper.page.$('.next-page:not(.disabled)')) {
      console.log(`📄 Scraping page ${pageNumber}...`);
      
      const pageData = await scraper.scrapeData({
        items: {
          selector: '.data-row',
          multiple: true
        }
      });
      
      allData.push(...(pageData.items || []));
      
      // Aller à la page suivante
      await scraper.page.click('.next-page');
      await scraper.page.waitForLoadState('networkidle');
      pageNumber++;
    }
    
    console.log(`📊 Total des données récupérées: ${allData.length} éléments`);
    
  } catch (error) {
    console.error('💥 Erreur:', error.message);
  } finally {
    await scraper.close();
  }
}

// Exporter les fonctions pour utilisation
export { runCustomScraper, advancedScrapingExample };

// Exécuter l'exemple si le fichier est lancé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  runCustomScraper();
}