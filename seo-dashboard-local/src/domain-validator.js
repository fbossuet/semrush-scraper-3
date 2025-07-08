// 🔍 Validateur de Domaines SEO
// Détecte si un domaine est présent dans les bases de données SEO

export class DomainValidator {
    
    constructor(page) {
        this.page = page;
        this.errorMessages = [
            'No data available',
            'Domain not found',
            'Insufficient data',
            'Not enough data',
            'No data for this domain',
            'Domain not in database',
            'Data unavailable',
            'No traffic data',
            'Site not found',
            'No organic data',
            'Pas de données disponibles',
            'Domaine non trouvé',
            'Données insuffisantes',
            'Aucune donnée'
        ];
    }

    /**
     * Vérifie si un domaine est répertorié dans les bases SEO
     */
    async checkDomainInSEODatabase(domain, analyticsUrl) {
        console.log(`🔍 Vérification de ${domain} dans les bases SEO...`);
        
        try {
            // Aller sur la page d'analytics du domaine
            const response = await this.page.goto(analyticsUrl, { 
                waitUntil: 'domcontentloaded',
                timeout: 30000 
            });
            
            if (!response || !response.ok()) {
                return {
                    found: false,
                    reason: 'PAGE_INACCESSIBLE',
                    message: 'Impossible d\'accéder à la page d\'analyse'
                };
            }

            // Attendre le chargement des données
            await this.page.waitForTimeout(5000);
            
            // Récupérer le contenu de la page
            const pageContent = await this.page.textContent('body');
            const htmlContent = await this.page.content();
            
            // Vérifier les messages d'erreur
            const hasErrorMessage = this.errorMessages.some(msg => 
                pageContent.toLowerCase().includes(msg.toLowerCase())
            );
            
            if (hasErrorMessage) {
                const foundError = this.errorMessages.find(msg => 
                    pageContent.toLowerCase().includes(msg.toLowerCase())
                );
                
                return {
                    found: false,
                    reason: 'DOMAINE_NON_REPERTORIE',
                    message: `Domaine non répertorié dans la base de données SEO`,
                    errorFound: foundError
                };
            }
            
            // Vérifier s'il y a des données numériques significatives
            const hasMetrics = this.checkForMetrics(pageContent);
            
            if (!hasMetrics.found) {
                return {
                    found: false,
                    reason: 'DONNEES_INSUFFISANTES',
                    message: 'Aucune métrique SEO trouvée pour ce domaine',
                    details: hasMetrics.details
                };
            }
            
            // Domaine semble avoir des données
            return {
                found: true,
                message: 'Domaine répertorié avec des données disponibles',
                metrics: hasMetrics.metrics
            };
            
        } catch (error) {
            console.error(`❌ Erreur validation ${domain}:`, error.message);
            return {
                found: false,
                reason: 'ERREUR_TECHNIQUE',
                message: `Erreur lors de la vérification: ${error.message}`
            };
        }
    }

    /**
     * Vérifie la présence de métriques sur la page
     */
    checkForMetrics(pageContent) {
        const result = {
            found: false,
            metrics: [],
            details: {}
        };
        
        // Patterns de métriques courantes
        const metricPatterns = [
            /(\d+\.?\d*[KMBkm])\s*(visits|visitors|traffic|organic|keywords|backlinks)/gi,
            /(?:visits|visitors|traffic|organic|keywords|backlinks)[:\s]*(\d+\.?\d*[KMBkm])/gi,
            /(\d{1,3}(?:,\d{3})*)\s*(visits|visitors|traffic)/gi
        ];
        
        // Chercher les métriques
        metricPatterns.forEach((pattern, index) => {
            const matches = [...pageContent.matchAll(pattern)];
            if (matches.length > 0) {
                result.found = true;
                matches.forEach(match => {
                    result.metrics.push({
                        value: match[1] || match[2],
                        type: match[2] || match[1],
                        pattern: index + 1
                    });
                });
            }
        });
        
        // Comptage de nombres sur la page (indicateur de données)
        const numbers = pageContent.match(/\d+\.?\d*[KMBkm]/g) || [];
        result.details.numbersFound = numbers.length;
        result.details.uniqueNumbers = [...new Set(numbers)];
        
        // Si au moins 3 nombres avec suffixes, probablement des données valides
        if (numbers.length >= 3) {
            result.found = true;
        }
        
        return result;
    }

    /**
     * Suggestions de domaines de test connus
     */
    getSuggestedTestDomains() {
        return {
            popular: [
                'amazon.com',
                'wikipedia.org', 
                'airbnb.com',
                'shopify.com',
                'github.com'
            ],
            ecommerce: [
                'amazon.com',
                'shopify.com',
                'etsy.com',
                'ebay.com'
            ],
            tested: [
                'the-foldie.com' // Déjà testé avec succès
            ]
        };
    }

    /**
     * Vérifie si un domaine existe (accessible web)
     */
    async checkDomainExists(domain) {
        try {
            // Enlever le protocole si présent
            const cleanDomain = domain.replace(/^https?:\/\//, '');
            const testUrl = `https://${cleanDomain}`;
            
            const response = await this.page.goto(testUrl, { 
                waitUntil: 'domcontentloaded',
                timeout: 15000 
            });
            
            return {
                exists: response && response.ok(),
                status: response ? response.status() : null,
                url: testUrl
            };
            
        } catch (error) {
            return {
                exists: false,
                error: error.message,
                url: `https://${domain}`
            };
        }
    }

    /**
     * Rapport complet de validation d'un domaine
     */
    async validateDomainCompletely(domain) {
        console.log(`🔍 VALIDATION COMPLÈTE: ${domain}`);
        console.log('═'.repeat(50));
        
        const result = {
            domain,
            timestamp: new Date().toISOString(),
            webAccessible: null,
            seoDatabase: null,
            recommendations: []
        };
        
        // 1. Vérifier l'existence web
        console.log('📡 Vérification accessibilité web...');
        result.webAccessible = await this.checkDomainExists(domain);
        
        if (!result.webAccessible.exists) {
            result.recommendations.push('Vérifier l\'orthographe du domaine');
            result.recommendations.push('S\'assurer que le site est en ligne');
            
            console.log(`❌ Domaine non accessible: ${result.webAccessible.error}`);
            return result;
        }
        
        console.log(`✅ Domaine accessible (${result.webAccessible.status})`);
        
        // 2. Vérifier présence dans bases SEO
        console.log('📊 Vérification bases de données SEO...');
        const analyticsUrl = `https://server1.noxtools.com/analytics/overview/?db=us&q=${encodeURIComponent(domain)}&searchType=domain`;
        
        result.seoDatabase = await this.checkDomainInSEODatabase(domain, analyticsUrl);
        
        if (!result.seoDatabase.found) {
            result.recommendations.push('Utiliser un domaine plus populaire pour tester');
            result.recommendations.push('Vérifier sur similarweb.com si des données existent');
            
            if (result.seoDatabase.reason === 'DOMAINE_NON_REPERTORIE') {
                result.recommendations.push('Site probablement trop petit (< 1000 visiteurs/mois)');
            }
        }
        
        // 3. Suggestions selon le résultat
        if (!result.seoDatabase.found) {
            const suggestions = this.getSuggestedTestDomains();
            result.alternativeDomains = suggestions.popular;
        }
        
        return result;
    }

    /**
     * Affiche un rapport de validation formaté
     */
    displayValidationReport(validationResult) {
        const { domain, webAccessible, seoDatabase, recommendations, alternativeDomains } = validationResult;
        
        console.log(`\n🎯 RAPPORT DE VALIDATION: ${domain}`);
        console.log('═'.repeat(60));
        
        // Accessibilité web
        console.log('\n📡 ACCESSIBILITÉ WEB:');
        if (webAccessible.exists) {
            console.log(`   ✅ Site accessible (HTTP ${webAccessible.status})`);
        } else {
            console.log(`   ❌ Site inaccessible: ${webAccessible.error}`);
        }
        
        // Base de données SEO
        console.log('\n📊 BASES DE DONNÉES SEO:');
        if (seoDatabase.found) {
            console.log(`   ✅ Domaine répertorié avec données`);
            if (seoDatabase.metrics) {
                console.log(`   📈 Métriques trouvées: ${seoDatabase.metrics.length}`);
            }
        } else {
            console.log(`   ❌ ${seoDatabase.message}`);
            if (seoDatabase.reason) {
                console.log(`   🔍 Raison: ${seoDatabase.reason}`);
            }
        }
        
        // Recommandations
        if (recommendations.length > 0) {
            console.log('\n💡 RECOMMANDATIONS:');
            recommendations.forEach(rec => {
                console.log(`   • ${rec}`);
            });
        }
        
        // Domaines alternatifs
        if (alternativeDomains) {
            console.log('\n🧪 DOMAINES DE TEST SUGGÉRÉS:');
            alternativeDomains.forEach(domain => {
                console.log(`   • ${domain}`);
            });
        }
        
        console.log('');
    }
}

// Export des fonctions utilitaires
export async function validateDomain(page, domain) {
    const validator = new DomainValidator(page);
    const result = await validator.validateDomainCompletely(domain);
    validator.displayValidationReport(result);
    return result;
}

export function createValidationResponse(domain, validationResult) {
    if (validationResult.seoDatabase.found) {
        return {
            success: true,
            domain,
            message: 'Domaine validé avec succès',
            data: validationResult
        };
    } else {
        return {
            success: false,
            domain,
            reason: validationResult.seoDatabase.reason || 'VALIDATION_FAILED',
            message: validationResult.seoDatabase.message,
            suggestions: validationResult.recommendations,
            alternativeDomains: validationResult.alternativeDomains
        };
    }
}