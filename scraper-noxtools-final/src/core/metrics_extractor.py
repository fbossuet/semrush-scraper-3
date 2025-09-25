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
from core.server_manager import get_server_manager
from .session_manager import SessionManager
from utils.url_params import build_date_range

logger = logging.getLogger(__name__)

@dataclass
class MetricsConfig:
    """Configuration for metrics extraction from Noxtools."""
    # URL de base des métriques (sans fid - sera construit dynamiquement)
    base_metrics_url: str = "https://semrush1.semrush.pw/analytics/traffic/market-overview"
    # URL dashboard (utilisée comme Referer pour réactiver la session)
    dashboard_url: str = "https://noxtools.com/secure/member"
    # URL passerelle Noxtools → Semrush (gérée dynamiquement par ServerManager)
    bridge_url: str = ""  # Sera définie dynamiquement selon le serveur actuel
    # URL overview pour CPC (sera construite dynamiquement avec le domaine)
    overview_base_url: str = "https://semrush3.semrush.pw/analytics/overview/"
    
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
                # Nouveau sélecteur VISITS fourni (SAP React gridcell)
                'visits': '[data-ui-name="Flex"][role="gridcell"][name="entrances"][tabindex="-1"][aria-colindex="3"]',
                'organic_search_traffic': '[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchOrganic"][tabindex="-1"][aria-colindex="9"]',
                'paid_search_traffic': '[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchPaid"][tabindex="-1"][aria-colindex="11"]',
                'purchase_conversion': '[data-ui-name="Flex"][role="gridcell"][name="purchasesPerVisit"][tabindex="-1"][aria-colindex="21"]',
                'avg_visit_duration': '[data-ui-name="Flex"][role="gridcell"][name="avgVisitDuration"][tabindex="-1"][aria-colindex="27"]',
                'bounce_rate': '[data-ui-name="Flex"][role="gridcell"][name="bouncesPerVisit"][tabindex="-1"][aria-colindex="29"]',
                # Sélecteur branded traffic (analytics domain overview page)
                'branded_traffic': '[data-at="br-vs-nonbr-legend"] > [data-ui-name="Link.Text"]'
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
    branded_traffic: Optional[str] = None
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
            'branded_traffic': self.branded_traffic,
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
    
    def _extract_domain_from_url(self, shop_url: str) -> str:
        """Extrait le domaine d'une URL de shop."""
        if not shop_url:
            logger.warning("⚠️ shop_url is None or empty")
            return ""
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(shop_url)
            domain = parsed.netloc
            # Enlever www. si présent
            if domain and domain.startswith('www.'):
                domain = domain[4:]
            return domain or ""
        except Exception as e:
            logger.warning(f"⚠️ Error extracting domain from {shop_url}: {e}")
            return ""  # Fallback: retourner une chaîne vide
    
    def _build_overview_url(self, domain: str) -> str:
        """Construit l'URL overview avec le domaine et la date calculée."""
        date_range = build_date_range()
        # Format de date pour l'URL overview (YYYYMM)
        date_param = date_range.replace('-', '')[:6]  # 2025-07-15 -> 202507
        
        params = {
            'searchType': 'domain',
            'q': domain,
            'db': 'us',
            'date': date_param
        }
        
        query_string = urlencode(params)
        # Normaliser l'URL avec le serveur actuel
        base_url = self.server_manager.normalize_url_to_current_server(self.config.overview_base_url)
        return f"{base_url}?{query_string}"
        
    async def extract_metrics(self, page: Page, playwright_manager: PlaywrightManager, 
                            session_manager: SessionManager, shop_url: str = None) -> ExtractedMetrics:
        """Extract metrics from the Noxtools analytics page.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            session_manager: SessionManager instance
            shop_url: Shop URL to extract domain for CPC extraction
            
        Returns:
            ExtractedMetrics: Extracted metrics data
        """
        metrics = ExtractedMetrics()
        
        try:
            logger.info("📊 Starting metrics extraction from Noxtools...")
            logger.info(f"📍 Base metrics URL: {self.config.base_metrics_url}")
            
            # Extract domain from shop_url for navigation
            domain = self._extract_domain_from_shop_url(shop_url) if shop_url else "cakesbody.com"
            logger.info(f"🌐 Using domain for navigation: {domain}")
            
            # WORKFLOW RESTAURÉ: Accès direct d'abord, bridge en fallback
            logger.info("🔄 Restoring working workflow: Direct access first, bridge as fallback")
            
            # Step 1: Navigate to Dashboard (https://noxtools.com/secure/member)
            logger.info("📊 Step 1: Navigating to Dashboard...")
            try:
                await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
                await asyncio.sleep(1.0)
                logger.info("✅ Dashboard navigation successful")
            except Exception as e:
                logger.warning(f"⚠️ Dashboard navigation failed: {e}")
            
            # Step 2: Test direct access to Semrush (comme dans l'ancien code qui marchait)
            logger.info("🧪 Step 2: Testing direct access to Semrush...")
            direct_access_success = False
            try:
                # Test direct access to market overview
                direct_url = f"https://semrush1.semrush.pw/analytics/traffic/market-overview"
                await page.goto(direct_url, referer=self.config.dashboard_url, timeout=5000)
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
                
                # Check if direct access worked
                current_url = page.url
                page_title = await page.evaluate('document.title')
                
                if "403" not in page_title and "forbidden" not in page_title.lower():
                    logger.info("✅ Direct server access successful, no bridge needed")
                    direct_access_success = True
                else:
                    logger.info("⚠️ Direct access failed, will use bridge")
                    
            except Exception as e:
                logger.info(f"⚠️ Direct access failed: {e}, will use bridge")
            
            # Step 3: Use bridge only if direct access failed
            if not direct_access_success:
                logger.info("🌉 Step 3: Using bridge as fallback...")
                bridge_url = self.server_manager.get_current_bridge_url()
                logger.info(f"🌉 Using bridge URL: {bridge_url}")
                try:
                    await page.goto(bridge_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    await asyncio.sleep(1.0)
                    logger.info("✅ Bridge URL visited successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Bridge URL visit failed: {e}")
            
            # Step 4: Navigate to Overview (https://semrush1.semrush.pw/analytics/overview/...)
            overview_url = self._build_overview_url(domain)
            logger.info(f"🔗 Step 4: Navigating to Overview: {overview_url}")
            try:
                await page.goto(overview_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                await page.wait_for_load_state('networkidle', timeout=10000)
                await asyncio.sleep(2.0)  # Extra time for SAP React
                logger.info("✅ Overview navigation successful")
                navigation_success = True
            except Exception as e:
                logger.warning(f"⚠️ Overview navigation failed: {e}")
                navigation_success = False
            
            if not navigation_success:
                metrics.error_message = "Failed to navigate to overview page"
                logger.error("❌ Failed to navigate to overview page")
                return metrics
                
            # Check for session expired before waiting
            page_content = await page.content()
            if "session expired" in page_content.lower():
                logger.warning("⚠️ Session expired detected on metrics page")
                metrics.error_message = "Session expired detected on metrics page"
                logger.error("❌ Failed to extract metrics from page")
                return metrics
            
            # Wait for SAP React to load (reduced delay)
            await asyncio.sleep(3.0)  # Reduced from 5s to 3s
            logger.info("⏳ Waiting for SAP React to load...")
            
            # DEBUG: Capture URL and page content
            current_url = page.url
            logger.info(f"🔍 DEBUG - Current URL: {current_url}")
            
            # Get page content for debugging
            try:
                page_content = await page.evaluate('document.body.innerText')
                logger.info(f"🔍 DEBUG - Page content (first 500 chars): {page_content[:500]}")
                
                # Check for specific elements
                title = await page.evaluate('document.title')
                logger.info(f"🔍 DEBUG - Page title: {title}")
                
                # Check for error messages
                error_elements = await page.query_selector_all('[class*="error"], [class*="Error"], [data-testid*="error"]')
                if error_elements:
                    logger.warning(f"🔍 DEBUG - Found {len(error_elements)} error elements")
                    for i, elem in enumerate(error_elements[:3]):  # First 3 errors
                        try:
                            error_text = await elem.inner_text()
                            logger.warning(f"🔍 DEBUG - Error {i+1}: {error_text[:200]}")
                        except:
                            pass
                
            except Exception as e:
                logger.warning(f"🔍 DEBUG - Error getting page content: {e}")
            
            # Check again for session expired after waiting
            page_content = await page.content()
            if "session expired" in page_content.lower():
                logger.warning("⚠️ Session expired detected after waiting")
                metrics.error_message = "Session expired detected after waiting"
                logger.error("❌ Failed to extract metrics from page")
                return metrics
            
            # Wait for page to stabilize (reduced delay)
            await asyncio.sleep(2.0)  # Reduced from 3s to 2s
            
            # Try network capture assisted extraction first
            network_data = await self._capture_network_metrics(page)

            if network_data:
                self._populate_metrics_from_network(metrics, network_data)
                metrics.success = True
                logger.info("✅ Metrics extracted from network responses")
                self._log_extracted_metrics(metrics)
                return metrics

            # Fallback: Extract from DOM
            extraction_success = await self._extract_metrics_from_page(page, metrics)
            
            if extraction_success:
                metrics.success = True
                logger.info("✅ Metrics extraction successful")
                
                # Extract CPC using the domain from shop_url (if provided)
                cpc_data = None
                if shop_url:
                    domain = self._extract_domain_from_url(shop_url)
                    if domain:  # Vérifier que le domaine n'est pas vide
                        cpc_data = await self.extract_cpc_best_ratio(page, playwright_manager, session_manager, domain)
                    else:
                        logger.warning("⚠️ Cannot extract CPC: domain is empty from shop_url")
                
                if cpc_data and cpc_data.get('cpc'):
                    metrics.cpc = str(cpc_data['cpc'])
                    logger.info(f"✅ CPC extracted: {metrics.cpc}")
                else:
                    logger.warning("⚠️ CPC extraction failed or no data found")
                
                self._log_extracted_metrics(metrics)
            else:
                metrics.error_message = "Failed to extract metrics from page"
                logger.error("❌ Failed to extract metrics from page")
                
        except Exception as e:
            metrics.error_message = str(e)
            logger.error(f"❌ Metrics extraction error: {e}")
            
        return metrics

    async def extract_cpc_best_ratio(self, page: Page, playwright_manager: PlaywrightManager,
                                     session_manager: SessionManager, domain: str) -> Optional[Dict[str, Any]]:
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

            # Step 2: Hit the Noxtools → Semrush bridge (server3 only)
            try:
                logger.info(f"🌉 Visiting bridge URL for CPC: {self.config.bridge_url}")
                await page.goto(self.config.bridge_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                await asyncio.sleep(1.0)
                logger.info("✅ Bridge URL visited successfully for CPC")
            except Exception as e:
                logger.warning(f"⚠️ Bridge URL visit failed for CPC: {e}")

            # Step 3: Build and navigate to overview URL with domain
            overview_url = self._build_overview_url(domain)
            logger.info(f"🔗 Navigating to overview URL: {overview_url}")
            
            # Use the same approach as _navigate_to_metrics_page for consistency
            navigation_success = False
            try:
                # First try session manager for cross-domain navigation
                navigation_success = await session_manager.navigate_cross_domain(
                    page, playwright_manager, overview_url
                )
            except Exception as e:
                logger.warning(f"⚠️ Cross-domain navigation error for CPC: {e}")

            # If session manager failed, try direct navigation with referer
            if not navigation_success:
                try:
                    await page.goto(overview_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
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
                    logger.info("✅ Grid scrolled using container method")
                except Exception as e:
                    logger.warning(f"⚠️ Container scroll failed, using window scroll: {e}")
                    for _ in range(6):
                        await page.evaluate('window.scrollBy(0, Math.max(300, window.innerHeight/2))')
                        await asyncio.sleep(0.25)
                    logger.info("✅ Grid scrolled using window method")

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
                    logger.info(f"CPC evaluation attempt {attempt + 1}: {best}")
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
        """Navigate to the metrics page with automatic server fallback."""
        max_server_attempts = len(self.server_manager.get_available_servers())
        
        for attempt in range(max_server_attempts):
            current_server = self.server_manager.get_current_server_name()
            logger.info(f"🔄 Tentative {attempt + 1}/{max_server_attempts} avec serveur: {current_server}")
            
            try:
                logger.info("🌐 Navigating to metrics page...")
                
                # Step 1: Ensure dashboard is visited to refresh session (referer source)
                try:
                    await playwright_manager.navigate_with_retry(page, self.config.dashboard_url)
                    await asyncio.sleep(1.0)
                except Exception as e:
                    logger.warning(f"⚠️ Unable to visit dashboard before metrics: {e}")

                # Step 2: Test server availability and use bridge only if needed
                try:
                    # Get current server bridge URL from ServerManager
                    current_bridge_url = self.server_manager.get_current_bridge_url()
                    logger.info(f"🌉 Current server bridge: {current_bridge_url}")
                    
                    # Test if we can access the target server directly first
                    target_url = self.config.base_metrics_url
                    logger.info(f"🧪 Testing direct access to: {target_url}")
                    
                    # Try direct navigation first (without bridge)
                    try:
                        await page.goto(target_url, referer=self.config.dashboard_url, timeout=5000)
                        await page.wait_for_load_state('domcontentloaded', timeout=5000)
                        
                        # Check if we got a valid response (not session expired immediately)
                        page_content = await page.content()
                        if "session expired" not in page_content.lower() and len(page_content) > 1000:
                            logger.info("✅ Direct server access successful, no bridge needed")
                            return True
                        else:
                            logger.info("⚠️ Direct access failed, will use bridge")
                    except Exception as e:
                        logger.info(f"⚠️ Direct access failed: {e}, will use bridge")
                    
                    # If direct access failed, use bridge
                    logger.info(f"🌉 Using bridge URL: {current_bridge_url}")
                    await page.goto(current_bridge_url, referer=self.config.dashboard_url, timeout=self.config.timeout_ms)
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    await asyncio.sleep(1.0)
                    logger.info("✅ Bridge URL visited successfully")
                    
                    # If we reach here, navigation was successful
                    return True
                    
                except Exception as e:
                    logger.warning(f"⚠️ Bridge URL visit failed on {current_server}: {e}")
                    # Mark server as failed and switch to next server immediately
                    self.server_manager.mark_server_failed(f"Bridge access failed: {e}", switch_immediately=True)
                    
                    # Check if we can try next server
                    if attempt < max_server_attempts - 1:
                        logger.info(f"🔄 Tentative avec le serveur suivant...")
                        continue
                    else:
                        logger.error("❌ Tous les serveurs ont échoué")
                        return False
                        
            except Exception as e:
                logger.error(f"❌ Erreur lors de la tentative {attempt + 1}: {e}")
                # Mark server as failed and switch to next server immediately
                self.server_manager.mark_server_failed(f"Navigation error: {e}", switch_immediately=True)
                
                # Check if we can try next server
                if attempt < max_server_attempts - 1:
                    logger.info(f"🔄 Tentative avec le serveur suivant...")
                    continue
                else:
                    logger.error("❌ Tous les serveurs ont échoué")
                    return False

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
            logger.warning(f"Dashboard link navigation attempt failed: {e}")

        # Step 4: Navigate to target URL with server fallback
        navigation_success = False
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Get current server URL (may have changed due to fallback)
                current_target_url = self.server_manager.normalize_url_to_current_server(self.config.base_metrics_url)
                logger.info(f"🎯 Attempt {attempt + 1}: Navigating to {current_target_url}")
                
                # Use session manager for cross-domain navigation
                navigation_success = await session_manager.navigate_cross_domain(
                    page, playwright_manager, current_target_url
                )
                
                if navigation_success:
                    logger.info(f"✅ Navigation successful on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"⚠️ Navigation failed on attempt {attempt + 1}")
                    # Mark current server as failed and try next
                    self.server_manager.mark_server_failed("Navigation failed")
                        
            except Exception as e:
                logger.warning(f"⚠️ Navigation error on attempt {attempt + 1}: {e}")
                self.server_manager.mark_server_failed(f"Navigation error: {e}")
        
        if not navigation_success:
            logger.error("❌ All navigation attempts failed")
            return False
        
        # Check for session expired after navigation
        page_content = await page.content()
        if "session expired" in page_content.lower():
            logger.warning("⚠️ Session expired detected after navigation")
            # Try session refresh
            if await session_manager.refresh_session_if_expired(page, playwright_manager, self.config.base_metrics_url, self.server_manager):
                logger.info("✅ Session refreshed successfully")
            else:
                logger.error("❌ Session refresh failed")
                return False
        
        logger.info("✅ Successfully navigated to metrics page")
        return True
    
    async def _extract_metrics_from_page(self, page: Page, metrics: ExtractedMetrics) -> bool:
        """Extract metrics from the current page."""
        try:
            logger.info("🔍 Extracting metrics from page...")
            
            # DEBUG: Detailed page analysis
            current_url = page.url
            logger.info(f"🔍 DEBUG - Extracting from URL: {current_url}")
            
            # Get page title and content for debugging
            try:
                title = await page.evaluate('document.title')
                logger.info(f"🔍 DEBUG - Page title: {title}")
                
                # Check for specific content indicators
                page_text = await page.evaluate('document.body.innerText')
                logger.info(f"🔍 DEBUG - Page contains 'market'? {'market' in page_text.lower()}")
                logger.info(f"🔍 DEBUG - Page contains 'overview'? {'overview' in page_text.lower()}")
                logger.info(f"🔍 DEBUG - Page contains 'traffic'? {'traffic' in page_text.lower()}")
                
                # Check for specific elements that should be present
                grid_elements = await page.query_selector_all('[role="gridcell"]')
                logger.info(f"🔍 DEBUG - Found {len(grid_elements)} gridcell elements")
                
                sap_elements = await page.query_selector_all('[data-ui-name]')
                logger.info(f"🔍 DEBUG - Found {len(sap_elements)} SAP React elements")
                
            except Exception as e:
                logger.warning(f"🔍 DEBUG - Error in page analysis: {e}")
            
            # Check if we're on the right page
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
                logger.warning(f"Content check error: {e}")
                
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

            # 1) Direct selector
            try:
                element = await page.wait_for_selector(selector, timeout=5000, state='attached')
                if element:
                    text = await read_element_text(element)
                    if text:
                        logger.info(f"✅ Extracted {metric_name} (direct): {text}")
                        return text
            except Exception as e:
                logger.warning(f"Direct selector failed for {metric_name}: {e}")

            # 1b) Relaxed variants
            for sel in relaxed_variants:
                try:
                    element = await page.wait_for_selector(sel, timeout=4000, state='attached')
                    if element:
                        text = await read_element_text(element)
                        if text:
                            logger.info(f"✅ Extracted {metric_name} (relaxed): {text}")
                            return text
                except Exception as e:
                    logger.warning(f"Relaxed selector failed for {metric_name}: {e}")

            # 2) Attribute selector [name="..."]
            try:
                if 'name=' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    attr_selector = f'[name="{attr_name}"]'
                    element = await page.wait_for_selector(attr_selector, timeout=3000, state='attached')
                    if element:
                        text = await read_element_text(element)
                        if text:
                            logger.info(f"✅ Extracted {metric_name} (attr): {text}")
                            return text
            except Exception as e:
                logger.warning(f"Attribute selector failed for {metric_name}: {e}")

            # 3) Input value
            try:
                if 'name=' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    input_selector = f'input[name="{attr_name}"]'
                    element = await page.wait_for_selector(input_selector, timeout=3000, state='attached')
                    if element:
                        input_value = await element.input_value()
                        if input_value and input_value.strip():
                            logger.info(f"✅ Extracted {metric_name} (input): {input_value.strip()}")
                            return input_value.strip()
            except Exception as e:
                logger.warning(f"Input selector failed for {metric_name}: {e}")

            # 4) Span inside named container
            try:
                if 'name=' in selector and '> span' in selector:
                    attr_name = selector.split('name="')[1].split('"')[0]
                    span_selector = f'[name="{attr_name}"] span'
                    element = await page.wait_for_selector(span_selector, timeout=3000, state='attached')
                    if element:
                        text_content = await element.text_content()
                        if text_content and text_content.strip():
                            logger.info(f"✅ Extracted {metric_name} (span): {text_content.strip()}")
                            return text_content.strip()
            except Exception as e:
                logger.warning(f"Span selector failed for {metric_name}: {e}")

            logger.warning(f"⚠️ {metric_name} not found with any approach (selector: {selector})")
            return None

        except Exception as e:
            logger.error(f"⚠️ Error extracting {metric_name}: {e}")
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
            logger.error(f"  Error: {metrics.error_message}")
            
    async def get_metrics_info(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive metrics extraction information."""
        try:
            current_url = page.url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            return {
                'metrics_url': self.config.base_metrics_url,
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
        return self.config.base_metrics_url

# Convenience function for metrics extraction
async def extract_noxtools_metrics(page: Page, playwright_manager: PlaywrightManager,
                                 session_manager: SessionManager,
                                 config: Optional[MetricsConfig] = None) -> ExtractedMetrics:
    """Quick metrics extraction function."""
    extractor = MetricsExtractor(config)
    return await extractor.extract_metrics(page, playwright_manager, session_manager)


