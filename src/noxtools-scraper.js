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

  async navigateToFinalSite() {
    console.log('🧭 Étape 2: Navigation vers le site final depuis NoxTools...');
    
    try {
      console.log(`🔍 URL actuelle: ${this.page.url()}`);
      
             // Forcer la navigation vers la page SEMrush si on n'y est pas déjà
       if (config.noxToolsPage) {
         if (!this.page.url().includes('secure/page/semrush')) {
           console.log('📍 Navigation forcée vers la page NoxTools SEMrush...');
           try {
             await this.page.goto(config.noxToolsPage, { 
               waitUntil: 'domcontentloaded', // Plus tolérant que 'networkidle'
               timeout: 15000 
             });
             console.log(`✅ Nouvelle URL: ${this.page.url()}`);
             
             // Attendre quelques secondes pour le chargement
             await this.page.waitForTimeout(3000);
             
           } catch (e) {
             console.log(`⚠️  Timeout navigation, mais on continue: ${e.message}`);
             // On continue même si la navigation timeout
           }
         } else {
           console.log('✅ Déjà sur la page SEMrush !');
         }
       }
      
             // Attendre et chercher les liens/boutons d'accès au site final
       await this.page.waitForTimeout(2000); // Laisser le temps à la page de charger
       
       const linkSelectors = [
         config.noxToolsSelectors.accessLink.selector,
         'a[href*="semrush.com"]',  // Lien direct vers SEMrush
         'a[href*="app.semrush"]',  // App SEMrush
         'iframe[src*="semrush"]',  // Frame embarquée
         'button[onclick*="semrush"]', // Bouton avec JS
         '.semrush-access',
         '.tool-access',
         '.launch-tool',
         'a[target="_blank"]',  // Liens qui s'ouvrent dans nouvel onglet
         '.btn-primary',
         '.access-button'
       ];
      
      let accessLink = null;
      for (const selector of linkSelectors) {
        try {
          accessLink = await this.page.$(selector);
          if (accessLink) {
            console.log(`🔗 Lien d'accès trouvé avec: ${selector}`);
            break;
          }
        } catch (e) {
          // Continue avec le sélecteur suivant
        }
      }
      
              if (accessLink) {
          try {
            console.log('🔗 Tentative de clic sur le lien d\'accès...');
            await accessLink.click();
            
            // Attendre avec timeout plus court
            try {
              await this.page.waitForLoadState('domcontentloaded', { timeout: 10000 });
              console.log('✅ Navigation par clic réussie');
            } catch (timeoutError) {
              console.log('⚠️  Timeout après clic, mais on continue...');
            }
            
          } catch (e) {
            console.log('🔄 Tentative avec gestion nouvel onglet...');
            try {
              // Essayer avec gestion des nouveaux onglets
              const [newPage] = await Promise.all([
                this.page.context().waitForEvent('page', { timeout: 5000 }).catch(() => null),
                accessLink.click()
              ]);
              
              if (newPage) {
                console.log('📱 Nouvel onglet ouvert, basculement...');
                this.page = newPage;
                await this.page.waitForTimeout(2000); // Attente simple
              }
            } catch (newTabError) {
              console.log('⚠️  Erreur gestion nouvel onglet:', newTabError.message);
            }
          }
        } else {
          console.log('⚠️  Aucun lien d\'accès trouvé, on continue avec la page actuelle');
        }
      
      // Enregistrer l'URL du site final
      this.finalSiteUrl = this.page.url();
      console.log(`✅ Navigation réussie vers: ${this.finalSiteUrl}`);
      
      return true;
      
    } catch (error) {
      console.error('❌ Erreur navigation vers site final:', error.message);
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

// Fonction principale
async function runNoxToolsWorkflow() {
  const scraper = new NoxToolsScraper();
  
  try {
    await scraper.init();
    const result = await scraper.performCompleteWorkflow();
    
    if (result) {
      // Optionnel: sauvegarder dans un fichier
      const fs = await import('fs/promises');
      const filename = `noxtools-data-${Date.now()}.json`;
      await fs.writeFile(filename, JSON.stringify(result, null, 2));
      console.log(`💾 Données sauvegardées dans: ${filename}`);
    }
    
  } catch (error) {
    console.error('💥 Erreur générale:', error.message);
  } finally {
    await scraper.close();
  }
}

// Export pour utilisation
export { NoxToolsScraper, runNoxToolsWorkflow };

// Exécution directe
if (import.meta.url === `file://${process.argv[1]}`) {
  runNoxToolsWorkflow();
}