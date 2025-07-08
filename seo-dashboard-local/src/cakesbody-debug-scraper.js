// 🔍 Scraper Debug Spécialisé pour cakesbody.com
import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';
import fs from 'fs';

class CakesbodyDebugScraper extends NoxToolsScraper {
  
  async debugCakesbodyAnalysis() {
    console.log('🔍 DEBUG SPÉCIALISÉ CAKESBODY.COM');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // 1. Connexion
      console.log('🔑 Étape 1: Connexion NoxTools...');
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      console.log('✅ Connexion réussie');
      
      // 2. Test URL cakesbody.com
      const domain = 'cakesbody.com';
      const cleanDomain = this.cleanDomain(domain);
      const organicUrl = `https://server1.noxtools.com/analytics/organic/overview/?db=us&q=${encodeURIComponent(cleanDomain)}&searchType=domain`;
      
      console.log(`🎯 Domaine nettoyé: "${cleanDomain}"`);
      console.log(`🌐 URL générée: ${organicUrl}`);
      
      // 3. Navigation avec debug
      console.log('🚀 Navigation vers la page...');
      const response = await this.page.goto(organicUrl, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      console.log(`📡 Status HTTP: ${response.status()}`);
      console.log(`🔗 URL finale: ${this.page.url()}`);
      
      // 4. Attente prolongée pour cakesbody
      console.log('⏳ Attente spéciale pour cakesbody (20 secondes)...');
      await this.page.waitForTimeout(20000);
      
      // 5. Capture complète du contenu
      const pageContent = await this.page.textContent('body');
      const htmlContent = await this.page.content();
      
      console.log(`📄 Taille contenu texte: ${pageContent.length} caractères`);
      console.log(`📄 Taille HTML: ${htmlContent.length} caractères`);
      
      // 6. Debug spécialisé cakesbody
      console.log('\n🔍 RECHERCHE PATTERNS CAKESBODY:');
      
      // Pattern 1: Recherche "cakesbody" dans le contenu
      const cakesbodyMentions = pageContent.match(/cakesbody/gi) || [];
      console.log(`🍰 Mentions "cakesbody": ${cakesbodyMentions.length}`);
      
      // Pattern 2: Tous les nombres sur la page
      const allNumbers = pageContent.match(/\d+/g) || [];
      const numbersWithSuffix = pageContent.match(/\d+\.?\d*[KMBkm]/g) || [];
      
      console.log(`🔢 Tous les nombres: ${allNumbers.slice(0, 20).join(', ')}... (${allNumbers.length} total)`);
      console.log(`📊 Nombres avec suffixe: ${numbersWithSuffix.join(', ')}`);
      
      // Pattern 3: Mots-clés traffic/visits
      const trafficKeywords = pageContent.match(/\b(?:traffic|visits?|visitors?|organic)\b/gi) || [];
      console.log(`🚗 Mots-clés traffic: ${[...new Set(trafficKeywords)].join(', ')}`);
      
      // Pattern 4: Patterns étendus pour cakesbody
      const extendedPatterns = this.extractCakesbodyMetrics(pageContent);
      
      // 7. Recherche dans les éléments DOM
      console.log('\n🎯 RECHERCHE DOM ELEMENTS:');
      const domAnalysis = await this.page.evaluate(() => {
        const result = {
          tables: [],
          spans: [],
          divs: [],
          numbersInElements: []
        };
        
        // Chercher dans les tableaux
        document.querySelectorAll('table, .table, [class*="table"]').forEach(table => {
          const text = table.textContent;
          if (text.includes('cakesbody') || text.match(/\d+\.?\d*[KMkm]/)) {
            result.tables.push(text.substring(0, 200));
          }
        });
        
        // Chercher dans les spans avec des nombres
        document.querySelectorAll('span, div').forEach(el => {
          const text = el.textContent?.trim();
          if (text && text.match(/\d+\.?\d*[KMkm]/)) {
            result.numbersInElements.push(text);
          }
        });
        
        return result;
      });
      
      console.log(`📋 Tableaux trouvés: ${domAnalysis.tables.length}`);
      console.log(`🔢 Éléments avec nombres: ${domAnalysis.numbersInElements.slice(0, 10).join(', ')}`);
      
      // 8. Sauvegarde debug complète
      const debugOutput = {
        timestamp: new Date().toISOString(),
        domain: 'cakesbody.com',
        url: organicUrl,
        httpStatus: response.status(),
        finalUrl: this.page.url(),
        contentLength: pageContent.length,
        allNumbers: allNumbers,
        numbersWithSuffix: numbersWithSuffix,
        trafficKeywords: trafficKeywords,
        extendedPatterns: extendedPatterns,
        domAnalysis: domAnalysis,
        pageContentSample: pageContent.substring(0, 2000),
        htmlSample: htmlContent.substring(0, 2000)
      };
      
      const filename = `cakesbody-debug-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(debugOutput, null, 2));
      console.log(`\n💾 Debug sauvegardé: ${filename}`);
      
      // 9. Conclusion debug
      console.log('\n🎯 RÉSUMÉ DEBUG CAKESBODY:');
      console.log('═══════════════════════════════════════════════════');
      
      if (cakesbodyMentions.length > 0) {
        console.log('✅ Le domaine cakesbody est bien présent sur la page');
      } else {
        console.log('❌ Le domaine cakesbody N\'EST PAS mentionné sur la page');
      }
      
      if (numbersWithSuffix.length > 0) {
        console.log(`✅ Des métriques sont présentes: ${numbersWithSuffix.join(', ')}`);
      } else {
        console.log('❌ Aucune métrique avec suffixe trouvée');
      }
      
      if (allNumbers.length > 10) {
        console.log(`✅ Page contient des données (${allNumbers.length} nombres)`);
      } else {
        console.log('❌ Page semble vide de données');
      }
      
      return debugOutput;
      
    } catch (error) {
      console.error('💥 Erreur debug cakesbody:', error.message);
      console.error('📜 Stack:', error.stack);
    } finally {
      await this.close();
    }
  }
  
  extractCakesbodyMetrics(content) {
    console.log('\n🎯 PATTERNS ÉTENDUS CAKESBODY:');
    
    const patterns = {
      // Pattern 1: Format standard
      standardMetrics: content.match(/(\d+\.?\d*[KMBkm])\s*(?:visits?|visitors?|traffic|organic)/gi) || [],
      
      // Pattern 2: Format avec virgules
      commaNumbers: content.match(/(\d{1,3}(?:,\d{3})+)\s*(?:visits?|visitors?|traffic)/gi) || [],
      
      // Pattern 3: Format monthly
      monthlyVisitors: content.match(/(\d+\.?\d*[KMBkm]?)\s*monthly\s*(?:visits?|visitors?)/gi) || [],
      
      // Pattern 4: Format inverse
      reversePattern: content.match(/(?:visits?|visitors?|traffic)[:\s]+(\d+\.?\d*[KMBkm]?)/gi) || [],
      
      // Pattern 5: Contexte cakesbody spécifique
      cakesbodyContext: content.match(/cakesbody[^0-9]*(\d+\.?\d*[KMBkm]?)/gi) || [],
      
      // Pattern 6: Nombres proches de mots-clés
      proximityNumbers: this.findNumbersNearKeywords(content, ['cakesbody', 'visits', 'traffic', 'organic']),
      
      // Pattern 7: Tous les nombres entre 1000-1M (potentiels visits)
      potentialVisits: content.match(/\b([1-9]\d{3,6})\b/g) || []
    };
    
    Object.entries(patterns).forEach(([key, matches]) => {
      console.log(`   🔸 ${key}: ${Array.isArray(matches) ? matches.slice(0, 5).join(', ') : matches} (${Array.isArray(matches) ? matches.length : 1} matches)`);
    });
    
    return patterns;
  }
  
  findNumbersNearKeywords(content, keywords, proximity = 50) {
    const results = [];
    
    keywords.forEach(keyword => {
      const regex = new RegExp(keyword, 'gi');
      let match;
      
      while ((match = regex.exec(content)) !== null) {
        const start = Math.max(0, match.index - proximity);
        const end = Math.min(content.length, match.index + keyword.length + proximity);
        const context = content.substring(start, end);
        
        const numbers = context.match(/\d+\.?\d*[KMBkm]?/g) || [];
        if (numbers.length > 0) {
          results.push({
            keyword: keyword,
            numbers: numbers,
            context: context.trim()
          });
        }
      }
    });
    
    return results;
  }
  
  cleanDomain(domain) {
    return domain
      .replace(/^https?:\/\//, '')  // Enlever protocole
      .replace(/\/$/, '')           // Enlever slash final
      .replace(/^www\./, '')        // Enlever www
      .toLowerCase()
      .trim();
  }
}

// Lancement du debug
async function debugCakesbody() {
  const scraper = new CakesbodyDebugScraper();
  await scraper.debugCakesbodyAnalysis();
}

export { CakesbodyDebugScraper, debugCakesbody };

if (import.meta.url === `file://${process.argv[1]}`) {
  debugCakesbody();
}