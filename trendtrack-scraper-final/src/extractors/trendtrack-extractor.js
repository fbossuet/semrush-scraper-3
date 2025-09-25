/**
 * Extracteur spécialisé pour TrendTrack
 * Extrait les données des boutiques tendances avec pagination
 */

import { BaseExtractor } from './base-extractor.js';
import { DataFormatter } from '../utils/data-formatter.js';
// import { MarketTrafficExtractor } from './market-traffic-extractor.js';
// import { MarketTrafficPythonBridge } from './market-traffic-python-bridge.js';
// import { AdditionalMetricsPythonBridge } from './additional-metrics-python-bridge.js';

export class TrendTrackExtractor extends BaseExtractor {
  constructor(page, errorHandler) {
    super(page, errorHandler);
    
    // Initialiser l'extracteur de trafic par pays (JavaScript)
    // this.marketTrafficExtractor = new MarketTrafficExtractor(page);
    
    // Initialiser le pont Python pour les nouvelles fonctionnalités
    // this.marketTrafficPythonBridge = new MarketTrafficPythonBridge();
    // this.additionalMetricsBridge = new AdditionalMetricsPythonBridge();
    
    // Sélecteurs spécifiques à TrendTrack basés sur l'analyse HTML
    this.selectors = {
      // Informations de la boutique
      shopName: {
        selector: 'td:nth-child(2) div:first-child p.text-sm.font-semibold',
        multiple: false
      },
      shopUrl: {
        selector: 'td:nth-child(2) a[href*="http"]',
        attribute: 'href',
        multiple: false
      },
      shopDomain: {
        selector: 'td:nth-child(2) a[href*="http"]',
        multiple: false
      },
      
      // Catégorie (supprimé - non persistée selon la documentation)
      // category: {
      //   selector: 'td:nth-child(4) div div',
      //   multiple: false
      // },
      
      // Visites mensuelles (supprimé comme demandé)
      // monthlyVisits: {
      //   selector: 'td:nth-child(5) div.h-full.w-full.flex.flex-col.items-center.justify-center.gap-1 p.font-bold',
      //   multiple: false
      // },
      
      // Année de fondation
      yearFounded: {
        selector: 'td:nth-child(2) p.text-\\[11px\\]',
        multiple: false
      },
      
      // Revenus mensuels (supprimé comme demandé)
      // monthlyRevenue: {
      //   selector: 'td div.h-full.w-full.flex.flex-col.items-center.justify-center p.font-bold',
      //   multiple: false
      // },
      
      // Nombre d'ads live (selon documentation: 5e td → p.font-bold)
      liveAds: {
        selector: 'td:nth-child(5) p.font-bold',
        multiple: false
      },
      

    };
    
    // Sélecteurs pour la pagination
    this.paginationSelectors = {
      currentPage: {
        selector: 'input[aria-label="Go to page"]',
        attribute: 'value',
        multiple: false
      },
      totalPages: {
        selector: 'span.text-sm.text-muted-foreground',
        multiple: false
      },
      nextButton: {
        selector: 'a[aria-label="Go to next page"]',
        multiple: false
      },
      previousButton: {
        selector: 'a[aria-label="Go to previous page"]',
        multiple: false
      },
      pageNumbers: {
        selector: 'li a[class*="h-10 w-10"]',
        multiple: true
      }
    };
  }

  /**
   * Se connecte à TrendTrack
   * @param {string} email - Email de connexion
   * @param {string} password - Mot de passe
   * @returns {Promise<boolean>} - Succès de la connexion
   */
  async login(email, password) {
    console.log('🔑 Connexion à TrendTrack...');
    
    try {
      // Navigation vers la page de connexion
      await this.page.goto('https://app.trendtrack.io/en/login', {
        waitUntil: 'domcontentloaded',
        timeout: 60000
      });
      
      // Attendre que le formulaire soit chargé
      await this.page.waitForSelector('input[type="email"][name="email"]', { timeout: 60000 });
      
      // Attendre 3 secondes comme dans le test visuel
      await this.page.waitForTimeout(3000);
      
      // Remplir le formulaire
      await this.page.fill('input[type="email"][name="email"]', email);
      await this.page.fill('input[type="password"][name="password"]', password);
      
      // Attendre 2 secondes comme dans le test visuel
      await this.page.waitForTimeout(2000);
      
      // Cliquer sur le bouton de connexion
      await this.page.click('button[type="submit"]');
      
      // Attendre la redirection comme dans le test visuel
      await this.page.waitForTimeout(5000);
      
      // Vérifier que la connexion a réussi en cherchant un élément de la page d'accueil
      try {
        await this.page.waitForSelector('a[href*="trending-shops"]', { timeout: 60000 });
        console.log('✅ Connexion réussie - Page d\'accueil détectée');
        return true;
      } catch (error) {
        console.log('⚠️ Connexion possiblement échouée - Vérification de la page...');
        
        // Vérifier l'URL actuelle
        const currentUrl = this.page.url();
        console.log(`🔍 URL actuelle: ${currentUrl}`);
        
        // Si on est toujours sur la page de login, la connexion a échoué
        if (currentUrl.includes('/login')) {
          console.log('❌ Connexion échouée - Reste sur la page de login');
          return false;
        }
        
        // Si on a été redirigé ailleurs, considérer comme réussi
        console.log('✅ Connexion réussie - Redirection détectée');
        return true;
      }
      
    } catch (error) {
      console.error('❌ Erreur de connexion:', error.message);
      return false;
    }
  }

  /**
   * Navigue vers la page des boutiques tendances
   * @param {number} [page=1] - Numéro de page à charger
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async navigateToTrendingShops(page = 1) {
    console.log(`📊 Navigation vers les boutiques tendances (page ${page})...`);
    try {
      // Vérifier qu'on est bien connecté et sur la page d'accueil
      const currentUrl = this.page.url();
      console.log(`🔍 URL actuelle: ${currentUrl}`);
      
      if (currentUrl.includes('/login')) {
        console.log('❌ Pas connecté - Redirection vers login détectée');
        return false;
      }
      
      // Si on n'est pas sur la page d'accueil, y aller d'abord
      if (!currentUrl.includes('workspace') && !currentUrl.includes('trending-shops')) {
        console.log('🔄 Navigation vers la page d\'accueil...');
        await this.page.goto('https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st', {
          waitUntil: 'domcontentloaded',
          timeout: 60000
        });
        await this.page.waitForTimeout(2000);
      }
      
      // URL complète avec tous les paramètres
      let url = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops?include=true&tab=websites&minTraffic=500000&languages=en&currencies=USD&creationCountry=US&orderBy=liveAds';
      
      // Ajouter le paramètre de page si nécessaire
      if (page > 1) {
        url += `&page=${page}`;
      }
      
      console.log(`🌐 URL complète de navigation: ${url}`);
      
      // Navigation en maintenant la session
      console.log(`🔄 Chargement de la page...`);
      await this.page.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: 60000
      });
      
      // Attendre un peu pour que la page se charge complètement
      await this.page.waitForTimeout(3000);
      
      // Vérifier qu'on n'a pas été redirigé vers login
      const finalUrl = this.page.url();
      console.log(`🔍 URL finale: ${finalUrl}`);
      
      if (finalUrl.includes('/login')) {
        console.log('❌ Redirection vers login détectée - Session perdue');
        return false;
      }
      
      console.log(`🔍 Recherche du tableau...`);
      // Attendre que le tableau soit chargé
      await this.page.waitForSelector('table', { timeout: 15000 });
      
      // Vérifier que la page contient bien des données
      console.log(`📊 Comptage des lignes...`);
      const tableRows = await this.page.locator('table tbody tr').count();
      console.log(`📊 Nombre de lignes trouvées: ${tableRows}`);
      
      if (tableRows === 0) {
        console.log('⚠️ Aucune donnée trouvée sur la page');
        // Vérifier si on est sur la bonne page
        const currentUrl = this.page.url();
        console.log(`🔍 URL actuelle: ${currentUrl}`);
        return false;
      }
      
      console.log('✅ Navigation vers les boutiques tendances réussie');
      return true;
    } catch (error) {
      console.error(`❌ Erreur navigation page ${page}:`, error.message);
      console.error(`🔍 Stack trace:`, error.stack);
      return false;
    }
  }

  /**
   * Trie par Live Ads
   * @returns {Promise<boolean>} - Succès du tri
   */
  async sortByLiveAds() {
    console.log('📈 Tri par Live Ads...');
    
    try {
      // Attendre que l'en-tête soit chargé
      await this.page.waitForSelector('th div.flex.items-center.gap-1', { timeout: 60000 });
      
      // Trouver l'en-tête "Live Ads" et cliquer dessus
      const liveAdsHeader = await this.page.$('th div.flex.items-center.gap-1:has-text("Live Ads")');
      if (liveAdsHeader) {
        await liveAdsHeader.click();
        
        // Attendre que le tri soit appliqué
        await this.page.waitForTimeout(2000);
        
        console.log('✅ Tri par Live Ads appliqué');
        return true;
      } else {
        console.log('⚠️ En-tête Live Ads non trouvé');
        return false;
      }
      
    } catch (error) {
      console.error('❌ Erreur tri Live Ads:', error.message);
      return false;
    }
  }

  /**
   * Extrait UNIQUEMENT les données du tableau (sans navigation)
   * @param {ElementHandle} row - Ligne du tableau
   * @returns {Promise<Object>} - Données de la boutique du tableau uniquement
   */
  async extractShopDataFromTable(row) {
    try {
      const cells = await row.locator('td').all();
      if (cells.length < 6) {
        console.log('⚠️ Ligne avec seulement', cells.length, 'cellules, ignorée');
        return null;
      }

      // Extraction des données de base du tableau en utilisant les méthodes existantes
      const shopData = {};
      
      // UUID de la boutique (attribut id du <tr>)
      try {
        const rowId = await row.getAttribute('id');
        if (rowId) {
          shopData.external_id = rowId;
          console.log(`✅ UUID de boutique extrait: ${shopData.external_id}`);
        }
      } catch (error) {
        console.log('⚠️ UUID de boutique non trouvé');
      }
      
      // Nom de la boutique (2e td > 1er div > p)
      try {
        const nameElement = await cells[1].locator('div:first-child p.text-sm.font-semibold').first();
        if (await nameElement.count() > 0) {
          shopData.shop_name = (await nameElement.textContent())?.trim();
          console.log(`✅ Nom de boutique extrait: ${shopData.shop_name}`);
        }
      } catch (error) {
        console.log('⚠️ Nom de boutique non trouvé');
      }

      // URL de la boutique (2e td)
      try {
        const urlElement = await cells[1].locator('a[href*="http"]').first();
        if (await urlElement.count() > 0) {
          shopData.shop_url = await urlElement.getAttribute('href');
          console.log(`✅ URL de boutique extraite: ${shopData.shop_url}`);
        }
      } catch (error) {
        console.log('⚠️ URL de boutique non trouvée');
      }

      // Catégorie (4e td)
      try {
        const categoryElement = await cells[3].locator('div div').first();
        if (await categoryElement.count() > 0) {
          shopData.category = (await categoryElement.textContent())?.trim();
          console.log(`✅ Catégorie extraite: ${shopData.category}`);
        }
      } catch (error) {
        console.log('⚠️ Catégorie non trouvée');
      }

      // Visites mensuelles: récupérées en Phase 3 (détails), pas en Phase 1

      // Revenus mensuels (supprimé comme demandé)
      // shopData.monthly_revenue = null;

      // Nombre de produits (3e td)
      try {
        const productsElement = await cells[2].locator('p.text-sm.font-semibold').first();
        if (await productsElement.count() > 0) {
          const productsText = await productsElement.textContent();
          const match = productsText.match(/\d[\d\s.,]*/);
          shopData.total_products = match ? Number(match[0].replace(/[^\d]/g, "")) : null;
          console.log(`✅ Nombre de produits extrait: ${shopData.total_products}`);
        }
      } catch (error) {
        console.log('⚠️ Nombre de produits non trouvé');
      }

      // Live ads 7d et 30d - Extrait UNIQUEMENT en Phase 3 (page de détail) selon la spécification
      // Ces métriques ne sont PAS extraites en Phase 1 - elles seront ajoutées en Phase 3

      // 🆕 Extraction de l'année de fondation (Phase 1 - page de liste) - V2 AMÉLIORÉE
      try {
        console.log(`🔍 Extraction année de fondation V2 pour ${shopData.shop_name}...`);
        
        // Sélecteurs multiples pour year_founded (V2)
        const yearSelectors = [
          'p.text-\\[11px\\]',  // Sélecteur principal (échappement CSS)
          'p[class*="text-11px"]',
          'p[class*="text-xs"]',
          'span[class*="text-11px"]',
          'div[class*="text-11px"]'
        ];
        
        let yearFound = false;
        
        for (const selector of yearSelectors) {
          try {
            console.log(`🔍 Tentative year_founded avec sélecteur: ${selector}`);
            const yearElement = await cells[1].locator(selector).first();
            
            if (await yearElement.count() > 0) {
              const yearText = await yearElement.textContent();
              console.log(`📅 Texte année trouvé: "${yearText}"`);
              
              // Formatage via le module dédié
              const formattedData = DataFormatter.formatYearFounded(yearText);
              if (formattedData !== null) {
                shopData.year_founded = formattedData.year_founded;
                shopData.creation_date = formattedData.creation_date;
                console.log(`✅ Année de fondation extraite: ${formattedData.year_founded}, Date: ${formattedData.creation_date}`);
                yearFound = true;
                break;
              }
            }
          } catch (selectorError) {
            console.log(`⚠️ Sélecteur year_founded échoué: ${selector}`);
            continue;
          }
        }
        
        // Fallback: recherche dans tout le contenu de la cellule
        if (!yearFound) {
          console.log('🔍 Fallback: recherche year_founded dans tout le contenu de la cellule...');
          const cellContent = await cells[1].textContent();
          const formattedData = DataFormatter.formatYearFounded(cellContent);
          if (formattedData !== null) {
            shopData.year_founded = formattedData.year_founded;
            shopData.creation_date = formattedData.creation_date;
            console.log(`✅ Année de fondation extraite via fallback: ${formattedData.year_founded}, Date: ${formattedData.creation_date}`);
            yearFound = true;
          }
        }
        
        if (!yearFound) {
          console.log(`⚠️ Année de fondation non trouvée pour ${shopData.shop_name}`);
          shopData.year_founded = null;
          shopData.creation_date = null;
        }
        
      } catch (error) {
        console.error(`❌ Erreur extraction année de fondation pour ${shopData.shop_name}:`, error.message);
        shopData.year_founded = null;
        shopData.creation_date = null;
      }

      // Ajouter les métadonnées
      shopData.table_scraping_status = 'table_extracted';
      shopData.last_updated = new Date().toISOString();

      // Vérifier qu'on a au moins le nom et l'URL
      if (!shopData.shop_name || !shopData.shop_url) {
        console.log('⚠️ Données insuffisantes pour la boutique');
        return null;
      }

      console.log(`✅ Boutique extraite: ${shopData.shop_name} (${shopData.shop_url})`);
      return shopData;
    } catch (error) {
      console.error('❌ Erreur extraction données tableau:', error.message);
      return null;
    }
  }

  /**
   * Extrait les données d'une ligne de boutique
   * @param {Object} row - Élément de ligne
   * @param {boolean} includeMarketData - Inclure les données de trafic par pays
   * @returns {Promise<Object>} - Données de la boutique
   */
  async extractShopData(row, includeMarketData = false) {
    try {
      const shopData = {};
      
      // 🆕 Extraire l'ID de la boutique avec timeout réduit
      let rowId = null;
      try {
        const rowHtml = await row.evaluate(el => el.outerHTML, { timeout: 10000 });
        const rowIdMatch = rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/);
        rowId = rowIdMatch ? rowIdMatch[1] : null;
      } catch (error) {
        console.log(`⚠️ Timeout extraction ID ligne, utilisation de l'index`);
        rowId = `row_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      }
      shopData.shopId = rowId;
      shopData.externalId = rowId; // Mapping pour la base de données
      
      // Utiliser une approche plus robuste pour extraire les données
      const cells = await row.locator('td').all();
      if (cells.length < 8) {
        console.log(`⚠️ Ligne avec seulement ${cells.length} cellules, ignorée`);
        return null;
      }
      
      // Extraire les données de base avec gestion d'erreur
      try {
        const shopInfoHtml = await cells[1].innerHTML();
        const shopNameMatch = shopInfoHtml.match(/<p class=\"text-sm font-semibold\">([^<]+)<\/p>/);
        shopData.shopName = shopNameMatch ? shopNameMatch[1].trim() : '';
        const shopUrlMatch = shopInfoHtml.match(/href=["']([^"']+)["']/);
        shopData.shopUrl = shopUrlMatch ? shopUrlMatch[1] : '';
        const dateMatch = shopInfoHtml.match(/(\d{2}\/\d{2}\/\d{4})/);
        shopData.creationDate = dateMatch ? dateMatch[1] : '';
      } catch (error) {
        console.error(`⚠️ Erreur extraction info boutique: ${error.message}`);
        shopData.shopName = '';
        shopData.shopUrl = '';
        shopData.creationDate = '';
      }
      
      try {
        shopData.category = (await cells[3].textContent()).trim();
        
        // Utiliser DataFormatter pour monthly_visits
        const monthlyVisitsText = (await cells[4].textContent()).trim();
        shopData.monthlyVisits = DataFormatter.formatMonthlyVisits(monthlyVisitsText);
        
        shopData.monthlyRevenue = (await cells[5].textContent()).trim();
      } catch (error) {
        console.error(`⚠️ Erreur extraction métriques de base: ${error.message}`);
        shopData.category = '';
        shopData.monthlyVisits = null;
        shopData.monthlyRevenue = '';
      }
      
      // Live Ads (cellule 7) avec gestion d'erreur améliorée
      try {
        const liveAdsDiv = await cells[7].locator('div.flex.items-center.justify-center.font-semibold');
        const liveAdsP = await liveAdsDiv.locator('p').first();
        shopData.liveAds = liveAdsP ? (await liveAdsP.textContent()).trim() : '';
      } catch (error) {
        console.error(`⚠️ Erreur extraction Live Ads: ${error.message}`);
        shopData.liveAds = '';
      }

      // 🆕 Extraction directe du nombre de produits (colonne 2)
      try {
        const productsCell = cells[2];
        const productsP = productsCell.locator("p:has(> span:has-text(\"products\"))");
        const productsText = await productsP.textContent();
        if (productsText) {
          const match = productsText.match(/\d[\d\s.,]*/);
          shopData.totalProducts = match ? Number(match[0].replace(/[^\d]/g, "")) : null;
          console.log(`📦 Produits extraits pour ${shopData.shopName}: ${shopData.totalProducts}`);
        } else {
          shopData.totalProducts = null;
        }
      } catch (error) {
        console.error(`⚠️ Erreur extraction produits pour ${shopData.shopName}:`, error.message);
        shopData.totalProducts = null;
      }

      // 🆕 Extraction de l'année de fondation (Phase 1 - page de liste)
      try {
        console.log(`🔍 Extraction année de fondation pour ${shopData.shopName}...`);
        
        // Chercher dans la cellule d'info de la boutique (cellule 1)
        const shopInfoHtml = await cells[1].innerHTML();
        
        // Patterns pour l'année de fondation
        const yearPatterns = [
          /founded[:\s]*(\d{4})/i,
          /since[:\s]*(\d{4})/i,
          /established[:\s]*(\d{4})/i,
          /created[:\s]*(\d{4})/i,
          /(\d{4})[:\s]*founded/i,
          /(\d{4})[:\s]*since/i,
          /(\d{4})[:\s]*established/i,
          /(\d{4})[:\s]*created/i
        ];
        
        let yearFounded = null;
        for (const pattern of yearPatterns) {
          const match = shopInfoHtml.match(pattern);
          if (match && match[1]) {
            const year = parseInt(match[1]);
            if (year >= 1990 && year <= new Date().getFullYear()) {
              yearFounded = year;
              console.log(`📅 Année de fondation trouvée: ${yearFounded}`);
              break;
            }
          }
        }
        
        shopData.yearFounded = yearFounded;
        
        if (!yearFounded) {
          console.log(`⚠️ Aucune année de fondation trouvée pour ${shopData.shopName}`);
        }
        
      } catch (error) {
        console.error(`⚠️ Erreur extraction année de fondation pour ${shopData.shopName}:`, error.message);
        shopData.yearFounded = null;
      }



      // Ajouter les données de trafic par pays si demandé
      if (includeMarketData && shopData.shopUrl) {
        try {
          console.log(`🌍 Extraction trafic par pays pour: ${shopData.shopName}`);
          const marketData = await this.extractMarketTrafficForShop(shopData.shopId || shopData.shopUrl);
          if (marketData) {
            Object.assign(shopData, marketData);
          }
        } catch (error) {
          console.error(`⚠️ Erreur extraction trafic pour ${shopData.shopName}:`, error.message);
          // Ajouter des valeurs null pour les champs market_*
          shopData.market_us = null;
          shopData.market_uk = null;
          shopData.market_de = null;
          shopData.market_ca = null;
          shopData.market_au = null;
          shopData.market_fr = null;
        }
      }

      // 🆕 Récupération des métriques supplémentaires via Python
      if (shopData.shopUrl) {
        try {
          console.log(`🔍 Extraction métriques supplémentaires pour: ${shopData.shopName}`);
          
          // Extraire les métriques supplémentaires (total_products, pixel_google, pixel_facebook, aov)
          const pixelData = await this.extractPixelsForShopJS(shopData.shopId);
            
            shopData.pixel_google = pixelData.pixel_google;
            shopData.pixel_facebook = pixelData.pixel_facebook;
            
            console.log(`✅ Métriques supplémentaires extraites pour ${shopData.shopName}`);
          
        } catch (error) {
          console.error(`⚠️ Erreur extraction métriques supplémentaires pour ${shopData.shopName}:`, error.message);
          // Ajouter des valeurs null pour les champs en cas d'erreur
          shopData.totalProducts = null;
          shopData.pixel_google = "non";
          shopData.pixel_facebook = "non";
          
        }
      }

      return shopData;
    } catch (error) {
      console.error('❌ Erreur extraction données boutique:', error.message);
      return null;
    }
  }

  /**
   * Extrait UNIQUEMENT les données du tableau (sans navigation vers les détails)
   * @returns {Promise<Array>} - Liste des boutiques avec données du tableau uniquement
   */
  async extractTableDataOnly() {
    console.log('📋 Extraction des données du tableau uniquement (sans navigation)...');
    
    try {
      // Attendre que le tableau soit chargé
      await this.page.waitForSelector('tbody tr', { timeout: 60000 });
      
      // Récupérer toutes les lignes du tableau
      const rows = await this.page.locator('tbody tr').all();
      console.log(`📊 ${rows.length} lignes trouvées`);
      
      const shopsData = [];
      
      for (let i = 0; i < rows.length; i++) {
        console.log(`🔍 Extraction ligne ${i + 1}/${rows.length}...`);
        
        const shopData = await this.extractShopDataFromTable(rows[i]);
        if (shopData) {
          shopsData.push({
            ...shopData,
            rowIndex: i + 1,
            timestamp: new Date().toISOString()
          });
        }
        
        // Pause minimale entre les extractions
        await this.sleep(50);
      }
      
      console.log(`✅ ${shopsData.length} boutiques extraites du tableau`);
      return shopsData;
      
    } catch (error) {
      console.error('❌ Erreur extraction tableau:', error.message);
      return [];
    }
  }

  /**
   * Extrait toutes les données du tableau
   * @param {boolean} includeMarketData - Inclure les données de trafic par pays
   * @returns {Promise<Array>} - Liste des boutiques
   */
  async extractAllShopsData(includeMarketData = false) {
    console.log('📋 Extraction de toutes les données du tableau...');
    
    try {
      // Attendre que le tableau soit chargé
      console.log('🔍 Debug: Recherche du sélecteur tbody tr...');
      
      // Debug: capturer le contenu de la page
      const pageContent = await this.page.content();
      console.log(`🔍 Debug: Taille du contenu de la page: ${pageContent.length} caractères`);
      
      // Debug: vérifier les éléments disponibles
      const hasTable = await this.page.locator('table').count();
      const hasTbody = await this.page.locator('tbody').count();
      const hasTr = await this.page.locator('tr').count();
      console.log(`🔍 Debug: Éléments trouvés - table: ${hasTable}, tbody: ${hasTbody}, tr: ${hasTr}`);
      
      // Debug: URL actuelle
      const currentUrl = await this.page.url();
      console.log(`🔍 Debug: URL actuelle: ${currentUrl}`);
      
      // Debug: titre de la page
      const pageTitle = await this.page.title();
      console.log(`🔍 Debug: Titre de la page: ${pageTitle}`);
      
      await this.page.waitForSelector('tbody tr', { timeout: 60000 });
      
      // Récupérer toutes les lignes du tableau
      const rows = await this.page.locator('tbody tr').all();
      console.log(`📊 ${rows.length} lignes trouvées`);
      
      const shopsData = [];
      
      for (let i = 0; i < rows.length; i++) {
        console.log(`🔍 Extraction ligne ${i + 1}/${rows.length}...`);
        
        const shopData = await this.extractShopData(rows[i], true); // Toujours activer l'extraction des métriques avancées
        if (shopData) {
          shopsData.push({
            ...shopData,
            rowIndex: i + 1,
            timestamp: new Date().toISOString()
          });
        }
        
        // Pause entre les extractions (plus longue si on inclut les données de trafic)
        await this.sleep(includeMarketData ? 2000 : 100);
      }
      
      console.log(`✅ ${shopsData.length} boutiques extraites`);
      return shopsData;
      
    } catch (error) {
      console.error('❌ Erreur extraction tableau:', error.message);
      return [];
    }
  }

  /**
   * Navigue vers la page de détail d'une boutique (Phase 3)
   * @param {string} shopId - UUID externe TrendTrack (external_id)
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async navigateToShopDetail(shopId) {
    console.log(`🔍 Navigation vers la page de détail (UUID): ${shopId}`);
    
    try {
      // URL cible Phase 3 (FR): /fr/workspace/.../trending-shops/{UUID}
      const detailUrl = `https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${shopId}`;
      console.log(`🔍 URL de détail TrendTrack: ${detailUrl}`);
      
      // Première tentative
      await this.page.goto(detailUrl, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      await this.page.waitForTimeout(2000);
      // Détection page login
      const isLogin = await this.isLoginPage();
      if (isLogin) {
        console.log('❌ Redirection vers login détectée après navigation');
        return false;
      }
      
      const currentUrl = this.page.url();
      if (currentUrl.includes(`/trending-shops/${shopId}`)) {
        console.log('✅ Navigation vers page de détail réussie');
        return true;
      } else {
        console.log('❌ Navigation échouée - URL incorrecte, nouvel essai...');
        // Retry unique avec backoff court
        await this.page.waitForTimeout(1500);
        await this.page.goto(detailUrl, {
          waitUntil: 'domcontentloaded',
          timeout: 60000
        });
        const url2 = this.page.url();
        if (url2.includes(`/trending-shops/${shopId}`)) {
          console.log('✅ Navigation vers page de détail réussie (retry)');
          return true;
        }
        console.log('❌ Navigation échouée après retry');
        return false;
      }
      
    } catch (error) {
      console.error(`❌ Erreur navigation détail: ${error.message}`);
      return false;
    }
  }

  /**
   * Vérifie si la page courante est la page de login TrendTrack
   * @returns {Promise<boolean>}
   */
  async isLoginPage() {
    try {
      const url = this.page.url();
      if (url.includes('/login')) return true;
      const title = await this.page.title();
      if ((title || '').toLowerCase().includes('login')) return true;
      // Vérifier présence du formulaire de login
      const hasLoginForm = await this.page.locator('input[type="email"], input[name="email"]').first().count();
      return hasLoginForm > 0;
    } catch {
      return false;
    }
  }

  /**
   * Extrait les détails d'une boutique depuis sa page
   * @returns {Promise<Object>} - Données de détail de la boutique
   */
  async extractShopDetails(shopId = null) {
    console.log(`🔍 Extraction des détails de la boutique (ID: ${shopId})...`);
    
    try {
      // Vérifier que la page est bien chargée - CORRECTION du sélecteur
      try {
        await this.page.waitForSelector('body', { timeout: 10000 });
        console.log('✅ Page de détail chargée');
      } catch (error) {
        console.log('⚠️ Timeout sur le chargement de la page');
      }
      
      // 🚀 NOUVELLE MÉTHODE : Extraction des pixels via API TrendTrack
      console.log('🔍 Extraction des pixels via API TrendTrack...');
      const pixelData = await this.extractPixelsForShopJS(shopId || 'current_shop'); // Utiliser l'ID de la boutique
      
      // 🌍 EXTRACTION DES DONNÉES GÉOGRAPHIQUES VIA DOM
      console.log('🌍 Extraction des données géographiques via DOM...');
      const marketData = await this.extractGeoDataViaDOM();
      
      const detailData = {
        
        // Métriques de performance
        bounce_rate: await this.extractMetric('Bounce Rate'),
        avg_visit_duration: await this.extractMetric('Avg. Visit Duration'),
        conversion_rate: await this.extractMetric('Conversion Rate'),
        
        // Trafic par pays - MÉTHODE API OPTIMISÉE
        market_us: marketData.market_us,
        market_uk: marketData.market_uk,
        market_de: marketData.market_de,
        market_ca: marketData.market_ca,
        market_au: marketData.market_au,
        market_fr: marketData.market_fr,
        
        // Pixels - MÉTHODE API OPTIMISÉE
        pixel_google: pixelData.pixel_google,
        pixel_facebook: pixelData.pixel_facebook,
        
        // Année de fondation (extraite en Phase 1, pas en Phase 3)
        year_founded: null,
        creation_date: null,
        
        // AOV (Average Order Value)
        aov: await this.extractAOV(),
        
        // Trafic payant
        paid_search_traffic: await this.extractPaidSearchTraffic(),
        cpc: await this.extractCPC(),
        
        // Trafic organique
        organic_traffic: await this.extractOrganicTraffic(),
        
        // Trafic marqué
        branded_traffic: await this.extractBrandedTraffic(),
        percent_branded_traffic: await this.extractPercentBrandedTraffic(),
        
        // Live ads 7d et 30d - Phase 3 (page de détail) selon la spécification
        live_ads_7d: await this.extractLiveAds7d(),
        live_ads_30d: await this.extractLiveAds30d(),
        
        details_scraping_status: 'details_extracted',
        last_updated: new Date().toISOString()
      };
      
      // Vérifier si au moins une métrique a été extraite
      const hasData = Object.values(detailData).some(value => 
        value !== null && value !== undefined && value !== '' && value !== 0
      );
      
      if (!hasData) {
        console.log('⚠️ Aucune métrique extraite - marquage comme failed');
        return {
          scraping_status: 'failed',
          last_updated: new Date().toISOString(),
          error: 'No metrics extracted'
        };
      }
      
      console.log('✅ Détails de la boutique extraits');
      return detailData;
      
    } catch (error) {
      console.error(`❌ Erreur extraction détails: ${error.message}`);
      return {
        scraping_status: 'failed',
        last_updated: new Date().toISOString(),
        error: error.message
      };
    }
  }

  /**
   * Retourne à la page liste (sans perdre la session)
   * @returns {Promise<boolean>} - Succès du retour
   */
  async returnToListPage() {
    console.log('⬅️ Retour à la page liste...');
    
    try {
      // Retour à la page des boutiques tendances
      await this.page.goto('https://trendtrack.io/trending-shops', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      // Attendre que la page se charge
      await this.page.waitForTimeout(2000);
      
      // Vérifier qu'on est bien sur la page liste
      const currentUrl = this.page.url();
      if (currentUrl.includes('trending-shops')) {
        console.log('✅ Retour à la page liste réussi');
        return true;
      } else {
        console.log('❌ Retour échoué - URL incorrecte');
        return false;
      }
      
    } catch (error) {
      console.error(`❌ Erreur retour liste: ${error.message}`);
      return false;
    }
  }

  /**
   * Extrait une métrique spécifique de la page
   * @param {string} metricName - Nom de la métrique
   * @returns {Promise<string>} - Valeur de la métrique
   */
  async extractMetric(metricName) {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = `text=${metricName}`;
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return value?.trim() || null;
      }
      return null;
    } catch (error) {
      console.log(`⚠️ Métrique ${metricName} non trouvée`);
      return null;
    }
  }

  /**
   * Extrait le trafic d'un pays spécifique
   * @param {string} country - Code du pays
   * @returns {Promise<number>} - Trafic du pays
   */
  async extractCountryTraffic(country) {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = `text=${country}`;
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return 0;
    } catch (error) {
      console.log(`⚠️ Trafic ${country} non trouvé`);
      return 0;
    }
  }

  /**
   * Extrait la présence d'un pixel
   * @param {string} pixelType - Type de pixel (Google, Facebook)
   * @returns {Promise<boolean>} - Présence du pixel
   */
  async extractPixel(pixelType) {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = `text=${pixelType}`;
      const element = await this.page.locator(selector).first();
      return await element.count() > 0;
    } catch (error) {
      console.log(`⚠️ Pixel ${pixelType} non trouvé`);
      return false;
    }
  }

  /**
   * Extrait l'année de fondation
   * @returns {Promise<number>} - Année de fondation
   */
  async extractYearFounded() {
    try {
      console.log('🔍 Extraction année de fondation via DOM...');
      
      // Sélecteurs basés sur l'analyse du DOM fourni
      const selectors = [
        'p.text-\\[11px\\]',           // Sélecteur principal unique trouvé dans le DOM
        'p[class*="text-11px"]',       // Variante du sélecteur
        'p[class*="text-xs"]',         // Autres variantes
        'p[class*="text-sm"]',
        'p[class*="text-"]',           // Sélecteur générique
        'text=/founded/i',             // Fallback textuel
        'text=/since/i', 
        'text=/established/i',
        'text=/created/i',
        'text=/©/i'
      ];
      
      // Essayer chaque sélecteur
      for (const selector of selectors) {
        try {
          const element = await this.page.locator(selector).first();
          if (await element.count() > 0) {
            const text = await element.textContent();
            if (text) {
              const year = this.extractYearFromString(text);
              if (year) {
                console.log(`📅 Année trouvée avec sélecteur '${selector}': ${year}`);
                return year;
              }
            }
          }
        } catch (e) {
          // Continuer avec le prochain sélecteur
          continue;
        }
      }
      
      console.log('❌ Aucune année de fondation trouvée');
      return null;
      
    } catch (error) {
      console.log('⚠️ Erreur extraction année de fondation:', error.message);
      return null;
    }
  }

  /**
   * Extrait l'AOV (Average Order Value)
   * @returns {Promise<number>} - AOV
   */
  async extractAOV() {
    try {
      console.log('🔍 Extraction AOV (V2 - calcul revenu/commandes puis fallback)...');

      // 0) Calcul direct: AOV = revenue / orders
      try {
        const { revenue, orders } = await this.extractRevenueAndOrders();
        if (typeof revenue === 'number' && revenue > 0 && typeof orders === 'number' && orders > 0) {
          const computedAov = revenue / orders;
          if (computedAov >= 1 && computedAov <= 10000) {
            console.log(`✅ AOV calculé: ${computedAov.toFixed(2)} (revenue=${revenue}, orders=${orders})`);
            return Number(computedAov.toFixed(2));
          }
        }
      } catch (calcErr) {
        console.log(`⚠️ Calcul AOV via revenu/commandes échoué: ${calcErr.message}`);
      }
      
      // Sélecteurs multiples pour AOV (V3 - Optimisés pour TrendTrack)
      const aovSelectors = [
        // Sélecteur 1: Spécifiques à TrendTrack (structure réelle)
        '[data-testid*="aov"]',
        '[data-testid*="order-value"]',
        // Sélecteur 2: Classes CSS spécifiques TrendTrack
        '.metric-card [class*="aov"]',
        '.metric-card [class*="order-value"]',
        '.stats-grid [class*="aov"]',
        // Sélecteur 3: Recherche dans les sections métriques
        'section:has-text("Average Order Value") p',
        'section:has-text("AOV") p',
        'div:has-text("Order Value") p',
        // Sélecteur 4: Recherche par texte "AOV" ou "Average Order Value"
        'text=AOV',
        'text=Average Order Value',
        'text=Order Value',
        // Sélecteur 5: Recherche par pattern de prix (plus spécifique)
        'text=/\\$[0-9]+(?:\\.[0-9]{2})?/',
        'text=/€[0-9]+(?:\\.[0-9]{2})?/',
        'text=/£[0-9]+(?:\\.[0-9]{2})?/',
        // Sélecteur 6: Fallback générique
        '[class*="aov"]',
        '[class*="order-value"]'
      ];
      
      for (const selector of aovSelectors) {
        try {
          console.log(`🔍 Tentative AOV avec sélecteur: ${selector}`);
      const element = await this.page.locator(selector).first();
          
      if (await element.count() > 0) {
        const value = await element.textContent();
            console.log(`📊 AOV trouvé: "${value}"`);
            
            // Parsing robuste de la valeur AOV
            const parsedValue = DataFormatter.formatAOV(value);
            if (parsedValue !== null) {
              console.log(`✅ AOV extrait avec succès: ${parsedValue}`);
              return parsedValue;
            }
          }
        } catch (selectorError) {
          console.log(`⚠️ Sélecteur AOV échoué: ${selector}`);
          continue;
        }
      }
      
      // Fallback: Recherche dans tout le contenu de la page
      console.log('🔍 Fallback: recherche AOV dans tout le contenu...');
      const pageContent = await this.page.content();
      const aovPatterns = [
        /AOV[:\s]*\$?([0-9,]+\.?[0-9]*)/i,
        /Average Order Value[:\s]*\$?([0-9,]+\.?[0-9]*)/i,
        /Order Value[:\s]*\$?([0-9,]+\.?[0-9]*)/i,
        /\$([0-9,]+\.?[0-9]*)\s*(?:AOV|per order)/i
      ];
      
      for (const pattern of aovPatterns) {
        const match = pageContent.match(pattern);
        if (match && match[1]) {
          const parsedValue = DataFormatter.formatAOV(match[1]);
          if (parsedValue !== null) {
            console.log(`✅ AOV extrait via fallback: ${parsedValue}`);
            return parsedValue;
          }
        }
      }
      
      console.log('⚠️ AOV non trouvé avec tous les sélecteurs');
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur extraction AOV: ${error.message}`);
      return null;
    }
  }

  /**
   * Extrait les visites mensuelles depuis la page de détail (Phase 3)
   * - Capture la valeur affichée, sélectionne le premier nombre valide (support K/M)
   */
  async extractMonthlyVisitsDetail() {
    try {
      // Cible potentielle sur la page de détail (ex. bloc KPI à proximité des live ads)
      // 1) Tentative directe sur un éventuel p de headline
      const headline = this.page.locator('p.text-2xl.font-medium').first();
      if (await headline.count() > 0) {
        const t = (await headline.textContent())?.trim() || '';
        const m = t.match(/([0-9][0-9.,]*)([kKmM]?)/);
        if (m) {
          return `${m[1]}${m[2] || ''}`;
        }
      }
      // 2) Fallback: chercher le premier <p> numérique globalement dans un bloc métrique
      const ps = await this.page.locator('p').all();
      for (const p of ps) {
        const t = (await p.textContent())?.trim() || '';
        if (/^[0-9][0-9.,]*[kKmM]?$/.test(t)) {
          return t;
        }
      }
      return null;
    } catch (e) {
      console.log(`⚠️ Erreur extraction visits détail: ${e.message}`);
      return null;
    }
  }

  /**
   * Extrait revenue et orders depuis la page détail (heuristiques, contenu)
   */
  async extractRevenueAndOrders() {
    let revenue = null;
    let orders = null;
    try {
      // 0) CIBLAGE PRÉCIS DU KPI "Revenu mensuel estimé" (ou EN: Estimated monthly revenue)
      try {
        const revenueCard = this.page.locator('div.rounded-xl', {
          has: this.page.getByText(/Revenu mensuel estimé|Estimated monthly revenue/i)
        }).first();
        if (await revenueCard.count() > 0) {
          const valueEl = revenueCard.locator('p.text-2xl.font-medium').first();
          if (await valueEl.count() > 0) {
            const raw = (await valueEl.textContent())?.trim() || '';
            const range = this.parseRevenueRange(raw);
            if (range && typeof range.avg === 'number' && range.avg > 0) {
              revenue = range.avg;
              console.log(`✅ Revenu KPI extrait: "${raw}" → avg=${revenue}`);
            } else {
              console.log(`⚠️ Plage de revenu non reconnue (KPI): "${raw}"`);
            }
          }
        }
      } catch (e) {
        console.log(`⚠️ Erreur ciblage KPI Revenu: ${e.message}`);
      }

      // 0.b) Si pas trouvé via KPI, éviter le headline des visits (mauvais bloc)
      // On ne lit PAS 'p.text-2xl.font-medium' globalement sans filtrer par label.

      // 0) Sélecteur direct pour la plage de revenu (ex: "597.9K$ - 1.8M$")
      try {
        const revenueLocator = this.page.locator('p.text-2xl.font-medium').first();
        if (await revenueLocator.count() > 0) {
          const raw = (await revenueLocator.textContent()) || '';
          const parsedRange = this.parseRevenueRange(raw);
          if (parsedRange && typeof parsedRange.avg === 'number' && parsedRange.avg > 0) {
            revenue = parsedRange.avg;
            console.log(`✅ Revenu extrait via sélecteur p.text-2xl.font-medium: "${raw.trim()}" → avg=${revenue}`);
          } else {
            console.log(`⚠️ Plage de revenu non reconnue: "${raw.trim()}"`);
          }
        }
      } catch (e) {
        console.log(`⚠️ Erreur sélecteur revenu: ${e.message}`);
      }

      const html = await this.page.content();
      // Revenue patterns (montants avec devise, suffixes K/M acceptés)
      const revenuePatterns = [
        /(Revenue|Sales|GMV)[^\n\r$£€]*([$€£]\s?[0-9,.]+[KM]?)/i,
        /([$€£]\s?[0-9,.]+[KM]?).{0,20}(Revenue|Sales|GMV)/i
      ];
      for (const rp of revenuePatterns) {
        const m = html.match(rp);
        if (m) {
          const raw = m[2] || m[1];
          const parsed = this.parseCurrencyToNumber(raw);
          if (parsed && parsed > 0) { revenue = parsed; break; }
        }
      }
      // Orders patterns (entiers proches des libellés)
      const ordersPatterns = [
        /(Orders|Commandes|Purchases)[:\s]*([0-9,\.]+)/i,
        /([0-9,\.]+)\s*(Orders|Commandes|Purchases)/i
      ];
      for (const op of ordersPatterns) {
        const m = html.match(op);
        if (m) {
          const raw = m[2] || m[1];
          const parsed = this.parseIntegerFromText(raw);
          if (parsed && parsed > 0) { orders = parsed; break; }
        }
      }
    } catch (e) {
      console.log(`⚠️ Fallback contenu revenu/commandes échoué: ${e.message}`);
    }

    // Si manquant, courte tentative par sélecteurs texte
    if (revenue === null) {
      try {
        const loc = this.page.locator('text=/Revenue|Sales|GMV/i').first();
        if (await loc.count() > 0) {
          const txt = await loc.textContent();
          const parsed = this.parseCurrencyToNumber(txt || '');
          if (parsed && parsed > 0) revenue = parsed;
        }
      } catch {}
    }
    if (orders === null) {
      try {
        const loc = this.page.locator('text=/Orders|Commandes|Purchases/i').first();
        if (await loc.count() > 0) {
          const txt = await loc.textContent();
          const parsed = this.parseIntegerFromText(txt || '');
          if (parsed && parsed > 0) orders = parsed;
        }
      } catch {}
    }
    console.log(`🔎 Revenue/Orders: revenue=${revenue}, orders=${orders}`);
    return { revenue, orders };
  }

  /**
   * Parse une plage de revenu au format "597.9K$ - 1.8M$" et retourne {min, max, avg}
   */
  parseRevenueRange(text) {
    if (!text) return null;
    try {
      const priceRegex = /^\s*[\d.,]+[KMB]*\$\s*-\s*[\d.,]+[KMB]*\$\s*$/i;
      const s = String(text).trim();
      if (!priceRegex.test(s)) return null;
      const parts = s.split('-').map(p => p.trim());
      if (parts.length !== 2) return null;
      const min = this.parseAmountWithSuffix(parts[0]);
      const max = this.parseAmountWithSuffix(parts[1]);
      if (typeof min === 'number' && typeof max === 'number' && min > 0 && max > 0) {
        const avg = (min + max) / 2;
        return { min, max, avg };
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Parse un token monétaire avec symbole en suffixe (ex: "597.9K$", "1.8M$")
   */
  parseAmountWithSuffix(token) {
    if (!token) return null;
    try {
      let t = String(token).trim();
      // Retirer symboles monétaires où qu'ils soient
      t = t.replace(/[$€£\s]/g, '');
      const m = t.match(/^([0-9][0-9.,]*)([kKmMbB]?)$/);
      if (!m) return null;
      const base = parseFloat(m[1].replace(/,/g, ''));
      if (isNaN(base)) return null;
      const suf = (m[2] || '').toLowerCase();
      if (suf === 'k') return base * 1_000;
      if (suf === 'm') return base * 1_000_000;
      if (suf === 'b') return base * 1_000_000_000;
      return base;
    } catch {
      return null;
    }
  }

  parseCurrencyToNumber(text) {
    try {
      if (!text) return null;
      let s = String(text).trim();
      const m = s.match(/([$€£]?\s*)([0-9,.]+)\s*([kKmM]?)/);
      if (!m) return null;
      let num = m[2].replace(/,/g, '');
      let value = parseFloat(num);
      if (isNaN(value)) return null;
      const suffix = (m[3] || '').toLowerCase();
      if (suffix === 'k') value *= 1000;
      if (suffix === 'm') value *= 1000000;
      return value;
    } catch {
      return null;
    }
  }

  parseIntegerFromText(text) {
    try {
      if (!text) return null;
      const m = String(text).match(/([0-9][0-9,\.]*)/);
      if (!m) return null;
      const cleaned = m[1].replace(/[,\.]/g, '');
      const n = parseInt(cleaned, 10);
      return isNaN(n) ? null : n;
    } catch {
      return null;
    }
  }

  // Fonction parseYearFounded supprimée - remplacée par DataFormatter.formatYearFounded()
  // Fonction parseAOVValue supprimée - remplacée par DataFormatter.formatAOV()

  /**
   * Extrait le trafic de recherche payante
   * @returns {Promise<number>} - Trafic de recherche payante
   */
  async extractPaidSearchTraffic() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=Paid Search';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return 0;
    } catch (error) {
      console.log('⚠️ Trafic de recherche payante non trouvé');
      return 0;
    }
  }

  /**
   * Extrait le CPC (Cost Per Click)
   * @returns {Promise<number>} - CPC
   */
  async extractCPC() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=CPC';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return null;
    } catch (error) {
      console.log('⚠️ CPC non trouvé');
      return null;
    }
  }

  /**
   * Extrait le trafic organique
   * @returns {Promise<number>} - Trafic organique
   */
  async extractOrganicTraffic() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=Organic';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return 0;
    } catch (error) {
      console.log('⚠️ Trafic organique non trouvé');
      return 0;
    }
  }

  /**
   * Extrait le trafic marqué
   * @returns {Promise<number>} - Trafic marqué
   */
  async extractBrandedTraffic() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=Branded';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return 0;
    } catch (error) {
      console.log('⚠️ Trafic marqué non trouvé');
      return 0;
    }
  }

  /**
   * Extrait le pourcentage de trafic marqué
   * @returns {Promise<number>} - Pourcentage de trafic marqué
   */
  async extractPercentBrandedTraffic() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=% Branded';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return null;
    } catch (error) {
      console.log('⚠️ Pourcentage de trafic marqué non trouvé');
      return null;
    }
  }

  /**
   * Récupère les informations de pagination
   * @returns {Promise<Object>} - Informations de pagination
   */
  async getPaginationInfo() {
    try {
      const paginationInfo = {};
      
      // Page actuelle
      const currentPageElement = await this.page.$('input[aria-label="Go to page"]');
      if (currentPageElement) {
        paginationInfo.currentPage = parseInt(await currentPageElement.getAttribute('value')) || 1;
      }
      
      // Total des pages
      const totalPagesElement = await this.page.$('span.text-sm.text-muted-foreground');
      if (totalPagesElement) {
        const totalText = await totalPagesElement.textContent();
        const match = totalText.match(/\/\s*(\d+)/);
        if (match) {
          paginationInfo.totalPages = parseInt(match[1]);
        }
      }
      
      // Bouton suivant
      const nextButton = await this.page.$('a[aria-label="Go to next page"]');
      paginationInfo.hasNextPage = nextButton !== null;
      
      // Bouton précédent
      const previousButton = await this.page.$('a[aria-label="Go to previous page"]');
      paginationInfo.hasPreviousPage = previousButton !== null;
      
      console.log(`📄 Pagination: Page ${paginationInfo.currentPage}/${paginationInfo.totalPages}`);
      return paginationInfo;
      
    } catch (error) {
      console.error('❌ Erreur pagination:', error.message);
      return { currentPage: 1, totalPages: 1, hasNextPage: false, hasPreviousPage: false };
    }
  }

  /**
   * Navigue vers la page suivante
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async goToNextPage() {
    try {
      const nextButton = await this.page.$('a[aria-label="Go to next page"]');
      if (nextButton) {
        await nextButton.click();
        await this.page.waitForLoadState('networkidle');
        await this.page.waitForTimeout(2000); // Attendre le chargement
        
        console.log('✅ Navigation vers la page suivante');
        return true;
      } else {
        console.log('⚠️ Pas de page suivante');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur navigation page suivante:', error.message);
      return false;
    }
  }

  /**
   * Navigue vers une page spécifique
   * @param {number} pageNumber - Numéro de page
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async goToPage(pageNumber) {
    try {
      // Trouver l'input de page
      const pageInput = await this.page.$('input[aria-label="Go to page"]');
      if (pageInput) {
        // Vider et remplir l'input
        await pageInput.fill('');
        await pageInput.fill(pageNumber.toString());
        
        // Appuyer sur Entrée
        await pageInput.press('Enter');
        
        // Attendre le chargement
        await this.page.waitForLoadState('networkidle');
        await this.page.waitForTimeout(2000);
        
        console.log(`✅ Navigation vers la page ${pageNumber}`);
        return true;
      } else {
        console.log('⚠️ Input de page non trouvé');
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur navigation page spécifique:', error.message);
      return false;
    }
  }

  /**
   * Scrape plusieurs pages
   * @param {number} maxPages - Nombre maximum de pages à scraper
   * @param {boolean} includeMarketData - Inclure les données de trafic par pays
   * @returns {Promise<Array>} - Toutes les données scrapées
   */
  async scrapeMultiplePages(maxPages = 30, includeMarketData = false) {
    console.log(`📋 Scraping de ${maxPages} pages...`);
    
    const allShopsData = [];
    
    // Naviguer vers la première page pour s'assurer qu'on est au bon endroit
    console.log('🔄 Navigation vers la page 1...');
    const navSuccess = await this.navigateToTrendingShops(1);
    if (!navSuccess) {
      console.log('❌ Échec navigation vers la page 1');
      return [];
    }
    
    for (let page = 1; page <= maxPages; page++) {
      console.log(`\n📄 Scraping page ${page}...`);
      
      // Extraire les données de la page actuelle
      const pageData = await this.extractAllShopsData(includeMarketData);
      
      // Ajouter les données avec l'information de page
      const pageDataWithPage = pageData.map(shop => ({
        ...shop,
        page: page
      }));
      
      allShopsData.push(...pageDataWithPage);
      
      console.log(`✅ Page ${page}: ${pageData.length} boutiques extraites`);
      
      // Vérifier s'il y a une page suivante
      // Naviguer vers la page suivante si ce n'est pas la dernière
      if (page < maxPages) {
        console.log(`🔄 Navigation vers la page ${page + 1}...`);
        const nextPageSuccess = await this.navigateToNextPage();
        if (!nextPageSuccess) {
          console.log(`❌ Échec navigation vers la page ${page + 1}`);
          break;
        }
        
        // Attendre un peu entre les pages
        await this.page.waitForTimeout(2000);
      }
    }
    
    console.log(`\n✅ Scraping terminé: ${allShopsData.length} boutiques au total`);
    return allShopsData;
  }

  /**
   * Formate les données pour CSV
   * @param {Array} shopsData - Données des boutiques
   * @returns {string} - Contenu CSV
   */
  formatToCSV(shopsData) {
    if (!shopsData || shopsData.length === 0) {
      return '';
    }
    
    // Définir les colonnes
    const headers = [
      'Page',
      'Shop Name',
      'Shop URL',
      'Creation Date',
      'Category',
      'Monthly Visits',
      'Monthly Revenue',
      'Live Ads',
      'Market US',
      'Market UK',
      'Market DE',
      'Market CA',
      'Market AU',
      'Market FR',
      'Timestamp'
    ];
    
    const csvRows = [headers.join(',')];
    
    for (const shop of shopsData) {
      const row = [
        shop.page || '',
        `"${(shop.shopName || '').replace(/"/g, '""')}"`,
        `"${(shop.shopUrl || '').replace(/"/g, '""')}"`,
        `"${(shop.creationDate || '').replace(/"/g, '""')}"`,
        `"${(shop.category || '').replace(/"/g, '""')}"`,
        `"${(shop.monthlyVisits || '').replace(/"/g, '""')}"`,
        `"${(shop.monthlyRevenue || '').replace(/"/g, '""')}"`,
        `"${(shop.liveAds || '').replace(/"/g, '""')}"`,
        shop.market_us || '',
        shop.market_uk || '',
        shop.market_de || '',
        shop.market_ca || '',
        shop.market_au || '',
        shop.market_fr || '',
        `"${(shop.timestamp || '').replace(/"/g, '""')}"`
      ];
      
      csvRows.push(row.join(','));
    }
    
    return csvRows.join('\n');
  }

  /**
   * Extrait les données de trafic par pays pour une boutique
   * @param {string} shopUrl - URL de la boutique
   * @param {Array} targets - Liste des pays cibles (défaut: ["us", "uk", "de", "ca", "au", "fr"])
   * @returns {Promise<Object>} - Données de trafic par pays
   */
  async extractMarketTrafficForShop(shopUrl, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🌍 Extraction trafic par pays pour: ${shopUrl}`);
    
    try {
      // Utiliser le pont Python pour les nouvelles fonctionnalités
      const marketData = await this.extractMarketTrafficForShopJS(shopUrl, targets);
      return marketData;
    } catch (error) {
      console.error(`❌ Erreur extraction trafic pour ${shopUrl}:`, error.message);
      return null;
    }
  }

  /**
   * Extrait les données de trafic par pays pour plusieurs boutiques
   * @param {Array} shopUrls - Liste des URLs de boutiques
   * @param {Array} targets - Liste des pays cibles
   * @returns {Promise<Array>} - Liste des données de trafic
   */
  async extractMarketTrafficForMultipleShops(shopUrls, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🌍 Extraction trafic par pays pour ${shopUrls.length} boutiques...`);
    
    try {
// Extraction markets en JS pur pour plusieurs boutiques      const results = [];      for (const shopUrl of shopUrls) {        const marketData = await this.extractMarketTrafficForShopJS(shopUrl, targets);        results.push(marketData);      }      return results;
    } catch (error) {
      console.error('❌ Erreur extraction trafic multiple:', error.message);
      return [];
    }
  }

  /**
   * Extrait les données complètes d'une boutique (données de base + trafic par pays)
   * @param {Object} shopData - Données de base de la boutique
   * @param {Array} targets - Liste des pays cibles
   * @returns {Promise<Object>} - Données complètes de la boutique
   */
  async extractCompleteShopData(shopData, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🔍 Extraction complète pour: ${shopData.shopName}`);
    
    try {
      // Extraire les données de trafic par pays
      const marketData = await this.extractMarketTrafficForShop(shopData.shopUrl, targets);
      
      // Combiner les données
      const completeData = {
        ...shopData,
        ...marketData
      };
      
      console.log(`✅ Données complètes extraites pour: ${shopData.shopName}`);
      return completeData;
      
    } catch (error) {
      console.error(`❌ Erreur extraction complète pour ${shopData.shopName}:`, error.message);
      
      // Retourner les données de base en cas d'erreur
      return {
        ...shopData,
        market_us: null,
        market_uk: null,
        market_de: null,
        market_ca: null,
        market_au: null,
        market_fr: null,
        error: error.message
      };
    }
  }

  /**
   * 🆕 MÉTHODE SUPPRIMÉE : Extraire l'ID API depuis la réponse RSC
   * Cette méthode a été supprimée car elle ne fonctionnait pas.
   * Voir la documentation API_REMOVAL.md pour plus de détails.
   * Remplacée par getGeoDataViaDOM() qui utilise le scraping DOM.
   */
  async extractApiIdFromRSC(shopId, workspace = 'w-al-yakoobs-workspace-x0Qg9st') {
    // Méthode supprimée - voir API_REMOVAL.md
    console.log(`⚠️ Extraction ID API désactivée pour: ${shopId} - Utilisation du scraping DOM`);
    return null;
  }

  /**
   * Extraction pixels via API TrendTrack avec cookies - MÉTHODE OPTIMISÉE
   */
  async extractPixelsForShopJS(shopId) {
    console.log(`📊 Extraction pixels (API) pour: ${shopId}`);
    const pixelData = { pixel_google: "non", pixel_facebook: "non" };
    
    try {
      // 🚀 NOUVELLE MÉTHODE : Requête directe à l'API TrendTrack avec cookies
      const result = await this.page.evaluate(async ({ shopId, workspace }) => {
        try {
          const response = await fetch(`https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`, {
            headers: {
              'RSC': '1', 
              'Accept': 'text/x-component',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, 
            credentials: 'include'
          });
          
          if (!response.ok) {
            return { error: `HTTP ${response.status}: ${response.statusText}` };
          }
          
          const text = await response.text();
          
          // Recherche des technologies dans le contenu de l'API
          const hasGoogleAnalytics = text.includes('Google Analytics') || text.includes('gtag') || text.includes('google-analytics');
          const hasFacebookPixel = text.includes('Facebook Pixel') || text.includes('fbq') || text.includes('fbevents');
          
          return { 
            hasGoogleAnalytics,
            hasFacebookPixel,
            responseLength: text.length
          };
          
        } catch (error) {
          return { error: error.message };
        }
      }, { shopId, workspace: 'w-al-yakoobs-workspace-x0Qg9st' });
      
      if (result.error) {
        console.error(`❌ Erreur API pour ${shopId}:`, result.error);
        return pixelData;
      }
      
      // Mettre à jour les résultats
      if (result.hasGoogleAnalytics) {
        pixelData.pixel_google = "oui";
        console.log("✅ Pixel Google détecté via API");
      }
      
      if (result.hasFacebookPixel) {
        pixelData.pixel_facebook = "oui";
        console.log("✅ Pixel Facebook détecté via API");
      }
      
      console.log(`✅ Pixels extraits pour ${shopId}: Google=${pixelData.pixel_google}, Facebook=${pixelData.pixel_facebook} (${result.responseLength} chars)`);
      return pixelData;
      
    } catch (error) {
      console.error(`❌ Erreur extraction pixels pour ${shopId}:`, error.message);
      return pixelData;
    }
  }

  /**
   * 🌍 ANALYSE GEO POUR PLUSIEURS SITES - MÉTHODE API OPTIMISÉE
   */
  async analyzeMultipleGeoData(siteIds, delayMs = 1000) {
    console.log(`🌍 Analyse géo pour ${siteIds.length} sites...`);
    const results = [];
    
    for (let i = 0; i < siteIds.length; i++) {
      const siteId = siteIds[i];
      
      try {
        console.log(`🔍 Analyse géo ${i+1}/${siteIds.length}: ${siteId}`);
        
        const geoData = { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0 };
        
        results.push({
          siteId,
          ...geoData,
          timestamp: new Date().toISOString()
        });
        
        // ⏱️ Pause entre requêtes
        if (i < siteIds.length - 1) {
          await new Promise(resolve => setTimeout(resolve, delayMs));
        }
        
      } catch (error) {
        console.error(`❌ Erreur pour ${siteId}:`, error.message);
        results.push({
          siteId,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    return results;
  }

  /**
   * 🌍 NOUVELLE MÉTHODE : Extraction des données géographiques via scraping DOM
   * Utilise le scraping DOM pour extraire les données de trafic par pays depuis la page de détail TrendTrack
   * @returns {Promise<Object>} - Données de trafic par pays
   */
  async extractGeoDataViaDOM() {
    console.log('🌍 Extraction des données géographiques via scraping DOM...');
    
    try {
      // ⚡ STRATÉGIE ASYNCHRONE REACT - Attendre le chargement complet
      console.log('⚡ Attente du chargement asynchrone React...');
      
      // 1. Attendre que la page soit stable
      await this.page.waitForTimeout(3000);
      
      // 2. Attendre les requêtes réseau
      await this.page.waitForLoadState('networkidle');
      
      // 3. Attendre que React soit prêt
      try {
        await this.page.waitForFunction(() => {
          return document.readyState === 'complete' && 
                 (window.React || window.__REACT_DEVTOOLS_GLOBAL_HOOK__ || 
                  document.querySelector('[data-reactroot], #root, #__next'));
        }, { timeout: 10000 });
        console.log('✅ React prêt');
      } catch (error) {
        console.log('⚠️ React non détecté, continuation...');
      }
      
      // 🔄 STRATÉGIE DE RETRY avec différents sélecteurs
      let geoData = null;
      const selectors = [
        '.flex.gap-2.w-full.items-center',
        '[class*="flex"][class*="gap"][class*="items-center"]',
        'img[alt*="US"], img[alt*="GB"], img[alt*="CA"]',
        '[class*="geo"], [class*="country"], [class*="market"]',
        'div[class*="traffic"], div[class*="visits"]'
      ];
      
      for (let attempt = 1; attempt <= 3; attempt++) {
        console.log(`🔄 Tentative ${attempt}/3 d'extraction géo...`);
        
        // Attendre un peu plus entre les tentatives
        if (attempt > 1) {
          await this.page.waitForTimeout(2000 * attempt);
        }
        
        geoData = await this.page.evaluate((selectors) => {
        const results = {
          market_us: 0,
          market_uk: 0,
          market_de: 0,
          market_ca: 0,
          market_au: 0,
          market_fr: 0,
          countries: []
        };
        
          // Tester chaque sélecteur
          for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            console.log(`[PAGE] Sélecteur "${selector}": ${elements.length} éléments`);
            
            if (elements.length > 0) {
              // Traiter les éléments trouvés
              elements.forEach((el, index) => {
                try {
                  const img = el.querySelector('img[alt]');
                  const country = img?.getAttribute('alt');
                  
                  if (country) {
                    // Chercher le pourcentage avec différents sélecteurs
                    const percentageSelectors = [
                      '.flex.justify-between p:last-child',
                      '.flex.items-center.gap-1 p:last-child',
                      'p:last-child',
                      'div:last-child p',
                      'span:last-child'
                    ];
                    
                    let percentage = null;
                    for (const pctSelector of percentageSelectors) {
                      const pctEl = el.querySelector(pctSelector);
                      if (pctEl && pctEl.textContent.includes('%')) {
                        percentage = pctEl.textContent;
                        break;
                      }
                    }
                    
                    if (percentage) {
                      const countryCode = country.toLowerCase().trim();
                      const percentageText = percentage.replace('%', '').trim();
                      const percentageValue = parseFloat(percentageText) / 100;
                      
                      console.log(`[PAGE] Pays trouvé: ${countryCode} → ${percentageText}%`);
                      
                      switch(countryCode) {
                        case 'us': case 'united states': results.market_us = percentageValue; break;
                        case 'gb': case 'uk': case 'united kingdom': results.market_uk = percentageValue; break;
                        case 'de': case 'germany': case 'deutschland': results.market_de = percentageValue; break;
                        case 'ca': case 'canada': results.market_ca = percentageValue; break;
                        case 'au': case 'australia': results.market_au = percentageValue; break;
                        case 'fr': case 'france': results.market_fr = percentageValue; break;
                      }
                      
                      results.countries.push({
                        countryCode: countryCode.toUpperCase(),
                        countryName: country,
                        visitsShare: percentageValue,
                        visitsSharePercent: parseFloat(percentageText)
                      });
                    }
                  }
                } catch (e) {
                  console.log(`[PAGE] Erreur parsing élément ${index}:`, e.message);
                }
              });
              
              // Si on a trouvé des pays, on peut arrêter
              if (results.countries.length > 0) {
                console.log(`[PAGE] ${results.countries.length} pays extraits avec le sélecteur "${selector}"`);
                return results;
              }
            }
          }
          
          return results;
        }, selectors);
        
        // Si on a trouvé des données, arrêter les tentatives
        if (geoData.countries.length > 0) {
          console.log(`✅ Données géographiques extraites: ${geoData.countries.length} pays`);
          break;
        }
        
        console.log(`⚠️ Tentative ${attempt} échouée, retry...`);
      }
      
      // Afficher les résultats
      if (geoData.countries.length > 0) {
        console.log(`✅ Données géographiques extraites: ${geoData.countries.length} pays`);
        geoData.countries.forEach(country => {
          console.log(`   ${country.countryName}: ${country.visitsSharePercent}%`);
        });
      } else {
        console.log('⚠️ Aucune donnée géographique trouvée via scraping DOM');
      }
      
      return geoData;
      
    } catch (error) {
      console.error('❌ Erreur extraction géo DOM:', error.message);
      return { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0, countries: [] };
    }
  }
  async checkSession() {
    try {
      const currentUrl = this.page.url();
      if (currentUrl.includes('/login')) {
        console.log('❌ Session expirée - Redirection vers login détectée');
        return false;
      }
      
      // Vérifier qu'on est sur une page TrendTrack valide
      if (!currentUrl.includes('trendtrack.io')) {
        console.log('❌ Session invalide - Pas sur TrendTrack');
        return false;
      }
      
      return true;
    } catch (error) {
      console.log(`❌ Erreur vérification session: ${error.message}`);
      return false;
    }
  }

  async ensureAuthenticated() {
    if (!(await this.checkSession())) {
      console.log('🔄 Session expirée, reconnexion nécessaire...');
      // Ici on pourrait implémenter une reconnexion automatique
      // Pour l'instant, on retourne false pour arrêter l'extraction
      return false;
    }
    return true;
  }

  async extractMarketTrafficForShopJS(shopId, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🌍 Extraction trafic par pays (JS) pour: ${shopId}`);
    const extractedMarkets = { ...targets.reduce((acc, t) => ({ ...acc, [`market_${t}`]: null }), {}) };

    try {
      // Vérifier la session avant de continuer
      if (!(await this.ensureAuthenticated())) {
        console.log('❌ Session non valide, arrêt de l\'extraction trafic par pays');
        return extractedMarkets;
      }
      const detailUrl = `https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${shopId}`;
      await this.page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await this.page.waitForTimeout(2000);

      // Attendre le bloc "Trafic par pays" (logique exacte du script Python)
      try {
        await this.page.waitForSelector('h3:has-text("Trafic par pays")', { state: "visible", timeout: 10000 });
        console.log('✅ Section "Trafic par pays" trouvée');
      } catch (error) {
        console.log('⚠️ Section "Trafic par pays" non trouvée sur cette page');
        return extractedMarkets;
      }

      // Localiser la carte contenant les données (logique exacte du script Python)
      const card = this.page.locator('h3:has-text("Trafic par pays")').locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();
      const rows = card.locator("div.flex.gap-2.w-full.items-center");
      const count = await rows.count();

      console.log(`📊 ${count} lignes de pays trouvées`);

      const observedMarkets = {};

      for (let i = 0; i < count; i++) {
        const row = rows.nth(i);
        
        // Code pays via alt du drapeau ou fallback sur le premier <p> gauche
        let code = await row.locator("img[alt]").first().getAttribute("alt");
        if (!code) {
          code = await row.locator("div.flex.justify-between > p").first().textContent();
        }

        code = this.canonicalizeCountryCode(code);
        if (!code) continue;

        // Valeur (le premier <p> avant le %)
        const valueText = await row.locator("div.flex.justify-between div.items-center > p").first().textContent();
        const value = this.parseTrafficValue(valueText);

        // On enregistre uniquement si une valeur numérique est présente
        if (value > 0) {
          observedMarkets[code] = value;
          console.log(`  📍 ${code.toUpperCase()}: ${value.toLocaleString()}`);
        }
      }

      if (Object.keys(observedMarkets).length > 0) {
        // Au moins une valeur trouvée: on met 0 pour les cibles manquantes
        for (const target_code of targets) {
          extractedMarkets[`market_${target_code}`] = observedMarkets[target_code] || 0;
        }
        console.log(`✅ Trafic par pays extrait: ${Object.keys(observedMarkets).length} pays trouvés`);
      } else {
        // Aucune donnée trouvée: on ne force pas à 0 (null pour signaler "pas de data")
        for (const target_code of targets) {
          extractedMarkets[`market_${target_code}`] = null;
        }
        console.log('⚠️ Aucune donnée de trafic par pays trouvée');
      }

      console.log(`✅ Trafic par pays extrait pour ${shopId}:`, extractedMarkets);
      return extractedMarkets;

    } catch (error) {
      console.error(`❌ Erreur lors de l'extraction du trafic par pays pour ${shopId}:`, error.message);
      return extractedMarkets;
    }
  }

  canonicalizeCountryCode(codeElement) {
    if (!codeElement) return null;
    const code = codeElement.toLowerCase();
    if (code === "us" || code === "united states") return "us";
    if (code === "uk" || code === "gb" || code === "united kingdom") return "uk";
    if (code === "de" || code === "germany") return "de";
    if (code === "ca" || code === "canada") return "ca";
    if (code === "au" || code === "australia") return "au";
    if (code === "fr" || code === "france") return "fr";
    return null;
  }

  parseTrafficValue(valueText) {
    if (!valueText) return null;
    const cleanText = valueText.replace(/[^\d.]/g, '');
    const value = parseFloat(cleanText);
    return isNaN(value) ? null : value;
  }

  /**
   * Pause pour éviter la surcharge
   * @param {number} ms - Millisecondes à attendre
   * @returns {Promise} - Promise qui se résout après la pause
   */
  /**
   * Navigue vers la page suivante en utilisant la pagination native
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async navigateToNextPage() {
    console.log('🔄 Navigation vers la page suivante...');
    
    try {
      // Attendre que le bouton "next" soit disponible
      await this.page.waitForSelector('a[aria-label="Go to next page"]', { timeout: 10000 });
      
      // Vérifier si le bouton est désactivé (pas de page suivante)
      const nextButton = await this.page.$('a[aria-label="Go to next page"]');
      const isDisabled = await nextButton.getAttribute('aria-disabled');
      
      if (isDisabled === 'true') {
        console.log('⚠️ Pas de page suivante disponible');
        return false;
      }
      
      // Cliquer sur le bouton "next"
      await nextButton.click();
      
      // Attendre le chargement
      await this.page.waitForLoadState('networkidle');
      await this.page.waitForTimeout(2000);
      
      // Vérifier qu'on est bien sur une nouvelle page
      const tableRows = await this.page.locator('table tbody tr').count();
      if (tableRows === 0) {
        console.log('⚠️ Aucune donnée trouvée sur la nouvelle page');
        return false;
      }
      
      console.log('✅ Navigation vers la page suivante réussie');
      return true;
    } catch (error) {
      console.error('❌ Erreur navigation page suivante:', error.message);
      return false;
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }


  /**
   * 🗑️ MÉTHODE SUPPRIMÉE : extractGeoDataViaAPI
   * Cette méthode a été supprimée car l'API TrendTrack ne fonctionnait pas.
   * Remplacée par getGeoDataViaDOM() qui utilise le scraping DOM.
   * Voir la documentation API_REMOVAL.md pour plus de détails.
   */

  /**
   * Extrait l'ID API depuis la réponse RSC
   * @param {string} shopId - ID de la boutique
   * @param {string} workspace - Workspace TrendTrack
   * @returns {Promise<string|null>} - ID API ou null
   */
  async extractApiIdFromRSC(shopId, workspace) {
    try {
      const response = await fetch(
        `https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${shopId}`,
        {
          headers: {
            'RSC': '1',
            'Accept': 'text/x-component'
          },
          credentials: 'include'
        }
      );

      const text = await response.text();
      
      // 🔍 PATTERNS À CHERCHER pour l'ID API
      const patterns = [
        /"websiteId":"([a-f0-9-]{36})"/,
        /"siteId":"([a-f0-9-]{36})"/,
        /"website["\.]id["\:]"([a-f0-9-]{36})"/,
        /website[\/:]([a-f0-9-]{36})/,
        /"id":"([a-f0-9-]{36})".*geography/,
        /\/api\/websites\/([a-f0-9-]{36})/
      ];

      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match && match[1] !== shopId) { // Différent de l'ID de la liste
          console.log(`✅ ID API trouvé avec pattern: ${pattern.source}`);
          return match[1];
        }
      }

      // 🔍 RECHERCHE PLUS LARGE - tous les UUIDs dans la réponse
      const allUuids = text.match(/[a-f0-9-]{36}/g) || [];
      const uniqueUuids = [...new Set(allUuids)].filter(id => id !== shopId);
      
      if (uniqueUuids.length > 0) {
        console.log(`🎯 UUIDs candidats trouvés:`, uniqueUuids);
        
        // Tester chaque UUID avec l'API géo
        for (const candidateId of uniqueUuids) {
          try {
            const testResponse = await fetch(
              `https://app.trendtrack.io/api/websites/${candidateId}`,
              {
                headers: {
                  "Accept": "*/*",
                  "Sec-Fetch-Dest": "empty",
                  "Sec-Fetch-Mode": "cors", 
                  "Sec-Fetch-Site": "same-origin"
                },
                credentials: 'include'
              }
            );
            
            if (testResponse.ok) {
              const testData = await testResponse.json();
              if (testData.website?.geography) {
                console.log(`✅ ID API validé: ${candidateId}`);
                return candidateId;
              }
            }
          } catch (e) {
            // Continue avec le suivant
          }
        }
      }

      return null;
    } catch (error) {
      console.error('❌ Erreur extraction ID API:', error);
      return null;
    }
  }


  /**
   * Extrait live_ads_7d depuis la page de détail (Phase 3) - Cellule 5
   * @returns {Promise<number>} - Nombre de live ads 7d
   */
  async extractLiveAds7d() {
    try {
      console.log('🔍 Extraction live_ads_7d (Phase 3 - .flex.items-center.gap-2)...');
      
      const metrics = await this.page.evaluate(() => {
        const results = {};
        
        // Chercher tous les éléments contenant les périodes et pourcentages
        const periodElements = document.querySelectorAll('.flex.items-center.gap-2');
        
        periodElements.forEach(element => {
          const text = element.textContent;
          
          // Vérifier si c'est un élément de période (contient "7d", "30d", etc.)
          if (text.includes('d') && text.includes('%')) {
            
            // Extraire la période (7d, 30d)
            const periodMatch = text.match(/(\d+d)/);
            
            // Extraire le pourcentage avec son signe
            const percentageMatch = text.match(/([+-]?\d+)%/);
            
            if (periodMatch && percentageMatch) {
              const period = periodMatch[1]; // "7d" ou "30d"
              let value = parseInt(percentageMatch[1]); // -22 ou 2
              
              // Appliquer les transformations
              if (period === '7d') {
                // Pour 7d: -22% → 22 (enlever le signe négatif)
                value = Math.abs(value);
              } else if (period === '30d') {
                // Pour 30d: 2% → 2 (garder tel quel)
                value = value;
              }
              
              results[period] = value;
              
              console.log(`${period}: ${percentageMatch[1]}% → transformé en: ${value}`);
            }
          }
        });
        
        return results;
      });

      const value = metrics['7d'] || 0;
      console.log(`📊 Live ads 7d extrait (Phase 3): ${value}`);
      return value;
      
    } catch (error) {
      console.log(`❌ Erreur extraction live_ads_7d (Phase 3): ${error.message}`);
      return 0;
    }
  }

  /**
   * Extrait live_ads_30d depuis la page de détail (Phase 3) - Cellule 6
   * Note: La cellule 6 a une structure HTML différente (pas d'élément <p>)
   * @returns {Promise<number>} - Nombre de live ads 30d
   */
  async extractLiveAds30d() {
    try {
      console.log('🔍 Extraction live_ads_30d (Phase 3 - .flex.items-center.gap-2)...');
      
      const metrics = await this.page.evaluate(() => {
        const results = {};
        
        // Chercher tous les éléments contenant les périodes et pourcentages
        const periodElements = document.querySelectorAll('.flex.items-center.gap-2');
        
        periodElements.forEach(element => {
          const text = element.textContent;
          
          // Vérifier si c'est un élément de période (contient "7d", "30d", etc.)
          if (text.includes('d') && text.includes('%')) {
            
            // Extraire la période (7d, 30d)
            const periodMatch = text.match(/(\d+d)/);
            
            // Extraire le pourcentage avec son signe
            const percentageMatch = text.match(/([+-]?\d+)%/);
            
            if (periodMatch && percentageMatch) {
              const period = periodMatch[1]; // "7d" ou "30d"
              let value = parseInt(percentageMatch[1]); // -22 ou 2
              
              // Appliquer les transformations
              if (period === '7d') {
                // Pour 7d: -22% → 22 (enlever le signe négatif)
                value = Math.abs(value);
              } else if (period === '30d') {
                // Pour 30d: 2% → 2 (garder tel quel)
                value = value;
              }
              
              results[period] = value;
              
              console.log(`${period}: ${percentageMatch[1]}% → transformé en: ${value}`);
            }
          }
        });
        
        return results;
      });

      const value = metrics['30d'] || 0;
      console.log(`📊 Live ads 30d extrait (Phase 3): ${value}`);
      return value;

    } catch (error) {
      console.log(`❌ Erreur extraction live_ads_30d (Phase 3): ${error.message}`);
      return 0;
    }
  }
} 