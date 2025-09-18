#!/usr/bin/env python3
"""
Test simple pour vérifier que la correction conversion_rate fonctionne
"""

import asyncio
import logging
from global_bootstrap import get_shared_browser_context

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_conversion_rate_fix():
    """Test simple de la correction conversion_rate"""
    logger.info("🚀 TEST CORRECTION CONVERSION_RATE")
    
    try:
        # Configuration du navigateur
        context = await get_shared_browser_context()
        page = await context.new_page()
        logger.info("✅ Navigateur configuré")
        
        # Navigation vers une page de test
        await page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(3)
        
        # Test du sélecteur de conversion_rate
        try:
            element = await page.wait_for_selector(
                'div[data-testid="summary-cell conversion"] > div > div > div > span[data-testid="value"]',
                timeout=5000
            )
            
            if element:
                value = await element.inner_text()
                logger.info(f"✅ CONVERSION_RATE TROUVÉ: {value}")
                return True
            else:
                logger.info("❌ CONVERSION_RATE: Sélecteur non trouvé")
                return False
                
        except Exception as e:
            logger.info(f"❌ CONVERSION_RATE: Erreur sélecteur: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_conversion_rate_fix())
    if result:
        logger.info("🎉 CORRECTION CONVERSION_RATE: SUCCÈS")
    else:
        logger.info("❌ CORRECTION CONVERSION_RATE: ÉCHEC")
