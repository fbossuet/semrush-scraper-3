#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import os
import config

async def analyze_current_page():
    """Analyse la page actuelle pour identifier les nouveaux sélecteurs"""
    print("🔍 ANALYSE DE LA PAGE ACTUELLE MYTOOLSPLAN")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Configuration du navigateur
        os.environ['DISPLAY'] = ':99'
        os.system('Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &')
        await asyncio.sleep(2)
        
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                '--disable-web-security', '--disable-features=VizDisplayCompositor'
            ]
        )
        
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        try:
            # 1. AUTHENTIFICATION
            print("🔐 Authentification...")
            await page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_selector('input[name="amember_login"]', timeout=15000)
            await page.wait_for_selector('input[name="amember_pass"]', timeout=15000)
            await page.fill('input[name="amember_login"]', config.MYTOOLSPLAN_USERNAME)
            await page.fill('input[name="amember_pass"]', config.MYTOOLSPLAN_PASSWORD)
            await page.click('input[class="frm-submit"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            print("✅ Authentification réussie")
            
            # 2. NAVIGATION VERS UN DOMAINE TEST
            test_domain = "bratz.com"  # Domaine qui marchait dans les logs
            current_date = "202509"
            url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q={test_domain}&date={current_date}"
            
            print(f"🌐 Navigation vers: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            print("✅ Page chargée")
            
            # 3. SAUVEGARDE DU HTML POUR ANALYSE
            html_content = await page.content()
            with open("/tmp/current_page_analysis.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("💾 HTML sauvegardé dans /tmp/current_page_analysis.html")
            
            # 4. ANALYSE DES SÉLECTEURS EXISTANTS
            print("\n🔍 ANALYSE DES SÉLECTEURS EXISTANTS :")
            
            # Organic Traffic (marche)
            organic_element = await page.query_selector('a[data-path="overview.summary.click_organic_search_traffic"] span[data-ui-name="Link.Text"]')
            if organic_element:
                organic_text = await organic_element.inner_text()
                print(f"✅ Organic Traffic: '{organic_text}' (sélecteur VALIDE)")
            else:
                print("❌ Organic Traffic: sélecteur INVALIDE")
            
            # Bounce Rate (marche)
            bounce_element = await page.query_selector('a[data-path="overview.engagement_metrics.bounce_rate"] span[data-ui-name="Link.Text"]')
            if bounce_element:
                bounce_text = await bounce_element.inner_text()
                print(f"✅ Bounce Rate: '{bounce_text}' (sélecteur VALIDE)")
            else:
                print("❌ Bounce Rate: sélecteur INVALIDE")
            
            # Average Visit Duration (marche)
            duration_element = await page.query_selector('a[data-path="overview.engagement_metrics.visit_duration"] span[data-ui-name="Link.Text"]')
            if duration_element:
                duration_text = await duration_element.inner_text()
                print(f"✅ Average Visit Duration: '{duration_text}' (sélecteur VALIDE)")
            else:
                print("❌ Average Visit Duration: sélecteur INVALIDE")
            
            # 5. RECHERCHE DES NOUVEAUX SÉLECTEURS
            print("\n🔍 RECHERCHE DES NOUVEAUX SÉLECTEURS :")
            
            # Chercher tous les éléments avec data-path
            data_path_elements = await page.query_selector_all('[data-path]')
            print(f"📊 Éléments avec data-path trouvés: {len(data_path_elements)}")
            
            # Lister les data-path uniques
            data_paths = set()
            for elem in data_path_elements[:20]:  # Limiter à 20 pour éviter le spam
                try:
                    data_path = await elem.get_attribute('data-path')
                    if data_path:
                        data_paths.add(data_path)
                except:
                    pass
            
            print("📋 Data-paths trouvés:")
            for path in sorted(data_paths):
                print(f"  - {path}")
            
            # 6. RECHERCHE DES SÉLECTEURS BRANDED TRAFFIC
            print("\n🔍 RECHERCHE BRANDED TRAFFIC :")
            
            # Essayer différents sélecteurs
            branded_selectors = [
                'div[data-at="summary-branded-traffic"] > div > div > span[data-at="summary-value"][data-ui-name="Text"]',
                '[data-path*="branded"]',
                '[data-path*="traffic"]',
                'span:contains("Branded")',
                'div:contains("Branded")'
            ]
            
            for selector in branded_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"✅ Branded Traffic trouvé avec '{selector}': '{text}'")
                        break
                except:
                    continue
            else:
                print("❌ Aucun sélecteur Branded Traffic trouvé")
            
            # 7. RECHERCHE DES SÉLECTEURS CONVERSION
            print("\n🔍 RECHERCHE CONVERSION RATE :")
            
            conversion_selectors = [
                'div[name="conversion"] span[data-ui-name="Text"]',
                '[data-path*="conversion"]',
                '[data-path*="purchase"]',
                'span:contains("Conversion")',
                'div:contains("Conversion")'
            ]
            
            for selector in conversion_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"✅ Conversion Rate trouvé avec '{selector}': '{text}'")
                        break
                except:
                    continue
            else:
                print("❌ Aucun sélecteur Conversion Rate trouvé")
            
            # 8. RECHERCHE DES SÉLECTEURS PAID SEARCH
            print("\n🔍 RECHERCHE PAID SEARCH TRAFFIC :")
            
            paid_selectors = [
                'div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]',
                '[data-path*="paid"]',
                '[data-path*="search"]',
                'span:contains("Paid")',
                'div:contains("Paid")'
            ]
            
            for selector in paid_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"✅ Paid Search Traffic trouvé avec '{selector}': '{text}'")
                        break
                except:
                    continue
            else:
                print("❌ Aucun sélecteur Paid Search Traffic trouvé")
            
            # 9. RECHERCHE DES SÉLECTEURS VISITS
            print("\n🔍 RECHERCHE VISITS :")
            
            visits_selectors = [
                'div[name="visits"] span[data-ui-name="Text"]',
                '[data-path*="visits"]',
                '[data-path*="sessions"]',
                'span:contains("Visits")',
                'div:contains("Visits")'
            ]
            
            for selector in visits_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"✅ Visits trouvé avec '{selector}': '{text}'")
                        break
                except:
                    continue
            else:
                print("❌ Aucun sélecteur Visits trouvé")
            
            print("\n🎯 ANALYSE TERMINÉE !")
            print("📁 HTML sauvegardé dans /tmp/current_page_analysis.html")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        finally:
            await browser.close()
            os.system('pkill Xvfb 2>/dev/null')

if __name__ == "__main__":
    asyncio.run(analyze_current_page())
