#!/usr/bin/env python3
"""
Configuration Playwright headless + stealth pour TrendTrack
Implémente les anti-détections et la configuration furtive
"""

import asyncio
import random
import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Configuration du logging
logger = logging.getLogger(__name__)

class StealthBrowser:
    """
    Navigateur Playwright avec configuration stealth et anti-détection
    """
    
    def __init__(self, headless: bool = True, stealth_mode: bool = True):
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.browser = None
        self.context = None
        self.page = None
        
        # Configuration des user agents
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0"
        ]
        
        # Configuration des viewports
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1280, "height": 720},
            {"width": 1600, "height": 900}
        ]
        
        # Configuration des timeouts
        self.timeouts = {
            "navigation": 30000,
            "action": 10000,
            "page_load": 30000
        }

    async def launch(self) -> Browser:
        """
        Lancer le navigateur avec configuration stealth
        """
        try:
            logger.info("🚀 Lancement du navigateur stealth...")
            
            playwright = await async_playwright().start()
            
            # Arguments du navigateur pour la furtivité
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Optionnel : désactiver les images pour la vitesse
                '--disable-javascript',  # Optionnel : désactiver JS si pas nécessaire
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-sync',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-domain-reliability',
                '--disable-component-extensions-with-background-pages',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-sync',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-domain-reliability',
                '--disable-component-extensions-with-background-pages',
                '--disable-background-networking'
            ]
            
            # Lancer le navigateur
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args,
                slow_mo=random.randint(50, 150)  # Délai aléatoire entre les actions
            )
            
            logger.info("✅ Navigateur lancé avec succès")
            return self.browser
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du lancement du navigateur: {e}")
            raise

    async def create_context(self) -> BrowserContext:
        """
        Créer un contexte de navigateur avec configuration stealth
        """
        try:
            if not self.browser:
                await self.launch()
            
            logger.info("🔧 Création du contexte stealth...")
            
            # Sélectionner un user agent aléatoire
            user_agent = random.choice(self.user_agents)
            logger.info(f"🔍 User-Agent sélectionné: {user_agent[:50]}...")
            
            # Sélectionner un viewport aléatoire
            viewport = random.choice(self.viewports)
            logger.info(f"📱 Viewport sélectionné: {viewport['width']}x{viewport['height']}")
            
            # Configuration du contexte
            context_options = {
                "user_agent": user_agent,
                "viewport": viewport,
                "locale": "fr-FR",
                "timezone_id": "Europe/Paris",
                "permissions": ["geolocation"],
                "geolocation": {"latitude": 48.8566, "longitude": 2.3522},  # Paris
                "color_scheme": "light",
                "reduced_motion": "no-preference",
                "forced_colors": "none",
                "accept_downloads": False,
                "has_touch": False,
                "is_mobile": False,
                "device_scale_factor": 1,
                "screen": viewport,
                "extra_http_headers": {
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0"
                }
            }
            
            # Créer le contexte
            self.context = await self.browser.new_context(**context_options)
            
            # Ajouter des scripts d'anti-détection
            if self.stealth_mode:
                await self._add_stealth_scripts()
            
            logger.info("✅ Contexte stealth créé avec succès")
            return self.context
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du contexte: {e}")
            raise

    async def _add_stealth_scripts(self):
        """
        Ajouter des scripts d'anti-détection au contexte
        """
        try:
            logger.info("🛡️ Ajout des scripts d'anti-détection...")
            
            # Script pour masquer les propriétés d'automatisation
            stealth_script = """
            // Masquer les propriétés d'automatisation
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Masquer les propriétés Playwright
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Masquer les propriétés Chrome
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en'],
            });
            
            // Masquer les propriétés de résolution
            Object.defineProperty(screen, 'availHeight', {
                get: () => window.innerHeight,
            });
            
            Object.defineProperty(screen, 'availWidth', {
                get: () => window.innerWidth,
            });
            
            // Masquer les propriétés de timezone
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                value: function() {
                    return {
                        locale: 'fr-FR',
                        timeZone: 'Europe/Paris'
                    };
                }
            });
            
            // Masquer les propriétés de permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Masquer les propriétés de canvas
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                if (type === '2d') {
                    const context = getContext.call(this, type);
                    const originalFillText = context.fillText;
                    context.fillText = function() {
                        // Ajouter du bruit aléatoire
                        const noise = Math.random() * 0.1;
                        arguments[1] += noise;
                        arguments[2] += noise;
                        return originalFillText.apply(this, arguments);
                    };
                    return context;
                }
                return getContext.call(this, type);
            };
            
            // Masquer les propriétés de WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
            
            // Masquer les propriétés de AudioContext
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                AudioContext.prototype.createAnalyser = function() {
                    const analyser = originalCreateAnalyser.call(this);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.call(this, array);
                        // Ajouter du bruit aléatoire
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.random() * 0.1;
                        }
                    };
                    return analyser;
                };
            }
            """
            
            # Ajouter le script au contexte
            await self.context.add_init_script(stealth_script)
            
            logger.info("✅ Scripts d'anti-détection ajoutés")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout des scripts stealth: {e}")
            raise

    async def new_page(self) -> Page:
        """
        Créer une nouvelle page avec configuration stealth
        """
        try:
            if not self.context:
                await self.create_context()
            
            logger.info("📄 Création d'une nouvelle page stealth...")
            
            # Créer la page
            self.page = await self.context.new_page()
            
            # Configurer les timeouts
            self.page.set_default_timeout(self.timeouts["action"])
            self.page.set_default_navigation_timeout(self.timeouts["navigation"])
            
            # Ajouter des event listeners pour la furtivité
            await self._add_page_stealth_features()
            
            logger.info("✅ Page stealth créée avec succès")
            return self.page
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la page: {e}")
            raise

    async def _add_page_stealth_features(self):
        """
        Ajouter des fonctionnalités stealth à la page
        """
        try:
            # Intercepter les requêtes pour ajouter des headers aléatoires
            await self.page.route("**/*", self._handle_route)
            
            # Ajouter des event listeners pour simuler un comportement humain
            await self.page.evaluate("""
                // Simuler des mouvements de souris aléatoires
                setInterval(() => {
                    const x = Math.random() * window.innerWidth;
                    const y = Math.random() * window.innerHeight;
                    const event = new MouseEvent('mousemove', {
                        clientX: x,
                        clientY: y,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }, Math.random() * 5000 + 2000);
                
                // Simuler des clics aléatoires (sans action)
                setInterval(() => {
                    if (Math.random() > 0.95) {
                        const event = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true
                        });
                        document.dispatchEvent(event);
                    }
                }, Math.random() * 10000 + 5000);
            """)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout des fonctionnalités stealth: {e}")

    async def _handle_route(self, route):
        """
        Gérer les requêtes pour ajouter des headers aléatoires
        """
        try:
            # Ajouter des headers aléatoires
            headers = route.request.headers
            headers["X-Forwarded-For"] = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            headers["X-Real-IP"] = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            # Continuer la requête
            await route.continue_(headers=headers)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la requête: {e}")
            await route.continue_()

    async def random_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """
        Ajouter un délai aléatoire pour simuler un comportement humain
        """
        delay = random.randint(min_ms, max_ms)
        logger.info(f"⏱️ Délai aléatoire: {delay}ms")
        await asyncio.sleep(delay / 1000)

    async def human_like_click(self, selector: str, timeout: int = 10000):
        """
        Effectuer un clic de manière humaine
        """
        try:
            # Attendre que l'élément soit visible
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            # Délai aléatoire avant le clic
            await self.random_delay(500, 1500)
            
            # Hover sur l'élément
            await self.page.hover(selector)
            await self.random_delay(200, 500)
            
            # Clic
            await self.page.click(selector)
            
            # Délai aléatoire après le clic
            await self.random_delay(300, 800)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du clic humain: {e}")
            raise

    async def human_like_type(self, selector: str, text: str, timeout: int = 10000):
        """
        Taper du texte de manière humaine
        """
        try:
            # Attendre que l'élément soit visible
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            # Délai aléatoire avant de commencer à taper
            await self.random_delay(500, 1500)
            
            # Cliquer sur l'élément
            await self.page.click(selector)
            await self.random_delay(200, 500)
            
            # Effacer le contenu existant
            await self.page.fill(selector, "")
            await self.random_delay(100, 300)
            
            # Taper caractère par caractère avec des délais aléatoires
            for char in text:
                await self.page.type(selector, char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Délai aléatoire après avoir fini de taper
            await self.random_delay(300, 800)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la saisie humaine: {e}")
            raise

    async def close(self):
        """
        Fermer le navigateur et nettoyer les ressources
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            logger.info("✅ Navigateur fermé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la fermeture: {e}")

    async def __aenter__(self):
        """Support pour async context manager"""
        await self.launch()
        await self.create_context()
        await self.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support pour async context manager"""
        await self.close()

# Instance globale pour compatibilité
stealth_browser = StealthBrowser()

# Fonctions de compatibilité
async def create_stealth_browser(headless: bool = True, stealth_mode: bool = True) -> StealthBrowser:
    """Créer un navigateur stealth"""
    browser = StealthBrowser(headless=headless, stealth_mode=stealth_mode)
    await browser.launch()
    await browser.create_context()
    await browser.new_page()
    return browser

async def get_stealth_page() -> Page:
    """Récupérer la page stealth globale"""
    if not stealth_browser.page:
        await stealth_browser.launch()
        await stealth_browser.create_context()
        await stealth_browser.new_page()
    return stealth_browser.page

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du navigateur stealth"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    async with StealthBrowser(headless=True, stealth_mode=True) as browser:
        page = browser.page
        
        # Navigation vers une page
        await page.goto("https://httpbin.org/headers")
        
        # Attendre un peu
        await browser.random_delay(2000, 4000)
        
        # Récupérer le contenu
        content = await page.content()
        print("✅ Page chargée avec succès")
        print(f"📄 Contenu (premiers 500 chars): {content[:500]}...")

if __name__ == "__main__":
    asyncio.run(main())
