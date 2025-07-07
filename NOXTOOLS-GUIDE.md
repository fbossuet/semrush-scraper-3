# 🔧 Guide NoxTools - Configuration et Utilisation

Ce guide te montre comment configurer le scraper pour utiliser NoxTools comme passerelle d'accès.

## 🎯 Workflow NoxTools

1. **Connexion à NoxTools** → 2. **Navigation vers site final** → 3. **Scraping du site final**

## ⚙️ Configuration Rapide

### Étape 1: Configurer tes identifiants NoxTools

Ouvre `src/config.js` et modifie :

```javascript
credentials: {
  username: 'semrush3hosting',        // ← Ton email NoxTools
  password: 'fbossuetg',      // ← Ton mot de passe NoxTools
  // Les sélecteurs sont déjà configurés pour NoxTools
}
```

### Étape 2: Adapter les sélecteurs pour le site final

Dans `src/config.js`, personnalise la section `selectors` selon le site que tu veux scraper :

```javascript
selectors: {
  // Exemple pour scraper des résultats SEMrush
  keywords: {
    selector: '.keyword-cell, [data-test="keyword"]',
    multiple: true
  },
  volumes: {
    selector: '.volume-cell, [data-test="volume"]', 
    multiple: true
  },
  difficulty: {
    selector: '.kd-cell, [data-test="difficulty"]',
    multiple: true
  }
}
```

## 🚀 Utilisation

### Lancement simple (automatique)
```bash
npm run noxtools
```

### Mode développement (avec debug)
```bash
npm run noxtools-dev
```

### 🎯 Mode interactif (recommandé pour débuter)
```bash
npm run interactive
```
**Ce mode te permet de :**
- Voir le navigateur en action
- Résoudre manuellement les CAPTCHA/protections
- Confirmer que la page est prête avant scraping
- Inspecter les éléments trouvés
- Contrôler chaque étape

## 🔍 Trouve les bons sélecteurs

1. **Lance le script en mode développement** avec `npm run noxtools-dev`
2. **Le navigateur va s'ouvrir** et se connecter automatiquement
3. **Utilise F12** pour inspecter les éléments du site final
4. **Copie les sélecteurs CSS** et mets-les dans `config.js`
5. **Relance le script** pour tester

## 📸 Captures d'écran automatiques

Le script prend automatiquement des captures :
- `before-scraping-*.png` : Avant le scraping
- `final-result-*.png` : Résultat final  
- `error-*.png` : En cas d'erreur

## 💾 Sauvegarde des données

Les données sont automatiquement sauvegardées dans :
- `noxtools-data-*.json` : Fichier JSON avec toutes les données

## 🛠️ Personnalisations avancées

### Ajouter des étapes de navigation

Dans `src/noxtools-scraper.js`, tu peux modifier `navigateToFinalSite()` :

```javascript
// Exemple : cliquer sur des menus spécifiques
await this.page.click('.menu-analytics');
await this.page.click('.submenu-keywords');
await this.page.waitForLoadState('networkidle');
```

### Gérer les pop-ups ou modales

```javascript
// Fermer une popup si elle apparaît
try {
  await this.page.click('.popup-close, .modal-dismiss', { timeout: 2000 });
} catch (e) {
  // Pas de popup, continue
}
```

## 🚨 Problèmes courants

### ❌ "Connexion NoxTools échouée"
- Vérifie tes identifiants dans `config.js`
- Vérifie que ton compte NoxTools est actif
- Assure-toi que tu n'as pas de 2FA activé

### ❌ "Impossible de naviguer vers le site final"
- Le lien d'accès a peut-être changé
- Modifie `noxToolsSelectors.accessLink.selector` dans `config.js`

### ❌ "Élément non trouvé pour le scraping"
- Utilise F12 pour trouver les vrais sélecteurs
- Le site a peut-être changé sa structure
- Teste avec des sélecteurs plus génériques

## 📋 Template de configuration

Voici un template prêt à utiliser pour des données typiques :

```javascript
selectors: {
  // Tableau de données
  tableRows: {
    selector: 'tr[data-row], .data-row, .result-item',
    multiple: true
  },
  
  // Mots-clés
  keywords: {
    selector: '.keyword, [data-col="keyword"]',
    multiple: true
  },
  
  // Métriques numériques
  metrics: {
    selector: '.metric, .number, [data-col="volume"]',
    multiple: true
  },
  
  // Liens vers détails
  detailLinks: {
    selector: 'a.detail-link, .view-more',
    attribute: 'href',
    multiple: true
  }
}
```

## 🎯 Cas d'usage fréquents

### Scraper des mots-clés SEMrush
```javascript
selectors: {
  keywords: { selector: '[data-test="keyword-cell"]', multiple: true },
  volumes: { selector: '[data-test="volume-cell"]', multiple: true },
  cpc: { selector: '[data-test="cpc-cell"]', multiple: true }
}
```

### Scraper des backlinks
```javascript
selectors: {
  domains: { selector: '.domain-cell', multiple: true },
  authScores: { selector: '.as-cell', multiple: true },
  urls: { selector: '.url-cell a', attribute: 'href', multiple: true }
}
```

## ✅ Test de connexion

Pour tester que tout fonctionne :

1. Configure tes identifiants
2. Lance `npm run noxtools`  
3. Vérifie dans la console que la connexion réussit
4. Les captures d'écran te montreront où tu en es

Bon scraping ! 🎉