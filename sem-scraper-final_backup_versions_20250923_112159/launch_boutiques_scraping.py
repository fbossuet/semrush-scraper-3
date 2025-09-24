#!/usr/bin/env python3
"""
Script pour lancer le scraping des boutiques avec rotation de sessions
"""

import asyncio
import logging
from production_scraper import ProductionScraperWithRotation as ProductionScraper, setup_logging
import config

async def main():
    """Lance le scraping des boutiques"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🏭 LANCEMENT DU SCRAPING DES BOUTIQUES")
    
    try:
        config.config.validate_credentials()
        logger.info("✅ Configuration validée")
    except ValueError as e:
        logger.error(f"❌ Erreur de configuration: {e}")
        return

    config.config.print_config_summary()

    scraper = ProductionScraper()
    
    # Lancer le scraping avec la méthode run()
    success = await scraper.run()
    
    if success:
        logger.info("🎉 SCRAPING DES BOUTIQUES TERMINÉ AVEC SUCCÈS")
    else:
        logger.error("❌ SCRAPING DES BOUTIQUES ÉCHOUÉ")

if __name__ == "__main__":
    asyncio.run(main())
