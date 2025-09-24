#!/usr/bin/env python3
"""
Script simple pour scraper Paid Search Traffic sur 20 boutiques completed
Utilise la même logique d'authentification que le single worker
"""

import asyncio
import os
import time
import sqlite3
from playwright.async_api import async_playwright
import config

async def scrape_paid_traffic_20():
    print("🚀 SCRAPER PAID TRAFFIC - 20 BOUTIQUES COMPLETED")
    print("=" * 50)
    
    try:
        # Configuration Xvfb
        print("🖥️ Configuration Xvfb...")
        os.system("Xvfb :106 -screen 0 1920x1080x24 > /dev/null 2>&1 &")
        time.sleep(3)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas', '--no-first-run', '--no-zygote',
                '--disable-gpu', '--display=:106'
            ]
        )
        
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_default_timeout(60000)
        
        print("✅ Navigateur configuré")
        
        # Authentification - même méthode que le single worker
        print("🔐 Authentification MyToolsPlan...")
        await page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_load_state('networkidle')
        
        # Récupérer les credentials
        username, password = config.get_mytoolsplan_credentials()
        
        # Remplir les champs de login - mêmes sélecteurs que le single worker
        await page.fill('input[name="amember_login"]', username)
        await page.fill('input[name="amember_pass"]', password)
        
        # Soumettre le formulaire - même méthode que le single worker
        try:
            await page.click('input[type="submit"][class="frm-submit"]')
        except:
            await page.evaluate('document.querySelector("form[name=\"login\"]").submit()')
        
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Vérifier que nous sommes sur la page membre
        current_url = page.url
        print(f"✅ Login réussi, URL actuelle: {current_url}")
        
        if "member" not in current_url.lower():
            print("❌ Login échoué - Pas sur la page membre")
            await browser.close()
            return
        
        # Récupérer 20 boutiques completed sans Paid Search Traffic
        print("📊 Récupération des boutiques...")
        conn = sqlite3.connect('/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT s.id, s.shop_url 
            FROM shops s 
            LEFT JOIN analytics a ON s.id = a.shop_id 
            WHERE s.scraping_status = 'completed'
              AND (a.paid_search_traffic IS NULL 
                   OR a.paid_search_traffic = '' 
                   OR a.paid_search_traffic = 'null'
                   OR a.id IS NULL)
            ORDER BY s.id
            LIMIT 20
        """)
        
        shops = cursor.fetchall()
        print(f"📦 {len(shops)} boutiques trouvées")
        
        if not shops:
            print("✅ Aucune boutique à traiter")
            await browser.close()
            return
        
        # Traiter chaque boutique
        for i, (shop_id, shop_url) in enumerate(shops, 1):
            print(f"\n📦 Progression: {i}/{len(shops)} - {shop_url}")
            
            try:
                # Extraire le domaine
                domain = shop_url.replace('https://', '').replace('http://', '').split('/')[0]
                
                # Navigation vers Domain Overview
                overview_url = f"https://sam.mytoolsplan.xyz/analytics/overview/?searchType=domain&db=us&q={domain}&date=202506"
                await page.goto(overview_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Vérifier le titre de la page
                title = await page.title()
                print(f"🔍 Titre: {title}")
                
                # Attendre le chargement des métriques
                await page.wait_for_selector('div[data-at="do-summary-pt"]', timeout=10000)
                await asyncio.sleep(2)
                
                # Scraper Paid Search Traffic
                element = await page.query_selector('div[data-at="do-summary-pt"] a[data-at="main-number"] span[data-ui-name="Link.Text"]')
                
                if element:
                    paid_traffic = await element.inner_text()
                    paid_traffic_clean = paid_traffic.strip().lower()
                    
                    if paid_traffic_clean and paid_traffic_clean.endswith(('k', 'm')):
                        print(f"✅ Paid Search Traffic: {paid_traffic}")
                        
                        # Mettre à jour la base de données
                        cursor.execute("""
                            INSERT OR REPLACE INTO analytics 
                            (shop_id, paid_search_traffic, updated_at)
                            VALUES (?, ?, datetime('now'))
                        """, (shop_id, paid_traffic))
                        conn.commit()
                        print(f"💾 Base mise à jour pour shop_id {shop_id}")
                    else:
                        print(f"⚠️ Paid traffic invalide: '{paid_traffic}' - marqué comme 'na'")
                        cursor.execute("""
                            INSERT OR REPLACE INTO analytics 
                            (shop_id, paid_search_traffic, updated_at)
                            VALUES (?, ?, datetime('now'))
                        """, (shop_id, "na"))
                        conn.commit()
                else:
                    print("❌ Sélecteur Paid Search Traffic non trouvé")
                    cursor.execute("""
                        INSERT OR REPLACE INTO analytics 
                        (shop_id, paid_search_traffic, updated_at)
                        VALUES (?, ?, datetime('now'))
                    """, (shop_id, "Sélecteur non trouvé|Erreur"))
                    conn.commit()
                
            except Exception as e:
                print(f"❌ Erreur pour {shop_url}: {e}")
                cursor.execute("""
                    INSERT OR REPLACE INTO analytics 
                    (shop_id, paid_search_traffic, updated_at)
                    VALUES (?, ?, datetime('now'))
                """, (shop_id, f"Erreur: {str(e)}"))
                conn.commit()
        
        conn.close()
        await browser.close()
        print("\n🎉 Scraping terminé !")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_paid_traffic_20())
