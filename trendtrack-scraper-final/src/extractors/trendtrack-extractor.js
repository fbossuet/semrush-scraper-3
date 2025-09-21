/**
 * Extracteur spécialisé pour TrendTrack
 * Extrait les données des boutiques tendances avec pagination
 */

import { BaseExtractor } from './base-extractor.js';
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
      
      // Nom de la boutique
      try {
        const nameElement = await cells[0].locator('p.text-sm.font-semibold').first();
        if (await nameElement.count() > 0) {
          shopData.shop_name = (await nameElement.textContent())?.trim();
        }
      } catch (error) {
        console.log('⚠️ Nom de boutique non trouvé');
      }

      // URL de la boutique
      try {
        const urlElement = await cells[0].locator('a[href*="http"]').first();
        if (await urlElement.count() > 0) {
          shopData.shop_url = await urlElement.getAttribute('href');
        }
      } catch (error) {
        console.log('⚠️ URL de boutique non trouvée');
      }

      // Catégorie
      try {
        const categoryElement = await cells[1].locator('div').first();
        if (await categoryElement.count() > 0) {
          shopData.category = (await categoryElement.textContent())?.trim();
        }
      } catch (error) {
        console.log('⚠️ Catégorie non trouvée');
      }

      // Visites mensuelles
      try {
        const visitsElement = await cells[2].locator('p.font-bold').first();
        if (await visitsElement.count() > 0) {
          shopData.monthly_visits = this.parseNumber(await visitsElement.textContent());
        }
      } catch (error) {
        console.log('⚠️ Visites mensuelles non trouvées');
      }

      // Revenus mensuels
      try {
        const revenueElement = await cells[3].locator('p.font-bold').first();
        if (await revenueElement.count() > 0) {
          shopData.monthly_revenue = this.parseNumber(await revenueElement.textContent());
        }
      } catch (error) {
        console.log('⚠️ Revenus mensuels non trouvés');
      }

      // Nombre de produits
      try {
        const productsElement = await cells[4].locator('p.font-bold').first();
        if (await productsElement.count() > 0) {
          shopData.total_products = this.parseNumber(await productsElement.textContent());
        }
      } catch (error) {
        console.log('⚠️ Nombre de produits non trouvé');
      }

      // Live ads 7d
      try {
        const liveAds7dElement = await cells[5].locator('p').first();
        if (await liveAds7dElement.count() > 0) {
          shopData.live_ads_7d = this.parseNumber(await liveAds7dElement.textContent());
        }
      } catch (error) {
        console.log('⚠️ Live ads 7d non trouvés');
      }

      // Live ads 30d
      try {
        const liveAds30dElement = await cells[6].locator('p').first();
        if (await liveAds30dElement.count() > 0) {
          shopData.live_ads_30d = this.parseNumber(await liveAds30dElement.textContent());
        }
      } catch (error) {
        console.log('⚠️ Live ads 30d non trouvés');
      }

      // Ajouter les métadonnées
      shopData.scraping_status = 'table_extracted';
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
        shopData.monthlyVisits = (await cells[4].textContent()).trim();
        shopData.monthlyRevenue = (await cells[5].textContent()).trim();
      } catch (error) {
        console.error(`⚠️ Erreur extraction métriques de base: ${error.message}`);
        shopData.category = '';
        shopData.monthlyVisits = '';
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
   * Navigue vers la page de détail d'une boutique
   * @param {string} shopUrl - URL de la boutique
   * @returns {Promise<boolean>} - Succès de la navigation
   */
  async navigateToShopDetail(shopUrl) {
    console.log(`🔍 Navigation vers la page de détail: ${shopUrl}`);
    
    try {
      // Construire l'URL de la page de détail TrendTrack
      // Format: https://app.trendtrack.io/en/workspace/.../shop-detail?url=SHOP_URL
      const baseUrl = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st';
      const detailUrl = `${baseUrl}/shop-detail?url=${encodeURIComponent(shopUrl)}`;
      
      console.log(`🔍 URL de détail TrendTrack: ${detailUrl}`);
      
      // Navigation vers la page de détail TrendTrack
      await this.page.goto(detailUrl, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      // Attendre que la page se charge
      await this.page.waitForTimeout(2000);
      
      // Vérifier qu'on est bien sur la page de la boutique
      const currentUrl = this.page.url();
      if (currentUrl.includes(shopUrl.replace('https://', '').replace('http://', ''))) {
        console.log('✅ Navigation vers page de détail réussie');
        return true;
      } else {
        console.log('❌ Navigation échouée - URL incorrecte');
        return false;
      }
      
    } catch (error) {
      console.error(`❌ Erreur navigation détail: ${error.message}`);
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
      
      // 🚀 NOUVELLE MÉTHODE : Extraction des données de marché via API TrendTrack
      console.log('🌍 Extraction des données de marché via API TrendTrack...');
      const marketData = await this.getGeoDataViaAPI(shopId || 'current_shop'); // Utiliser l'ID de la boutique
      
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
        
        // Année de fondation
        year_founded: await this.extractYearFounded(),
        
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
        
        scraping_status: 'details_extracted',
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
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=Founded';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return null;
    } catch (error) {
      console.log('⚠️ Année de fondation non trouvée');
      return null;
    }
  }

  /**
   * Extrait l'AOV (Average Order Value)
   * @returns {Promise<number>} - AOV
   */
  async extractAOV() {
    try {
      // Implémentation basique - à adapter selon la structure de la page
      const selector = 'text=AOV';
      const element = await this.page.locator(selector).first();
      if (await element.count() > 0) {
        const value = await element.textContent();
        return this.parseNumber(value);
      }
      return null;
    } catch (error) {
      console.log('⚠️ AOV non trouvé');
      return null;
    }
  }

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
        
        const geoData = await this.getGeoDataViaAPI(siteId);
        
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
   * 📊 RÉCUPÉRATION DES DONNÉES GÉO VIA API TRENDTRACK AVEC COOKIES AUTOMATIQUES
   */
  async getGeoDataViaAPI(siteId) {
    console.log(`🌍 Récupération données géo (API) pour: ${siteId}`);
    
    try {
      // Utiliser l'ID passé en paramètre directement
      let actualSiteId = siteId;
      if (siteId === 'current_shop') {
        console.log('⚠️ ID générique utilisé, les données peuvent être incorrectes');
      } else {
        console.log(`🔍 Utilisation de l'ID TrendTrack: ${actualSiteId}`);
      }
      
      // 🍪 Utilisation des cookies automatiques depuis le navigateur
      const result = await this.page.evaluate(async ({ siteId, workspace }) => {
        try {
          // Récupération automatique des cookies du navigateur
          const cookies = await document.cookie;
          const cookieString = cookies;
          
          const response = await fetch(`https://app.trendtrack.io/en/workspace/${workspace}/trending-shops/${siteId}`, {
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
          
          // 🎯 Extraction des données géographiques depuis la réponse RSC
          const marketData = {
            market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0, 
            countries: []
          };
          
          // Rechercher les données géographiques dans la réponse RSC
          // Pattern pour les données géographiques : "visitsShare":0.7463570938382258,"countryUrlCode":"united-states","countryAlpha2Code":"US"
          const geoPattern = /"visitsShare":([0-9.]+),"countryUrlCode":"[^"]+","countryAlpha2Code":"([^"]+)"/g;
          let match;
          
          while ((match = geoPattern.exec(text)) !== null) {
            const visitsShare = parseFloat(match[1]);
            const countryCode = match[2].toLowerCase();
            
            marketData.countries.push({
              countryCode: countryCode,
              visitsShare: visitsShare,
              visitsSharePercent: Math.round(visitsShare * 100 * 100) / 100,
              countryName: match[0].match(/"countryUrlCode":"([^"]+)"/)[1]
            });
            
            switch (countryCode) {
              case 'us': marketData.market_us = visitsShare; break;
              case 'gb': marketData.market_uk = visitsShare; break;
              case 'de': marketData.market_de = visitsShare; break;
              case 'ca': marketData.market_ca = visitsShare; break;
              case 'au': marketData.market_au = visitsShare; break;
              case 'fr': marketData.market_fr = visitsShare; break;
            }
          }
          
          return { 
            ...marketData,
            countriesFound: marketData.countries.length,
            responseLength: text.length,
            cookieUsed: cookieString ? 'Oui' : 'Non'
          };
          
    } catch (error) {
          return { error: error.message };
        }
      }, { siteId: actualSiteId, workspace: 'w-al-yakoobs-workspace-x0Qg9st' });
      
      if (result.error) {
        console.error(`❌ Erreur API géo pour ${siteId}:`, result.error);
        return { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0 };
      }
      
      console.log(`✅ Données géo extraites pour ${siteId}: ${result.countriesFound} pays (${result.responseLength} chars, cookies: ${result.cookieUsed})`);
      return result;
      
    } catch (error) {
      console.error(`❌ Erreur extraction géo pour ${siteId}:`, error.message);
      return { market_us: 0, market_uk: 0, market_de: 0, market_ca: 0, market_au: 0, market_fr: 0 };
    }
  }

  /**
   * 📊 FORMATAGE SIMPLE POUR EXPORT
   */
  formatGeoDataForExport(results) {
    const formatted = [];
    
    results.forEach(result => {
      if (!result.error && result.countries) {
        result.countries.forEach(country => {
          formatted.push({
            site_id: result.siteId,
            country_code: country.countryCode,
            visits_share: country.visitsShare,
            visits_share_percent: country.visitsSharePercent,
            country_name: country.countryName
          });
        });
      }
    });
    
    return formatted;
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
} 