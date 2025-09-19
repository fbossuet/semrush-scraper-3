#!/usr/bin/env python3
"""
Script de debug complet pour l'extraction de trafic par pays
Date: 2025-09-19
Description: Debug approfondi de la page de détail TrendTrack
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_market_extraction():
    """Debug complet de l'extraction de trafic par pays"""
    
    # ID de la boutique problématique
    shop_id = "14a9708a-2445-4c0f-8fe2-9dfbb400376a"
    shop_url = "burga.com"
    
    print(f"🔍 DEBUG COMPLET - Extraction trafic par pays")
    print(f"🆔 Boutique: {shop_url} (ID: {shop_id})")
    print("=" * 80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Mode headless pour serveur
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # URL de détail de la boutique (corrigée)
            detail_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/{shop_id}"
            print(f"🌐 Navigation vers: {detail_url}")
            
            await page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)  # Attendre le chargement complet
            
            print(f"✅ Page chargée")
            print(f"📄 Titre: {await page.title()}")
            print(f"🔗 URL finale: {page.url}")
            
            # 1. DEBUG: Vérifier le contenu de la page
            print(f"\n🔍 DEBUG 1: Contenu de la page")
            page_content = await page.content()
            print(f"📊 Taille du contenu: {len(page_content)} caractères")
            
            # Chercher tous les h3
            h3_elements = await page.locator('h3').all()
            print(f"📋 Nombre d'éléments h3 trouvés: {len(h3_elements)}")
            
            for i, h3 in enumerate(h3_elements):
                try:
                    text = await h3.text_content()
                    print(f"  h3[{i}]: '{text}'")
                except:
                    print(f"  h3[{i}]: [erreur lecture]")
            
            # 2. DEBUG: Chercher spécifiquement "Trafic" ou "Traffic"
            print(f"\n🔍 DEBUG 2: Recherche de 'Trafic'/'Traffic'")
            trafic_elements = await page.locator('text=/trafic|traffic/i').all()
            print(f"📋 Éléments contenant 'trafic'/'traffic': {len(trafic_elements)}")
            
            for i, elem in enumerate(trafic_elements):
                try:
                    text = await elem.text_content()
                    tag_name = await elem.evaluate('el => el.tagName')
                    print(f"  {tag_name}[{i}]: '{text}'")
                except:
                    print(f"  elem[{i}]: [erreur lecture]")
            
            # 3. DEBUG: Vérifier les sélecteurs spécifiques
            print(f"\n🔍 DEBUG 3: Test des sélecteurs spécifiques")
            selectors = [
                'h3:has-text("Trafic par pays")',
                'h3:has-text("Traffic by Country")',
                'h3.font-semibold.tracking-tight.text-lg:has-text("Trafic")',
                'h3.font-semibold.tracking-tight.text-lg:has-text("Traffic")',
                'h3:has-text("Trafic")',
                'h3:has-text("Traffic")',
                '[class*="traffic"]',
                '[class*="country"]',
                '[class*="market"]'
            ]
            
            for selector in selectors:
                try:
                    count = await page.locator(selector).count()
                    print(f"  {selector}: {count} éléments")
                    if count > 0:
                        for i in range(min(count, 3)):  # Max 3 éléments
                            try:
                                text = await page.locator(selector).nth(i).text_content()
                                print(f"    [{i}]: '{text}'")
                            except:
                                print(f"    [{i}]: [erreur lecture]")
                except Exception as e:
                    print(f"  {selector}: ERREUR - {e}")
            
            # 4. DEBUG: Vérifier la structure des cartes
            print(f"\n🔍 DEBUG 4: Structure des cartes")
            cards = await page.locator('div[class*="bg-card"]').all()
            print(f"📋 Nombre de cartes bg-card: {len(cards)}")
            
            for i, card in enumerate(cards):
                try:
                    # Chercher les h3 dans cette carte
                    h3_in_card = await card.locator('h3').all()
                    print(f"  Carte[{i}]: {len(h3_in_card)} h3")
                    for j, h3 in enumerate(h3_in_card):
                        try:
                            text = await h3.text_content()
                            print(f"    h3[{j}]: '{text}'")
                        except:
                            print(f"    h3[{j}]: [erreur lecture]")
                except:
                    print(f"  Carte[{i}]: [erreur lecture]")
            
            # 5. DEBUG: Vérifier les éléments avec drapeaux/pays
            print(f"\n🔍 DEBUG 5: Éléments avec drapeaux/pays")
            flag_elements = await page.locator('img[alt]').all()
            print(f"📋 Nombre d'images avec alt: {len(flag_elements)}")
            
            for i, img in enumerate(flag_elements):
                try:
                    alt = await img.get_attribute('alt')
                    if alt and any(country in alt.lower() for country in ['us', 'uk', 'de', 'ca', 'au', 'fr', 'usa', 'gb']):
                        print(f"  img[{i}]: alt='{alt}'")
                except:
                    pass
            
            # 6. DEBUG: Sauvegarder le HTML pour analyse
            print(f"\n🔍 DEBUG 6: Sauvegarde du HTML")
            html_file = f"debug_page_{shop_id}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_content)
            print(f"💾 HTML sauvegardé dans: {html_file}")
            
            # 7. DEBUG: Vérifier les erreurs de console
            print(f"\n🔍 DEBUG 7: Erreurs de console")
            console_messages = []
            
            def handle_console(msg):
                console_messages.append(f"{msg.type}: {msg.text}")
            
            page.on("console", handle_console)
            await page.wait_for_timeout(2000)  # Attendre les messages
            
            if console_messages:
                print(f"📋 Messages de console ({len(console_messages)}):")
                for msg in console_messages[-10:]:  # 10 derniers messages
                    print(f"  {msg}")
            else:
                print("  Aucun message de console")
            
            print(f"\n🎯 RÉSUMÉ DU DEBUG")
            print(f"  - Page chargée: ✅")
            print(f"  - H3 trouvés: {len(h3_elements)}")
            print(f"  - Éléments 'trafic': {len(trafic_elements)}")
            print(f"  - Cartes bg-card: {len(cards)}")
            print(f"  - Images avec alt: {len(flag_elements)}")
            print(f"  - HTML sauvegardé: {html_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors du debug: {e}")
        finally:
            await context.close()
            await browser.close()

def main():
    """Fonction principale"""
    print("🔍 DEBUG COMPLET - Extraction trafic par pays")
    print("=" * 80)
    
    try:
        asyncio.run(debug_market_extraction())
    except KeyboardInterrupt:
        print("\n⏹️ Debug interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du debug: {e}")

if __name__ == "__main__":
    main()
