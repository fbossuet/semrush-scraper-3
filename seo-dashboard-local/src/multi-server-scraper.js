// 🌐 Multi-Server Scraper avec Fallback Automatique
import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import fs from 'fs';

class MultiServerScraper extends NoxToolsScraper {
  
  constructor() {
    super();
    this.availableServers = [
      'server1.noxtools.com',
      'server2.noxtools.com', 
      'server3.noxtools.com',
      'server4.noxtools.com',
      'server5.noxtools.com'
    ];
    this.workingServer = null;
  }

  async findWorkingServer(domain, path = '/analytics/overview/') {
    console.log('🌐 RECHERCHE D\'UN SERVEUR DISPONIBLE...');
    console.log('═══════════════════════════════════════════════════');
    
    for (let i = 0; i < this.availableServers.length; i++) {
      const server = this.availableServers[i];
      const serverNumber = i + 1;
      
      console.log(`🔍 Test server${serverNumber}: ${server}`);
      
      try {
        const testUrl = `https://${server}${path}?db=us&q=${encodeURIComponent(domain)}&searchType=domain`;
        
        console.log(`   📡 URL: ${testUrl}`);
        
        // Tester la connexion au serveur
        const response = await this.page.goto(testUrl, { 
          waitUntil: 'domcontentloaded',
          timeout: 30000 
        });
        
        console.log(`   📊 Status HTTP: ${response.status()}`);
        
        if (!response.ok()) {
          console.log(`   ❌ Server${serverNumber} HTTP Error: ${response.status()}`);
          continue;
        }
        
        // Attendre le chargement
        await this.page.waitForTimeout(3000);
        
        // Vérifier si on a une page de login (serveur indisponible)
        const pageContent = await this.page.textContent('body');
        
        if (pageContent.includes('Login to your Account') || 
            pageContent.includes('Username/Email')) {
          console.log(`   ❌ Server${serverNumber} nécessite une connexion`);
          continue;
        }
        
        // Vérifier les limitations quotidiennes
        const hasLimitOverlay = await this.checkDailyLimitOverlay();
        if (hasLimitOverlay) {
          console.log(`   ⚠️  Server${serverNumber} limite quotidienne atteinte`);
          continue; // Essayer le serveur suivant
        }
        
        // Vérifier si on a des données réelles
        const hasData = await this.quickDataCheck(domain, pageContent);
        
        if (hasData) {
          console.log(`   ✅ Server${serverNumber} fonctionne avec des données !`);
          this.workingServer = server;
          return {
            success: true,
            server: server,
            serverNumber: serverNumber,
            url: testUrl
          };
        } else {
          console.log(`   ⚠️  Server${serverNumber} accessible mais pas de données pour ${domain}`);
        }
        
      } catch (error) {
        console.log(`   ❌ Server${serverNumber} erreur: ${error.message}`);
        continue;
      }
    }
    
    console.log('💥 Aucun serveur disponible trouvé !');
    return {
      success: false,
      error: 'Tous les serveurs sont indisponibles ou ont atteint leurs limites'
    };
  }

  async checkDailyLimitOverlay() {
    try {
      // Vérifier l'overlay de limite quotidienne selon le code HTML fourni
      const limitOverlay = await this.page.evaluate(() => {
        // Chercher l'overlay par différents sélecteurs
        const overlaySelectors = [
          '[data-at="limit-block"]',
          '.sc-gsFSXq[data-at="limit-block"]',
          'div:has-text("Reports per day are limited")',
          'div:has-text("Get more with Business plan")'
        ];
        
        for (const selector of overlaySelectors) {
          try {
            const element = document.querySelector(selector);
            if (element && element.offsetParent !== null) { // Visible
              return {
                found: true,
                text: element.textContent?.substring(0, 100),
                selector: selector
              };
            }
          } catch (e) {
            // Continuer avec le prochain sélecteur
          }
        }
        
        // Vérification par texte aussi
        const bodyText = document.body.textContent || '';
        if (bodyText.includes('Reports per day are limited') || 
            bodyText.includes('Upgrade to Business')) {
          return {
            found: true,
            text: 'Limite détectée par texte',
            selector: 'text-based'
          };
        }
        
        return { found: false };
      });
      
      if (limitOverlay.found) {
        console.log(`   🚫 Limite quotidienne détectée: ${limitOverlay.text}`);
        return true;
      }
      
      return false;
      
    } catch (error) {
      console.log(`   ⚠️  Erreur vérification limite: ${error.message}`);
      return false;
    }
  }

  async quickDataCheck(domain, pageContent) {
    // Vérification rapide de la présence de données
    const checks = {
      domainMentioned: pageContent.includes(domain),
      hasNumbers: (pageContent.match(/\d+/g) || []).length > 10,
      hasMetrics: /\d+\.?\d*[KMBkm]/.test(pageContent),
      hasTrafficWords: /\b(?:traffic|visits?|visitors?|organic)\b/i.test(pageContent)
    };
    
    console.log(`   🔍 Vérifications: domain=${checks.domainMentioned}, numbers=${checks.hasNumbers}, metrics=${checks.hasMetrics}, traffic=${checks.hasTrafficWords}`);
    
    // Au moins 2 checks doivent passer
    const passedChecks = Object.values(checks).filter(Boolean).length;
    return passedChecks >= 2;
  }

  async extractDataFromWorkingServer(domain) {
    if (!this.workingServer) {
      throw new Error('Aucun serveur disponible');
    }
    
    console.log(`\n📊 EXTRACTION DES DONNÉES depuis ${this.workingServer}...`);
    console.log('═══════════════════════════════════════════════════');
    
    try {
      // Attendre le chargement complet des données
      console.log('⏳ Attente du chargement des données...');
      await this.page.waitForTimeout(10000);
      
      // Extraction exhaustive
      const pageContent = await this.page.textContent('body');
      const htmlContent = await this.page.content();
      
      // Patterns d'extraction étendus
      const extractedData = {
        domain: domain,
        server: this.workingServer,
        timestamp: new Date().toISOString(),
        
        // Métriques basiques
        allNumbers: pageContent.match(/\d+/g) || [],
        numbersWithSuffix: pageContent.match(/\d+\.?\d*[KMBkm]/g) || [],
        
        // Patterns spécialisés
        trafficMetrics: this.extractTrafficMetrics(pageContent),
        organicMetrics: this.extractOrganicMetrics(pageContent),
        
        // Métriques spécifiques au domaine
        domainSpecificData: this.extractDomainSpecificData(pageContent, domain),
        
        // Analyse DOM
        domAnalysis: await this.extractFromDOM(),
        
        // Échantillon de contenu
        contentSample: pageContent.substring(0, 2000),
        htmlSample: htmlContent.substring(0, 2000)
      };
      
      // Affichage des résultats
      this.displayExtractionResults(extractedData);
      
      return extractedData;
      
    } catch (error) {
      console.error('❌ Erreur extraction:', error.message);
      throw error;
    }
  }

  extractTrafficMetrics(content) {
    const patterns = {
      // Standard : "1.2K visits"
      standard: content.match(/(\d+\.?\d*[KMBkm])\s*(?:visits?|visitors?|traffic)/gi) || [],
      
      // Inverse : "visits: 1.2K"  
      inverse: content.match(/(?:visits?|visitors?|traffic)[:\s]+(\d+\.?\d*[KMBkm]?)/gi) || [],
      
      // Avec virgules : "1,200 visits"
      withCommas: content.match(/(\d{1,3}(?:,\d{3})+)\s*(?:visits?|visitors?|traffic)/gi) || [],
      
      // Monthly : "1.2K monthly visitors"
      monthly: content.match(/(\d+\.?\d*[KMBkm]?)\s*monthly\s*(?:visits?|visitors?)/gi) || []
    };
    
    return patterns;
  }

  extractOrganicMetrics(content) {
    const patterns = {
      // "60.1K organic traffic"
      organicTraffic: content.match(/(\d+\.?\d*[KMBkm]?)\s*organic\s*(?:traffic|visits?)/gi) || [],
      
      // "organic: 60.1K"
      organicInverse: content.match(/organic[:\s]+(\d+\.?\d*[KMBkm]?)/gi) || [],
      
      // "60.1K organic keywords"  
      organicKeywords: content.match(/(\d+\.?\d*[KMBkm]?)\s*organic\s*keywords?/gi) || []
    };
    
    return patterns;
  }

  extractDomainSpecificData(content, domain) {
    const domainLower = domain.toLowerCase();
    const results = [];
    
    // Chercher le domaine dans le contexte avec des nombres
    const regex = new RegExp(`${domainLower}[^0-9]{0,50}(\\d+\\.?\\d*[KMBkm]?)`, 'gi');
    const matches = content.matchAll(regex);
    
    for (const match of matches) {
      results.push({
        domain: domain,
        value: match[1],
        context: match[0]
      });
    }
    
    return results;
  }

  async extractFromDOM() {
    return await this.page.evaluate(() => {
      const result = {
        tables: [],
        metrics: [],
        buttons: []
      };
      
      // Analyser les tableaux
      document.querySelectorAll('table, .table, [class*="table"]').forEach(table => {
        const text = table.textContent || '';
        const numbers = text.match(/\d+\.?\d*[KMBkm]/g) || [];
        if (numbers.length > 0) {
          result.tables.push({
            text: text.substring(0, 300),
            numbers: numbers
          });
        }
      });
      
      // Chercher des métriques dans des éléments spécifiques
      document.querySelectorAll('span, div, td, th').forEach(el => {
        const text = el.textContent?.trim();
        if (text && text.match(/\d+\.?\d*[KMBkm]/)) {
          result.metrics.push(text);
        }
      });
      
      return result;
    });
  }

  displayExtractionResults(data) {
    console.log('\n🎯 RÉSULTATS EXTRACTION:');
    console.log('═══════════════════════════════════════════════════');
    
    console.log(`📡 Serveur utilisé: ${data.server}`);
    console.log(`🎯 Domaine: ${data.domain}`);
    console.log(`🔢 Nombres trouvés: ${data.allNumbers.length} total`);
    console.log(`📊 Avec suffixe (K/M/B): ${data.numbersWithSuffix.join(', ')}`);
    
    // Métriques traffic
    if (data.trafficMetrics.standard.length > 0) {
      console.log(`🚗 Traffic standard: ${data.trafficMetrics.standard.join(', ')}`);
    }
    
    if (data.trafficMetrics.withCommas.length > 0) {
      console.log(`🚗 Traffic avec virgules: ${data.trafficMetrics.withCommas.join(', ')}`);
    }
    
    // Métriques organiques
    if (data.organicMetrics.organicTraffic.length > 0) {
      console.log(`🌱 Organic traffic: ${data.organicMetrics.organicTraffic.join(', ')}`);
    }
    
    // Données spécifiques au domaine
    if (data.domainSpecificData.length > 0) {
      console.log(`🎯 Données ${data.domain}:`);
      data.domainSpecificData.forEach(item => {
        console.log(`   • ${item.value} (contexte: ${item.context.substring(0, 50)}...)`);
      });
    }
    
    // Analyse DOM
    if (data.domAnalysis.tables.length > 0) {
      console.log(`📋 Tableaux avec données: ${data.domAnalysis.tables.length}`);
    }
  }

  async fullMultiServerAnalysis(domain) {
    console.log('🌐 ANALYSE MULTI-SERVEUR COMPLÈTE');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // 1. Connexion
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      
      // 2. Trouver un serveur disponible
      const serverResult = await this.findWorkingServer(domain);
      
      if (!serverResult.success) {
        throw new Error(serverResult.error);
      }
      
      console.log(`\n✅ Serveur trouvé: ${serverResult.server} (server${serverResult.serverNumber})`);
      
      // 3. Extraire les données
      const extractedData = await this.extractDataFromWorkingServer(domain);
      
      // 4. Sauvegarder
      const filename = `multi-server-${domain.replace(/\W/g, '-')}-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(extractedData, null, 2));
      console.log(`\n💾 Données sauvegardées: ${filename}`);
      
      return extractedData;
      
    } catch (error) {
      console.error('💥 Erreur analyse multi-serveur:', error.message);
      throw error;
    } finally {
      await this.close();
    }
  }
}

// Fonction d'export
async function analyzeWithMultiServer(domain) {
  const scraper = new MultiServerScraper();
  return await scraper.fullMultiServerAnalysis(domain);
}

export { MultiServerScraper, analyzeWithMultiServer };

if (import.meta.url === `file://${process.argv[1]}`) {
  const domain = process.argv[2] || 'cakesbody.com';
  analyzeWithMultiServer(domain);
}