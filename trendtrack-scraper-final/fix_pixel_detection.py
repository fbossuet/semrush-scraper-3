#!/usr/bin/env python3
"""
Fix pour améliorer la détection des pixels Google et Facebook
Date: 2025-09-19
Description: Améliore les sélecteurs pour détecter les pixels de tracking
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_pixels():
    """Sauvegarde et corrige la détection des pixels"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ancienne logique de détection des pixels
    old_pixel_logic = '''      const facebookPixel = await this.page.locator('img[alt="facebook"][src*="meta-icon.svg"]').isVisible();
      const googlePixel = await this.page.locator('img[alt="google"][src*="google-icon.svg"]').isVisible();

      if (facebookPixel) {
        pixelData.pixel_facebook = "oui";
      }
      if (googlePixel) {
        pixelData.pixel_google = "oui";
      }'''
    
    # Nouvelle logique de détection des pixels (plus robuste)
    new_pixel_logic = '''      // Détection améliorée des pixels Facebook
      const facebookSelectors = [
        'img[alt="facebook"][src*="meta-icon.svg"]',
        'img[alt="facebook"]',
        'img[src*="facebook"]',
        'img[src*="meta-icon"]',
        '[class*="facebook"]',
        'script[src*="facebook"]',
        'script[src*="fbevents"]'
      ];
      
      let facebookPixel = false;
      for (const selector of facebookSelectors) {
        try {
          if (await this.page.locator(selector).isVisible()) {
            facebookPixel = true;
            break;
          }
        } catch (e) {
          // Ignorer les erreurs de sélecteur
        }
      }
      
      // Détection améliorée des pixels Google
      const googleSelectors = [
        'img[alt="google"][src*="google-icon.svg"]',
        'img[alt="google"]',
        'img[src*="google"]',
        'img[src*="google-icon"]',
        '[class*="google"]',
        'script[src*="google-analytics"]',
        'script[src*="gtag"]',
        'script[src*="googletagmanager"]'
      ];
      
      let googlePixel = false;
      for (const selector of googleSelectors) {
        try {
          if (await this.page.locator(selector).isVisible()) {
            googlePixel = true;
            break;
          }
        } catch (e) {
          // Ignorer les erreurs de sélecteur
        }
      }

      if (facebookPixel) {
        pixelData.pixel_facebook = "oui";
      }
      if (googlePixel) {
        pixelData.pixel_google = "oui";
      }'''
    
    if old_pixel_logic in content:
        content = content.replace(old_pixel_logic, new_pixel_logic)
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {js_file} corrigé avec détection améliorée des pixels")
        return True
    else:
        print(f"⚠️ Logique de détection des pixels non trouvée")
        return False

def main():
    """Fonction principale"""
    print("🔧 Fix de la détection des pixels Google et Facebook")
    print("=" * 60)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_pixels():
            print("\n🎉 Fix terminé avec succès !")
            print("\n📋 Améliorations apportées:")
            print("  ✅ Sélecteurs multiples pour Facebook (7 variantes)")
            print("  ✅ Sélecteurs multiples pour Google (8 variantes)")
            print("  ✅ Détection par images, classes et scripts")
            print("  ✅ Gestion d'erreur robuste")
            print("  ✅ Détection plus flexible")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Redémarrer le scraper")
            print("  2. Vérifier la détection des pixels")
            print("  3. Valider les données en base")
        else:
            print("❌ Échec du fix")
            
    except Exception as e:
        print(f"❌ Erreur lors du fix: {e}")

if __name__ == "__main__":
    main()

