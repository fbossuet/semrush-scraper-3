#!/usr/bin/env python3
"""
Extracteur Python pour les données de trafic par pays
Utilisé comme pont depuis JavaScript
"""

import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketTrafficExtractor:
    """Extracteur pour les données de trafic par pays depuis TrendTrack"""
    
    def __init__(self):
        self.DEFAULT_TARGETS = ["us", "uk", "de", "ca", "au", "fr"]
        self.ALIASES = {
            "gb": "uk",
            "uk": "uk", 
            "usa": "us",
        }
    
    def canonical(self, code):
        """Normalise le code pays"""
        if not code:
            return ""
        c = code.strip().lower()
        return self.ALIASES.get(c, c)
    
    def parse_int(self, s):
        """Parse un entier depuis une chaîne"""
        if not s:
            return 0
        import re
        digits = re.sub(r"[^0-9]", "", s)
        return int(digits) if digits else 0
    
    async def scrape_market_traffic(self, page, targets=None):
        """
        Scrape les données de trafic par pays depuis la page TrendTrack
        """
        if targets is None:
            targets = self.DEFAULT_TARGETS
            
        try:
            # Attendre le bloc "Trafic par pays"
            await page.wait_for_selector('h3:has-text("Trafic par pays")', state="visible", timeout=10000)
            
            # Localiser la carte contenant les données
            card = page.locator('h3:has-text("Trafic par pays")').locator(
                'xpath=ancestor::div[contains(@class,"bg-card")]'
            ).first
            
            # Récupérer les lignes de pays
            rows = page.locator("div.flex.gap-2.w-full.items-center")
            count = await rows.count()
            
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
                value_text = await row.locator("div.flex.justify-between div.flex.items-center.gap-1 p").first.text_content()
                value = self.parse_int(value_text)
                
                # Enregistrer uniquement si une valeur numérique est présente
                if value is not None:
                    observed[code] = value
            
            targets = [t.lower() for t in targets]
            
            if observed:
                # Au moins une valeur trouvée: mettre 0 pour les cibles manquantes
                result = {f"market_{t}": observed.get(t, 0) for t in targets}
            else:
                # Aucune donnée trouvée: mettre None pour signaler "pas de data"
                result = {f"market_{t}": None for t in targets}
                
            return result
            
        except Exception as error:
            logger.error(f"❌ Erreur lors du scraping du trafic par pays: {error}")
            # Retourner None pour tous les targets en cas d'erreur
            return {f"market_{t}": None for t in targets}
    
    async def extract_market_traffic_for_shop(self, shop_url, targets=None):
        """
        Extrait les données de trafic par pays pour une boutique spécifique
        """
        if targets is None:
            targets = self.DEFAULT_TARGETS
            
        logger.info(f"🌍 Navigation vers {shop_url} pour extraire le trafic par pays...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Construire l'URL TrendTrack pour la page détail de cette boutique
                # Format: https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/[shop_id]
                # IMPORTANT: shop_url contient l'ID de la boutique, pas l'URL du site
                # Exemple: shop_url = "5c1f6e07-41d0-4607-a48c-386098e20e9d"
                if shop_url.startswith('http'):
                    # Si c'est une URL complète, extraire l'ID depuis l'URL
                    logger.warning(f"⚠️ URL complète reçue au lieu d'ID: {shop_url}")
                    # Pour l'instant, utiliser une page générique
                    trendtrack_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops"
                else:
                    # C'est un ID de boutique
                    trendtrack_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/{shop_url}"
                
                logger.info(f"🌐 Navigation vers page détail TrendTrack: {trendtrack_url}")
                await page.goto(trendtrack_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)  # Pause humaine
                
                market_data = await self.scrape_market_traffic(page, targets)
                
                await browser.close()
                
                return {
                    "shop_url": shop_url,
                    **market_data,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as error:
            logger.error(f"❌ Erreur lors de l'extraction du trafic par pays pour {shop_url}: {error}")
            return {
                "shop_url": shop_url,
                **{f"market_{t}": None for t in targets},
                "extracted_at": datetime.now(timezone.utc).isoformat()
            }

async def main():
    """Point d'entrée principal pour l'appel depuis JavaScript"""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "URL du shop requise"}))
        sys.exit(1)
    
    shop_url = sys.argv[1]
    targets = json.loads(sys.argv[2]) if len(sys.argv) > 2 else ["us", "uk", "de", "ca", "au", "fr"]
    
    extractor = MarketTrafficExtractor()
    result = await extractor.extract_market_traffic_for_shop(shop_url, targets)
    
    # Output JSON pour JavaScript
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
