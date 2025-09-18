#!/usr/bin/env node
/**
 * Test du scraper TrendTrack avec extraction des données de trafic par pays
 * Test sur les 3 premiers résultats de recherche
 */

import { TrendTrackScraper } from './src/trendtrack-scraper.js';

async function testTrendTrackWithMarketData() {
    console.log('🧪 TEST DU SCRAPER TRENDTRACK AVEC DONNÉES DE TRAFIC PAR PAYS');
    console.log('=' .repeat(70));
    
    const scraper = new TrendTrackScraper();
    
    try {
        // 1. Initialiser le scraper
        console.log('\n1️⃣ Initialisation du scraper...');
        await scraper.init();
        console.log('✅ Scraper initialisé');
        
        // 2. Naviguer vers TrendTrack
        console.log('\n2️⃣ Navigation vers TrendTrack...');
        const navSuccess = await scraper.navigateToTrendingShops();
        if (!navSuccess) {
            throw new Error('Échec de la navigation vers TrendTrack');
        }
        console.log('✅ Navigation réussie');
        
        // 3. Scraper 1 page avec données de trafic par pays
        console.log('\n3️⃣ Scraping d\'une page avec données de trafic par pays...');
        const shopsData = await scraper.scrapeMultiplePages(1, true); // includeMarketData = true
        
        if (shopsData.length === 0) {
            console.log('⚠️ Aucune donnée extraite');
            return;
        }
        
        console.log(`✅ ${shopsData.length} boutiques extraites`);
        
        // 4. Afficher les données des 3 premiers shops
        console.log('\n4️⃣ Données des 3 premiers shops:');
        const firstThreeShops = shopsData.slice(0, 3);
        
        firstThreeShops.forEach((shop, index) => {
            console.log(`\n📊 Shop ${index + 1}:`);
            console.log(`  Nom: ${shop.shopName || 'N/A'}`);
            console.log(`  URL: ${shop.shopUrl || 'N/A'}`);
            console.log(`  Domaine: ${shop.shopDomain || 'N/A'}`);
            console.log(`  Visites mensuelles: ${shop.monthlyVisits || 'N/A'}`);
            console.log(`  Revenus mensuels: ${shop.monthlyRevenue || 'N/A'}`);
            console.log(`  Publicités actives: ${shop.liveAds || 'N/A'}`);
            
            // Données de trafic par pays
            console.log(`  🌍 Trafic par pays:`);
            console.log(`    US: ${shop.market_us || 'N/A'}`);
            console.log(`    UK: ${shop.market_uk || 'N/A'}`);
            console.log(`    DE: ${shop.market_de || 'N/A'}`);
            console.log(`    CA: ${shop.market_ca || 'N/A'}`);
            console.log(`    AU: ${shop.market_au || 'N/A'}`);
            console.log(`    FR: ${shop.market_fr || 'N/A'}`);
        });
        
        // 5. Vérifier que les données market_* sont présentes
        console.log('\n5️⃣ Vérification des données de trafic par pays...');
        const shopsWithMarketData = firstThreeShops.filter(shop => 
            shop.market_us !== undefined || 
            shop.market_uk !== undefined || 
            shop.market_de !== undefined ||
            shop.market_ca !== undefined ||
            shop.market_au !== undefined ||
            shop.market_fr !== undefined
        );
        
        console.log(`✅ ${shopsWithMarketData.length}/${firstThreeShops.length} shops ont des données de trafic par pays`);
        
        // 6. Sauvegarder les données en CSV
        console.log('\n6️⃣ Sauvegarde des données...');
        const csvData = await scraper.extractor.formatToCSV(shopsData);
        
        // Écrire le fichier CSV
        const fs = await import('fs');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `test_trendtrack_market_data_${timestamp}.csv`;
        
        fs.writeFileSync(filename, csvData);
        console.log(`✅ Données sauvegardées dans: ${filename}`);
        
        // 7. Résumé
        console.log('\n🎉 TEST TERMINÉ AVEC SUCCÈS!');
        console.log('=' .repeat(70));
        console.log(`📊 Boutiques extraites: ${shopsData.length}`);
        console.log(`🌍 Données de trafic par pays: ${shopsWithMarketData.length} shops`);
        console.log(`📄 Fichier CSV: ${filename}`);
        
    } catch (error) {
        console.error('❌ Erreur lors du test:', error.message);
        console.error('Stack trace:', error.stack);
    } finally {
        // Fermer le scraper
        console.log('\n🔚 Fermeture du scraper...');
        await scraper.close();
        console.log('✅ Scraper fermé');
    }
}

// Lancer le test
testTrendTrackWithMarketData().catch(console.error);
