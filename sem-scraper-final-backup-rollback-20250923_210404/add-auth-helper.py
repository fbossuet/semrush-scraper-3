#!/usr/bin/env python3
"""
Script pour ajouter la fonction helper check_and_authenticate
de manière sécurisée dans production_scraper.py
"""

import re
import sys
from pathlib import Path

def add_auth_helper():
    """Ajoute la fonction helper check_and_authenticate"""
    
    # Lire le fichier
    with open('production_scraper.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fonction helper à ajouter
    auth_helper = '''
    async def check_and_authenticate(self):
        """Vérifie si l'utilisateur est authentifié et s'authentifie si nécessaire"""
        try:
            current_url = self.page.url
            
            # Vérifier l'URL ET le contenu de la page
            login_redirected = False
            
            # 1. Vérifier l'URL
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                login_redirected = True
                logger.info("   🔐 Redirection vers login détectée (URL)")
            
            # 2. Vérifier le contenu de la page pour le message de login
            try:
                page_content = await self.page.content()
                if "If you are a registered member, please login" in page_content:
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté dans le contenu de la page")
                elif "please login" in page_content.lower() and "registered member" in page_content.lower():
                    login_redirected = True
                    logger.info("   🔐 Message de login détecté (variante)")
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")
            
            if login_redirected:
                logger.info("   🔐 Authentification nécessaire, authentification...")
                await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=30000)
                
                await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
                await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)
                
                await self.page.fill('input[name="amember_login"]', config.config.MYTOOLSPLAN_USERNAME)
                await self.page.fill('input[name="amember_pass"]', config.config.MYTOOLSPLAN_PASSWORD)
                await self.page.click('input[type="submit"]')
                
                await self.page.wait_for_url("**/member", timeout=15000)
                logger.info("   ✅ Authentification réussie")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification d'authentification: {e}")
            return False
'''
    
    # Trouver la fin de la fonction authenticate_mytoolsplan
    # Chercher la ligne "return False" qui termine cette fonction
    pattern = r'(async def authenticate_mytoolsplan\(self\):.*?return False\s*\n\s*\n)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Impossible de trouver la fonction authenticate_mytoolsplan")
        return False
    
    # Remplacer par la fonction + la nouvelle fonction helper
    replacement = match.group(1) + auth_helper
    
    # Faire le remplacement
    new_content = content.replace(match.group(1), replacement)
    
    # Écrire le fichier modifié
    with open('production_scraper.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fonction helper check_and_authenticate ajoutée")
    return True

def update_traffic_analysis():
    """Met à jour scrape_traffic_analysis pour utiliser la fonction helper"""
    
    # Lire le fichier
    with open('production_scraper.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour les fonctions de scraping parallèle
    old_pattern = '''            # Scraping des métriques en parallèle
            async def scrape_visits():
                element = await self.validate_selector_adaptive(
                    'div[data-testid="summary-cell visits"] > div > div > div > span[data-testid="value"]',

                    "Visits"
                )
                if element:
                    value = await element.inner_text()
                    logger.info(f"✅ Visits: {value}")
                    return value
                else:
                    logger.info("❌ Visits: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"

            async def scrape_purchase_conversion():
                element = await self.validate_selector_adaptive(
                    'div[data-testid="summary-cell conversion"] > div > div > div > span[data-testid="value"]',

                    "Purchase Conversion"
                )
                if element:
                    value = await element.inner_text()
                    logger.info(f"✅ Purchase Conversion: {value}")
                    return value
                else:
                    logger.info("❌ Purchase Conversion: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"'''
    
    new_pattern = '''            # Scraping des métriques en parallèle
            async def scrape_visits():
                # Vérifier l'authentification avant de scraper
                await self.check_and_authenticate()
                
                element = await self.validate_selector_adaptive(
                    'div[data-testid="summary-cell visits"] > div > div > div > span[data-testid="value"]',

                    "Visits"
                )
                if element:
                    value = await element.inner_text()
                    logger.info(f"✅ Visits: {value}")
                    return value
                else:
                    logger.info("❌ Visits: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"

            async def scrape_purchase_conversion():
                # Vérifier l'authentification avant de scraper
                await self.check_and_authenticate()
                
                element = await self.validate_selector_adaptive(
                    'div[data-testid="summary-cell conversion"] > div > div > div > span[data-testid="value"]',

                    "Purchase Conversion"
                )
                if element:
                    value = await element.inner_text()
                    logger.info(f"✅ Purchase Conversion: {value}")
                    return value
                else:
                    logger.info("❌ Purchase Conversion: Sélecteur non trouvé")
                    return "Sélecteur non trouvé"'''
    
    # Faire le remplacement
    if old_pattern in content:
        new_content = content.replace(old_pattern, new_pattern)
        
        # Écrire le fichier modifié
        with open('production_scraper.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fonctions de scraping parallèle mises à jour")
        return True
    else:
        print("❌ Pattern pour les fonctions de scraping parallèle non trouvé")
        return False

def verify_syntax():
    """Vérifie la syntaxe Python du fichier modifié"""
    try:
        import ast
        with open('production_scraper.py', 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("✅ Syntaxe Python vérifiée - OK")
        return True
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Ajout de la fonction helper check_and_authenticate...")
    
    # Étape 1: Ajouter la fonction helper
    if not add_auth_helper():
        print("❌ Échec de l'ajout de la fonction helper")
        return False
    
    # Étape 2: Mettre à jour scrape_traffic_analysis
    if not update_traffic_analysis():
        print("❌ Échec de la mise à jour de scrape_traffic_analysis")
        return False
    
    # Étape 3: Vérifier la syntaxe
    if not verify_syntax():
        print("❌ Erreur de syntaxe détectée")
        return False
    
    print("✅ Modification terminée avec succès")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
