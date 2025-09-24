#!/usr/bin/env python3
"""
Injections JavaScript pour masquer les propriétés de détection de bots
Basé sur les techniques anti-détection les plus récentes
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StealthInjections:
    """Injections JavaScript pour masquer les traces de bots"""
    
    def __init__(self):
        self.injections = {
            'webdriver_mask': self._get_webdriver_mask(),
            'navigator_mask': self._get_navigator_mask(),
            'chrome_mask': self._get_chrome_mask(),
            'permissions_mask': self._get_permissions_mask(),
            'plugins_mask': self._get_plugins_mask(),
            'languages_mask': self._get_languages_mask(),
            'webgl_mask': self._get_webgl_mask(),
            'canvas_mask': self._get_canvas_mask(),
            'audio_mask': self._get_audio_mask(),
            'battery_mask': self._get_battery_mask(),
            'connection_mask': self._get_connection_mask(),
            'media_devices_mask': self._get_media_devices_mask(),
            'automation_mask': self._get_automation_mask()
        }
    
    def _get_webdriver_mask(self) -> str:
        """Masque la propriété webdriver"""
        return """
        // Masquer webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Masquer __webdriver_evaluate
        delete window.__webdriver_evaluate;
        delete window.__webdriver_script_function;
        delete window.__webdriver_script_func;
        delete window.__webdriver_script_fn;
        delete window.__fxdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__driver_evaluate;
        delete window.__selenium_unwrapped;
        delete window.__fxdriver_unwrapped;
        """
    
    def _get_navigator_mask(self) -> str:
        """Masque les propriétés suspectes de navigator"""
        return """
        // Masquer les propriétés de détection
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        
        // Masquer les propriétés d'automation
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' })
            }),
        });
        """
    
    def _get_chrome_mask(self) -> str:
        """Masque les propriétés Chrome suspectes"""
        return """
        // Masquer les propriétés Chrome d'automation
        if (window.chrome) {
            Object.defineProperty(window.chrome, 'runtime', {
                get: () => ({
                    onConnect: undefined,
                    onMessage: undefined,
                    connect: undefined,
                    sendMessage: undefined,
                    getManifest: () => ({ name: 'Chrome', version: '120.0.0.0' })
                }),
            });
        }
        
        // Masquer les propriétés d'automation
        delete window.chrome.runtime.onConnect;
        delete window.chrome.runtime.onMessage;
        delete window.chrome.runtime.connect;
        delete window.chrome.runtime.sendMessage;
        """
    
    def _get_permissions_mask(self) -> str:
        """Masque les permissions suspectes"""
        return """
        // Masquer les permissions d'automation
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
    
    def _get_plugins_mask(self) -> str:
        """Masque les plugins suspects"""
        return """
        // Masquer les plugins d'automation
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: { type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin },
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: { type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin },
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: { type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin },
                    1: { type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin },
                    description: "",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });
        """
    
    def _get_languages_mask(self) -> str:
        """Masque les langues suspectes"""
        return """
        // Masquer les langues d'automation
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
        """
    
    def _get_webgl_mask(self) -> str:
        """Masque les propriétés WebGL suspectes"""
        return """
        // Masquer les propriétés WebGL d'automation
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
        """
    
    def _get_canvas_mask(self) -> str:
        """Masque les empreintes canvas"""
        return """
        // Masquer les empreintes canvas
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            if (type === '2d') {
                const context = getContext.apply(this, [type, ...args]);
                const originalFillText = context.fillText;
                context.fillText = function(...args) {
                    // Ajouter du bruit aléatoire
                    const noise = Math.random() * 0.1;
                    args[1] += noise;
                    args[2] += noise;
                    return originalFillText.apply(this, args);
                };
                return context;
            }
            return getContext.apply(this, [type, ...args]);
        };
        """
    
    def _get_audio_mask(self) -> str:
        """Masque les empreintes audio"""
        return """
        // Masquer les empreintes audio
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.apply(this, arguments);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.apply(this, arguments);
                    // Ajouter du bruit aléatoire
                    for (let i = 0; i < array.length; i++) {
                        array[i] += Math.random() * 0.0001;
                    }
                };
                return analyser;
            };
        }
        """
    
    def _get_battery_mask(self) -> str:
        """Masque les propriétés de batterie"""
        return """
        // Masquer les propriétés de batterie
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        """
    
    def _get_connection_mask(self) -> str:
        """Masque les propriétés de connexion"""
        return """
        // Masquer les propriétés de connexion
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            }),
        });
        """
    
    def _get_media_devices_mask(self) -> str:
        """Masque les périphériques média"""
        return """
        // Masquer les périphériques média
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                { deviceId: 'default', groupId: 'group1', kind: 'audioinput', label: 'Default - Microphone' },
                { deviceId: 'default', groupId: 'group2', kind: 'audiooutput', label: 'Default - Speaker' }
            ]);
        }
        """
    
    def _get_automation_mask(self) -> str:
        """Masque les traces d'automation générales"""
        return """
        // Masquer les traces d'automation
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Error;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Error;
        
        // Masquer les propriétés d'automation Playwright
        delete window.__playwright;
        delete window.__pw_manual;
        delete window.__pw_original;
        delete window.__pw_selector;
        delete window.__pw_selector_engine;
        delete window.__pw_selector_engine_version;
        delete window.__pw_selector_engine_version_major;
        delete window.__pw_selector_engine_version_minor;
        delete window.__pw_selector_engine_version_patch;
        delete window.__pw_selector_engine_version_prerelease;
        delete window.__pw_selector_engine_version_build;
        delete window.__pw_selector_engine_version_full;
        delete window.__pw_selector_engine_version_string;
        delete window.__pw_selector_engine_version_array;
        delete window.__pw_selector_engine_version_object;
        delete window.__pw_selector_engine_version_function;
        delete window.__pw_selector_engine_version_boolean;
        delete window.__pw_selector_engine_version_number;
        delete window.__pw_selector_engine_version_undefined;
        delete window.__pw_selector_engine_version_null;
        delete window.__pw_selector_engine_version_symbol;
        delete window.__pw_selector_engine_version_bigint;
        delete window.__pw_selector_engine_version_date;
        delete window.__pw_selector_engine_version_regexp;
        delete window.__pw_selector_engine_version_error;
        delete window.__pw_selector_engine_version_map;
        delete window.__pw_selector_engine_version_set;
        delete window.__pw_selector_engine_version_weakmap;
        delete window.__pw_selector_engine_version_weakset;
        delete window.__pw_selector_engine_version_proxy;
        delete window.__pw_selector_engine_version_promise;
        delete window.__pw_selector_engine_version_generator;
        delete window.__pw_selector_engine_version_asyncgenerator;
        delete window.__pw_selector_engine_version_asyncfunction;
        delete window.__pw_selector_engine_version_function;
        delete window.__pw_selector_engine_version_arrowfunction;
        delete window.__pw_selector_engine_version_method;
        delete window.__pw_selector_engine_version_class;
        delete window.__pw_selector_engine_version_constructor;
        delete window.__pw_selector_engine_version_prototype;
        delete window.__pw_selector_engine_version_arguments;
        delete window.__pw_selector_engine_version_caller;
        delete window.__pw_selector_engine_version_length;
        delete window.__pw_selector_engine_version_name;
        delete window.__pw_selector_engine_version_displayname;
        delete window.__pw_selector_engine_version_tostring;
        delete window.__pw_selector_engine_version_valueof;
        delete window.__pw_selector_engine_version_hasownproperty;
        delete window.__pw_selector_engine_version_propertyisenumerable;
        delete window.__pw_selector_engine_version_isprototypeof;
        delete window.__pw_selector_engine_version_tolocalestring;
        delete window.__pw_selector_engine_version_tolocaledatestring;
        delete window.__pw_selector_engine_version_tolocaletimestring;
        delete window.__pw_selector_engine_version_tolocalenumberstring;
        delete window.__pw_selector_engine_version_tolocalecurrencystring;
        delete window.__pw_selector_engine_version_tolocalestring;
        delete window.__pw_selector_engine_version_tolocaledatestring;
        delete window.__pw_selector_engine_version_tolocaletimestring;
        delete window.__pw_selector_engine_version_tolocalenumberstring;
        delete window.__pw_selector_engine_version_tolocalecurrencystring;
        """
    
    def get_all_injections(self) -> str:
        """Retourne toutes les injections combinées"""
        return '\n'.join(self.injections.values())
    
    def get_injection_by_name(self, name: str) -> str:
        """Retourne une injection spécifique par nom"""
        return self.injections.get(name, '')
    
    async def apply_stealth_injections(self, page) -> None:
        """Applique toutes les injections de discrétion à une page"""
        try:
            # Appliquer toutes les injections
            await page.add_init_script(self.get_all_injections())
            logger.info("✅ Injections de discrétion appliquées")
        except Exception as e:
            logger.error(f"❌ Erreur application injections: {e}")

# Instance globale
stealth_injections = StealthInjections()

async def apply_stealth_to_page(page) -> None:
    """Fonction utilitaire pour appliquer la discrétion à une page"""
    await stealth_injections.apply_stealth_injections(page)

if __name__ == "__main__":
    # Test des injections
    injections = StealthInjections()
    
    print("🛡️ Injections de Discrétion")
    print("=" * 50)
    print(f"Nombre d'injections: {len(injections.injections)}")
    print("Injections disponibles:")
    for name in injections.injections.keys():
        print(f"  - {name}")
    print("=" * 50)
