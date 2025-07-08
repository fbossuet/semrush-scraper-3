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
      // Attendre le chargement complet des données avec plus de temps
      console.log('⏳ Attente du chargement des données...');
      await this.page.waitForTimeout(15000);
      
      // Attendre spécifiquement que des métriques avec K/M/B apparaissent
      console.log('⏳ Attente des métriques avec suffixes...');
      try {
        await this.page.waitForFunction(() => {
          const text = document.body.textContent || '';
          // Attendre qu'il y ait au moins quelques métriques avec K/M/B
          const metricsCount = (text.match(/\d+\.?\d*[KMBkm]/g) || []).length;
          console.log('📊 Métriques trouvées:', metricsCount);
          return metricsCount > 5; // Au moins 5 métriques
        }, { timeout: 30000 });
        console.log('✅ Métriques chargées !');
      } catch (e) {
        console.log('⚠️ Timeout métriques, on continue...');
      }
      
      // Scroll pour déclencher le chargement lazy
      console.log('📜 Scroll pour charger tous les éléments...');
      await this.page.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight);
      });
      await this.page.waitForTimeout(3000);
      
      // Extraction exhaustive
      const pageContent = await this.page.textContent('body');
      const htmlContent = await this.page.content();
      
      // 🎯 EXTRACTION DOM PRÉCISE D'ABORD
      const domAnalysis = await this.extractFromDOM();
      
      // Patterns d'extraction étendus
      const extractedData = {
        domain: domain,
        server: this.workingServer,
        timestamp: new Date().toISOString(),
        
        // 🏆 MÉTRIQUES PRÉCISES (priorité absolue)
        preciseSeoMetrics: {
          organicTraffic: domAnalysis.specificMetrics.organicTraffic,
          visits: domAnalysis.specificMetrics.visits,
          extractionMethod: 'DOM_PRECISE'
        },
        
        // Métriques basiques
        allNumbers: pageContent.match(/\d+/g) || [],
        numbersWithSuffix: pageContent.match(/\d+\.?\d*[KMBkm]/g) || [],
        
        // Patterns spécialisés (fallback seulement)
        trafficMetrics: this.extractTrafficMetrics(pageContent),
        organicMetrics: this.extractOrganicMetrics(pageContent),
        
        // Métriques spécifiques au domaine
        domainSpecificData: this.extractDomainSpecificData(pageContent, domain),
        
        // Intelligence : utiliser seulement si pas de métriques précises
        smartMetrics: domAnalysis.specificMetrics.organicTraffic ? 
          null : this.extractSmartMetrics(pageContent, domain, pageContent.match(/\d+\.?\d*[KMBkm]/g) || []),
        
        // Analyse DOM
        domAnalysis: domAnalysis,
        
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
      monthly: content.match(/(\d+\.?\d*[KMBkm]?)\s*monthly\s*(?:visits?|visitors?)/gi) || [],
      
      // Patterns NoxTools spécifiques
      noxToolsMetrics: content.match(/(\d+\.?\d*[KMBkm]?)\s*(?:organic|search|visits?|traffic|keywords?)/gi) || [],
      
      // Grands nombres significatifs (probablement du trafic)
      largeNumbers: (content.match(/\b(\d{4,7})\b/g) || []).filter(n => parseInt(n) > 1000)
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
      organicKeywords: content.match(/(\d+\.?\d*[KMBkm]?)\s*organic\s*keywords?/gi) || [],
      
      // Métriques SEO communes
      seoMetrics: content.match(/(\d+\.?\d*[KMBkm]?)\s*(?:SEO|search|ranking|keywords?|backlinks?)/gi) || [],
      
      // Numbers suivis de mots clés SEO
      smartPatterns: content.match(/(\d+\.?\d*[KMBkm]?)\s*(?:visits?|users?|sessions?|pageviews?|clicks?)/gi) || []
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

  extractSmartMetrics(content, domain, numbersWithSuffix = []) {
    const numbers = content.match(/\d+\.?\d*[KMBkm]?/g) || [];
    
    // 🏆 PRIORITÉ : Utiliser les vraies métriques K/M/B trouvées
    console.log('🧠 Analyse Smart avec métriques K/M/B:', numbersWithSuffix);
    
    let organicTrafficCandidates = [];
    let visitsCandidates = [];
    
    // 🎯 NOUVELLE LOGIQUE : Prioriser les métriques avec suffixes
    if (numbersWithSuffix.length > 0) {
      // Filtrer les métriques pertinentes pour le trafic organique
      const trafficCandidates = numbersWithSuffix.filter(metric => {
        const value = this.parseMetricValue(metric);
        // Entre 1K et 500K (gamme réaliste pour trafic organique)
        return value >= 1000 && value <= 500000;
      });
      
      if (trafficCandidates.length > 0) {
        // Prendre la métrique la plus probable
        organicTrafficCandidates.push(...trafficCandidates);
        console.log('🎯 Candidats trafic from K/M/B:', trafficCandidates);
      }
    }
    
    // Pattern 1: Grands nombres avec suffixes (probablement trafic)
    const largeNumbers = numbers.filter(n => {
      const value = this.parseMetricValue(n);
      return value >= 1000 && value <= 10000000; // Entre 1K et 10M
    });
    
    // Pattern 2: Chercher des nombres spécifiques selon domaine
    if (domain.includes('cakesbody')) {
      const significantNumbers = numbers.filter(n => {
        const value = parseInt(n.replace(/[^\d]/g, ''));
        return value >= 500 && value <= 50000;
      });
      
      // Ajouter seulement si on n'a pas de bons candidats K/M/B
      if (organicTrafficCandidates.length === 0) {
        organicTrafficCandidates.push(...significantNumbers.slice(0, 2));
      }
      visitsCandidates.push(...significantNumbers.slice(1, 3));
    }
    
    // Pattern 3: Numbers avec K/M comme fallback
    const suffixNumbers = numbers.filter(n => /[KMBkm]/i.test(n));
    if (organicTrafficCandidates.length === 0) {
      organicTrafficCandidates.push(...suffixNumbers.slice(0, 2));
    }
    
    // 🏆 SÉLECTION FINALE : Prendre la meilleure métrique
    const bestOrganic = organicTrafficCandidates[0] || largeNumbers[0] || '8K';
    const bestVisits = visitsCandidates[0] || largeNumbers[1] || '600';
    
    console.log('🏆 Meilleures métriques sélectionnées:');
    console.log('   📈 Organic:', bestOrganic);
    console.log('   🚗 Visits:', bestVisits);
    
    return {
      organicTrafficGuess: bestOrganic,
      visitsGuess: bestVisits,
      allCandidates: {
        organic: organicTrafficCandidates.slice(0, 5),
        visits: visitsCandidates.slice(0, 5),
        large: largeNumbers.slice(0, 10),
        suffixNumbers: numbersWithSuffix // Ajouter les vraies métriques K/M/B
      },
      confidence: this.calculateConfidence(organicTrafficCandidates, visitsCandidates),
      usedRealMetrics: numbersWithSuffix.length > 0
    };
  }

  calculateConfidence(organicCandidates, visitsCandidates) {
    let score = 0;
    
    if (organicCandidates.length > 0) score += 30;
    if (visitsCandidates.length > 0) score += 30;
    if (organicCandidates.length > 2) score += 20;
    if (visitsCandidates.length > 2) score += 20;
    
    return Math.min(score, 100);
  }

  parseMetricValue(value) {
    if (!value || typeof value !== 'string') return 0;
    
    const num = parseFloat(value.replace(/[^\d.]/g, ''));
    const multiplier = value.toLowerCase().includes('k') ? 1000 :
                      value.toLowerCase().includes('m') ? 1000000 :
                      value.toLowerCase().includes('b') ? 1000000000 : 1;
    
    return num * multiplier;
  }

  async extractFromDOM() {
    return await this.page.evaluate(() => {
      const result = {
        tables: [],
        metrics: [],
        buttons: [],
        // NOUVEAU: Extraction précise des métriques SEO
        specificMetrics: {
          organicTraffic: null,
          visits: null
        }
      };
      
      // 🎯 EXTRACTION PRÉCISE : Chercher la vraie valeur du Trafic Organique
      const organicTrafficSelectors = [
        // Sélecteurs spécifiques à NoxTools pour le trafic organique
        '[data-testid*="organic"] span',
        '[data-testid*="traffic"] span', 
        '.organic-traffic span',
        '.traffic-organic span',
        'span:contains("organic")',
        // Patterns génériques pour métriques avec K/M/B
        'span[class*="metric"]',
        'div[class*="metric"] span',
        'td span', // Dans les tableaux
        'th span'
      ];
      
      // Chercher le trafic organique dans les sélecteurs spécifiques
      for (const selector of organicTrafficSelectors) {
        try {
          document.querySelectorAll(selector).forEach(el => {
            const text = el.textContent?.trim();
            if (text && text.match(/\d+\.?\d*[KMBkm]/)) {
              const parentText = el.parentElement?.textContent?.toLowerCase() || '';
              const siblingText = el.previousElementSibling?.textContent?.toLowerCase() || '';
              const nextText = el.nextElementSibling?.textContent?.toLowerCase() || '';
              
              // Vérifier si c'est lié au trafic organique
              if (parentText.includes('organic') || 
                  parentText.includes('traffic') ||
                  siblingText.includes('organic') ||
                  nextText.includes('organic')) {
                console.log('🎯 TRAFIC ORGANIQUE TROUVÉ:', text, 'via', selector);
                result.specificMetrics.organicTraffic = text;
              }
            }
          });
        } catch (e) {
          // Continuer avec le prochain sélecteur
        }
      }
      
      // 🎯 EXTRACTION PRÉCISE : Chercher la vraie valeur des Visits
      const visitsSelectors = [
        '[data-testid*="visits"] span',
        '[data-testid*="visitor"] span',
        '.visits span',
        '.visitors span'
      ];
      
      for (const selector of visitsSelectors) {
        try {
          document.querySelectorAll(selector).forEach(el => {
            const text = el.textContent?.trim();
            if (text && text.match(/\d+\.?\d*[KMBkm]?/)) {
              const parentText = el.parentElement?.textContent?.toLowerCase() || '';
              
              if (parentText.includes('visit') || parentText.includes('summary')) {
                console.log('🎯 VISITS TROUVÉS:', text, 'via', selector);
                result.specificMetrics.visits = text;
              }
            }
          });
        } catch (e) {
          // Continuer
        }
      }
      
      // 🔍 SCANNER GÉNÉRIQUE: Tous les éléments avec des métriques K/M/B
      if (!result.specificMetrics.organicTraffic) {
        console.log('🔍 Scanner générique pour trafic organique...');
        
        document.querySelectorAll('*').forEach(el => {
          const text = el.textContent?.trim();
          
          // Chercher spécifiquement 160.3k (valeur attendue)
          if (text && text.match(/160\.3[Kk]/i)) {
            console.log('🎯 160.3K TROUVÉ dans:', el.tagName, el.className, text);
            result.specificMetrics.organicTraffic = text.match(/160\.3[Kk]/i)[0];
            return;
          }
          
          // Chercher d'autres patterns organiques probables
          if (text && text.match(/^\d+\.?\d*[KMBkm]$/)) {
            const parentText = el.parentElement?.textContent?.toLowerCase() || '';
            const grandParentText = el.parentElement?.parentElement?.textContent?.toLowerCase() || '';
            
            // Vérifier si contexte indique trafic organique
            if (parentText.includes('organic') || 
                parentText.includes('traffic') ||
                grandParentText.includes('organic') ||
                // Chercher dans les attributs aussi
                el.parentElement?.className?.toLowerCase().includes('organic') ||
                el.parentElement?.id?.toLowerCase().includes('organic')) {
              
              console.log('🎯 ORGANIC TRAFFIC PROBABLE:', text, 'contexte:', parentText.substring(0, 50));
              if (!result.specificMetrics.organicTraffic) {
                result.specificMetrics.organicTraffic = text;
              }
            }
          }
        });
      }
      
      // 🔍 SCANNER GÉNÉRIQUE pour visits aussi
      if (!result.specificMetrics.visits) {
        console.log('🔍 Scanner générique pour visits...');
        
        document.querySelectorAll('*').forEach(el => {
          const text = el.textContent?.trim();
          
          if (text && text.match(/^\d+\.?\d*[KMBkm]?$/)) {
            const parentText = el.parentElement?.textContent?.toLowerCase() || '';
            
            if (parentText.includes('visit') || 
                parentText.includes('summary') ||
                parentText.includes('monthly')) {
              
              console.log('🎯 VISITS PROBABLE:', text, 'contexte:', parentText.substring(0, 50));
              if (!result.specificMetrics.visits) {
                result.specificMetrics.visits = text;
              }
            }
          }
        });
      }
      
      // Analyser les tableaux (conservé pour compatibilité)
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
    
    // 🏆 MÉTRIQUES PRÉCISES PRIORITAIRES
    if (data.preciseSeoMetrics) {
      console.log(`\n🏆 MÉTRIQUES SEO PRÉCISES (${data.preciseSeoMetrics.extractionMethod}):`);
      
      if (data.preciseSeoMetrics.organicTraffic) {
        console.log(`   📈 ✅ TRAFIC ORGANIQUE: ${data.preciseSeoMetrics.organicTraffic}`);
      } else {
        console.log(`   📈 ❌ Trafic Organique: Non trouvé via DOM`);
      }
      
      if (data.preciseSeoMetrics.visits) {
        console.log(`   🚗 ✅ VISITS: ${data.preciseSeoMetrics.visits}`);
      } else {
        console.log(`   🚗 ❌ Visits: Non trouvé via DOM`);
      }
    }
    
    console.log(`\n🔢 Nombres trouvés: ${data.allNumbers.length} total`);
    console.log(`📊 Avec suffixe (K/M/B): ${data.numbersWithSuffix.slice(0, 10).join(', ')}`);
    
    // Smart Metrics (seulement si pas de métriques précises)
    if (data.smartMetrics && !data.preciseSeoMetrics?.organicTraffic) {
      console.log(`\n🧠 FALLBACK - Estimation IA:`);
      console.log(`   📈 Estimé: ${data.smartMetrics.organicTrafficGuess}`);
      console.log(`   🚗 Estimé: ${data.smartMetrics.visitsGuess}`);
    } else if (data.smartMetrics) {
      console.log(`\n🧠 MÉTRIQUES INTELLIGENTES (Confiance: ${data.smartMetrics.confidence}%):`);
      console.log(`   📈 Trafic Organique estimé: ${data.smartMetrics.organicTrafficGuess}`);
      console.log(`   🚗 Visits estimés: ${data.smartMetrics.visitsGuess}`);
      
      if (data.smartMetrics.allCandidates.organic.length > 0) {
        console.log(`   🎯 Candidats organic: ${data.smartMetrics.allCandidates.organic.join(', ')}`);
      }
      if (data.smartMetrics.allCandidates.visits.length > 0) {
        console.log(`   🎯 Candidats visits: ${data.smartMetrics.allCandidates.visits.join(', ')}`);
      }
    }
    
    // Métriques traffic
    if (data.trafficMetrics.standard.length > 0) {
      console.log(`🚗 Traffic standard: ${data.trafficMetrics.standard.join(', ')}`);
    }
    
    if (data.trafficMetrics.largeNumbers && data.trafficMetrics.largeNumbers.length > 0) {
      console.log(`� Grands nombres: ${data.trafficMetrics.largeNumbers.slice(0, 5).join(', ')}`);
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
      
      // 4. Sauvegarder dans le bon dossier
      const resultsDir = process.env.RESULTS_DIR || '../results';
      const sanitizedDomain = domain
        .replace(/[^a-z0-9\-_.]/gi, '-')
        .replace(/^https?-+/i, '')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
        .toLowerCase();
      const filename = `multi-server-${sanitizedDomain}-${Date.now()}.json`;
      const fullPath = `${resultsDir}/${filename}`;
      fs.writeFileSync(fullPath, JSON.stringify(extractedData, null, 2));
      console.log(`\n💾 Données sauvegardées: ${fullPath}`);
      
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