import fs from 'fs';

class CustomTrafficTracker {
  
  constructor() {
    this.metrics = {};
  }
  
  // Permet à l'utilisateur de saisir manuellement les métriques
  addManualMetric(name, value, source = 'Manual Entry', notes = '') {
    this.metrics[name] = {
      value,
      source,
      timestamp: new Date().toISOString(),
      notes
    };
    
    console.log(`✅ Métrique ajoutée: ${name} = ${value}`);
  }
  
  // Ajoute la métrique organic traffic de 60.1k
  addOrganicTraffic(value = '60.1k', source = 'SEMrush Visual', notes = '') {
    this.addManualMetric('organicTraffic', value, source, notes);
  }
  
  // Sauvegarde le tracking personnalisé
  saveTracking(domain = 'https://the-foldie.com') {
    const output = {
      timestamp: new Date().toISOString(),
      domain,
      metrics: this.metrics,
      totalMetrics: Object.keys(this.metrics).length,
      summary: this.generateSummary()
    };
    
    const filename = `custom-tracking-${domain.replace(/[^a-zA-Z0-9]/g, '-')}-${Date.now()}.json`;
    fs.writeFileSync(filename, JSON.stringify(output, null, 2));
    
    console.log(`💾 Tracking sauvegardé: ${filename}`);
    return filename;
  }
  
  generateSummary() {
    const summary = [];
    Object.entries(this.metrics).forEach(([key, data]) => {
      summary.push(`${key}: ${data.value} (${data.source})`);
    });
    return summary;
  }
  
  // Affiche un résumé
  displayMetrics() {
    console.log('\n📊 MÉTRIQUES TRACKÉES:');
    console.log('═══════════════════════════════════════');
    
    if (Object.keys(this.metrics).length === 0) {
      console.log('⚠️  Aucune métrique ajoutée');
      return;
    }
    
    Object.entries(this.metrics).forEach(([name, data]) => {
      console.log(`\n🔸 ${name}:`);
      console.log(`   📊 Valeur: ${data.value}`);
      console.log(`   📂 Source: ${data.source}`);
      console.log(`   ⏰ Date: ${data.timestamp}`);
      if (data.notes) {
        console.log(`   📝 Notes: ${data.notes}`);
      }
    });
  }
}

// Fonction pour créer un tracking avec la valeur 60.1k
function create60kTracking() {
  console.log('🎯 CRÉATION DU TRACKING AVEC 60.1K');
  console.log('═══════════════════════════════════════');
  
  const tracker = new CustomTrafficTracker();
  
  // Ajouter la métrique principale
  tracker.addOrganicTraffic('60.1k', 'SEMrush Dashboard', 'Valeur observée visuellement sur SEMrush');
  
  // Ajouter d'autres métriques possibles
  tracker.addManualMetric('domain', 'https://the-foldie.com', 'User Input', 'Domaine analysé');
  tracker.addManualMetric('analysisDate', new Date().toISOString().split('T')[0], 'System', 'Date de l\'analyse');
  tracker.addManualMetric('tool', 'SEMrush via NoxTools', 'System', 'Outil utilisé');
  
  // Affichage et sauvegarde
  tracker.displayMetrics();
  const filename = tracker.saveTracking();
  
  console.log('\n🎉 TRACKING CRÉÉ AVEC SUCCÈS !');
  console.log(`📄 Fichier: ${filename}`);
  
  return tracker;
}

// Interface en ligne de commande
function interactiveTracker() {
  console.log('🚀 TRACKER INTERACTIF DE MÉTRIQUES SEO');
  console.log('═══════════════════════════════════════════════════');
  console.log('💡 Exemple d\'utilisation:');
  console.log('   node src/custom-60k-tracker.js organic-traffic 60.1k');
  console.log('   node src/custom-60k-tracker.js backlinks 1.2k');
  console.log('   node src/custom-60k-tracker.js keywords 500');
  
  const args = process.argv.slice(2);
  
  if (args.length >= 2) {
    const metricName = args[0];
    const metricValue = args[1];
    const metricSource = args[2] || 'Manual Entry';
    
    const tracker = new CustomTrafficTracker();
    tracker.addManualMetric(metricName, metricValue, metricSource);
    tracker.displayMetrics();
    tracker.saveTracking();
  } else {
    // Mode par défaut: créer le tracking avec 60.1k
    create60kTracking();
  }
}

export { CustomTrafficTracker, create60kTracking };

if (import.meta.url === `file://${process.argv[1]}`) {
  interactiveTracker();
}