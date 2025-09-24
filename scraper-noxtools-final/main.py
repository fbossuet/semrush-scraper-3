#!/usr/bin/env python3
"""
Script principal du scraper Noxtools (Alpha)
- Lancement du scraping en production
- Workflow complet : Auth → Navigation → Extraction → Formatage → Status
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.playwright_manager import PlaywrightManager
from core.auth_manager import AuthManager
from core.session_manager import SessionManager
from core.metrics_extractor import MetricsExtractor
from core.market_overview_navigator import MarketOverviewNavigator
from services.shop_repository import ShopRepository, get_total_shops_count
from services.formatter import format_metrics
from services.status_manager import StatusManager
from utils.url_params import get_url_params_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('noxtools_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NoxtoolsScraper:
    """Scraper principal Noxtools Alpha."""
    
    def __init__(self):
        self.playwright_manager = PlaywrightManager()
        self.auth_manager = AuthManager()
        self.session_manager = SessionManager()
        self.metrics_extractor = MetricsExtractor()
        self.market_navigator = MarketOverviewNavigator()
        self.shop_repo = ShopRepository()
        self.status_manager = StatusManager()
        
        # Configuration
        self.username = "johnychareon"
        self.password = "fbossuetg"
        self.max_shops_per_run = 10  # Limite pour Alpha
        
    async def initialize(self) -> bool:
        """Initialise le scraper."""
        try:
            logger.info("🚀 Initializing Noxtools scraper...")
            await self.playwright_manager.initialize()
            logger.info("✅ Scraper initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize scraper: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authentification sur Noxtools."""
        try:
            logger.info("🔐 Starting authentication...")
            page = await self.playwright_manager.new_page()
            
            auth_success = await self.auth_manager.authenticate(
                page, self.username, self.password, self.playwright_manager
            )
            
            if auth_success:
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error("❌ Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    async def scrape_shop(self, shop_url: str) -> dict:
        """Scrape une boutique individuelle."""
        try:
            logger.info(f"🏪 Scraping shop: {shop_url}")
            
            # Step 1: Navigate to market overview
            page = await self.playwright_manager.new_page()
            market_url = await self.market_navigator.navigate_market_overview(
                page, self.playwright_manager, self.session_manager, shop_url
            )
            
            if not market_url:
                logger.warning(f"⚠️ Failed to navigate to market overview for {shop_url}")
                return {"status": "failed", "error": "Navigation failed"}
            
            # Step 2: Extract metrics
            metrics = await self.metrics_extractor.extract_metrics(
                page, self.playwright_manager, self.session_manager, shop_url
            )
            
            if not metrics.success:
                logger.warning(f"⚠️ Failed to extract metrics for {shop_url}")
                return {"status": "failed", "error": metrics.error_message}
            
            # Step 3: Format data
            raw_metrics = {
                'visits': metrics.visits,
                'entrancesSearchOrganic': metrics.organic_search_traffic,
                'entrancesSearchPaid': metrics.paid_search_traffic,
                'purchasesPerVisit': metrics.purchase_conversion,
                'avgVisitDuration': metrics.avg_visit_duration,
                'bouncesPerVisit': metrics.bounce_rate,
                'cpc': getattr(metrics, 'cpc', None),
                'branded_traffic': getattr(metrics, 'branded_traffic', None)
            }
            
            formatted_metrics = format_metrics(raw_metrics)
            
            # Step 4: Classify status
            status = self.status_manager.classify_scraping_status(raw_metrics)
            
            # Step 5: Log results
            self.status_manager.log_status_result(
                shop_id=0,  # Will be updated in Beta
                shop_url=shop_url,
                metrics=raw_metrics,
                status=status
            )
            
            return {
                "status": status,
                "metrics": formatted_metrics,
                "raw_metrics": raw_metrics
            }
            
        except Exception as e:
            logger.error(f"❌ Error scraping {shop_url}: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_scraping_session(self) -> dict:
        """Lance une session de scraping complète."""
        try:
            logger.info("🎯 Starting scraping session...")
            
            # Get URL parameters
            url_params = get_url_params_info()
            logger.info(f"📅 Date range: {url_params['date_range']}")
            logger.info(f"🌍 Country: {url_params['default_country']}")
            
            # Get shops to scrape
            total_shops = get_total_shops_count()
            logger.info(f"🏪 Total shops available: {total_shops}")
            
            if total_shops == 0:
                logger.warning("⚠️ No shops available for scraping")
                return {"status": "no_shops", "scraped": 0}
            
            # Limit shops for Alpha
            shops_to_scrape = min(total_shops, self.max_shops_per_run)
            logger.info(f"🎯 Scraping {shops_to_scrape} shops (Alpha limit)")
            
            # Get shop batch
            shops = await self.shop_repo.get_shops_batch_with_delay(0)
            if not shops:
                logger.warning("⚠️ No shops in batch")
                return {"status": "no_batch", "scraped": 0}
            
            # Scrape each shop
            results = []
            for i, shop in enumerate(shops[:shops_to_scrape]):
                logger.info(f"📊 Processing shop {i+1}/{shops_to_scrape}: {shop.shop_url}")
                
                result = await self.scrape_shop(shop.shop_url)
                result["shop_id"] = shop.id
                result["shop_url"] = shop.shop_url
                results.append(result)
                
                # Anti-detection delay between shops
                if i < len(shops) - 1:
                    await asyncio.sleep(2.0)
            
            # Summary
            completed = sum(1 for r in results if r["status"] == "completed")
            partial = sum(1 for r in results if r["status"] == "partial")
            failed = sum(1 for r in results if r["status"] == "failed")
            
            logger.info(f"📊 Session summary:")
            logger.info(f"   ✅ Completed: {completed}")
            logger.info(f"   ⚠️ Partial: {partial}")
            logger.info(f"   ❌ Failed: {failed}")
            
            return {
                "status": "completed",
                "scraped": len(results),
                "completed": completed,
                "partial": partial,
                "failed": failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Scraping session failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Nettoyage des ressources."""
        try:
            await self.playwright_manager.cleanup()
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")

async def main():
    """Fonction principale."""
    print("=" * 60)
    print("🚀 NOXTOOLS SCRAPER ALPHA - PRODUCTION SCRIPT")
    print("=" * 60)
    
    scraper = NoxtoolsScraper()
    
    try:
        # Initialize
        if not await scraper.initialize():
            print("❌ Failed to initialize scraper")
            return 1
        
        # Authenticate
        if not await scraper.authenticate():
            print("❌ Authentication failed")
            return 1
        
        # Run scraping session
        result = await scraper.run_scraping_session()
        
        if result["status"] == "completed":
            print(f"✅ Scraping completed: {result['scraped']} shops processed")
            print(f"   ✅ Completed: {result['completed']}")
            print(f"   ⚠️ Partial: {result['partial']}")
            print(f"   ❌ Failed: {result['failed']}")
        else:
            print(f"⚠️ Scraping session ended with status: {result['status']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
        
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
