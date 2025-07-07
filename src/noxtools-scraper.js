import { WebScraper } from './scraper.js';
import { config } from './config.js';

class NoxToolsScraper extends WebScraper {
  constructor() {
    super();
    this.finalSiteUrl = null; // URL du site final après navigation depuis NoxTools
  }

  async connectToNoxTools() {
    console.log('🔑 Étape 1: Connexion à NoxTools...');
    
    try {
      await this.page.goto(config.loginUrl);
      await this.page.waitForLoadState('networkidle');
      
      console.log('📝 Remplissage du formulaire de connexion NoxTools...');
      
      // Remplir les champs de connexion NoxTools
      await this.page.fill(config.credentials.usernameSelector, config.credentials.username);
      await this.page.fill(config.credentials.passwordSelector, config.credentials.password);
      
      // Soumettre le formulaire
      await this.page.click(config.credentials.submitSelector);
      
      // Attendre la redirection après connexion
      await this.page.waitForLoadState('networkidle');
      
      // Vérifier si on est bien connecté - plus flexible avec les URLs
      const currentUrl = this.page.url();
      console.log(`🔍 URL après connexion: ${currentUrl}`);
      
      // Vérifications multiples pour valider la connexion
      const validUrlPatterns = [
        'secure/page',
        'dashboard', 
        'member',
        'semrush',
        '/secure/',
        'noxtools.com'
      ];
      
      const isValidUrl = validUrlPatterns.some(pattern => currentUrl.includes(pattern));
      const hasLoginError = await this.page.$('.error, .alert-danger, .login-error');
      
      if (isValidUrl && !hasLoginError) {
        console.log('✅ Connexion NoxTools réussie !');
        return true;
      } else if (hasLoginError) {
        const errorText = await hasLoginError.textContent();
        throw new Error(`Connexion échouée: ${errorText}`);
      } else {
        console.log(`⚠️  URL inattendue mais on continue: ${currentUrl}`);
        return true; // On continue même si l'URL est différente
      }
      
    } catch (error) {
      console.error('❌ Erreur connexion NoxTools:', error.message);
      return false;
    }
  }

    buildAnalyticsUrl(domain = null) {
    const targetDomain = domain || config.analyticsParams.domain;
    const encodedDomain = encodeURIComponent(targetDomain);
    
    const params = new URLSearchParams({
      searchType: config.analyticsParams.searchType,
      db: config.analyticsParams.db,
      q: encodedDomain
    });
    
    return `${config.baseAnalyticsUrl}?${params.toString()}`;
  }

  async navigateToFinalSite(customDomain = null) {
    console.log('🧭 Étape 2: Navigation vers le site d\'analytics...');
    
    try {
      console.log(`🔍 URL actuelle: ${this.page.url()}`);
      
      // D'abord aller sur la page intermédiaire NoxTools si nécessaire
      if (config.noxToolsPage) {
        if (!this.page.url().includes('secure/page/semrush')) {
          console.log('📍 Navigation vers la page intermédiaire NoxTools...');
          try {
            await this.page.goto(config.noxToolsPage, { 
              waitUntil: 'domcontentloaded',
              timeout: 15000 
            });
            console.log(`✅ Sur la page intermédiaire: ${this.page.url()}`);
            await this.page.waitForTimeout(2000);
          } catch (e) {
            console.log(`⚠️  Timeout page intermédiaire: ${e.message}`);
          }
        }
      }
      
      // Construire l'URL d'analytics avec le domaine cible
      const analyticsUrl = this.buildAnalyticsUrl(customDomain);
      const targetDomain = customDomain || config.analyticsParams.domain;
      
      console.log(`🎯 Navigation vers analytics pour: ${targetDomain}`);
      console.log(`� URL complète: ${analyticsUrl}`);
      
      // Naviguer directement vers l'URL d'analytics
      try {
        await this.page.goto(analyticsUrl, {
          waitUntil: 'domcontentloaded',
          timeout: 20000
        });
        
        console.log(`✅ Navigation réussie vers analytics !`);
        await this.page.waitForTimeout(3000); // Attendre le chargement des données
        
      } catch (navError) {
        console.log(`⚠️  Timeout navigation analytics: ${navError.message}`);
        console.log('🔄 On continue quand même...');
      }
      
      // Enregistrer l'URL finale
      this.finalSiteUrl = this.page.url();
      console.log(`📊 URL finale: ${this.finalSiteUrl}`);
      
      return true;
      
    } catch (error) {
      console.error('❌ Erreur navigation vers analytics:', error.message);
      return false;
    }
  }

  async waitForFinalSiteLoading() {
    console.log('⏳ Étape 3: Attente du chargement complet du site final...');
    
    try {
      // Attendre les éléments principaux du site final
      const mainSelectors = [
        config.selectors.mainContainer.selector,
        'body',
        '[data-testid]',
        '.app',
        '#app'
      ];
      
      for (const selector of mainSelectors) {
        try {
          await this.page.waitForSelector(selector, { timeout: 5000 });
          console.log(`✅ Élément trouvé: ${selector}`);
          break;
        } catch (e) {
          console.log(`⚠️  Élément non trouvé: ${selector}`);
        }
      }
      
      // Attendre que les données se chargent (ajuster selon le site)
      await this.page.waitForTimeout(3000);
      
      console.log('✅ Site final chargé !');
      return true;
      
    } catch (error) {
      console.error('❌ Erreur attente chargement:', error.message);
      return false;
    }
  }

  async scrapeFinalSiteData() {
    console.log('📊 Étape 4: Scraping des données du site final...');
    
    try {
      // Prendre une capture avant scraping
      await this.takeScreenshot(`before-scraping-${Date.now()}.png`);
      
      // Scraper selon la config
      const scrapedData = await this.scrapeData(config.selectors);
      
      // Ajouter des métadonnées
      const finalData = {
        timestamp: new Date().toISOString(),
        sourceUrl: this.finalSiteUrl,
        viaGateway: 'NoxTools',
        data: scrapedData
      };
      
      console.log('✅ Scraping terminé !');
      return finalData;
      
    } catch (error) {
      console.error('❌ Erreur scraping:', error.message);
      return null;
    }
  }

  async performCompleteWorkflow() {
    console.log('🚀 Démarrage du workflow NoxTools complet...');
    
    try {
      // Étape 1: Connexion NoxTools
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) {
        throw new Error('Impossible de se connecter à NoxTools');
      }
      
      // Étape 2: Navigation vers site final
      const navSuccess = await this.navigateToFinalSite();
      if (!navSuccess) {
        throw new Error('Impossible de naviguer vers le site final');
      }
      
      // Étape 3: Attendre chargement
      await this.waitForFinalSiteLoading();
      
      // Étape 4: Scraper les données
      const data = await this.scrapeFinalSiteData();
      
      if (data) {
        console.log('🎉 Workflow complet réussi !');
        console.log('📋 Données récupérées:');
        console.log(JSON.stringify(data, null, 2));
        
        // Prendre capture finale
        await this.takeScreenshot(`final-result-${Date.now()}.png`);
        
        return data;
      }
      
    } catch (error) {
      console.error('💥 Erreur workflow:', error.message);
      await this.takeScreenshot(`error-${Date.now()}.png`);
      return null;
    }
  }
}

// Fonction pour scraper un domaine spécifique
async function scrapeDomain(domain) {
  const scraper = new NoxToolsScraper();
  
  try {
    await scraper.init();
    console.log(`🎯 Analyse du domaine: ${domain}`);
    
    // Connexion NoxTools
    const loginSuccess = await scraper.connectToNoxTools();
    if (!loginSuccess) {
      throw new Error('Impossible de se connecter à NoxTools');
    }
    
    // Navigation vers analytics avec le domaine spécifique
    const navSuccess = await scraper.navigateToFinalSite(domain);
    if (!navSuccess) {
      throw new Error('Impossible de naviguer vers analytics');
    }
    
    // Attendre chargement et scraper
    await scraper.waitForFinalSiteLoading();
    const data = await scraper.scrapeFinalSiteData();
    
    if (data) {
      // Sauvegarder avec nom de fichier basé sur le domaine
      const fs = await import('fs/promises');
      const cleanDomain = domain.replace(/[^a-zA-Z0-9]/g, '-');
      const filename = `analytics-${cleanDomain}-${Date.now()}.json`;
      await fs.writeFile(filename, JSON.stringify(data, null, 2));
      console.log(`💾 Données sauvegardées dans: ${filename}`);
      
      return data;
    }
    
  } catch (error) {
    console.error('💥 Erreur analyse domaine:', error.message);
    return null;
  } finally {
    await scraper.close();
  }
}

// Fonction principale (utilise le domaine de config)
async function runNoxToolsWorkflow() {
  return await scrapeDomain(config.analyticsParams.domain);
}

// Fonction pour analyser plusieurs domaines
async function scrapeMultipleDomains(domains) {
  console.log(`🚀 Analyse de ${domains.length} domaines...`);
  const results = [];
  
  for (let i = 0; i < domains.length; i++) {
    const domain = domains[i];
    console.log(`\n📊 ${i + 1}/${domains.length} - Analyse de: ${domain}`);
    
    const result = await scrapeDomain(domain);
    if (result) {
      results.push({ domain, data: result });
    }
    
    // Pause entre les domaines pour éviter la surcharge
    if (i < domains.length - 1) {
      console.log('⏳ Pause de 3 secondes...');
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
  
  // Sauvegarder le rapport consolidé
  const fs = await import('fs/promises');
  const reportFilename = `multi-domain-report-${Date.now()}.json`;
  await fs.writeFile(reportFilename, JSON.stringify(results, null, 2));
  console.log(`📋 Rapport consolidé: ${reportFilename}`);
  
  return results;
}

// Export pour utilisation
export { NoxToolsScraper, runNoxToolsWorkflow, scrapeDomain, scrapeMultipleDomains };

// Exécution directe
if (import.meta.url === `file://${process.argv[1]}`) {
  runNoxToolsWorkflow();
}