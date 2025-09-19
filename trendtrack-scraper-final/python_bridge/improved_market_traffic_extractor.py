#!/usr/bin/env python3
"""
Extracteur amélioré de trafic par pays pour TrendTrack
Date: 2025-09-19
Description: Version améliorée basée sur le script proposé, adaptée à notre écosystème
"""

import asyncio
import re
from typing import Iterable, Dict, Optional
from playwright.async_api import async_playwright

class ImprovedMarketTrafficExtractor:
    """Extracteur amélioré de trafic par pays"""
    
    DEFAULT_TARGETS = ["us", "uk", "de", "ca", "au", "fr"]
    
    ALIASES = {
        "gb": "uk",
        "uk": "uk", 
        "usa": "us",
        "united states": "us",
        "united kingdom": "uk",
        "germany": "de",
        "canada": "ca",
        "australia": "au",
        "france": "fr"
    }
    
    def __init__(self):
        self.targets = self.DEFAULT_TARGETS
    
    def canonical(self, code: Optional[str]) -> str:
        """Normalise le code pays"""
        if not code:
            return ""
        c = code.strip().lower()
        return self.ALIASES.get(c, c)
    
    def parse_int(self, s: Optional[str]) -> int:
        """Parse un entier depuis une chaîne, ignore les caractères non-numériques"""
        if not s:
            return 0
        digits = re.sub(r"[^0-9]", "", s)
        return int(digits) if digits else 0
    
    async def scrape_market_traffic(self, page, targets: Iterable[str] = None) -> Dict[str, Optional[int]]:
        """
        Extrait le trafic par pays depuis la page TrendTrack
        
        Args:
            page: Page Playwright
            targets: Liste des codes pays cibles
            
        Returns:
            Dict avec les clés market_XX et valeurs numériques ou None
        """
        if targets is None:
            targets = self.targets
            
        print(f"🌍 Extraction trafic par pays améliorée...")
        
        try:
            # Attendre le bloc "Trafic par pays" avec plusieurs sélecteurs
            selectors = [
                'h3:has-text("Trafic par pays")',
                'h3:has-text("Traffic by Country")',
                'h3.font-semibold.tracking-tight.text-lg:has-text("Trafic")',
                'h3.font-semibold.tracking-tight.text-lg:has-text("Traffic")'
            ]
            
            section_found = False
            working_selector = None
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, state="visible", timeout=5000)
                    print(f"✅ Section trouvée avec le sélecteur: {selector}")
                    section_found = True
                    working_selector = selector
                    break
                except Exception as e:
                    print(f"⚠️ Sélecteur {selector} non trouvé, essai suivant...")
            
            if not section_found:
                print("⚠️ Section 'Trafic par pays' non trouvée sur cette page")
                return {f"market_{t}": None for t in targets}
            
            # Localiser la carte contenant les données
            card = page.locator(working_selector).locator(
                'xpath=ancestor::div[contains(@class,"bg-card")]'
            ).first
            
            # Lignes pays
            rows = card.locator("div.flex.gap-2.w-full.items-center")
            count = await rows.count()
            
            print(f"📊 {count} lignes de pays trouvées")
            
            observed = {}  # ex: {"us": 175942, "au": 18555284}
            
            for i in range(count):
                row = rows.nth(i)
                
                # Code pays via alt du drapeau ou fallback sur le premier <p> gauche
                code = await row.locator("img[alt]").first.get_attribute("alt")
                if not code:
                    code = await row.locator("div.flex.justify-between > p").first.text_content()
                
                code = self.canonical(code)
                if not code:
                    continue
                
                # Valeur (le premier <p> avant le %)
                value_text = await row.locator("div.flex.justify-between div.items-center > p").first.text_content()
                value = self.parse_int(value_text)
                
                # On enregistre uniquement si une valeur numérique est présente
                if value > 0:
                    observed[code] = value
                    print(f"  📍 {code.upper()}: {value:,}")
            
            targets = [t.lower() for t in targets]
            
            if observed:
                # Au moins une valeur trouvée: on met 0 pour les cibles manquantes
                result = {f"market_{t}": observed.get(t, 0) for t in targets}
                print(f"✅ Trafic par pays extrait: {len(observed)} pays trouvés")
            else:
                # Aucune donnée trouvée: on ne force pas à 0 (None pour signaler "pas de data")
                result = {f"market_{t}": None for t in targets}
                print("⚠️ Aucune donnée de trafic par pays trouvée")
            
            return result
            
        except Exception as error:
            print(f"❌ Erreur lors de l'extraction du trafic par pays: {error}")
            return {f"market_{t}": None for t in targets}
    
    async def extract_for_shop(self, page, shop_id: str, shop_url: str) -> Dict[str, Optional[int]]:
        """
        Extrait le trafic par pays pour une boutique spécifique
        
        Args:
            page: Page Playwright
            shop_id: ID de la boutique
            shop_url: URL de la boutique
            
        Returns:
            Dict avec les données de trafic par pays
        """
        print(f"🌍 Extraction trafic par pays pour: {shop_url}")
        
        try:
            # Naviguer vers la page de détail de la boutique
            detail_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/websites/{shop_id}"
            await page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Extraire les données de trafic
            market_data = await self.scrape_market_traffic(page)
            
            return market_data
            
        except Exception as error:
            print(f"❌ Erreur lors de l'extraction pour {shop_url}: {error}")
            return {f"market_{t}": None for t in self.targets}

# Fonction de compatibilité avec l'écosystème existant
async def extract_market_traffic_improved(page, shop_id: str = None, shop_url: str = None) -> Dict[str, Optional[int]]:
    """
    Fonction de compatibilité pour l'intégration avec l'écosystème existant
    
    Args:
        page: Page Playwright
        shop_id: ID de la boutique (optionnel)
        shop_url: URL de la boutique (optionnel)
        
    Returns:
        Dict avec les données de trafic par pays
    """
    extractor = ImprovedMarketTrafficExtractor()
    
    if shop_id and shop_url:
        return await extractor.extract_for_shop(page, shop_id, shop_url)
    else:
        return await extractor.scrape_market_traffic(page)

# Test standalone
async def main():
    """Test standalone du script"""
    url = "https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/websites/14a9708a-2445-4c0f-8fe2-9dfbb400376a"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle")
            
            extractor = ImprovedMarketTrafficExtractor()
            data = await extractor.scrape_market_traffic(page, targets=["us","uk","de","ca","au","fr"])
            
            print("📊 Résultat de l'extraction:")
            for key, value in data.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

