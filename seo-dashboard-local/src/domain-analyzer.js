import { scrapeDomain, scrapeMultipleDomains } from './noxtools-scraper.js';

// Exemples d'utilisation simple

// 1. Analyser un seul domaine
async function analyzeSingleDomain() {
  console.log('🔍 Analyse d\'un domaine unique...\n');
  
  const domain = 'https://example.com'; // ← Change ici le domaine à analyser
  const result = await scrapeDomain(domain);
  
  if (result) {
    console.log('\n✅ Analyse terminée !');
    console.log('📊 Résumé des données récupérées:');
    console.log(`- Domaine: ${result.data.analyzedDomain || 'N/A'}`);
    console.log(`- Métriques de trafic: ${result.data.trafficMetrics?.length || 0}`);
    console.log(`- Mots-clés: ${result.data.organicKeywords?.length || 0}`);
    console.log(`- Backlinks: ${result.data.backlinks?.length || 0}`);
  }
}

// 2. Analyser plusieurs domaines
async function analyzeMultipleDomains() {
  console.log('🔍 Analyse de plusieurs domaines...\n');
  
  const domains = [
    'https://example.com',
    'https://google.com',
    'https://github.com'
  ]; // ← Ajoute tes domaines ici
  
  const results = await scrapeMultipleDomains(domains);
  
  console.log('\n✅ Analyses terminées !');
  console.log(`📊 ${results.length} domaines analysés avec succès`);
}

// 3. Script personnalisé
async function customAnalysis() {
  // Domaines à analyser (modifie cette liste)
  const targetDomains = [
    'https://the-foldie.com',
    // Ajoute d'autres domaines ici
  ];
  
  console.log('🚀 Analyse personnalisée démarrée...\n');
  
  for (const domain of targetDomains) {
    console.log(`🎯 Analyse de: ${domain}`);
    
    try {
      const result = await scrapeDomain(domain);
      
      if (result && result.data) {
        // Traitement personnalisé des données
        console.log(`✅ ${domain} analysé avec succès`);
        
        // Exemple : afficher les métriques principales
        if (result.data.trafficMetrics) {
          console.log(`📈 ${result.data.trafficMetrics.length} métriques trouvées`);
        }
        
        // Exemple : chercher des mots-clés spécifiques
        if (result.data.organicKeywords) {
          const keywords = result.data.organicKeywords;
          console.log(`🔑 ${keywords.length} mots-clés organiques`);
        }
        
      } else {
        console.log(`❌ Échec de l'analyse pour: ${domain}`);
      }
      
    } catch (error) {
      console.error(`💥 Erreur pour ${domain}:`, error.message);
    }
    
    console.log(''); // Ligne vide pour lisibilité
  }
  
  console.log('🎉 Analyse personnalisée terminée !');
}

// Choisir quelle fonction exécuter
async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || 'single';
  
  switch (mode) {
    case 'single':
      await analyzeSingleDomain();
      break;
    case 'multiple':
      await analyzeMultipleDomains();
      break;
    case 'custom':
      await customAnalysis();
      break;
    default:
      console.log(`
🔧 Usage:
  node src/domain-analyzer.js single    # Analyser un domaine
  node src/domain-analyzer.js multiple  # Analyser plusieurs domaines  
  node src/domain-analyzer.js custom    # Analyse personnalisée
      `);
  }
}

// Exécution
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}