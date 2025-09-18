/**
 * Extracteur spécialisé pour les sites e-commerce
 * Extrait les informations de produits, prix, descriptions, etc.
 */

import { BaseExtractor } from './base-extractor.js';
import { siteConfigs } from '../config.js';

export class EcommerceExtractor extends BaseExtractor {
  constructor(page, errorHandler) {
    super(page, errorHandler);
    this.selectors = siteConfigs.ecommerce.selectors;
  }

  /**
   * Extrait les informations d'un produit
   * @param {string} productUrl - URL du produit
   * @returns {Promise<Object>} - Informations du produit
   */
  async extractProductInfo(productUrl) {
    console.log(`🛍️ Extraction produit: ${productUrl}`);
    
    const validationRules = {
      productTitle: { required: true, minLength: 3 },
      productPrice: { required: true, pattern: 'price' },
      productDescription: { required: false, maxLength: 1000 }
    };
    
    return this.extractWithValidation(this.selectors, validationRules, 'product');
  }

  /**
   * Extrait les informations de plusieurs produits
   * @param {Array} productUrls - URLs des produits
   * @returns {Promise<Array>} - Informations des produits
   */
  async extractMultipleProducts(productUrls) {
    console.log(`📦 Extraction de ${productUrls.length} produits...`);
    
    const results = [];
    
    for (const url of productUrls) {
      try {
        const result = await this.extractProductInfo(url);
        results.push(result);
        
        // Pause entre les extractions
        await this.sleep(1000);
        
      } catch (error) {
        console.log(`❌ Erreur extraction produit ${url}: ${error.message}`);
        results.push({
          success: false,
          url,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    return results;
  }

  /**
   * Extrait les informations de catégorie
   * @returns {Promise<Object>} - Informations de catégorie
   */
  async extractCategoryInfo() {
    console.log('📂 Extraction informations catégorie...');
    
    const categorySelectors = {
      categoryTitle: {
        selector: 'h1, .category-title, .page-title',
        multiple: false
      },
      productCount: {
        selector: '.product-count, .results-count, [data-product-count]',
        multiple: false
      },
      categoryDescription: {
        selector: '.category-description, .description',
        multiple: false
      },
      filters: {
        selector: '.filter, .facet, [data-filter]',
        multiple: true
      }
    };
    
    return this.extractData(categorySelectors, 'category');
  }

  /**
   * Extrait les informations de panier
   * @returns {Promise<Object>} - Informations du panier
   */
  async extractCartInfo() {
    console.log('🛒 Extraction informations panier...');
    
    const cartSelectors = {
      cartItems: {
        selector: '.cart-item, .basket-item, [data-cart-item]',
        multiple: true
      },
      cartTotal: {
        selector: '.cart-total, .basket-total, [data-cart-total]',
        multiple: false
      },
      cartCount: {
        selector: '.cart-count, .basket-count, [data-cart-count]',
        multiple: false
      }
    };
    
    return this.extractData(cartSelectors, 'cart');
  }

  /**
   * Extrait les informations de recherche
   * @param {string} searchTerm - Terme de recherche
   * @returns {Promise<Object>} - Résultats de recherche
   */
  async extractSearchResults(searchTerm) {
    console.log(`🔍 Extraction résultats recherche: ${searchTerm}`);
    
    const searchSelectors = {
      searchResults: {
        selector: '.search-result, .product-item, [data-search-result]',
        multiple: true
      },
      searchCount: {
        selector: '.search-count, .results-count, [data-search-count]',
        multiple: false
      },
      searchSuggestions: {
        selector: '.search-suggestion, .suggestion, [data-suggestion]',
        multiple: true
      }
    };
    
    const data = await this.extractData(searchSelectors, 'search');
    
    return {
      ...data,
      searchTerm,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Extrait les informations de disponibilité
   * @returns {Promise<Object>} - Informations de disponibilité
   */
  async extractAvailabilityInfo() {
    console.log('📦 Extraction informations disponibilité...');
    
    const availabilitySelectors = {
      stockStatus: {
        selector: '.stock-status, .availability, [data-stock]',
        multiple: false
      },
      deliveryInfo: {
        selector: '.delivery-info, .shipping-info, [data-delivery]',
        multiple: false
      },
      returnPolicy: {
        selector: '.return-policy, .returns, [data-returns]',
        multiple: false
      }
    };
    
    return this.extractData(availabilitySelectors, 'availability');
  }

  /**
   * Extrait les informations de prix et promotions
   * @returns {Promise<Object>} - Informations de prix
   */
  async extractPricingInfo() {
    console.log('💰 Extraction informations prix...');
    
    const pricingSelectors = {
      originalPrice: {
        selector: '.original-price, .old-price, [data-original-price]',
        multiple: false
      },
      salePrice: {
        selector: '.sale-price, .discount-price, [data-sale-price]',
        multiple: false
      },
      discount: {
        selector: '.discount, .savings, [data-discount]',
        multiple: false
      },
      currency: {
        selector: '[data-currency], .currency',
        multiple: false
      }
    };
    
    return this.extractData(pricingSelectors, 'pricing');
  }

  /**
   * Extrait les informations de navigation
   * @returns {Promise<Object>} - Informations de navigation
   */
  async extractNavigationInfo() {
    console.log('🧭 Extraction informations navigation...');
    
    const navigationSelectors = {
      breadcrumbs: {
        selector: '.breadcrumb, .breadcrumbs, [data-breadcrumb]',
        multiple: true
      },
      menuItems: {
        selector: '.menu-item, .nav-item, [data-menu-item]',
        multiple: true
      },
      pagination: {
        selector: '.pagination, .pager, [data-pagination]',
        multiple: false
      }
    };
    
    return this.extractData(navigationSelectors, 'navigation');
  }

  /**
   * Formate les résultats pour l'affichage
   * @param {Object} results - Résultats de l'extraction
   * @returns {string} - Résultats formatés
   */
  formatProductResults(results) {
    if (!results || !results.data) {
      return '❌ Aucune donnée produit disponible';
    }

    const { data } = results;
    return [
      '🛍️ PRODUIT:',
      `   Titre: ${data.productTitle || 'Non trouvé'}`,
      `   Prix: ${data.productPrice || 'Non trouvé'}`,
      `   Description: ${data.productDescription ? data.productDescription.substring(0, 100) + '...' : 'Non trouvé'}`,
      `   Images: ${data.productImages ? data.productImages.length : 0} trouvées`,
      `   Bouton Achat: ${data.addToCartButton ? 'Présent' : 'Non trouvé'}`
    ].join('\n');
  }

  /**
   * Pause pour éviter la surcharge
   * @param {number} ms - Millisecondes à attendre
   * @returns {Promise} - Promise qui se résout après la pause
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
} 