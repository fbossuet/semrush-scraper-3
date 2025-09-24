#!/usr/bin/env python3
"""
Script pour inspecter les endpoints API de MyTools
et trouver les bonnes URLs pour les requêtes
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_mytools_endpoints():
    """🔍 Inspecte les endpoints API de MyTools"""
    print("🔍 INSPECTION DES ENDPOINTS MYTOOLS")
    print("=" * 50)
    
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox']
    )
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page = await context.new_page()
    
    # Intercepter les requêtes réseau
    requests_captured = []
    
    async def handle_request(request):
        if 'rpc' in request.url or 'api' in request.url:
            requests_captured.append({
                'url': request.url,
                'method': request.method,
                'headers': request.headers,
                'post_data': request.post_data
            })
            print(f"🌐 Requête capturée: {request.method} {request.url}")
    
    page.on('request', handle_request)
    
    try:
        print("🚀 Navigation vers MyTools...")
        await page.goto("https://sam.mytoolsplan.xyz", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        print("🔍 Recherche d'éléments de navigation...")
        
        # Essayer de trouver des liens ou boutons pour déclencher des requêtes API
        try:
            # Chercher des éléments qui pourraient déclencher des requêtes
            await page.click('body')  # Cliquer quelque part pour activer
            await page.wait_for_timeout(2000)
        except:
            pass
        
        # Essayer d'accéder à une page qui pourrait faire des requêtes API
        try:
            print("🔍 Tentative d'accès à une page de domaine...")
            await page.goto("https://sam.mytoolsplan.xyz/domain-overview?searchItem=apple.com", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"⚠️ Erreur navigation: {e}")
        
        print(f"\n📊 {len(requests_captured)} requêtes capturées:")
        for i, req in enumerate(requests_captured, 1):
            print(f"\n{i}. {req['method']} {req['url']}")
            if req['post_data']:
                print(f"   Data: {req['post_data'][:200]}...")
        
        # Essayer de trouver des endpoints dans le code source
        print("\n🔍 Recherche d'endpoints dans le code source...")
        content = await page.content()
        
        # Chercher des patterns d'API
        import re
        api_patterns = [
            r'/api/[^"\']+',
            r'/rpc/[^"\']+',
            r'/dpa/[^"\']+',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.[^(]+\(["\']([^"\']+)["\']'
        ]
        
        found_endpoints = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_endpoints.update(matches)
        
        if found_endpoints:
            print("🎯 Endpoints trouvés dans le code:")
            for endpoint in sorted(found_endpoints):
                print(f"   - {endpoint}")
        else:
            print("❌ Aucun endpoint trouvé dans le code source")
        
        # Essayer d'exécuter du JavaScript pour trouver les endpoints
        print("\n🔍 Recherche d'endpoints via JavaScript...")
        try:
            js_endpoints = await page.evaluate("""
                () => {
                    const endpoints = [];
                    
                    // Chercher dans window
                    if (window.apiEndpoint) endpoints.push(window.apiEndpoint);
                    if (window.apiUrl) endpoints.push(window.apiUrl);
                    if (window.baseUrl) endpoints.push(window.baseUrl);
                    
                    // Chercher dans des objets globaux
                    const globalObjects = ['app', 'api', 'config', 'settings'];
                    globalObjects.forEach(obj => {
                        if (window[obj] && window[obj].endpoint) {
                            endpoints.push(window[obj].endpoint);
                        }
                        if (window[obj] && window[obj].baseUrl) {
                            endpoints.push(window[obj].baseUrl);
                        }
                    });
                    
                    return endpoints;
                }
            """)
            
            if js_endpoints:
                print("🎯 Endpoints trouvés via JavaScript:")
                for endpoint in js_endpoints:
                    if endpoint:
                        print(f"   - {endpoint}")
            else:
                print("❌ Aucun endpoint trouvé via JavaScript")
                
        except Exception as e:
            print(f"⚠️ Erreur JavaScript: {e}")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    
    finally:
        await browser.close()
        print("\n🔒 Navigateur fermé")

if __name__ == "__main__":
    asyncio.run(inspect_mytools_endpoints())
