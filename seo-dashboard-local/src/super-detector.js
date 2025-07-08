import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import fs from 'fs';

class SuperDetector extends NoxToolsScraper {
  
  constructor() {
    super();
    this.networkResponses = [];
    this.allContent = [];
  }
  
  async setupNetworkMonitoring() {
    console.log('🕵️ Surveillance des appels réseau...');
    
    // Capturer toutes les réponses réseau
    this.page.on('response', async (response) => {
      try {
        const url = response.url();
        if (url.includes('analytics') || url.includes('api') || url.includes('data')) {
          const text = await response.text();
          this.networkResponses.push({
            url,
            status: response.status(),
            contentType: response.headers()['content-type'],
            body: text
          });
          
          // Chercher immédiatement 60.1 dans les réponses
          if (text.includes('60.1') || text.includes('60,1')) {
            console.log(`🎯 TROUVÉ 60.1 dans ${url} !`);
            console.log(`📝 Contenu: ${text.substring(0, 500)}...`);
          }
        }
      } catch (error) {
        // Ignore les erreurs de parsing
      }
    });
  }
  
  async captureEverything() {
    console.log('🔍 CAPTURE EXHAUSTIVE DE TOUT LE CONTENU');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      // 1. Contenu HTML complet
      const html = await this.page.content();
      this.allContent.push({ type: 'HTML', content: html });
      
      // 2. Tous les iframes
      const frames = this.page.frames();
      for (const frame of frames) {
        try {
          const frameContent = await frame.content();
          this.allContent.push({ type: 'IFRAME', url: frame.url(), content: frameContent });
        } catch (e) {}
      }
      
      // 3. Variables JavaScript globales  
      const jsVars = await this.page.evaluate(() => {
        const vars = {};
        
        // Capturer toutes les variables globales
        for (let key in window) {
          try {
            if (typeof window[key] === 'object' && window[key] !== null) {
              vars[key] = JSON.stringify(window[key]);
            } else if (typeof window[key] === 'string' || typeof window[key] === 'number') {
              vars[key] = window[key];
            }
          } catch (e) {}
        }
        
        return vars;
      });
      
      this.allContent.push({ type: 'JS_VARS', content: JSON.stringify(jsVars) });
      
      // 4. Local Storage et Session Storage
      const storageData = await this.page.evaluate(() => {
        const data = {};
        
        try {
          data.localStorage = { ...localStorage };
          data.sessionStorage = { ...sessionStorage };
        } catch (e) {}
        
        return data;
      });
      
      this.allContent.push({ type: 'STORAGE', content: JSON.stringify(storageData) });
      
      // 5. Tous les éléments avec du texte
      const allElementsText = await this.page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('*'));
        return elements.map(el => ({
          tag: el.tagName,
          class: el.className,
          id: el.id,
          text: el.textContent?.trim(),
          innerHTML: el.innerHTML?.substring(0, 200)
        })).filter(el => el.text && el.text.length > 0);
      });
      
      this.allContent.push({ type: 'ALL_ELEMENTS', content: JSON.stringify(allElementsText) });
      
      return this.allContent;
      
    } catch (error) {
      console.error('❌ Erreur capture exhaustive:', error.message);
      return this.allContent;
    }
  }
  
  searchForValue(searchValue = '60.1') {
    console.log(`\n🎯 RECHERCHE EXHAUSTIVE DE "${searchValue}"`);
    console.log('═══════════════════════════════════════════════════');
    
    const results = [];
    
    // Variations possibles
    const variations = [
      '60.1k', '60.1K', '60,1k', '60,1K',
      '60.1 k', '60.1 K', '60,1 k', '60,1 K',
      '60.1', '60,1',
      'traffic 60.1', 'organic 60.1', 'visits 60.1'
    ];
    
    // Chercher dans tout le contenu capturé
    this.allContent.forEach((item, index) => {
      variations.forEach(variation => {
        if (item.content && item.content.includes(variation)) {
          const context = this.extractContext(item.content, variation);
          results.push({
            type: item.type,
            url: item.url || 'N/A',
            variation,
            context,
            index
          });
        }
      });
    });
    
    // Chercher dans les réponses réseau
    this.networkResponses.forEach((response, index) => {
      variations.forEach(variation => {
        if (response.body && response.body.includes(variation)) {
          const context = this.extractContext(response.body, variation);
          results.push({
            type: 'NETWORK_RESPONSE',
            url: response.url,
            variation,
            context,
            index
          });
        }
      });
    });
    
    return results;
  }
  
  extractContext(content, searchValue) {
    const index = content.indexOf(searchValue);
    const start = Math.max(0, index - 100);
    const end = Math.min(content.length, index + 100);
    return content.substring(start, end);
  }
  
  async fullDetection() {
    console.log('🚀 SUPER-DÉTECTEUR ACTIVÉ');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // Configurer la surveillance réseau
      await this.setupNetworkMonitoring();
      
      // Connexion
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      
      // Tester plusieurs pages
      const pages = [
        'https://server1.noxtools.com/analytics/overview/?db=us&q=https%3A%2F%2Fthe-foldie.com&searchType=domain',
        'https://server1.noxtools.com/analytics/organic/overview/?db=us&q=https%3A%2F%2Fthe-foldie.com&searchType=domain'
      ];
      
      for (const pageUrl of pages) {
        console.log(`\n📄 ANALYSE DE: ${pageUrl}`);
        console.log('-'.repeat(60));
        
        await this.page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
        
        // Attendre le chargement
        await this.page.waitForTimeout(15000);
        
        // Capture exhaustive
        await this.captureEverything();
        
        // Recherche immédiate
        const results = this.searchForValue('60.1');
        
        if (results.length > 0) {
          console.log(`\n🎉 TROUVÉ ${results.length} CORRESPONDANCE(S) !`);
          results.forEach((result, i) => {
            console.log(`\n🎯 RÉSULTAT ${i + 1}:`);
            console.log(`   📂 Type: ${result.type}`);
            console.log(`   🔗 URL: ${result.url}`);
            console.log(`   🔸 Valeur: ${result.variation}`);
            console.log(`   📝 Contexte: ...${result.context}...`);
          });
        } else {
          console.log('❌ Aucune correspondance sur cette page');
        }
      }
      
      // Sauvegarde finale
      const output = {
        timestamp: new Date().toISOString(),
        domain: 'https://the-foldie.com',
        allContent: this.allContent,
        networkResponses: this.networkResponses,
        searchResults: this.searchForValue('60.1')
      };
      
      const filename = `super-detection-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(output, null, 2));
      console.log(`\n💾 Rapport complet sauvegardé: ${filename}`);
      
      return output;
      
    } catch (error) {
      console.error('💥 Erreur super-détecteur:', error.message);
    } finally {
      await this.close();
    }
  }
}

// Lancement
async function runSuperDetection() {
  const detector = new SuperDetector();
  await detector.fullDetection();
}

export { SuperDetector, runSuperDetection };

if (import.meta.url === `file://${process.argv[1]}`) {
  runSuperDetection();
}