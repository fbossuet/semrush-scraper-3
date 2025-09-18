/**
 * Extracteur spécialisé pour TrendTrack
 * Extrait les données des boutiques tendances avec pagination
 */

import { BaseExtractor } from './base-extractor.js';

export class TrendTrackExtractor extends BaseExtractor {
  constructor(page, errorHandler) {
    super(page, errorHandler);
    
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
      await this.page.waitForSelector('input[type="email"][name="email"]', { timeout: 10000 });
      
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
        await this.page.waitForSelector('a[href*="trending-shops"]', { timeout: 10000 });
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
      // URL complète avec tous les paramètres (corrigée)
      // Ancienne URL (commentée)
      // let url = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops?minTraffic=10000&creationCountry=US&include=true&languages=en&currencies=USD&orderBy=liveAds&growth=1m=100=greater&minGrowth=100';
      
                  // Nouvelle URL avec paramètres mis à jour
            let url = 'https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops?include=true&tab=websites&minTraffic=500000&minAds=120&languages=en&currencies=USD&creationCountry=US=include&maxAds=1000&minDate=2020-06-01&maxDate=2025-08-19&orderBy=liveAds';
      
      // Ajouter le paramètre de page si nécessaire
      if (page > 1) {
        url += `&page=${page}`;
      }
      
      console.log(`🌐 URL complète de navigation: ${url}`);
      
      // Navigation avec plus de détails de debug
      console.log(`🔄 Chargement de la page...`);
      await this.page.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: 30000
      });
      
      // Attendre un peu pour que la page se charge complètement
      await this.page.waitForTimeout(3000);
      
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
      await this.page.waitForSelector('th div.flex.items-center.gap-1', { timeout: 10000 });
      
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
   * @returns {Promise<Object>} - Données de la boutique
   */
  async extractShopData(row) {
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
      
      // 🆕 Récupération de l'année de fondation via API
      if (shopData.shopUrl) {
        shopData.yearFounded = await this.extractYearFounded(shopData.shopUrl);
      }
      
      return shopData;
    } catch (error) {
      console.error('❌ Erreur extraction données boutique:', error.message);
      return null;
    }
  }

  /**
   * Extrait l'année de fondation d'une boutique via interception d'API
   * @param {string} url - URL de la boutique
   * @returns {Promise<string|null>} - Année de fondation ou null
   */
  async extractYearFounded(url) {
    try {
      console.log(`🔍 Extraction année de fondation pour: ${url}`);
      
      // Créer un nouveau contexte pour cette requête
      const context = await this.page.context().browser().newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      });
      const newPage = await context.newPage();
      
      const apiData = [];
      
      // Intercepter les requêtes API
      newPage.on('response', async (response) => {
        try {
          const responseUrl = response.url();
          
          if (this.isRelevantAPI(responseUrl)) {
            const data = await response.json();
            if (this.containsTargetData(data)) {
              apiData.push({
                url: responseUrl,
                method: response.request().method(),
                status: response.status(),
                data: data
              });
              console.log(`📡 API pertinente trouvée: ${responseUrl}`);
            }
          }
        } catch (e) {
          // Ignore les erreurs de parsing JSON
        }
      });
      
      // Navigation avec timeout
      await newPage.goto(url, { 
        waitUntil: 'networkidle', 
        timeout: 30000 
      });
      
      // Attendre le chargement des données dynamiques
      await newPage.waitForTimeout(3000);
      
      // Extraire les données du DOM pour les dates
      const domData = await newPage.evaluate(() => {
        const findDates = () => {
          const elements = Array.from(document.querySelectorAll('*'));
          return elements
            .filter(el => el.textContent && el.textContent.match(/\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2}|\d{4}/))
            .map(el => ({
              text: el.textContent.trim(),
              tag: el.tagName
            }))
            .slice(0, 10); // Limiter à 10 résultats
        };

        return {
          title: document.title || '',
          url: window.location.href,
          dates: findDates(),
          metaDescription: document.querySelector('meta[name="description"]')?.content || '',
          h1Count: document.querySelectorAll('h1').length,
          imageCount: document.querySelectorAll('img').length
        };
      });
      
      // Extraire l'année de fondation des données collectées
      const yearFounded = this.extractYearFromData(apiData, domData);
      
      await context.close();
      
      if (yearFounded) {
        console.log(`📅 Année de fondation trouvée: ${yearFounded}`);
      } else {
        console.log(`❌ Aucune année de fondation trouvée pour ${url}`);
      }
      
      return yearFounded;
      
    } catch (error) {
      console.error(`❌ Erreur extraction année de fondation pour ${url}:`, error.message);
      return null;
    }
  }
  
  /**
   * Vérifie si une URL d'API est pertinente
   * @param {string} url - URL à vérifier
   * @returns {boolean} - True si pertinente
   */
  isRelevantAPI(url) {
    const staticExtensions = /\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico|webp)(\?.*)?$/i;
    const relevantPaths = /(api|data|ajax|json|graphql|analytics|metrics|stats|company|about|founded)/i;
    
    return !staticExtensions.test(url) && relevantPaths.test(url);
  }
  
  /**
   * Vérifie si les données contiennent des informations pertinentes
   * @param {Object} data - Données à vérifier
   * @returns {boolean} - True si pertinentes
   */
  containsTargetData(data) {
    if (!data || typeof data !== 'object') return false;
    
    const jsonStr = JSON.stringify(data).toLowerCase();
    const targetKeywords = [
      'shop_created_at',
      'website',
      'domain',
      'traffic',
      'visitors',
      'analytics',
      'created_at',
      'launch_date',
      'founded',
      'established',
      'year',
      'company',
      'about'
    ];
    
    return targetKeywords.some(keyword => jsonStr.includes(keyword)) ||
           jsonStr.match(/\d{4}-\d{2}-\d{2}|\d{4}/);
  }
  
  /**
   * Extrait l'année de fondation des données collectées
   * @param {Array} apiData - Données API
   * @param {Object} domData - Données DOM
   * @returns {string|null} - Année de fondation ou null
   */
  extractYearFromData(apiData, domData) {
    // Chercher dans les données API
    for (const api of apiData) {
      const data = api.data;
      
      // Chercher des champs spécifiques
      const yearFields = [
        'shop_created_at', 'created_at', 'launch_date', 
        'founded', 'established', 'year_founded', 'founding_year'
      ];
      
      for (const field of yearFields) {
        if (field in data) {
          const yearValue = data[field];
          if (yearValue) {
            const year = this.extractYearFromString(String(yearValue));
            if (year && this.isValidFoundingYear(year)) {
              return year;
            }
          }
        }
      }
      
      // Chercher dans les structures imbriquées
      const year = this.searchYearInObject(data);
      if (year) {
        return year;
      }
    }
    
    // Chercher dans les données DOM
    if (domData.dates) {
      for (const dateInfo of domData.dates) {
        const year = this.extractYearFromString(dateInfo.text);
        if (year && this.isValidFoundingYear(year)) {
          return year;
        }
      }
    }
    
    return null;
  }
  
  /**
   * Recherche récursive d'année dans un objet
   * @param {Object} obj - Objet à rechercher
   * @param {number} maxDepth - Profondeur maximale
   * @returns {string|null} - Année trouvée ou null
   */
  searchYearInObject(obj, maxDepth = 3) {
    if (maxDepth <= 0) return null;
    
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'object' && value !== null) {
        const year = this.searchYearInObject(value, maxDepth - 1);
        if (year) return year;
      } else if (typeof value === 'string') {
        const year = this.extractYearFromString(value);
        if (year && this.isValidFoundingYear(year)) {
          return year;
        }
      }
    }
    
    return null;
  }
  
  /**
   * Extrait une année d'une chaîne de caractères
   * @param {string} text - Texte à analyser
   * @returns {string|null} - Année trouvée ou null
   */
  extractYearFromString(text) {
    const patterns = [
      /\b(19|20)\d{2}\b/,  // Année simple (1900-2099)
      /\d{4}-\d{2}-\d{2}/,  // Format ISO
      /\d{2}\/\d{2}\/\d{4}/,   // Format MM/DD/YYYY
    ];
    
    for (const pattern of patterns) {
      const matches = text.match(pattern);
      if (matches) {
        const year = matches[0];
        if (this.isValidFoundingYear(year)) {
          return year;
        }
      }
    }
    
    return null;
  }
  
  /**
   * Vérifie si l'année est valide pour une fondation d'entreprise
   * @param {string} year - Année à vérifier
   * @returns {boolean} - True si valide
   */
  isValidFoundingYear(year) {
    try {
      const yearInt = parseInt(year);
      const currentYear = new Date().toISOString().getFullYear();
      // Accepter les années entre 1800 et l'année actuelle
      return 1800 <= yearInt && yearInt <= currentYear;
    } catch (e) {
      return false;
    }
  }

  /**
   * Extrait toutes les données du tableau
   * @returns {Promise<Array>} - Liste des boutiques
   */
  async extractAllShopsData() {
    console.log('📋 Extraction de toutes les données du tableau...');
    
    try {
      // Attendre que le tableau soit chargé
      await this.page.waitForSelector('tbody tr', { timeout: 10000 });
      
      // Récupérer toutes les lignes du tableau
      const rows = await this.page.locator('tbody tr').all();
      console.log(`📊 ${rows.length} lignes trouvées`);
      
      const shopsData = [];
      
      for (let i = 0; i < rows.length; i++) {
        console.log(`🔍 Extraction ligne ${i + 1}/${rows.length}...`);
        
        const shopData = await this.extractShopData(rows[i]);
        if (shopData) {
          shopsData.push({
            ...shopData,
            rowIndex: i + 1,
            timestamp: new Date().toISOString()
          });
        }
        
        // Pause entre les extractions
        await this.sleep(100);
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
   * @returns {Promise<Array>} - Toutes les données scrapées
   */
  async scrapeMultiplePages(maxPages = 3) {
    console.log(`📋 Scraping de ${maxPages} pages...`);
    
    const allShopsData = [];
    
    for (let page = 1; page <= maxPages; page++) {
      console.log(`\n📄 Scraping page ${page}...`);
      
      // Extraire les données de la page actuelle
      const pageData = await this.extractAllShopsData();
      
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
          
          // Attendre un peu entre les pages
          await this.sleep(2000);
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
   * Sauvegarde les données en base via l'API TrendTrack
   * @param {Array} shopsData - Données des boutiques
   * @returns {Promise<Object>} - Résultats de la sauvegarde
   */
  async saveToDatabase(shopsData) {
    if (!shopsData || shopsData.length === 0) {
      console.log('⚠️ Aucune donnée à sauvegarder');
      return { success: 0, errors: 0, skipped: 0 };
    }
    
    console.log(`💾 Sauvegarde de ${shopsData.length} boutiques en base...`);
    
    const results = {
      success: 0,
      errors: 0,
      skipped: 0
    };
    
    const { spawn } = require('child_process');
    
    for (const shop of shopsData) {
      try {
        // Préparer les données pour le script Python
        const shopData = {
          shopName: shop.shopName || '',
          shopUrl: shop.shopUrl || '',
          monthlyVisits: shop.monthlyVisits || '',
          monthlyRevenue: shop.monthlyRevenue || '',
          liveAds: shop.liveAds || '',
          creationDate: shop.creationDate || '',
          page: shop.page || '',
          yearFounded: shop.yearFounded || null
        };
        
        // Appeler le script Python
        const pythonProcess = spawn('python3', ['save_shop_data.py', JSON.stringify(shopData)]);
        
        let output = '';
        let errorOutput = '';
        
        pythonProcess.stdout.on('data', (data) => {
          output += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
          errorOutput += data.toString();
        });
        
        // Attendre la fin du processus
        await new Promise((resolve, reject) => {
          pythonProcess.on('close', (code) => {
            if (code === 0) {
              try {
                const result = JSON.parse(output.trim());
                console.log(`📊 Résultat pour ${shopData.shopName}: ${result.status}`);
                
                if (result.status === 'added') {
                  results.success++;
                } else if (result.status === 'updated') {
                  results.skipped++;
                } else if (result.status === 'skipped') {
                  results.skipped++;
                } else {
                  results.errors++;
                }
              } catch (e) {
                console.error(`❌ Erreur parsing résultat: ${e.message}`);
                results.errors++;
              }
              resolve();
            } else {
              console.error(`❌ Erreur script Python: ${errorOutput}`);
              results.errors++;
              reject(new Error(`Script Python failed with code ${code}`));
            }
          });
        });
        
      } catch (error) {
        console.error(`❌ Erreur sauvegarde ${shop.shopName}:`, error.message);
        results.errors++;
      }
    }
    
    console.log(`📊 Résultats sauvegarde: ${results.success} ajoutées, ${results.skipped} mises à jour, ${results.errors} erreurs`);
    return results;
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