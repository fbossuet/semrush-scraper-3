#!/usr/bin/env python3
"""
Bootstrap global pour initialisation unique (Xvfb + navigateur/session persistante)
Tous les workers utilisent cette session partagée sans relancer Playwright
"""

import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext
from stealth_system import stealth_system

logger = logging.getLogger(__name__)

class GlobalBootstrap:
    """Bootstrap global unique pour tous les workers"""
    
    def __init__(self):
        self.xvfb_process = None
        self.playwright = None
        self.browser = None
        self.context = None
        self.is_initialized = False
        self.display_num = ":99"
        
    async def initialize_xvfb(self):
        """Initialise Xvfb une seule fois globalement"""
        try:
            if self.xvfb_process is not None:
                logger.info("🖥️ Xvfb déjà initialisé")
                return True
                
            logger.info("🖥️ Initialisation Xvfb global...")
            
            # Vérifier si Xvfb est déjà en cours
            result = subprocess.run(['pgrep', '-f', f'Xvfb {self.display_num}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"🖥️ Xvfb déjà en cours sur {self.display_num}")
                self.xvfb_process = "existing"
                return True
            
            # Lancer Xvfb
            cmd = [
                'Xvfb', self.display_num,
                '-screen', '0', '1920x1080x24',
                '-ac', '+extension', 'GLX', '+render', '-noreset'
            ]
            
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Attendre que Xvfb démarre
            await asyncio.sleep(2)
            
            # Vérifier que Xvfb fonctionne
            result = subprocess.run(['pgrep', '-f', f'Xvfb {self.display_num}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Xvfb initialisé sur {self.display_num}")
                return True
            else:
                logger.error("❌ Échec initialisation Xvfb")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Xvfb: {e}")
            return False
    
    async def initialize_browser(self):
        """Initialise le navigateur une seule fois globalement"""
        try:
            if self.browser is not None:
                logger.info("🌐 Navigateur déjà initialisé")
                return True
                
            logger.info("🌐 Initialisation navigateur global...")
            
            # Initialiser Playwright
            self.playwright = await async_playwright().start()
            
            # Configuration du navigateur
            browser_args = [
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
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                # '--disable-javascript',  # JavaScript nécessaire pour les appels API et scraping
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
            
            # Headers de discrétion
            stealth_headers = stealth_system.get_stealth_headers()
            
            # Lancer le navigateur avec session persistante et headers de discrétion
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir="session-profile-shared",
                headless=True,
                args=browser_args,
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True,
                java_script_enabled=True,
                user_agent=stealth_headers['User-Agent'],
                extra_http_headers=stealth_headers
            )
            
            logger.info("✅ Navigateur global initialisé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation navigateur: {e}")
            return False
    
    async def initialize(self):
        """Initialise le bootstrap global complet"""
        try:
            if self.is_initialized:
                logger.info("✅ Bootstrap déjà initialisé")
                return True
                
            logger.info("🚀 INITIALISATION BOOTSTRAP GLOBAL")
            logger.info("=" * 50)
            
            # Initialiser Xvfb
            if not await self.initialize_xvfb():
                return False
            
            # Initialiser le navigateur
            if not await self.initialize_browser():
                return False
            
            self.is_initialized = True
            logger.info("✅ BOOTSTRAP GLOBAL INITIALISÉ")
            logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur bootstrap global: {e}")
            return False
    
    def get_browser_context(self):
        """Retourne le contexte navigateur partagé"""
        if not self.is_initialized or self.browser is None:
            raise RuntimeError("Bootstrap non initialisé")
        return self.browser
    
    async def cleanup(self):
        """Nettoie les ressources globales"""
        try:
            logger.info("🧹 Nettoyage bootstrap global...")
            
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            if self.xvfb_process and self.xvfb_process != "existing":
                self.xvfb_process.terminate()
                self.xvfb_process = None
            
            self.is_initialized = False
            logger.info("✅ Bootstrap global nettoyé")
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage bootstrap: {e}")

# Instance globale
global_bootstrap = GlobalBootstrap()

async def get_shared_browser_context():
    """Retourne le contexte navigateur partagé (initialise si nécessaire)"""
    if not global_bootstrap.is_initialized:
        await global_bootstrap.initialize()
    return global_bootstrap.get_browser_context()
