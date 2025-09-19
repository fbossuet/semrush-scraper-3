/**
 * Pont JavaScript pour l'extracteur Python des métriques supplémentaires
 * Appelle le script Python pour récupérer:
 * - total_products
 * - pixel_google
 * - pixel_facebook
 * - aov
 */

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class AdditionalMetricsPythonBridge {
  constructor() {
    // Chemin vers le script Python
    this.pythonScriptPath = path.join(__dirname, '../../python_bridge/additional_metrics_extractor.py');
  }

  /**
   * Extrait les métriques supplémentaires via le script Python
   * @param {string} shopUrl - URL de la boutique
   * @returns {Promise<Object>} - Métriques supplémentaires
   */
  async extractAdditionalMetrics(shopUrl) {
    console.log(`🌉 Appel du pont Python pour métriques supplémentaires: ${shopUrl}`);
    
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python3', [this.pythonScriptPath, shopUrl], {
        cwd: path.dirname(this.pythonScriptPath)
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            console.log(`✅ Résultat Python Bridge: ${JSON.stringify(result, null, 2)}`);
            resolve(result);
          } catch (error) {
            console.error('❌ Erreur parsing JSON:', error.message);
            reject(new Error(`Erreur parsing JSON: ${error.message}`));
          }
        } else {
          console.error(`❌ Script Python échoué avec le code ${code}`);
          console.error(`stderr: ${stderr}`);
          reject(new Error(`Script Python échoué: ${stderr}`));
        }
      });

      pythonProcess.on('error', (error) => {
        console.error('❌ Erreur lancement script Python:', error.message);
        reject(error);
      });

      // Timeout après 60 secondes
      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Timeout: Script Python trop lent'));
      }, 60000);
    });
  }

  /**
   * Extrait les métriques supplémentaires pour plusieurs boutiques
   * @param {Array<string>} shopUrls - URLs des boutiques
   * @returns {Promise<Array<Object>>} - Métriques pour chaque boutique
   */
  async extractAdditionalMetricsForMultipleShops(shopUrls) {
    console.log(`🌉 Extraction métriques supplémentaires pour ${shopUrls.length} boutiques`);
    
    const results = [];
    
    for (const shopUrl of shopUrls) {
      try {
        const metrics = await this.extractAdditionalMetrics(shopUrl);
        results.push({
          shop_url: shopUrl,
          ...metrics
        });
        
        // Pause entre les requêtes pour éviter la surcharge
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        console.error(`❌ Erreur pour ${shopUrl}:`, error.message);
        results.push({
          shop_url: shopUrl,
          total_products: null,
          pixel_google: null,
          pixel_facebook: null,
          aov: null,
          error: error.message
        });
      }
    }
    
    return results;
  }
}
