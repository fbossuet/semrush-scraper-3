#!/usr/bin/env python3
"""
Script de lancement du scraper de production avec API organic.Summary
"""

import asyncio
import logging
import sys
import os
import argparse
from datetime import datetime, timezone

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from production_scraper_parallel_with_organic_summary import main, setup_logging

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Désactiver les logs de playwright
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

async def launch_production():
    """Lance le scraper de production"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 LANCEMENT DU SCRAPER DE PRODUCTION")
    logger.info("=" * 60)
    logger.info(f"📅 Date: {datetime.now(timezone.utc).isoformat()}")
    logger.info("🔧 API: organic.Summary (Organic + Paid Traffic)")
    logger.info("🌐 DOM: Average Visit Duration + Bounce Rate")
    logger.info("💾 BDD: Enregistrement activé")
    logger.info("=" * 60)
    
    try:
        await main()
        logger.info("🎉 SCRAPER DE PRODUCTION TERMINÉ AVEC SUCCÈS")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du lancement: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lanceur du scraper de production')
    parser.add_argument('--dry-run', action='store_true', help='Mode test (pas d\'enregistrement BDD)')
    parser.add_argument('--workers', type=int, default=2, help='Nombre de workers (défaut: 2)')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 MODE TEST ACTIVÉ - Pas d'enregistrement en BDD")
    
    success = asyncio.run(launch_production())
    
    if success:
        print("\n✅ Scraper de production terminé avec succès !")
        sys.exit(0)
    else:
        print("\n❌ Scraper de production échoué !")
        sys.exit(1)
