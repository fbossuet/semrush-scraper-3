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
  
  // URLs du site web
  loginUrl: 'https://example.com/login', // Remplace par l'URL de connexion
  targetUrl: 'https://example.com/dashboard', // Remplace par l'URL de l'interface cible
  
  // Informations de connexion
  credentials: {
    username: 'ton_nom_utilisateur', // Remplace par tes identifiants
    password: 'ton_mot_de_passe', // Remplace par ton mot de passe
    usernameSelector: '#username', // Sélecteur du champ nom d'utilisateur
    passwordSelector: '#password', // Sélecteur du champ mot de passe
    submitSelector: 'button[type="submit"]' // Sélecteur du bouton de connexion
  },
  
  // Sélecteurs pour le scraping
  selectors: {
    // Exemple de conteneur principal
    mainContainer: {
      selector: '.main-content',
      multiple: false
    },
    
    // Exemple de titre de page
    pageTitle: {
      selector: 'h1',
      multiple: false
    },
    
    // Exemple de liste d'éléments
    items: {
      selector: '.item',
      multiple: true
    },
    
    // Exemple de données spécifiques avec attributs
    links: {
      selector: 'a.important-link',
      attribute: 'href',
      multiple: true
    },
    
    // Exemple de texte simple
    description: {
      selector: '.description',
      multiple: false
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