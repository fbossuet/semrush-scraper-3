#!/usr/bin/env node

/**
 * TEST D'ACCÈS DIRECT À LA PAGE DE DÉTAIL POUR LES DONNÉES DE MARCHÉ
 */

import { WebScraper } from './src/scraper.js';
import { TrendTrackExtractor } from './src/extractors/trendtrack-extractor.js';
import { ErrorHandler } from './src/utils/error-handler.js';

const testDirectPage = async () => {
    console.log('🌍 TEST D\'ACCÈS DIRECT À LA PAGE DE DÉTAIL');
    console.log('==========================================');
    
    let scraper = null;
    let extractor = null;
    
    try {
        // Initialisation du scraper
        scraper = new WebScraper();
        await scraper.init();
        
        const errorHandler = new ErrorHandler();
        extractor = new TrendTrackExtractor(scraper.page, errorHandler);
        
        // Connexion à TrendTrack
        const loginSuccess = await extractor.login('seif.alyakoob@gmail.com', 'Toulouse31!');
        if (!loginSuccess) {
            console.log('❌ Échec de la connexion');
            return;
        }
        
        console.log('✅ Connexion réussie');
        
        // Test avec un site spécifique
        const testSiteId = '2804';
        console.log(`\n🔍 ACCÈS DIRECT À LA PAGE DE DÉTAIL: ${testSiteId}`);
        
        // Aller directement à la page de détail
        const detailUrl = `https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${testSiteId}`;
        console.log(`🌐 Navigation vers: ${detailUrl}`);
        
        await scraper.page.goto(detailUrl, { waitUntil: 'networkidle' });
        console.log('✅ Page de détail chargée');
        
        // Attendre que la page soit complètement chargée
        await scraper.page.waitForTimeout(5000);
        
        // Chercher les données de marché sur la page
        const marketData = await scraper.page.evaluate(() => {
            const results = {
                marketElements: [],
                countryElements: [],
                percentageElements: [],
                geoElements: []
            };
            
            // Recherche d'éléments contenant des données de marché
            const selectors = [
                '[data-testid*="market"]',
                '[data-testid*="country"]',
                '[data-testid*="geo"]',
                '[class*="market"]',
                '[class*="country"]',
                '[class*="geo"]',
                'div:contains("US")',
                'div:contains("UK")',
                'div:contains("DE")',
                'div:contains("CA")',
                'div:contains("AU")',
                'div:contains("FR")'
            ];
            
            selectors.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (el.textContent && el.textContent.trim()) {
                            results.marketElements.push({
                                selector: selector,
                                text: el.textContent.trim(),
                                html: el.outerHTML.substring(0, 200)
                            });
                        }
                    });
                } catch (e) {
                    // Ignorer les sélecteurs invalides
                }
            });
            
            // Recherche de textes contenant des codes pays
            const countryCodes = ['US', 'UK', 'DE', 'CA', 'AU', 'FR'];
            countryCodes.forEach(code => {
                const elements = document.querySelectorAll(`*:contains("${code}")`);
                elements.forEach(el => {
                    if (el.textContent && el.textContent.includes(code)) {
                        results.countryElements.push({
                            country: code,
                            text: el.textContent.trim(),
                            html: el.outerHTML.substring(0, 200)
                        });
                    }
                });
            });
            
            // Recherche de pourcentages
            const percentageElements = document.querySelectorAll('*');
            percentageElements.forEach(el => {
                if (el.textContent && el.textContent.match(/[0-9]+\.[0-9]+%/)) {
                    results.percentageElements.push({
                        text: el.textContent.trim(),
                        html: el.outerHTML.substring(0, 200)
                    });
                }
            });
            
            // Recherche d'éléments géographiques
            const geoKeywords = ['country', 'market', 'traffic', 'visits'];
            geoKeywords.forEach(keyword => {
                const elements = document.querySelectorAll(`*:contains("${keyword}")`);
                elements.forEach(el => {
                    if (el.textContent && el.textContent.toLowerCase().includes(keyword)) {
                        results.geoElements.push({
                            keyword: keyword,
                            text: el.textContent.trim(),
                            html: el.outerHTML.substring(0, 200)
                        });
                    }
                });
            });
            
            return results;
        });
        
        console.log('\n📊 ÉLÉMENTS DE MARCHÉ TROUVÉS:');
        console.log('='.repeat(40));
        marketData.marketElements.forEach((element, index) => {
            console.log(`\n   ${index + 1}. ${element.selector}`);
            console.log(`      Texte: ${element.text}`);
        });
        
        console.log('\n🌍 ÉLÉMENTS PAYS TROUVÉS:');
        console.log('='.repeat(40));
        marketData.countryElements.forEach((element, index) => {
            console.log(`\n   ${index + 1}. ${element.country}`);
            console.log(`      Texte: ${element.text}`);
        });
        
        console.log('\n📊 ÉLÉMENTS POURCENTAGES TROUVÉS:');
        console.log('='.repeat(40));
        marketData.percentageElements.forEach((element, index) => {
            console.log(`\n   ${index + 1}. ${element.text}`);
        });
        
        console.log('\n🌍 ÉLÉMENTS GÉOGRAPHIQUES TROUVÉS:');
        console.log('='.repeat(40));
        marketData.geoElements.forEach((element, index) => {
            console.log(`\n   ${index + 1}. ${element.keyword}`);
            console.log(`      Texte: ${element.text}`);
        });
        
        // Test de l'extraction des métriques existante
        console.log('\n🚀 TEST DE L\'EXTRACTION EXISTANTE:');
        console.log('='.repeat(40));
        
        const existingMetrics = await extractor.extractShopDetails();
        console.log('✅ Métriques extraites:');
        console.log(`   - Bounce Rate: ${existingMetrics.bounce_rate}`);
        console.log(`   - Avg Visit Duration: ${existingMetrics.avg_visit_duration}`);
        console.log(`   - Conversion Rate: ${existingMetrics.conversion_rate}`);
        console.log(`   - Market US: ${existingMetrics.market_us}`);
        console.log(`   - Market UK: ${existingMetrics.market_uk}`);
        console.log(`   - Market DE: ${existingMetrics.market_de}`);
        console.log(`   - Market CA: ${existingMetrics.market_ca}`);
        console.log(`   - Market AU: ${existingMetrics.market_au}`);
        console.log(`   - Market FR: ${existingMetrics.market_fr}`);
        
    } catch (error) {
        console.error('❌ Erreur:', error.message);
    } finally {
        if (scraper) {
            await scraper.close();
            console.log('\n🔚 Scraper fermé');
        }
    }
};

// Lancer le test
testDirectPage();

