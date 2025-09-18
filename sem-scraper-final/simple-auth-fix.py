#!/usr/bin/env python3

def add_auth_helper():
    """Ajoute la fonction helper check_and_authenticate"""
    with open('production_scraper.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trouver la fin de la fonction authenticate_mytoolsplan (ligne 490)
    auth_helper = [
        '\n',
        '    async def check_and_authenticate(self):\n',
        '        """Vérifie si l\'utilisateur est authentifié et s\'authentifie si nécessaire"""\n',
        '        try:\n',
        '            current_url = self.page.url\n',
        '            \n',
        '            # Vérifier l\'URL ET le contenu de la page\n',
        '            login_redirected = False\n',
        '            \n',
        '            # 1. Vérifier l\'URL\n',
        '            if "app.mytoolsplan.com" in current_url and "login" in current_url:\n',
        '                login_redirected = True\n',
        '                logger.info("   🔐 Redirection vers login détectée (URL)")\n',
        '            \n',
        '            # 2. Vérifier le contenu de la page pour le message de login\n',
        '            try:\n',
        '                page_content = await self.page.content()\n',
        '                if "If you are a registered member, please login" in page_content:\n',
        '                    login_redirected = True\n',
        '                    logger.info("   🔐 Message de login détecté dans le contenu de la page")\n',
        '                elif "please login" in page_content.lower() and "registered member" in page_content.lower():\n',
        '                    login_redirected = True\n',
        '                    logger.info("   🔐 Message de login détecté (variante)")\n',
        '            except Exception as e:\n',
        '                logger.warning(f"   ⚠️ Erreur lors de la vérification du contenu: {e}")\n',
        '            \n',
        '            if login_redirected:\n',
        '                logger.info("   🔐 Authentification nécessaire, authentification...")\n',
        '                await self.page.goto("https://app.mytoolsplan.com/login", wait_until=\'domcontentloaded\', timeout=30000)\n',
        '                \n',
        '                await self.page.wait_for_selector(\'input[name="amember_login"]\', timeout=15000)\n',
        '                await self.page.wait_for_selector(\'input[name="amember_pass"]\', timeout=15000)\n',
        '                \n',
        '                await self.page.fill(\'input[name="amember_login"]\', config.config.MYTOOLSPLAN_USERNAME)\n',
        '                await self.page.fill(\'input[name="amember_pass"]\', config.config.MYTOOLSPLAN_PASSWORD)\n',
        '                await self.page.click(\'input[type="submit"]\')\n',
        '                \n',
        '                await self.page.wait_for_url("**/member", timeout=15000)\n',
        '                logger.info("   ✅ Authentification réussie")\n',
        '                return True\n',
        '            \n',
        '            return False\n',
        '            \n',
        '        except Exception as e:\n',
        '            logger.error(f"❌ Erreur lors de la vérification d\'authentification: {e}")\n',
        '            return False\n',
        '\n'
    ]
    
    # Insérer après la ligne 490
    lines[490:490] = auth_helper
    
    # Écrire le fichier
    with open('production_scraper.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fonction helper ajoutée")
    return True

def add_auth_calls():
    """Ajoute les appels à check_and_authenticate dans les fonctions de scraping"""
    with open('production_scraper.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trouver les lignes où ajouter les appels
    # Ligne 1179: début de scrape_visits
    # Ligne 1195: début de scrape_purchase_conversion (après l'ajout de la fonction helper)
    
    # Ajouter dans scrape_visits (ligne 1179)
    auth_call = [
        '                # Vérifier l\'authentification avant de scraper\n',
        '                await self.check_and_authenticate()\n',
        '\n'
    ]
    
    # Calculer la nouvelle ligne après l'ajout de la fonction helper
    new_line_1179 = 1179 + len(auth_helper) - 1  # -1 car on compte à partir de 0
    
    lines[new_line_1179:new_line_1179] = auth_call
    
    # Ajouter dans scrape_purchase_conversion
    new_line_1195 = 1195 + len(auth_helper) - 1 + len(auth_call) - 1
    
    lines[new_line_1195:new_line_1195] = auth_call
    
    # Écrire le fichier
    with open('production_scraper.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Appels à check_and_authenticate ajoutés")
    return True

def verify_syntax():
    """Vérifie la syntaxe Python"""
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

if __name__ == "__main__":
    print("🔧 Ajout de la fonction helper check_and_authenticate...")
    
    if add_auth_helper() and add_auth_calls() and verify_syntax():
        print("✅ Modification terminée avec succès")
    else:
        print("❌ Échec de la modification")
