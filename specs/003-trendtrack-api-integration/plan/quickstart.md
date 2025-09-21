# Guide de Démarrage Rapide : Intégration API TrendTrack

**Branche de Fonctionnalité** : `003-trendtrack-api-integration`  
**Créé** : 2025-09-20  
**Statut** : Guide  
**Basé sur** : [Spec 003](../spec.md)

---

## 🚀 Démarrage Rapide

### Objectif
Intégrer l'API TrendTrack pour récupérer les données de marché (pixels et données géographiques) en utilisant les IDs extraits depuis le DOM de la page de liste des boutiques.

### Durée Estimée
**2-3 heures** pour l'implémentation complète

---

## 📋 Checklist de Démarrage

### ✅ Prérequis
- [ ] Scraper TrendTrack fonctionnel
- [ ] Base de données SQLite configurée
- [ ] Authentification TrendTrack active
- [ ] Compréhension de l'API des pixels existante

### ✅ Fichiers à Modifier
- [ ] `src/extractors/trendtrack-extractor.js` - Extraction des IDs et appels API
- [ ] `src/database/shop-repository.js` - Stockage des données de marché
- [ ] `update-database.js` - Intégration dans le flux principal

### ✅ Tests à Effectuer
- [ ] Test d'extraction des IDs depuis le DOM
- [ ] Test d'appels API avec les bons IDs
- [ ] Test d'extraction des données géographiques
- [ ] Test d'intégration complète

---

## 🔧 Implémentation Étape par Étape

### Étape 1 : Analyser l'API des Pixels (15 min)
```bash
# Examiner le code existant
grep -n "extractPixelsForShopJS" src/extractors/trendtrack-extractor.js
grep -n "shopId" src/extractors/trendtrack-extractor.js
```

**Objectif** : Comprendre comment l'API des pixels fonctionne actuellement

### Étape 2 : Corriger l'Extraction des IDs (30 min)
```javascript
// Dans extractShopData()
const rowHtml = await row.evaluate(el => el.outerHTML);
const rowIdMatch = rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/);
shopData.shopId = rowIdMatch ? rowIdMatch[1] : null;
```

**Objectif** : Utiliser le même ID que l'API des pixels

### Étape 3 : Implémenter l'API des Données Géographiques (45 min)
```javascript
// Nouvelle méthode
async getGeoDataViaAPI(shopId) {
  const result = await this.page.evaluate(async ({ shopId, workspace }) => {
    const response = await fetch(`https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`, {
      headers: {
        'RSC': '1',
        'Accept': 'text/x-component',
        'User-Agent': 'Mozilla/5.0...'
      },
      credentials: 'include'
    });
    
    const text = await response.text();
    // Extraction des données géographiques
    return extractGeography(text);
  }, { shopId, workspace: 'w-al-yakoobs-workspace-x0Qg9st' });
  
  return result;
}
```

**Objectif** : Récupérer les données géographiques via l'API

### Étape 4 : Intégrer dans le Scraper Principal (30 min)
```javascript
// Dans extractShopDetails()
const marketData = await this.getGeoDataViaAPI(shopData.shopId);

const detailData = {
  // ... autres données
  market_us: marketData.market_us,
  market_uk: marketData.market_uk,
  market_de: marketData.market_de,
  market_ca: marketData.market_ca,
  market_au: marketData.market_au,
  market_fr: marketData.market_fr
};
```

**Objectif** : Intégrer l'API dans le flux principal

### Étape 5 : Tester et Valider (30 min)
```bash
# Test rapide
node test-market-api.js

# Vérification en base
sqlite3 data/trendtrack.db "SELECT shop_name, market_us, market_uk FROM shops WHERE market_us > 0 LIMIT 5;"
```

**Objectif** : Valider que tout fonctionne correctement

---

## 🧪 Tests Rapides

### Test 1 : Extraction des IDs
```javascript
// Test d'extraction d'ID depuis le DOM
const testId = await extractor.extractShopDataFromTable(row);
console.log('ID extrait:', testId.shopId);
```

### Test 2 : Appel API
```javascript
// Test d'appel API avec l'ID
const apiData = await extractor.getGeoDataViaAPI(testId.shopId);
console.log('Données API:', apiData);
```

### Test 3 : Intégration Complète
```javascript
// Test du flux complet
const shopData = await extractor.extractShopData(row, true);
console.log('Données complètes:', shopData);
```

---

## 🔍 Debugging

### Problème 1 : ID non extrait
**Symptôme** : `shopId` est `null` ou `undefined`
**Solution** : Vérifier le sélecteur DOM et le format de l'ID

### Problème 2 : Appel API échoue
**Symptôme** : Erreur HTTP ou réponse vide
**Solution** : Vérifier les cookies de session et les headers

### Problème 3 : Données géographiques manquantes
**Symptôme** : Tous les `market_*` sont à 0
**Solution** : Vérifier le pattern de regex et le format de la réponse

### Problème 4 : Données non stockées
**Symptôme** : Données extraites mais pas en base
**Solution** : Vérifier le mapping et l'insertion en base

---

## 📊 Validation des Résultats

### Métriques de Succès
- **IDs extraits** : 100% des boutiques ont un ID valide
- **Appels API** : 90%+ de succès
- **Données géographiques** : 80%+ des boutiques ont des données
- **Performance** : 50%+ plus rapide que l'extraction DOM

### Vérifications
```sql
-- Vérifier les données de marché
SELECT COUNT(*) as total_shops,
       COUNT(CASE WHEN market_us > 0 THEN 1 END) as shops_with_us_data,
       COUNT(CASE WHEN pixel_google = 'oui' THEN 1 END) as shops_with_google_pixel
FROM shops;

-- Vérifier la complétude des données
SELECT shop_name, market_us, market_uk, pixel_google, pixel_facebook
FROM shops 
WHERE market_us > 0 OR pixel_google = 'oui'
LIMIT 10;
```

---

## 🚨 Points d'Attention

### Sécurité
- **Cookies** : Ne pas exposer les cookies de session
- **Rate Limiting** : Respecter les limites de l'API TrendTrack
- **Erreurs** : Gérer gracieusement les erreurs d'API

### Performance
- **Parallélisation** : Limiter le nombre d'appels API simultanés
- **Cache** : Mettre en cache les réponses API si possible
- **Timeout** : Définir des timeouts appropriés

### Fiabilité
- **Retry** : Implémenter un système de retry pour les échecs
- **Fallback** : Prévoir un fallback vers l'extraction DOM
- **Monitoring** : Surveiller les taux de succès et d'erreur

---

## 📝 Notes de Développement

### Bonnes Pratiques
1. **Validation** : Toujours valider les données avant stockage
2. **Logging** : Logger tous les appels API et erreurs
3. **Tests** : Tester avec différentes boutiques
4. **Documentation** : Documenter les changements

### Optimisations
1. **Batch Processing** : Traiter les boutiques par lots
2. **Connection Pooling** : Réutiliser les connexions API
3. **Data Compression** : Compresser les réponses volumineuses
4. **Caching** : Mettre en cache les données fréquemment utilisées

---

## 🎯 Prochaines Étapes

### Après l'Implémentation
1. **Monitoring** : Surveiller les performances en production
2. **Optimisation** : Optimiser les appels API si nécessaire
3. **Extension** : Ajouter d'autres métriques si disponibles
4. **Documentation** : Mettre à jour la documentation

### Évolutions Futures
1. **API Externe** : Intégrer d'autres sources de données
2. **Machine Learning** : Utiliser ML pour prédire les données manquantes
3. **Real-time** : Mettre à jour les données en temps réel
4. **Analytics** : Ajouter des analytics sur les données de marché

---

**Statut du Guide** : ✅ **PRÊT POUR L'IMPLÉMENTATION**

Ce guide permet de démarrer rapidement l'implémentation de l'intégration API TrendTrack. Toutes les étapes sont détaillées et les tests sont prêts.
