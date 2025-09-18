import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

// Servir les fichiers statiques
app.use(express.static(path.join(__dirname, 'src/dashboard')));

// Route API spécifique pour shops/with-analytics
app.get('/api/shops/with-analytics', async (req, res) => {
    try {
        console.log('Redirecting to Python API...');
        
        // Récupérer les boutiques depuis l'API Python
        const { stdout: shopsData } = await execAsync('curl -s http://localhost:8000/shops');
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
        
        res.json({
            success: true,
            data: shopsWithAnalytics,
            pagination: {
                total: shopsWithAnalytics.length,
                limit: 1000,
                offset: 0,
                page: 1,
                totalPages: 1
            }
        });
    } catch (error) {
        console.error('API Error:', error);
        res.status(500).json({ error: 'Erreur API: ' + error.message });
    }
});

// Route par défaut
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'src/dashboard/index.html'));
});

app.listen(PORT, () => {
    console.log(`🚀 Dashboard accessible sur http://localhost:${PORT}`);
    console.log(`🔗 API Python: http://localhost:8000`);
});
