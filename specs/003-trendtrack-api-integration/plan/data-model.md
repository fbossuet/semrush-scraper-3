# Modèle de Données : Intégration API TrendTrack

**Branche de Fonctionnalité** : `003-trendtrack-api-integration`  
**Créé** : 2025-09-20  
**Statut** : Conception  
**Basé sur** : [Spec 003](../spec.md)

---

## 🎯 Vue d'Ensemble

Ce document définit le modèle de données pour l'intégration de l'API TrendTrack, incluant les structures de données, les formats d'échange, et les mappings entre les différentes sources.

---

## 📊 Entités Principales

### 1. Boutique (Shop)
**Source** : Page de liste TrendTrack + API TrendTrack

```javascript
{
  // Données de base (depuis la page de liste)
  id: "shop_12345",                    // ID unique extrait du DOM
  shop_name: "Happiest Baby",          // Nom de la boutique
  shop_url: "https://happiestbaby.com", // URL de la boutique
  category: "Baby & Kids",             // Catégorie
  monthly_visits: "1.2M",             // Visites mensuelles
  monthly_revenue: "$2.5M",           // Revenus mensuels
  
  // Données de marché (depuis l'API TrendTrack)
  pixel_google: "oui",                // Pixel Google Analytics
  pixel_facebook: "non",              // Pixel Facebook
  
  // Données géographiques (depuis l'API TrendTrack)
  market_us: 0.45,                    // Pourcentage de trafic US
  market_uk: 0.23,                    // Pourcentage de trafic UK
  market_de: 0.12,                    // Pourcentage de trafic DE
  market_ca: 0.08,                    // Pourcentage de trafic CA
  market_au: 0.07,                    // Pourcentage de trafic AU
  market_fr: 0.05,                    // Pourcentage de trafic FR
  
  // Métadonnées
  scraping_status: "completed",       // Statut du scraping
  last_updated: "2025-09-20T10:30:00Z", // Dernière mise à jour
  external_id: "shop_12345"           // ID externe TrendTrack
}
```

### 2. Données de Marché (Market Data)
**Source** : API TrendTrack

```javascript
{
  // Pixels de tracking
  pixels: {
    google: {
      present: true,                  // Présence du pixel
      status: "oui",                  // Statut (oui/non)
      detected_via: "api"             // Méthode de détection
    },
    facebook: {
      present: false,                 // Présence du pixel
      status: "non",                  // Statut (oui/non)
      detected_via: "api"             // Méthode de détection
    }
  },
  
  // Données géographiques
  geography: {
    countries: [
      {
        code: "us",                   // Code pays (ISO 2)
        name: "United States",        // Nom du pays
        visits_share: 0.45,           // Part des visites
        visits_percentage: 45.0       // Pourcentage des visites
      },
      {
        code: "uk",
        name: "United Kingdom", 
        visits_share: 0.23,
        visits_percentage: 23.0
      }
    ],
    
    // Résumé par pays cibles
    summary: {
      market_us: 0.45,
      market_uk: 0.23,
      market_de: 0.12,
      market_ca: 0.08,
      market_au: 0.07,
      market_fr: 0.05
    }
  }
}
```

### 3. Réponse API TrendTrack
**Source** : API TrendTrack

```javascript
{
  // Métadonnées de la réponse
  metadata: {
    endpoint: "/trending-shops/{shopId}",
    method: "GET",
    status: 200,
    content_type: "text/x-component",
    size: 200819,
    timestamp: "2025-09-20T10:30:00Z"
  },
  
  // Contenu de la réponse (RSC)
  content: {
    raw: "...",                       // Contenu brut de la réponse
    length: 200819,                   // Taille en caractères
    format: "rsc"                     // Format (React Server Components)
  },
  
  // Données extraites
  extracted_data: {
    pixels: {
      google: "oui",
      facebook: "non"
    },
    geography: {
      countries_found: 6,
      market_data: {
        market_us: 0.45,
        market_uk: 0.23,
        market_de: 0.12,
        market_ca: 0.08,
        market_au: 0.07,
        market_fr: 0.05
      }
    }
  }
}
```

---

## 🔄 Flux de Données

### 1. Extraction depuis la Page de Liste
```
Page de liste → DOM → Extraction IDs → Stockage temporaire
```

**Données extraites** :
- ID de la boutique (attribut `id` de `<tr>`)
- Nom de la boutique
- URL de la boutique
- Catégorie
- Métriques de base

### 2. Appels API TrendTrack
```
ID boutique → API TrendTrack → Réponse RSC → Parsing → Données structurées
```

**Données récupérées** :
- Pixels de tracking (Google, Facebook)
- Données géographiques (répartition par pays)

### 3. Stockage en Base de Données
```
Données structurées → Validation → Mapping → Insertion BDD
```

**Données stockées** :
- Toutes les données de la boutique
- Statut du scraping
- Métadonnées de mise à jour

---

## 🗄️ Mapping Base de Données

### Table `shops`
```sql
-- Champs existants
id INTEGER PRIMARY KEY,
shop_name TEXT,
shop_url TEXT,
category TEXT,
monthly_visits TEXT,
monthly_revenue TEXT,

-- Nouveaux champs (à ajouter)
pixel_google TEXT DEFAULT 'non',
pixel_facebook TEXT DEFAULT 'non',
market_us REAL DEFAULT 0.0,
market_uk REAL DEFAULT 0.0,
market_de REAL DEFAULT 0.0,
market_ca REAL DEFAULT 0.0,
market_au REAL DEFAULT 0.0,
market_fr REAL DEFAULT 0.0,
scraping_status TEXT DEFAULT 'pending',
last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
external_id TEXT
```

### Mapping des Données
```javascript
// Mapping des pixels
pixel_google: extractedData.pixels.google ? "oui" : "non",
pixel_facebook: extractedData.pixels.facebook ? "oui" : "non",

// Mapping des données géographiques
market_us: extractedData.geography.summary.market_us || 0.0,
market_uk: extractedData.geography.summary.market_uk || 0.0,
market_de: extractedData.geography.summary.market_de || 0.0,
market_ca: extractedData.geography.summary.market_ca || 0.0,
market_au: extractedData.geography.summary.market_au || 0.0,
market_fr: extractedData.geography.summary.market_fr || 0.0,

// Métadonnées
scraping_status: "completed",
last_updated: new Date().toISOString(),
external_id: shopId
```

---

## 🔍 Validation des Données

### 1. Validation des Pixels
```javascript
function validatePixels(pixelData) {
  const validStatuses = ["oui", "non"];
  
  return {
    pixel_google: validStatuses.includes(pixelData.pixel_google) ? pixelData.pixel_google : "non",
    pixel_facebook: validStatuses.includes(pixelData.pixel_facebook) ? pixelData.pixel_facebook : "non"
  };
}
```

### 2. Validation des Données Géographiques
```javascript
function validateGeography(geoData) {
  const countries = ["us", "uk", "de", "ca", "au", "fr"];
  const validated = {};
  
  countries.forEach(country => {
    const value = geoData[`market_${country}`];
    validated[`market_${country}`] = (typeof value === 'number' && value >= 0 && value <= 1) ? value : 0.0;
  });
  
  return validated;
}
```

### 3. Validation des IDs
```javascript
function validateShopId(shopId) {
  // Format attendu : shop_12345 ou similaire
  const idPattern = /^[a-zA-Z0-9_-]+$/;
  return idPattern.test(shopId) && shopId.length > 0;
}
```

---

## 📊 Formats d'Échange

### 1. Format d'Entrée (API TrendTrack)
```
GET /en/workspace/{workspace}/trending-shops/{shopId}
Headers: {
  'RSC': '1',
  'Accept': 'text/x-component',
  'User-Agent': 'Mozilla/5.0...',
  'Cookie': 'session_cookie=...'
}
```

### 2. Format de Sortie (Données Structurées)
```javascript
{
  success: true,
  data: {
    shop_id: "shop_12345",
    pixels: {
      google: "oui",
      facebook: "non"
    },
    geography: {
      market_us: 0.45,
      market_uk: 0.23,
      market_de: 0.12,
      market_ca: 0.08,
      market_au: 0.07,
      market_fr: 0.05
    }
  },
  metadata: {
    timestamp: "2025-09-20T10:30:00Z",
    response_size: 200819,
    countries_found: 6
  }
}
```

### 3. Format d'Erreur
```javascript
{
  success: false,
  error: {
    code: "API_ERROR",
    message: "Failed to fetch data from TrendTrack API",
    details: {
      endpoint: "/trending-shops/shop_12345",
      status: 404,
      response: "Not Found"
    }
  },
  metadata: {
    timestamp: "2025-09-20T10:30:00Z",
    shop_id: "shop_12345"
  }
}
```

---

## 🔧 Transformations de Données

### 1. Extraction des Pixels
```javascript
function extractPixels(responseText) {
  const hasGoogleAnalytics = responseText.includes('Google Analytics') || 
                           responseText.includes('gtag') || 
                           responseText.includes('google-analytics');
  
  const hasFacebookPixel = responseText.includes('Facebook Pixel') || 
                          responseText.includes('fbq') || 
                          responseText.includes('fbevents');
  
  return {
    pixel_google: hasGoogleAnalytics ? "oui" : "non",
    pixel_facebook: hasFacebookPixel ? "oui" : "non"
  };
}
```

### 2. Extraction des Données Géographiques
```javascript
function extractGeography(responseText) {
  const geoPattern = /"visitsShare":([0-9.]+),"countryUrlCode":"[^"]+","countryAlpha2Code":"([^"]+)"/g;
  const marketData = {
    market_us: 0, market_uk: 0, market_de: 0, 
    market_ca: 0, market_au: 0, market_fr: 0
  };
  
  let match;
  while ((match = geoPattern.exec(responseText)) !== null) {
    const visitsShare = parseFloat(match[1]);
    const countryCode = match[2].toLowerCase();
    
    switch (countryCode) {
      case 'us': marketData.market_us = visitsShare; break;
      case 'gb': marketData.market_uk = visitsShare; break;
      case 'de': marketData.market_de = visitsShare; break;
      case 'ca': marketData.market_ca = visitsShare; break;
      case 'au': marketData.market_au = visitsShare; break;
      case 'fr': marketData.market_fr = visitsShare; break;
    }
  }
  
  return marketData;
}
```

---

## 📝 Notes de Conception

### Principes de Conception
1. **Cohérence** : Même format pour toutes les données de marché
2. **Robustesse** : Valeurs par défaut pour les données manquantes
3. **Traçabilité** : Métadonnées pour le debugging et monitoring
4. **Performance** : Structures optimisées pour les requêtes fréquentes

### Gestion des Erreurs
1. **Validation** : Vérification des données avant stockage
2. **Fallback** : Valeurs par défaut en cas d'erreur
3. **Logging** : Enregistrement des erreurs pour investigation
4. **Retry** : Tentatives de récupération automatique

### Évolutivité
1. **Extensibilité** : Structure modulaire pour ajouter de nouveaux pays
2. **Compatibilité** : Rétrocompatibilité avec les données existantes
3. **Performance** : Optimisation pour de gros volumes de données
4. **Monitoring** : Métriques pour surveiller la qualité des données

---

**Statut du Modèle de Données** : ✅ **PRÊT POUR L'IMPLÉMENTATION**

Le modèle de données est complet et prêt pour l'implémentation. Toutes les structures sont définies, les mappings sont clairs, et la validation est en place.
