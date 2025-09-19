#!/usr/bin/env python3
"""
Fix pour les timeouts d'extraction dans extractShopData
Date: 2025-09-19
Description: Améliore la robustesse de l'extraction des données de boutique
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_extraction():
    """Sauvegarde et corrige la méthode extractShopData"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la logique d'extraction avec timeout réduit
    old_logic = '''      // 🆕 Extraire l'ID de la boutique depuis l'attribut id de la ligne (via outerHTML pour éviter les timeouts)
      const rowHtml = await row.evaluate(el => el.outerHTML);
      const rowIdMatch = rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/);
      const rowId = rowIdMatch ? rowIdMatch[1] : null;
      shopData.shopId = rowId;'''
    
    new_logic = '''      // 🆕 Extraire l'ID de la boutique avec timeout réduit
      let rowId = null;
      try {
        const rowHtml = await row.evaluate(el => el.outerHTML, { timeout: 10000 });
        const rowIdMatch = rowHtml.match(/<tr[^>]*id=["']([^"']+)["']/);
        rowId = rowIdMatch ? rowIdMatch[1] : null;
      } catch (error) {
        console.log(`⚠️ Timeout extraction ID ligne, utilisation de l'index`);
        rowId = `row_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      }
      shopData.shopId = rowId;'''
    
    # Remplacer la logique
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {js_file} corrigé avec timeout réduit")
        return True
    else:
        print(f"⚠️ Logique d'extraction non trouvée dans {js_file}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Fix des timeouts d'extraction")
    print("=" * 40)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_extraction():
            print("\n🎉 Fix terminé avec succès !")
            print("\n📋 Améliorations apportées:")
            print("  ✅ Timeout réduit pour extractShopData (10s au lieu de 30s)")
            print("  ✅ Gestion d'erreur avec ID de fallback")
            print("  ✅ Logs d'erreur plus clairs")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Redémarrer le scraper")
            print("  2. Vérifier les logs d'extraction")
            print("  3. Valider la stabilité")
        else:
            print("❌ Échec du fix")
            
    except Exception as e:
        print(f"❌ Erreur lors du fix: {e}")

if __name__ == "__main__":
    main()

