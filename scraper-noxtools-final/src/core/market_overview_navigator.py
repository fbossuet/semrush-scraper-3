#!/usr/bin/env python3
"""
Market Overview Navigator for Noxtools scraper
- Navigate to market overview page via search
- Handle paywall detection and server fallback (server2 → server5)
- Extract FID and build complete URL with parameters
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from playwright.async_api import Page

from .playwright_manager import PlaywrightManager
from .session_manager import SessionManager
from utils.url_params import build_market_overview_url, extract_fid_from_url

logger = logging.getLogger(__name__)

@dataclass
class MarketOverviewConfig:
    """Configuration for market overview navigation."""
    # Base URL for market overview
    base_url: str = "https://semrush1.semrush.pw/analytics/traffic/market-overview/"
    
    # Dashboard URL for session refresh
    dashboard_url: str = "https://noxtools.com/secure/member"
    
    # Bridge URLs for fallback (server2 → server5)
    bridge_urls: list[str] = None
    
    # Timeouts
    navigation_timeout_ms: int = 30000
    element_wait_timeout_ms: int = 10000
    network_idle_timeout_ms: int = 10000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_ms: int = 2000
    
    def __post_init__(self):
        if self.bridge_urls is None:
            self.bridge_urls = [
                "https://semrush.noxtools.com/server2.php",
                "https://semrush.noxtools.com/server3.php", 
                "https://semrush.noxtools.com/server4.php",
                "https://semrush.noxtools.com/server5.php"
            ]

class MarketOverviewNavigator:
    """Handles navigation to market overview page with search and fallback logic."""
    
    def __init__(self, config: Optional[MarketOverviewConfig] = None):
        self.config = config or MarketOverviewConfig()
    
    async def navigate_market_overview(self, page: Page, playwright_manager: PlaywrightManager,
                                     session_manager: SessionManager, domain: str) -> Optional[str]:
        """
        Navigate to market overview page via search with fallback logic.
        
        Args:
            page: Playwright page instance
            playwright_manager: Playwright manager for navigation
            session_manager: Session manager for cross-domain handling
            domain: Domain to search for (e.g., "cakesbody.com")
            
        Returns:
            Complete market overview URL with parameters or None if failed
        """
        try:
            logger.info(f"🔍 Starting market overview navigation for domain: {domain}")
            
            # Try each bridge URL in sequence
            for bridge_index, bridge_url in enumerate(self.config.bridge_urls):
                logger.info(f"🌉 Trying bridge {bridge_index + 1}/{len(self.config.bridge_urls)}: {bridge_url}")
                
                try:
                    # Step 1: Refresh session via dashboard
                    await self._refresh_session(page, playwright_manager, bridge_url)
                    
                    # Step 2: Navigate to market overview base URL
                    await self._navigate_to_base_url(page, playwright_manager, session_manager)
                    
                    # Step 3: Check for paywall
                    if await self._check_paywall(page):
                        logger.warning(f"⚠️ Paywall detected on bridge {bridge_index + 1}, trying next bridge")
                        continue
                    
                    # Step 4: Perform search
                    search_success = await self._perform_search(page, domain)
                    if not search_success:
                        logger.warning(f"⚠️ Search failed on bridge {bridge_index + 1}, trying next bridge")
                        continue
                    
                    # Step 5: Extract FID and build complete URL
                    complete_url = await self._extract_fid_and_build_url(page)
                    if complete_url:
                        logger.info(f"✅ Market overview navigation successful: {complete_url}")
                        return complete_url
                    else:
                        logger.warning(f"⚠️ FID extraction failed on bridge {bridge_index + 1}, trying next bridge")
                        continue
                        
                except Exception as e:
                    logger.warning(f"⚠️ Bridge {bridge_index + 1} failed: {e}, trying next bridge")
                    continue
            
            logger.error("❌ All bridge URLs failed for market overview navigation")
            return None
            
        except Exception as e:
            logger.error(f"❌ Market overview navigation error: {e}")
            return None
    
    async def _refresh_session(self, page: Page, playwright_manager: PlaywrightManager, bridge_url: str):
        """Refresh session via dashboard and bridge."""
        try:
            # Navigate to dashboard first
            await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
            await asyncio.sleep(1.0)
            
            # Navigate to bridge URL
            await page.goto(bridge_url, referer=self.config.dashboard_url, timeout=self.config.navigation_timeout_ms)
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.network_idle_timeout_ms)
            await asyncio.sleep(1.0)
            
            logger.info(f"✅ Session refreshed via bridge: {bridge_url}")
            
        except Exception as e:
            logger.warning(f"⚠️ Session refresh failed for bridge {bridge_url}: {e}")
            raise
    
    async def _navigate_to_base_url(self, page: Page, playwright_manager: PlaywrightManager, 
                                  session_manager: SessionManager):
        """Navigate to market overview base URL."""
        try:
            # Use session manager for cross-domain navigation
            await session_manager.navigate_cross_domain(page, playwright_manager, self.config.base_url)
            
            # Wait for page to settle
            await page.wait_for_load_state('networkidle', timeout=self.config.network_idle_timeout_ms)
            await asyncio.sleep(2.0)  # Extra time for SAP React
            
            logger.info("✅ Navigated to market overview base URL")
            
        except Exception as e:
            logger.warning(f"⚠️ Navigation to base URL failed: {e}")
            raise
    
    async def _check_paywall(self, page: Page) -> bool:
        """Check if paywall is present on the page."""
        try:
            # Check for paywall indicator
            paywall_element = await page.query_selector('*[data-testid="paywall"]')
            if paywall_element:
                logger.warning("🚫 Paywall detected on page")
                return True
            
            # Check for other paywall indicators
            page_content = await page.content()
            if "paywall" in page_content.lower() or "upgrade" in page_content.lower():
                logger.warning("🚫 Paywall indicators found in page content")
                return True
            
            logger.info("✅ No paywall detected")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking paywall: {e}")
            return False
    
    async def _perform_search(self, page: Page, domain: str) -> bool:
        """Perform domain search on the market overview page."""
        try:
            # Try primary search method (competitors input + analyze button)
            primary_success = await self._try_primary_search(page, domain)
            if primary_success:
                return True
            
            # Try secondary search method (searchbar)
            secondary_success = await self._try_secondary_search(page, domain)
            if secondary_success:
                return True
            
            logger.warning("⚠️ Both search methods failed")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Search error: {e}")
            return False
    
    async def _try_primary_search(self, page: Page, domain: str) -> bool:
        """Try primary search method with competitors input."""
        try:
            # Check if primary selectors are present
            competitors_input = await page.query_selector('input[name="competitors.0"]')
            analyze_button = await page.query_selector('button[data-testid="analyze-cta"]')
            
            if not competitors_input or not analyze_button:
                logger.info("Primary search selectors not found")
                return False
            
            # Fill domain and submit
            await competitors_input.fill(domain)
            await analyze_button.click()
            
            # Wait for navigation
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.navigation_timeout_ms)
            await asyncio.sleep(2.0)
            
            logger.info("✅ Primary search method successful")
            return True
            
        except Exception as e:
            logger.info(f"Primary search method failed: {e}")
            return False
    
    async def _try_secondary_search(self, page: Page, domain: str) -> bool:
        """Try secondary search method with searchbar."""
        try:
            # Check if secondary selectors are present
            search_input = await page.query_selector('input[data-test="searchbar_input"]')
            search_button = await page.query_selector('button[data-test="searchbar_search_submit"]')
            
            if not search_input or not search_button:
                logger.info("Secondary search selectors not found")
                return False
            
            # Fill domain and submit
            await search_input.fill(domain)
            await search_button.click()
            
            # Wait for navigation
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.navigation_timeout_ms)
            await asyncio.sleep(2.0)
            
            logger.info("✅ Secondary search method successful")
            return True
            
        except Exception as e:
            logger.info(f"Secondary search method failed: {e}")
            return False
    
    async def _extract_fid_and_build_url(self, page: Page) -> Optional[str]:
        """Extract FID from current URL and build complete market overview URL."""
        try:
            current_url = page.url
            logger.info(f"Current URL for FID extraction: {current_url}")
            
            # Extract FID from URL
            fid = extract_fid_from_url(current_url)
            if not fid:
                logger.warning("No FID found in current URL")
                return None
            
            # Build complete URL with parameters
            from utils.url_params import build_date_range
            date_range = build_date_range()
            
            complete_url = build_market_overview_url(
                base_url="https://semrush3.semrush.pw/analytics/traffic/market-overview/",
                fid=fid,
                date_range=date_range,
                country="us"
            )
            
            logger.info(f"Built complete URL: {complete_url}")
            return complete_url
            
        except Exception as e:
            logger.error(f"Error extracting FID and building URL: {e}")
            return None
    
    async def get_navigation_info(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive navigation information for debugging."""
        try:
            current_url = page.url
            
            return {
                'current_url': current_url,
                'base_url': self.config.base_url,
                'bridge_urls': self.config.bridge_urls,
                'dashboard_url': self.config.dashboard_url,
                'config': {
                    'navigation_timeout_ms': self.config.navigation_timeout_ms,
                    'element_wait_timeout_ms': self.config.element_wait_timeout_ms,
                    'network_idle_timeout_ms': self.config.network_idle_timeout_ms,
                    'max_retries': self.config.max_retries
                }
            }
            
        except Exception as e:
            logger.error(f"Navigation info error: {e}")
            return {'error': str(e)}

# Convenience function
async def navigate_to_market_overview(page: Page, playwright_manager: PlaywrightManager,
                                    session_manager: SessionManager, domain: str,
                                    config: Optional[MarketOverviewConfig] = None) -> Optional[str]:
    """Quick market overview navigation function."""
    navigator = MarketOverviewNavigator(config)
    return await navigator.navigate_market_overview(page, playwright_manager, session_manager, domain)
