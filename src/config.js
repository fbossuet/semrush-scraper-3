export const config = {
  // Configuration du navigateur
  headless: false, // Mettre à true pour exécuter en arrière-plan
  slowMo: 100, // Délai entre les actions (en ms)
  
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
  
  // Sélecteurs pour le scraping sur la page ANALYTICS (à personnaliser selon les données)
  selectors: {
    // Conteneur principal de l'analytics
    mainContainer: {
      selector: '.analytics-container, .overview-container, .main-content',
      multiple: false
    },
    
    // Domaine analysé
    analyzedDomain: {
      selector: '.domain-name, .analyzed-url, h1',
      multiple: false
    },
    
    // Métriques de trafic
    trafficMetrics: {
      selector: '.traffic-metric, .overview-metric, .stat-value',
      multiple: true
    },
    
    // Mots-clés organiques
    organicKeywords: {
      selector: '.keyword-row, .organic-keyword, .keyword-cell',
      multiple: true
    },
    
    // Backlinks
    backlinks: {
      selector: '.backlink-row, .backlink-item',
      multiple: true
    },
    
    // Scores/Ratings
    scores: {
      selector: '.authority-score, .domain-score, .rating',
      multiple: true
    },
    
    // Tableaux de données génériques
    dataTable: {
      selector: 'table tr, .data-table tr',
      multiple: true
    },
    
    // Liens vers détails
    detailLinks: {
      selector: 'a[href*="detail"], .view-more, .expand-link',
      attribute: 'href',
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