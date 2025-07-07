export const config = {
  // Configuration du navigateur
  headless: true, // Mode invisible (nécessaire sur serveur sans X Server)
  slowMo: 500, // Délai plus long pour éviter la détection
  
  // Configuration de la viewport
  viewport: {
    width: 1920,
    height: 1080
  },
  
  // User Agent (pour éviter la détection de bot)
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  
  // URLs NoxTools (passerelle)
  loginUrl: 'https://noxtools.com/secure/login?amember_redirect_url=https%3A%2F%2Fnoxtools.com%2Fsecure%2Fpage%2Fsemrush',
  noxToolsPage: 'https://noxtools.com/secure/page/semrush', // Page intermédiaire NoxTools
  
  // URL du site final à scraper (analytics)
  baseAnalyticsUrl: 'https://server1.noxtools.com/analytics/overview/',
  
  // Paramètres pour l'URL d'analytics
  analyticsParams: {
    searchType: 'domain',
    db: 'us',
    domain: 'https://the-foldie.com' // ← Domaine à analyser (modifiable)
  },
  
  // Informations de connexion NoxTools
  credentials: {
    username: 'semrush3hosting', // Ton email NoxTools
    password: 'fbossuetg', // Ton mot de passe NoxTools
    usernameSelector: 'input[name="amember_login"]', // Sélecteur NoxTools pour email
    passwordSelector: 'input[name="amember_pass"]', // Sélecteur NoxTools pour password
    submitSelector: 'input[type="submit"]' // Sélecteur du bouton connexion NoxTools
  },
  
  // Sélecteurs NoxTools pour navigation
  noxToolsSelectors: {
    // Lien ou bouton pour accéder au site final depuis NoxTools
    accessLink: {
      selector: 'a[href*="semrush"]', // À adapter selon l'interface NoxTools
      multiple: false
    },
    // Autres éléments de navigation si nécessaire
    menuItem: {
      selector: '.menu-item',
      multiple: false
    }
  },
  
  // Sélecteurs pour le scraping sur la page ANALYTICS (basés sur l'inspection réelle)
  selectors: {
    // Conteneur principal de l'analytics (ID trouvé lors de l'inspection)
    mainContainer: {
      selector: '#domain-overview-app, .domain-overview-app-wrapper, .srf-layout-main-content-wrapper',
      multiple: false
    },
    
    // Domaine analysé (sélecteur confirmé qui fonctionne)
    analyzedDomain: {
      selector: 'h1, h2, h3',
      multiple: false
    },
    
    // Navigation et menus SEMrush
    navigationMenus: {
      selector: '[data-testid], .nav-item, .menu-item',
      multiple: true
    },
    
    // Tous les liens de la page analytics
    allLinks: {
      selector: 'a[href*="server1.noxtools.com"]',
      attribute: 'href',
      multiple: true
    },
    
    // Scripts et données JavaScript (contiennent souvent des infos)
    scriptData: {
      selector: 'script',
      multiple: true
    },
    
    // Messages d'erreur à détecter
    errorMessages: {
      selector: '[class*="error"], [class*="warning"], [class*="problem"]',
      multiple: true
    },
    
    // Conteneurs de widgets/données
    widgets: {
      selector: '[class*="widget"], [class*="panel"], [class*="card"], [class*="container"]',
      multiple: true
    },
    
    // Tous les éléments avec du texte visible
    textElements: {
      selector: 'div, span, p, td, th',
      multiple: true
    }
  },
  
  // Configuration des timeouts
  timeouts: {
    navigation: 30000, // 30 secondes
    element: 5000 // 5 secondes
  },
  
  // Options de debugging
  debug: {
    screenshots: true,
    logs: true,
    slowMode: true
  }
};

// Configuration alternative pour les tests
export const testConfig = {
  ...config,
  headless: true,
  slowMo: 0,
  loginUrl: 'https://httpbin.org/forms/post',
  targetUrl: 'https://httpbin.org/html',
  credentials: {
    username: 'test',
    password: 'test',
    usernameSelector: 'input[name="custname"]',
    passwordSelector: 'input[name="custemail"]',
    submitSelector: 'input[type="submit"]'
  },
  selectors: {
    mainContainer: {
      selector: 'body',
      multiple: false
    },
    title: {
      selector: 'h1',
      multiple: false
    }
  }
};