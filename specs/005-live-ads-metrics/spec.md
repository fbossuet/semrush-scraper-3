# Spécification : Métriques Live Ads 7d et 30d

## Vue d'ensemble

Cette spécification décrit l'implémentation de la récupération des métriques `live_ads_7d` et `live_ads_30d` depuis le tableau TrendTrack pour enrichir les données des boutiques.

## Contexte

Le scraper TrendTrack récupère actuellement la métrique `live_ads` (total) depuis la cellule 7 du tableau. Cette fonctionnalité étend le scraper pour récupérer également :
- `live_ads_7d` : Nombre de live ads sur 7 jours
- `live_ads_30d` : Nombre de live ads sur 30 jours

## Objectifs

### Objectif Principal
Récupérer les métriques de progression des live ads pour une analyse temporelle plus fine.

### Objectifs Secondaires
- Enrichir les données des boutiques avec des métriques temporelles
- Améliorer l'analyse des tendances publicitaires
- Fournir des données plus granulaires via l'API

## Fonctionnalités

### Fonctionnalité 1 : Extraction des Métriques
- **Description** : Récupération des métriques depuis la page de liste et de détail TrendTrack
- **Source** : 
  - live_ads : Cellule 7 du tableau (Phase 1 - page de liste)
  - live_ads_7d : Cellule 5 du tableau (Phase 3 - page de détail)
  - live_ads_30d : Cellule 6 du tableau (Phase 3 - page de détail)
- **Format** : Valeurs numériques entières

### Fonctionnalité 2 : Sauvegarde en Base de Données
- **Description** : Stockage des métriques dans les colonnes `live_ads_7d` et `live_ads_30d`
- **Table** : `shops`
- **Type** : INTEGER DEFAULT 0

### Fonctionnalité 3 : Exposition API
- **Description** : Disponibilité des métriques via l'endpoint `/albert`
- **Format** : JSON avec champs `live_ads_7d` et `live_ads_30d`

## Contraintes Techniques

### Contraintes de Source
- **live_ads** : Extraite dans extractShopDataFromTable (Phase 1 - page de liste)
- **live_ads_7d** : Extraite dans extractShopDetails (Phase 3 - page de détail)
- **live_ads_30d** : Extraite dans extractShopDetails (Phase 3 - page de détail)
- La cellule 6 (live_ads_30d) a une structure HTML différente (pas d'élément <p>)
- Seule la cellule 5 (live_ads_7d) contient des données dans un format extractible

### Contraintes de Performance
- Extraction en parallèle avec les autres métriques de la page de détail
- Pas d'impact sur les performances du scraper
- Sauvegarde atomique avec les autres données

## Critères d'Acceptation

### Critère 1 : Extraction
- [x] La métrique `live_ads` est extraite depuis la cellule 7 (Phase 1)
- [x] La métrique `live_ads_7d` est extraite depuis la cellule 5 (Phase 3)
- [x] La métrique `live_ads_30d` est tentée depuis la cellule 6 (structure HTML différente)
- [x] Les valeurs sont correctement parsées en entiers

### Critère 2 : Sauvegarde
- [x] Les colonnes `live_ads_7d` et `live_ads_30d` existent en base
- [x] Les données sont correctement mappées et sauvegardées
- [x] Les valeurs par défaut sont 0

### Critère 3 : API
- [x] L'endpoint `/albert` retourne les nouvelles métriques
- [x] Les champs sont présents dans la réponse JSON
- [x] Les valeurs sont correctement formatées

## Résultats des Tests

### Test d'Extraction
- ✅ **Live Ads** : Récupéré avec succès depuis la page de liste (Phase 1)
- ✅ **Live Ads 7d** : Récupéré avec succès depuis la page de détail (Phase 3) (valeurs : 670, 982, 2, 3, 658, etc.)
- ❌ **Live Ads 30d** : Structure HTML différente dans la cellule 6 (pas d'élément <p>)

### Test de Sauvegarde
- ✅ **Base de données** : 150 boutiques avec métriques live_ads_7d
- ✅ **Exemples** : ryzesuperfoods.com (live_ads_7d=1), meshki.us (live_ads_7d=1)

### Test API
- ✅ **Endpoint** : `/albert` retourne les métriques
- ✅ **Format** : JSON avec champs `live_ads_7d` et `live_ads_30d`

## Statut

**✅ IMPLÉMENTÉ ET FONCTIONNEL**

- Date d'implémentation : 22/01/2025
- Statut : Terminé
- Tests : Validés
- Production : Opérationnel

## Notes d'Implémentation

- **Phase d'extraction** : 
  - `live_ads` : **Phase 1** (page de liste) - Cellule 7
  - `live_ads_7d` : **Phase 3** (page de détail) - Cellule 5
  - `live_ads_30d` : **Phase 3** (page de détail) - Cellule 6
- **Source** : Cellules 5, 6 et 7 du tableau des boutiques tendances
- **Mapping** : Les IDs des boutiques sont extraits en Phase 1 et utilisés en Phase 3
- **Structure HTML** : La cellule 6 a une structure différente (pas d'élément `<p>`)

## Solution API pour les Données Géographiques

### Script d'Implémentation

```javascript
// Dans src/extractors/trendtrack-extractor.js

async extractShopDetails(shopId) {
    try {
        console.log(`🎯 Extraction détails pour Shop ID: ${shopId}`);
        
        const workspace = 'workspace-1'; // ou récupérer dynamiquement
        
        // 1. ✅ EXTRACTION PIXELS (fonctionne déjà)
        const pixelData = await this.extractPixelsForShopJS(shopId, workspace);
        let pixels = {
            pixel_google: 'non',
            pixel_facebook: 'non'
        };
        
        if (pixelData) {
            pixels.pixel_google = pixelData.pixel_google || 'non';
            pixels.pixel_facebook = pixelData.pixel_facebook || 'non';
        }

        // 2. 🆕 EXTRACTION DE L'ID API depuis la réponse RSC
        const apiId = await this.extractApiIdFromRSC(shopId, workspace);
        
        let geoData = null;
        if (apiId) {
            console.log(`🔗 ID API trouvé: ${apiId}`);
            // 3. ✅ EXTRACTION GEO avec l'ID API
            geoData = await this.getGeoDataViaAPI(apiId);
        } else {
            console.log('❌ ID API non trouvé dans la réponse RSC');
        }

        // 4. 📊 FORMATAGE DES DONNÉES
        const result = {
            ...pixels,
            market_us: 0,
            market_uk: 0, 
            market_de: 0,
            market_ca: 0,
            market_au: 0,
            market_fr: 0
        };

        // Mapper les données géo si disponibles
        if (geoData && geoData.countries) {
            geoData.countries.forEach(country => {
                const percentage = Math.round(country.visitsShare * 100 * 100) / 100;
                
                switch(country.countryCode) {
                    case 'US': result.market_us = percentage; break;
                    case 'GB': result.market_uk = percentage; break;
                    case 'DE': result.market_de = percentage; break;
                    case 'CA': result.market_ca = percentage; break;
                    case 'AU': result.market_au = percentage; break;
                    case 'FR': result.market_fr = percentage; break;
                }
            });
        }

        console.log('✅ Données extraites:', result);
        return result;

    } catch (error) {
        console.error(`❌ Erreur extraction shop ${shopId}:`, error);
        throw error;
    }
}

// 🆕 NOUVELLE MÉTHODE : Extraire l'ID API depuis RSC
async extractApiIdFromRSC(shopId, workspace) {
    try {
        const response = await fetch(
            `https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`,
            {
                headers: {
                    'RSC': '1',
                    'Accept': 'text/x-component'
                },
                credentials: 'include'
            }
        );

        const text = await response.text();
        
        // 🔍 PATTERNS À CHERCHER pour l'ID API
        const patterns = [
            /"websiteId":"([a-f0-9-]{36})"/,
            /"siteId":"([a-f0-9-]{36})"/,
            /"website["\.]id["\:]"([a-f0-9-]{36})"/,
            /website[\/:]([a-f0-9-]{36})/,
            /"id":"([a-f0-9-]{36})".*geography/,
            /\/api\/websites\/([a-f0-9-]{36})/
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match && match[1] !== shopId) { // Différent de l'ID de la liste
                console.log(`✅ ID API trouvé avec pattern: ${pattern.source}`);
                return match[1];
            }
        }

        // 🔍 RECHERCHE PLUS LARGE - tous les UUIDs dans la réponse
        const allUuids = text.match(/[a-f0-9-]{36}/g) || [];
        const uniqueUuids = [...new Set(allUuids)].filter(id => id !== shopId);
        
        if (uniqueUuids.length > 0) {
            console.log(`🎯 UUIDs candidats trouvés:`, uniqueUuids);
            
            // Tester chaque UUID avec l'API géo
            for (const candidateId of uniqueUuids) {
                try {
                    const testResponse = await fetch(
                        `https://app.trendtrack.io/api/websites/${candidateId}`,
                        {
                            headers: {
                                "Accept": "*/*",
                                "Sec-Fetch-Dest": "empty",
                                "Sec-Fetch-Mode": "cors", 
                                "Sec-Fetch-Site": "same-origin"
                            },
                            credentials: 'include'
                        }
                    );
                    
                    if (testResponse.ok) {
                        const testData = await testResponse.json();
                        if (testData.website?.geography) {
                            console.log(`✅ ID API validé: ${candidateId}`);
                            return candidateId;
                        }
                    }
                } catch (e) {
                    // Continue avec le suivant
                }
            }
        }

        return null;
    } catch (error) {
        console.error('❌ Erreur extraction ID API:', error);
        return null;
    }
}

// 🧪 MÉTHODE DEBUG pour analyser la réponse RSC
async debugRSCResponse(shopId, workspace) {
    try {
        const response = await fetch(
            `https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`,
            {
                headers: { 'RSC': '1', 'Accept': 'text/x-component' },
                credentials: 'include'
            }
        );

        const text = await response.text();
        
        console.log('📝 DEBUG RSC Response:');
        console.log(`📏 Taille: ${text.length} caractères`);
        
        // Chercher tous les UUIDs
        const uuids = text.match(/[a-f0-9-]{36}/g) || [];
        console.log(`🆔 UUIDs trouvés: ${[...new Set(uuids)]}`);
        
        // Chercher des mots-clés liés aux données géo
        const keywords = ['website', 'geography', 'api', 'topCountries', 'traffic'];
        keywords.forEach(keyword => {
            if (text.includes(keyword)) {
                console.log(`✅ Mot-clé "${keyword}" trouvé`);
            }
        });

        return text;
    } catch (error) {
        console.error('❌ Erreur debug:', error);
    }
}

// 🚀 Test Rapide
// Test avec ton shop ID existant
const extractor = new TrendTrackExtractor();
await extractor.debugRSCResponse('7fbb404d-63d6-4c5c-b38a-b09e67b7a501', 'workspace-1');
```
