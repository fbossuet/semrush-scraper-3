#!/usr/bin/env python3
"""
Version modifiée du scraper principal pour mettre à jour uniquement conversion_rate
Ne fait que Traffic Analysis (pas Domain Overview ni Organic Search)
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from production_scraper import ProductionScraper
import trendtrack_api as api

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/conversion_rate_only_{datetime.now(timezone.utc).isoformat()}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConversionRateOnlyScraper(ProductionScraper):
    """Scraper spécialisé pour conversion_rate uniquement"""
    
    async def scrape_conversion_rate_only(self, domain: str):
        """Scrape uniquement Traffic Analysis pour récupérer conversion_rate"""
        try:
            logger.info(f"🔄 Scraping conversion_rate pour {domain}")
            
            # Scraping Traffic Analysis uniquement
            logger.info("📊 ÉTAPE: Scraping Traffic Analysis...")
            traffic_success = await self.scrape_traffic_analysis(domain)
            
            if traffic_success:
                # Récupérer les données de session
                traffic_data = self.session_data.get('data', {}).get('traffic_analysis', {})
                conversion_rate = traffic_data.get('purchase_conversion', '')
                
                if conversion_rate and conversion_rate not in ["Sélecteur non trouvé", "Erreur"]:
                    # Trouver le shop_id
                    all_shops = api.get_all_shops()
                    shop_id = None
                    for shop in all_shops:
                        if shop.get('shop_url') == domain:
                            shop_id = shop.get('id')
                            break
                    
                    if shop_id:
                        # Mise à jour directe en SQL
                        conn = api._get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE analytics 
                            SET conversion_rate = ?, updated_at = ? 
                            WHERE shop_id = ?
                        """, (conversion_rate, datetime.now(timezone.utc), shop_id))
                        conn.commit()
                        logger.info(f"✅ Conversion rate mis à jour pour {domain}: {conversion_rate}")
                        return True
                    else:
                        logger.error(f"❌ Shop ID non trouvé pour {domain}")
                        return False
                else:
                    logger.warning(f"⚠️ Conversion rate non trouvé pour {domain}")
                    return False
            else:
                logger.error(f"❌ Échec scraping Traffic Analysis pour {domain}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping conversion_rate pour {domain}: {e}")
            return False

async def main():
    """Fonction principale"""
    logger.info("🚀 DÉBUT MISE À JOUR CONVERSION RATE ONLY")
    
    try:
        # Récupérer tous les shops
        all_shops = api.get_all_shops()
        logger.info(f"📊 {len(all_shops)} shops trouvés")
        
        # Initialiser le scraper
        scraper = ConversionRateOnlyScraper()
        await scraper.setup_browser()
        
        # Authentification MyToolsPlan
        auth_success = await scraper.authenticate_mytoolsplan()
        if not auth_success:
            logger.error("❌ Échec de l'authentification - Arrêt du scraping")
            return
        
        success_count = 0
        error_count = 0
        
        for shop in all_shops:
            shop_url = shop.get('shop_url')
            
            if not shop_url:
                continue
                
            try:
                success = await scraper.scrape_conversion_rate_only(shop_url)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
                # Pause entre les shops
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Erreur traitement {shop_url}: {e}")
                error_count += 1
        
        logger.info(f"✅ MISE À JOUR TERMINÉE: {success_count} réussis, {error_count} échecs")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
    finally:
        if 'scraper' in locals():
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(main())
