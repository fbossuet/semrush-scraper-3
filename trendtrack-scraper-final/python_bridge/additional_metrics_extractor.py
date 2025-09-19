#!/usr/bin/env python3
"""
Extracteur Python pour les métriques supplémentaires des boutiques
Utilisé comme pont depuis JavaScript pour récupérer:
- pixel_google
- pixel_facebook
- aov
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

class AdditionalMetricsExtractor:
    """Extracteur pour les métriques supplémentaires des boutiques"""
    
    def __init__(self):
        self.timeout = 30000  # 30 secondes
    
    def parse_int(self, s):
        """Parse un entier depuis une chaîne"""
        if not s:
            return None
        try:
            # Supprimer les caractères non-numériques sauf le point et la virgule
            cleaned = re.sub(r'[^\d.,]', '', str(s))
            if not cleaned:
                return None
            # Remplacer la virgule par un point pour les décimales
            cleaned = cleaned.replace(',', '.')
            return int(float(cleaned))
        except:
            return None
    
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
    
    async def extract_additional_metrics(self, shop_url):
        """
        Extrait les métriques supplémentaires d'une boutique
        """
        logger.info(f"🔍 Extraction des métriques supplémentaires pour: {shop_url}")
        
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
                
                # Aller sur la page de la boutique
                # Construire l'URL TrendTrack pour cette boutique
                # Format: https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/[shop_id]
                # Pour l'instant, on utilise une URL générique - à améliorer avec l'ID réel
                trendtrack_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops"
                logger.info(f"🌐 Navigation vers TrendTrack: {trendtrack_url}")
                await page.goto(trendtrack_url, timeout=self.timeout)
                await page.wait_for_load_state('networkidle', timeout=10000)  # Timeout réduit à 10s
                
                # Initialiser les résultats
                metrics = {
                    
                    "pixel_google": None,
                    "pixel_facebook": None,
                    "aov": None,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
                
                # 2. Détecter les pixels Google Analytics et Facebook
                try:
                    # Vérifier la présence de Google Analytics
                    google_scripts = await page.query_selector_all('script[src*="google-analytics"], script[src*="gtag"]')
                    if google_scripts:
                        metrics["pixel_google"] = "oui"
                        logger.info("✅ Pixel Google détecté")
                    else:
                        # Vérifier aussi dans le contenu des scripts
                        page_content = await page.content()
                        if 'gtag' in page_content or 'google-analytics' in page_content:
                            metrics["pixel_google"] = "oui"
                            logger.info("✅ Pixel Google détecté dans le contenu")
                        else:
                            metrics["pixel_google"] = "non"
                    
                    # Vérifier la présence de Facebook Pixel
                    facebook_scripts = await page.query_selector_all('script[src*="facebook"]')
                    if facebook_scripts:
                        metrics["pixel_facebook"] = "oui"
                        logger.info("✅ Pixel Facebook détecté")
                    else:
                        # Vérifier aussi dans le contenu des scripts
                        if 'fbq' in page_content or 'facebook' in page_content:
                            metrics["pixel_facebook"] = "oui"
                            logger.info("✅ Pixel Facebook détecté dans le contenu")
                        else:
                            metrics["pixel_facebook"] = "non"
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur détection pixels: {e}")
                    metrics["pixel_google"] = "non"
                    metrics["pixel_facebook"] = "non"
                
                    logger.warning(f"⚠️ Erreur extraction AOV: {e}")
                
                await browser.close()
                
                logger.info(f"✅ Métriques extraites: {json.dumps(metrics, indent=2)}")
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Erreur extraction métriques supplémentaires: {e}")
            return {
                
                "pixel_google": None,
                "pixel_facebook": None,
                "aov": None,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

async def main():
    """Fonction principale pour tester l'extracteur"""
    if len(sys.argv) < 2:
        print("Usage: python3 additional_metrics_extractor.py <shop_url>")
        sys.exit(1)
    
    shop_url = sys.argv[1]
    extractor = AdditionalMetricsExtractor()
    
    try:
        result = await extractor.extract_additional_metrics(shop_url)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
