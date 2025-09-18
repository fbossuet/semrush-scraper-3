#!/usr/bin/env python3
"""
Extracteur Python pour les métriques supplémentaires des boutiques
Utilisé comme pont depuis JavaScript pour récupérer:
- total_products
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
                await page.goto(shop_url, timeout=self.timeout)
                await page.wait_for_load_state('networkidle', timeout=10000)  # Timeout réduit à 10s
                
                # Initialiser les résultats
                metrics = {
                    "total_products": None,
                    "pixel_google": None,
                    "pixel_facebook": None,
                    "aov": None,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
                # 1. Extraire le nombre total de produits
                try:
                    # Chercher des sélecteurs communs pour le nombre de produits
                    product_selectors = [
                        '[data-testid*="product"]',
                        '.product-count',
                        '.total-products',
                        '[class*="product"][class*="count"]',
                        'span:contains("products")',
                        'div:contains("items")'
                    ]
                    
                    for selector in product_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text:
                                    # Extraire les nombres du texte
                                    numbers = re.findall(r'\d+', text)
                                    if numbers:
                                        metrics["total_products"] = self.parse_int(numbers[0])
                                        logger.info(f"✅ Total products trouvé: {metrics['total_products']}")
                                        break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"⚠️ Erreur extraction total_products: {e}")
                
                # 2. Détecter les pixels Google Analytics et Facebook
                try:
                    # Vérifier la présence de Google Analytics
                    google_scripts = await page.query_selector_all('script[src*="google-analytics"], script[src*="gtag"]')
                    if google_scripts:
                        metrics["pixel_google"] = 1
                        logger.info("✅ Pixel Google détecté")
                    else:
                        # Vérifier aussi dans le contenu des scripts
                        page_content = await page.content()
                        if 'gtag' in page_content or 'google-analytics' in page_content:
                            metrics["pixel_google"] = 1
                            logger.info("✅ Pixel Google détecté dans le contenu")
                        else:
                            metrics["pixel_google"] = 0
                    
                    # Vérifier la présence de Facebook Pixel
                    facebook_scripts = await page.query_selector_all('script[src*="facebook"]')
                    if facebook_scripts:
                        metrics["pixel_facebook"] = 1
                        logger.info("✅ Pixel Facebook détecté")
                    else:
                        # Vérifier aussi dans le contenu des scripts
                        if 'fbq' in page_content or 'facebook' in page_content:
                            metrics["pixel_facebook"] = 1
                            logger.info("✅ Pixel Facebook détecté dans le contenu")
                        else:
                            metrics["pixel_facebook"] = 0
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur détection pixels: {e}")
                    metrics["pixel_google"] = 0
                    metrics["pixel_facebook"] = 0
                
                # 3. Extraire l'AOV (Average Order Value)
                try:
                    # Chercher des sélecteurs communs pour l'AOV
                    aov_selectors = [
                        '[data-testid*="aov"]',
                        '[class*="aov"]',
                        '[class*="order-value"]',
                        'span:contains("AOV")',
                        'div:contains("average order")',
                        'span:contains("$")'
                    ]
                    
                    for selector in aov_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text and '$' in text:
                                    # Extraire les nombres avec le symbole $
                                    numbers = re.findall(r'\$?(\d+(?:\.\d+)?)', text)
                                    if numbers:
                                        metrics["aov"] = self.parse_float(numbers[0])
                                        logger.info(f"✅ AOV trouvé: {metrics['aov']}")
                                        break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"⚠️ Erreur extraction AOV: {e}")
                
                await browser.close()
                
                logger.info(f"✅ Métriques extraites: {json.dumps(metrics, indent=2)}")
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Erreur extraction métriques supplémentaires: {e}")
            return {
                "total_products": None,
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
