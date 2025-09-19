#!/usr/bin/env python3
"""
Fix pour utiliser exactement la logique du script Python fourni
Date: 2025-09-19
Description: Remplace la logique multi-sélecteurs par la logique exacte du script Python
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_exact_logic():
    """Sauvegarde et corrige avec la logique exacte du script Python"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la logique multi-sélecteurs par la logique exacte du script Python
    old_logic = '''      // Essayer plusieurs sélecteurs pour trouver la section "Trafic par pays"
      let sectionFound = false;
      let workingSelector = null;
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
          workingSelector = selector;
          break;
        } catch (error) {
          console.log(`⚠️ Sélecteur ${selector} non trouvé, essai suivant...`);
        }
      }
      
      if (!sectionFound) {
        console.log('⚠️ Section "Trafic par pays" non trouvée sur cette page');
        return extractedMarkets;
      }

      // Localiser la carte contenant les données avec le sélecteur qui a fonctionné
      const card = this.page.locator(workingSelector).locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();'''
    
    new_logic = '''      // Attendre le bloc "Trafic par pays" (logique exacte du script Python)
      try {
        await this.page.waitForSelector('h3:has-text("Trafic par pays")', { state: "visible", timeout: 10000 });
        console.log('✅ Section "Trafic par pays" trouvée');
      } catch (error) {
        console.log('⚠️ Section "Trafic par pays" non trouvée sur cette page');
        return extractedMarkets;
      }

      // Localiser la carte contenant les données (logique exacte du script Python)
      const card = this.page.locator('h3:has-text("Trafic par pays")').locator('xpath=ancestor::div[contains(@class,"bg-card")]').first();'''
    
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {js_file} corrigé avec la logique exacte du script Python")
        return True
    else:
        print(f"⚠️ Logique multi-sélecteurs non trouvée")
        return False

def main():
    """Fonction principale"""
    print("🔧 Fix avec la logique exacte du script Python")
    print("=" * 50)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_exact_logic():
            print("\n🎉 Fix terminé avec succès !")
            print("\n📋 Changements apportés:")
            print("  ✅ Suppression de la logique multi-sélecteurs")
            print("  ✅ Utilisation du sélecteur unique: 'h3:has-text(\"Trafic par pays\")'")
            print("  ✅ Timeout augmenté à 10 secondes")
            print("  ✅ Logique exacte du script Python intégrée")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Redémarrer le scraper")
            print("  2. Vérifier les logs")
            print("  3. Valider l'extraction")
        else:
            print("❌ Échec du fix")
            
    except Exception as e:
        print(f"❌ Erreur lors du fix: {e}")

if __name__ == "__main__":
    main()

