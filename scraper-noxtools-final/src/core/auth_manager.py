#!/usr/bin/env python3
"""
Authentication manager for Noxtools scraper (Alpha)
- Form-based authentication with provided selectors
- Session validation and error handling
- Cross-domain session maintenance
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .anti_detection import compute_delay_seconds, get_default_stealth_config, StealthConfig
from .playwright_manager import PlaywrightManager

logger = logging.getLogger(__name__)

@dataclass
class AuthConfig:
    """Configuration for Noxtools authentication."""
    login_url: str = "https://noxtools.com/secure/login"
    success_redirect_url: str = "https://noxtools.com/secure/member"
    username_selector: str = "#amember-login"
    password_selector: str = "#amember-pass"
    submit_selector: str = "[type=\"submit\"]"
    max_retries: int = 3
    timeout_ms: int = 30000
    delay_after_submit_ms: int = 2000

class AuthManager:
    """Manages Noxtools authentication with form-based login."""
    
    def __init__(self, config: Optional[AuthConfig] = None, stealth_config: Optional[StealthConfig] = None):
        self.config = config or AuthConfig()
        self.stealth_config = stealth_config or get_default_stealth_config()
        self.is_authenticated = False
        
    async def authenticate(self, page: Page, username: str, password: str, playwright_manager: PlaywrightManager) -> bool:
        """Authenticate with Noxtools using form-based login.
        
        Args:
            page: Playwright page instance
            username: Noxtools username
            password: Noxtools password
            playwright_manager: PlaywrightManager instance for navigation
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            logger.info("🔐 Starting Noxtools authentication...")
            
            # Navigate to login page
            if not await self._navigate_to_login(page, playwright_manager):
                return False
                
            # Fill login form
            if not await self._fill_login_form(page, username, password):
                return False
                
            # Submit form and wait for redirect
            if not await self._submit_and_validate(page):
                return False
                
            self.is_authenticated = True
            logger.info("✅ Noxtools authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False
    
    async def _navigate_to_login(self, page: Page, playwright_manager: PlaywrightManager) -> bool:
        """Navigate to the Noxtools login page using PlaywrightManager."""
        try:
            logger.info(f"🌐 Navigating to login page: {self.config.login_url}")
            
            # Use PlaywrightManager's navigate_with_retry for consistency
            navigation_success = await playwright_manager.navigate_with_retry(
                page, 
                self.config.login_url, 
                max_retries=self.config.max_retries
            )
            
            if not navigation_success:
                logger.error("❌ Failed to navigate to login page")
                return False
                
            # Verify we're on the login page
            if await self._verify_login_page(page):
                logger.info("✅ Successfully navigated to login page")
                return True
            else:
                logger.error("❌ Login page verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Navigation error: {e}")
            return False
    
    async def _verify_login_page(self, page: Page) -> bool:
        """Verify that we're on the correct login page."""
        try:
            # Check if login form elements are present
            username_field = await page.query_selector(self.config.username_selector)
            password_field = await page.query_selector(self.config.password_selector)
            submit_button = await page.query_selector(self.config.submit_selector)
            
            if username_field and password_field and submit_button:
                logger.debug("✅ Login form elements found")
                return True
            else:
                logger.warning("⚠️ Login form elements not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login page verification error: {e}")
            return False
    
    async def _fill_login_form(self, page: Page, username: str, password: str) -> bool:
        """Fill the login form with credentials."""
        try:
            logger.info("📝 Filling login form...")
            
            # Clear and fill username field
            username_field = await page.query_selector(self.config.username_selector)
            if not username_field:
                logger.error(f"❌ Username field not found: {self.config.username_selector}")
                return False
                
            await username_field.fill("")  # Clear field
            await username_field.fill(username)
            logger.debug("✅ Username field filled")
            
            # Clear and fill password field
            password_field = await page.query_selector(self.config.password_selector)
            if not password_field:
                logger.error(f"❌ Password field not found: {self.config.password_selector}")
                return False
                
            await password_field.fill("")  # Clear field
            await password_field.fill(password)
            logger.debug("✅ Password field filled")
            
            # Add human-like delay before submit
            delay = compute_delay_seconds(
                self.stealth_config.base_delay_ms,
                self.stealth_config.jitter_ms
            )
            await asyncio.sleep(delay)
            
            logger.info("✅ Login form filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Form filling error: {e}")
            return False
    
    async def _submit_and_validate(self, page: Page) -> bool:
        """Submit the login form and validate success."""
        try:
            logger.info("🚀 Submitting login form...")
            
            # Find and click submit button
            submit_button = await page.query_selector(self.config.submit_selector)
            if not submit_button:
                logger.error(f"❌ Submit button not found: {self.config.submit_selector}")
                return False
                
            # Click submit button
            await submit_button.click()
            logger.debug("✅ Submit button clicked")
            
            # Wait for navigation/redirect
            await asyncio.sleep(self.config.delay_after_submit_ms / 1000.0)
            
            # Wait for page to load
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning("⚠️ Page load timeout, continuing...")
            
            # Verify successful authentication
            current_url = page.url
            logger.info(f"📍 Current URL after submit: {current_url}")
            
            if self._is_authentication_successful(current_url):
                logger.info("✅ Authentication successful - redirected to member page")
                return True
            else:
                logger.error(f"❌ Authentication failed - unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Form submission error: {e}")
            return False
    
    def _is_authentication_successful(self, current_url: str) -> bool:
        """Check if authentication was successful based on URL."""
        # Check if we're redirected to the success page
        if self.config.success_redirect_url in current_url:
            return True
            
        # Additional checks for successful authentication
        success_indicators = [
            '/secure/member',
            '/member',
            'dashboard',
            'profile'
        ]
        
        for indicator in success_indicators:
            if indicator in current_url.lower():
                return True
                
        return False
    
    async def validate_session(self, page: Page) -> bool:
        """Validate that the current session is still authenticated."""
        try:
            current_url = page.url
            logger.debug(f"🔍 Validating session at: {current_url}")
            
            # Check if we're on an authenticated page
            if self._is_authentication_successful(current_url):
                logger.debug("✅ Session is valid")
                return True
            else:
                logger.warning("⚠️ Session appears to be invalid")
                return False
                
        except Exception as e:
            logger.error(f"❌ Session validation error: {e}")
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return {
            'is_authenticated': self.is_authenticated,
            'login_url': self.config.login_url,
            'success_redirect_url': self.config.success_redirect_url,
            'selectors': {
                'username': self.config.username_selector,
                'password': self.config.password_selector,
                'submit': self.config.submit_selector
            }
        }

# Convenience function for quick authentication
async def authenticate_noxtools(page: Page, username: str, password: str, playwright_manager: PlaywrightManager,
                              config: Optional[AuthConfig] = None) -> bool:
    """Quick authentication function for Noxtools."""
    auth_manager = AuthManager(config)
    return await auth_manager.authenticate(page, username, password, playwright_manager)
