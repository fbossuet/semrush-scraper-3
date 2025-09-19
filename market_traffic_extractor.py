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
                # Utiliser l'URL directe de la boutique fournie
                logger.info(f"🌐 Navigation vers la page de détail boutique: {shop_url}")
                await page.goto(shop_url, wait_until='domcontentloaded', timeout=30000)
                
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
                
                # Attendre que la page se charge complètement
                await page.wait_for_timeout(3000)
                
                # Extraire les données de trafic par pays
                try:
                    # Attendre la section "Trafic par pays" avec timeout augmenté
                    logger.info("🔍 Recherche de la section 'Trafic par pays'...")
                    
                    # Essayer plusieurs sélecteurs pour la section
                    section_found = False
                    selectors_to_try = [
                        'h3:has-text("Trafic par pays")',
                        'h3.font-semibold.tracking-tight.text-lg',
                        'h3:has-text("Traffic by Country")'
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            await page.wait_for_selector(selector, timeout=10000)
                            logger.info(f"✅ Section trouvée avec le sélecteur: {selector}")
                            section_found = True
                            break
                        except:
                            logger.info(f"⚠️ Sélecteur {selector} non trouvé, essai suivant...")
                            continue
                    
                    if not section_found:
                        logger.warning("⚠️ Section 'Trafic par pays' non trouvée sur cette page")
                        return market_data
                    
                    # Extraire les données des pays
                    country_data = await page.evaluate("""
                        () => {
                            const marketData = {
                                market_us: null,
                                market_uk: null,
                                market_de: null,
                                market_ca: null,
                                market_au: null,
                                market_fr: null
                            };
                            
                            // Chercher tous les éléments de pays
                            const countryElements = document.querySelectorAll('.flex.gap-2.w-full.items-center');
                            
                            countryElements.forEach(el => {
                                try {
                                    const img = el.querySelector('img');
                                    const percentageEl = el.querySelector('p:last-child');
                                    
                                    if (img && percentageEl) {
                                        const countryCode = img.alt.toLowerCase();
                                        const percentageText = percentageEl.textContent.replace('%', '').trim();
                                        const percentage = parseFloat(percentageText) / 100; // Convertir en décimal
                                        
                                        // Mapper les codes pays
                                        switch(countryCode) {
                                            case 'us':
                                                marketData.market_us = percentage;
                                                break;
                                            case 'gb':
                                                marketData.market_uk = percentage;
                                                break;
                                            case 'de':
                                                marketData.market_de = percentage;
                                                break;
                                            case 'ca':
                                                marketData.market_ca = percentage;
                                                break;
                                            case 'au':
                                                marketData.market_au = percentage;
                                                break;
                                            case 'fr':
                                                marketData.market_fr = percentage;
                                                break;
                                        }
                                    }
                                } catch (e) {
                                    console.log('Erreur parsing pays:', e);
                                }
                            });
                            
                            return marketData;
                        }
                    """)
                    
                    if country_data:
                        market_data.update(country_data)
                        logger.info(f"✅ Données de trafic extraites: {country_data}")
                    else:
                        logger.warning("⚠️ Aucune donnée de trafic par pays trouvée")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur extraction trafic par pays: {e}")
                
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