/**
 * Configuration générique pour le scraper web
 * Basé sur l'architecture du projet semrush-scraper
 */

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
  },
  
  // Configuration du cache
  cache: {
    enabled: true,
    directory: 'cache',
    ttl: 30 * 60 * 1000 // 30 minutes par défaut
  },
  
  // Configuration des résultats
  results: {
    directory: 'results',
    format: 'json', // json, csv, xml
    includeScreenshots: true
  }
};

// Configuration pour différents types de sites
export const siteConfigs = {
  // Configuration pour un site e-commerce
  ecommerce: {
    selectors: {
      productTitle: {
        selector: 'h1, .product-title, .product-name',
        multiple: false
      },
      productPrice: {
        selector: '.price, .product-price, [data-price]',
        multiple: false
      },
      productImages: {
        selector: 'img[src*="product"], .product-image img',
        attribute: 'src',
        multiple: true
      },
      productDescription: {
        selector: '.product-description, .description, [data-description]',
        multiple: false
      },
      addToCartButton: {
        selector: '.add-to-cart, .buy-now, [data-action="add-to-cart"]',
        multiple: false
      }
    }
  },
  
  // Configuration pour un site d'actualités
  news: {
    selectors: {
      articleTitle: {
        selector: 'h1, .article-title, .post-title',
        multiple: false
      },
      articleContent: {
        selector: '.article-content, .post-content, .entry-content',
        multiple: false
      },
      articleDate: {
        selector: '.article-date, .post-date, time[datetime]',
        multiple: false
      },
      articleAuthor: {
        selector: '.article-author, .post-author, .byline',
        multiple: false
      },
      articleTags: {
        selector: '.article-tags, .post-tags, .tags a',
        multiple: true
      }
    }
  },
  
  // Configuration pour un site de blog
  blog: {
    selectors: {
      postTitle: {
        selector: 'h1, .post-title, .entry-title',
        multiple: false
      },
      postContent: {
        selector: '.post-content, .entry-content, .blog-content',
        multiple: false
      },
      postDate: {
        selector: '.post-date, .entry-date, time',
        multiple: false
      },
      postAuthor: {
        selector: '.post-author, .entry-author, .author',
        multiple: false
      },
      postComments: {
        selector: '.comments, .comment-list',
        multiple: false
      }
    }
  }
};

// Configuration pour la gestion d'erreurs
export const errorConfig = {
  retryAttempts: 3,
  retryDelay: 2000,
  logErrors: true,
  saveErrorScreenshots: true
};

// Configuration pour l'optimisation
export const optimizationConfig = {
  // Configuration des interfaces
  interfaces: {
    overview: {
      timeout: 30000,
      retryAttempts: 2
    },
    details: {
      timeout: 45000,
      retryAttempts: 3
    },
    list: {
      timeout: 60000,
      retryAttempts: 2
    }
  },
  
  // Configuration du cache
  cache: {
    interfaces: {
      overview: { maxAge: 30 * 60 * 1000 }, // 30 minutes
      details: { maxAge: 60 * 60 * 1000 }, // 1 heure
      list: { maxAge: 15 * 60 * 1000 } // 15 minutes
    }
  },
  
  // Configuration de validation
  validation: {
    patterns: {
      url: /^https?:\/\/.+/,
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      phone: /^[\+]?[0-9\s\-\(\)]+$/,
      price: /^[\$€£]?\s*\d+([.,]\d{2})?$/,
      date: /^\d{4}-\d{2}-\d{2}$/
    }
  }
}; 