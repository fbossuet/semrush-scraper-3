#!/usr/bin/env python3
"""
Session manager for Noxtools scraper (Alpha)
- Cross-domain session and cookie management
- Navigation between noxtools.com and semrush1.semrush.pw
- Session validation and persistence
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import Page

from .anti_detection import get_default_stealth_config, StealthConfig
from .playwright_manager import PlaywrightManager

logger = logging.getLogger(__name__)

@dataclass
class SessionConfig:
    """Configuration for cross-domain session management."""
    noxtools_domain: str = "noxtools.com"
    semrush_domain: str = "semrush1.semrush.pw"
    session_timeout_ms: int = 30000  # 30 seconds (consistent with other modules)
    cookie_validation_retries: int = 3
    navigation_delay_ms: int = 2000
    session_check_interval_ms: int = 5000

class SessionManager:
    """Manages cross-domain sessions and cookies for Noxtools scraper."""
    
    def __init__(self, config: Optional[SessionConfig] = None, stealth_config: Optional[StealthConfig] = None):
        self.config = config or SessionConfig()
        self.stealth_config = stealth_config or get_default_stealth_config()
        self.session_active = False
        self.current_domain = None
        self.cookies_before_navigation = []
        
    async def navigate_cross_domain(self, page: Page, playwright_manager: PlaywrightManager, 
                                  target_url: str) -> bool:
        """Navigate to a different domain while maintaining session.
        
        Args:
            page: Playwright page instance
            playwright_manager: PlaywrightManager instance
            target_url: Target URL to navigate to
            
        Returns:
            bool: True if navigation successful and session maintained
        """
        try:
            logger.info(f"🌐 Starting cross-domain navigation to: {target_url}")
            
            # Parse target URL to get domain
            target_domain = urlparse(target_url).netloc
            current_domain = urlparse(page.url).netloc if page.url else None
            
            logger.info(f"📍 Current domain: {current_domain}")
            logger.info(f"🎯 Target domain: {target_domain}")
            
            # Check if we're already on the target domain
            if current_domain == target_domain:
                logger.info("✅ Already on target domain, using direct navigation")
                return await playwright_manager.navigate_with_retry(page, target_url)
            
            # Store cookies before navigation
            await self._store_cookies_before_navigation(page)
            
            # Navigate to target domain
            navigation_success = await playwright_manager.navigate_with_retry(page, target_url)
            
            if not navigation_success:
                logger.error("❌ Cross-domain navigation failed")
                return False
                
            # Wait for page to stabilize
            await asyncio.sleep(self.config.navigation_delay_ms / 1000.0)
            
            # Validate session after navigation
            session_valid = await self._validate_session_after_navigation(page, target_domain)
            
            if session_valid:
                self.session_active = True
                self.current_domain = target_domain
                logger.info("✅ Cross-domain navigation successful, session maintained")
                return True
            else:
                logger.warning("⚠️ Cross-domain navigation completed but session may be invalid")
                return False
                
        except Exception as e:
            logger.error(f"❌ Cross-domain navigation error: {e}")
            return False
    
    async def _store_cookies_before_navigation(self, page: Page) -> None:
        """Store current cookies before cross-domain navigation."""
        try:
            context = page.context
            cookies = await context.cookies()
            
            # Filter cookies relevant to our domains
            relevant_cookies = []
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if (self.config.noxtools_domain in domain or 
                    self.config.semrush_domain in domain):
                    relevant_cookies.append(cookie)
            
            self.cookies_before_navigation = relevant_cookies
            logger.info(f"🍪 Stored {len(relevant_cookies)} relevant cookies before navigation")
            
        except Exception as e:
            logger.error(f"❌ Error storing cookies: {e}")
    
    async def _validate_session_after_navigation(self, page: Page, target_domain: str) -> bool:
        """Validate session after cross-domain navigation."""
        try:
            logger.info(f"🔍 Validating session on {target_domain}")
            
            # Check if we can access the page (not redirected to login)
            current_url = page.url
            logger.info(f"📍 Current URL after navigation: {current_url}")
            
            # Check for authentication indicators
            auth_indicators = await self._check_authentication_indicators(page, target_domain)
            
            if auth_indicators['is_authenticated']:
                logger.info("✅ Session validation successful - authenticated")
                return True
            else:
                logger.warning(f"⚠️ Session validation failed - {auth_indicators['reason']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Session validation error: {e}")
            return False
    
    async def _check_authentication_indicators(self, page: Page, domain: str) -> Dict[str, Any]:
        """Check various indicators of successful authentication."""
        try:
            indicators = {
                'is_authenticated': False,
                'reason': 'Unknown',
                'details': {}
            }
            
            current_url = page.url.lower()
            
            # Check URL-based indicators
            if domain == self.config.noxtools_domain:
                # Noxtools authentication indicators
                if any(indicator in current_url for indicator in ['/secure/member', '/member', '/dashboard']):
                    indicators['is_authenticated'] = True
                    indicators['reason'] = 'Noxtools member page detected'
                elif '/login' in current_url or '/secure/login' in current_url:
                    indicators['is_authenticated'] = False
                    indicators['reason'] = 'Redirected to login page'
                    
            elif domain == self.config.semrush_domain:
                # Semrush authentication indicators
                if any(indicator in current_url for indicator in ['/analytics', '/overview', '/dashboard']):
                    indicators['is_authenticated'] = True
                    indicators['reason'] = 'Semrush analytics page detected'
                elif '/login' in current_url:
                    indicators['is_authenticated'] = False
                    indicators['reason'] = 'Redirected to Semrush login'
            
            # Check for specific page elements that indicate authentication
            try:
                # Look for common authenticated page elements
                auth_elements = await page.query_selector_all('[data-testid*="user"], [class*="user"], [id*="user"]')
                if auth_elements:
                    indicators['details']['user_elements'] = len(auth_elements)
                    
                # Look for logout buttons (indicates authentication)
                logout_elements = await page.query_selector_all('a[href*="logout"], button[class*="logout"]')
                if logout_elements:
                    indicators['is_authenticated'] = True
                    indicators['reason'] = f'Logout elements found ({len(logout_elements)})'
                    
            except Exception as e:
                logger.info(f"Element check error: {e}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Authentication indicator check error: {e}")
            return {'is_authenticated': False, 'reason': f'Check error: {e}', 'details': {}}
    
    async def validate_current_session(self, page: Page) -> bool:
        """Validate the current session on any domain."""
        try:
            current_domain = urlparse(page.url).netloc if page.url else None
            if not current_domain:
                logger.warning("⚠️ No current URL to validate session")
                return False
                
            auth_indicators = await self._check_authentication_indicators(page, current_domain)
            return auth_indicators['is_authenticated']
            
        except Exception as e:
            logger.error(f"❌ Current session validation error: {e}")
            return False
    
    async def get_session_info(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive session information."""
        try:
            current_url = page.url
            current_domain = urlparse(current_url).netloc if current_url else None
            
            # Get current cookies
            context = page.context
            cookies = await context.cookies()
            
            # Filter relevant cookies
            relevant_cookies = []
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if (self.config.noxtools_domain in domain or 
                    self.config.semrush_domain in domain):
                    relevant_cookies.append({
                        'name': cookie.get('name'),
                        'domain': cookie.get('domain'),
                        'path': cookie.get('path'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    })
            
            # Validate current session
            session_valid = await self.validate_current_session(page)
            
            return {
                'session_active': self.session_active,
                'current_domain': current_domain,
                'current_url': current_url,
                'session_valid': session_valid,
                'cookies_count': len(relevant_cookies),
                'cookies': relevant_cookies,
                'config': {
                    'noxtools_domain': self.config.noxtools_domain,
                    'semrush_domain': self.config.semrush_domain,
                    'session_timeout_ms': self.config.session_timeout_ms
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Session info error: {e}")
            return {'error': str(e)}
    
    def reset_session(self) -> None:
        """Reset session state."""
        self.session_active = False
        self.current_domain = None
        self.cookies_before_navigation = []
        logger.info("🔄 Session state reset")

# Convenience function for cross-domain navigation
async def navigate_cross_domain(page: Page, playwright_manager: PlaywrightManager, 
                               target_url: str, config: Optional[SessionConfig] = None) -> bool:
    """Quick cross-domain navigation function."""
    session_manager = SessionManager(config)
    return await session_manager.navigate_cross_domain(page, playwright_manager, target_url)
