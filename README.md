# 🤖 Semrush Scraper 3 - Playwright Web Automation

Un scraper web automatisé utilisant Playwright pour naviguer, se connecter et extraire des données de sites web.

## 🚀 Fonctionnalités

- ✅ **Connexion automatique** sur les sites web
- 🧭 **Navigation intelligente** entre les interfaces
- 📊 **Extraction de données** configurables
- 📸 **Captures d'écran** automatiques
- ⚡ **Configuration flexible** via fichiers de config
- 🔧 **Mode debug** pour développement
- 📱 **Support multi-navigateurs** (Chrome, Firefox, Safari)

## 📦 Installation

### 1. Installer les dépendances

```bash
npm install
```

### 2. Installer les navigateurs Playwright

```bash
npm run install-playwright
```

## 🛠️ Configuration

### Fichier principal: `src/config.js`

Modifie ce fichier pour adapter le scraper à ton site web:

```javascript
export const config = {
  // URLs du site
  loginUrl: 'https://tonsite.com/login',
  targetUrl: 'https://tonsite.com/data',
  
  // Identifiants de connexion
  credentials: {
    username: 'ton_username',
    password: 'ton_password',
    usernameSelector: '#email',    // Sélecteur CSS du champ email
    passwordSelector: '#password', // Sélecteur CSS du champ password
    submitSelector: 'button[type="submit"]'
  },
  
  // Éléments à scraper
  selectors: {
    titre: {
      selector: 'h1.main-title',
      multiple: false
    },
    produits: {
      selector: '.product-item',
      multiple: true
    },
    liens: {
      selector: 'a.product-link',
      attribute: 'href',
      multiple: true
    }
  }
};
```

## 🎯 Utilisation

### Scraper générique

```bash
npm start              # Lancement simple
npm run dev           # Mode développement avec debug
```

### 🔧 Workflow NoxTools (spécialisé)

Pour utiliser NoxTools comme passerelle d'accès :

```bash
npm run noxtools       # Workflow NoxTools complet
npm run noxtools-dev   # Mode développement NoxTools
```

**📋 Guide complet NoxTools**: Voir [NOXTOOLS-GUIDE.md](NOXTOOLS-GUIDE.md)

### Exemples d'utilisation

#### 1. Scraping basique

```javascript
import { WebScraper } from './src/scraper.js';

const scraper = new WebScraper();
await scraper.init();

// Connexion
await scraper.login('https://monsite.com/login', {
  username: 'user',
  password: 'pass',
  usernameSelector: '#email',
  passwordSelector: '#password'
});

// Navigation
await scraper.navigateToInterface('https://monsite.com/data');

// Extraction
const data = await scraper.scrapeData({
  titles: { selector: '.title', multiple: true },
  prices: { selector: '.price', multiple: true }
});

console.log(data);
await scraper.close();
```

#### 2. Navigation complexe avec attentes

```javascript
// Attendre qu'un élément apparaisse
await scraper.waitForElement('.data-table');

// Cliquer sur des éléments
await scraper.page.click('.menu-button');

// Remplir des formulaires
await scraper.page.fill('#search', 'terme de recherche');

// Attendre le chargement
await scraper.page.waitForLoadState('networkidle');
```

#### 3. Pagination automatique

```javascript
let allData = [];
let page = 1;

while (await scraper.page.$('.next-page:not(.disabled)')) {
  console.log(`Scraping page ${page}...`);
  
  const pageData = await scraper.scrapeData(config.selectors);
  allData.push(...pageData.items);
  
  await scraper.page.click('.next-page');
  await scraper.page.waitForLoadState('networkidle');
  page++;
}
```

## 📁 Structure du projet

```
semrush-scraper-3/
├── src/
│   ├── scraper.js         # Classe principale du scraper
│   ├── config.js          # Configuration (URLs, sélecteurs, etc.)
│   ├── noxtools-scraper.js # Scraper spécialisé NoxTools
│   └── example.js         # Exemples d'utilisation
├── screenshots/           # Captures d'écran automatiques
├── package.json          # Dépendances et scripts
├── README.md            # Documentation générale
├── NOXTOOLS-GUIDE.md    # Guide spécifique NoxTools
└── .gitignore           # Fichiers à ignorer
```

## 🔧 Options de configuration

### Navigateur
- `headless`: true/false (mode sans interface)
- `slowMo`: délai entre actions (ms)
- `viewport`: taille de la fenêtre

### Sélecteurs
- `selector`: sélecteur CSS de l'élément
- `multiple`: true pour récupérer plusieurs éléments
- `attribute`: attribut HTML à extraire (href, src, etc.)

### Timeouts
- `navigation`: timeout pour navigation (ms)
- `element`: timeout pour attente d'éléments (ms)

## 🚨 Conseils d'utilisation

### 1. Trouver les bons sélecteurs CSS

Utilise les outils de développeur de ton navigateur:
1. F12 pour ouvrir les dev tools
2. Clique sur l'icône de sélection
3. Clique sur l'élément à scraper
4. Copie le sélecteur CSS

### 2. Gérer les sites avec authentification

```javascript
// Attendre la redirection après connexion
await scraper.page.waitForURL('**/dashboard**');

// Vérifier si la connexion a réussi
const isLoggedIn = await scraper.page.$('.user-menu');
if (!isLoggedIn) {
  throw new Error('Connexion échouée');
}
```

### 3. Contourner les protections anti-bot

```javascript
// User agent réaliste
userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',

// Délais aléatoires
slowMo: Math.random() * 200 + 100,

// Mouvements de souris naturels
await scraper.page.mouse.move(100, 100);
await scraper.page.mouse.move(200, 200);
```

## 🐛 Debugging

### Mode debug activé

```javascript
// Dans config.js
debug: {
  screenshots: true,  // Capture automatique
  logs: true,        // Logs détaillés
  slowMode: true     // Ralentir l'exécution
}
```

### Captures d'écran manuelles

```javascript
await scraper.takeScreenshot('debug-step-1.png');
```

### Logs détaillés

```javascript
// Activer les logs Playwright
DEBUG=pw:api npm start
```

## ⚠️ Considérations légales

- ✅ Respecte les `robots.txt` des sites
- ✅ N'abuse pas des serveurs (délais entre requêtes)
- ✅ Respecte les conditions d'utilisation
- ✅ Utilise tes propres comptes/identifiants

## 🔄 Scripts disponibles

```bash
npm start                    # Lancer le scraper générique
npm run dev                 # Mode développement générique
npm run noxtools            # Workflow NoxTools complet  
npm run noxtools-dev        # Mode développement NoxTools
npm run install-playwright  # Installer les navigateurs
npm test                    # Tests (à implémenter)
```

## 🆘 Problèmes courants

### "Browser not found"
```bash
npm run install-playwright
```

### "Element not found"
- Vérifier les sélecteurs CSS
- Augmenter les timeouts
- Ajouter des attentes explicites

### "Login failed"
- Vérifier les identifiants
- Adapter les sélecteurs de connexion
- Vérifier les CAPTCHA

### "Page not loading"
- Vérifier l'URL
- Augmenter le timeout de navigation
- Vérifier la connexion internet

## 📞 Support

Pour toute question ou problème, consulte:
- [Documentation Playwright](https://playwright.dev/)
- [Exemples de sélecteurs CSS](https://www.w3schools.com/cssref/css_selectors.asp)

Bon scraping ! 🎯
