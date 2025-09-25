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
from core.server_manager import get_server_manager

logger = logging.getLogger(__name__)

@dataclass
class MarketOverviewConfig:
    """Configuration for market overview navigation."""
    # Base URL for market overview (sera normalisée par ServerManager)
    base_url: str = "https://semrush1.semrush.pw/analytics/traffic/market-overview/"
    
    # Dashboard URL for session refresh
    dashboard_url: str = "https://noxtools.com/secure/member"
    
    # Bridge URLs for fallback (sera géré par ServerManager)
    bridge_urls: list[str] = None
    
    # Timeouts
    navigation_timeout_ms: int = 30000
    element_wait_timeout_ms: int = 10000
    network_idle_timeout_ms: int = 10000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_ms: int = 2000
    
    def __post_init__(self):
        # Les bridge URLs seront gérées par le ServerManager
        if self.bridge_urls is None:
            self.bridge_urls = []

class MarketOverviewNavigator:
    """Handles navigation to market overview page with search and fallback logic."""
    
    def __init__(self, config: Optional[MarketOverviewConfig] = None):
        self.config = config or MarketOverviewConfig()
        self.server_manager = get_server_manager()
    
    async def navigate_market_overview(self, page: Page, playwright_manager: PlaywrightManager,
                                     session_manager: SessionManager, domain: str, 
                                     auth_manager=None) -> Optional[str]:
        """
        Navigate to market overview page via search with fallback logic and session retry.
        
        Args:
            page: Playwright page instance
            playwright_manager: Playwright manager for navigation
            session_manager: Session manager for cross-domain handling
            domain: Domain to search for (e.g., "cakesbody.com")
            auth_manager: Authentication manager for re-authentication if needed
            
        Returns:
            Complete market overview URL with parameters or None if failed
        """
        try:
            logger.info(f"🔍 Starting market overview navigation for domain: {domain}")
            
            # Utiliser le ServerManager pour gérer les serveurs
            available_servers = self.server_manager.get_available_servers()
            logger.info(f"🌐 Serveurs disponibles: {[s.name for s in available_servers]}")
            
            # Essayer chaque serveur disponible
            for server in available_servers:
                logger.info(f"🌉 Trying server: {server.name} ({server.domain})")
                
                try:
                    # Forcer l'utilisation de ce serveur
                    self.server_manager.force_server(server.name)
                    
                    # Step 1: Refresh session via dashboard et bridge
                    bridge_url = self.server_manager.get_current_bridge_url()
                    await self._refresh_session(page, playwright_manager, bridge_url)
                    
                    # Step 2: Navigate to market overview base URL (normalisée)
                    await self._navigate_to_base_url(page, playwright_manager, session_manager)
                    
                    # Step 3: Check for session expired
                    if await self._check_session_expired(page):
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"🚫 Session expired detected on server {current_server}")
                        self.server_manager.mark_server_failed("Session expired")
                        continue
                    
                    # Step 4: Check for paywall
                    if await self._check_paywall(page):
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ Paywall detected on server {current_server}")
                        self.server_manager.mark_server_failed("Paywall detected")
                        continue
                    
                    # Step 5: Perform search
                    search_success = await self._perform_search(page, domain)
                    if not search_success:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ Search failed on server {current_server}")
                        self.server_manager.mark_server_failed("Search failed")
                        continue
                    
                    # Step 6: Extract FID and build complete URL
                    complete_url = await self._extract_fid_and_build_url(page)
                    if complete_url:
                        current_server = self.server_manager.get_current_server_name()
                        logger.info(f"✅ Market overview navigation successful on {current_server}: {complete_url}")
                        self.server_manager.mark_server_success()
                        return complete_url
                    else:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ FID extraction failed on server {current_server}")
                        self.server_manager.mark_server_failed("FID extraction failed")
                        continue
                        
                except Exception as e:
                    current_server = self.server_manager.get_current_server_name()
                    logger.warning(f"⚠️ Server {current_server} failed: {e}")
                    self.server_manager.mark_server_failed(f"Exception: {e}")
                    continue
            
            logger.error("❌ All servers failed for market overview navigation")
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
            # Normaliser l'URL avec le serveur actuel
            normalized_url = self.server_manager.normalize_url_to_current_server(self.config.base_url)
            logger.info(f"🌐 Navigating to normalized URL: {normalized_url}")
            
            # Use session manager for cross-domain navigation
            await session_manager.navigate_cross_domain(page, playwright_manager, normalized_url)
            
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
    
    async def _check_session_expired(self, page: Page) -> bool:
        """Check if session has expired on the page."""
        try:
            # Get page content to check for session expired message
            page_content = await page.evaluate('document.body.innerText')
            
            # Check for session expired indicators
            session_expired_indicators = [
                "Session expired",
                "access again from Dashboard",
                "session expired",
                "please login again",
                "authentication required"
            ]
            
            for indicator in session_expired_indicators:
                if indicator.lower() in page_content.lower():
                    logger.warning(f"🚫 Session expired detected: '{indicator}' found in page content")
                    return True
            
            logger.info("✅ Session appears to be valid")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking session status: {e}")
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
            logger.warning(f"Primary search method failed: {e}")
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
            logger.warning(f"Secondary search method failed: {e}")
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
                base_url=self.server_manager.normalize_url_to_current_server("https://semrush1.semrush.pw/analytics/traffic/market-overview/"),
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
                                    config: Optional[MarketOverviewConfig] = None,
                                    auth_manager=None) -> Optional[str]:
    """Quick market overview navigation function with session retry support."""
    navigator = MarketOverviewNavigator(config)
    return await navigator.navigate_market_overview(page, playwright_manager, session_manager, domain, auth_manager)

