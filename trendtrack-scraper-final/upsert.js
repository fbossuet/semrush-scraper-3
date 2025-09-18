#!/usr/bin/env node

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = './data/trendtrack.db';

console.log('🔍 Diagnostic de l\'erreur FOREIGN KEY constraint failed...');

if (!fs.existsSync(DB_PATH)) {
  console.log('❌ Base de données non trouvée:', DB_PATH);
  process.exit(1);
}

if (!fs.existsSync('debug-extracted-data.json')) {
  console.log('❌ Fichier debug-extracted-data.json non trouvé');
  console.log('💡 Exécutez d\'abord: node debug-extracted-data.js');
  process.exit(1);
}

try {
  const db = new Database(DB_PATH);
  
  // Charger les données extraites
  const rawData = JSON.parse(fs.readFileSync('debug-extracted-data.json', 'utf8'));
  console.log(`📊 ${rawData.length} boutiques chargées`);
  
  if (rawData.length === 0) {
    console.log('❌ Aucune donnée à tester');
    process.exit(0);
  }
  
  const testShop = rawData[0];
  console.log('\n📋 Données de test:');
  console.log(JSON.stringify(testShop, null, 2));
  
  // Fonction d'adaptation (même que dans update-database-fixed.js)
  function adaptShopData(rawShopData) {
    return {
      shopName: rawShopData.shopName || '',
      shopUrl: rawShopData.shopUrl || '',
      creationDate: rawShopData.creationDate || '',
      category: rawShopData.category || '',
      monthlyVisits: rawShopData.monthlyVisits || '',
      monthlyRevenue: rawShopData.monthlyRevenue || '',
      liveAds: parseInt(rawShopData.liveAds) || 0,
      page: rawShopData.rowIndex || 1,
      projectSource: 'trendtrack',
      externalId: null,
      metadata: JSON.stringify({
        timestamp: rawShopData.timestamp,
        rowIndex: rawShopData.rowIndex,
        originalData: rawShopData
      }),
      scrapingStatus: 'active',
      scrapingLastUpdate: new Date().toISOString(),
      // Données analytiques (optionnelles)
      conversionRate: rawShopData.conversionRate || null,
      organicTraffic: rawShopData.organicTraffic || null,
      brandedTraffic: rawShopData.brandedTraffic || null,
      bounceRate: rawShopData.bounceRate || null,
      averageVisitDuration: rawShopData.averageVisitDuration || null
    };
  }
  
  const adaptedShop = adaptShopData(testShop);
  console.log('\n📋 Données adaptées:');
  console.log(JSON.stringify(adaptedShop, null, 2));
  
  // Test d'insertion étape par étape
  console.log('\n🧪 Test d\'insertion étape par étape...');
  
  try {
    // 1. Test insertion dans shops seulement
    console.log('1️⃣ Test insertion dans shops...');
    const shopStmt = db.prepare(`
      INSERT OR REPLACE INTO shops 
      (shop_name, shop_url, creation_date, category, monthly_visits, monthly_revenue, live_ads, page_number, updated_at, project_source, external_id, metadata, scraping_status, scraping_last_update)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat(), ?, ?, ?, ?, ?)
    `);
    
    const shopResult = shopStmt.run([
      adaptedShop.shopName,
      adaptedShop.shopUrl,
      adaptedShop.creationDate,
      adaptedShop.category,
      adaptedShop.monthlyVisits,
      adaptedShop.monthlyRevenue,
      adaptedShop.liveAds,
      adaptedShop.page,
      adaptedShop.projectSource,
      adaptedShop.externalId,
      adaptedShop.metadata,
      adaptedShop.scrapingStatus,
      adaptedShop.scrapingLastUpdate
    ]);
    
    console.log('✅ Insertion dans shops réussie, ID:', shopResult.lastInsertRowid);
    
    // 2. Test insertion dans analytics
    console.log('2️⃣ Test insertion dans analytics...');
    const analyticsStmt = db.prepare(`
      INSERT OR REPLACE INTO analytics 
      (shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, scraping_status, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat())
    `);
    
    const analyticsResult = analyticsStmt.run([
      shopResult.lastInsertRowid,
      adaptedShop.organicTraffic,
      adaptedShop.bounceRate,
      adaptedShop.averageVisitDuration,
      adaptedShop.brandedTraffic,
      adaptedShop.conversionRate,
      'completed'
    ]);
    
    console.log('✅ Insertion dans analytics réussie, ID:', analyticsResult.lastInsertRowid);
    
    // Vérifier les insertions
    const insertedShop = db.prepare('SELECT * FROM shops WHERE id = ?').get(shopResult.lastInsertRowid);
    const insertedAnalytics = db.prepare('SELECT * FROM analytics WHERE shop_id = ?').get(shopResult.lastInsertRowid);
    
    console.log('📊 Vérification des données insérées:');
    console.log('  - Shop:', insertedShop.shop_name, '| Live Ads:', insertedShop.live_ads);
    console.log('  - Analytics ID:', insertedAnalytics.id, '| Shop ID:', insertedAnalytics.shop_id);
    
    // Nettoyer le test
    db.prepare("DELETE FROM analytics WHERE shop_id = ?").run(shopResult.lastInsertRowid);
    db.prepare("DELETE FROM shops WHERE id = ?").run(shopResult.lastInsertRowid);
    console.log('✅ Test nettoyé');
    
    console.log('\n🎉 Test d\'insertion directe RÉUSSI !');
    console.log('💡 Le problème vient de la méthode upsert du shop-repository');
    
  } catch (error) {
    console.log('❌ Erreur insertion directe:', error.message);
    console.log('Détails de l\'erreur:', error);
  }
  
  // Vérifier la structure des tables
  console.log('\n🔍 Vérification de la structure des tables...');
  
  const shopsColumns = db.prepare("PRAGMA table_info(shops)").all();
  const analyticsColumns = db.prepare("PRAGMA table_info(analytics)").all();
  
  console.log('📋 Colonnes de la table shops:');
  shopsColumns.forEach(col => {
    console.log(`  - ${col.name}: ${col.type} ${col.notnull ? 'NOT NULL' : ''} ${col.pk ? 'PRIMARY KEY' : ''}`);
  });
  
  console.log('\n📋 Colonnes de la table analytics:');
  analyticsColumns.forEach(col => {
    console.log(`  - ${col.name}: ${col.type} ${col.notnull ? 'NOT NULL' : ''} ${col.pk ? 'PRIMARY KEY' : ''}`);
  });
  
  // Vérifier les contraintes de clés étrangères
  console.log('\n🔗 Contraintes de clés étrangères:');
  const foreignKeys = db.prepare("PRAGMA foreign_key_list(shops)").all();
  if (foreignKeys.length === 0) {
    console.log('✅ Aucune contrainte de clé étrangère sur la table shops');
  } else {
    console.log('❌ Contraintes de clés étrangères trouvées:');
    foreignKeys.forEach(fk => {
      console.log(`  - ${fk.from} -> ${fk.table}.${fk.to}`);
    });
  }
  
  db.close();
  console.log('\n🎉 Diagnostic terminé !');
  
} catch (error) {
  console.error('❌ Erreur:', error.message);
  process.exit(1);
}
