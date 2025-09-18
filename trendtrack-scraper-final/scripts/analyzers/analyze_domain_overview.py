#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import os
import time

async def analyze_domain_overview():
    """Analyse complète de la page Domain Overview pour identifier les sélecteurs"""
    
    print("🔍 ANALYSE PAGE DOMAIN OVERVIEW")
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
            # 1. LOGIN
            print("🔐 Étape 1: Connexion...")
            await page.goto('https://app.mytoolsplan.com/login', timeout=30000)
            await page.fill('input[name="amember_login"]', 'Semrush3my')
            await page.fill('input[name="amember_pass"]', 'afhznmd455!fhIhh7FHkd')
            await page.click('input[class="frm-submit"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            print("✅ Login réussi")
            
            # 2. NAVIGATION VERS DOMAIN OVERVIEW
            print("\n🌐 Étape 2: Navigation vers Domain Overview...")
            test_domain = "skims.com"
            await page.goto(f'https://app.mytoolsplan.com/domain-overview?domain={test_domain}', timeout=30000)
            print("✅ Page Domain Overview chargée")
            
            # 3. ANALYSE COMPLÈTE DE LA PAGE
            print("\n📊 Étape 3: Analyse complète de la page...")
            
            # Récupérer tout le HTML
            html_content = await page.content()
            
            # Analyser les éléments de texte
            print("\n🔍 ÉLÉMENTS DE TEXTE TROUVÉS:")
            print("-" * 30)
            
            # Chercher des patterns de métriques
            text_elements = await page.query_selector_all('*')
            metric_keywords = [
                'traffic', 'bounce', 'duration', 'conversion', 'visit', 'branded', 'paid'
            ]
            
            found_metrics = []
            for element in text_elements[:100]:  # Limiter pour éviter la surcharge
                try:
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        text_lower = text.lower()
                        for keyword in metric_keywords:
                            if keyword in text_lower:
                                found_metrics.append((text.strip()[:50], element.tag_name))
                                break
                except:
                    continue
            
            # Afficher les métriques trouvées
            for text, tag in found_metrics[:20]:
                print(f"   {tag}: '{text}'")
            
            # 4. ANALYSE DES STRUCTURES DE DONNÉES
            print("\n🏗️ ÉTUDE DES STRUCTURES DE DONNÉES:")
            print("-" * 30)
            
            # Chercher des tableaux
            tables = await page.query_selector_all('table')
            print(f"📋 Nombre de tableaux trouvés: {len(tables)}")
            
            for i, table in enumerate(tables[:3]):
                try:
                    rows = await table.query_selector_all('tr')
                    print(f"   Tableau {i+1}: {len(rows)} lignes")
                    
                    # Analyser les en-têtes
                    if rows:
                        headers = await rows[0].query_selector_all('th, td')
                        header_texts = []
                        for header in headers[:5]:
                            try:
                                text = await header.text_content()
                                header_texts.append(text.strip()[:20])
                            except:
                                continue
                        print(f"      En-têtes: {header_texts}")
                except Exception as e:
                    print(f"      Erreur analyse tableau {i+1}: {e}")
            
            # 5. ANALYSE DES DIVS ET SECTIONS
            print("\n📦 ANALYSE DES SECTIONS:")
            print("-" * 30)
            
            # Chercher des divs avec des classes spécifiques
            divs = await page.query_selector_all('div[class*="metric"], div[class*="data"], div[class*="stat"]')
            print(f"📊 Divs avec classes métriques: {len(divs)}")
            
            for i, div in enumerate(divs[:5]):
                try:
                    class_attr = await div.get_attribute('class')
                    text = await div.text_content()
                    print(f"   Div {i+1} (class='{class_attr}'): '{text.strip()[:50]}'")
                except:
                    continue
            
            # 6. ANALYSE DES SPANS ET LABELS
            print("\n🏷️ ANALYSE DES LABELS ET SPANS:")
            print("-" * 30)
            
            spans = await page.query_selector_all('span, label')
            metric_spans = []
            
            for span in spans[:50]:
                try:
                    text = await span.text_content()
                    if text and any(keyword in text.lower() for keyword in metric_keywords):
                        metric_spans.append(text.strip()[:40])
                except:
                    continue
            
            for span_text in metric_spans[:10]:
                print(f"   Span: '{span_text}'")
            
            # 7. SAUVEGARDE DU HTML POUR ANALYSE MANUELLE
            print("\n💾 SAUVEGARDE DU HTML...")
            with open('/tmp/domain_overview_analysis.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("✅ HTML sauvegardé dans /tmp/domain_overview_analysis.html")
            
            # 8. RECHERCHE DE PATTERNS SPÉCIFIQUES
            print("\n🎯 RECHERCHE DE PATTERNS SPÉCIFIQUES:")
            print("-" * 30)
            
            # Chercher des patterns comme "Organic Traffic: 2.5M"
            pattern_selectors = [
                'text=/.*[Tt]raffic.*:/',
                'text=/.*[Bb]ounce.*:/',
                'text=/.*[Dd]uration.*:/',
                'text=/.*[Cc]onversion.*:/',
                'text=/.*[Vv]isit.*:/'
            ]
            
            for pattern in pattern_selectors:
                try:
                    elements = await page.query_selector_all(pattern)
                    if elements:
                        print(f"   Pattern '{pattern}': {len(elements)} éléments trouvés")
                        for j, elem in enumerate(elements[:2]):
                            text = await elem.text_content()
                            print(f"      {j+1}: '{text.strip()[:50]}'")
                except Exception as e:
                    print(f"   Pattern '{pattern}': Erreur - {e}")
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            print(f"   Type: {type(e).__name__}")
        
        finally:
            await browser.close()
            os.system('pkill Xvfb 2>/dev/null')
    
    print(f"\n🎯 ANALYSE TERMINÉE")
    print("=" * 50)
    print("📝 Vérifiez le fichier HTML sauvegardé pour une analyse manuelle")

if __name__ == "__main__":
    asyncio.run(analyze_domain_overview())
