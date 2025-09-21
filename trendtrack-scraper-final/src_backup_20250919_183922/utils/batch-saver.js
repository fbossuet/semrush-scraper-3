/**
 * Système de sauvegarde incrémentale par lots pour TrendTrack
 * Permet de sauvegarder les données au fur et à mesure sans impacter les performances
 */

import fs from 'fs';
import path from 'path';

export class BatchSaver {
  constructor(batchSize = 10, flushInterval = 30000) {
    this.batchSize = batchSize;
    this.flushInterval = flushInterval;
    this.queue = [];
    this.isProcessing = false;
    this.stats = {
      saved: 0,
      errors: 0,
      pending: 0,
      batchesProcessed: 0,
      avgSaveTime: 0
    };
    this.startTime = Date.now();
    
    this.autoFlushTimer = setInterval(() => {
      this.flush();
    }, this.flushInterval);
    
    console.log('BatchSaver initialisé: batch=' + batchSize + ', interval=' + flushInterval + 'ms');
  }

  async add(shopData) {
    this.queue.push({
      data: shopData,
      timestamp: Date.now(),
      retries: 0
    });
    
    this.stats.pending++;
    
    console.log('Donnée ajoutée à la queue: ' + (shopData.shopName || 'Unknown') + ' (queue: ' + this.queue.length + ')');
    
    if (this.queue.length >= this.batchSize) {
      console.log('Batch plein (' + this.batchSize + '), flush automatique...');
      await this.flush();
    }
  }

  async flush() {
    if (this.queue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;
    const batch = this.queue.splice(0, this.batchSize);
    const startTime = Date.now();
    
    try {
      await this.saveBatch(batch);
      const saveTime = Date.now() - startTime;
      
      this.stats.saved += batch.length;
      this.stats.pending -= batch.length;
      this.stats.batchesProcessed++;
      this.stats.avgSaveTime = (this.stats.avgSaveTime + saveTime) / 2;
      
      console.log('Batch sauvegardé: ' + batch.length + ' boutiques en ' + saveTime + 'ms');
      
    } catch (error) {
      console.error('Erreur batch:', error.message);
      
      const failedItems = batch.filter(item => item.retries < 3);
      failedItems.forEach(item => item.retries++);
      this.queue.unshift(...failedItems);
      
      this.stats.errors += batch.length - failedItems.length;
    }
    
    this.isProcessing = false;
  }

  async saveBatch(batch) {
    const { spawn } = require('child_process');
    
    for (const item of batch) {
      try {
        const shopData = item.data;
        
        const dataForPython = {
          shopName: shopData.shopName || '',
          shopUrl: shopData.shopUrl || '',
          monthlyVisits: shopData.monthlyVisits || null,
          monthlyRevenue: shopData.monthlyRevenue || '',
          liveAds: shopData.liveAds || '',
          creationDate: shopData.creationDate || '',
          page: shopData.page || 1,
          scrapedAt: shopData.scrapedAt || new Date().toISOString(),
          yearFounded: shopData.yearFounded || null,
          totalProducts: shopData.totalProducts || null,
          pixelGoogle: shopData.pixelGoogle || null,
          pixelFacebook: shopData.pixelFacebook || null,
          aov: shopData.aov || null,
          marketUs: shopData.marketUs || null,
          marketUk: shopData.marketUk || null,
          marketDe: shopData.marketDe || null,
          marketCa: shopData.marketCa || null,
          marketAu: shopData.marketAu || null,
          marketFr: shopData.marketFr || null,
          category: shopData.category || ''
        };
        
        await new Promise((resolve, reject) => {
          const pythonProcess = spawn('python3', [
            path.join(process.cwd(), 'save_shop_batch.py'),
            JSON.stringify(dataForPython)
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
                const result = JSON.parse(output.trim());
                if (result.status === 'success') {
                  resolve(result);
                } else {
                  reject(new Error(result.message || 'Erreur inconnue'));
                }
              } catch (parseError) {
                reject(new Error('Erreur parsing résultat Python'));
              }
            } else {
              reject(new Error('Processus Python échoué: ' + errorOutput));
            }
          });
        });
        
      } catch (error) {
        console.error('Erreur sauvegarde ' + item.data.shopName + ':', error.message);
        throw error;
      }
    }
  }

  async close() {
    console.log('Fermeture du BatchSaver...');
    
    if (this.autoFlushTimer) {
      clearInterval(this.autoFlushTimer);
    }
    
    await this.flush();
    this.printFinalStats();
    
    console.log('BatchSaver fermé');
  }

  printFinalStats() {
    const elapsed = Date.now() - this.startTime;
    const stats = {
      ...this.stats,
      elapsedTime: elapsed,
      saveRate: this.stats.saved / (elapsed / 1000),
      errorRate: this.stats.errors / (this.stats.saved + this.stats.errors) || 0
    };
    
    console.log('=== STATISTIQUES FINALES BATCHSAVER ===');
    console.log('Boutiques sauvegardées: ' + stats.saved);
    console.log('Erreurs: ' + stats.errors);
    console.log('Temps écoulé: ' + Math.round(stats.elapsedTime / 1000) + 's');
    console.log('Taux de sauvegarde: ' + stats.saveRate.toFixed(2) + ' items/sec');
    console.log('Batches traités: ' + stats.batchesProcessed);
    console.log('Temps moyen/batch: ' + Math.round(stats.avgSaveTime) + 'ms');
    console.log('Taux d erreur: ' + (stats.errorRate * 100).toFixed(1) + '%');
    console.log('==========================================');
  }

  getStats() {
    const elapsed = Date.now() - this.startTime;
    return {
      ...this.stats,
      elapsedTime: elapsed,
      saveRate: this.stats.saved / (elapsed / 1000),
      errorRate: this.stats.errors / (this.stats.saved + this.stats.errors) || 0
    };
  }
}
