// Serveur Web pour le Dashboard SEO Analytics
import express from 'express';
import path from 'path';
import fs from 'fs/promises';
import { spawn } from 'child_process';
import cors from 'cors';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// Configuration des chemins
const SCRAPERS_DIR = path.join(__dirname);
const RESULTS_DIR = path.join(__dirname, '../results');

// Créer le dossier results s'il n'existe pas
async function ensureResultsDir() {
    try {
        await fs.access(RESULTS_DIR);
    } catch {
        await fs.mkdir(RESULTS_DIR, { recursive: true });
        console.log('📁 Dossier results créé');
    }
}

// Routes principales

// Page d'accueil
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// API endpoints

// Lancer le scraper organic traffic (avec fallback multi-serveur)
app.post('/api/organic-traffic', async (req, res) => {
    try {
        const { domain } = req.body;
        
        if (!domain) {
            return res.status(400).json({ 
                success: false, 
                error: 'Domaine requis' 
            });
        }

        console.log('🔄 Lancement scraper organic traffic (multi-serveur) pour:', domain);
        
        // Essayer d'abord le multi-server scraper
        try {
            const result = await runScraper('multi-server-scraper.js', domain);
            
            res.json({
                success: true,
                message: 'Scraper multi-serveur organic traffic terminé',
                result: result,
                method: 'multi-server'
            });
            
        } catch (multiServerError) {
            console.log('⚠️ Multi-serveur échoué, fallback vers scraper standard...');
            
            // Fallback vers l'ancien scraper
            const result = await runScraper('organic-traffic-scraper.js', domain);
            
            res.json({
                success: true,
                message: 'Scraper organic traffic standard terminé',
                result: result,
                method: 'fallback',
                multiServerError: multiServerError.message
            });
        }

    } catch (error) {
        console.error('❌ Erreur scraper organic traffic:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Lancer le scraper smart traffic (avec fallback multi-serveur)
app.post('/api/smart-traffic', async (req, res) => {
    try {
        const { domain } = req.body;
        
        if (!domain) {
            return res.status(400).json({ 
                success: false, 
                error: 'Domaine requis' 
            });
        }

        console.log('🔄 Lancement scraper smart traffic (multi-serveur) pour:', domain);
        
        // Essayer d'abord le multi-server scraper
        try {
            const result = await runScraper('multi-server-scraper.js', domain);
            
            res.json({
                success: true,
                message: 'Scraper multi-serveur smart traffic terminé',
                result: result,
                method: 'multi-server'
            });
            
        } catch (multiServerError) {
            console.log('⚠️ Multi-serveur échoué, fallback vers scraper standard...');
            
            // Fallback vers l'ancien scraper
            const result = await runScraper('smart-traffic-scraper.js', domain);
            
            res.json({
                success: true,
                message: 'Scraper smart traffic standard terminé',
                result: result,
                method: 'fallback',
                multiServerError: multiServerError.message
            });
        }

    } catch (error) {
        console.error('❌ Erreur scraper smart traffic:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Lancer le scraper domain overview
app.post('/api/domain-overview', async (req, res) => {
    try {
        const { domain } = req.body;
        
        if (!domain) {
            return res.status(400).json({ 
                success: false, 
                error: 'Domaine requis' 
            });
        }

        console.log('🔄 Lancement scraper domain overview pour:', domain);
        
        const result = await runScraper('smart-scraper.js', domain);
        
        res.json({
            success: true,
            message: 'Scraper domain overview terminé',
            result: result
        });

    } catch (error) {
        console.error('❌ Erreur scraper domain overview:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Analyse intelligente (combine plusieurs scrapers)
app.post('/api/smart-analysis', async (req, res) => {
    try {
        const { domain } = req.body;
        
        if (!domain) {
            return res.status(400).json({ 
                success: false, 
                error: 'Domaine requis' 
            });
        }

        console.log('🧠 Lancement analyse intelligente pour:', domain);
        
        // Lancer plusieurs scrapers en parallèle
        const results = await Promise.allSettled([
            runScraper('organic-traffic-scraper.js', domain),
            runScraper('smart-traffic-scraper.js', domain),
            runScraper('smart-scraper.js', domain)
        ]);

        // Analyser les résultats
        const analysisResult = {
            domain,
            timestamp: new Date().toISOString(),
            scrapers: {
                organicTraffic: results[0].status === 'fulfilled' ? results[0].value : null,
                smartTraffic: results[1].status === 'fulfilled' ? results[1].value : null,
                smartScraper: results[2].status === 'fulfilled' ? results[2].value : null
            },
            errors: results.filter(r => r.status === 'rejected').map(r => r.reason)
        };

        // Sauvegarder le résultat d'analyse
        const analysisFile = path.join(RESULTS_DIR, `smart-analysis-${sanitizeFilename(domain)}-${Date.now()}.json`);
        await fs.writeFile(analysisFile, JSON.stringify(analysisResult, null, 2));

        res.json({
            success: true,
            message: 'Analyse intelligente terminée',
            result: analysisResult,
            file: path.basename(analysisFile)
        });

    } catch (error) {
        console.error('❌ Erreur analyse intelligente:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Récupérer la liste des fichiers pour un domaine
app.get('/api/files/:domain', async (req, res) => {
    try {
        const domain = decodeURIComponent(req.params.domain);
        const sanitizedDomain = sanitizeFilename(domain);
        
        console.log('📂 Récupération fichiers pour:', domain);
        
        const files = await fs.readdir(RESULTS_DIR);
        const domainFiles = files.filter(file => 
            file.includes(sanitizedDomain) && file.endsWith('.json')
        );

        const fileStats = await Promise.all(
            domainFiles.map(async (filename) => {
                const filePath = path.join(RESULTS_DIR, filename);
                const stats = await fs.stat(filePath);
                return {
                    name: filename,
                    size: stats.size,
                    date: stats.mtime.toISOString(),
                    path: filePath
                };
            })
        );

        // Trier par date de modification (plus récent en premier)
        fileStats.sort((a, b) => new Date(b.date) - new Date(a.date));

        res.json(fileStats);

    } catch (error) {
        console.error('❌ Erreur récupération fichiers:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Récupérer le contenu d'un fichier
app.get('/api/data/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        
        // Sécurité : vérifier que le fichier est dans le bon dossier
        if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
            return res.status(400).json({
                success: false,
                error: 'Nom de fichier invalide'
            });
        }

        const filePath = path.join(RESULTS_DIR, filename);
        
        // Vérifier que le fichier existe
        await fs.access(filePath);
        
        const content = await fs.readFile(filePath, 'utf8');
        const data = JSON.parse(content);
        
        res.json(data);

    } catch (error) {
        console.error('❌ Erreur lecture fichier:', error);
        
        if (error.code === 'ENOENT') {
            res.status(404).json({
                success: false,
                error: 'Fichier non trouvé'
            });
        } else {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }
});

// Télécharger un fichier
app.get('/api/download/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        
        // Sécurité
        if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
            return res.status(400).send('Nom de fichier invalide');
        }

        const filePath = path.join(RESULTS_DIR, filename);
        
        // Vérifier que le fichier existe
        await fs.access(filePath);
        
        res.download(filePath, filename);

    } catch (error) {
        console.error('❌ Erreur téléchargement:', error);
        res.status(404).send('Fichier non trouvé');
    }
});

// Voir un fichier dans le navigateur
app.get('/api/view/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        
        // Sécurité
        if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
            return res.status(400).send('Nom de fichier invalide');
        }

        const filePath = path.join(RESULTS_DIR, filename);
        
        // Vérifier que le fichier existe
        await fs.access(filePath);
        
        const content = await fs.readFile(filePath, 'utf8');
        
        // Formater le JSON pour l'affichage
        res.set('Content-Type', 'application/json');
        res.send(content);

    } catch (error) {
        console.error('❌ Erreur affichage fichier:', error);
        res.status(404).send('Fichier non trouvé');
    }
});

// Endpoint spécialisé pour debug cakesbody.com
app.post('/api/debug-cakesbody', async (req, res) => {
    try {
        const { domain } = req.body;
        const targetDomain = domain || 'cakesbody.com';
        
        console.log('🔍 Lancement debug spécialisé pour:', targetDomain);
        
        const result = await runScraper('cakesbody-debug-scraper.js', targetDomain);
        
        res.json({
            success: true,
            message: 'Debug cakesbody terminé',
            result: result,
            domain: targetDomain
        });

    } catch (error) {
        console.error('❌ Erreur debug cakesbody:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Status de l'API
app.get('/api/status', (req, res) => {
    res.json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        scrapers: {
            organicTraffic: 'Disponible (Multi-serveur)',
            smartTraffic: 'Disponible (Multi-serveur)',
            domainOverview: 'Disponible',
            smartAnalysis: 'Disponible',
            multiServer: 'Disponible (Servers 1-5)',
            cakesbodyDebug: 'Disponible'
        },
        servers: [
            'server1.noxtools.com',
            'server2.noxtools.com',
            'server3.noxtools.com',
            'server4.noxtools.com',
            'server5.noxtools.com'
        ],
        resultsDir: RESULTS_DIR
    });
});

// Fonctions utilitaires

// Lancer un scraper
async function runScraper(scraperFile, domain) {
    return new Promise((resolve, reject) => {
        const scraperPath = path.join(SCRAPERS_DIR, scraperFile);
        
        console.log(`🚀 Lancement de ${scraperFile} avec le domaine: ${domain}`);
        
        const child = spawn('node', [scraperPath, domain], {
            stdio: 'pipe',
            cwd: SCRAPERS_DIR
        });

        let stdout = '';
        let stderr = '';

        child.stdout.on('data', (data) => {
            const output = data.toString();
            stdout += output;
            console.log(`📤 ${scraperFile}:`, output.trim());
        });

        child.stderr.on('data', (data) => {
            const error = data.toString();
            stderr += error;
            console.error(`❌ ${scraperFile}:`, error.trim());
        });

        child.on('close', (code) => {
            console.log(`✅ ${scraperFile} terminé avec le code: ${code}`);
            
            if (code === 0) {
                resolve({
                    success: true,
                    output: stdout,
                    scraper: scraperFile,
                    domain: domain,
                    timestamp: new Date().toISOString()
                });
            } else {
                reject(new Error(`Le scraper ${scraperFile} a échoué avec le code ${code}. Erreur: ${stderr}`));
            }
        });

        child.on('error', (error) => {
            console.error(`💥 Erreur lancement ${scraperFile}:`, error);
            reject(error);
        });

        // Timeout de 5 minutes
        setTimeout(() => {
            child.kill();
            reject(new Error(`Timeout: ${scraperFile} a pris trop de temps`));
        }, 5 * 60 * 1000);
    });
}

// Nettoyer le nom de fichier
function sanitizeFilename(filename) {
    return filename
        .replace(/[^a-z0-9\-_.]/gi, '-')
        .replace(/^https?-+/i, '')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
        .toLowerCase();
}

// Gestionnaire d'erreur global
app.use((error, req, res, next) => {
    console.error('💥 Erreur serveur:', error);
    res.status(500).json({
        success: false,
        error: 'Erreur interne du serveur'
    });
});

// Route 404
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Route non trouvée'
    });
});

// Démarrage du serveur
async function startServer() {
    try {
        // Créer le dossier results
        await ensureResultsDir();
        
        // Vérifier que les scrapers existent
        const scrapers = [
            'organic-traffic-scraper.js',
            'smart-traffic-scraper.js',
            'smart-scraper.js'
        ];

        for (const scraper of scrapers) {
            try {
                await fs.access(path.join(SCRAPERS_DIR, scraper));
                console.log(`✅ Scraper trouvé: ${scraper}`);
            } catch {
                console.warn(`⚠️  Scraper manquant: ${scraper}`);
            }
        }

        // Démarrer le serveur
        app.listen(PORT, () => {
            console.log('');
            console.log('🎯 ================================');
            console.log('   SEO Analytics Dashboard');
            console.log('🎯 ================================');
            console.log('');
            console.log(`🌐 Serveur démarré sur: http://localhost:${PORT}`);
            console.log(`📁 Dossier résultats: ${RESULTS_DIR}`);
            console.log(`🔧 API Status: http://localhost:${PORT}/api/status`);
            console.log('');
            console.log('📋 Endpoints disponibles:');
            console.log('   POST /api/organic-traffic   (Multi-serveur 1-5)');
            console.log('   POST /api/smart-traffic     (Multi-serveur 1-5)');
            console.log('   POST /api/domain-overview');
            console.log('   POST /api/smart-analysis');
            console.log('   POST /api/debug-cakesbody   (Debug spécialisé)');
            console.log('   GET  /api/files/:domain');
            console.log('   GET  /api/data/:filename');
            console.log('   GET  /api/status            (+ info serveurs)');
            console.log('');
            console.log('🚀 Interface web: http://localhost:3000');
            console.log('');
        });

    } catch (error) {
        console.error('💥 Erreur démarrage serveur:', error);
        process.exit(1);
    }
}

// Gestionnaire d'arrêt propre
process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt du serveur...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Arrêt du serveur (SIGTERM)...');
    process.exit(0);
});

// Démarrer le serveur
startServer();

export default app;