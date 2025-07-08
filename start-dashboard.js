#!/usr/bin/env node

// Script de démarrage pour le Dashboard SEO Analytics
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🎯 ================================');
console.log('   SEO Analytics Dashboard');
console.log('   Script de Démarrage');
console.log('🎯 ================================');
console.log('');

// Vérifications préalables
console.log('🔍 Vérifications préalables...');

// Vérifier Node.js
const nodeVersion = process.version;
console.log(`✅ Node.js: ${nodeVersion}`);

// Vérifier les fichiers essentiels
const essentialFiles = [
    'src/web-server.js',
    'public/index.html',
    'public/style.css',
    'public/script.js',
    'package.json'
];

let missingFiles = [];

for (const file of essentialFiles) {
    if (fs.existsSync(file)) {
        console.log(`✅ ${file}`);
    } else {
        console.log(`❌ ${file} - MANQUANT`);
        missingFiles.push(file);
    }
}

// Vérifier les scrapers optionnels
console.log('');
console.log('🔍 Vérification des scrapers...');

const scrapers = [
    'src/organic-traffic-scraper.js',
    'src/smart-traffic-scraper.js', 
    'src/smart-scraper.js'
];

for (const scraper of scrapers) {
    if (fs.existsSync(scraper)) {
        console.log(`✅ ${scraper}`);
    } else {
        console.log(`⚠️  ${scraper} - Non trouvé (fonctionnalité limitée)`);
    }
}

// Si des fichiers essentiels manquent, arrêter
if (missingFiles.length > 0) {
    console.log('');
    console.log('❌ Fichiers essentiels manquants:', missingFiles.join(', '));
    console.log('Veuillez vérifier votre installation.');
    process.exit(1);
}

// Créer le dossier results s'il n'existe pas
if (!fs.existsSync('results')) {
    fs.mkdirSync('results', { recursive: true });
    console.log('📁 Dossier results créé');
}

console.log('');
console.log('🚀 Démarrage du serveur...');
console.log('');

// Démarrer le serveur
const serverProcess = spawn('node', ['src/web-server.js'], {
    stdio: 'inherit',
    cwd: process.cwd()
});

// Gérer les signaux d'arrêt
process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt du dashboard...');
    serverProcess.kill('SIGINT');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Arrêt du dashboard (SIGTERM)...');
    serverProcess.kill('SIGTERM');
    process.exit(0);
});

// Gérer les erreurs du serveur
serverProcess.on('error', (error) => {
    console.error('💥 Erreur serveur:', error);
    process.exit(1);
});

serverProcess.on('exit', (code) => {
    console.log(`\n📊 Serveur arrêté avec le code: ${code}`);
    process.exit(code);
});