import fs from 'fs';
import path from 'path';

class SEOMetricsExtractor {
  
  constructor() {
    // Patterns pour identifier les métriques SEO importantes
    this.metricsPatterns = {
      // Traffic organiques
      organicTraffic: [
        /organic\s+(?:search\s+)?traffic[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /organic\s+visits[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /organic\s+users[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i
      ],
      
      // Mots-clés organiques
      organicKeywords: [
        /organic\s+keywords[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /organic\s+search\s+terms[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /total\s+keywords[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i
      ],
      
      // Backlinks
      backlinks: [
        /backlinks[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /referring\s+domains[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /external\s+links[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i
      ],
      
      // Authority Score
      authorityScore: [
        /authority\s+score[:\s]*([0-9]+)/i,
        /domain\s+authority[:\s]*([0-9]+)/i,
        /as[:\s]*([0-9]+)/i
      ],
      
      // Position moyenne
      avgPosition: [
        /average\s+position[:\s]*([0-9]+\.?[0-9]*)/i,
        /avg\s+position[:\s]*([0-9]+\.?[0-9]*)/i,
        /mean\s+position[:\s]*([0-9]+\.?[0-9]*)/i
      ],
      
      // Pages indexées
      indexedPages: [
        /indexed\s+pages[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i,
        /pages\s+in\s+index[:\s]*([0-9]+\.?[0-9]*[KMkm]?)/i
      ]
    };
  }
  
  // Extrait les métriques d'un fichier JSON analytics
  extractFromFile(filePath) {
    console.log(`📊 Extraction des métriques SEO depuis: ${path.basename(filePath)}`);
    
    try {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      const extractedMetrics = this.extractMetrics(data);
      
      console.log('\n🎯 MÉTRIQUES SEO EXTRAITES:');
      console.log('═══════════════════════════════════════');
      
      if (Object.keys(extractedMetrics).length > 0) {
        Object.entries(extractedMetrics).forEach(([metric, value]) => {
          console.log(`📈 ${this.formatMetricName(metric)}: ${value}`);
        });
      } else {
        console.log('⚠️  Aucune métrique numérique trouvée');
        console.log('🔍 Recherche de valeurs dans le contenu brut...');
        this.searchRawNumbers(data);
      }
      
      return extractedMetrics;
      
    } catch (error) {
      console.error('❌ Erreur lecture fichier:', error.message);
      return {};
    }
  }
  
  // Extrait les métriques des données JSON
  extractMetrics(data) {
    const metrics = {};
    const allText = this.getAllTextContent(data);
    
    // Chercher chaque pattern de métrique
    Object.entries(this.metricsPatterns).forEach(([metricName, patterns]) => {
      for (const pattern of patterns) {
        const match = allText.match(pattern);
        if (match && match[1]) {
          metrics[metricName] = match[1];
          break; // Prendre la première correspondance trouvée
        }
      }
    });
    
    return metrics;
  }
  
  // Récupère tout le contenu textuel des données JSON
  getAllTextContent(obj, texts = []) {
    if (typeof obj === 'string') {
      texts.push(obj);
    } else if (Array.isArray(obj)) {
      obj.forEach(item => this.getAllTextContent(item, texts));
    } else if (obj && typeof obj === 'object') {
      Object.values(obj).forEach(value => this.getAllTextContent(value, texts));
    }
    
    return texts.join(' ');
  }
  
  // Recherche des nombres dans le contenu brut
  searchRawNumbers(data) {
    const allText = this.getAllTextContent(data);
    
    // Chercher tous les nombres avec K/M
    const numberMatches = allText.match(/\b\d+\.?\d*[KMkm]\b/g);
    if (numberMatches) {
      console.log('\n🔍 NOMBRES TROUVÉS:');
      const uniqueNumbers = [...new Set(numberMatches)];
      uniqueNumbers.forEach(num => {
        console.log(`   📊 ${num}`);
      });
    }
    
    // Chercher des mots-clés SEO suivis de nombres
    const seoKeywords = ['traffic', 'keywords', 'backlinks', 'visitors', 'sessions', 'users', 'organic', 'pages'];
    
    console.log('\n🎯 CONTEXTE AUTOUR DES MOTS-CLÉS SEO:');
    seoKeywords.forEach(keyword => {
      const regex = new RegExp(`${keyword}[^0-9]*([0-9]+\\.?[0-9]*[KMkm]?)`, 'gi');
      const matches = [...allText.matchAll(regex)];
      
      matches.forEach(match => {
        console.log(`   🔸 ${keyword}: ${match[1]}`);
      });
    });
  }
  
  // Formate le nom de la métrique pour l'affichage
  formatMetricName(metricName) {
    const nameMap = {
      organicTraffic: 'Trafic Organique',
      organicKeywords: 'Mots-clés Organiques', 
      backlinks: 'Backlinks',
      authorityScore: 'Score d\'Autorité',
      avgPosition: 'Position Moyenne',
      indexedPages: 'Pages Indexées'
    };
    
    return nameMap[metricName] || metricName;
  }
  
  // Sauvegarde les métriques extraites
  saveMetrics(metrics, originalFileName) {
    const outputFileName = originalFileName.replace('.json', '-metrics.json');
    
    const output = {
      timestamp: new Date().toISOString(),
      originalFile: originalFileName,
      extractedMetrics: metrics,
      summary: this.generateSummary(metrics)
    };
    
    fs.writeFileSync(outputFileName, JSON.stringify(output, null, 2));
    console.log(`\n💾 Métriques sauvegardées: ${outputFileName}`);
    
    return outputFileName;
  }
  
  // Génère un résumé des métriques
  generateSummary(metrics) {
    const summary = [];
    
    Object.entries(metrics).forEach(([key, value]) => {
      summary.push(`${this.formatMetricName(key)}: ${value}`);
    });
    
    return summary.length > 0 ? summary : ['Aucune métrique extraite'];
  }
}

// Fonction pour analyser le fichier le plus récent
function analyzeLatestFile() {
  console.log('🔍 Recherche du fichier analytics le plus récent...');
  
  const files = fs.readdirSync('.')
    .filter(file => file.startsWith('analytics-') && file.endsWith('.json'))
    .sort((a, b) => {
      const timeA = fs.statSync(a).mtime;
      const timeB = fs.statSync(b).mtime;
      return timeB - timeA; // Plus récent en premier
    });
  
  if (files.length === 0) {
    console.log('❌ Aucun fichier analytics trouvé');
    return;
  }
  
  const latestFile = files[0];
  console.log(`📂 Fichier le plus récent: ${latestFile}\n`);
  
  const extractor = new SEOMetricsExtractor();
  const metrics = extractor.extractFromFile(latestFile);
  
  if (Object.keys(metrics).length > 0) {
    extractor.saveMetrics(metrics, latestFile);
  }
}

// Fonction pour analyser un fichier spécifique
function analyzeSpecificFile(fileName) {
  if (!fs.existsSync(fileName)) {
    console.log(`❌ Fichier non trouvé: ${fileName}`);
    return;
  }
  
  const extractor = new SEOMetricsExtractor();
  const metrics = extractor.extractFromFile(fileName);
  
  if (Object.keys(metrics).length > 0) {
    extractor.saveMetrics(metrics, fileName);
  }
}

// Script principal
if (import.meta.url === `file://${process.argv[1]}`) {
  const fileName = process.argv[2];
  
  if (fileName) {
    analyzeSpecificFile(fileName);
  } else {
    analyzeLatestFile();
  }
}

export { SEOMetricsExtractor, analyzeLatestFile, analyzeSpecificFile };