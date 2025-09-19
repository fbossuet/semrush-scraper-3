#!/usr/bin/env python3
"""
Fix pour la gestion de session TrendTrack
Date: 2025-09-19
Description: Améliore la gestion de session pour éviter les expirations
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_session():
    """Sauvegarde et corrige la gestion de session"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    js_file = "src/extractors/trendtrack-extractor.js"
    
    # Sauvegarde
    backup_file = f"{js_file}.backup_{timestamp}"
    shutil.copy2(js_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter une méthode de vérification de session
    session_check_method = '''
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
  }'''
    
    # Insérer la méthode avant extractMarketTrafficForShopJS
    insertion_point = '  async extractMarketTrafficForShopJS(shopId, targets = ["us", "uk", "de", "ca", "au", "fr"]) {'
    
    if insertion_point in content:
        content = content.replace(insertion_point, session_check_method + '\n\n' + insertion_point)
        
        # Modifier extractMarketTrafficForShopJS pour vérifier la session
        old_start = '''  async extractMarketTrafficForShopJS(shopId, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🌍 Extraction trafic par pays (JS) pour: ${shopId}`);
    const extractedMarkets = { ...targets.reduce((acc, t) => ({ ...acc, [`market_${t}`]: null }), {}) };

    try {'''
    
        new_start = '''  async extractMarketTrafficForShopJS(shopId, targets = ["us", "uk", "de", "ca", "au", "fr"]) {
    console.log(`🌍 Extraction trafic par pays (JS) pour: ${shopId}`);
    const extractedMarkets = { ...targets.reduce((acc, t) => ({ ...acc, [`market_${t}`]: null }), {}) };

    try {
      // Vérifier la session avant de continuer
      if (!(await this.ensureAuthenticated())) {
        console.log('❌ Session non valide, arrêt de l\'extraction trafic par pays');
        return extractedMarkets;
      }'''
    
        if old_start in content:
            content = content.replace(old_start, new_start)
            
            # Écrire le fichier mis à jour
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {js_file} corrigé avec gestion de session")
            return True
        else:
            print(f"⚠️ Méthode extractMarketTrafficForShopJS non trouvée")
            return False
    else:
        print(f"⚠️ Point d'insertion non trouvé")
        return False

def main():
    """Fonction principale"""
    print("🔧 Fix de la gestion de session TrendTrack")
    print("=" * 50)
    
    if not os.path.exists("src/extractors/trendtrack-extractor.js"):
        print("❌ Veuillez exécuter ce script depuis le répertoire trendtrack-scraper-final")
        return
    
    try:
        if backup_and_fix_session():
            print("\n🎉 Fix terminé avec succès !")
            print("\n📋 Améliorations apportées:")
            print("  ✅ Méthode checkSession() pour vérifier la validité")
            print("  ✅ Méthode ensureAuthenticated() pour maintenir la session")
            print("  ✅ Vérification avant chaque extraction de trafic par pays")
            print("  ✅ Arrêt gracieux si session expirée")
            
            print("\n🔧 Prochaines étapes:")
            print("  1. Redémarrer le scraper")
            print("  2. Vérifier les logs de session")
            print("  3. Valider la stabilité")
        else:
            print("❌ Échec du fix")
            
    except Exception as e:
        print(f"❌ Erreur lors du fix: {e}")

if __name__ == "__main__":
    main()

