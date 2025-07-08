import fs from 'fs';

class TrafficManualTracker {
  
  constructor() {
    this.trafficData = {};
  }

  // Ajoute manuellement une valeur de traffic pour un concurrent
  addCompetitorTraffic(domain, visits, source = 'Manual Entry', additionalData = {}) {
    this.trafficData[domain] = {
      visits,
      source,
      timestamp: new Date().toISOString(),
      additionalData,
      notes: `Traffic visits value for ${domain}`
    };
    
    console.log(`✅ Traffic ajouté: ${domain} = ${visits} visits`);
  }

  // Ajoute spécifiquement les données cakesbody.com
  addCakesBodyData(visits = '846.6K', source = 'Traffic Overview Visual') {
    this.addCompetitorTraffic('cakesbody.com', visits, source, {
      metric: 'visits',
      tool: 'SEMrush Traffic Analytics',
      interface: 'Traffic Overview page',
      method: 'Manual observation'
    });
  }

  // Importe des données depuis un fichier smart-traffic
  importSmartTrafficData(filename) {
    try {
      const data = JSON.parse(fs.readFileSync(filename, 'utf8'));
      
      if (data.competitorData && Array.isArray(data.competitorData)) {
        data.competitorData.forEach(competitor => {
          const domain = competitor.domain;
          const automaticData = {
            allNumbers: competitor.allNumbers || [],
            trafficRelated: competitor.trafficRelated || [],
            foundData: competitor.foundData || {},
            automaticSource: data.source || 'Smart Traffic Scraper'
          };
          
          // Si on a déjà des données pour ce domaine, on enrichit
          if (this.trafficData[domain]) {
            this.trafficData[domain].automaticData = automaticData;
          } else {
            // Sinon on crée une entrée avec les données automatiques
            this.trafficData[domain] = {
              visits: 'Manual entry required',
              source: 'Automatic + Manual',
              timestamp: new Date().toISOString(),
              automaticData
            };
          }
        });
        
        console.log(`✅ Données automatiques importées depuis ${filename}`);
      }
    } catch (error) {
      console.error(`❌ Erreur import ${filename}:`, error.message);
    }
  }

  // Trouve le fichier smart-traffic le plus récent
  importLatestSmartTraffic() {
    try {
      const files = fs.readdirSync('.')
        .filter(file => file.startsWith('smart-traffic-') && file.endsWith('.json'))
        .sort((a, b) => {
          const timeA = fs.statSync(a).mtime;
          const timeB = fs.statSync(b).mtime;
          return timeB - timeA;
        });
      
      if (files.length > 0) {
        const latestFile = files[0];
        console.log(`📂 Import du fichier le plus récent: ${latestFile}`);
        this.importSmartTrafficData(latestFile);
      } else {
        console.log('⚠️ Aucun fichier smart-traffic trouvé');
      }
    } catch (error) {
      console.error('❌ Erreur recherche fichiers:', error.message);
    }
  }

  // Sauvegarde le tracking traffic
  saveTrafficTracking() {
    const output = {
      timestamp: new Date().toISOString(),
      source: 'Traffic Manual Tracker',
      trafficData: this.trafficData,
      summary: this.generateSummary(),
      totalCompetitors: Object.keys(this.trafficData).length
    };
    
    const filename = `traffic-tracking-${Date.now()}.json`;
    fs.writeFileSync(filename, JSON.stringify(output, null, 2));
    
    console.log(`💾 Traffic tracking sauvegardé: ${filename}`);
    return filename;
  }

  generateSummary() {
    return Object.entries(this.trafficData).map(([domain, data]) => 
      `${domain}: ${data.visits} (${data.source})`
    );
  }

  // Affiche le tracking
  displayTracking() {
    console.log('\n🚗 TRACKING TRAFFIC COMPETITORS:');
    console.log('═══════════════════════════════════════════════════');
    
    if (Object.keys(this.trafficData).length === 0) {
      console.log('⚠️ Aucun concurrent tracké');
      return;
    }
    
    Object.entries(this.trafficData).forEach(([domain, data]) => {
      console.log(`\n🔸 ${domain.toUpperCase()}:`);
      console.log(`   📊 Visits: ${data.visits}`);
      console.log(`   📂 Source: ${data.source}`);
      console.log(`   ⏰ Date: ${data.timestamp}`);
      
      if (data.additionalData) {
        console.log(`   📋 Détails: ${JSON.stringify(data.additionalData, null, 2)}`);
      }
      
      if (data.automaticData) {
        console.log(`   🤖 Données automatiques:`);
        console.log(`     • Nombres trouvés: ${data.automaticData.allNumbers?.slice(0, 10).join(', ')}...`);
        console.log(`     • Source auto: ${data.automaticData.automaticSource}`);
      }
    });
    
    // Highlight spécial pour cakesbody
    const cakesData = this.trafficData['cakesbody.com'];
    if (cakesData) {
      console.log(`\n🎉 VALEUR CAKESBODY.COM: ${cakesData.visits}`);
    }
  }

  // Trouve des valeurs proches dans les données automatiques
  findSimilarValues(targetValue) {
    console.log(`\n🔍 RECHERCHE VALEURS SIMILAIRES À "${targetValue}":`);
    
    Object.entries(this.trafficData).forEach(([domain, data]) => {
      if (data.automaticData && data.automaticData.allNumbers) {
        const similar = data.automaticData.allNumbers.filter(num => 
          num.includes(targetValue.replace(/[KMB]/i, '')) || 
          targetValue.includes(num.replace(/[KMB]/i, ''))
        );
        
        if (similar.length > 0) {
          console.log(`   ${domain}: ${similar.join(', ')}`);
        }
      }
    });
  }
}

// Fonction pour créer un tracking complet avec cakesbody
function createCakesBodyTracking() {
  console.log('🎯 CRÉATION TRACKING CAKESBODY.COM');
  console.log('═══════════════════════════════════════════════════');
  
  const tracker = new TrafficManualTracker();
  
  // Importer les données automatiques du smart scraper
  tracker.importLatestSmartTraffic();
  
  // Ajouter manuellement la valeur cakesbody
  tracker.addCakesBodyData('846.6K', 'Traffic Overview - Manual Visual Check');
  
  // Affichage et sauvegarde
  tracker.displayTracking();
  
  // Rechercher des valeurs similaires à 846
  tracker.findSimilarValues('846');
  
  const filename = tracker.saveTrafficTracking();
  
  console.log('\n🎉 TRACKING CAKESBODY CRÉÉ !');
  console.log(`📄 Fichier: ${filename}`);
  
  return tracker;
}

// Interface en ligne de commande
function interactiveTrafficTracker() {
  console.log('🚗 TRACKER INTERACTIF TRAFFIC COMPETITORS');
  console.log('═══════════════════════════════════════════════════');
  console.log('💡 Exemples d\'utilisation:');
  console.log('   node src/traffic-manual-tracker.js cakesbody.com 846.6K');
  console.log('   node src/traffic-manual-tracker.js example.com 1.2M');
  console.log('   node src/traffic-manual-tracker.js competitor.com 500K');
  
  const args = process.argv.slice(2);
  
  if (args.length >= 2) {
    const domain = args[0];
    const visits = args[1];
    const source = args[2] || 'Manual Entry';
    
    const tracker = new TrafficManualTracker();
    tracker.importLatestSmartTraffic();
    tracker.addCompetitorTraffic(domain, visits, source);
    tracker.displayTracking();
    tracker.saveTrafficTracking();
  } else {
    // Mode par défaut: créer le tracking cakesbody
    createCakesBodyTracking();
  }
}

export { TrafficManualTracker, createCakesBodyTracking };

if (import.meta.url === `file://${process.argv[1]}`) {
  interactiveTrafficTracker();
}