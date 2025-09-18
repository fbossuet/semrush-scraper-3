#!/usr/bin/env node

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = './data/trendtrack.db';

/**
 * Script de vérification et correction de la base de données
 */
async function checkDatabase() {
  console.log('🔍 Vérification de la base de données...');
  
  if (!fs.existsSync(DB_PATH)) {
    console.log('❌ Base de données non trouvée:', DB_PATH);
    return;
  }

  try {
    const db = new Database(DB_PATH);
    
    // Vérifier la structure de la table shops
    console.log('\n📋 Structure de la table shops:');
    const tableInfo = db.prepare("PRAGMA table_info(shops)").all();
    console.table(tableInfo);
    
    // Vérifier les contraintes
    console.log('\n🔗 Contraintes de la table shops:');
    const foreignKeys = db.prepare("PRAGMA foreign_key_list(shops)").all();
    if (foreignKeys.length > 0) {
      console.table(foreignKeys);
    } else {
      console.log('✅ Aucune contrainte de clé étrangère trouvée');
    }
    
    // Vérifier les index
    console.log('\n📊 Index de la table shops:');
    const indexes = db.prepare("PRAGMA index_list(shops)").all();
    console.table(indexes);
    
    // Compter les enregistrements
    console.log('\n📈 Statistiques:');
    const count = db.prepare("SELECT COUNT(*) as total FROM shops").get();
    console.log(`Total boutiques: ${count.total}`);
    
    // Vérifier les données problématiques
    console.log('\n🔍 Vérification des données problématiques:');
    
    // URLs vides ou nulles
    const emptyUrls = db.prepare("SELECT COUNT(*) as count FROM shops WHERE shop_url IS NULL OR shop_url = ''").get();
    console.log(`URLs vides: ${emptyUrls.count}`);
    
    // Noms vides
    const emptyNames = db.prepare("SELECT COUNT(*) as count FROM shops WHERE shop_name IS NULL OR shop_name = ''").get();
    console.log(`Noms vides: ${emptyNames.count}`);
    
    // Vérifier les colonnes manquantes
    const columns = tableInfo.map(col => col.name);
    const expectedColumns = [
      'id', 'shop_name', 'shop_url', 'shop_domain', 'creation_date', 'category',
      'monthly_visits', 'monthly_revenue', 'live_ads', 'page_number', 'scraped_at',
      'updated_at', 'project_source', 'external_id', 'metadata', 'conversion_rate',
      'scraping_status', 'scraping_last_update', 'organic_traffic', 'branded_traffic',
      'bounce_rate', 'average_visit_duration'
    ];
    
    const missingColumns = expectedColumns.filter(col => !columns.includes(col));
    const extraColumns = columns.filter(col => !expectedColumns.includes(col));
    
    if (missingColumns.length > 0) {
      console.log('❌ Colonnes manquantes:', missingColumns);
    }
    
    if (extraColumns.length > 0) {
      console.log('⚠️ Colonnes supplémentaires:', extraColumns);
    }
    
    if (missingColumns.length === 0 && extraColumns.length === 0) {
      console.log('✅ Structure de la table conforme');
    }
    
    db.close();
    
  } catch (error) {
    console.error('❌ Erreur lors de la vérification:', error.message);
  }
}

// Exécuter la vérification
checkDatabase();
