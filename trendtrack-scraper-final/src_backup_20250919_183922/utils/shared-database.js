/**
 * Utilitaire pour partager la base de données entre projets
 */

import { DatabaseManager } from '../database/database-manager.js';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

export class SharedDatabase {
  constructor(dbPath = './data/trendtrack.db') {
    this.dbPath = dbPath;
    this.dbManager = new DatabaseManager(dbPath);
  }

  /**
   * Initialise la base de données partagée
   */
  async init() {
    try {
      await this.dbManager.init();
      console.log('✅ Base de données partagée initialisée');
      return true;
    } catch (error) {
      console.error('❌ Erreur initialisation base partagée:', error.message);
      return false;
    }
  }

  /**
   * Crée un nouveau projet partagé
   */
  async createProject(projectName, projectPath) {
    try {
      const apiKey = this.generateAPIKey();
      const projectId = await this.dbManager.createSharedProject(projectName, projectPath, apiKey);
      
      console.log(`✅ Projet "${projectName}" créé avec succès`);
      console.log(`🔑 Clé API: ${apiKey}`);
      console.log(`📁 Chemin: ${projectPath}`);
      
      return {
        projectId,
        apiKey,
        projectName,
        projectPath
      };
    } catch (error) {
      console.error('❌ Erreur création projet:', error.message);
      return null;
    }
  }

  /**
   * Liste tous les projets partagés
   */
  async listProjects() {
    try {
      const projects = await this.dbManager.getSharedProjects();
      return projects;
    } catch (error) {
      console.error('❌ Erreur liste projets:', error.message);
      return [];
    }
  }

  /**
   * Ajoute des données depuis un autre projet
   */
  async addDataFromProject(projectSource, shopsData) {
    try {
      const stmt = this.dbManager.db.prepare(`
        INSERT OR REPLACE INTO shops 
        (shop_name, shop_url, creation_date, category, monthly_visits, monthly_revenue, live_ads, page_number, updated_at, project_source, external_id, metadata, scraping_status, scraping_last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime.now(timezone.utc).isoformat(), ?, ?, ?, ?, ?)
      `);

      const insert = this.dbManager.db.transaction((shops) => {
        for (const shop of shops) {
          stmt.run([
            shop.shopName || shop.shop_name || '',
            shop.shopUrl || shop.shop_url || '',
            shop.creationDate || shop.creation_date || '',
            shop.category || '',
            shop.monthlyVisits || shop.monthly_visits || '',
            shop.monthlyRevenue || shop.monthly_revenue || '',
            parseInt(shop.liveAds || shop.live_ads) || 0,
            shop.page || shop.page_number || 1,
            projectSource,
            shop.externalId || shop.external_id || null,
            shop.metadata ? JSON.stringify(shop.metadata) : null,
            shop.scrapingStatus || shop.scraping_status || null,
            shop.scrapingLastUpdate || shop.scraping_last_update || null
          ]);
        }
      });

      insert(shopsData);
      console.log(`✅ ${shopsData.length} boutiques ajoutées depuis ${projectSource}`);
      return true;
    } catch (error) {
      console.error('❌ Erreur ajout données projet:', error.message);
      return false;
    }
  }

  /**
   * Récupère les données par projet
   */
  async getDataByProject(projectSource) {
    try {
      const stmt = this.dbManager.db.prepare(`
        SELECT * FROM shops 
        WHERE project_source = ?
        ORDER BY live_ads DESC, scraped_at DESC
      `);
      return stmt.all(projectSource);
    } catch (error) {
      console.error('❌ Erreur récupération données projet:', error.message);
      return [];
    }
  }

  /**
   * Récupère les données par domaine (clé unique)
   */
  async getDataByDomain(domain) {
    try {
      const stmt = this.dbManager.db.prepare(`
        SELECT * FROM shops 
        WHERE shop_domain = ?
        ORDER BY scraped_at DESC
      `);
      return stmt.all(domain);
    } catch (error) {
      console.error('❌ Erreur récupération par domaine:', error.message);
      return [];
    }
  }

  /**
   * Met à jour les données d'un domaine
   */
  async updateDomainData(domain, newData) {
    try {
      const stmt = this.dbManager.db.prepare(`
        UPDATE shops 
        SET shop_name = ?, category = ?, monthly_visits = ?, monthly_revenue = ?, 
            live_ads = ?, updated_at = datetime.now(timezone.utc).isoformat(), metadata = ?
        WHERE shop_domain = ?
      `);

      const result = stmt.run([
        newData.shopName || '',
        newData.category || '',
        newData.monthlyVisits || '',
        newData.monthlyRevenue || '',
        parseInt(newData.liveAds) || 0,
        newData.metadata ? JSON.stringify(newData.metadata) : null,
        domain
      ]);

      return result.changes > 0;
    } catch (error) {
      console.error('❌ Erreur mise à jour domaine:', error.message);
      return false;
    }
  }

  /**
   * Exporte les données vers un fichier
   */
  async exportData(format = 'json', projectSource = null) {
    try {
      let query = 'SELECT * FROM shops';
      let params = [];
      
      if (projectSource) {
        query += ' WHERE project_source = ?';
        params.push(projectSource);
      }
      
      query += ' ORDER BY live_ads DESC, scraped_at DESC';
      
      const stmt = this.dbManager.db.prepare(query);
      const data = stmt.all(...params);
      
      const exportDir = './exports';
      if (!fs.existsSync(exportDir)) {
        fs.mkdirSync(exportDir, { recursive: true });
      }
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `trendtrack-export-${timestamp}.${format}`;
      const filepath = path.join(exportDir, filename);
      
      if (format === 'json') {
        fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
      } else if (format === 'csv') {
        const csv = this.convertToCSV(data);
        fs.writeFileSync(filepath, csv);
      }
      
      console.log(`✅ Données exportées vers: ${filepath}`);
      return filepath;
    } catch (error) {
      console.error('❌ Erreur export données:', error.message);
      return null;
    }
  }

  /**
   * Convertit les données en CSV
   */
  convertToCSV(data) {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }

  /**
   * Génère une clé API unique
   */
  generateAPIKey() {
    return 'tt_' + crypto.randomBytes(16).toString('hex');
  }

  /**
   * Vérifie la validité d'une clé API
   */
  async validateAPIKey(apiKey) {
    try {
      const stmt = this.dbManager.db.prepare(`
        SELECT * FROM shared_projects 
        WHERE api_key = ? AND is_active = 1
      `);
      const project = stmt.get(apiKey);
      return project !== undefined;
    } catch (error) {
      console.error('❌ Erreur validation clé API:', error.message);
      return false;
    }
  }

  /**
   * Ferme la connexion
   */
  close() {
    if (this.dbManager) {
      this.dbManager.close();
    }
  }
}

/**
 * Script de commande pour gérer les projets partagés
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  const sharedDB = new SharedDatabase();
  await sharedDB.init();
  
  switch (command) {
    case 'create-project':
      const projectName = args[1];
      const projectPath = args[2];
      
      if (!projectName || !projectPath) {
        console.log('Usage: node shared-database.js create-project <nom> <chemin>');
        process.exit(1);
      }
      
      const project = await sharedDB.createProject(projectName, projectPath);
      if (project) {
        console.log('\n📋 Informations du projet:');
        console.log(JSON.stringify(project, null, 2));
      }
      break;
      
    case 'list-projects':
      const projects = await sharedDB.listProjects();
      console.log('\n📋 Projets partagés:');
      projects.forEach(project => {
        console.log(`   ${project.project_name} (${project.api_key})`);
        console.log(`   Chemin: ${project.project_path}`);
        console.log(`   Créé: ${project.created_at}`);
        console.log('');
      });
      break;
      
    case 'export':
      const format = args[1] || 'json';
      const projectSource = args[2];
      
      const filepath = await sharedDB.exportData(format, projectSource);
      if (filepath) {
        console.log(`✅ Export terminé: ${filepath}`);
      }
      break;
      
    default:
      console.log('Usage:');
      console.log('  node shared-database.js create-project <nom> <chemin>');
      console.log('  node shared-database.js list-projects');
      console.log('  node shared-database.js export [format] [project]');
      break;
  }
  
  sharedDB.close();
}

// Exécuter si appelé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
} 
  main();
} 