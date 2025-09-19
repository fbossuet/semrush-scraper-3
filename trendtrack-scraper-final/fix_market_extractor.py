#!/usr/bin/env python3
"""
Script de correction de l'extracteur de trafic par pays
Date: 2025-09-19
Description: Corrige la méthode extractMarketTrafficForShopJS avec la logique améliorée
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_extractor():
    """Sauvegarde et corrige l'extracteur"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la logique d'extraction
    old_logic = '''      // Utiliser le sélecteur qui a fonctionné
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
      }'''

    new_logic = '''      // Localiser la carte contenant les données avec le sélecteur qui a fonctionné
      const card = this.page.locator('h3:has-text("Trafic par pays"), h3:has-text("Traffic by Country")').locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();
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
      }'''

    # Remplacer la logique
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {js_file} corrigé avec la logique améliorée")
        return True
    else:
        print(f"⚠️ Logique d'extraction non trouvée dans {js_file}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Correction de l'extracteur de trafic par pays")
    print("=" * 50)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_extractor():
            print("\n🎉 Correction terminée avec succès !")
            print("\n📋 Améliorations apportées:")
            print("  ✅ Logs plus détaillés pour le debug")
            print("  ✅ Gestion améliorée des cas vides")
            print("  ✅ Parsing plus robuste des valeurs")
            print("  ✅ Affichage des pays trouvés avec leurs valeurs")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Tester le scraper avec une boutique")
            print("  2. Vérifier les logs d'extraction")
            print("  3. Valider les données en base")
        else:
            print("❌ Échec de la correction")
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")

if __name__ == "__main__":
    main()

