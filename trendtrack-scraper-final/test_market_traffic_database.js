/**
 * Test de stockage des données de trafic par pays en base de données
 */

import sqlite3 from 'sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function testMarketTrafficDatabase() {
  console.log('🧪 Test de stockage des données de trafic par pays en base de données');
  console.log('='.repeat(70));
  
  const dbPath = path.join(__dirname, 'data', 'trendtrack.db');
  console.log(`📁 Chemin de la base de données: ${dbPath}`);
  
  try {
    // Ouvrir la base de données
    console.log('\n1️⃣ Ouverture de la base de données...');
    const db = new sqlite3.Database(dbPath);
    
    // Vérifier la structure de la table shops
    console.log('\n2️⃣ Vérification de la structure de la table shops...');
    const tableInfo = await new Promise((resolve, reject) => {
      db.all("SELECT name, type FROM pragma_table_info('shops') WHERE name LIKE 'market_%' ORDER BY name;", (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    
    console.log('📋 Champs market_* dans la table shops:');
    tableInfo.forEach(field => {
      console.log(`  - ${field.name}: ${field.type}`);
    });
    
    // Vérifier que tous les champs market_* sont présents
    const expectedFields = ['market_au', 'market_ca', 'market_de', 'market_fr', 'market_uk', 'market_us'];
    const presentFields = tableInfo.map(field => field.name);
    const missingFields = expectedFields.filter(field => !presentFields.includes(field));
    
    if (missingFields.length === 0) {
      console.log('✅ Tous les champs market_* sont présents');
    } else {
      console.log(`❌ Champs manquants: ${missingFields.join(', ')}`);
    }
    
    // Vérifier les types de données
    console.log('\n3️⃣ Vérification des types de données...');
    const incorrectTypes = tableInfo.filter(field => field.type !== 'NUMERIC');
    if (incorrectTypes.length === 0) {
      console.log('✅ Tous les champs market_* ont le bon type (NUMERIC)');
    } else {
      console.log('⚠️ Champs avec des types incorrects:');
      incorrectTypes.forEach(field => {
        console.log(`  - ${field.name}: ${field.type} (attendu: NUMERIC)`);
      });
    }
    
    // Tester l'insertion de données de test
    console.log('\n4️⃣ Test d\'insertion de données de test...');
    
    // Créer une boutique de test
    const testShop = {
      shop_url: 'https://test-shop.example.com',
      shop_name: 'Test Shop Market Traffic',
      scraping_status: 'completed',
      monthly_visits: 100000,
      monthly_revenue: '$50,000',
      live_ads: '25',
      project_source: 'test',
      market_us: 45000,
      market_uk: 25000,
      market_de: 15000,
      market_ca: 10000,
      market_au: 5000,
      market_fr: 0
    };
    
    // Insérer la boutique de test
    const insertQuery = `
      INSERT INTO shops (
        shop_url, shop_name, scraping_status, monthly_visits, monthly_revenue,
        live_ads, project_source, market_us, market_uk, market_de, market_ca, market_au, market_fr
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    
    await new Promise((resolve, reject) => {
      db.run(insertQuery, [
        testShop.shop_url, testShop.shop_name, testShop.scraping_status,
        testShop.monthly_visits, testShop.monthly_revenue, testShop.live_ads,
        testShop.project_source, testShop.market_us, testShop.market_uk,
        testShop.market_de, testShop.market_ca, testShop.market_au, testShop.market_fr
      ], function(err) {
        if (err) reject(err);
        else resolve(this.lastID);
      });
    });
    
    console.log('✅ Boutique de test insérée');
    
    // Vérifier que les données ont été correctement stockées
    console.log('\n5️⃣ Vérification des données stockées...');
    const selectQuery = `
      SELECT shop_name, market_us, market_uk, market_de, market_ca, market_au, market_fr
      FROM shops WHERE shop_name = ?
    `;
    
    const storedData = await new Promise((resolve, reject) => {
      db.get(selectQuery, [testShop.shop_name], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
    
    if (storedData) {
      console.log('📊 Données stockées:');
      console.log(`  - Nom: ${storedData.shop_name}`);
      console.log(`  - Market US: ${storedData.market_us}`);
      console.log(`  - Market UK: ${storedData.market_uk}`);
      console.log(`  - Market DE: ${storedData.market_de}`);
      console.log(`  - Market CA: ${storedData.market_ca}`);
      console.log(`  - Market AU: ${storedData.market_au}`);
      console.log(`  - Market FR: ${storedData.market_fr}`);
      
      // Vérifier que les valeurs correspondent
      const valuesMatch = (
        storedData.market_us === testShop.market_us &&
        storedData.market_uk === testShop.market_uk &&
        storedData.market_de === testShop.market_de &&
        storedData.market_ca === testShop.market_ca &&
        storedData.market_au === testShop.market_au &&
        storedData.market_fr === testShop.market_fr
      );
      
      if (valuesMatch) {
        console.log('✅ Toutes les valeurs correspondent');
      } else {
        console.log('❌ Certaines valeurs ne correspondent pas');
      }
    } else {
      console.log('❌ Aucune donnée trouvée');
    }
    
    // Nettoyer les données de test
    console.log('\n6️⃣ Nettoyage des données de test...');
    await new Promise((resolve, reject) => {
      db.run("DELETE FROM shops WHERE shop_name = ?", [testShop.shop_name], (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    console.log('✅ Données de test supprimées');
    
    // Fermer la base de données
    db.close();
    
    console.log('\n✅ Tests de base de données terminés avec succès!');
    
  } catch (error) {
    console.error('\n❌ Erreur lors des tests de base de données:', error.message);
    console.error('Stack trace:', error.stack);
  }
}

// Exécuter les tests si le script est appelé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  testMarketTrafficDatabase()
    .then(() => {
      console.log('\n🎉 Tests terminés');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Erreur fatale:', error.message);
      process.exit(1);
    });
}

export { testMarketTrafficDatabase };

