#!/usr/bin/env python3
"""
Test de détection pour vérifier l'efficacité des protections anti-détection
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from anti_detection_config import get_stealth_browser_config, get_stealth_headers
from stealth_injections import apply_stealth_to_page

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StealthDetectionTester:
    """Testeur de détection pour vérifier les protections"""
    
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
        self.detection_results = {}
    
    async def initialize(self):
        """Initialise le testeur"""
        try:
            logger.info("🛡️ Initialisation du testeur de détection")
            
            self.playwright = await async_playwright().start()
            
            # Configuration anti-détection
            stealth_config = get_stealth_browser_config()
            
            # Lancer le navigateur avec protection
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir='./test-stealth-profile',
                **stealth_config
            )
            
            # Créer une page
            self.page = await self.context.new_page()
            
            # Appliquer les injections de discrétion
            await apply_stealth_to_page(self.page)
            
            # Configurer les headers
            stealth_headers = get_stealth_headers()
            await self.page.set_extra_http_headers(stealth_headers)
            
            logger.info("✅ Testeur initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            return False
    
    async def test_webdriver_detection(self):
        """Test la détection de webdriver"""
        try:
            logger.info("🧪 Test de détection webdriver")
            
            # Naviguer vers une page de test
            await self.page.goto("https://bot.sannysoft.com/", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Vérifier les propriétés webdriver
            webdriver_detected = await self.page.evaluate("""
                () => {
                    return {
                        webdriver: navigator.webdriver,
                        webdriver_evaluate: window.__webdriver_evaluate,
                        webdriver_script_function: window.__webdriver_script_function,
                        playwright: window.__playwright,
                        pw_manual: window.__pw_manual
                    }
                }
            """)
            
            self.detection_results['webdriver'] = webdriver_detected
            
            # Vérifier si webdriver est détecté
            if webdriver_detected['webdriver'] is not None:
                logger.warning("⚠️ Webdriver détecté!")
            else:
                logger.info("✅ Webdriver masqué avec succès")
            
            return webdriver_detected
            
        except Exception as e:
            logger.error(f"❌ Erreur test webdriver: {e}")
            return None
    
    async def test_navigator_properties(self):
        """Test les propriétés de navigator"""
        try:
            logger.info("🧪 Test des propriétés navigator")
            
            # Vérifier les propriétés navigator
            navigator_props = await self.page.evaluate("""
                () => {
                    return {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        languages: navigator.languages,
                        plugins: navigator.plugins.length,
                        webdriver: navigator.webdriver,
                        permissions: typeof navigator.permissions,
                        connection: typeof navigator.connection,
                        getBattery: typeof navigator.getBattery,
                        mediaDevices: typeof navigator.mediaDevices
                    }
                }
            """)
            
            self.detection_results['navigator'] = navigator_props
            
            logger.info(f"✅ Propriétés navigator: {navigator_props}")
            return navigator_props
            
        except Exception as e:
            logger.error(f"❌ Erreur test navigator: {e}")
            return None
    
    async def test_chrome_properties(self):
        """Test les propriétés Chrome"""
        try:
            logger.info("🧪 Test des propriétés Chrome")
            
            # Vérifier les propriétés Chrome
            chrome_props = await self.page.evaluate("""
                () => {
                    if (window.chrome) {
                        return {
                            chrome: true,
                            runtime: typeof window.chrome.runtime,
                            runtime_onConnect: typeof window.chrome.runtime.onConnect,
                            runtime_onMessage: typeof window.chrome.runtime.onMessage,
                            runtime_connect: typeof window.chrome.runtime.connect,
                            runtime_sendMessage: typeof window.chrome.runtime.sendMessage
                        }
                    } else {
                        return { chrome: false }
                    }
                }
            """)
            
            self.detection_results['chrome'] = chrome_props
            
            logger.info(f"✅ Propriétés Chrome: {chrome_props}")
            return chrome_props
            
        except Exception as e:
            logger.error(f"❌ Erreur test Chrome: {e}")
            return None
    
    async def test_automation_detection(self):
        """Test la détection d'automation"""
        try:
            logger.info("🧪 Test de détection d'automation")
            
            # Vérifier les traces d'automation
            automation_traces = await self.page.evaluate("""
                () => {
                    const traces = [];
                    
                    // Vérifier les propriétés d'automation
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Array) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Array');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Promise) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Promise');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Symbol');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_JSON) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_JSON');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Object) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Object');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Proxy');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Reflect');
                    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Error) traces.push('cdc_adoQpoasnfa76pfcZLmcfl_Error');
                    
                    // Vérifier les propriétés Playwright
                    if (window.__playwright) traces.push('__playwright');
                    if (window.__pw_manual) traces.push('__pw_manual');
                    if (window.__pw_original) traces.push('__pw_original');
                    if (window.__pw_selector) traces.push('__pw_selector');
                    
                    return {
                        traces_found: traces,
                        count: traces.length
                    }
                }
            """)
            
            self.detection_results['automation'] = automation_traces
            
            if automation_traces['count'] > 0:
                logger.warning(f"⚠️ Traces d'automation détectées: {automation_traces['traces_found']}")
            else:
                logger.info("✅ Aucune trace d'automation détectée")
            
            return automation_traces
            
        except Exception as e:
            logger.error(f"❌ Erreur test automation: {e}")
            return None
    
    async def test_fingerprinting(self):
        """Test le fingerprinting"""
        try:
            logger.info("🧪 Test de fingerprinting")
            
            # Vérifier le fingerprinting
            fingerprint = await self.page.evaluate("""
                () => {
                    return {
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            availWidth: screen.availWidth,
                            availHeight: screen.availHeight,
                            colorDepth: screen.colorDepth,
                            pixelDepth: screen.pixelDepth
                        },
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        language: navigator.language,
                        platform: navigator.platform,
                        userAgent: navigator.userAgent,
                        hardwareConcurrency: navigator.hardwareConcurrency,
                        deviceMemory: navigator.deviceMemory,
                        maxTouchPoints: navigator.maxTouchPoints
                    }
                }
            """)
            
            self.detection_results['fingerprint'] = fingerprint
            
            logger.info(f"✅ Fingerprint: {fingerprint}")
            return fingerprint
            
        except Exception as e:
            logger.error(f"❌ Erreur test fingerprinting: {e}")
            return None
    
    async def run_all_tests(self):
        """Exécute tous les tests de détection"""
        try:
            logger.info("🚀 Démarrage des tests de détection")
            
            # Initialiser le testeur
            if not await self.initialize():
                logger.error("❌ Échec initialisation testeur")
                return False
            
            # Exécuter tous les tests
            await self.test_webdriver_detection()
            await self.test_navigator_properties()
            await self.test_chrome_properties()
            await self.test_automation_detection()
            await self.test_fingerprinting()
            
            # Afficher les résultats
            self.display_results()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur tests: {e}")
            return False
        finally:
            await self.cleanup()
    
    def display_results(self):
        """Affiche les résultats des tests"""
        logger.info("📊 RÉSULTATS DES TESTS DE DÉTECTION")
        logger.info("=" * 60)
        
        for test_name, results in self.detection_results.items():
            logger.info(f"\n🧪 {test_name.upper()}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    logger.info(f"   {key}: {value}")
            else:
                logger.info(f"   {results}")
        
        logger.info("\n" + "=" * 60)
        
        # Évaluation globale
        vulnerabilities = []
        
        # Vérifier webdriver
        if self.detection_results.get('webdriver', {}).get('webdriver') is not None:
            vulnerabilities.append("Webdriver détecté")
        
        # Vérifier les traces d'automation
        if self.detection_results.get('automation', {}).get('count', 0) > 0:
            vulnerabilities.append("Traces d'automation détectées")
        
        if vulnerabilities:
            logger.warning(f"⚠️ VULNÉRABILITÉS DÉTECTÉES: {', '.join(vulnerabilities)}")
        else:
            logger.info("✅ AUCUNE VULNÉRABILITÉ DÉTECTÉE")
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✅ Nettoyage terminé")
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage: {e}")

async def main():
    """Fonction principale"""
    tester = StealthDetectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
