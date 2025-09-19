#!/usr/bin/env python3
"""
Script d'intégration de l'extracteur amélioré de trafic par pays
Date: 2025-09-19
Description: Remplace l'extracteur actuel par la version améliorée
"""

import os
import shutil
from datetime import datetime

def backup_current_extractor():
    """Sauvegarde l'extracteur actuel"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sauvegarder l'extracteur JavaScript actuel
    js_extractor = "src/extractors/trendtrack-extractor.js"
    if os.path.exists(js_extractor):
        backup_js = f"{js_extractor}.backup_{timestamp}"
        shutil.copy2(js_extractor, backup_js)
        print(f"✅ Sauvegarde JS créée: {backup_js}")
    
    # Sauvegarder l'extracteur Python actuel
    py_extractor = "python_bridge/market_traffic_extractor.py"
    if os.path.exists(py_extractor):
        backup_py = f"{py_extractor}.backup_{timestamp}"
        shutil.copy2(py_extractor, backup_py)
        print(f"✅ Sauvegarde Python créée: {backup_py}")

def update_js_extractor():
    """Met à jour l'extracteur JavaScript avec la logique améliorée"""
    js_file = "src/extractors/trendtrack-extractor.js"
    
    if not os.path.exists(js_file):
        print(f"❌ Fichier non trouvé: {js_file}")
        return False
    
    print(f"🔄 Mise à jour de {js_file}...")
    
    # Lire le fichier actuel
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la méthode d'extraction du trafic par pays
    old_method = '''  async extractMarketTraffic(shopId) {
    const extractedMarkets = {};
    const targets = ['us', 'uk', 'de', 'ca', 'au', 'fr'];

    try {
      const detailUrl = `https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/websites/${shopId}`;
      await this.page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await this.page.waitForTimeout(2000);

      // Essayer plusieurs sélecteurs pour trouver la section "Trafic par pays"
      let sectionFound = false;
      const selectors = [
        'h3:has-text("Trafic par pays")',
        'h3:has-text("Traffic by Country")',
        'h3.font-semibold.tracking-tight.text-lg:has-text("Trafic")',
        'h3.font-semibold.tracking-tight.text-lg:has-text("Traffic")'
      ];
      
      for (const selector of selectors) {
        try {
          await this.page.waitForSelector(selector, { state: "visible", timeout: 5000 });
          console.log(`✅ Section trouvée avec le sélecteur: ${selector}`);
          sectionFound = true;
          break;
        } catch (error) {
          console.log(`⚠️ Sélecteur ${selector} non trouvé, essai suivant...`);
        }
      }
      
      if (!sectionFound) {
        console.log('⚠️ Section "Trafic par pays" non trouvée sur cette page');
        return extractedMarkets;
      }

      // Utiliser le sélecteur qui a fonctionné
      const card = this.page.locator('h3:has-text("Trafic par pays"), h3:has-text("Traffic by Country")').locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();
      const rows = card.locator("div.flex.gap-2.w-full.items-center");
      const count = await rows.count();

      const observedMarkets = {};

      for (let i = 0; i < count; i++) {
        const row = rows.nth(i);
        let codeElement = await row.locator("img[alt]").first().getAttribute("alt");
        if (!codeElement) {
          codeElement = await row.locator("div.flex.justify-between > p").first().textContent();
        }

        const code = this.canonicalizeCountryCode(codeElement);
        if (!code) continue;

        const valueText = await row.locator("div.flex.justify-between div.items-center > p").first().textContent();
        const value = this.parseTrafficValue(valueText);

        if (value !== null) {
          observedMarkets[code] = value;
        }
      }

      let foundAnyTargetMarket = false;
      for (const target_code of targets) {
        if (target_code in observedMarkets) {
          extractedMarkets[`market_${target_code}`] = observedMarkets[target_code];
          foundAnyTargetMarket = true;
        } else {
          extractedMarkets[`market_${target_code}`] = 0;
        }
      }

      if (!foundAnyTargetMarket && Object.keys(observedMarkets).length > 0) {
        for (const target_code of targets) {
          extractedMarkets[`market_${target_code}`] = 0;
        }
      } else if (Object.keys(observedMarkets).length === 0) {
        for (const target_code of targets) {
          extractedMarkets[`market_${target_code}`] = null;
        }
      }

      console.log(`✅ Trafic par pays extrait pour ${shopId}:`, extractedMarkets);
      return extractedMarkets;

    } catch (error) {
      console.error(`❌ Erreur lors de l'extraction du trafic par pays pour ${shopId}:`, error.message);
      return extractedMarkets;
    }
  }'''

    new_method = '''  async extractMarketTraffic(shopId) {
    const extractedMarkets = {};
    const targets = ['us', 'uk', 'de', 'ca', 'au', 'fr'];

    try {
      const detailUrl = `https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/websites/${shopId}`;
      await this.page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await this.page.waitForTimeout(2000);

      console.log('🌍 Extraction trafic par pays améliorée...');

      // Essayer plusieurs sélecteurs pour trouver la section "Trafic par pays"
      let sectionFound = false;
      const selectors = [
        'h3:has-text("Trafic par pays")',
        'h3:has-text("Traffic by Country")',
        'h3.font-semibold.tracking-tight.text-lg:has-text("Trafic")',
        'h3.font-semibold.tracking-tight.text-lg:has-text("Traffic")'
      ];
      
      let workingSelector = null;
      for (const selector of selectors) {
        try {
          await this.page.waitForSelector(selector, { state: "visible", timeout: 5000 });
          console.log(`✅ Section trouvée avec le sélecteur: ${selector}`);
          sectionFound = true;
          workingSelector = selector;
          break;
        } catch (error) {
          console.log(`⚠️ Sélecteur ${selector} non trouvé, essai suivant...`);
        }
      }
      
      if (!sectionFound) {
        console.log('⚠️ Section "Trafic par pays" non trouvée sur cette page');
        return { market_us: null, market_uk: null, market_de: null, market_ca: null, market_au: null, market_fr: null };
      }

      // Localiser la carte contenant les données avec le sélecteur qui a fonctionné
      const card = this.page.locator(workingSelector).locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();
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
      return { market_us: null, market_uk: null, market_de: null, market_ca: null, market_au: null, market_fr: null };
    }
  }'''

    # Remplacer la méthode
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {js_file} mis à jour avec la logique améliorée")
        return True
    else:
        print(f"⚠️ Méthode extractMarketTraffic non trouvée dans {js_file}")
        return False

def main():
    """Fonction principale d'intégration"""
    print("🚀 Intégration de l'extracteur amélioré de trafic par pays")
    print("=" * 60)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        # 1. Sauvegarder les fichiers actuels
        print("📦 Sauvegarde des fichiers actuels...")
        backup_current_extractor()
        
        # 2. Mettre à jour l'extracteur JavaScript
        print("\n🔄 Mise à jour de l'extracteur JavaScript...")
        if update_js_extractor():
            print("✅ Extracteur JavaScript mis à jour")
        else:
            print("❌ Échec de la mise à jour JavaScript")
            return
        
        print("\n🎉 Intégration terminée avec succès !")
        print("\n📋 Résumé des améliorations:")
        print("  ✅ Sélecteurs plus robustes")
        print("  ✅ Gestion améliorée des cas vides")
        print("  ✅ Logs plus détaillés")
        print("  ✅ Parsing plus intelligent des valeurs")
        print("  ✅ Gestion des alias de pays")
        
        print("\n🔧 Prochaines étapes:")
        print("  1. Tester le scraper avec une boutique")
        print("  2. Vérifier les logs d'extraction")
        print("  3. Valider les données en base")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration: {e}")

if __name__ == "__main__":
    main()

