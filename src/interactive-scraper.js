import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import readline from 'readline';

// Interface pour interaction utilisateur
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function askUser(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer.toLowerCase().trim());
    });
  });
}

class InteractiveScraper extends NoxToolsScraper {
  constructor() {
    super();
  }

  async waitForManualIntervention() {
    console.log('\n🖥️  NAVIGATEUR OUVERT - MODE INTERACTIF');
    console.log('📋 Actions possibles :');
    console.log('   1. Résoudre les CAPTCHA/protections manuellement');
    console.log('   2. Vérifier que la page analytics est bien chargée');
    console.log('   3. Naviguer manuellement si besoin');
    console.log('');
    
    let ready = false;
    while (!ready) {
      const currentUrl = this.page.url();
      console.log(`🔍 URL actuelle: ${currentUrl}`);
      
      // Vérifier automatiquement s'il y a des protections
      try {
        const hasProtection = await this.page.$('.cf-browser-verification, .challenge-form, #challenge-error-text');
        if (hasProtection) {
          console.log('🛡️  ⚠️  PROTECTION DÉTECTÉE sur la page');
        } else {
          console.log('✅ Aucune protection visible');
        }
      } catch (e) {
        // Pas grave si la vérification échoue
      }
      
      const answer = await askUser('\n❓ La page est-elle prête pour le scraping ? (oui/non/refresh/quit) : ');
      
      switch (answer) {
        case 'oui':
        case 'o':
        case 'y':
        case 'yes':
          ready = true;
          console.log('✅ Parfait ! On continue avec le scraping...\n');
          break;
          
        case 'refresh':
        case 'r':
          console.log('🔄 Actualisation de la page...');
          await this.page.reload();
          await this.page.waitForTimeout(3000);
          break;
          
        case 'quit':
        case 'q':
          console.log('👋 Arrêt du script...');
          rl.close();
          await this.close();
          process.exit(0);
          break;
          
        default:
          console.log('⏳ D\'accord, prenez votre temps...');
          console.log('💡 Résolvez les protections puis tapez "oui"');
          await this.page.waitForTimeout(2000);
      }
    }
    
    return true;
  }

  async inspectPageElements() {
    console.log('\n🔍 INSPECTION DE LA PAGE');
    console.log('═══════════════════════════════════');
    
    try {
      // Vérifier le titre de la page
      const title = await this.page.title();
      console.log(`📄 Titre: ${title}`);
      
      // Vérifier l'URL
      const url = await this.page.url();
      console.log(`🌐 URL: ${url}`);
      
      // Chercher les éléments de données potentiels
      const potentialSelectors = [
        '.analytics-data',
        '.overview-stats',
        '.metrics',
        '.keyword-data',
        '.traffic-data',
        'table',
        '.data-table',
        '.chart',
        '.widget',
        '[data-value]',
        '.stat',
        '.number'
      ];
      
      console.log('\n📊 Éléments trouvés sur la page :');
      for (const selector of potentialSelectors) {
        try {
          const elements = await this.page.$$(selector);
          if (elements.length > 0) {
            console.log(`✅ ${selector} : ${elements.length} élément(s)`);
            
            // Afficher un aperçu du contenu
            try {
              const firstElement = elements[0];
              const text = await firstElement.textContent();
              const preview = text.slice(0, 100).replace(/\s+/g, ' ').trim();
              if (preview) {
                console.log(`   📝 Aperçu: "${preview}..."`);
              }
            } catch (e) {
              // Pas grave si on ne peut pas récupérer le texte
            }
          }
        } catch (e) {
          // Continue avec le sélecteur suivant
        }
      }
      
    } catch (error) {
      console.log(`❌ Erreur inspection: ${error.message}`);
    }
    
    console.log('═══════════════════════════════════\n');
  }

  async runInteractiveSession(domain = null) {
    console.log('🚀 DÉMARRAGE SESSION INTERACTIVE\n');
    
    try {
      // Étape 1: Initialisation
      await this.init();
      
      // Étape 2: Connexion
      console.log('🔑 Étape 1: Connexion à NoxTools...');
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) {
        throw new Error('Impossible de se connecter à NoxTools');
      }
      
      // Étape 3: Navigation vers analytics
      console.log('🧭 Étape 2: Navigation vers analytics...');
      const navSuccess = await this.navigateToFinalSite(domain);
      if (!navSuccess) {
        throw new Error('Impossible de naviguer vers analytics');
      }
      
      // Étape 4: Attente et intervention manuelle
      await this.waitForManualIntervention();
      
      // Étape 5: Inspection de la page
      await this.inspectPageElements();
      
      // Étape 6: Scraping avec confirmation
      const doScraping = await askUser('🤖 Lancer le scraping automatique ? (oui/non) : ');
      
      if (doScraping === 'oui' || doScraping === 'o') {
        console.log('📊 Démarrage du scraping...');
        await this.takeScreenshot(`interactive-before-scraping-${Date.now()}.png`);
        
        const data = await this.scrapeFinalSiteData();
        
        if (data) {
          console.log('\n✅ SCRAPING TERMINÉ !');
          console.log('📋 Résumé des données :');
          
          Object.entries(data.data).forEach(([key, value]) => {
            if (Array.isArray(value)) {
              console.log(`   ${key}: ${value.length} élément(s)`);
            } else if (value) {
              const preview = String(value).slice(0, 50);
              console.log(`   ${key}: "${preview}..."`);
            } else {
              console.log(`   ${key}: vide`);
            }
          });
          
          return data;
        }
      } else {
        console.log('⏸️  Scraping annulé par l\'utilisateur');
      }
      
    } catch (error) {
      console.error('💥 Erreur session interactive:', error.message);
    } finally {
      rl.close();
      await this.close();
    }
  }
}

// Fonction principale
async function runInteractiveMode() {
  const scraper = new InteractiveScraper();
  
  const targetDomain = config.analyticsParams.domain;
  console.log(`🎯 Domaine à analyser: ${targetDomain}\n`);
  
  const result = await scraper.runInteractiveSession(targetDomain);
  
  if (result) {
    console.log('\n🎉 Session terminée avec succès !');
  } else {
    console.log('\n⚠️  Session terminée sans données');
  }
}

// Export
export { InteractiveScraper, runInteractiveMode };

// Exécution directe
if (import.meta.url === `file://${process.argv[1]}`) {
  runInteractiveMode();
}