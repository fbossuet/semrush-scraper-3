#!/usr/bin/env python3
"""
Playwright manager for Noxtools scraper (Alpha)
- Async initialization with stealth headless mode
- Persistent context for session management
- Anti-detection headers integration
- Cross-domain cookie handling (noxtools.com → semrush1.semrush.pw)
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright, BrowserContext, Page

from .anti_detection import build_stealth_headers, get_default_stealth_config, StealthConfig

logger = logging.getLogger(__name__)

class PlaywrightManager:
    """Manages Playwright browser instance with stealth configuration."""
    
    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or get_default_stealth_config()
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.session_dir = Path("session-profiles")
        self.session_dir.mkdir(exist_ok=True)
        
    async def initialize(self) -> None:
        """Initialize Playwright with stealth configuration."""
        try:
            logger.info("🚀 Initializing Playwright with stealth configuration...")
            
            # Setup display for headless mode on Linux
            if os.name == 'posix' and not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':99'
                logger.info("📺 Set DISPLAY=:99 for headless mode")
            
            self.playwright = await async_playwright().start()
            
            # Create persistent context for session management (cookies persist between domains)
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir / "noxtools-session"),
                headless=True,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                ]
            )
            
            logger.info("✅ Playwright initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright: {e}")
            await self.cleanup()
            raise
    
    async def new_page(self, context_type: str = 'navigate') -> Page:
        """Create a new page with appropriate headers."""
        if not self.context:
            raise RuntimeError("Playwright not initialized. Call initialize() first.")
        
        page = await self.context.new_page()
        
        # Set headers based on context
        headers = build_stealth_headers(context_type)
        await page.set_extra_http_headers(headers)
        
        # Set viewport and other stealth settings
        await page.set_viewport_size({'width': 1920, 'height': 1080})
        
        logger.info(f"📄 Created new page with {context_type} headers")
        return page
    
    async def navigate_with_retry(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic, session validation and logout detection."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Vérifier la validité des cookies avant navigation
                if not await self._validate_session_cookies(page):
                    logger.warning("🚨 Cookies de session invalides détectés")
                    if attempt < max_retries - 1:
                        logger.info("🔄 Tentative de re-authentification...")
                        # Ici on pourrait déclencher une re-authentification
                        # mais pour l'instant on continue avec la navigation
                
                # Set timeout based on config (30 seconds default)
                timeout = 30000  # 30 seconds in milliseconds
                await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
                
                # Wait for page to be ready
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Vérifier si on a été redirigé vers logout
                if await self._is_redirected_to_logout(page):
                    logger.warning("🚨 Redirection vers logout détectée")
                    if attempt < max_retries - 1:
                        logger.info("🔄 Retry avec nouvelle session...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        logger.error("❌ Redirection vers logout persistante")
                        return False
                
                logger.info(f"✅ Successfully navigated to {url}")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to navigate to {url} after {max_retries} attempts")
                    return False
        
        return False
    
    async def _validate_session_cookies(self, page: Page) -> bool:
        """Vérifier la validité des cookies de session.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True si cookies valides, False sinon
        """
        try:
            cookies = await page.context.cookies()
            
            # Vérifier la présence des cookies essentiels
            essential_cookies = ['PHPSESSID', 'amember_nr', 'proxy_token']
            found_cookies = {cookie['name'] for cookie in cookies}
            
            missing_cookies = set(essential_cookies) - found_cookies
            if missing_cookies:
                logger.warning(f"🚨 Cookies manquants: {missing_cookies}")
                return False
            
            # Vérifier l'expiration des cookies
            current_time = asyncio.get_event_loop().time()
            for cookie in cookies:
                if cookie.get('expires', -1) > 0:
                    if cookie['expires'] < current_time:
                        logger.warning(f"🚨 Cookie expiré: {cookie['name']}")
                        return False
            
            logger.debug("✅ Cookies de session valides")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la validation des cookies: {e}")
            return False
    
    async def _is_redirected_to_logout(self, page: Page) -> bool:
        """Détecter si la page a été redirigée vers logout.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True si redirection vers logout, False sinon
        """
        try:
            current_url = page.url.lower()
            
            # Patterns de redirection vers logout
            logout_patterns = [
                '/sso/logout',
                '/login/disable_hard',
                'backurl=/login/disable_hard',
                'session expired',
                'access again from dashboard'
            ]
            
            for pattern in logout_patterns:
                if pattern in current_url:
                    logger.warning(f"🚨 Redirection vers logout détectée: {pattern}")
                    return True
            
            # Vérifier le contenu de la page
            page_content = await page.evaluate('document.body.innerText')
            if 'this url is protected by proxy' in page_content.lower():
                logger.warning("🚨 Page protégée par proxy détectée")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la détection de redirection: {e}")
            return True  # En cas d'erreur, considérer comme redirection
    
    async def cleanup(self) -> None:
        """Clean up Playwright resources."""
        try:
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("🧹 Playwright cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

# Convenience function for quick initialization
async def create_playwright_manager(config: Optional[StealthConfig] = None) -> PlaywrightManager:
    """Create and initialize a PlaywrightManager."""
    manager = PlaywrightManager(config)
    await manager.initialize()
    return manager
