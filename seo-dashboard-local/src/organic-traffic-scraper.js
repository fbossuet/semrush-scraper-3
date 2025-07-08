import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import fs from 'fs';

class DynamicMetricsScraper extends NoxToolsScraper {
  
  async waitForDynamicContent() {
    console.log('⏳ Attente du chargement des données dynamiques...');
    
    // Attendre que les données se chargent (plus long délai)
    await this.page.waitForTimeout(10000);
    
    // Attendre que les scripts JS s'exécutent ou timeout plus court
    try {
      await this.page.waitForFunction(() => {
        // Vérifier si des éléments contenant des métriques sont chargés
        const hasNumbers = document.body.textContent.match(/\d+\.?\d*[KMkm]/);
        const hasOrganicContent = document.body.textContent.includes('organic');
        return (hasNumbers && hasNumbers.length > 2) || hasOrganicContent;
      }, { timeout: 15000 });
    } catch (e) {
      console.log('⚠️  Timeout attente contenu dynamique, on continue...');
    }
    
    console.log('✅ Contenu dynamique chargé !');
  }
  
  async captureRealTimeMetrics() {
    console.log('📊 Capture des métriques en temps réel...');
    
    try {
      // Attendre le chargement dynamique
      await this.waitForDynamicContent();
      
      // Récupérer le HTML final après chargement des données
      const finalHtml = await this.page.content();
      
      // Récupérer les données depuis les variables JavaScript
      const jsData = await this.page.evaluate(() => {
        const data = {};
        
        // Chercher dans les variables globales communes
        if (window.sm2) data.sm2 = window.sm2;
        if (window.analytics) data.analytics = window.analytics;
        if (window.__sm2mfp) data.sm2mfp = window.__sm2mfp;
        
        // Chercher les éléments contenant des métriques
        const allElements = document.querySelectorAll('*');
        const metrics = [];
        
        allElements.forEach(el => {
          const text = el.textContent || '';
          // Chercher les patterns de métriques
          const metricMatch = text.match(/(\d+\.?\d*[KMkm]?)\s*(traffic|visitors|keywords|backlinks|organic)/i);
          if (metricMatch) {
            metrics.push({
              value: metricMatch[1],
              type: metricMatch[2],
              fullText: text.trim(),
              tagName: el.tagName,
              className: el.className
            });
          }
        });
        
        data.extractedMetrics = metrics;
        return data;
      });
      
      // Recherche spécifique de métriques dans le HTML
      const htmlMetrics = this.extractMetricsFromHtml(finalHtml);
      
      return {
        jsData,
        htmlMetrics,
        finalHtml: finalHtml.length > 10000 ? finalHtml.substring(0, 10000) + '...' : finalHtml
      };
      
    } catch (error) {
      console.error('❌ Erreur capture métriques:', error.message);
      return null;
    }
  }
  
  extractMetricsFromHtml(html) {
    console.log('🔍 Extraction des métriques depuis HTML...');
    
    const metrics = {};
    
    // Patterns spécifiques pour les métriques SEO
    const patterns = {
      organicTraffic: [
        /organic\s+(?:search\s+)?traffic[:\s]*(\d+\.?\d*[KMkm]?)/gi,
        /(\d+\.?\d*[KMkm]?)\s+organic\s+(?:search\s+)?traffic/gi,
        /traffic.*?organic[:\s]*(\d+\.?\d*[KMkm]?)/gi
      ],
      organicKeywords: [
        /organic\s+keywords[:\s]*(\d+\.?\d*[KMkm]?)/gi,
        /(\d+\.?\d*[KMkm]?)\s+organic\s+keywords/gi,
        /keywords.*?organic[:\s]*(\d+\.?\d*[KMkm]?)/gi
      ],
      backlinks: [
        /backlinks[:\s]*(\d+\.?\d*[KMkm]?)/gi,
        /(\d+\.?\d*[KMkm]?)\s+backlinks/gi
      ]
    };
    
    Object.entries(patterns).forEach(([metricName, regexList]) => {
      regexList.forEach(regex => {
        const matches = [...html.matchAll(regex)];
        matches.forEach(match => {
          const value = match[1] || match[2];
          if (value && !metrics[metricName]) {
            metrics[metricName] = value;
            console.log(`   ✅ ${metricName}: ${value}`);
          }
        });
      });
    });
    
    return metrics;
  }
  
  async navigateToOrganicOverview() {
    console.log('🌱 Navigation vers Organic Overview...');
    
    try {
      // 🔧 CORRECTIF : Récupérer le domaine depuis l'argument ou config
      const targetDomain = process.argv[2] || config.analyticsParams?.domain || 'https://the-foldie.com';
      const domain = encodeURIComponent(targetDomain);
      const organicUrl = `https://server1.noxtools.com/analytics/organic/overview/?db=us&q=${domain}&searchType=domain`;
      
      console.log(`🎯 Domaine analysé: ${targetDomain}`);
      
      console.log(`🎯 URL Organic: ${organicUrl}`);
      
      await this.page.goto(organicUrl, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      console.log('✅ Page Organic Overview chargée !');
      
      // Attendre le chargement des données spécifiques à organic
      await this.waitForDynamicContent();
      
      return true;
      
    } catch (error) {
      console.error('❌ Erreur navigation organic:', error.message);
      return false;
    }
  }
  
  async fullOrganicTrafficAnalysis() {
    console.log('🚀 ANALYSE COMPLÈTE DU TRAFIC ORGANIQUE');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // Étape 1: Connexion
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      
      // Étape 2: Navigation vers organic overview
      const organicSuccess = await this.navigateToOrganicOverview();
      if (!organicSuccess) throw new Error('Navigation organic échouée');
      
      // Étape 3: Capture des métriques dynamiques
      const metrics = await this.captureRealTimeMetrics();
      
      // Étape 4: Sauvegarde
      const timestamp = Date.now();
      const targetDomain = process.argv[2] || config.analyticsParams?.domain || 'https://the-foldie.com';
      const domain = targetDomain.replace(/[^a-zA-Z0-9]/g, '-');
      const filename = `organic-traffic-${domain}-${timestamp}.json`;
      
              const output = {
          timestamp: new Date().toISOString(),
          domain: targetDomain,
          source: 'Organic Overview Page',
        metrics,
        extractionMethod: 'Dynamic Content Capture'
      };
      
              // Sauvegarde
        fs.writeFileSync(filename, JSON.stringify(output, null, 2));
        console.log(`💾 Données organiques sauvegardées: ${filename}`);
      
      // Affichage des résultats
      this.displayOrganicResults(metrics);
      
      return metrics;
      
    } catch (error) {
      console.error('💥 Erreur analyse organique:', error.message);
    } finally {
      await this.close();
    }
  }
  
  displayOrganicResults(metrics) {
    console.log('\n🎯 RÉSULTATS TRAFIC ORGANIQUE:');
    console.log('═══════════════════════════════════════');
    
    if (metrics && metrics.jsData && metrics.jsData.extractedMetrics) {
      const extracted = metrics.jsData.extractedMetrics;
      
      if (extracted.length > 0) {
        console.log('\n📊 MÉTRIQUES EXTRAITES:');
        extracted.forEach(metric => {
          console.log(`   🔸 ${metric.type}: ${metric.value}`);
          console.log(`      📝 Contexte: ${metric.fullText.substring(0, 100)}...`);
        });
      }
    }
    
    if (metrics && metrics.htmlMetrics) {
      console.log('\n📈 MÉTRIQUES HTML:');
      Object.entries(metrics.htmlMetrics).forEach(([key, value]) => {
        console.log(`   ✅ ${key}: ${value}`);
      });
    }
    
    // Chercher spécifiquement "60.1k"
    const allContent = JSON.stringify(metrics);
    if (allContent.includes('60.1') || allContent.includes('60,1')) {
      console.log('\n🎯 VALEUR 60.1 TROUVÉE !');
      const matches = allContent.match(/60[.,]1[KMkm]?/g);
      if (matches) {
        matches.forEach(match => {
          console.log(`   ⭐ ${match}`);
        });
      }
    }
  }
}

// Lancement du script
async function runOrganicAnalysis() {
  const scraper = new DynamicMetricsScraper();
  await scraper.fullOrganicTrafficAnalysis();
}

export { DynamicMetricsScraper, runOrganicAnalysis };

if (import.meta.url === `file://${process.argv[1]}`) {
  runOrganicAnalysis();
}