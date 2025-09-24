#!/usr/bin/env python3
"""
Script pour afficher uniquement le JSON brut de la réponse API MyTools
"""

import asyncio
import os
import json
from playwright.async_api import async_playwright

class MyToolsRawJSON:
    def __init__(self):
        self.credentials = {
            "userId": 26931056,
            "apiKey": "943cfac719badc2ca14126e08b8fe44f"
        }
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        """Initialiser le navigateur avec le même contexte que production_scraper.py"""
        print("🔧 Configuration du navigateur...")
        
        # Détection du système
        import platform
        if platform.system() == "Linux":
            print("🖥️ Linux détecté - Configuration Xvfb...")
            # Vérifier si Xvfb est déjà en cours
            import subprocess
            try:
                subprocess.run(["pgrep", "Xvfb"], check=True, capture_output=True)
                print("🖥️ Xvfb déjà en cours")
            except subprocess.CalledProcessError:
                print("🖥️ Démarrage de Xvfb...")
                subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1024x768x24"])
                os.environ["DISPLAY"] = ":99"
        
        playwright = await async_playwright().start()
        
        # Configuration pour VPS
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        # Contexte persistant pour maintenir la session
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        self.page = await self.context.new_page()

    async def authenticate_mytoolsplan(self):
        """Authentification MyToolsPlan"""
        print("🔐 Authentification MyToolsPlan...")
        
        # Aller à la page de login
        await self.page.goto("https://app.mytoolsplan.com/login", timeout=30000)
        await self.page.wait_for_timeout(2000)
        
        # Remplir les identifiants
        await self.page.fill('input[name="username"]', str(self.credentials["userId"]))
        await self.page.fill('input[name="password"]', self.credentials["apiKey"])
        
        # Cliquer sur login
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_timeout(3000)
        
        # Vérifier la connexion
        current_url = self.page.url
        print(f"✅ Login réussi, URL actuelle: {current_url}")
        
        # Aller à sam.mytoolsplan.xyz
        await self.page.goto("https://sam.mytoolsplan.xyz", timeout=30000)
        await self.page.wait_for_timeout(2000)
        
        print("✅ Authentification complète réussie")

    async def get_raw_json_response(self, domain):
        """Récupérer uniquement le JSON brut de l'API"""
        print(f"📊 Récupération JSON brut pour: {domain}")
        
        # Paramètres pour l'API
        params = {
            "dateType": "daily",
            "searchItem": domain,
            "searchType": "domain",
            "database": "us",
            "global": True
        }
        
        try:
            # Appel API pour récupérer uniquement le JSON brut
            response = await self.page.evaluate("""
                async (data) => {
                    const response = await fetch('/dpa/rpc', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'include',
                        body: JSON.stringify({
                            id: new Date().toISOString(),
                            jsonrpc: "2.0",
                            method: "organic.OverviewTrend",
                            params: {
                                request_id: crypto.randomUUID(),
                                report: "domain.overview",
                                args: data.params,
                                userId: data.credentials.userId,
                                apiKey: data.credentials.apiKey
                            }
                        })
                    });
                    
                    const responseText = await response.text();
                    return responseText;
                }
            """, {
                'params': params,
                'credentials': self.credentials
            })
            
            print("=" * 100)
            print("🔍 JSON BRUT DE LA RÉPONSE API MyTools")
            print("=" * 100)
            print(response)
            print("=" * 100)
            
            return response
            
        except Exception as e:
            print(f"❌ Erreur API: {e}")
            return None

    async def close(self):
        """Fermer le navigateur"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

async def main():
    api = MyToolsRawJSON()
    
    try:
        await api.init_browser()
        await api.authenticate_mytoolsplan()
        
        # Test avec spanx.com
        result = await api.get_raw_json_response("spanx.com")
        
        if result:
            print("✅ JSON brut récupéré avec succès!")
        else:
            print("❌ Échec de récupération du JSON")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
