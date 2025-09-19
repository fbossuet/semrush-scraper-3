/**
 * Extracteur spécialisé pour TrendTrack
 * Extrait les données des boutiques tendances avec pagination
 */

import { BaseExtractor } from './base-extractor.js';
import { MarketTrafficExtractor } from './market-traffic-extractor.js';
import { MarketTrafficPythonBridge } from './market-traffic-python-bridge.js';
import { AdditionalMetricsPythonBridge } from './additional-metrics-python-bridge.js';

export class TrendTrackExtractor extends BaseExtractor {
  constructor(page, errorHandler) {
    super(page, errorHandler);
    
    // Initialiser l'extracteur de trafic par pays (JavaScript)
    this.marketTrafficExtractor = new MarketTrafficExtractor(page);
    
    // Initialiser le pont Python pour les nouvelles fonctionnalités
    this.marketTrafficPythonBridge = new MarketTrafficPythonBridge();
    this.additionalMetricsBridge = new AdditionalMetricsPythonBridge();
    
    // Sélecteurs spécifiques à TrendTrack basés sur l'analyse HTML
    this.selectors = {
      // Informations de la boutique
      shopName: {
        selector: 'td p.text-sm.font-semibold',
        multiple: false
      },
      shopUrl: {
        selector: 'td a[href*="http"]',
        attribute: 'href',
        multiple: false
      },
      shopDomain: {
        selector: 'td a[href*="http"]',
        multiple: false
      },
      
      // Catégorie
      category: {
        selector: 'td div.h-full.w-full.flex.items-center.justify-center.text-center.flex-col.font-semibold div',
        multiple: false
      },
      
      // Visites mensuelles
      monthlyVisits: {
        selector: 'td p.font-bold',
        multiple: false
      },
      
      // Revenus mensuels
      monthlyRevenue: {
        selector: 'td div.h-full.w-full.flex.flex-col.items-center.justify-center p.font-bold',
        multiple: false
      },
      
      // Nombre d'ads live
      liveAds: {
        selector: 'td div.flex.items-center.justify-center.font-semibold p',
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
        timeout: 30000
      });
      
      // Attendre que le formulaire soit chargé
      await this.page.waitForSelector('input[type="email"][name="email"]', { timeout: 30000 });
      
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
        await this.page.waitForSelector('a[href*="trending-shops"]', { timeout: 30000 });
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
          timeout: 30000
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
        timeout: 30000
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
      await this.page.waitForSelector('th div.flex.items-center.gap-1', { timeout: 30000 });
      
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
   * Extrait les données d'une ligne de boutique
   * @param {Object} row - Élément de ligne
   * @param {boolean} includeMarketData - Inclure les données de trafic par pays
   * @returns {Promise<Object>} - Données de la boutique
   */
  async extractShopData(row, includeMarketData = false) {
    try {
      const shopData = {};
      const cells = await row.locator('td').all();
      if (cells.length < 8) {
        return null;
      }
      const shopInfoHtml = await cells[1].innerHTML();
      const shopNameMatch = shopInfoHtml.match(/<p class=\"text-sm font-semibold\">([^<]+)<\/p>/);
      shopData.shopName = shopNameMatch ? shopNameMatch[1].trim() : '';
      const shopUrlMatch = shopInfoHtml.match(/href=["']([^"']+)["']/);
      shopData.shopUrl = shopUrlMatch ? shopUrlMatch[1] : '';
      const dateMatch = shopInfoHtml.match(/(\d{2}\/\d{2}\/\d{4})/);
      shopData.creationDate = dateMatch ? dateMatch[1] : '';
      shopData.category = (await cells[3].textContent()).trim();
      shopData.monthlyVisits = (await cells[4].textContent()).trim();
      shopData.monthlyRevenue = (await cells[5].textContent()).trim();
      // Live Ads (cellule 7)
      if (shopData.shopName.toLowerCase().includes('beyondalpha')) {
        const liveAdsHtml = await cells[7].innerHTML();
        console.log('=== HTML cellule Live Ads pour Beyondalpha ===');
        console.log(liveAdsHtml);
        // Afficher toutes les valeurs <p> numériques
        const liveAdsPs = await cells[7].locator('p').all();
        for (const p of liveAdsPs) {
          const txt = (await p.textContent()).trim();
          if (/^\d+$/.test(txt)) {
            console.log('Valeur <p> numérique trouvée :', txt);
          }
        }
        console.log('============================================');
      }
      const liveAdsDiv = await cells[7].locator('div.flex.items-center.justify-center.font-semibold');
      const liveAdsP = await liveAdsDiv.locator('p').first();
      shopData.liveAds = liveAdsP ? (await liveAdsP.textContent()).trim() : '';

      // 🆕 Extraction directe du nombre de produits (colonne 2)
      try {
        const productsCell = cells[2]; // 3ème colonne (index 2)
        const productsP = productsCell.locator('p:has(> span:has-text("products"))');
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

      // Ajouter les données de trafic par pays si demandé
      if (includeMarketData && shopData.shopUrl) {
        try {
          console.log(`🌍 Extraction trafic par pays pour: ${shopData.shopName}`);
          const marketData = await this.extractMarketTrafficForShop(shopData.shopUrl);
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
          const additionalMetrics = await this.additionalMetricsBridge.extractAdditionalMetrics(shopData.shopUrl);
          if (additionalMetrics) {
            shopData.totalProducts = additionalMetrics.total_products;
            shopData.pixelGoogle = additionalMetrics.pixel_google;
            shopData.pixelFacebook = additionalMetrics.pixel_facebook;
            shopData.aov = additionalMetrics.aov;
            console.log(`✅ Métriques supplémentaires extraites pour ${shopData.shopName}`);
          }
          
        } catch (error) {
          console.error(`⚠️ Erreur extraction métriques supplémentaires pour ${shopData.shopName}:`, error.message);
          // Ajouter des valeurs null pour les champs en cas d'erreur
          shopData.totalProducts = null;
          shopData.pixelGoogle = null;
          shopData.pixelFacebook = null;
          shopData.aov = null;
        }
      }

      return shopData;
    } catch (error) {
      console.error('❌ Erreur extraction données boutique:', error.message);
      return null;
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
      
      await this.page.waitForSelector('tbody tr', { timeout: 30000 });
      
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
    if (maxPages > 1) {
      console.log('🔄 Navigation vers la page 1...');
      const navSuccess = await this.navigateToTrendingShops(1);
      if (!navSuccess) {
        console.log('❌ Échec navigation vers la page 1');
        return [];
      }
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
      if (page < maxPages) {
        const paginationInfo = await this.getPaginationInfo();
        
        if (paginationInfo.hasNextPage && page < paginationInfo.totalPages) {
          // Aller à la page suivante
          const success = await this.goToNextPage();
          if (!success) {
            console.log('⚠️ Impossible d\'aller à la page suivante, arrêt du scraping');
            break;
          }
          
          // Attendre un peu entre les pages (plus longtemps si on inclut les données de trafic)
          await this.sleep(includeMarketData ? 5000 : 2000);
        } else {
          console.log('⚠️ Plus de pages disponibles');
          break;
        }
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
      const marketData = await this.marketTrafficPythonBridge.extractMarketTraffic(shopUrl, targets);
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
      const marketData = await this.marketTrafficExtractor.extractMarketTrafficForMultipleShops(shopUrls, targets);
      return marketData;
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
   * Pause pour éviter la surcharge
   * @param {number} ms - Millisecondes à attendre
   * @returns {Promise} - Promise qui se résout après la pause
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
} 