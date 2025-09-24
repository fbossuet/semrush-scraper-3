/**
 * Module de formatage des données TrendTrack
 * Centralise tous les formats de données selon les spécifications
 */

export class DataFormatter {
  
  /**
   * Formate une année de fondation avec création de timestamp ISO 8601 UTC
   * @param {string} value - Valeur brute (ex: "09/17/2021(4 years)")
   * @returns {Object|null} - {year_founded: TEXT, creation_date: ISO_STRING}
   */
  static formatYearFounded(value) {
    if (!value) return null;
    
    try {
      console.log(`🔍 Formatage year_founded: "${value}"`);
      
      // Patterns multiples pour extraire l'année
      const yearPatterns = [
        // Format date: "17/09/2021" ou "09/17/2021"
        /(\d{1,2})\/(\d{1,2})\/(\d{4})/,
        // Format date: "2021-09-17"
        /(\d{4})-(\d{1,2})-(\d{1,2})/,
        // Format date: "17-09-2021"
        /(\d{1,2})-(\d{1,2})-(\d{4})/,
        // Année seule: "2021"
        /(\d{4})/,
        // Format avec texte: "17/09/2021 (4 années)"
        /(\d{1,2})\/(\d{1,2})\/(\d{4}).*?\((\d+)\s*années?\)/,
        // Format avec texte: "Founded in 2021"
        /Founded\s+in\s+(\d{4})/i,
        // Format avec texte: "Since 2021"
        /Since\s+(\d{4})/i
      ];
      
      for (const pattern of yearPatterns) {
        const match = value.match(pattern);
        if (match) {
          let year = null;
          let creationDate = null;
          
          // Extraire l'année selon le pattern
          if (match.length === 4) {
            // Format avec jour/mois/année - Format américain MM/DD/YYYY
            const month = match[1].padStart(2, '0');
            const day = match[2].padStart(2, '0');
            year = parseInt(match[3]);
            // Créer un timestamp ISO 8601 UTC
            const date = new Date(`${year}-${month}-${day}T00:00:00.000Z`);
            creationDate = date.toISOString();
          } else if (match.length === 2) {
            // Année seule
            year = parseInt(match[1]);
            // Créer un timestamp ISO 8601 UTC pour le 1er janvier
            const date = new Date(`${year}-01-01T00:00:00.000Z`);
            creationDate = date.toISOString();
          }
          
          if (year && !isNaN(year)) {
            // Validation: année raisonnable (1990 à maintenant + 1)
            const currentYear = new Date().getFullYear();
            if (year >= 1990 && year <= currentYear + 1) {
              console.log(`✅ Année de fondation formatée: "${value}" -> year: ${year}, date: ${creationDate}`);
              return {
                year_founded: year.toString(), // TEXT (pas de .0)
                creation_date: creationDate // ISO 8601 UTC timestamp
              };
            } else {
              console.log(`⚠️ Année hors plage raisonnable: ${year} (1990-${currentYear + 1})`);
            }
          }
        }
      }
      
      console.log(`⚠️ Aucune année valide trouvée dans: "${value}"`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage year_founded: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate les visites mensuelles (conversion K/M vers INTEGER)
   * @param {string} visitsText - Texte brut (ex: "647.6K", "1.25M")
   * @returns {number|null} - Nombre entier
   */
  static formatMonthlyVisits(visitsText) {
    if (!visitsText) return null;
    
    try {
      console.log(`🔍 Formatage monthly_visits: "${visitsText}"`);
      
      // Nettoyer le texte
      const cleaned = visitsText.trim().replace(/[,\s]/g, '');
      
      if (cleaned.includes('K')) {
        const value = parseFloat(cleaned.replace('K', ''));
        const result = Math.round(value * 1000);
        console.log(`✅ Visites formatées: "${visitsText}" -> ${result}`);
        return result;
      }
      
      if (cleaned.includes('M')) {
        const value = parseFloat(cleaned.replace('M', ''));
        const result = Math.round(value * 1000000);
        console.log(`✅ Visites formatées: "${visitsText}" -> ${result}`);
        return result;
      }
      
      // Nombre direct
      const result = parseInt(cleaned);
      if (!isNaN(result)) {
        console.log(`✅ Visites formatées: "${visitsText}" -> ${result}`);
        return result;
      }
      
      console.log(`⚠️ Format de visites non reconnu: "${visitsText}"`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage monthly_visits: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate les revenus mensuels (conserve le format range)
   * @param {string} revenueText - Texte brut (ex: "597.9K$ - 1.8M$")
   * @returns {string|null} - Texte formaté
   */
  static formatMonthlyRevenue(revenueText) {
    if (!revenueText) return null;
    
    try {
      console.log(`🔍 Formatage monthly_revenue: "${revenueText}"`);
      
      // Nettoyer et conserver le format range
      const cleaned = revenueText.trim();
      
      if (cleaned.includes('$') || cleaned.includes('K') || cleaned.includes('M')) {
        console.log(`✅ Revenus formatés: "${revenueText}" -> "${cleaned}"`);
        return cleaned;
      }
      
      console.log(`⚠️ Format de revenus non reconnu: "${revenueText}"`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage monthly_revenue: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate les live ads (extraction du nombre entier)
   * @param {string} liveAdsText - Texte brut (ex: "7319")
   * @returns {number|null} - Nombre entier
   */
  static formatLiveAds(liveAdsText) {
    if (!liveAdsText) return null;
    
    try {
      console.log(`🔍 Formatage live_ads: "${liveAdsText}"`);
      
      // Extraire le nombre entier
      const match = liveAdsText.match(/\d+/);
      if (match) {
        const result = parseInt(match[0]);
        console.log(`✅ Live ads formatés: "${liveAdsText}" -> ${result}`);
        return result;
      }
      
      console.log(`⚠️ Format de live ads non reconnu: "${liveAdsText}"`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage live_ads: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate les catégories (jointure avec |)
   * @param {Array} categoryElements - Éléments DOM des catégories
   * @returns {string|null} - Catégories jointes
   */
  static formatCategories(categoryElements) {
    if (!categoryElements || categoryElements.length === 0) return null;
    
    try {
      console.log(`🔍 Formatage categories: ${categoryElements.length} éléments`);
      
      const categories = categoryElements.map(div => div.textContent.trim()).filter(text => text);
      const result = categories.join('|');
      
      if (result) {
        console.log(`✅ Catégories formatées: "${result}"`);
        return result;
      }
      
      console.log(`⚠️ Aucune catégorie valide trouvée`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage categories: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate l'AOV (Average Order Value) avec normalisation robuste
   * @param {string} aovText - Texte brut (ex: "1.25", "25.50$", "AOV: $15.99")
   * @returns {number|null} - Valeur numérique
   */
  static formatAOV(aovText) {
    if (!aovText) return null;
    
    try {
      console.log(`🔍 Formatage AOV: "${aovText}"`);
      
      // Nettoyer la valeur
      let cleanValue = aovText.toString().trim();
      
      // Supprimer les préfixes de devise
      cleanValue = cleanValue.replace(/^[\$€£¥]/, '');
      
      // Supprimer les suffixes
      cleanValue = cleanValue.replace(/\s*(USD|EUR|GBP|CAD|AUD|per order|AOV).*$/i, '');
      
      // Supprimer les virgules et espaces
      cleanValue = cleanValue.replace(/[, ]/g, '');
      
      // Convertir en nombre
      const numericValue = parseFloat(cleanValue);
      
      if (isNaN(numericValue) || numericValue <= 0) {
        console.log(`⚠️ Valeur AOV invalide: "${aovText}" -> "${cleanValue}" -> ${numericValue}`);
        return null;
      }
      
      // Validation: AOV raisonnable (entre 1$ et 10000$)
      if (numericValue < 1 || numericValue > 10000) {
        console.log(`⚠️ AOV hors plage raisonnable: ${numericValue}`);
        return null;
      }
      
      console.log(`✅ AOV formaté: "${aovText}" -> ${numericValue}`);
      return numericValue;
      
    } catch (error) {
      console.log(`❌ Erreur formatage AOV: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate le nombre de produits
   * @param {string} productsText - Texte brut (ex: "24750 products")
   * @returns {number|null} - Nombre entier
   */
  static formatTotalProducts(productsText) {
    if (!productsText) return null;
    
    try {
      console.log(`🔍 Formatage total_products: "${productsText}"`);
      
      // Extraire le nombre
      const match = productsText.match(/\d[\d\s.,]*/);
      if (match) {
        const result = parseInt(match[0].replace(/[^\d]/g, ''));
        console.log(`✅ Produits formatés: "${productsText}" -> ${result}`);
        return result;
      }
      
      console.log(`⚠️ Format de produits non reconnu: "${productsText}"`);
      return null;
      
    } catch (error) {
      console.log(`❌ Erreur formatage total_products: ${error.message}`);
      return null;
    }
  }

  /**
   * Formate un timestamp ISO 8601 UTC
   * @param {Date|string} date - Date à formater
   * @returns {string} - Timestamp ISO 8601 UTC
   */
  static formatTimestamp(date = new Date()) {
    try {
      const dateObj = date instanceof Date ? date : new Date(date);
      return dateObj.toISOString();
    } catch (error) {
      console.log(`❌ Erreur formatage timestamp: ${error.message}`);
      return new Date().toISOString();
    }
  }

  /**
   * Valide et formate une URL
   * @param {string} url - URL à valider
   * @returns {string|null} - URL formatée ou null
   */
  static formatUrl(url) {
    if (!url) return null;
    
    try {
      // Ajouter https:// si manquant
      if (!url.startsWith('http')) {
        url = 'https://' + url;
      }
      
      // Valider l'URL
      new URL(url);
      return url;
      
    } catch (error) {
      console.log(`❌ URL invalide: "${url}"`);
      return null;
    }
  }
}
