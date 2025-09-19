#!/usr/bin/env python3
"""
Fix pour corriger l'URL de détail des boutiques
Date: 2025-09-19
Description: Corrige l'URL de /shop/ vers /trending-shops/ et /en/ vers /fr/
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_url():
    """Sauvegarde et corrige l'URL de détail"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corriger les URLs
    old_url = "https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/${shopId}"
    new_url = "https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/${shopId}"
    
    if old_url in content:
        content = content.replace(old_url, new_url)
        print(f"✅ URL corrigée: {old_url} → {new_url}")
        
        # Écrire le fichier mis à jour
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print(f"⚠️ URL non trouvée dans le fichier")
        return False

def main():
    """Fonction principale"""
    print("🔧 Fix de l'URL de détail des boutiques")
    print("=" * 50)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_url():
            print("\n🎉 Fix terminé avec succès !")
            print("\n📋 Changements apportés:")
            print("  ✅ /en/ → /fr/ (langue française)")
            print("  ✅ /shop/ → /trending-shops/ (chemin correct)")
            print("  ✅ URL de détail corrigée")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Redémarrer le scraper")
            print("  2. Vérifier l'extraction du trafic par pays")
            print("  3. Valider les données")
        else:
            print("❌ Échec du fix")
            
    except Exception as e:
        print(f"❌ Erreur lors du fix: {e}")

if __name__ == "__main__":
    main()

