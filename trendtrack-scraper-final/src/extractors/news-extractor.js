/**
 * Extracteur spécialisé pour les sites d'actualités
 * Extrait les articles, titres, contenus, dates, auteurs, etc.
 */

import { BaseExtractor } from './base-extractor.js';
import { siteConfigs } from '../config.js';

export class NewsExtractor extends BaseExtractor {
  constructor(page, errorHandler) {
    super(page, errorHandler);
    this.selectors = siteConfigs.news.selectors;
  }

  /**
   * Extrait les informations d'un article
   * @param {string} articleUrl - URL de l'article
   * @returns {Promise<Object>} - Informations de l'article
   */
  async extractArticleInfo(articleUrl) {
    console.log(`📰 Extraction article: ${articleUrl}`);
    
    const validationRules = {
      articleTitle: { required: true, minLength: 5 },
      articleContent: { required: true, minLength: 50 },
      articleDate: { required: false, pattern: 'date' },
      articleAuthor: { required: false, minLength: 2 }
    };
    
    return this.extractWithValidation(this.selectors, validationRules, 'article');
  }

  /**
   * Extrait les informations de plusieurs articles
   * @param {Array} articleUrls - URLs des articles
   * @returns {Promise<Array>} - Informations des articles
   */
  async extractMultipleArticles(articleUrls) {
    console.log(`📰 Extraction de ${articleUrls.length} articles...`);
    
    const results = [];
    
    for (const url of articleUrls) {
      try {
        const result = await this.extractArticleInfo(url);
        results.push(result);
        
        // Pause entre les extractions
        await this.sleep(1000);
        
      } catch (error) {
        console.log(`❌ Erreur extraction article ${url}: ${error.message}`);
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
   * Extrait les informations de la page d'accueil
   * @returns {Promise<Object>} - Informations de la page d'accueil
   */
  async extractHomepageInfo() {
    console.log('🏠 Extraction page d\'accueil...');
    
    const homepageSelectors = {
      mainHeadline: {
        selector: '.main-headline, .hero-title, .featured-title',
        multiple: false
      },
      featuredArticles: {
        selector: '.featured-article, .hero-article, [data-featured]',
        multiple: true
      },
      latestNews: {
        selector: '.latest-news, .recent-articles, [data-latest]',
        multiple: true
      },
      categories: {
        selector: '.news-category, .section-link, [data-category]',
        multiple: true
      }
    };
    
    return this.extractData(homepageSelectors, 'homepage');
  }

  /**
   * Extrait les informations de catégorie
   * @returns {Promise<Object>} - Informations de catégorie
   */
  async extractCategoryInfo() {
    console.log('📂 Extraction informations catégorie...');
    
    const categorySelectors = {
      categoryTitle: {
        selector: 'h1, .category-title, .section-title',
        multiple: false
      },
      categoryDescription: {
        selector: '.category-description, .section-description',
        multiple: false
      },
      articleList: {
        selector: '.article-list, .news-list, [data-article-list]',
        multiple: true
      },
      pagination: {
        selector: '.pagination, .pager, [data-pagination]',
        multiple: false
      }
    };
    
    return this.extractData(categorySelectors, 'category');
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
        selector: '.search-result, .article-item, [data-search-result]',
        multiple: true
      },
      searchCount: {
        selector: '.search-count, .results-count, [data-search-count]',
        multiple: false
      },
      searchFilters: {
        selector: '.search-filter, .filter-option, [data-filter]',
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
   * Extrait les informations d'auteur
   * @returns {Promise<Object>} - Informations d'auteur
   */
  async extractAuthorInfo() {
    console.log('👤 Extraction informations auteur...');
    
    const authorSelectors = {
      authorName: {
        selector: '.author-name, .byline-author, [data-author]',
        multiple: false
      },
      authorBio: {
        selector: '.author-bio, .author-description, [data-author-bio]',
        multiple: false
      },
      authorImage: {
        selector: '.author-image, .author-avatar, [data-author-image]',
        attribute: 'src',
        multiple: false
      },
      authorArticles: {
        selector: '.author-articles, .author-posts, [data-author-articles]',
        multiple: true
      }
    };
    
    return this.extractData(authorSelectors, 'author');
  }

  /**
   * Extrait les informations de commentaires
   * @returns {Promise<Object>} - Informations de commentaires
   */
  async extractCommentsInfo() {
    console.log('💬 Extraction informations commentaires...');
    
    const commentsSelectors = {
      commentCount: {
        selector: '.comment-count, .comments-count, [data-comment-count]',
        multiple: false
      },
      commentList: {
        selector: '.comment, .comment-item, [data-comment]',
        multiple: true
      },
      commentForm: {
        selector: '.comment-form, .comment-box, [data-comment-form]',
        multiple: false
      }
    };
    
    return this.extractData(commentsSelectors, 'comments');
  }

  /**
   * Extrait les informations de partage social
   * @returns {Promise<Object>} - Informations de partage
   */
  async extractSocialSharingInfo() {
    console.log('📱 Extraction informations partage social...');
    
    const socialSelectors = {
      shareButtons: {
        selector: '.share-button, .social-share, [data-share]',
        multiple: true
      },
      shareCount: {
        selector: '.share-count, .social-count, [data-share-count]',
        multiple: false
      },
      socialLinks: {
        selector: '.social-link, .social-media, [data-social]',
        multiple: true
      }
    };
    
    return this.extractData(socialSelectors, 'social');
  }

  /**
   * Extrait les informations de navigation
   * @returns {Promise<Object>} - Informations de navigation
   */
  async extractNavigationInfo() {
    console.log('🧭 Extraction informations navigation...');
    
    const navigationSelectors = {
      mainMenu: {
        selector: '.main-menu, .primary-nav, [data-main-menu]',
        multiple: true
      },
      breadcrumbs: {
        selector: '.breadcrumb, .breadcrumbs, [data-breadcrumb]',
        multiple: true
      },
      relatedArticles: {
        selector: '.related-article, .similar-article, [data-related]',
        multiple: true
      }
    };
    
    return this.extractData(navigationSelectors, 'navigation');
  }

  /**
   * Extrait les métadonnées de l'article
   * @returns {Promise<Object>} - Métadonnées
   */
  async extractArticleMetadata() {
    console.log('📋 Extraction métadonnées article...');
    
    const metadataSelectors = {
      metaTitle: {
        selector: 'title',
        multiple: false
      },
      metaDescription: {
        selector: 'meta[name="description"]',
        attribute: 'content',
        multiple: false
      },
      metaKeywords: {
        selector: 'meta[name="keywords"]',
        attribute: 'content',
        multiple: false
      },
      metaAuthor: {
        selector: 'meta[name="author"]',
        attribute: 'content',
        multiple: false
      },
      ogTitle: {
        selector: 'meta[property="og:title"]',
        attribute: 'content',
        multiple: false
      },
      ogDescription: {
        selector: 'meta[property="og:description"]',
        attribute: 'content',
        multiple: false
      },
      ogImage: {
        selector: 'meta[property="og:image"]',
        attribute: 'content',
        multiple: false
      }
    };
    
    return this.extractData(metadataSelectors, 'metadata');
  }

  /**
   * Formate les résultats pour l'affichage
   * @param {Object} results - Résultats de l'extraction
   * @returns {string} - Résultats formatés
   */
  formatArticleResults(results) {
    if (!results || !results.data) {
      return '❌ Aucune donnée article disponible';
    }

    const { data } = results;
    return [
      '📰 ARTICLE:',
      `   Titre: ${data.articleTitle || 'Non trouvé'}`,
      `   Auteur: ${data.articleAuthor || 'Non trouvé'}`,
      `   Date: ${data.articleDate || 'Non trouvé'}`,
      `   Contenu: ${data.articleContent ? data.articleContent.substring(0, 150) + '...' : 'Non trouvé'}`,
      `   Tags: ${data.articleTags ? data.articleTags.length : 0} trouvés`
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