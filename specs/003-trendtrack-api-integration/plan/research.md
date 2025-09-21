# Recherche Technique : Intégration API TrendTrack

**Branche de Fonctionnalité** : `003-trendtrack-api-integration`  
**Créé** : 2025-09-20  
**Statut** : Recherche  
**Basé sur** : [Spec 003](../spec.md)

---

## 🔍 Objectif de la Recherche

Comprendre comment l'API TrendTrack fonctionne actuellement pour les pixels et identifier le bon endpoint pour les données géographiques.

---

## 📊 Analyse de l'API des Pixels (Fonctionnelle)

### Endpoint Utilisé
```
https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/{shopId}
```

### Headers Requis
```javascript
{
  'RSC': '1', 
  'Accept': 'text/x-component',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
```

### Authentification
- **Méthode** : Cookies de session automatiques
- **Source** : `document.cookie` depuis le navigateur
- **Inclusion** : `credentials: 'include'` dans la requête

### Format de Réponse
- **Type** : React Server Components (RSC)
- **Format** : Texte brut contenant du HTML/JS
- **Taille** : ~200k caractères pour une boutique

### Extraction des Données
```javascript
// Recherche de patterns dans le contenu
const hasGoogleAnalytics = text.includes('Google Analytics') || text.includes('gtag') || text.includes('google-analytics');
const hasFacebookPixel = text.includes('Facebook Pixel') || text.includes('fbq') || text.includes('fbevents');
```

### ID Utilisé
- **Source** : Attribut `id` de la balise `<tr>` dans la page de liste
- **Format** : `shop_12345` ou similaire
- **Extraction** : `rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/)`

---

## 🌍 Recherche des Données Géographiques

### Problème Identifié
L'endpoint actuel ne contient pas les données géographiques dans la réponse.

### Endpoints Testés
1. **Endpoint principal** : `/trending-shops/{shopId}` ❌
2. **Endpoint de détail** : `/shop-detail?url={encodedUrl}` ❌
3. **Endpoint alternatif** : `/api/trending-shops/{shopId}` ❌

### Format de Données Attendues
```javascript
// Structure attendue dans la réponse
{
  "geography": {
    "topCountriesTraffics": [
      {
        "visitsShare": 0.45,
        "countryUrlCode": "us",
        "countryAlpha2Code": "US"
      },
      {
        "visitsShare": 0.23,
        "countryUrlCode": "uk", 
        "countryAlpha2Code": "GB"
      }
    ]
  }
}
```

### Regex Pattern pour Extraction
```javascript
const geoPattern = /"visitsShare":([0-9.]+),"countryUrlCode":"[^"]+","countryAlpha2Code":"([^"]+)"/g;
```

---

## 🔧 Découvertes Techniques

### 1. Gestion des Cookies
- **Automatique** : Les cookies sont récupérés depuis `document.cookie`
- **Inclusion** : `credentials: 'include'` dans la requête fetch
- **Persistance** : La session est maintenue entre les appels

### 2. Format des Réponses
- **RSC** : React Server Components, pas du JSON pur
- **Parsing** : Recherche de patterns dans le texte brut
- **Taille** : Réponses volumineuses (~200k caractères)

### 3. Extraction des IDs
- **Source** : DOM de la page de liste, pas l'URL de détail
- **Format** : Attribut `id` des balises `<tr>`
- **Validation** : L'ID doit correspondre au format attendu par l'API

### 4. Gestion des Erreurs
- **HTTP** : Vérification du statut de réponse
- **Parsing** : Gestion des données manquantes
- **Fallback** : Valeurs par défaut si extraction échoue

---

## 🚨 Problèmes Identifiés

### Problème 1 : Endpoint des Données Géographiques
- **Symptôme** : L'endpoint actuel ne contient pas les données géographiques
- **Cause** : Mauvais endpoint ou données chargées dynamiquement
- **Solution** : Identifier le bon endpoint ou utiliser une approche différente

### Problème 2 : Format des Données
- **Symptôme** : Les données géographiques ne sont pas dans le format attendu
- **Cause** : Format RSC complexe ou données dans un autre format
- **Solution** : Analyser le format exact des données dans la réponse

### Problème 3 : Extraction des IDs
- **Symptôme** : L'ID extrait ne correspond pas au format attendu
- **Cause** : Mauvaise extraction depuis le DOM ou format incorrect
- **Solution** : Corriger l'extraction pour utiliser le même ID que l'API des pixels

---

## 💡 Solutions Proposées

### Solution 1 : Endpoint Alternatif
- **Approche** : Tester d'autres endpoints TrendTrack
- **Avantage** : Solution directe si l'endpoint existe
- **Inconvénient** : Peut ne pas exister

### Solution 2 : Navigation et Extraction DOM
- **Approche** : Aller sur la page de détail et extraire depuis le DOM
- **Avantage** : Données disponibles sur la page
- **Inconvénient** : Plus lent que l'API

### Solution 3 : Analyse Approfondie de la Réponse
- **Approche** : Analyser en détail le contenu de la réponse RSC
- **Avantage** : Les données peuvent être présentes mais mal extraites
- **Inconvénient** : Format complexe à parser

### Solution 4 : API Externe
- **Approche** : Utiliser une autre source pour les données géographiques
- **Avantage** : Données fiables et structurées
- **Inconvénient** : Coût et complexité d'intégration

---

## 🔍 Prochaines Étapes

### Étape 1 : Analyse Approfondie
- Analyser en détail le contenu de la réponse RSC
- Rechercher les données géographiques dans différents formats
- Tester différents patterns de regex

### Étape 2 : Test d'Endpoints
- Tester d'autres endpoints TrendTrack
- Vérifier les endpoints d'API internes
- Analyser les appels réseau dans le navigateur

### Étape 3 : Navigation et Extraction
- Tester l'extraction depuis la page de détail
- Comparer les performances avec l'API
- Évaluer la fiabilité de cette approche

### Étape 4 : Validation
- Valider les données extraites
- Tester avec différentes boutiques
- Mesurer les performances

---

## 📊 Métriques de Recherche

### Données Collectées
- **Endpoints testés** : 3
- **Formats analysés** : RSC, JSON, HTML
- **Patterns testés** : 5+
- **Boutiques testées** : 1 (happiestbaby.com)

### Résultats
- **API des pixels** : ✅ Fonctionnelle
- **API des données géographiques** : ❌ Non fonctionnelle
- **Extraction des IDs** : ⚠️ Partiellement fonctionnelle
- **Gestion des cookies** : ✅ Fonctionnelle

---

## 📝 Notes de Recherche

### Observations
- L'API TrendTrack utilise un format RSC complexe
- Les cookies de session sont automatiquement gérés
- L'extraction des IDs depuis le DOM fonctionne
- Les données géographiques ne sont pas dans l'endpoint actuel

### Recommandations
1. **Priorité 1** : Analyser en détail la réponse RSC pour trouver les données géographiques
2. **Priorité 2** : Tester d'autres endpoints TrendTrack
3. **Priorité 3** : Implémenter l'extraction depuis la page de détail comme fallback

### Questions Ouvertes
1. Les données géographiques sont-elles dans la réponse RSC mais dans un format différent ?
2. Existe-t-il un autre endpoint pour les données géographiques ?
3. Les données sont-elles chargées dynamiquement après la réponse initiale ?

---

**Statut de la Recherche** : 🔍 **EN COURS**

La recherche est en cours. L'API des pixels est comprise, mais l'endpoint pour les données géographiques nécessite une investigation plus approfondie.
