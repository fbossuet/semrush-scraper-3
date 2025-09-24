#!/usr/bin/env python3
"""
Configuration anti-détection avancée pour Playwright
Basé sur les meilleures pratiques pour éviter la détection de bots
"""

import random
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AntiDetectionConfig:
    """Configuration anti-détection pour Playwright"""
    
    def __init__(self):
        self.user_agents = [
            # Chrome Windows (le plus commun)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15'
        ]
        
        self.accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,fr;q=0.8',
            'en-GB,en;q=0.9,en-US;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'en-US,en;q=0.9,es;q=0.8',
            'en-US,en;q=0.9,de;q=0.8'
        ]
        
        self.viewports = [
            {'width': 1920, 'height': 1080},  # Full HD
            {'width': 1366, 'height': 768},   # HD
            {'width': 1536, 'height': 864},   # HD+
            {'width': 1440, 'height': 900},   # WXGA+
            {'width': 1280, 'height': 720},   # HD
            {'width': 1600, 'height': 900}    # HD+
        ]
    
    def get_stealth_browser_args(self) -> List[str]:
        """Retourne les arguments de navigateur pour la discrétion"""
        return [
            # Arguments de base
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            
            # Anti-détection critiques
            '--disable-blink-features=AutomationControlled',
            '--disable-features=VizDisplayCompositor,TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-web-security',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-background-networking',
            '--disable-component-extensions-with-background-pages',
            '--disable-component-update',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--no-first-run',
            '--no-service-autorun',
            '--disable-logging',
            '--disable-gpu-logging',
            '--silent',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-background-mode',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-sync',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--enable-automation',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-features=VizDisplayCompositor',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Optimisation performance
            '--disable-javascript',  # Si pas nécessaire
            '--disable-plugins-discovery',
            '--disable-preconnect',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--no-startup-window'
        ]
    
    def get_random_user_agent(self) -> str:
        """Retourne un User-Agent aléatoire"""
        return random.choice(self.user_agents)
    
    def get_random_accept_language(self) -> str:
        """Retourne un Accept-Language aléatoire"""
        return random.choice(self.accept_languages)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Retourne une résolution aléatoire"""
        return random.choice(self.viewports)
    
    def get_stealth_headers(self) -> Dict[str, str]:
        """Retourne les headers de discrétion"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept-Language': self.get_random_accept_language(),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
    
    def get_stealth_context_config(self) -> Dict:
        """Retourne la configuration complète du contexte"""
        return {
            'headless': True,  # CRITIQUE : Toujours headless
            'args': self.get_stealth_browser_args(),
            'viewport': self.get_random_viewport(),
            'user_agent': self.get_random_user_agent(),
            'extra_http_headers': self.get_stealth_headers(),
            'ignore_https_errors': True,
            'java_script_enabled': True,
            'accept_downloads': False,
            'bypass_csp': True,
            'color_scheme': 'light',
            'forced_colors': 'none',
            'reduced_motion': 'no-preference',
            'screen': {
                'width': self.get_random_viewport()['width'],
                'height': self.get_random_viewport()['height']
            },
            'timezone_id': random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris']),
            'locale': random.choice(['en-US', 'en-GB', 'fr-FR', 'de-DE']),
            'permissions': [],
            'geolocation': None,
            'http_credentials': None,
            'device_scale_factor': 1,
            'is_mobile': False,
            'has_touch': False
        }

# Instance globale
anti_detection_config = AntiDetectionConfig()

def get_stealth_browser_config() -> Dict:
    """Fonction utilitaire pour récupérer la configuration anti-détection"""
    return anti_detection_config.get_stealth_context_config()

def get_stealth_headers() -> Dict[str, str]:
    """Fonction utilitaire pour récupérer les headers anti-détection"""
    return anti_detection_config.get_stealth_headers()

def get_stealth_browser_args() -> List[str]:
    """Fonction utilitaire pour récupérer les arguments anti-détection"""
    return anti_detection_config.get_stealth_browser_args()

if __name__ == "__main__":
    # Test de la configuration
    config = AntiDetectionConfig()
    
    print("🛡️ Configuration Anti-Détection")
    print("=" * 50)
    print(f"User-Agent: {config.get_random_user_agent()}")
    print(f"Accept-Language: {config.get_random_accept_language()}")
    print(f"Viewport: {config.get_random_viewport()}")
    print(f"Headers: {config.get_stealth_headers()}")
    print(f"Browser Args: {len(config.get_stealth_browser_args())} arguments")
    print("=" * 50)
