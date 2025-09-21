/**
 * Serveur API REST pour le dashboard TrendTrack
 */

import express from 'express';
import cors from 'cors';
import compression from 'compression';
import { DatabaseManager } from '../database/database-manager.js';
import { ShopRepository } from '../database/shop-repository.js';
import crypto from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class APIServer {
  constructor(port = 3000) {
    this.port = port;
    this.app = express();
    this.dbManager = null;
    this.shopRepository = null;
    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Configure le middleware
   */
  setupMiddleware() {
    // Compression gzip pour réduire la taille des réponses
    this.app.use(compression());

    // CORS pour permettre l'accès depuis d'autres domaines
    this.app.use(cors({
      origin: ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000'],
      credentials: true
    }));

    // Parser JSON avec limite de taille
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Cache HTTP pour les ressources statiques
    this.app.use(express.static(path.join(__dirname, '../dashboard'), {
      maxAge: '1h',
      etag: true,
      lastModified: true
    }));

    // Logging des requêtes avec performance
    this.app.use((req, res, next) => {
      const start = new Date().toISOString();
      res.on('finish', () => {
        const duration = new Date().toISOString() - start;
        console.log(`🌐 ${req.method} ${req.path} - ${res.statusCode} - ${duration}ms - ${new Date().toISOString()}`);
      });
      next();
    });
  }

  /**
   * Configure les routes API
   */
  setupRoutes() {
    // Route principale du dashboard
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(__dirname, '../dashboard/index.html'));
    });

    // API Routes
    this.app.use('/api', this.createAPIRoutes());
  }

  /**
   * Crée les routes API
   */
  createAPIRoutes() {
    const router = express.Router();

    // Middleware d'authentification API
    router.use('/secure', this.authenticateAPI);

    // === ROUTES PUBLIQUES ===

    // Nouvelle route pour lancer le script de mise à jour
    router.post('/trigger-update', async (req, res) => {
      try {
        const child = spawn('node', ['update-database.js'], { 
          cwd: process.cwd(),
          stdio: ['pipe', 'pipe', 'pipe']
        });
        
        let output = '';
        let errorOutput = '';
        
        child.stdout.on('data', data => { 
          output += data.toString(); 
        });
        
        child.stderr.on('data', data => { 
          errorOutput += data.toString(); 
        });
        
        child.on('close', code => {
          if (code === 0) {
            res.json({ success: true, output: output + errorOutput });
          } else {
            res.json({ success: false, error: errorOutput || output });
          }
        });
        
        child.on('error', (error) => {
          res.status(500).json({ success: false, error: error.message });
        });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Route pour récupérer le statut de mise à jour
    router.get('/update-status', (req, res) => {
      try {
        const logPath = path.join(process.cwd(), 'logs', 'update-progress.log');
        if (fs.existsSync(logPath)) {
          const log = fs.readFileSync(logPath, 'utf8');
          res.json({ success: true, log });
        } else {
          res.json({ success: true, log: 'Aucun log disponible' });
        }
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Statistiques générales avec cache
    router.get('/stats', async (req, res) => {
      try {
        // Cache HTTP pour les stats (5 minutes)
        res.set('Cache-Control', 'public, max-age=300');
        
        const stats = await this.shopRepository.getStats();
        res.json({ success: true, data: stats });
      } catch (error) {
        console.error('❌ Erreur stats:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Liste des boutiques avec pagination optimisée
    router.get('/shops', async (req, res) => {
      try {
        const limit = parseInt(req.query.limit) || 50;
        const offset = parseInt(req.query.offset) || 0;
        const page = parseInt(req.query.page) || 1;
        
        // Validation des paramètres
        if (limit > 1000) {
          return res.status(400).json({ success: false, error: 'Limite maximale: 1000' });
        }
        
        const actualOffset = offset || (page - 1) * limit;
        const shops = await this.shopRepository.getAllWithPagination(limit, actualOffset);
        const total = await this.shopRepository.getTotalCount();
        
        res.json({
          success: true,
          data: shops,
          pagination: {
            total,
            limit,
            offset: actualOffset,
            page,
            totalPages: Math.ceil(total / limit)
          }
        });
      } catch (error) {
        console.error('❌ Erreur récupération boutiques:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Route pour les boutiques avec analytics (version corrigée)
    router.get('/shops/with-analytics', async (req, res) => {
      try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 50;
        const offset = (page - 1) * limit;
        
        // Récupérer les boutiques avec pagination
        const shops = await this.shopRepository.getAllWithPagination(limit, offset);
        
        // Ajouter les analytics pour chaque boutique
        const shopsWithAnalytics = [];
        for (const shop of shops) {
          const shopWithAnalytics = { ...shop };
          
          // Récupérer les analytics depuis la table analytics
          try {
            const analyticsStmt = this.dbManager.db.prepare(`
              SELECT organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, paid_search_traffic, scraping_status
              FROM analytics 
              WHERE shop_id = ?
            `);
            
            const analytics = analyticsStmt.get(shop.id);
            if (analytics) {
              shopWithAnalytics.organic_traffic = analytics.organic_traffic;
              shopWithAnalytics.bounce_rate = analytics.bounce_rate;
              shopWithAnalytics.average_visit_duration = analytics.avg_visit_duration;
              shopWithAnalytics.branded_traffic = analytics.branded_traffic;
              shopWithAnalytics.conversion_rate = analytics.conversion_rate;
              shopWithAnalytics.paid_search_traffic = analytics.paid_search_traffic;
              shopWithAnalytics.analytics_scraping_status = analytics.scraping_status;
            }
          } catch (error) {
            console.error(`❌ Erreur récupération analytics pour shop ${shop.id}:`, error.message);
          }
          
          shopsWithAnalytics.push(shopWithAnalytics);
        }
        
        // Récupérer le total pour la pagination
        const totalStmt = this.dbManager.db.prepare('SELECT COUNT(*) as total FROM shops');
        const total = totalStmt.get().total;
        
        res.json({ 
          success: true, 
          data: shopsWithAnalytics,
          pagination: {
            page,
            pages: Math.ceil(total / limit),
            total,
            limit
          }
        });
      } catch (error) {
        console.error('❌ Erreur boutiques avec analytics:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Top boutiques par Live Ads
    router.get('/shops/top', async (req, res) => {
      try {
        const limit = parseInt(req.query.limit) || 10;
        const shops = await this.shopRepository.getTopByLiveAds(limit);
        res.json({ success: true, data: shops });
      } catch (error) {
        console.error('❌ Erreur top boutiques:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Recherche de boutiques avec analytics
    router.get('/shops/search', async (req, res) => {
      try {
        const query = req.query.q;
        if (!query || query.length < 2) {
          return res.status(400).json({ success: false, error: 'Requête trop courte' });
        }
        
        const shops = await this.shopRepository.search(query);
        
        // Ajouter les métriques analytics pour chaque boutique trouvée
        const shopsWithAnalytics = [];
        for (const shop of shops) {
          const shopWithAnalytics = { ...shop };
          
          // Récupérer les analytics depuis l'API FastAPI
          try {
            const response = await fetch(`http://37.59.102.7:8000/analytics/${shop.id}`);
            if (response.ok) {
              const analyticsData = await response.json();
              if (analyticsData.success && analyticsData.data) {
                Object.assign(shopWithAnalytics, analyticsData.data);
              }
            }
          } catch (error) {
            console.error(`❌ Erreur récupération analytics pour shop ${shop.id}:`, error.message);
          }
          
          shopsWithAnalytics.push(shopWithAnalytics);
        }
        
        res.json({ success: true, data: shopsWithAnalytics });
      } catch (error) {
        console.error('❌ Erreur recherche:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Boutiques par catégorie
    router.get('/shops/category/:category', async (req, res) => {
      try {
        const category = req.params.category;
        const shops = await this.shopRepository.getByCategory(category);
        res.json({ success: true, data: shops });
      } catch (error) {
        console.error('❌ Erreur catégorie:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Domaines uniques (extraits de shop_url)
    router.get('/domains', async (req, res) => {
      try {
        const stmt = this.dbManager.db.prepare(`
          SELECT 
            CASE 
              WHEN shop_url LIKE '%://%' THEN 
                REPLACE(REPLACE(REPLACE(shop_url, 'https://', ''), 'http://', ''), 'www.', '')
              ELSE shop_url 
            END as domain,
            COUNT(*) as shop_count
          FROM shops 
          WHERE shop_url IS NOT NULL AND shop_url != ''
          GROUP BY domain
          ORDER BY shop_count DESC
        `);
        const domains = stmt.all();
        res.json({ success: true, data: domains });
      } catch (error) {
        console.error('❌ Erreur domaines:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // === ROUTES SÉCURISÉES ===

    // Ajouter une boutique
    router.post('/secure/shops', async (req, res) => {
      try {
        const shopData = req.body;
        const shopId = await this.shopRepository.upsert(shopData);
        
        if (shopId) {
          res.json({ success: true, data: { id: shopId } });
        } else {
          res.status(400).json({ success: false, error: 'Erreur lors de l\'ajout' });
        }
      } catch (error) {
        console.error('❌ Erreur ajout boutique:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Modifier une boutique
    router.put('/secure/shops/:id', async (req, res) => {
      try {
        const id = parseInt(req.params.id);
        const shopData = req.body;
        
        const success = await this.shopRepository.update(id, shopData);
        
        if (success) {
          res.json({ success: true });
        } else {
          res.status(404).json({ success: false, error: 'Boutique non trouvée' });
        }
      } catch (error) {
        console.error('❌ Erreur modification boutique:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Mettre à jour les métriques d'analyse d'une boutique
    router.put('/secure/shops/:id/analytics', async (req, res) => {
      try {
        const id = parseInt(req.params.id);
        const analyticsData = req.body;
        
        // Validation des données requises
        if (!analyticsData) {
          return res.status(400).json({ success: false, error: 'Données d\'analyse manquantes' });
        }
        
        const success = await this.shopRepository.updateAnalytics(id, analyticsData);
        
        if (success) {
          res.json({ success: true, message: 'Métriques mises à jour avec succès' });
        } else {
          res.status(404).json({ success: false, error: 'Boutique non trouvée' });
        }
      } catch (error) {
        console.error('❌ Erreur mise à jour métriques:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Supprimer une boutique
    router.delete('/secure/shops/:id', async (req, res) => {
      try {
        const id = parseInt(req.params.id);
        const success = await this.shopRepository.delete(id);
        
        if (success) {
        res.json({ success: true });
        } else {
          res.status(404).json({ success: false, error: 'Boutique non trouvée' });
        }
      } catch (error) {
        console.error('❌ Erreur suppression boutique:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    return router;
  }

  /**
   * Middleware d'authentification API
   */
  authenticateAPI(req, res, next) {
    const apiKey = req.headers['x-api-key'] || req.query.apiKey;
    
    if (!apiKey) {
      return res.status(401).json({ success: false, error: 'API key manquante' });
    }

    // Vérifier la clé API (simplifié pour l'exemple)
    // En production, utilisez une vraie authentification
    if (apiKey === 'trendtrack-admin-2024' || apiKey.startsWith('tt_')) {
      next();
    } else {
      res.status(401).json({ success: false, error: 'Clé API invalide' });
    }
  }

  /**
   * Génère une clé API
   */
  generateAPIKey() {
    return 'tt_' + crypto.randomBytes(16).toString('hex');
  }

  /**
   * Initialise le serveur
   */
  async init() {
    try {
      // Initialiser la base de données
      this.dbManager = new DatabaseManager();
      await this.dbManager.init();
      
      this.shopRepository = new ShopRepository(this.dbManager);
      
      console.log('✅ Base de données initialisée pour l\'API');
      return true;
    } catch (error) {
      console.error('❌ Erreur initialisation API:', error.message);
      return false;
    }
  }

  /**
   * Démarre le serveur
   */
  async start() {
    const initialized = await this.init();
    if (!initialized) {
      console.error('❌ Impossible de démarrer l\'API');
      return;
    }

    this.app.listen(this.port, () => {
      console.log(`🚀 API Dashboard démarrée sur http://localhost:${this.port}`);
      console.log(`📊 Dashboard web: http://localhost:${this.port}`);
      console.log(`🔑 Clé API admin: trendtrack-admin-2024`);
    });
  }
} 