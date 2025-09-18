/**
 * Serveur Dashboard TrendTrack
 */

import { APIServer } from './src/api/server.js';

async function main() {
  console.log('🚀 Démarrage du Dashboard TrendTrack...\n');

  try {
    // Créer et démarrer le serveur API
    const server = new APIServer(3000);
    await server.start();

    console.log('\n📊 Dashboard accessible sur:');
    console.log('   🌐 Interface web: http://localhost:3000');
    console.log('   🔗 API REST: http://localhost:3000/api');
    console.log('   📖 Documentation: http://localhost:3000/api/docs');
    
    console.log('\n🔑 Clés API:');
    console.log('   🔐 Admin: trendtrack-admin-2024');
    console.log('   📝 Exemple: curl -H "X-API-Key: trendtrack-admin-2024" http://localhost:3000/api/stats');
    
    console.log('\n📋 Endpoints disponibles:');
    console.log('   GET  /api/stats                    - Statistiques générales');
    console.log('   GET  /api/shops                    - Liste des boutiques (avec pagination)');
    console.log('   GET  /api/shops/top                - Top boutiques par Live Ads');
    console.log('   GET  /api/shops/search?q=query     - Recherche de boutiques');
    console.log('   GET  /api/shops/category/:category - Boutiques par catégorie');
    console.log('   GET  /api/shops/domain/:domain     - Boutiques par domaine');
    console.log('   GET  /api/domains                  - Domaines uniques');
    console.log('   GET  /api/stats/projects           - Statistiques par projet');
    
    console.log('\n🔒 Endpoints sécurisés (nécessitent une clé API):');
    console.log('   POST   /api/secure/shops           - Ajouter une boutique');
    console.log('   PUT    /api/secure/shops/:id       - Modifier une boutique');
    console.log('   DELETE /api/secure/shops/:id       - Supprimer une boutique');
    console.log('   POST   /api/secure/projects        - Créer un projet partagé');
    console.log('   GET    /api/secure/projects        - Lister les projets');
    console.log('   GET    /api/secure/sessions        - Sessions de scraping');
    
    console.log('\n💡 Exemples d\'utilisation:');
    console.log('   # Récupérer les statistiques');
    console.log('   curl http://localhost:3000/api/stats');
    console.log('');
    console.log('   # Récupérer les top 10 boutiques');
    console.log('   curl http://localhost:3000/api/shops/top?limit=10');
    console.log('');
    console.log('   # Rechercher des boutiques');
    console.log('   curl "http://localhost:3000/api/shops/search?q=fashion"');
    console.log('');
    console.log('   # Ajouter une boutique (avec clé API)');
    console.log('   curl -X POST -H "Content-Type: application/json" \\');
    console.log('        -H "X-API-Key: trendtrack-admin-2024" \\');
    console.log('        -d \'{"shopName":"Test Shop","shopUrl":"https://test.com"}\' \\');
    console.log('        http://localhost:3000/api/secure/shops');
    
    console.log('\n🎯 Le dashboard est maintenant opérationnel !');
    console.log('   Ouvrez http://localhost:3000 dans votre navigateur');
    console.log('   Appuyez sur Ctrl+C pour arrêter le serveur\n');

  } catch (error) {
    console.error('❌ Erreur lors du démarrage du dashboard:', error.message);
    process.exit(1);
  }
}

// Gestion de l'arrêt propre
process.on('SIGINT', () => {
  console.log('\n🛑 Arrêt du dashboard...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Arrêt du dashboard...');
  process.exit(0);
});

// Démarrer le serveur
main(); 