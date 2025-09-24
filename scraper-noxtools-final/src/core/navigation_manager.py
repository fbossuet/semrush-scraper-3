#!/usr/bin/env python3
"""
Navigation manager for Noxtools scraper (Alpha)
- Final URL navigation with hardcoded parameters for Alpha version
- Timeout protection and validation
- Integration with session management
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urlencode, parse_qs

from playwright.async_api import Page

from .anti_detection import get_default_stealth_config, StealthConfig
from .playwright_manager import PlaywrightManager
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

@dataclass
class NavigationConfig:
    """Configuration for final navigation to Noxtools analytics."""
    # Hardcoded parameters for Alpha version (will be dynamic in Beta)
    search_type: str = "domain"
    query: str = "cakesbody.com"
    database: str = "us"
    date: str = "202507"
    
    # Navigation settings
    max_retries: int = 3
    timeout_ms: int = 30000
    validation_timeout_ms: int = 15000
    stabilization_delay_ms: int = 3000
    
    # URL components
    base_url: str = "https://semrush1.semrush.pw/analytics/overview/"
    
    def build_final_url(self) -> str:
        """Build the final URL with hardcoded parameters for Alpha."""
        params = {
            'searchType': self.search_type,
            'q': self.query,
            'db': self.database,
            'date': self.date
        }
        return f"{self.base_url}?{urlencode(params)}"

class NavigationManager:
    """Manages navigation to the final Noxtools analytics page."""
    
    def __init__(self, config: Optional[NavigationConfig] = None, stealth_config: Optional[StealthConfig] = None):
        self.config = config or NavigationConfig()
        self.stealth_config = stealth_config or get_default_stealth_config()
        self.final_url = self.config.build_final_url()
        
    async def navigate_to_final_page(self, page: Page, playwright_manager: PlaywrightManager, 
                                   session_manager: SessionManager) -> bool:
        """Navigate to the final Noxtools analytics page with validation.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            session_manager: SessionManager instance
            
        Returns:
            bool: True if navigation successful and page validated
        """
        try:
            logger.info(f"🎯 Starting navigation to final Noxtools page...")
            logger.info(f"📍 Target URL: {self.final_url}")
            
            # Use session manager for cross-domain navigation
            navigation_success = await session_manager.navigate_cross_domain(
                page, playwright_manager, self.final_url
            )
            
            if not navigation_success:
                logger.error("❌ Cross-domain navigation to final page failed")
                return False
                
            # Wait for page to stabilize
            await asyncio.sleep(self.config.stabilization_delay_ms / 1000.0)
            
            # Validate the final page
            page_valid = await self._validate_final_page(page)
            
            if page_valid:
                logger.info("✅ Successfully navigated to final Noxtools analytics page")
                return True
            else:
                logger.error("❌ Final page validation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Final navigation error: {e}")
            return False
    
    async def _validate_final_page(self, page: Page) -> bool:
        """Validate that we're on the correct final analytics page."""
        try:
            logger.info("🔍 Validating final Noxtools analytics page...")
            
            # Check current URL
            current_url = page.url
            logger.debug(f"📍 Current URL: {current_url}")
            
            # Validate URL structure
            url_valid = self._validate_url_structure(current_url)
            if not url_valid:
                logger.warning("⚠️ URL structure validation failed")
                return False
                
            # Check for analytics page indicators
            page_indicators = await self._check_analytics_indicators(page)
            
            if page_indicators['is_analytics_page']:
                logger.info(f"✅ Analytics page validation successful - {page_indicators['reason']}")
                return True
            else:
                logger.warning(f"⚠️ Analytics page validation failed - {page_indicators['reason']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Final page validation error: {e}")
            return False
    
    def _validate_url_structure(self, url: str) -> bool:
        """Validate that the URL has the expected structure."""
        try:
            parsed = urlparse(url)
            
            # Check domain
            if not parsed.netloc or 'semrush1.semrush.pw' not in parsed.netloc:
                logger.warning(f"⚠️ Unexpected domain: {parsed.netloc}")
                return False
                
            # Check path
            if not parsed.path or '/analytics/overview/' not in parsed.path:
                logger.warning(f"⚠️ Unexpected path: {parsed.path}")
                return False
                
            # Check query parameters
            query_params = parse_qs(parsed.query)
            required_params = ['searchType', 'q', 'db', 'date']
            
            for param in required_params:
                if param not in query_params:
                    logger.warning(f"⚠️ Missing required parameter: {param}")
                    return False
                    
            # Validate parameter values
            if query_params.get('searchType', [''])[0] != self.config.search_type:
                logger.warning(f"⚠️ Unexpected searchType: {query_params.get('searchType')}")
                return False
                
            if query_params.get('q', [''])[0] != self.config.query:
                logger.warning(f"⚠️ Unexpected query: {query_params.get('q')}")
                return False
                
            logger.debug("✅ URL structure validation successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ URL structure validation error: {e}")
            return False
    
    async def _check_analytics_indicators(self, page: Page) -> Dict[str, Any]:
        """Check for indicators that we're on the analytics page."""
        try:
            indicators = {
                'is_analytics_page': False,
                'reason': 'Unknown',
                'details': {}
            }
            
            # Check for common analytics page elements
            try:
                # Look for analytics-specific elements
                analytics_elements = await page.query_selector_all(
                    '[class*="analytics"], [id*="analytics"], [data-testid*="analytics"]'
                )
                if analytics_elements:
                    indicators['details']['analytics_elements'] = len(analytics_elements)
                    
                # Look for overview/dashboard elements
                overview_elements = await page.query_selector_all(
                    '[class*="overview"], [id*="overview"], [class*="dashboard"]'
                )
                if overview_elements:
                    indicators['details']['overview_elements'] = len(overview_elements)
                    
                # Look for data tables or charts
                data_elements = await page.query_selector_all(
                    'table, [class*="chart"], [class*="graph"], [class*="metric"]'
                )
                if data_elements:
                    indicators['details']['data_elements'] = len(data_elements)
                    indicators['is_analytics_page'] = True
                    indicators['reason'] = f'Data elements found ({len(data_elements)})'
                    
                # Look for search/query related elements
                search_elements = await page.query_selector_all(
                    'input[type="search"], [class*="search"], [id*="search"]'
                )
                if search_elements:
                    indicators['details']['search_elements'] = len(search_elements)
                    
                # Check page title
                title = await page.title()
                if title:
                    indicators['details']['page_title'] = title
                    if any(keyword in title.lower() for keyword in ['analytics', 'overview', 'semrush']):
                        indicators['is_analytics_page'] = True
                        indicators['reason'] = f'Analytics-related title: {title}'
                        
            except Exception as e:
                logger.debug(f"Element check error: {e}")
                indicators['details']['element_check_error'] = str(e)
            
            # If no specific indicators found, check for general page content
            if not indicators['is_analytics_page']:
                try:
                    # Check if page has substantial content (not an error page)
                    body_text = await page.evaluate('document.body.innerText')
                    if body_text and len(body_text.strip()) > 50:  # Reduced threshold
                        indicators['is_analytics_page'] = True
                        indicators['reason'] = 'Page has substantial content'
                        indicators['details']['content_length'] = len(body_text.strip())
                    else:
                        # Check if we're on the right domain and path (even with minimal content)
                        current_url = page.url
                        if 'semrush1.semrush.pw' in current_url and '/analytics/overview/' in current_url:
                            indicators['is_analytics_page'] = True
                            indicators['reason'] = 'Correct domain and path detected'
                            indicators['details']['url_match'] = True
                        else:
                            indicators['reason'] = 'Page appears to have minimal content and wrong URL'
                        
                except Exception as e:
                    logger.debug(f"Content check error: {e}")
                    indicators['reason'] = f'Content check failed: {e}'
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Analytics indicators check error: {e}")
            return {'is_analytics_page': False, 'reason': f'Check error: {e}', 'details': {}}
    
    async def get_navigation_info(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive navigation information."""
        try:
            current_url = page.url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            # Get page indicators
            page_indicators = await self._check_analytics_indicators(page)
            
            return {
                'final_url': self.final_url,
                'current_url': current_url,
                'url_valid': self._validate_url_structure(current_url),
                'page_valid': page_indicators['is_analytics_page'],
                'validation_reason': page_indicators['reason'],
                'query_parameters': {
                    'searchType': query_params.get('searchType', [''])[0],
                    'q': query_params.get('q', [''])[0],
                    'db': query_params.get('db', [''])[0],
                    'date': query_params.get('date', [''])[0]
                },
                'page_indicators': page_indicators['details'],
                'config': {
                    'search_type': self.config.search_type,
                    'query': self.config.query,
                    'database': self.config.database,
                    'date': self.config.date,
                    'timeout_ms': self.config.timeout_ms,
                    'max_retries': self.config.max_retries
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Navigation info error: {e}")
            return {'error': str(e)}
    
    def get_final_url(self) -> str:
        """Get the final URL that will be navigated to."""
        return self.final_url

# Convenience function for final navigation
async def navigate_to_final_noxtools_page(page: Page, playwright_manager: PlaywrightManager,
                                        session_manager: SessionManager,
                                        config: Optional[NavigationConfig] = None) -> bool:
    """Quick navigation to final Noxtools page function."""
    navigation_manager = NavigationManager(config)
    return await navigation_manager.navigate_to_final_page(page, playwright_manager, session_manager)
