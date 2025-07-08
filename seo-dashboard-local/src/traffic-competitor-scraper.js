import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import fs from 'fs';

class TrafficCompetitorScraper extends NoxToolsScraper {
  
  constructor() {
    super();
    this.competitorData = [];
  }

  async navigateToTrafficOverview() {
    console.log('🚗 Navigation vers Traffic Overview...');
    
    try {
      const trafficUrl = 'https://server1.noxtools.com/analytics/traffic/traffic-overview/';
      console.log(`🎯 URL Traffic: ${trafficUrl}`);
      
      await this.page.goto(trafficUrl, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      console.log('✅ Page Traffic Overview chargée !');
      
      // Attendre le chargement de la page
      await this.page.waitForTimeout(5000);
      
      return true;
      
    } catch (error) {
      console.error('❌ Erreur navigation traffic:', error.message);
      return false;
    }
  }

  async addCompetitor(domain) {
    console.log(`➕ Ajout du concurrent: ${domain}`);
    
    try {
      // 1. Chercher et cliquer sur le bouton bleu avec +
      console.log('🔍 Recherche du bouton + ...');
      
      const addButtonSelectors = [
        'button[class*="add"]',
        'button[title*="add"]',
        'button[aria-label*="add"]',
        '.add-competitor',
        '.add-btn',
        'button.btn-primary',
        '[data-action="add"]',
        '.btn-add',
        '.add-button'
      ];
      
      let addButton = null;
      for (const selector of addButtonSelectors) {
        try {
          addButton = await this.page.$(selector);
          if (addButton) {
            console.log(`✅ Bouton + trouvé avec: ${selector}`);
            break;
          }
        } catch (e) {}
      }
      
      if (!addButton) {
        // Recherche plus large
        console.log('🔍 Recherche élargie du bouton +...');
        const allButtons = await this.page.$$('button');
        
        for (const button of allButtons) {
          const text = await button.textContent();
          const className = await button.getAttribute('class');
          
          if (text?.includes('+') || className?.includes('add') || className?.includes('plus')) {
            addButton = button;
            console.log(`✅ Bouton + trouvé par texte/classe: "${text}" / "${className}"`);
            break;
          }
        }
      }
      
      if (!addButton) {
        throw new Error('Bouton + non trouvé');
      }
      
      // 2. Cliquer sur le bouton +
      console.log('👆 Clic sur le bouton +...');
      await addButton.click();
      await this.page.waitForTimeout(2000);
      
      // 3. Chercher le champ "competitor"
      console.log('🔍 Recherche du champ competitor...');
      
      const inputSelectors = [
        'input[placeholder*="competitor"]',
        'input[name*="competitor"]',
        'input[id*="competitor"]',
        'input[class*="competitor"]',
        'input[type="text"]:last-of-type',
        '.competitor-input',
        '[data-field="competitor"]'
      ];
      
      let competitorInput = null;
      for (const selector of inputSelectors) {
        try {
          competitorInput = await this.page.$(selector);
          if (competitorInput) {
            console.log(`✅ Champ competitor trouvé: ${selector}`);
            break;
          }
        } catch (e) {}
      }
      
      if (!competitorInput) {
        // Chercher le dernier input text ajouté
        const allInputs = await this.page.$$('input[type="text"]');
        if (allInputs.length > 0) {
          competitorInput = allInputs[allInputs.length - 1];
          console.log('✅ Utilisation du dernier input text');
        }
      }
      
      if (!competitorInput) {
        throw new Error('Champ competitor non trouvé');
      }
      
      // 4. Saisir le domaine
      console.log(`⌨️ Saisie du domaine: ${domain}`);
      await competitorInput.click();
      await competitorInput.fill('');
      await competitorInput.type(domain, { delay: 100 });
      await this.page.waitForTimeout(1000);
      
      // 5. Chercher et cliquer sur la coche verte
      console.log('✅ Recherche de la coche verte...');
      
      const validateSelectors = [
        'button[class*="check"]',
        'button[class*="valid"]',
        'button[class*="confirm"]',
        '.btn-success',
        '.validate-btn',
        'button[title*="validate"]',
        'button[title*="confirm"]',
        '[data-action="validate"]',
        '.fa-check',
        '.check-button',
        '.confirm-btn'
      ];
      
      let validateButton = null;
      for (const selector of validateSelectors) {
        try {
          validateButton = await this.page.$(selector);
          if (validateButton) {
            console.log(`✅ Coche verte trouvée: ${selector}`);
            break;
          }
        } catch (e) {}
      }
      
      if (!validateButton) {
        // Recherche par couleur/style
        const allButtons = await this.page.$$('button');
        for (const button of allButtons) {
          const className = await button.getAttribute('class');
          const style = await button.getAttribute('style');
          
          if (className?.includes('success') || className?.includes('green') || 
              style?.includes('green') || className?.includes('check')) {
            validateButton = button;
            console.log(`✅ Coche verte trouvée par style: "${className}"`);
            break;
          }
        }
      }
      
      if (!validateButton) {
        console.log('⚠️ Coche verte non trouvée, tentative ENTER...');
        await competitorInput.press('Enter');
      } else {
        console.log('👆 Clic sur la coche verte...');
        await validateButton.click();
      }
      
      // 6. Attendre que la ligne soit ajoutée
      console.log('⏳ Attente de l\'ajout de la ligne...');
      await this.page.waitForTimeout(5000);
      
      console.log(`✅ Concurrent ${domain} ajouté avec succès !`);
      return true;
      
    } catch (error) {
      console.error(`❌ Erreur ajout concurrent ${domain}:`, error.message);
      return false;
    }
  }

  async extractCompetitorData(domain) {
    console.log(`📊 Extraction des données pour: ${domain}`);
    
    try {
      // Attendre que les données se chargent
      await this.page.waitForTimeout(3000);
      
      // Chercher la ligne contenant le domaine
      const rowData = await this.page.evaluate((searchDomain) => {
        const rows = document.querySelectorAll('tr, .row, .competitor-row');
        
        for (const row of rows) {
          const text = row.textContent || '';
          
          if (text.includes(searchDomain)) {
            // Extraire toutes les cellules/colonnes de cette ligne
            const cells = row.querySelectorAll('td, .cell, .col, .data-cell');
            const data = {};
            
            cells.forEach((cell, index) => {
              const cellText = cell.textContent?.trim();
              const cellClass = cell.className;
              
              // Identifier les colonnes par contenu
              if (cellText?.match(/\d+\.?\d*[KMB]?/)) {
                if (cellText.includes('K') || cellText.includes('M') || cellText.includes('B')) {
                  // C'est probablement visits ou une métrique
                  if (cellClass?.includes('visits') || index === 1 || index === 2) {
                    data.visits = cellText;
                  } else {
                    data[`metric_${index}`] = cellText;
                  }
                }
              }
            });
            
            // Extraire également tout le contenu de la ligne
            data.fullRowText = text;
            data.domain = searchDomain;
            
            return data;
          }
        }
        
        return null;
      }, domain);
      
      if (rowData) {
        console.log(`✅ Données extraites pour ${domain}:`);
        console.log(`   📊 Visits: ${rowData.visits || 'Non trouvé'}`);
        console.log(`   📝 Ligne complète: ${rowData.fullRowText?.substring(0, 100)}...`);
        
        return rowData;
      } else {
        console.log(`⚠️ Aucune donnée trouvée pour ${domain}`);
        
        // Extraction alternative - chercher tous les nombres avec K/M/B
        const allNumbers = await this.page.evaluate(() => {
          const text = document.body.textContent;
          const numbers = text.match(/\d+\.?\d*[KMB]/g);
          return numbers ? [...new Set(numbers)] : [];
        });
        
        console.log(`🔍 Nombres trouvés sur la page: ${allNumbers.join(', ')}`);
        
        return {
          domain,
          visits: 'Non trouvé',
          alternativeNumbers: allNumbers,
          error: 'Ligne non trouvée'
        };
      }
      
    } catch (error) {
      console.error(`❌ Erreur extraction ${domain}:`, error.message);
      return {
        domain,
        visits: 'Erreur',
        error: error.message
      };
    }
  }

  async scrapeCompetitorTraffic(competitors = ['cakesbody.com']) {
    console.log('🚀 SCRAPING TRAFFIC COMPETITORS');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // 1. Connexion
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      
      // 2. Navigation vers Traffic Overview
      const navSuccess = await this.navigateToTrafficOverview();
      if (!navSuccess) throw new Error('Navigation échouée');
      
      // 3. Pour chaque concurrent
      for (const competitor of competitors) {
        console.log(`\n🎯 TRAITEMENT: ${competitor}`);
        console.log('-'.repeat(50));
        
        // Ajouter le concurrent
        const addSuccess = await this.addCompetitor(competitor);
        
        if (addSuccess) {
          // Extraire les données
          const data = await this.extractCompetitorData(competitor);
          this.competitorData.push(data);
        } else {
          this.competitorData.push({
            domain: competitor,
            visits: 'Erreur ajout',
            error: 'Impossible d\'ajouter le concurrent'
          });
        }
        
        // Pause entre les ajouts
        await this.page.waitForTimeout(2000);
      }
      
      // 4. Sauvegarde
      const output = {
        timestamp: new Date().toISOString(),
        source: 'Traffic Overview - Competitors',
        competitorData: this.competitorData,
        summary: this.generateSummary()
      };
      
      const filename = `traffic-competitors-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(output, null, 2));
      console.log(`\n💾 Données sauvegardées: ${filename}`);
      
      // 5. Affichage des résultats
      this.displayResults();
      
      return this.competitorData;
      
    } catch (error) {
      console.error('💥 Erreur scraping traffic:', error.message);
    } finally {
      await this.close();
    }
  }

  generateSummary() {
    return this.competitorData.map(data => 
      `${data.domain}: ${data.visits || 'N/A'}`
    );
  }

  displayResults() {
    console.log('\n🎯 RÉSULTATS TRAFFIC COMPETITORS:');
    console.log('═══════════════════════════════════════════════════');
    
    if (this.competitorData.length === 0) {
      console.log('⚠️ Aucune donnée récupérée');
      return;
    }
    
    this.competitorData.forEach((data, index) => {
      console.log(`\n🔸 CONCURRENT ${index + 1}: ${data.domain}`);
      console.log(`   📊 Visits: ${data.visits || 'Non disponible'}`);
      
      if (data.alternativeNumbers?.length > 0) {
        console.log(`   🔍 Autres nombres: ${data.alternativeNumbers.join(', ')}`);
      }
      
      if (data.error) {
        console.log(`   ⚠️ Erreur: ${data.error}`);
      }
    });
    
    // Highlight pour cakesbody.com
    const cakesData = this.competitorData.find(d => d.domain.includes('cakesbody'));
    if (cakesData && cakesData.visits && cakesData.visits !== 'Non trouvé') {
      console.log(`\n🎉 VALEUR CAKESBODY.COM TROUVÉE: ${cakesData.visits}`);
    }
  }
}

// Fonction principale
async function scrapeCakesBodyTraffic() {
  const scraper = new TrafficCompetitorScraper();
  await scraper.scrapeCompetitorTraffic(['cakesbody.com']);
}

// Fonction pour scraper plusieurs concurrents
async function scrapeMultipleCompetitors(competitors) {
  const scraper = new TrafficCompetitorScraper();
  await scraper.scrapeCompetitorTraffic(competitors);
}

export { TrafficCompetitorScraper, scrapeCakesBodyTraffic, scrapeMultipleCompetitors };

if (import.meta.url === `file://${process.argv[1]}`) {
  const competitors = process.argv.slice(2);
  
  if (competitors.length > 0) {
    scrapeMultipleCompetitors(competitors);
  } else {
    scrapeCakesBodyTraffic();
  }
}