#!/usr/bin/env python3
import sqlite3
import asyncio
from playwright.async_api import async_playwright
import os
import time

async def diagnostic_boutique():
    """Diagnostic complet d'une boutique partial"""
    
    # 1. VÉRIFIER LA BASE - Trouver une boutique partial
    db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 DIAGNOSTIC BOUTIQUE PARTIAL")
    print("=" * 50)
    
    # Trouver une boutique partial avec des métriques manquantes
    cursor.execute("""
        SELECT s.id, s.shop_name, s.shop_url, s.scraping_status,
               a.organic_traffic, a.bounce_rate, a.avg_visit_duration,
               a.branded_traffic, a.conversion_rate, a.paid_search_traffic,
               a.visits, a.traffic, a.percent_branded_traffic
        FROM shops s 
        JOIN analytics a ON s.id = a.shop_id 
        WHERE s.scraping_status = 'partial'
        AND (a.organic_traffic = 'na' OR a.bounce_rate = 'na' OR a.avg_visit_duration = 'na')
        LIMIT 1
    """)
    
    shop = cursor.fetchone()
    if not shop:
        print("❌ Aucune boutique partial avec métriques manquantes trouvée")
        return
    
    shop_id, name, url, status, *metrics = shop
    print(f"📊 BOUTIQUE TESTÉE: {name} ({url})")
    print(f"🆔 ID: {shop_id}, Statut: {status}")
    print(f"📈 MÉTRIQUES ACTUELLES:")
    metric_names = ['organic_traffic', 'bounce_rate', 'avg_visit_duration', 'branded_traffic', 
                   'conversion_rate', 'paid_search_traffic', 'visits', 'traffic', 'percent_branded_traffic']
    
    for i, metric in enumerate(metrics):
        print(f"   {metric_names[i]}: '{metric}'")
    
    conn.close()
    
    # 2. TESTER LA CONNEXION ET LES SELECTEURS
    print(f"\n🔐 TEST CONNEXION ET SELECTEURS")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Configuration Xvfb
        os.environ['DISPLAY'] = ':99'
        os.system('Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &')
        time.sleep(2)
        
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        page = await browser.new_page()
        
        try:
            print("🌐 Test 1: Connexion à MyToolsPlan...")
            await page.goto('https://app.mytoolsplan.com/login', timeout=30000)
            print("✅ Page de login chargée")
            
            # Vérifier les selecteurs de login
            print("🔍 Test 2: Vérification des selecteurs de login...")
            try:
                email_input = await page.wait_for_selector('input[name="amember_login"], input[name="email"], #email', timeout=5000)
                print("✅ Sélecteur email trouvé")
            except:
                print("❌ Sélecteur email NON TROUVÉ")
                print("   Sélecteurs disponibles:")
                inputs = await page.query_selector_all('input')
                for inp in inputs[:5]:
                    attrs = await inp.get_attribute('type') or await inp.get_attribute('name') or await inp.get_attribute('id')
                    print(f"      {attrs}")
            
            try:
                password_input = await page.wait_for_selector('input[name="amember_pass"], input[name="password"], #password', timeout=5000)
                print("✅ Sélecteur password trouvé")
            except:
                print("❌ Sélecteur password NON TROUVÉ")
            
            # Test de login
            print("🔐 Test 3: Tentative de login...")
            try:
                await page.fill('input[name="amember_login"]', 'Semrush3my')
                await page.fill('input[name="amember_pass"]', 'afhznmd455!fhIhh7FHkd')
                await page.click('button[type="submit"], input[type="submit"]')
                
                # Attendre la redirection
                await page.wait_for_load_state('networkidle', timeout=30000)
                current_url = page.url
                print(f"✅ Login tenté, URL actuelle: {current_url}")
                
                if 'member' in current_url:
                    print("✅ Login réussi - Page membre détectée")
                else:
                    print("⚠️ Login peut-être échoué - URL inattendue")
                    
            except Exception as e:
                print(f"❌ Erreur lors du login: {e}")
            
            # Test de navigation vers Domain Overview
            print(f"\n🌐 Test 4: Navigation vers Domain Overview pour {url}...")
            try:
                await page.goto(f'https://app.mytoolsplan.com/domain-overview?domain={url.replace("https://", "").replace("http://", "")}', timeout=30000)
                print("✅ Page Domain Overview chargée")
                
                # Vérifier les selecteurs des métriques
                print("🔍 Test 5: Vérification des selecteurs de métriques...")
                
                selectors_to_test = [
                    'text=Organic Traffic',
                    'text=Bounce Rate', 
                    'text=Average Visit Duration',
                    'text=Branded Traffic',
                    'text=Conversion Rate',
                    'text=Paid Search Traffic',
                    'text=Visits',
                    'text=Traffic',
                    'text=Percent Branded Traffic'
                ]
                
                for selector in selectors_to_test:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            print(f"✅ Sélecteur trouvé: {selector}")
                        else:
                            print(f"❌ Sélecteur NON trouvé: {selector}")
                    except:
                        print(f"❌ Sélecteur NON trouvé: {selector}")
                
                # Test de récupération d'une métrique
                print("\n📊 Test 6: Tentative de récupération d'une métrique...")
                try:
                    # Essayer de récupérer Organic Traffic
                    organic_element = await page.query_selector('text=Organic Traffic')
                    if organic_element:
                        # Chercher la valeur associée
                        parent = await organic_element.query_selector('xpath=..')
                        if parent:
                            text_content = await parent.text_content()
                            print(f"✅ Contenu trouvé: {text_content[:100]}...")
                        else:
                            print("⚠️ Parent de l'élément non trouvé")
                    else:
                        print("❌ Élément Organic Traffic non trouvé")
                        
                except Exception as e:
                    print(f"❌ Erreur lors de la récupération: {e}")
                
            except Exception as e:
                print(f"❌ Erreur lors de la navigation Domain Overview: {e}")
                print(f"   Détail: {type(e).__name__}")
                
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            print(f"   Type: {type(e).__name__}")
        
        finally:
            await browser.close()
            os.system('pkill Xvfb 2>/dev/null')
    
    print(f"\n🎯 DIAGNOSTIC TERMINÉ")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(diagnostic_boutique())
