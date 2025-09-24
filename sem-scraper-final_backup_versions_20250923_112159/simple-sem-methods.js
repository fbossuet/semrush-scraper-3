#!/usr/bin/env node
/**
 * Script simple pour ajouter les méthodes SEM
 */

import fs from 'fs';

function addSimpleSEMMethods() {
    console.log("🔧 Ajout des méthodes SEM simples...");
    
    try {
        // Lire le fichier
        const filePath = './src/dashboard/dashboard.js';
        let content = fs.readFileSync(filePath, 'utf8');
        
        // Sauvegarder
        const backupPath = `./src/dashboard/dashboard-backup-simple-${new Date().toISOString().replace(/[:.]/g, '-')}.js`;
        fs.writeFileSync(backupPath, content);
        console.log(`✅ Backup créé: ${backupPath}`);
        
        // Trouver la fin de la classe (avant la fermeture)
        const classEnd = content.lastIndexOf('}');
        
        // Méthodes simples
        const semMethods = `
    async triggerSEMScraper() {
        const btn = document.querySelector('.btn.btn-primary[onclick*="triggerSEMScraper"]');
        if (btn) btn.disabled = true;
        if (!confirm('Lancer le scraper SEM ?')) {
            if (btn) btn.disabled = false;
            return;
        }
        this.showLoader();
        this.showInfo('Scraper SEM en cours...');
        try {
            const response = await fetch('/api/trigger-sem-scraper', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.showSuccess('Scraper SEM terminé avec succès !');
                await this.loadStats();
                await this.loadShops();
            } else {
                this.showError('Échec du scraper SEM : ' + data.error);
            }
        } catch (error) {
            this.showError('Erreur lors de la requête : ' + error.message);
        } finally {
            setTimeout(async () => {
                await this.hideLoader();
                if (btn) btn.disabled = false;
            }, 2000);
        }
    }

    async showSEMLogs() {
        try {
            const response = await fetch('/api/sem-logs');
            const data = await response.json();
            if (data.success) {
                this.showLogsModal('Logs SEM', data.logs);
            } else {
                this.showError('Erreur lors du chargement des logs SEM : ' + data.error);
            }
        } catch (error) {
            this.showError('Erreur lors de la requête : ' + error.message);
        }
    }`;
        
        // Insérer avant la fermeture de la classe
        const beforeEnd = content.substring(0, classEnd);
        const afterEnd = content.substring(classEnd);
        
        content = beforeEnd + semMethods + afterEnd;
        
        fs.writeFileSync(filePath, content);
        console.log("✅ Méthodes SEM ajoutées");
        
        return true;
        
    } catch (error) {
        console.error("❌ Erreur:", error.message);
        return false;
    }
}

addSimpleSEMMethods(); 