/**
 * Extracteur spécialisé pour les données de trafic par pays (market_*)
 * Basé sur le code fourni par l'utilisateur
 */

export class MarketTrafficExtractor {
  constructor(page) {
    this.page = page;
    
    // Pays cibles par défaut
    this.DEFAULT_TARGETS = ["us", "uk", "de", "ca", "au", "fr"];
    
    // Alias pour les codes pays
    this.ALIASES = {
      "gb": "uk",
      "uk": "uk", 
      "usa": "us",
    };
  }

  /**
   * Normalise un code pays
   * @param {string} code - Code pays
   * @returns {string} - Code normalisé
   */
  canonical(code) {
    const c = (code || "").trim().toLowerCase();
    return this.ALIASES[c] || c;
  }

  /**
   * Parse une valeur numérique en supprimant les caractères non-numériques
   * @param {string} s - Valeur à parser
   * @returns {number} - Valeur numérique
   */
  parseInt(s) {
    if (!s) return 0;
    const digits = s.replace(/[^0-9]/g, "");
    return digits ? parseInt(digits) : 0;
  }

  /**
   * Extrait les données de trafic par pays depuis la page d'une boutique
   * @param {Array} targets - Liste des pays cibles
   * @returns {Promise<Object>} - Données de trafic par pays
   */
  async scrapeMarketTraffic(targets = this.DEFAULT_TARGETS) {
    console.log('🌍 Extraction des données de trafic par pays...');
    
    try {
      // Attendre le bloc "Trafic par pays"
      await this.page.waitForSelector('h3:has-text("Trafic par pays")', { 
        state: "visible",
        timeout: 10000 
      });

      // Trouver la carte contenant les données de trafic
      const card = this.page.locator('h3:has-text("Trafic par pays")')
        .locator('xpath=ancestor::div[contains(@class,"bg-card")]')
        .first();

      // Récupérer les lignes de pays
      const rows = card.locator("div.flex.gap-2.w-full.items-center");
      const count = await rows.count();

      console.log(`📊 ${count} lignes de pays trouvées`);

      const observed = {}; // ex: {"us": 175942, "au": 18555284}

      // Extraire les données de chaque ligne
      for (let i = 0; i < count; i++) {
        const row = rows.nth(i);

        // Récupérer le code pays via l'attribut alt du drapeau ou fallback sur le premier <p>
        let code = await row.locator("img[alt]").first.getAttribute("alt");
        if (!code) {
          code = await row.locator("div.flex.justify-between > p").first.textContent();
        }

        code = this.canonical(code);
        if (!code) {
          console.log(`⚠️ Code pays non trouvé pour la ligne ${i + 1}`);
          continue;
        }

        // Récupérer la valeur (le premier <p> avant le %)
        const valueText = await row.locator("div.flex.justify-between div.items-center > p")
          .first.textContent();
        const value = this.parseInt(valueText);

        // Enregistrer uniquement si une valeur numérique est présente
        if (value !== null && value !== undefined) {
          observed[code] = value;
          console.log(`✅ ${code.toUpperCase()}: ${value}`);
        }
      }

      // Normaliser les targets
      const normalizedTargets = targets.map(t => t.toLowerCase());

      // Construire le résultat final
      let result;
      if (Object.keys(observed).length > 0) {
        // Au moins une valeur trouvée: on met 0 pour les cibles manquantes
        result = {};
        for (const target of normalizedTargets) {
          result[`market_${target}`] = observed[target] || 0;
        }
        console.log(`✅ Données de trafic extraites: ${Object.keys(observed).length} pays`);
      } else {
        // Aucune donnée trouvée: on met null pour signaler "pas de data"
        result = {};
        for (const target of normalizedTargets) {
          result[`market_${target}`] = null;
        }
        console.log('⚠️ Aucune donnée de trafic trouvée');
      }

      return result;

    } catch (error) {
      console.error('❌ Erreur lors de l\'extraction du trafic par pays:', error.message);
      
      // En cas d'erreur, retourner null pour tous les pays
      const result = {};
      for (const target of targets) {
        result[`market_${target.toLowerCase()}`] = null;
      }
      return result;
    }
  }

  /**
   * Navigue vers la page d'une boutique pour extraire les données de trafic
   * @param {string} shopUrl - URL de la boutique
   * @param {Array} targets - Liste des pays cibles
   * @returns {Promise<Object>} - Données de trafic par pays
   */
  async extractMarketTrafficForShop(shopUrl, targets = this.DEFAULT_TARGETS) {
    console.log(`🔍 Extraction trafic pour: ${shopUrl}`);
    
    try {
      // Naviguer vers la page de la boutique
      await this.page.goto(shopUrl, {
        waitUntil: 'domcontentloaded',
        timeout: 30000
      });

      // Attendre que la page se charge
      await this.page.waitForTimeout(3000);

      // Extraire les données de trafic
      const marketData = await this.scrapeMarketTraffic(targets);
      
      return {
        shopUrl,
        ...marketData,
        extractedAt: new Date().toISOString()
      };

    } catch (error) {
      console.error(`❌ Erreur extraction trafic pour ${shopUrl}:`, error.message);
      
      // En cas d'erreur, retourner null pour tous les pays
      const result = { shopUrl };
      for (const target of targets) {
        result[`market_${target.toLowerCase()}`] = null;
      }
      result.extractedAt = new Date().toISOString();
      return result;
    }
  }

  /**
   * Extrait les données de trafic pour plusieurs boutiques
   * @param {Array} shopUrls - Liste des URLs de boutiques
   * @param {Array} targets - Liste des pays cibles
   * @returns {Promise<Array>} - Liste des données de trafic
   */
  async extractMarketTrafficForMultipleShops(shopUrls, targets = this.DEFAULT_TARGETS) {
    console.log(`🌍 Extraction trafic pour ${shopUrls.length} boutiques...`);
    
    const results = [];
    
    for (let i = 0; i < shopUrls.length; i++) {
      const shopUrl = shopUrls[i];
      console.log(`\n📊 Boutique ${i + 1}/${shopUrls.length}: ${shopUrl}`);
      
      try {
        const marketData = await this.extractMarketTrafficForShop(shopUrl, targets);
        results.push(marketData);
        
        // Pause entre les extractions pour éviter la surcharge
        if (i < shopUrls.length - 1) {
          await this.sleep(2000);
        }
        
      } catch (error) {
        console.error(`❌ Erreur pour ${shopUrl}:`, error.message);
        
        // Ajouter un résultat d'erreur
        const errorResult = { shopUrl };
        for (const target of targets) {
          errorResult[`market_${target.toLowerCase()}`] = null;
        }
        errorResult.extractedAt = new Date().toISOString();
        errorResult.error = error.message;
        results.push(errorResult);
      }
    }
    
    console.log(`\n✅ Extraction terminée: ${results.length} boutiques traitées`);
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

