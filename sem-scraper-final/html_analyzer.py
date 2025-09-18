#!/usr/bin/env python3
"""
Analyseur HTML de la page de connexion MyToolsPlan
"""

import asyncio
from playwright.async_api import async_playwright
import config

async def analyze_html():
    """Analyse le HTML de la page de connexion"""
    print("🔍 ANALYSE HTML DE LA PAGE DE CONNEXION")
    print("=" * 60)
    
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            print(f"🌐 Navigation vers: {config.MYTOOLSPLAN_LOGIN_URL}")
            await page.goto(config.MYTOOLSPLAN_LOGIN_URL, wait_until="networkidle")
            await asyncio.sleep(5)
            
            print(f"✅ Page chargée: {page.url}")
            
            # Analyser tous les éléments input
            print(f"\n🔍 ANALYSE DES ÉLÉMENTS INPUT:")
            inputs = await page.query_selector_all('input')
            print(f"   Total des inputs: {len(inputs)}")
            
            for i, input_elem in enumerate(inputs):
                try:
                    input_type = await input_elem.get_attribute('type')
                    input_name = await input_elem.get_attribute('name')
                    input_id = await input_elem.get_attribute('id')
                    input_class = await input_elem.get_attribute('class')
                    input_placeholder = await input_elem.get_attribute('placeholder')
                    input_aria_label = await input_elem.get_attribute('aria-label')
                    
                    print(f"\n   Input {i+1}:")
                    print(f"     Type: {input_type}")
                    print(f"     Name: {input_name}")
                    print(f"     ID: {input_id}")
                    print(f"     Class: {input_class}")
                    print(f"     Placeholder: {input_placeholder}")
                    print(f"     Aria-label: {input_aria_label}")
                    
                    # Si c'est un input de type email ou text, c'est probablement le login
                    if input_type in ['email', 'text'] and (input_name or input_id or input_placeholder):
                        print(f"     🎯 CANDIDAT LOGIN DÉTECTÉ!")
                    
                except Exception as e:
                    print(f"     ❌ Erreur analyse input {i+1}: {e}")
            
            # Analyser tous les boutons
            print(f"\n🔍 ANALYSE DES BOUTONS:")
            buttons = await page.query_selector_all('button')
            print(f"   Total des boutons: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    button_type = await button.get_attribute('type')
                    button_text = await button.inner_text()
                    button_class = await button.get_attribute('class')
                    button_id = await button.get_attribute('id')
                    
                    print(f"\n   Bouton {i+1}:")
                    print(f"     Type: {button_type}")
                    print(f"     Texte: {button_text}")
                    print(f"     Class: {button_class}")
                    print(f"     ID: {button_id}")
                    
                    # Si c'est un bouton submit ou contient "login", c'est probablement le bouton de connexion
                    if button_type == 'submit' or 'login' in button_text.lower():
                        print(f"     🎯 CANDIDAT BOUTON CONNEXION DÉTECTÉ!")
                    
                except Exception as e:
                    print(f"     ❌ Erreur analyse bouton {i+1}: {e}")
            
            # Analyser les formulaires
            print(f"\n🔍 ANALYSE DES FORMULAIRES:")
            forms = await page.query_selector_all('form')
            print(f"     Total des formulaires: {len(forms)}")
            
            for i, form in enumerate(forms):
                try:
                    form_action = await form.get_attribute('action')
                    form_method = await form.get_attribute('method')
                    form_class = await form.get_attribute('class')
                    form_id = await form.get_attribute('id')
                    
                    print(f"\n   Formulaire {i+1}:")
                    print(f"     Action: {form_action}")
                    print(f"     Method: {form_method}")
                    print(f"     Class: {form_class}")
                    print(f"     ID: {form_id}")
                    
                except Exception as e:
                    print(f"     ❌ Erreur analyse formulaire {i+1}: {e}")
            
            # Sauvegarder le HTML pour analyse manuelle
            html_content = await page.content()
            with open('login_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"\n📄 HTML sauvegardé dans: login_page.html")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_html())
