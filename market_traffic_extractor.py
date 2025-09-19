#!/usr/bin/env python3
"""
Extracteur Python pour les données de trafic par pays
Utilisé comme pont depuis les scrapers pour récupérer les métriques market_*
"""

import sys
import json
import asyncio
import logging
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketTrafficExtractor:
    """Extracteur pour les données de trafic par pays"""
    
    def __init__(self):
        self.timeout = 30000  # 30 secondes
    
    def parse_float(self, s):
        """Parse un float depuis une chaîne"""
        if not s:
            return None
        try:
            # Supprimer les caractères non-numériques sauf le point et la virgule
            cleaned = re.sub(r'[^\d.,]', '', str(s))
            if not cleaned:
                return None
            # Remplacer la virgule par un point pour les décimales
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except:
            return None
    
    async def extract_market_traffic(self, shop_url, targets=["us", "uk", "de", "ca", "au", "fr"]):
        """
        Extrait les données de trafic par pays d'une boutique
        """
        logger.info(f"🌍 Extraction trafic par pays pour: {shop_url}")
        
        try:
            async with async_playwright() as p:
                # Lancer le navigateur
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # CORRECTION: Construire l'URL TrendTrack pour cette boutique
                # Format: https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/[shop_id]
                # Pour l'instant, on utilise une URL générique - à améliorer avec l'ID réel
                trendtrack_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops"
                logger.info(f"🌐 Navigation vers TrendTrack: {trendtrack_url}")
                await page.goto(trendtrack_url, wait_until='domcontentloaded', timeout=30000)
                
                # Initialiser les résultats
                market_data = {
                    "market_us": None,
                    "market_uk": None,
                    "market_de": None,
                    "market_ca": None,
                    "market_au": None,
                    "market_fr": None,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Pour l'instant, retourner des données simulées
                # TODO: Implémenter l'extraction réelle depuis TrendTrack
                logger.info("⚠️ Extraction simulée - à implémenter avec l'API TrendTrack réelle")
                
                await browser.close()
                
                logger.info(f"✅ Données de trafic extraites: {json.dumps(market_data, indent=2)}")
                return market_data
                
        except Exception as e:
            logger.error(f"❌ Erreur extraction trafic par pays: {e}")
            return {
                "market_us": None,
                "market_uk": None,
                "market_de": None,
                "market_ca": None,
                "market_au": None,
                "market_fr": None,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

async def main():
    """Fonction principale pour tester l'extracteur"""
    if len(sys.argv) < 2:
        print("Usage: python3 market_traffic_extractor.py <shop_url>")
        sys.exit(1)
    
    shop_url = sys.argv[1]
    extractor = MarketTrafficExtractor()
    
    try:
        result = await extractor.extract_market_traffic(shop_url)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())