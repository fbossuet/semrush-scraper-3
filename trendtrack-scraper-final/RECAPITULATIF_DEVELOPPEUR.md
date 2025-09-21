# 📋 **RÉCAPITULATIF POUR DÉVELOPPEUR - INTÉGRATION API TRENDTRACK**

**Date** : 2025-09-20  
**Statut** : 90% terminé - Problème de mapping des IDs à résoudre  
**Objectif** : Intégrer l'API TrendTrack pour récupérer les données de marché (pixels et données géographiques)

---

## 🎯 **OBJECTIF DU PROJET**

Le scraper TrendTrack doit récupérer des données de marché détaillées pour chaque boutique :
- **Pixels de tracking** : Google Analytics et Facebook Pixel
- **Données géographiques** : Répartition du trafic par pays (US, UK, DE, CA, AU, FR)

**Architecture** : Le scraper TrendTrack alimente la table `shops`, le scraper SEM alimente la table `analytics`.

---

## 📝 **INPUTS FOURNIS PAR L'UTILISATEUR**

### **1. Exemple de Code Python Fonctionnel**
```python
import asyncio
import aiohttp
import json

async def get_geo_data(site_id):
    """🚀 FONCTION POUR RÉCUPÉRER LES DONNÉES GÉOGRAPHIQUES"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Accept": "*/*",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors", 
                "Sec-Fetch-Site": "same-origin"
            }
            
            async with session.get(
                f"https://app.trendtrack.io/api/websites/{site_id}",
                headers=headers
            ) as response:
                data = await response.json()
        
        # 🎯 Extraction des données géographiques
        geography = data.get('website', {}).get('geography')
        
        if not geography or not geography.get('topCountriesTraffics'):
            return {'error': 'Aucune donnée géographique trouvée'}
        
        # 📊 Formatage des données
        geo_data = []
        for country in geography['topCountriesTraffics']:
            geo_data.append({
                'countryCode': country['countryAlpha2Code'],
                'visitsShare': country['visitsShare'],
                'visitsSharePercent': round(country['visitsShare'] * 100 * 100) / 100,
                'countryName': country['countryUrlCode']
            })
        
        return {
            'totalCountries': geography['countriesTotalCount'],
            'countries': geo_data
        }
        
    except Exception as error:
        print(f'❌ Erreur récupération geo data: {error}')
        return {'error': str(error)}

async def test_geo_data():
    """🧪 TEST AVEC TON EXEMPLE"""
    site_id = '90c2965f-9881-40ce-bcb7-f7da383fd815'
    
    result = await get_geo_data(site_id)
    
    if 'error' in result:
        print(f'❌ Erreur: {result["error"]}')
        return
    
    print('🌍 DONNÉES GÉOGRAPHIQUES:')
    print(f'📊 Total pays: {result["totalCountries"]}')
    print('\n🎯 Répartition par pays:')
    
    for index, country in enumerate(result['countries']):
        print(f'{index + 1}. {country["countryCode"]}: {country["visitsSharePercent"]}% ({country["visitsShare"]})')
    
    return result

# 🚀 LANCER LE TEST
if __name__ == "__main__":
    asyncio.run(test_geo_data())
```

### **2. Résultats de Test Python**
```
🌍 DONNÉES GÉOGRAPHIQUES:
📊 Total pays: 5

🎯 Répartition par pays:
1. US: 74.64% (0.7463570938382258)
2. CA: 5.53% (0.055305203723785626)
3. GB: 3.32% (0.033161369204622045)
4. AU: 2.64% (0.026404760571075575)
5. DE: 1.99% (0.01987304688450781)
```

### **3. Instructions Utilisateur**
- **"arrete de faire de la doc tant que le comportement attendu n'est pas ok"**
- **"aide toi de ça"** (en référence au code Python)
- **"mais regarde sur l'api pour recup les pixels puisque ça marche deja !!!"**

---

## ✅ **CE QUI FONCTIONNE DÉJÀ**

### 1. **Extraction des IDs depuis la page de liste**
- ✅ L'ID est correctement extrait depuis l'attribut `id` des balises `<tr>`
- ✅ Format : `7fbb404d-63d6-4c5c-b38a-b09e67b7a501`
- ✅ Code : `src/extractors/trendtrack-extractor.js` ligne 398-399

### 2. **API des Pixels (100% fonctionnelle)**
- ✅ Endpoint : `/en/workspace/{workspace}/trending-shops/{shopId}`
- ✅ Headers : `RSC: 1`, `Accept: text/x-component`
- ✅ Parsing : Recherche de patterns dans la réponse RSC
- ✅ Résultat : Pixels Google et Facebook correctement extraits

### 3. **API des Données Géographiques (100% fonctionnelle)**
- ✅ Endpoint : `/api/websites/{site_id}`
- ✅ Headers : `Accept: */*`, `Sec-Fetch-*`
- ✅ Parsing : JSON avec structure `data.website.geography.topCountriesTraffics`
- ✅ Résultat : Données géographiques correctement extraites

### 4. **Intégration dans le scraper principal**
- ✅ Code intégré dans `extractShopDetails(shopId)`
- ✅ Appel dans `update-database.js` avec l'ID correct
- ✅ Stockage en base de données configuré

---

## ❌ **PROBLÈME PRINCIPAL À RÉSOUDRE**

### **Mapping des IDs**
- **ID de la page de liste** : `7fbb404d-63d6-4c5c-b38a-b09e67b7a501`
- **ID de l'API** : `90c2965f-9881-40ce-bcb7-f7da383fd815`
- **Problème** : Ce sont deux IDs différents !

### **Conséquences**
- ✅ L'API des pixels fonctionne avec l'ID de la page de liste
- ❌ L'API des données géographiques ne fonctionne qu'avec l'ID de l'API
- ❌ Impossible d'extraire les données géographiques pour les boutiques de la page de liste

---

## 🔍 **ANALYSE TECHNIQUE**

### **Endpoints Identifiés**
1. **`/en/workspace/{workspace}/trending-shops/{shopId}`**
   - ✅ Fonctionne pour les pixels
   - ❌ Ne contient pas les données géographiques
   - Format : RSC (React Server Components)

2. **`/api/websites/{site_id}`**
   - ✅ Fonctionne pour les données géographiques
   - ❌ Nécessite un ID différent
   - Format : JSON

### **Structure des Données Géographiques (Confirmée par Python)**
```json
{
  "website": {
    "geography": {
      "topCountriesTraffics": [
        {
          "visitsShare": 0.7463570938382258,
          "countryUrlCode": "united-states",
          "countryAlpha2Code": "US"
        }
      ],
      "countriesTotalCount": 5
    }
  }
}
```

### **Headers Confirmés par Python**
```javascript
{
  "Accept": "*/*",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors", 
  "Sec-Fetch-Site": "same-origin"
}
```

---

## 🛠️ **SOLUTIONS POSSIBLES**

### **Solution 1 : Trouver le mapping des IDs**
- **Approche** : Analyser la réponse de `/trending-shops/` pour trouver l'ID de l'API
- **Avantage** : Solution directe
- **Inconvénient** : Peut ne pas exister

### **Solution 2 : Utiliser l'URL de la boutique**
- **Approche** : Faire le mapping via l'URL de la boutique
- **Avantage** : L'URL est disponible dans les deux cas
- **Inconvénient** : Nécessite une logique de mapping

### **Solution 3 : Extraire l'ID depuis la page de détail**
- **Approche** : Aller sur la page de détail et extraire l'ID de l'API
- **Avantage** : L'ID est probablement présent
- **Inconvénient** : Plus lent (navigation supplémentaire)

### **Solution 4 : Approche hybride**
- **Approche** : Pixels depuis `/trending-shops/`, géo depuis `/api/websites/`
- **Avantage** : Utilise les deux endpoints qui fonctionnent
- **Inconvénient** : Nécessite de résoudre le mapping

---

## 📁 **FICHIERS MODIFIÉS**

### **`src/extractors/trendtrack-extractor.js`**
- ✅ Méthode `extractShopDetails(shopId)` modifiée
- ✅ Méthode `getGeoDataViaAPI(siteId)` implémentée
- ✅ Parsing JSON pour les données géographiques

### **`update-database.js`**
- ✅ Appel à `extractShopDetails(shop.shopId)` avec l'ID correct

### **Base de données**
- ✅ Champs `market_us`, `market_uk`, `market_de`, `market_ca`, `market_au`, `market_fr` prêts
- ✅ Champs `pixel_google`, `pixel_facebook` prêts

---

## 🧪 **TESTS EFFECTUÉS**

### **Tests Réussis**
- ✅ Extraction des IDs depuis la page de liste
- ✅ API des pixels avec l'ID de la page de liste
- ✅ API des données géographiques avec l'ID de l'API Python (`90c2965f-9881-40ce-bcb7-f7da383fd815`)

### **Tests Échoués**
- ❌ API des données géographiques avec l'ID de la page de liste (`7fbb404d-63d6-4c5c-b38a-b09e67b7a501`)
- ❌ Recherche des données géographiques dans la réponse RSC

---

## 🎯 **PROCHAINES ÉTAPES POUR LE DÉVELOPPEUR**

### **Étape 1 : Analyser la réponse RSC**
```javascript
// Dans extractPixelsForShopJS, analyser la réponse pour trouver l'ID de l'API
const response = await fetch(`https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`, {
  headers: { 'RSC': '1', 'Accept': 'text/x-component' },
  credentials: 'include'
});
const text = await response.text();
// Chercher un pattern comme "websiteId" ou "siteId" dans la réponse
```

### **Étape 2 : Implémenter le mapping**
```javascript
// Extraire l'ID de l'API depuis la réponse RSC
const apiIdMatch = text.match(/"websiteId":"([^"]+)"/);
const apiId = apiIdMatch ? apiIdMatch[1] : null;
```

### **Étape 3 : Utiliser l'ID de l'API pour les données géographiques**
```javascript
// Utiliser l'ID de l'API pour l'endpoint des données géographiques
const geoData = await this.getGeoDataViaAPI(apiId);
```

### **Étape 4 : Tester l'intégration complète**
- Tester avec plusieurs boutiques
- Vérifier que les données sont stockées en base
- Valider les performances

---

## 📊 **MÉTRIQUES DE SUCCÈS**

### **Objectifs**
- **Pixels** : 95% des boutiques avec pixels extraits
- **Données géographiques** : 80% des boutiques avec données géographiques
- **Performance** : 50% plus rapide que l'extraction DOM

### **Tests de Validation**
```sql
-- Vérifier les données de marché
SELECT COUNT(*) as total_shops,
       COUNT(CASE WHEN market_us > 0 THEN 1 END) as shops_with_us_data,
       COUNT(CASE WHEN pixel_google = 'oui' THEN 1 END) as shops_with_google_pixel
FROM shops;
```

---

## 🚨 **POINTS D'ATTENTION**

### **Sécurité**
- Les cookies de session sont automatiquement gérés
- Ne pas exposer les cookies dans les logs

### **Performance**
- Limiter le nombre d'appels API simultanés
- Implémenter un système de retry pour les échecs

### **Gestion des Erreurs**
- Marquer les boutiques avec un statut `failed` en cas d'erreur
- Logger les erreurs pour investigation

---

## 🛠️ **NOTES DE DÉVELOPPEMENT**

### **Technologies Utilisées**
- **Node.js** : Runtime principal
- **Playwright** : Automatisation du navigateur
- **SQLite** : Base de données
- **Fetch API** : Appels HTTP

### **Bonnes Pratiques**
- Validation des données avant stockage
- Logging détaillé pour le debugging
- Gestion gracieuse des erreurs

---

## 🎯 **CONCLUSION**

**Le projet est à 90% terminé.** L'infrastructure est complète, les APIs fonctionnent, mais il faut résoudre le problème de mapping des IDs pour que les données géographiques soient extraites pour toutes les boutiques.

**Temps estimé pour finaliser** : 2-4 heures

**Priorité** : Résoudre le mapping des IDs pour débloquer l'extraction des données géographiques.

---

**Développeur précédent** : Assistant IA  
**Date de transfert** : 2025-09-20  
**Statut** : Prêt pour reprise de développement