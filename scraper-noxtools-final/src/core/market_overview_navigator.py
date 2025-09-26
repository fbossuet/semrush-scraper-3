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
            logger.info(f"🔍 [DEBUG] Starting market overview navigation for domain: {domain}")
            logger.info(f"🔍 [DEBUG] Page URL before navigation: {page.url}")
            logger.info(f"🔍 [DEBUG] Page title before navigation: {await page.title()}")
            
            # Utiliser le ServerManager pour gérer les serveurs
            available_servers = self.server_manager.get_available_servers()
            logger.info(f"🌐 [DEBUG] Serveurs disponibles: {[s.name for s in available_servers]}")
            logger.info(f"🌐 [DEBUG] Serveur actuel: {self.server_manager.get_current_server_name()}")
            
            # Essayer chaque serveur disponible
            for server_index, server in enumerate(available_servers, 1):
                logger.info(f"🌉 [DEBUG] Trying server {server_index}/{len(available_servers)}: {server.name} ({server.domain})")
                logger.info(f"🌉 [DEBUG] Server status: {server.status}")
                logger.info(f"🌉 [DEBUG] Server last_error: {server.last_error}")
                
                try:
                    # Forcer l'utilisation de ce serveur
                    logger.info(f"🔄 [DEBUG] Forcing server to: {server.name}")
                    self.server_manager.force_server(server.name)
                    logger.info(f"🔄 [DEBUG] Current server after force: {self.server_manager.get_current_server_name()}")
                    
                    # Step 1: Refresh session via dashboard et bridge
                    bridge_url = self.server_manager.get_current_bridge_url()
                    logger.info(f"🔐 [DEBUG] Bridge URL: {bridge_url}")
                    logger.info(f"🔐 [DEBUG] Dashboard URL: {self.config.dashboard_url}")
                    await self._refresh_session(page, playwright_manager, bridge_url)
                    
                    # Step 2: Navigate to market overview base URL (normalisée)
                    logger.info(f"🌐 [DEBUG] Navigating to market overview base URL...")
                    await self._navigate_to_base_url(page, playwright_manager, session_manager)
                    
                    # Step 3: Check for session expired
                    logger.info(f"🔍 [DEBUG] Checking session status...")
                    session_expired = await self._check_session_expired(page)
                    logger.info(f"🔍 [DEBUG] Session expired result: {session_expired}")
                    if session_expired:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"🚫 [DEBUG] Session expired detected on server {current_server}")
                        self.server_manager.mark_server_failed("Session expired")
                        continue
                    
                    # Step 4: Check for paywall
                    logger.info(f"🔍 [DEBUG] Checking paywall status...")
                    paywall_detected = await self._check_paywall(page)
                    logger.info(f"🔍 [DEBUG] Paywall detected result: {paywall_detected}")
                    # LOGIQUE CORRIGÉE: Fallback SEULEMENT si paywall détecté
                    if paywall_detected:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ [DEBUG] Paywall detected on server {current_server}")
                        self.server_manager.mark_server_failed("Paywall detected")
                        continue  # Fallback vers serveur suivant
                    
                    # Step 5: Perform search
                    logger.info(f"🔍 [DEBUG] Starting domain search for: {domain}")
                    search_success = await self._perform_search(page, domain)
                    logger.info(f"🔍 [DEBUG] Search success result: {search_success}")
                    if not search_success:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ [DEBUG] Search failed on server {current_server} - NO PAYWALL DETECTED")
                        # CORRECTION: Pas de fallback si pas de paywall - juste retry ou erreur
                        # Le fallback ne doit se déclencher QUE si paywall détecté
                        logger.error(f"❌ [DEBUG] Search failed without paywall - staying on server {current_server}")
                        # Option 1: Retry sur le même serveur
                        # Option 2: Raise exception pour arrêter le processus
                        raise Exception(f"Search failed on server {current_server} without paywall - no fallback")
                    
                    # Step 6: Extract FID and build complete URL
                    logger.info(f"📊 [DEBUG] Extracting FID and building complete URL...")
                    complete_url = await self._extract_fid_and_build_url(page)
                    logger.info(f"📊 [DEBUG] Complete URL result: {complete_url}")
                    if complete_url:
                        current_server = self.server_manager.get_current_server_name()
                        logger.info(f"✅ [DEBUG] Market overview navigation successful on {current_server}: {complete_url}")
                        self.server_manager.mark_server_success()
                        return complete_url
                    else:
                        current_server = self.server_manager.get_current_server_name()
                        logger.warning(f"⚠️ [DEBUG] FID extraction failed on server {current_server}")
                        self.server_manager.mark_server_failed("FID extraction failed")
                        continue
                        
                except Exception as e:
                    current_server = self.server_manager.get_current_server_name()
                    logger.warning(f"⚠️ [DEBUG] Server {current_server} failed: {e}")
                    logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
                    logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
                    self.server_manager.mark_server_failed(f"Exception: {e}")
                    continue
            
            logger.error("❌ [DEBUG] All servers failed for market overview navigation")
            logger.error(f"❌ [DEBUG] Total servers tried: {len(available_servers)}")
            return None
            
        except Exception as e:
            logger.error(f"❌ [DEBUG] Market overview navigation error: {e}")
            logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] Exception args: {e.args}")
            return None
    
    async def _refresh_session(self, page: Page, playwright_manager: PlaywrightManager, bridge_url: str):
        """Refresh session via dashboard and bridge."""
        try:
            logger.info(f"🔐 [DEBUG] Starting session refresh...")
            logger.info(f"🔐 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔐 [DEBUG] Current page title: {await page.title()}")
            
            # Navigate to dashboard first
            logger.info(f"🔐 [DEBUG] Navigating to dashboard: {self.config.dashboard_url}")
            await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
            logger.info(f"🔐 [DEBUG] Dashboard navigation completed")
            logger.info(f"🔐 [DEBUG] Dashboard page URL: {page.url}")
            logger.info(f"🔐 [DEBUG] Dashboard page title: {await page.title()}")
            await asyncio.sleep(1.0)
            
            # Navigate to bridge URL
            logger.info(f"🔐 [DEBUG] Navigating to bridge URL: {bridge_url}")
            logger.info(f"🔐 [DEBUG] Bridge referer: {self.config.dashboard_url}")
            logger.info(f"🔐 [DEBUG] Bridge timeout: {self.config.navigation_timeout_ms}ms")
            await page.goto(bridge_url, referer=self.config.dashboard_url, timeout=self.config.navigation_timeout_ms)
            logger.info(f"🔐 [DEBUG] Bridge navigation completed")
            logger.info(f"🔐 [DEBUG] Bridge page URL: {page.url}")
            logger.info(f"🔐 [DEBUG] Bridge page title: {await page.title()}")
            
            logger.info(f"🔐 [DEBUG] Waiting for DOM content loaded...")
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.network_idle_timeout_ms)
            logger.info(f"🔐 [DEBUG] DOM content loaded completed")
            await asyncio.sleep(1.0)
            
            logger.info(f"✅ [DEBUG] Session refreshed via bridge: {bridge_url}")
            logger.info(f"✅ [DEBUG] Final page URL: {page.url}")
            logger.info(f"✅ [DEBUG] Final page title: {await page.title()}")
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Session refresh failed for bridge {bridge_url}: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            raise
    
    async def _navigate_to_base_url(self, page: Page, playwright_manager: PlaywrightManager, 
                                  session_manager: SessionManager):
        """Navigate to market overview base URL."""
        try:
            logger.info(f"🌐 [DEBUG] Starting navigation to base URL...")
            logger.info(f"🌐 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🌐 [DEBUG] Current page title: {await page.title()}")
            logger.info(f"🌐 [DEBUG] Base URL from config: {self.config.base_url}")
            logger.info(f"🌐 [DEBUG] Current server: {self.server_manager.get_current_server_name()}")
            
            # Normaliser l'URL avec le serveur actuel
            normalized_url = self.server_manager.normalize_url_to_current_server(self.config.base_url)
            logger.info(f"🌐 [DEBUG] Normalized URL: {normalized_url}")
            
            # Use session manager for cross-domain navigation
            logger.info(f"🌐 [DEBUG] Starting cross-domain navigation...")
            await session_manager.navigate_cross_domain(page, playwright_manager, normalized_url)
            logger.info(f"🌐 [DEBUG] Cross-domain navigation completed")
            logger.info(f"🌐 [DEBUG] Page URL after navigation: {page.url}")
            logger.info(f"🌐 [DEBUG] Page title after navigation: {await page.title()}")
            
            # Wait for page to settle
            logger.info(f"🌐 [DEBUG] Waiting for network idle...")
            logger.info(f"🌐 [DEBUG] Network idle timeout: {self.config.network_idle_timeout_ms}ms")
            await page.wait_for_load_state('networkidle', timeout=self.config.network_idle_timeout_ms)
            logger.info(f"🌐 [DEBUG] Network idle completed")
            await asyncio.sleep(2.0)  # Extra time for SAP React
            logger.info(f"🌐 [DEBUG] Extra wait for SAP React completed")
            
            logger.info(f"✅ [DEBUG] Navigated to market overview base URL")
            logger.info(f"✅ [DEBUG] Final page URL: {page.url}")
            logger.info(f"✅ [DEBUG] Final page title: {await page.title()}")
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Navigation to base URL failed: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            raise
    
    async def _check_paywall(self, page: Page) -> bool:
        """Check if paywall is present on the page."""
        try:
            logger.info(f"🔍 [DEBUG] Starting paywall check...")
            logger.info(f"🔍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Current page title: {await page.title()}")
            
            # Check for paywall indicator
            logger.info(f"🔍 [DEBUG] Checking for paywall element with selector: *[data-testid=\"paywall\"]")
            paywall_element = await page.query_selector('*[data-testid="paywall"]')
            logger.info(f"🔍 [DEBUG] Paywall element found: {paywall_element is not None}")
            if paywall_element:
                logger.warning("🚫 [DEBUG] Paywall detected on page")
                return True
            
            # Check for other paywall indicators
            logger.info(f"🔍 [DEBUG] Getting page content for paywall indicators...")
            page_content = await page.content()
            logger.info(f"🔍 [DEBUG] Page content length: {len(page_content)} characters")
            
            paywall_indicators = ["paywall", "upgrade"]
            found_indicators = []
            for indicator in paywall_indicators:
                if indicator in page_content.lower():
                    found_indicators.append(indicator)
                    logger.info(f"🔍 [DEBUG] Found paywall indicator: '{indicator}'")
            
            if found_indicators:
                logger.warning(f"🚫 [DEBUG] Paywall indicators found in page content: {found_indicators}")
                return True
            
            logger.info("✅ [DEBUG] No paywall detected")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Error checking paywall: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            return False
    
    async def _check_session_expired(self, page: Page) -> bool:
        """Check if session has expired on the page."""
        try:
            logger.info(f"🔍 [DEBUG] Starting session expired check...")
            logger.info(f"🔍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Current page title: {await page.title()}")
            
            # Get page content to check for session expired message
            logger.info(f"🔍 [DEBUG] Getting page content for session check...")
            page_content = await page.evaluate('document.body.innerText')
            logger.info(f"🔍 [DEBUG] Page content length: {len(page_content)} characters")
            logger.info(f"🔍 [DEBUG] Page content preview: {page_content[:200]}...")
            
            # Check for session expired indicators
            session_expired_indicators = [
                "Session expired",
                "access again from Dashboard",
                "session expired",
                "please login again",
                "authentication required"
            ]
            
            logger.info(f"🔍 [DEBUG] Checking for session expired indicators: {session_expired_indicators}")
            found_indicators = []
            for indicator in session_expired_indicators:
                if indicator.lower() in page_content.lower():
                    found_indicators.append(indicator)
                    logger.warning(f"🚫 [DEBUG] Session expired detected: '{indicator}' found in page content")
                    return True
            
            logger.info("✅ [DEBUG] Session appears to be valid")
            logger.info(f"✅ [DEBUG] No session expired indicators found")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Error checking session status: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            return False
    
    async def _perform_search(self, page: Page, domain: str) -> bool:
        """Perform domain search on the market overview page."""
        try:
            logger.info(f"🔍 [DEBUG] Starting domain search for: {domain}")
            logger.info(f"🔍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Current page title: {await page.title()}")
            
            # Try primary search method (competitors input + analyze button)
            logger.info(f"🔍 [DEBUG] Trying primary search method...")
            primary_success = await self._try_primary_search(page, domain)
            logger.info(f"🔍 [DEBUG] Primary search result: {primary_success}")
            if primary_success:
                logger.info(f"✅ [DEBUG] Primary search successful")
                return True
            
            # Try secondary search method (searchbar)
            logger.info(f"🔍 [DEBUG] Trying secondary search method...")
            secondary_success = await self._try_secondary_search(page, domain)
            logger.info(f"🔍 [DEBUG] Secondary search result: {secondary_success}")
            if secondary_success:
                logger.info(f"✅ [DEBUG] Secondary search successful")
                return True
            
            logger.warning("⚠️ [DEBUG] Both search methods failed")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Search error: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            return False
    
    async def _try_primary_search(self, page: Page, domain: str) -> bool:
        """Try primary search method with competitors input."""
        try:
            logger.info(f"🔍 [DEBUG] Trying primary search method for domain: {domain}")
            logger.info(f"🔍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Current page title: {await page.title()}")
            
            # Check if primary selectors are present
            logger.info(f"🔍 [DEBUG] Looking for competitors input with selector: input[name=\"competitors.0\"]")
            competitors_input = await page.query_selector('input[name="competitors.0"]')
            logger.info(f"🔍 [DEBUG] Competitors input found: {competitors_input is not None}")
            
            logger.info(f"🔍 [DEBUG] Looking for analyze button with selector: button[data-testid=\"analyze-cta\"]")
            analyze_button = await page.query_selector('button[data-testid="analyze-cta"]')
            logger.info(f"🔍 [DEBUG] Analyze button found: {analyze_button is not None}")
            
            if not competitors_input or not analyze_button:
                logger.info("🔍 [DEBUG] Primary search selectors not found")
                logger.info(f"🔍 [DEBUG] Competitors input: {competitors_input}")
                logger.info(f"🔍 [DEBUG] Analyze button: {analyze_button}")
                return False
            
            # Fill domain and submit
            logger.info(f"🔍 [DEBUG] Filling domain: {domain}")
            await competitors_input.fill(domain)
            logger.info(f"🔍 [DEBUG] Domain filled successfully")
            
            logger.info(f"🔍 [DEBUG] Clicking analyze button...")
            await analyze_button.click()
            logger.info(f"🔍 [DEBUG] Analyze button clicked")
            
            # Wait for navigation
            logger.info(f"🔍 [DEBUG] Waiting for DOM content loaded...")
            logger.info(f"🔍 [DEBUG] Navigation timeout: {self.config.navigation_timeout_ms}ms")
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.navigation_timeout_ms)
            logger.info(f"🔍 [DEBUG] DOM content loaded completed")
            await asyncio.sleep(2.0)
            logger.info(f"🔍 [DEBUG] Extra wait completed")
            
            logger.info(f"🔍 [DEBUG] Final page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Final page title: {await page.title()}")
            logger.info("✅ [DEBUG] Primary search method successful")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Primary search method failed: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            return False
    
    async def _try_secondary_search(self, page: Page, domain: str) -> bool:
        """Try secondary search method with searchbar."""
        try:
            logger.info(f"🔍 [DEBUG] Trying secondary search method for domain: {domain}")
            logger.info(f"🔍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Current page title: {await page.title()}")
            
            # Check if secondary selectors are present
            logger.info(f"🔍 [DEBUG] Looking for search input with selector: input[data-test=\"searchbar_input\"]")
            search_input = await page.query_selector('input[data-test="searchbar_input"]')
            logger.info(f"🔍 [DEBUG] Search input found: {search_input is not None}")
            
            logger.info(f"🔍 [DEBUG] Looking for search button with selector: button[data-test=\"searchbar_search_submit\"]")
            search_button = await page.query_selector('button[data-test="searchbar_search_submit"]')
            logger.info(f"🔍 [DEBUG] Search button found: {search_button is not None}")
            
            if not search_input or not search_button:
                logger.info("🔍 [DEBUG] Secondary search selectors not found")
                logger.info(f"🔍 [DEBUG] Search input: {search_input}")
                logger.info(f"🔍 [DEBUG] Search button: {search_button}")
                return False
            
            # Fill domain and submit
            logger.info(f"🔍 [DEBUG] Filling domain: {domain}")
            await search_input.fill(domain)
            logger.info(f"🔍 [DEBUG] Domain filled successfully")
            
            logger.info(f"🔍 [DEBUG] Clicking search button...")
            await search_button.click()
            logger.info(f"🔍 [DEBUG] Search button clicked")
            
            # Wait for navigation
            logger.info(f"🔍 [DEBUG] Waiting for DOM content loaded...")
            logger.info(f"🔍 [DEBUG] Navigation timeout: {self.config.navigation_timeout_ms}ms")
            await page.wait_for_load_state('domcontentloaded', timeout=self.config.navigation_timeout_ms)
            logger.info(f"🔍 [DEBUG] DOM content loaded completed")
            await asyncio.sleep(2.0)
            logger.info(f"🔍 [DEBUG] Extra wait completed")
            
            logger.info(f"🔍 [DEBUG] Final page URL: {page.url}")
            logger.info(f"🔍 [DEBUG] Final page title: {await page.title()}")
            logger.info("✅ [DEBUG] Secondary search method successful")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ [DEBUG] Secondary search method failed: {e}")
            logger.warning(f"⚠️ [DEBUG] Exception type: {type(e).__name__}")
            logger.warning(f"⚠️ [DEBUG] Exception args: {e.args}")
            return False
    
    async def _extract_fid_and_build_url(self, page: Page) -> Optional[str]:
        """Extract FID from current URL and build complete market overview URL."""
        try:
            logger.info(f"📊 [DEBUG] Starting FID extraction and URL building...")
            current_url = page.url
            logger.info(f"📊 [DEBUG] Current URL for FID extraction: {current_url}")
            logger.info(f"📊 [DEBUG] Current page title: {await page.title()}")
            
            # Extract FID from URL
            logger.info(f"📊 [DEBUG] Extracting FID from URL...")
            fid = extract_fid_from_url(current_url)
            logger.info(f"📊 [DEBUG] Extracted FID: {fid}")
            if not fid:
                logger.warning("⚠️ [DEBUG] No FID found in current URL")
                return None
            
            # Build complete URL with parameters
            logger.info(f"📊 [DEBUG] Building date range...")
            from utils.url_params import build_date_range
            date_range = build_date_range()
            logger.info(f"📊 [DEBUG] Date range: {date_range}")
            
            logger.info(f"📊 [DEBUG] Normalizing base URL...")
            base_url = self.server_manager.normalize_url_to_current_server("https://semrush1.semrush.pw/analytics/traffic/market-overview/")
            logger.info(f"📊 [DEBUG] Normalized base URL: {base_url}")
            
            logger.info(f"📊 [DEBUG] Building complete market overview URL...")
            complete_url = build_market_overview_url(
                base_url=base_url,
                fid=fid,
                date_range=date_range,
                country="us"
            )
            
            logger.info(f"📊 [DEBUG] Built complete URL: {complete_url}")
            logger.info(f"✅ [DEBUG] FID extraction and URL building successful")
            return complete_url
            
        except Exception as e:
            logger.error(f"❌ [DEBUG] Error extracting FID and building URL: {e}")
            logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] Exception args: {e.args}")
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

