#!/usr/bin/env python3
"""
Script corrigé pour ajouter la fonction helper check_and_authenticate
de manière sécurisée dans production_scraper.py
"""

import re
import sys

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
    
    # Pattern plus flexible pour les fonctions de scraping parallèle
    # Chercher ligne par ligne
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Si on trouve le début des fonctions de scraping parallèle
        if '# Scraping des métriques en parallèle' in line:
            new_lines.append(line)
            i += 1
            
            # Chercher la fonction scrape_visits
            while i < len(lines) and 'async def scrape_visits():' not in lines[i]:
                new_lines.append(lines[i])
                i += 1
            
            if i < len(lines):
                new_lines.append(lines[i])  # async def scrape_visits():
                i += 1
                
                # Ajouter la vérification d'authentification
                new_lines.append('                # Vérifier l\'authentification avant de scraper')
                new_lines.append('                await self.check_and_authenticate()')
                new_lines.append('')
                
                # Continuer jusqu'à la fin de scrape_visits
                while i < len(lines) and 'async def scrape_purchase_conversion():' not in lines[i]:
                    new_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    new_lines.append(lines[i])  # async def scrape_purchase_conversion():
                    i += 1
                    
                    # Ajouter la vérification d'authentification
                    new_lines.append('                # Vérifier l\'authentification avant de scraper')
                    new_lines.append('                await self.check_and_authenticate()')
                    new_lines.append('')
                    
                    # Continuer jusqu'à la fin de scrape_purchase_conversion
                    while i < len(lines) and '# Exécuter les scrapings en parallèle' not in lines[i]:
                        new_lines.append(lines[i])
                        i += 1
                    
                    # Ajouter le reste
                    while i < len(lines):
                        new_lines.append(lines[i])
                        i += 1
                else:
                    # Ajouter le reste si scrape_purchase_conversion n'est pas trouvé
                    while i < len(lines):
                        new_lines.append(lines[i])
                        i += 1
            else:
                # Ajouter le reste si scrape_visits n'est pas trouvé
                while i < len(lines):
                    new_lines.append(lines[i])
                    i += 1
        else:
            new_lines.append(line)
            i += 1
    
    # Écrire le fichier modifié
    new_content = '\n'.join(new_lines)
    with open('production_scraper.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fonctions de scraping parallèle mises à jour")
    return True

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

def verify_changes():
    """Vérifie que les changements ont été appliqués"""
    with open('production_scraper.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier que la fonction helper a été ajoutée
    if 'async def check_and_authenticate(self):' in content:
        print("✅ Fonction helper check_and_authenticate trouvée")
    else:
        print("❌ Fonction helper check_and_authenticate non trouvée")
        return False
    
    # Vérifier que les appels ont été ajoutés
    if 'await self.check_and_authenticate()' in content:
        print("✅ Appels à check_and_authenticate trouvés")
    else:
        print("❌ Appels à check_and_authenticate non trouvés")
        return False
    
    return True

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
    
    # Étape 4: Vérifier que les changements ont été appliqués
    if not verify_changes():
        print("❌ Vérification des changements échouée")
        return False
    
    print("✅ Modification terminée avec succès")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
