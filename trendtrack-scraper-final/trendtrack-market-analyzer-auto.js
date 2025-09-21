#!/usr/bin/env node

/**
 * TRENDTRACK MARKET DATA ANALYZER - VERSION AUTOMATIQUE
 * Utilise les cookies automatiques pour récupérer les données de marché
 */

import { promises as fs } from 'fs';
import path from 'path';

// 🍪 IMPORT AUTOMATIQUE DES COOKIES
let COOKIES = {};

const loadCookies = async () => {
    try {
        // Essayer de charger depuis cookies.js
        const { default: cookiesModule } = await import('./cookies.js');
        COOKIES = cookiesModule;
        console.log('✅ Cookies chargés depuis cookies.js');
        return true;
    } catch {
        try {
            // Essayer cookies.json
            const cookieData = await fs.readFile('cookies.json', 'utf8');
            COOKIES = JSON.parse(cookieData);
            console.log('✅ Cookies chargés depuis cookies.json');
            return true;
        } catch {
            console.warn('⚠️  Aucun fichier de cookies trouvé');
            return false;
        }
    }
};

// 🔄 AUTO-REFRESH DES COOKIES SI NÉCESSAIRE
const ensureValidCookies = async () => {
    const cookiesLoaded = await loadCookies();
    
    if (!cookiesLoaded || Object.keys(COOKIES).length === 0) {
        console.log('🔄 Aucun cookie trouvé, lancement de la récupération automatique...');
        
        try {
            const { refreshCookies } = await import('./cookie-fetcher.js');
            const newCookies = await refreshCookies();
            
            if (newCookies) {
                COOKIES = newCookies;
                return true;
            } else {
                throw new Error('Échec récupération cookies');
            }
        } catch (error) {
            console.error('❌ Impossible de récupérer les cookies automatiquement');
            console.error('💡 Lance d\'abord: node cookie-fetcher.js');
            return false;
        }
    }
    
    // Test rapide de validité
    const testResult = await testCookieValidity();
    if (!testResult) {
        console.log('🔄 Cookies expirés, refresh...');
        try {
            const { refreshCookies } = await import('./cookie-fetcher.js');
            const newCookies = await refreshCookies();
            if (newCookies) {
                COOKIES = newCookies;
                return true;
            }
        } catch (error) {
            console.error('❌ Refresh cookies échoué:', error.message);
            return false;
        }
    }
    
    return true;
};

// 🧪 TEST RAPIDE DE VALIDITÉ DES COOKIES
const testCookieValidity = async () => {
    const cookieString = Object.entries(COOKIES)
        .map(([key, value]) => `${key}=${value}`)
        .join('; ');
    
    if (!cookieString) return false;
    
    try {
        const response = await fetch('https://app.trendtrack.io/api/user/me', {
            headers: {
                "Cookie": cookieString,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0"
            },
            timeout: 5000
        });
        
        return response.ok;
    } catch {
        return false;
    }
};

// 🌍 ANALYSE DES DONNÉES DE MARCHÉ POUR UN SITE
const analyzeMarketData = async (siteId) => {
    console.log(`🌍 Analyse des données de marché pour le site: ${siteId}`);
    
    const cookieString = Object.entries(COOKIES)
        .map(([key, value]) => `${key}=${value}`)
        .join('; ');
    
    try {
        const response = await fetch(`https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${siteId}`, {
            headers: {
                'RSC': '1', 
                'Accept': 'text/x-component',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookieString
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const text = await response.text();
        
        // Extraction des données de marché depuis l'API
        const marketData = {
            market_us: 0,
            market_uk: 0,
            market_de: 0,
            market_ca: 0,
            market_au: 0,
            market_fr: 0,
            countries: []
        };
        
        // 🎯 PATTERN CORRIGÉ : Recherche de la section geography.topCountriesTraffics
        const geoPattern = /"visitsShare":([0-9.]+),"countryUrlCode":"[^"]+","countryAlpha2Code":"([^"]+)"/g;
        let match;
        
        while ((match = geoPattern.exec(text)) !== null) {
            const visitsShare = parseFloat(match[1]);
            const countryCode = match[2].toLowerCase();
            
            marketData.countries.push({
                countryCode: countryCode,
                visitsShare: visitsShare,
                visitsSharePercent: visitsShare * 100
            });
            
            // Mapping vers les champs de marché
            switch (countryCode) {
                case 'us': marketData.market_us = visitsShare; break;
                case 'gb': marketData.market_uk = visitsShare; break; // UK = GB dans l'API
                case 'de': marketData.market_de = visitsShare; break;
                case 'ca': marketData.market_ca = visitsShare; break;
                case 'au': marketData.market_au = visitsShare; break;
                case 'fr': marketData.market_fr = visitsShare; break;
            }
        }
        
        return {
            success: true,
            siteId: siteId,
            ...marketData,
            responseLength: text.length,
            countriesFound: marketData.countries.length
        };
        
    } catch (error) {
        console.error(`❌ Erreur analyse marché pour ${siteId}:`, error.message);
        return {
            success: false,
            siteId: siteId,
            error: error.message
        };
    }
};

// 🌍 ANALYSE POUR PLUSIEURS SITES
const analyzeMultipleMarketData = async (siteIds, delayMs = 1000) => {
    console.log(`🌍 Analyse des données de marché pour ${siteIds.length} sites...`);
    const results = [];
    
    for (let i = 0; i < siteIds.length; i++) {
        const siteId = siteIds[i];
        
        try {
            console.log(`🔍 Analyse marché ${i+1}/${siteIds.length}: ${siteId}`);
            
            const marketData = await analyzeMarketData(siteId);
            
            results.push({
                ...marketData,
                timestamp: new Date().toISOString()
            });
            
            // ⏱️ Pause entre requêtes
            if (i < siteIds.length - 1) {
                await new Promise(resolve => setTimeout(resolve, delayMs));
            }
            
        } catch (error) {
            console.error(`❌ Erreur pour ${siteId}:`, error.message);
            results.push({
                success: false,
                siteId: siteId,
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    return results;
};

// 📊 FORMATAGE SIMPLE POUR EXPORT
const formatMarketDataForExport = (results) => {
    const formatted = [];
    
    results.forEach(result => {
        if (result.success && result.countries) {
            result.countries.forEach(country => {
                formatted.push({
                    site_id: result.siteId,
                    country_code: country.countryCode,
                    visits_share: country.visitsShare,
                    visits_share_percent: country.visitsSharePercent
                });
            });
        }
    });
    
    return formatted;
};

// 🚀 FONCTION PRINCIPALE
const analyzeMarketDataComplete = async (siteIds) => {
    console.log('🎯 === ANALYSE COMPLÈTE DONNÉES DE MARCHÉ (AUTO) ===');
    
    // 1️⃣ S'assurer que les cookies sont valides
    console.log('🍪 Vérification des cookies...');
    const cookiesValid = await ensureValidCookies();
    
    if (!cookiesValid) {
        console.error('❌ Impossible d\'obtenir des cookies valides');
        console.error('💡 Assure-toi que tes identifiants sont corrects dans cookie-fetcher.js');
        return { success: false, error: 'Cookies invalides' };
    }
    
    console.log('✅ Cookies validés');
    
    // 2️⃣ Analyser les données de marché
    console.log('🌍 Analyse des données de marché...');
    const results = await analyzeMultipleMarketData(siteIds, 2000); // 2 secondes de pause
    
    // 3️⃣ Afficher les résultats
    console.log('\n🎯 RÉSULTATS FINAUX:');
    console.log('===================');
    
    results.forEach((result, index) => {
        console.log(`\n📊 Site ${index + 1}: ${result.siteId}`);
        if (result.success) {
            console.log(`✅ Pays trouvés: ${result.countriesFound}`);
            console.log(`📄 Taille réponse: ${result.responseLength} chars`);
            console.log(`🌍 Données marché:`);
            console.log(`   - US: ${result.market_us}`);
            console.log(`   - UK: ${result.market_uk}`);
            console.log(`   - DE: ${result.market_de}`);
            console.log(`   - CA: ${result.market_ca}`);
            console.log(`   - AU: ${result.market_au}`);
            console.log(`   - FR: ${result.market_fr}`);
            
            if (result.countries && result.countries.length > 0) {
                console.log(`🌍 Pays détaillés:`);
                result.countries.slice(0, 5).forEach(country => {
                    console.log(`   - ${country.countryCode.toUpperCase()}: ${country.visitsSharePercent.toFixed(2)}%`);
                });
                if (result.countries.length > 5) {
                    console.log(`   ... et ${result.countries.length - 5} autres pays`);
                }
            }
        } else {
            console.log(`❌ Erreur: ${result.error}`);
        }
    });
    
    // 4️⃣ Formatage pour export
    console.log('\n📊 FORMATAGE POUR EXPORT:');
    console.log('========================');
    const formattedData = formatMarketDataForExport(results);
    console.log(`📈 ${formattedData.length} entrées formatées`);
    
    if (formattedData.length > 0) {
        console.log('\n🔍 Exemples de données formatées:');
        formattedData.slice(0, 10).forEach(entry => {
            console.log(`   ${entry.site_id} | ${entry.country_code.toUpperCase()} | ${entry.visits_share_percent.toFixed(2)}%`);
        });
    }
    
    return {
        success: true,
        results: results,
        formattedData: formattedData
    };
};

// 🎯 LANCEMENT DU SCRIPT
if (import.meta.url === `file://${process.argv[1]}`) {
    const siteIds = process.argv.slice(2);
    
    if (siteIds.length === 0) {
        console.log('💡 Usage: node trendtrack-market-analyzer-auto.js <siteId1> <siteId2> ...');
        console.log('💡 Exemple: node trendtrack-market-analyzer-auto.js 2804 2803 2802');
        process.exit(1);
    }
    
    analyzeMarketDataComplete(siteIds)
        .then(result => {
            if (result.success) {
                console.log('\n🎉 ANALYSE TERMINÉE AVEC SUCCÈS !');
            } else {
                console.log('\n❌ ANALYSE ÉCHOUÉE');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('❌ Erreur fatale:', error.message);
            process.exit(1);
        });
}

export {
    analyzeMarketData,
    analyzeMultipleMarketData,
    formatMarketDataForExport,
    analyzeMarketDataComplete
};
