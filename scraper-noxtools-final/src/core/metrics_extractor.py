#!/usr/bin/env python3
"""
Metrics extractor for Noxtools scraper (Alpha)
- Extraction des métriques via sélecteurs DOM
- Gestion des pages SAP React
- Logging des métriques extraites
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import urlparse, urlencode, parse_qs

from playwright.async_api import Page

from .anti_detection import get_default_stealth_config, StealthConfig
from .playwright_manager import PlaywrightManager
from .session_manager import SessionManager
from .server_manager import get_server_manager
from utils.url_params import build_overview_url, build_date_range

logger = logging.getLogger(__name__)

@dataclass
class MetricsConfig:
    """Configuration for metrics extraction from Noxtools."""
    # URL des métriques (hardcodée pour Alpha)
    metrics_url: str = "https://semrush1.semrush.pw/analytics/traffic/market-overview?searchType=domain&fid=1355702&date=202507&country=us"
    # URL dashboard (utilisée comme Referer pour réactiver la session)
    dashboard_url: str = "https://noxtools.com/secure/member"
    # URL passerelle Noxtools → Semrush (réactive la session côté Semrush)
    # Note: Cette URL sera remplacée par ServerManager.get_current_bridge_url()
    bridge_url: str = "https://semrush.noxtools.com/server1.php"
    # URL overview pour CPC (Alpha hardcodée)
    overview_url: str = "https://semrush3.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507"
    
    # Sélecteurs des métriques (à enregistrer en BDD plus tard)
    selectors: Dict[str, str] = None
    
    # Configuration d'extraction
    max_retries: int = 3
    timeout_ms: int = 30000
    react_load_delay_ms: int = 5000  # Délai pour le chargement SAP React
    stabilization_delay_ms: int = 3000
    
    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {
                # Sélecteurs pour extraire les VALEURS (pas les labels)
                # On prend la 2ème occurrence de chaque sélecteur (valeurs au lieu des labels)
                'visits': '[name="entrances"]:nth-of-type(2)',
                'organic_search_traffic': '[name="entrancesSearchOrganic"]:nth-of-type(2)',
                'paid_search_traffic': '[name="entrancesSearchPaid"]:nth-of-type(2)',
                'purchase_conversion': '[name="purchasesPerVisit"]:nth-of-type(2)',
                'avg_visit_duration': '[name="avgVisitDuration"]:nth-of-type(2)',
                'bounce_rate': '[name="bouncesPerVisit"]:nth-of-type(2)'
            }

@dataclass
class ExtractedMetrics:
    """Structure des métriques extraites."""
    visits: Optional[str] = None
    organic_search_traffic: Optional[str] = None
    paid_search_traffic: Optional[str] = None
    purchase_conversion: Optional[str] = None
    avg_visit_duration: Optional[str] = None
    bounce_rate: Optional[str] = None
    cpc: Optional[str] = None
    
    # Métadonnées
    extraction_timestamp: Optional[str] = None
    url: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'visits': self.visits,
            'organic_search_traffic': self.organic_search_traffic,
            'paid_search_traffic': self.paid_search_traffic,
            'purchase_conversion': self.purchase_conversion,
            'avg_visit_duration': self.avg_visit_duration,
            'bounce_rate': self.bounce_rate,
            'cpc': self.cpc,
            'extraction_timestamp': self.extraction_timestamp,
            'url': self.url,
            'success': self.success,
            'error_message': self.error_message
        }

class MetricsExtractor:
    """Extracteur de métriques Noxtools avec gestion SAP React."""
    
    def __init__(self, config: Optional[MetricsConfig] = None, stealth_config: Optional[StealthConfig] = None):
        self.config = config or MetricsConfig()
        self.stealth_config = stealth_config or get_default_stealth_config()
        self.server_manager = get_server_manager()
        
    async def extract_metrics(self, page: Page, playwright_manager: PlaywrightManager, 
                            session_manager: SessionManager, shop_url: str = None) -> ExtractedMetrics:
        """Extract metrics from the Noxtools analytics page.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            session_manager: SessionManager instance
            
        Returns:
            ExtractedMetrics: Extracted metrics data
        """
        metrics = ExtractedMetrics()
        metrics.url = self.config.metrics_url
        
        try:
            logger.info("📊 [DEBUG] Starting metrics extraction from Noxtools...")
            logger.info(f"📍 [DEBUG] Metrics URL: {self.config.metrics_url}")
            logger.info(f"📍 [DEBUG] Input shop_url: {shop_url}")
            logger.info(f"📍 [DEBUG] Current page URL: {page.url}")
            logger.info(f"📍 [DEBUG] Current page title: {await page.title()}")
            
            # Navigate to metrics page (via dashboard referer, capture network)
            logger.info("🌐 [DEBUG] Starting navigation to metrics page...")
            navigation_success = await self._navigate_to_metrics_page(
                page, playwright_manager, session_manager
            )
            logger.info(f"🌐 [DEBUG] Navigation success: {navigation_success}")
            
            if not navigation_success:
                metrics.error_message = "Failed to navigate to metrics page"
                logger.error("❌ [DEBUG] Failed to navigate to metrics page")
                return metrics
                
            # Wait for SAP React to load
            logger.info(f"⏳ [DEBUG] Waiting for SAP React to load... (delay: {self.config.react_load_delay_ms}ms)")
            await asyncio.sleep(self.config.react_load_delay_ms / 1000.0)
            logger.info("⏳ [DEBUG] SAP React wait completed")
            
            # Wait for page to stabilize
            logger.info(f"⏳ [DEBUG] Waiting for page to stabilize... (delay: {self.config.stabilization_delay_ms}ms)")
            await asyncio.sleep(self.config.stabilization_delay_ms / 1000.0)
            logger.info("⏳ [DEBUG] Page stabilization completed")
            
            # DEBUG: Display page content for analysis
            logger.info("🔍 [DEBUG] ===== PAGE CONTENT ANALYSIS =====")
            try:
                page_title = await page.title()
                logger.info(f"🔍 [DEBUG] Page title: {page_title}")
                
                page_url = page.url
                logger.info(f"🔍 [DEBUG] Page URL: {page_url}")
                
                # Get page content
                page_content = await page.content()
                logger.info(f"🔍 [DEBUG] Page content length: {len(page_content)} characters")
                
                # Get visible text content
                visible_text = await page.evaluate('document.body.innerText')
                logger.info(f"🔍 [DEBUG] Visible text length: {len(visible_text)} characters")
                logger.info(f"🔍 [DEBUG] Visible text preview (first 500 chars): {visible_text[:500]}")
                
                # Check for specific elements
                logger.info("🔍 [DEBUG] Checking for specific elements...")
                
                # Check for data tables
                tables = await page.query_selector_all('table')
                logger.info(f"🔍 [DEBUG] Found {len(tables)} tables on page")
                
                # Check for grid elements
                grid_elements = await page.query_selector_all('[role="grid"]')
                logger.info(f"🔍 [DEBUG] Found {len(grid_elements)} grid elements")
                
                # Check for specific selectors we're looking for
                target_selectors = [
                    '[data-ui-name="Flex"][role="gridcell"]',
                    '[name="entrances"]',
                    '[name="entrancesSearchOrganic"]',
                    '[name="entrancesSearchPaid"]',
                    '[name="purchasesPerVisit"]',
                    '[name="avgVisitDuration"]',
                    '[name="bouncesPerVisit"]'
                ]
                
                for selector in target_selectors:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"🔍 [DEBUG] Selector '{selector}': {len(elements)} elements found")
                    if elements:
                        for i, element in enumerate(elements[:3]):  # Show first 3 elements
                            try:
                                text = await element.inner_text()
                                logger.info(f"🔍 [DEBUG] Element {i+1} text: '{text[:100]}...'")
                            except:
                                logger.info(f"🔍 [DEBUG] Element {i+1}: Could not get text")
                
                # Check for error messages
                error_indicators = ['error', 'not found', 'no data', 'loading', 'session expired']
                for indicator in error_indicators:
                    if indicator.lower() in visible_text.lower():
                        logger.warning(f"🔍 [DEBUG] Found error indicator: '{indicator}'")
                
                logger.info("🔍 [DEBUG] ===== END PAGE CONTENT ANALYSIS =====")
                
            except Exception as e:
                logger.error(f"🔍 [DEBUG] Error analyzing page content: {e}")
            
            # Try network capture assisted extraction first
            logger.info("🔍 [DEBUG] Starting network capture assisted extraction...")
            network_data = await self._capture_network_metrics(page)
            logger.info(f"🔍 [DEBUG] Network data result: {network_data}")

            if network_data:
                logger.info("✅ [DEBUG] Network data found, populating metrics...")
                self._populate_metrics_from_network(metrics, network_data)
                metrics.success = True
                logger.info("✅ [DEBUG] Metrics extracted from network responses")
                self._log_extracted_metrics(metrics)
                return metrics

            # Fallback: Extract from DOM
            logger.info("🔍 [DEBUG] Network capture failed, trying DOM extraction...")
            extraction_success = await self._extract_metrics_from_page(page, metrics)
            logger.info(f"🔍 [DEBUG] DOM extraction success: {extraction_success}")
            
            # Extract CPC data from overview page with retry
            logger.info("💰 [DEBUG] Starting CPC extraction from overview page...")
            logger.info(f"💰 [DEBUG] Shop URL for CPC: {shop_url}")
            cpc_data = await self._extract_cpc_with_retry(page, playwright_manager, session_manager, shop_url)
            logger.info(f"💰 [DEBUG] CPC data result: {cpc_data}")
            
            if cpc_data and cpc_data.get('cpc') is not None:
                metrics.cpc = str(cpc_data['cpc'])
                logger.info(f"✅ [DEBUG] CPC extracted: {cpc_data['cpc']} (keyword: {cpc_data.get('keyword', 'N/A')})")
            else:
                logger.warning("⚠️ [DEBUG] No CPC data found after all retries")
                metrics.cpc = None
            
            if extraction_success:
                metrics.success = True
                logger.info("✅ [DEBUG] Metrics extraction successful")
                self._log_extracted_metrics(metrics)
            else:
                metrics.error_message = "Failed to extract metrics from page"
                logger.error("❌ [DEBUG] Failed to extract metrics from page")
                
        except Exception as e:
            metrics.error_message = str(e)
            logger.error(f"❌ [DEBUG] Metrics extraction error: {e}")
            logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] Exception args: {e.args}")
            
        logger.info(f"✅ [DEBUG] Metrics extraction process completed")
        return metrics

    async def _extract_cpc_with_retry(self, page: Page, playwright_manager: PlaywrightManager,
                                    session_manager: SessionManager, shop_url: str = None) -> Optional[Dict[str, Any]]:
        """Extract CPC with retry mechanism and dynamic URL construction.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            session_manager: SessionManager instance
            shop_url: Shop URL to extract domain for CPC extraction
            
        Returns:
            CPC data dict or None if failed
        """
        if not shop_url:
            logger.warning("⚠️ No shop_url provided for CPC extraction")
            return None
            
        # Extract domain from shop_url
        from urllib.parse import urlparse
        parsed_url = urlparse(shop_url)
        domain = parsed_url.netloc or parsed_url.path
        if domain.startswith('www.'):
            domain = domain[4:]
        
        logger.info(f"🔍 Extracting CPC for domain: {domain}")
        
        # Build dynamic overview URL using current server
        date_range = build_date_range()
        
        # Use current server instead of config overview_url to avoid server switching
        current_server = self.server_manager.get_current_server_name()
        overview_base_url = f"https://{current_server}.semrush.pw/analytics/overview/"
        
        logger.info(f"🔗 [DEBUG] Using current server for overview: {current_server}")
        logger.info(f"🔗 [DEBUG] Overview base URL: {overview_base_url}")
        
        dynamic_overview_url = build_overview_url(
            base_url=overview_base_url,
            shop_url=domain,
            date_range=date_range,
            country="us",
            search_type="domain"
        )
        
        logger.info(f"📍 Dynamic overview URL: {dynamic_overview_url}")
        
        # Retry mechanism
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"🔄 CPC extraction attempt {attempt + 1}/{self.config.max_retries}")
                
                # Use the dynamic URL for CPC extraction
                cpc_data = await self._extract_cpc_from_overview(
                    page, playwright_manager, session_manager, dynamic_overview_url
                )
                
                if cpc_data and cpc_data.get('cpc') is not None:
                    logger.info(f"✅ CPC extraction successful on attempt {attempt + 1}")
                    return cpc_data
                else:
                    logger.warning(f"⚠️ CPC extraction failed on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"⚠️ CPC extraction error on attempt {attempt + 1}: {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(2.0)
        
        logger.error("❌ CPC extraction failed after all retries")
        return None

    async def _extract_cpc_from_overview(self, page: Page, playwright_manager: PlaywrightManager,
                                       session_manager: SessionManager, overview_url: str) -> Optional[Dict[str, Any]]:
        """Extract CPC from overview page with session maintenance.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            session_manager: SessionManager instance
            overview_url: Dynamic overview URL
            
        Returns:
            CPC data dict or None if failed
        """
        try:
            # Navigate to overview page with session maintenance
            navigation_success = await session_manager.navigate_cross_domain(
                page, playwright_manager, overview_url
            )
            
            if not navigation_success:
                logger.warning("⚠️ Failed to navigate to overview page, trying direct navigation")
                try:
                    await page.goto(overview_url, timeout=self.config.timeout_ms)
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    navigation_success = True
                except Exception as e:
                    logger.error(f"❌ Direct navigation to overview failed: {e}")
                    return None
            
            if not navigation_success:
                logger.error("❌ Failed to navigate to overview page")
                return None
            
            # Check for session expired
            try:
                page_content = await page.content()
                if "Session expired" in page_content or "access again from Dashboard" in page_content:
                    logger.error("❌ Session expired on overview page")
                    return None
            except Exception as e:
                logger.warning(f"⚠️ Could not check page content: {e}")
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(2.0)
            
            # Extract CPC using the existing logic
            return await self._extract_cpc_from_page(page)
            
        except Exception as e:
            logger.error(f"❌ CPC extraction from overview error: {e}")
            return None

    async def _extract_cpc_from_page(self, page: Page) -> Optional[Dict[str, Any]]:
        """Extract CPC data from the current page using existing logic."""
        try:
            # Wait for grid presence
            try:
                await page.wait_for_selector('div[data-ui-name="Body.Row"]', timeout=10000)
                logger.info("✅ Found Body.Row elements for CPC extraction")
            except Exception as e:
                logger.warning(f"⚠️ Body.Row not found, trying volume cells: {e}")
                try:
                    await page.wait_for_selector('div[name="volume"][role="gridcell"] [data-at="value-volume"]', timeout=8000)
                    logger.info("✅ Found volume cells for CPC extraction")
                except Exception as e2:
                    logger.warning(f"⚠️ Volume cells not found either: {e2}")

            # Scroll to force virtualization
            async def _scroll_grid():
                try:
                    await page.evaluate("""
                        () => {
                          const cont = document.querySelector('[data-ui-name="Body"]') || document.scrollingElement || document.body;
                          let y = 0; let steps = 0;
                          const max = (cont.scrollHeight || 0) - (cont.clientHeight || 0);
                          while (y < max && steps < 8) { y += Math.max(200, (cont.clientHeight||0)/2); cont.scrollTo(0, y); steps++; }
                          return true;
                        }
                    """)
                    logger.debug("✅ Grid scrolled using container method")
                except Exception as e:
                    logger.debug(f"⚠️ Container scroll failed, using window scroll: {e}")
                    for _ in range(6):
                        await page.evaluate('window.scrollBy(0, Math.max(300, window.innerHeight/2))')
                        await asyncio.sleep(0.25)
                    logger.debug("✅ Grid scrolled using window method")

            # Extract CPC data
            eval_script = r"""
            () => {
              const parseNum = (s) => {
                if (!s) return NaN;
                const t = s.trim().replace(/[,%]/g,'').replace(/[, ]/g,'');
                const m = t.match(/^([\d.]+)([KkMm])?$/);
                if (!m) {
                  const v = parseFloat(t);
                  return isFinite(v) ? v : NaN;
                }
                const n = parseFloat(m[1]);
                const mul = m[2] ? (m[2].toLowerCase()==='k' ? 1e3 : 1e6) : 1;
                return n * mul;
              };
              let best = null;
              const rows = document.querySelectorAll('div[data-ui-name="Body.Row"]');
              rows.forEach(row => {
                const q = (sel) => row.querySelector(sel)?.textContent?.trim() ?? '';
                const kw   = q('div[name="phrase"] a');
                const vol  = parseNum(q('div[name="volume"][role="gridcell"] [data-at="value-volume"]'));
                const traf = parseNum(q('div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]'));
                const cpcT = q('div[name="cpc"][role="gridcell"] [data-at="value-cpc"]');
                const cpc  = parseNum(cpcT);
                if (!isFinite(vol) || !isFinite(traf) || traf <= 0) return;
                const ratio = vol / traf;
                if (!best || ratio > best.ratio) best = { keyword: kw, ratio, cpc, cpcRaw: cpcT };
              });
              return best;
            }
            """
            
            best = None
            for attempt in range(3):
                try:
                    best = await page.evaluate(eval_script)
                    logger.debug(f"CPC evaluation attempt {attempt + 1}: {best}")
                except Exception as e:
                    logger.warning(f"⚠️ CPC evaluation attempt {attempt + 1} failed: {e}")
                    best = None
                if best and best.get('cpc') is not None:
                    logger.info(f"✅ CPC found on attempt {attempt + 1}: {best}")
                    break
                if attempt < 2:  # Don't scroll on last attempt
                    await _scroll_grid()
                    await asyncio.sleep(0.5)
            
            if not best or best.get('cpc') is None:
                logger.warning("⚠️ No CPC data found after all attempts")
            return best
            
        except Exception as e:
            logger.error(f"❌ CPC extraction from page error: {e}")
            return None

    async def extract_cpc_best_ratio(self, page: Page, playwright_manager: PlaywrightManager,
                                     session_manager: SessionManager) -> Optional[Dict[str, Any]]:
        """Extract CPC based on max(volume/traffic) from overview grid.
        Returns dict: { keyword, ratio, cpc, cpcRaw }
        """
        try:
            # Step 1: Use the same session refresh flow as metrics extraction
            # Navigate to dashboard first to refresh session
            try:
                await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.warning(f"⚠️ Unable to visit dashboard before CPC extraction: {e}")

            # Step 2: Hit the Noxtools → Semrush bridge (ServerManager)
            try:
                server_manager = get_server_manager()
                bridge_url = server_manager.get_current_bridge_url()
                logger.info(f"🌉 Visiting bridge URL for CPC: {bridge_url}")
                await page.goto(bridge_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                await asyncio.sleep(1.0)
                logger.info("✅ Bridge URL visited successfully for CPC")
            except Exception as e:
                logger.warning(f"⚠️ Bridge URL visit failed for CPC: {e}")

            # Step 3: Navigate to overview URL for CPC extraction
            # Use the same approach as _navigate_to_metrics_page for consistency
            navigation_success = False
            try:
                # First try session manager for cross-domain navigation
                navigation_success = await session_manager.navigate_cross_domain(
                    page, playwright_manager, self.config.overview_url
                )
            except Exception as e:
                logger.warning(f"⚠️ Cross-domain navigation error for CPC: {e}")

            # If session manager failed, try direct navigation with referer
            if not navigation_success:
                try:
                    await page.goto(self.config.overview_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                    navigation_success = True
                    logger.info("✅ Direct navigation to CPC page with referer succeeded")
                except Exception as e:
                    logger.warning(f"⚠️ Direct navigation with referer failed for CPC: {e}")
            
            if not navigation_success:
                logger.error("❌ Failed to navigate to CPC page")
                return None
            
            # Log current URL to debug session issues
            current_url = page.url
            logger.info(f"📍 Current URL after CPC navigation: {current_url}")
            
            # Check if we got session expired message
            try:
                page_content = await page.content()
                if "Session expired" in page_content or "access again from Dashboard" in page_content:
                    logger.error("❌ Session expired on CPC page - need to refresh session")
                    return None
            except Exception as e:
                logger.warning(f"⚠️ Could not check page content: {e}")
            
            # Network settle + extra RAFs for SAP React
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception as e:
                logger.warning(f"⚠️ Network idle wait failed for CPC page: {e}")
            await asyncio.sleep(2.0)

            # Step 2b: Wait grid presence
            try:
                await page.wait_for_selector('div[data-ui-name="Body.Row"]', timeout=10000)
                logger.info("✅ Found Body.Row elements for CPC extraction")
            except Exception as e:
                logger.warning(f"⚠️ Body.Row not found, trying volume cells: {e}")
                try:
                    await page.wait_for_selector('div[name="volume"][role="gridcell"] [data-at="value-volume"]', timeout=8000)
                    logger.info("✅ Found volume cells for CPC extraction")
                except Exception as e2:
                    logger.warning(f"⚠️ Volume cells not found either: {e2}")

            # Helper: scroll to force virtualization to render rows
            async def _scroll_grid():
                try:
                    await page.evaluate("""
                        () => {
                          const cont = document.querySelector('[data-ui-name="Body"]') || document.scrollingElement || document.body;
                          let y = 0; let steps = 0;
                          const max = (cont.scrollHeight || 0) - (cont.clientHeight || 0);
                          while (y < max && steps < 8) { y += Math.max(200, (cont.clientHeight||0)/2); cont.scrollTo(0, y); steps++; }
                          return true;
                        }
                    """)
                    logger.debug("✅ Grid scrolled using container method")
                except Exception as e:
                    logger.debug(f"⚠️ Container scroll failed, using window scroll: {e}")
                    for _ in range(6):
                        await page.evaluate('window.scrollBy(0, Math.max(300, window.innerHeight/2))')
                        await asyncio.sleep(0.25)
                    logger.debug("✅ Grid scrolled using window method")

            # Step 3: Evaluate table-like grid with retries
            eval_script = r"""
            () => {
              const parseNum = (s) => {
                if (!s) return NaN;
                const t = s.trim().replace(/[,%]/g,'').replace(/[, ]/g,'');
                const m = t.match(/^([\d.]+)([KkMm])?$/);
                if (!m) {
                  const v = parseFloat(t);
                  return isFinite(v) ? v : NaN;
                }
                const n = parseFloat(m[1]);
                const mul = m[2] ? (m[2].toLowerCase()==='k' ? 1e3 : 1e6) : 1;
                return n * mul;
              };
              let best = null;
              const rows = document.querySelectorAll('div[data-ui-name="Body.Row"]');
              rows.forEach(row => {
                const q = (sel) => row.querySelector(sel)?.textContent?.trim() ?? '';
                const kw   = q('div[name="phrase"] a');
                const vol  = parseNum(q('div[name="volume"][role="gridcell"] [data-at="value-volume"]'));
                const traf = parseNum(q('div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]'));
                const cpcT = q('div[name="cpc"][role="gridcell"] [data-at="value-cpc"]');
                const cpc  = parseNum(cpcT);
                if (!isFinite(vol) || !isFinite(traf) || traf <= 0) return;
                const ratio = vol / traf;
                if (!best || ratio > best.ratio) best = { keyword: kw, ratio, cpc, cpcRaw: cpcT };
              });
              return best;
            }
            """
            best = None
            for attempt in range(3):
                try:
                    best = await page.evaluate(eval_script)
                    logger.debug(f"CPC evaluation attempt {attempt + 1}: {best}")
                except Exception as e:
                    logger.warning(f"⚠️ CPC evaluation attempt {attempt + 1} failed: {e}")
                    best = None
                if best and best.get('cpc') is not None:
                    logger.info(f"✅ CPC found on attempt {attempt + 1}: {best}")
                    break
                if attempt < 2:  # Don't scroll on last attempt
                    await _scroll_grid()
                    await asyncio.sleep(0.5)
            
            if not best or best.get('cpc') is None:
                logger.warning("⚠️ No CPC data found after all attempts")
            return best
        except Exception as e:
            logger.error(f"❌ CPC extraction error: {e}")
            return None
    
    async def _navigate_to_metrics_page(self, page: Page, playwright_manager: PlaywrightManager,
                                      session_manager: SessionManager) -> bool:
        """Navigate to the metrics page."""
        try:
            logger.info("🌐 Navigating to metrics page...")
            
            # Step 1: Ensure dashboard is visited to refresh session (referer source)
            try:
                await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.warning(f"⚠️ Unable to visit dashboard before metrics: {e}")

            # Step 2: Hit the Noxtools → Semrush bridge to refresh/carry session/token
            try:
                server_manager = get_server_manager()
                bridge_url = server_manager.get_current_bridge_url()
                logger.info(f"🌉 Visiting bridge URL: {bridge_url}")
                await page.goto(bridge_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                await asyncio.sleep(1.0)
                logger.info("✅ Bridge URL visited successfully")
            except Exception as e:
                logger.warning(f"⚠️ Bridge URL visit failed: {e}")

            # Step 3: Prefer clicking the actual dashboard link to Semrush (carries auth context)
            try:
                # Try to locate the semrush link on dashboard
                link_selector = 'a[href*="semrush1.semrush.pw/analytics/traffic/market-overview"], a[href*="/analytics/traffic/market-overview"]'
                link = await page.query_selector(link_selector)
                if link:
                    href = await link.get_attribute('href')
                    logger.info(f"🔗 Found metrics link on dashboard: {href}")
                    try:
                        await link.click()
                        await page.wait_for_load_state('domcontentloaded', timeout=self.config.timeout_ms)
                        logger.info("✅ Clicked dashboard link to metrics page")
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ Click navigation failed, trying location change: {e}")
                        if href:
                            await page.evaluate("url => window.location.href = url", href)
                            await page.wait_for_load_state('domcontentloaded', timeout=self.config.timeout_ms)
                            logger.info("✅ Navigated via window.location to metrics page")
                            return True
            except Exception as e:
                logger.debug(f"Dashboard link navigation attempt failed: {e}")

            # Step 4: Use session manager for cross-domain navigation with referer
            navigation_success = False
            try:
                # First jump to same domain context if needed
                navigation_success = await session_manager.navigate_cross_domain(
                    page, playwright_manager, self.config.metrics_url
                )
            except Exception as e:
                logger.warning(f"⚠️ Cross-domain navigation error: {e}")

            # If already on target domain, enforce referer on direct goto
            try:
                await page.goto(self.config.metrics_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                navigation_success = True
            except Exception as e:
                logger.warning(f"⚠️ Direct navigation with referer failed: {e}")
            
            if navigation_success:
                logger.info("✅ Successfully navigated to metrics page")
                return True
            else:
                logger.error("❌ Failed to navigate to metrics page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Navigation to metrics page error: {e}")
            return False
    
    async def _extract_metrics_from_page(self, page: Page, metrics: ExtractedMetrics) -> bool:
        """Extract metrics from the current page."""
        try:
            logger.info("🔍 Extracting metrics from page...")
            
            # Check if we're on the right page
            current_url = page.url
            if 'analytics/traffic/market-overview' not in current_url:
                logger.warning(f"⚠️ Not on metrics page: {current_url}")
                return False
                
            # Check for session expired message
            try:
                page_content = await page.content()
                if 'Session expired' in page_content or 'access again from Dashboard' in page_content:
                    logger.warning("⚠️ Session expired detected on metrics page")
                    metrics.error_message = "Session expired on metrics page"
                    return False
            except Exception as e:
                logger.debug(f"Content check error: {e}")
                
            # Wait for React to fully load
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
                logger.info("✅ Page network idle state reached")
            except Exception as e:
                logger.warning(f"⚠️ Network idle timeout: {e}")
                
            # Additional wait for React components
            await asyncio.sleep(2000 / 1000.0)  # 2 seconds
                
            # Extract each metric
            extraction_results = {}
            
            for metric_name, selector in self.config.selectors.items():
                try:
                    value = await self._extract_single_metric(page, selector, metric_name)
                    extraction_results[metric_name] = value
                    
                    # Set the value in the metrics object
                    if hasattr(metrics, metric_name):
                        setattr(metrics, metric_name, value)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract {metric_name}: {e}")
                    extraction_results[metric_name] = None
                    
            # Log extraction results
            logger.info("📊 Metrics extraction results:")
            for metric_name, value in extraction_results.items():
                if value:
                    logger.info(f"  ✅ {metric_name}: {value}")
                else:
                    logger.warning(f"  ❌ {metric_name}: Not found")
                    
            # Check if we extracted at least one metric
            successful_extractions = sum(1 for v in extraction_results.values() if v is not None)
            if successful_extractions > 0:
                logger.info(f"✅ Successfully extracted {successful_extractions}/{len(extraction_results)} metrics")
                return True
            else:
                logger.error("❌ No metrics extracted")
                return False
                
        except Exception as e:
            logger.error(f"❌ Metrics extraction error: {e}")
            return False

    async def _capture_network_metrics(self, page: Page) -> Dict[str, Any]:
        """Capture XHR/Fetch JSON responses and try to extract metrics."""
        collected: List[Dict[str, Any]] = []

        def is_candidate_response(url: str, headers: Dict[str, str]) -> bool:
            ctype = headers.get('content-type', '')
            return (
                'analytics' in url or 'market' in url or 'overview' in url or 'api' in url or 'traffic' in url
            ) and ('application/json' in ctype or 'json' in ctype)

        async def on_response(response):
            try:
                req = response.request
                url = response.url
                headers = {k.lower(): v for k, v in (response.headers or {}).items()}
                if is_candidate_response(url, headers):
                    data = None
                    try:
                        data = await response.json()
                    except Exception:
                        text = await response.text()
                        data = {'_raw': text}
                    collected.append({'url': url, 'data': data})
            except Exception:
                pass

        page.on('response', on_response)

        # Allow network to settle and collect responses
        await asyncio.sleep(3.0)

        # Stop listening
        try:
            page.off('response', on_response)
        except Exception:
            pass

        # Try to extract metrics from collected responses
        parsed: Dict[str, Any] = {}
        keys_map = {
            'visits': ['entrances', 'visits', 'sessions'],
            'organic_search_traffic': ['entrancesSearchOrganic', 'organic', 'organicTraffic', 'organic_visits'],
            'paid_search_traffic': ['entrancesSearchPaid', 'paid', 'paidTraffic', 'paid_visits'],
            'purchase_conversion': ['purchasesPerVisit', 'conversion', 'convRate'],
            'avg_visit_duration': ['avgVisitDuration', 'avgDuration', 'duration'],
            'bounce_rate': ['bouncesPerVisit', 'bounce', 'bounceRate'],
            'cpc': ['cpc']
        }

        def deep_find(obj: Any, targets: List[str]) -> Optional[str]:
            try:
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        lk = str(k).lower()
                        if any(t.lower() == lk for t in targets):
                            if isinstance(v, (str, int, float)):
                                return str(v)
                        res = deep_find(v, targets)
                        if res is not None:
                            return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = deep_find(item, targets)
                        if res is not None:
                            return res
                else:
                    return None
            except Exception:
                return None
            return None

        for item in collected:
            data = item.get('data')
            if not data:
                continue
            for out_key, candidates in keys_map.items():
                if out_key in parsed and parsed[out_key]:
                    continue
                val = deep_find(data, candidates)
                if val is not None:
                    parsed[out_key] = val

        return parsed

    def _populate_metrics_from_network(self, metrics: ExtractedMetrics, parsed: Dict[str, Any]) -> None:
        """Populate metrics object from parsed network data."""
        field_map = {
            'visits': 'visits',
            'organic_search_traffic': 'organic_search_traffic',
            'paid_search_traffic': 'paid_search_traffic',
            'purchase_conversion': 'purchase_conversion',
            'avg_visit_duration': 'avg_visit_duration',
            'bounce_rate': 'bounce_rate'
        }
        for src, dst in field_map.items():
            val = parsed.get(src)
            if val:
                setattr(metrics, dst, val)
    
    async def _extract_single_metric(self, page: Page, selector: str, metric_name: str) -> Optional[str]:
        """Extract a single metric using the provided selector (with relaxed fallbacks)."""
        try:
            # Try multiple approaches for React-rendered elements
            value: Optional[str] = None

            async def read_element_text(el) -> Optional[str]:
                try:
                    try:
                        await el.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    txt = await el.text_content()
                    if txt and txt.strip():
                        return txt.strip()
                    inner = await page.evaluate('(el)=>el.innerText', el)
                    if inner and inner.strip():
                        return inner.strip()
                    aria = await el.get_attribute('aria-label')
                    if aria and aria.strip():
                        return aria.strip()
                    title = await el.get_attribute('title')
                    if title and title.strip():
                        return title.strip()
                except Exception:
                    return None
                return None

            # Build relaxed selector variants for gridcells (drop tabindex/aria-colindex)
            relaxed_variants: List[str] = []
            if '[role="gridcell"]' in selector:
                base = selector
                import re
                base = re.sub(r"\[tabindex=\"?-?\d+\"?\]", "", base)
                base = re.sub(r"\[aria-colindex=\"?\d+\"?\]", "", base)
                relaxed_variants.append(base)

            # 1) Direct selector - prendre le 2ème élément (valeur au lieu du label)
            try:
                elements = await page.query_selector_all(selector)
                if len(elements) >= 2:
                    # Prendre le 2ème élément (valeur) au lieu du 1er (label)
                    element = elements[1]
                    text = await read_element_text(element)
                    if text:
                        logger.debug(f"✅ Extracted {metric_name} (direct, 2nd element): {text}")
                        return text
                elif len(elements) == 1:
                    # Fallback: prendre le 1er élément si pas de 2ème
                    element = elements[0]
                    text = await read_element_text(element)
                    if text:
                        logger.debug(f"✅ Extracted {metric_name} (direct, 1st element fallback): {text}")
                        return text
            except Exception as e:
                logger.debug(f"Direct selector failed for {metric_name}: {e}")

            # 1b) Relaxed variants - prendre le 2ème élément
            for sel in relaxed_variants:
                try:
                    elements = await page.query_selector_all(sel)
                    if len(elements) >= 2:
                        element = elements[1]  # 2ème élément (valeur)
                        text = await read_element_text(element)
                        if text:
                            logger.debug(f"✅ Extracted {metric_name} (relaxed, 2nd element): {text}")
                            return text
                    elif len(elements) == 1:
                        element = elements[0]  # Fallback
                        text = await read_element_text(element)
                        if text:
                            logger.debug(f"✅ Extracted {metric_name} (relaxed, 1st element fallback): {text}")
                            return text
                except Exception as e:
                    logger.debug(f"Relaxed selector failed for {metric_name}: {e}")

            # 2) Attribute selector [name="..."] - prendre le 2ème élément
            try:
                if 'name=' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    attr_selector = f'[name="{attr_name}"]'
                    elements = await page.query_selector_all(attr_selector)
                    if len(elements) >= 2:
                        element = elements[1]  # 2ème élément (valeur)
                        text = await read_element_text(element)
                        if text:
                            logger.debug(f"✅ Extracted {metric_name} (attr, 2nd element): {text}")
                            return text
                    elif len(elements) == 1:
                        element = elements[0]  # Fallback
                        text = await read_element_text(element)
                        if text:
                            logger.debug(f"✅ Extracted {metric_name} (attr, 1st element fallback): {text}")
                            return text
            except Exception as e:
                logger.debug(f"Attribute selector failed for {metric_name}: {e}")

            # 3) Input value
            try:
                if 'name=' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    input_selector = f'input[name="{attr_name}"]'
                    element = await page.wait_for_selector(input_selector, timeout=3000, state='attached')
                    if element:
                        input_value = await element.input_value()
                        if input_value and input_value.strip():
                            logger.debug(f"✅ Extracted {metric_name} (input): {input_value.strip()}")
                            return input_value.strip()
            except Exception as e:
                logger.debug(f"Input selector failed for {metric_name}: {e}")

            # 4) Span inside named container
            try:
                if 'name=' in selector and '> span' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    span_selector = f'[name="{attr_name}"] span'
                    element = await page.wait_for_selector(span_selector, timeout=3000, state='attached')
                    if element:
                        text_content = await element.text_content()
                        if text_content and text_content.strip():
                            logger.debug(f"✅ Extracted {metric_name} (span): {text_content.strip()}")
                            return text_content.strip()
            except Exception as e:
                logger.debug(f"Span selector failed for {metric_name}: {e}")

            logger.warning(f"⚠️ {metric_name} not found with any approach (selector: {selector})")
            return None

        except Exception as e:
            logger.debug(f"⚠️ Error extracting {metric_name}: {e}")
            return None
    
    def _log_extracted_metrics(self, metrics: ExtractedMetrics):
        """Log the extracted metrics in a formatted way."""
        logger.info("📊 EXTRACTED METRICS SUMMARY:")
        logger.info("=" * 50)
        
        metrics_dict = metrics.to_dict()
        for key, value in metrics_dict.items():
            if key in ['success', 'error_message', 'extraction_timestamp', 'url']:
                continue
                
            if value:
                logger.info(f"  {key.replace('_', ' ').title()}: {value}")
            else:
                logger.warning(f"  {key.replace('_', ' ').title()}: Not found")
                
        logger.info("=" * 50)
        logger.info(f"  Success: {metrics.success}")
        if metrics.error_message:
            logger.info(f"  Error: {metrics.error_message}")
            
    async def get_metrics_info(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive metrics extraction information."""
        try:
            current_url = page.url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            return {
                'metrics_url': self.config.metrics_url,
                'current_url': current_url,
                'url_valid': 'analytics/traffic/market-overview' in current_url,
                'query_parameters': {
                    'searchType': query_params.get('searchType', [''])[0],
                    'fid': query_params.get('fid', [''])[0],
                    'dateRange': query_params.get('dateRange', [''])[0],
                    'country': query_params.get('country', [''])[0]
                },
                'selectors': self.config.selectors,
                'config': {
                    'max_retries': self.config.max_retries,
                    'timeout_ms': self.config.timeout_ms,
                    'react_load_delay_ms': self.config.react_load_delay_ms,
                    'stabilization_delay_ms': self.config.stabilization_delay_ms
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Metrics info error: {e}")
            return {'error': str(e)}
    
    def get_metrics_url(self) -> str:
        """Get the metrics URL that will be navigated to."""
        return self.config.metrics_url

# Convenience function for metrics extraction
async def extract_noxtools_metrics(page: Page, playwright_manager: PlaywrightManager,
                                 session_manager: SessionManager,
                                 config: Optional[MetricsConfig] = None) -> ExtractedMetrics:
    """Quick metrics extraction function."""
    extractor = MetricsExtractor(config)
    return await extractor.extract_metrics(page, playwright_manager, session_manager)
