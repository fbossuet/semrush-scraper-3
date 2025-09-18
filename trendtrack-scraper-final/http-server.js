import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;

const server = http.createServer(async (req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Route API pour shops/with-analytics
    if (req.url === '/api/shops/with-analytics') {
        try {
            console.log('API call: /api/shops/with-analytics');
            
            // Récupérer les boutiques depuis l'API Python
            const { stdout: shopsData } = await execAsync('python3 api_helper.py');
            const shops = JSON.parse(shopsData);
            
            // Pour chaque boutique, récupérer les analytics
            const shopsWithAnalytics = [];
            for (const shop of shops) {
                try {
                    const { stdout: analyticsData } = await execAsync(`curl -s http://localhost:8000/analytics/${shop.id}`);
                    const analytics = JSON.parse(analyticsData);
                    
                    if (analytics.success) {
                        shopsWithAnalytics.push({
                            ...shop,
                            ...analytics.data
                        });
                    } else {
                        shopsWithAnalytics.push(shop);
                    }
                } catch (error) {
                    shopsWithAnalytics.push(shop);
                }
            }
            
            const response = {
                success: true,
                data: shopsWithAnalytics,
                pagination: {
                    total: shopsWithAnalytics.length,
                    limit: 1000,
                    offset: 0,
                    page: 1,
                    totalPages: 1
                }
            };
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(response));
        } catch (error) {
            console.error('API Error:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Erreur API: ' + error.message }));
        }
        return;
    }

    // Servir les fichiers statiques
    let filePath = req.url === '/' ? '/index.html' : req.url;
    filePath = path.join(__dirname, 'src/dashboard', filePath);

    try {
        const content = fs.readFileSync(filePath);
        const ext = path.extname(filePath);
        
        let contentType = 'text/plain';
        if (ext === '.html') contentType = 'text/html';
        else if (ext === '.js') contentType = 'application/javascript';
        else if (ext === '.css') contentType = 'text/css';
        
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
    } catch (error) {
        res.writeHead(404);
        res.end('File not found');
    }
});

server.listen(PORT, () => {
    console.log(`🚀 Dashboard accessible sur http://localhost:${PORT}`);
    console.log(`🔗 API Python: http://localhost:8000`);
});
