/**
 * Pont Python-JavaScript pour l'extraction des données de trafic par pays
 * Permet d'utiliser du code Python dans l'environnement JavaScript
 */

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class MarketTrafficPythonBridge {
    constructor() {
        this.pythonScript = path.join(__dirname, '../../python_bridge/market_traffic_extractor.py');
    }

    /**
     * Extrait les données de trafic par pays en utilisant Python
     * @param {string} shopUrl - URL du shop TrendTrack
     * @param {Array} targets - Liste des pays cibles
     * @returns {Promise<Object>} Données de trafic par pays
     */
    async extractMarketTraffic(shopUrl, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
        return new Promise((resolve, reject) => {
            const pythonProcess = spawn('python3', [
                this.pythonScript,
                shopUrl,
                JSON.stringify(targets)
            ]);

            let output = '';
            let errorOutput = '';

            pythonProcess.stdout.on('data', (data) => {
                output += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });

            pythonProcess.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(output);
                        resolve(result);
                    } catch (parseError) {
                        reject(new Error(`Erreur de parsing: ${parseError.message}`));
                    }
                } else {
                    reject(new Error(`Processus Python échoué: ${errorOutput}`));
                }
            });

            pythonProcess.on('error', (error) => {
                reject(new Error(`Erreur de processus: ${error.message}`));
            });
        });
    }

    /**
     * Extrait les données de trafic par pays pour plusieurs shops
     * @param {Array} shopUrls - Liste des URLs des shops
     * @param {Array} targets - Liste des pays cibles
     * @returns {Promise<Array>} Liste des données de trafic par pays
     */
    async extractMarketTrafficForMultipleShops(shopUrls, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
        const results = [];
        
        for (const shopUrl of shopUrls) {
            try {
                const marketData = await this.extractMarketTraffic(shopUrl, targets);
                results.push({
                    shopUrl,
                    ...marketData,
                    extractedAt: new Date().toISOString()
                });
                
                // Pause entre les shops pour éviter la surcharge
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error(`❌ Erreur pour ${shopUrl}: ${error.message}`);
                results.push({
                    shopUrl,
                    market_us: null,
                    market_uk: null,
                    market_de: null,
                    market_ca: null,
                    market_au: null,
                    market_fr: null,
                    extractedAt: new Date().toISOString(),
                    error: error.message
                });
            }
        }
        
        return results;
    }
}
