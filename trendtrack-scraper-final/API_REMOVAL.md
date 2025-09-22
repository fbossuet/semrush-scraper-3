# 🗑️ SUPPRESSION DES MÉTHODES API POUR LES DONNÉES GÉOGRAPHIQUES

## 📋 RÉSUMÉ

Les méthodes d'extraction des données géographiques via l'API TrendTrack ont été supprimées car elles ne fonctionnaient pas correctement. Ce document explique pourquoi et ce qui a été supprimé.

## 🎯 OBJECTIF INITIAL

L'objectif était de résoudre le problème des données géographiques vides (0 pays) en utilisant l'API TrendTrack pour récupérer les données de trafic par pays.

### Problème identifié
- **ID de la page de liste** : `7fbb404d-63d6-4c5c-b38a-b09e67b7a501`
- **ID de l'API** : `90c2965f-9881-40ce-bcb7-f7da383fd815`
- **Problème** : Ces deux IDs sont différents et l'API géo ne fonctionne qu'avec l'ID API

## 🚫 MÉTHODES SUPPRIMÉES

### 1. `extractApiIdFromRSC(shopId, workspace)`

**Objectif** : Extraire l'ID API depuis la réponse RSC de la page de liste TrendTrack.

**Code supprimé** :
```javascript
async extractApiIdFromRSC(shopId, workspace = 'w-al-yakoobs-workspace-x0Qg9st') {
  console.log(`🔍 Extraction de l'ID API pour: ${shopId}`);
  
  try {
    const result = await this.page.evaluate(async ({ shopId, workspace }) => {
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

        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` };
        }

        const text = await response.text();
        
        // 🔍 PATTERNS À CHERCHER pour l'ID API (basés sur le rapport)
        const patterns = [
          /"websiteId":"([^"]+)"/,  // Pattern principal du rapport
          /"siteId":"([^"]+)"/,
          /"website["\.]id["\:]"([^"]+)"/,
          /website[\/:]([a-f0-9-]{36})/,
          /"id":"([a-f0-9-]{36})".*geography/,
          /\/api\/websites\/([a-f0-9-]{36})/,
          /"websiteId":"([a-f0-9-]{36})"/,  // Version UUID stricte
          /"siteId":"([a-f0-9-]{36})"/      // Version UUID stricte
        ];

        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match && match[1] !== shopId) { // Différent de l'ID de la liste
            console.log(`✅ ID API trouvé avec pattern: ${pattern.source}`);
            return { 
              success: true, 
              apiId: match[1], 
              pattern: pattern.source,
              responseLength: text.length 
            };
          }
        }
        
        // 🔍 RECHERCHE PLUS LARGE - tous les UUIDs dans la réponse
        const allUuids = text.match(/[a-f0-9-]{36}/g) || [];
        const uniqueUuids = [...new Set(allUuids)].filter(id => id !== shopId);
        
        if (uniqueUuids.length > 0) {
          console.log(`🎯 UUIDs candidats trouvés:`, uniqueUuids);
          
          // Tester chaque UUID avec l'API géo
          console.log(`🧪 Test de ${uniqueUuids.length} UUIDs candidats...`);
          for (let i = 0; i < Math.min(uniqueUuids.length, 10); i++) { // Tester les 10 premiers
            const candidateId = uniqueUuids[i];
            try {
              console.log(`🔍 Test ${i + 1}/10: ${candidateId}`);
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
              
              console.log(`📊 Status: ${testResponse.status}`);
              
              if (testResponse.ok) {
                const testData = await testResponse.json();
                console.log(`📋 Réponse: ${JSON.stringify(testData).substring(0, 200)}...`);
                
                if (testData.website?.geography) {
                  console.log(`✅ ID API validé: ${candidateId}`);
                  return { 
                    success: true, 
                    apiId: candidateId, 
                    pattern: 'candidate_validation',
                    responseLength: text.length 
                  };
                } else {
                  console.log(`⚠️ Pas de géo pour: ${candidateId}`);
                }
              } else {
                console.log(`❌ HTTP ${testResponse.status} pour: ${candidateId}`);
              }
            } catch (e) {
              console.log(`❌ Erreur pour ${candidateId}: ${e.message}`);
            }
          }
        }

        return { 
          success: false, 
          allUuids: uniqueUuids, 
          responseLength: text.length,
          message: 'Aucun ID API valide trouvé'
        };

      } catch (error) {
        return { error: error.message };
      }
    }, { shopId, workspace });

    if (result.error) {
      console.error('❌ Erreur extraction ID API:', result.error);
      return null;
    }

    if (result.success) {
      console.log(`✅ ID API extrait: ${result.apiId}`);
      return result.apiId;
    } else {
      console.log('⚠️ Aucun ID API trouvé dans la réponse RSC');
      console.log(`🆔 UUIDs disponibles: ${result.allUuids?.join(', ')}`);
      return null;
    }

  } catch (error) {
    console.error('❌ Erreur extraction ID API:', error);
    return null;
  }
}
```

### 2. `getGeoDataViaAPI(siteId)`

**Objectif** : Récupérer les données géographiques via l'API TrendTrack.

**Code supprimé** :
```javascript
async getGeoDataViaAPI(siteId) {
  console.log(`🌍 Récupération données géo (API) pour: ${siteId}`);
  
  try {
    // Utiliser l'ID passé en paramètre directement
    let actualSiteId = siteId;
    if (siteId === 'current_shop') {
      console.log('⚠️ ID générique utilisé, les données peuvent être incorrectes');
    } else {
      console.log(`🔍 Utilisation de l'ID TrendTrack: ${actualSiteId}`);
    }
    
    // 🍪 Utilisation des cookies automatiques depuis le navigateur
    const result = await this.page.evaluate(async ({ siteId, workspace }) => {
      try {
        // Récupération automatique des cookies du navigateur
        const cookies = await document.cookie;
        const cookieString = cookies;
        
        const response = await fetch(`https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${siteId}`, {
          headers: {
            'RSC': '1', 
            'Accept': 'text/x-component',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }, 
          credentials: 'include'
        });
        
        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` };
        }
        
        const text = await response.text();
        
        // 🎯 Extraction des données géographiques depuis la réponse RSC
        const marketData = {
          market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0, 
          countries: []
        };
        
        // Rechercher les données géographiques dans la réponse RSC
        // Pattern pour les données géographiques : "visitsShare":0.7463570938382258,"countryUrlCode":"united-states","countryAlpha2Code":"US"
        const geoPattern = /"visitsShare":([0-9.]+),"countryUrlCode":"[^"]+","countryAlpha2Code":"([^"]+)"/g;
        let match;
        
        while ((match = geoPattern.exec(text)) !== null) {
          const visitsShare = parseFloat(match[1]);
          const countryCode = match[2].toLowerCase();
          
          marketData.countries.push({
            countryCode: countryCode,
            visitsShare: visitsShare,
            visitsSharePercent: Math.round(visitsShare * 100 * 100) / 100,
            countryName: match[0].match(/"countryUrlCode":"([^"]+)"/)[1]
          });
          
          switch (countryCode) {
            case 'us': marketData.market_us = visitsShare; break;
            case 'gb': marketData.market_uk = visitsShare; break;
            case 'de': marketData.market_de = visitsShare; break;
            case 'ca': marketData.market_ca = visitsShare; break;
            case 'au': marketData.market_au = visitsShare; break;
            case 'fr': marketData.market_fr = visitsShare; break;
          }
        }
        
        return { 
          ...marketData,
          countriesFound: marketData.countries.length,
          responseLength: text.length,
          cookieUsed: cookieString ? 'Oui' : 'Non'
        };
        
      } catch (error) {
        return { error: error.message };
      }
    }, { siteId: actualSiteId, workspace: 'w-al-yakoobs-workspace-x0Qg9st' });
    
    if (result.error) {
      console.error(`❌ Erreur API géo pour ${siteId}:`, result.error);
      return { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0 };
    }
    
    console.log(`✅ Données géo extraites pour ${siteId}: ${result.countriesFound} pays (${result.responseLength} chars, cookies: ${result.cookieUsed})`);
    return result;
    
  } catch (error) {
    console.error(`❌ Erreur extraction géo pour ${siteId}:`, error.message);
    return { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0 };
  }
}
```

### 3. Appels supprimés dans `extractShopDetails`

**Code supprimé** :
```javascript
// 🆕 NOUVELLE MÉTHODE : Extraction de l'ID API depuis la réponse RSC
let marketData = null;
if (shopId) {
  const apiId = await this.extractApiIdFromRSC(shopId);
  
  if (apiId) {
    console.log(`🔗 ID API trouvé: ${apiId}`);
    // 🚀 NOUVELLE MÉTHODE : Extraction des données de marché via API TrendTrack avec l'ID API
    console.log('🌍 Extraction des données de marché via API TrendTrack avec ID API...');
    marketData = await this.getGeoDataViaAPI(apiId);
  } else {
    console.log('❌ ID API non trouvé, utilisation de l\'ID de la page de liste');
    // Fallback vers l'ancienne méthode
    marketData = await this.getGeoDataViaAPI(shopId);
  }
} else {
  console.log('⚠️ Pas d\'ID de boutique fourni, utilisation de la méthode par défaut');
  marketData = await this.getGeoDataViaAPI('current_shop');
}
```

## ❌ POURQUOI ÇA NE MARCHAIT PAS

### 1. **Problème de mapping des IDs**
- L'ID de la page de liste (`7fbb404d-63d6-4c5c-b38a-b09e67b7a501`) est différent de l'ID API (`90c2965f-9881-40ce-bcb7-f7da383fd815`)
- L'API géo ne fonctionne qu'avec l'ID API, pas avec l'ID de la page de liste

### 2. **L'ID API n'est pas dans la réponse RSC**
- La réponse RSC de la page de liste ne contient pas les patterns `"websiteId"`, `"siteId"`, `"geography"`, ou `/api/websites/`
- Les UUIDs trouvés dans la réponse RSC ne sont pas des IDs API valides

### 3. **L'ID API n'est pas dans la page de détail non plus**
- La page de détail TrendTrack ne contient pas non plus l'ID API
- Les patterns recherchés ne correspondent pas à la structure réelle des pages

### 4. **Validation des UUIDs échoue**
- Les UUIDs trouvés dans les réponses ne fonctionnent pas avec l'API géo
- L'API retourne `{"error":"User not found"}` pour tous les UUIDs testés

## 🧪 TESTS EFFECTUÉS

### Tests de la réponse RSC
- **Taille de la réponse** : 138,313 caractères
- **Contient "websiteId"** : false
- **Contient "siteId"** : false
- **Contient "geography"** : false
- **Contient "/api/websites/"** : false
- **UUIDs trouvés** : 2 (mais aucun ne fonctionne avec l'API géo)

### Tests de la page de détail
- **Taille HTML** : 165,426 caractères
- **UUIDs trouvés** : 2 (mais aucun ne fonctionne avec l'API géo)
- **Aucun UUID validé avec l'API géo**

### Tests de validation des UUIDs
- **UUIDs testés** : Plus de 100 UUIDs différents
- **Résultat** : Tous retournent `{"error":"User not found"}`
- **Conclusion** : Les UUIDs trouvés ne sont pas des IDs API valides

## 🔄 ÉTAT ACTUEL

### Ce qui fonctionne
- ✅ **Extraction des pixels** : Fonctionne parfaitement avec l'ID de la page de liste
- ✅ **Extraction des métriques de base** : Fonctionne correctement
- ✅ **Extraction des données de table** : Fonctionne correctement

### Ce qui ne fonctionne pas
- ❌ **Données géographiques** : Toujours à 0 pays
- ❌ **Mapping des IDs** : Impossible de trouver l'ID API depuis l'ID de la page de liste
- ❌ **API géo** : Ne fonctionne qu'avec l'ID API manuel

## 🚀 CE QUI RESTERAIT À FAIRE

### 1. **Investigation approfondie de l'API TrendTrack**
- Analyser toutes les APIs disponibles dans l'application TrendTrack
- Identifier où l'ID API est réellement stocké ou accessible
- Comprendre la structure complète de l'API TrendTrack

### 2. **Approche alternative : Scraping direct**
- Extraire les données géographiques directement depuis la page de détail TrendTrack
- Analyser le HTML/JavaScript de la page pour trouver les données géo
- Utiliser des sélecteurs CSS ou des patterns de texte

### 3. **Approche alternative : API externe**
- Utiliser une API externe pour les données géographiques (ex: SimilarWeb, SEMrush)
- Intégrer une solution de géolocalisation basée sur l'IP
- Utiliser des données de trafic estimées

### 4. **Approche alternative : Base de données manuelle**
- Créer une base de données manuelle des correspondances ID liste → ID API
- Mapper manuellement les boutiques importantes
- Utiliser des heuristiques pour estimer les données géo

### 5. **Approche alternative : Machine Learning**
- Entraîner un modèle pour prédire les données géographiques
- Utiliser les données existantes pour créer des patterns
- Implémenter une solution de fallback intelligente

## 📝 CONCLUSION

L'approche API pour récupérer les données géographiques a échoué car :
1. L'ID API n'est pas accessible depuis l'ID de la page de liste
2. Les patterns de recherche ne correspondent pas à la structure réelle
3. Les UUIDs trouvés ne sont pas des IDs API valides

**Recommandation** : Explorer des approches alternatives comme le scraping direct ou l'utilisation d'APIs externes pour résoudre le problème des données géographiques vides.

---

*Document créé le 22 septembre 2025 - Suppression des méthodes API non fonctionnelles*
