#!/usr/bin/env python3
"""
Script de debug pour analyser le problème de session Semrush
- Capture le contenu de chaque page à chaque étape
- Analyse les cookies et headers
- Compare avec l'état précédent
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le chemin src
sys.path.insert(0, 'src')

from main import NoxtoolsScraper
from src.services.shop_repository import ShopRepository, ShopRepositoryConfig

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_session_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SessionDebugger:
    """Debugger pour analyser les problèmes de session."""
    
    def __init__(self):
        self.debug_data = {
            'timestamp': datetime.now().isoformat(),
            'steps': [],
            'cookies': [],
            'headers': [],
            'page_contents': [],
            'errors': []
        }
        self.output_dir = Path('debug_output')
        self.output_dir.mkdir(exist_ok=True)
    
    async def capture_page_state(self, page, step_name: str, url: str = None):
        """Capture l'état complet d'une page."""
        try:
            if url is None:
                url = page.url
            
            # Contenu de la page
            page_content = await page.evaluate('document.body.innerText')
            page_html = await page.content()
            
            # Cookies
            cookies = await page.context.cookies()
            
            # Headers (approximation)
            headers = await page.evaluate('''
                () => {
                    const headers = {};
                    // Essayer de capturer les headers via performance API
                    const perfEntries = performance.getEntriesByType('navigation');
                    if (perfEntries.length > 0) {
                        headers['referrer'] = document.referrer;
                        headers['user_agent'] = navigator.userAgent;
                    }
                    return headers;
                }
            ''')
            
            # Éléments de la page
            elements = await page.evaluate('''
                () => {
                    const elements = {
                        inputs: [],
                        buttons: [],
                        forms: [],
                        links: []
                    };
                    
                    // Inputs
                    document.querySelectorAll('input').forEach((input, i) => {
                        elements.inputs.push({
                            index: i,
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            placeholder: input.placeholder,
                            value: input.value,
                            class: input.className
                        });
                    });
                    
                    // Buttons
                    document.querySelectorAll('button').forEach((button, i) => {
                        elements.buttons.push({
                            index: i,
                            text: button.textContent?.trim(),
                            type: button.type,
                            class: button.className,
                            data_test: button.getAttribute('data-test'),
                            data_testid: button.getAttribute('data-testid')
                        });
                    });
                    
                    // Forms
                    document.querySelectorAll('form').forEach((form, i) => {
                        elements.forms.push({
                            index: i,
                            action: form.action,
                            method: form.method,
                            class: form.className
                        });
                    });
                    
                    return elements;
                }
            ''')
            
            step_data = {
                'step_name': step_name,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'page_content': page_content[:2000],  # Limiter la taille
                'page_html': page_html[:5000],  # Limiter la taille
                'cookies': cookies,
                'headers': headers,
                'elements': elements,
                'title': await page.title(),
                'viewport': await page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            }
            
            self.debug_data['steps'].append(step_data)
            
            # Sauvegarder individuellement
            step_file = self.output_dir / f"step_{len(self.debug_data['steps']):02d}_{step_name.replace(' ', '_')}.json"
            with open(step_file, 'w', encoding='utf-8') as f:
                json.dump(step_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📸 Captured step: {step_name} - {url}")
            
        except Exception as e:
            error_data = {
                'step_name': step_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.debug_data['errors'].append(error_data)
            logger.error(f"❌ Error capturing step {step_name}: {e}")
    
    async def analyze_session_flow(self):
        """Analyser le flux de session complet."""
        try:
            logger.info("🔍 Starting session flow analysis...")
            
            # Créer le scraper
            scraper = NoxtoolsScraper()
            
            # Initialisation
            await scraper.initialize()
            page = await scraper.playwright_manager.new_page()
            await self.capture_page_state(page, "01_after_initialize", "initialized")
            
            # Authentification
            auth_success = await scraper.authenticate()
            await self.capture_page_state(page, "02_after_auth", "authenticated")
            
            if not auth_success:
                logger.error("❌ Authentication failed")
                return
            
            # Test de navigation vers Market Overview
            logger.info("🌐 Testing Market Overview navigation...")
            
            # Créer une nouvelle page pour le test
            test_page = await scraper.playwright_manager.new_page()
            await self.capture_page_state(test_page, "03_new_page_created", test_page.url)
            
            # Naviguer vers dashboard
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://noxtools.com/secure/member')
            await self.capture_page_state(test_page, "04_dashboard_reached", test_page.url)
            
            # Naviguer vers bridge
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://semrush.noxtools.com/server3.php')
            await self.capture_page_state(test_page, "05_bridge_reached", test_page.url)
            
            # Naviguer vers Market Overview
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://semrush1.semrush.pw/analytics/traffic/market-overview/')
            await self.capture_page_state(test_page, "06_market_overview_reached", test_page.url)
            
            # Analyser le contenu de la page Market Overview
            await self.analyze_market_overview_page(test_page)
            
            # Nettoyage
            await scraper.cleanup()
            
            # Sauvegarder les données complètes
            self.save_debug_data()
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            self.debug_data['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def analyze_market_overview_page(self, page):
        """Analyser spécifiquement la page Market Overview."""
        try:
            # Attendre que la page soit chargée
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Capturer l'état après chargement
            await self.capture_page_state(page, "08_market_overview_loaded", page.url)
            
            # Vérifier la présence d'éléments de recherche
            search_elements = await page.evaluate('''
                () => {
                    const elements = {
                        primary_input: !!document.querySelector('input[name="competitors.0"]'),
                        primary_button: !!document.querySelector('button[data-testid="analyze-cta"]'),
                        secondary_input: !!document.querySelector('input[data-test="searchbar_input"]'),
                        secondary_button: !!document.querySelector('button[data-test="searchbar_search_submit"]'),
                        all_inputs: document.querySelectorAll('input').length,
                        all_buttons: document.querySelectorAll('button').length
                    };
                    return elements;
                }
            ''')
            
            logger.info(f"🔍 Search elements found: {search_elements}")
            
            # Vérifier la présence de messages d'erreur
            error_messages = await page.evaluate('''
                () => {
                    const text = document.body.innerText.toLowerCase();
                    const errors = [];
                    
                    if (text.includes('session expired')) errors.push('session_expired');
                    if (text.includes('access again from dashboard')) errors.push('access_again_dashboard');
                    if (text.includes('please login')) errors.push('please_login');
                    if (text.includes('authentication required')) errors.push('auth_required');
                    if (text.includes('unauthorized')) errors.push('unauthorized');
                    if (text.includes('forbidden')) errors.push('forbidden');
                    
                    return errors;
                }
            ''')
            
            logger.info(f"🚨 Error messages found: {error_messages}")
            
            # Capturer l'état final
            await self.capture_page_state(page, "09_market_overview_analysis", page.url)
            
        except Exception as e:
            logger.error(f"❌ Market overview analysis error: {e}")
    
    def save_debug_data(self):
        """Sauvegarder toutes les données de debug."""
        try:
            # Sauvegarder le fichier principal
            main_file = self.output_dir / "debug_session_analysis.json"
            with open(main_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_data, f, indent=2, ensure_ascii=False)
            
            # Créer un résumé
            summary = {
                'total_steps': len(self.debug_data['steps']),
                'total_errors': len(self.debug_data['errors']),
                'analysis_timestamp': self.debug_data['timestamp'],
                'steps_summary': [
                    {
                        'step': step['step_name'],
                        'url': step['url'],
                        'title': step.get('title', 'N/A'),
                        'elements_count': {
                            'inputs': len(step.get('elements', {}).get('inputs', [])),
                            'buttons': len(step.get('elements', {}).get('buttons', []))
                        }
                    }
                    for step in self.debug_data['steps']
                ]
            }
            
            summary_file = self.output_dir / "debug_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Debug data saved to {self.output_dir}")
            logger.info(f"📊 Summary: {summary['total_steps']} steps, {summary['total_errors']} errors")
            
        except Exception as e:
            logger.error(f"❌ Error saving debug data: {e}")

async def main():
    """Fonction principale de debug."""
    debugger = SessionDebugger()
    await debugger.analyze_session_flow()

if __name__ == "__main__":
    asyncio.run(main())

Script de debug pour analyser le problème de session Semrush
- Capture le contenu de chaque page à chaque étape
- Analyse les cookies et headers
- Compare avec l'état précédent
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le chemin src
sys.path.insert(0, 'src')

from main import NoxtoolsScraper
from src.services.shop_repository import ShopRepository, ShopRepositoryConfig

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_session_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SessionDebugger:
    """Debugger pour analyser les problèmes de session."""
    
    def __init__(self):
        self.debug_data = {
            'timestamp': datetime.now().isoformat(),
            'steps': [],
            'cookies': [],
            'headers': [],
            'page_contents': [],
            'errors': []
        }
        self.output_dir = Path('debug_output')
        self.output_dir.mkdir(exist_ok=True)
    
    async def capture_page_state(self, page, step_name: str, url: str = None):
        """Capture l'état complet d'une page."""
        try:
            if url is None:
                url = page.url
            
            # Contenu de la page
            page_content = await page.evaluate('document.body.innerText')
            page_html = await page.content()
            
            # Cookies
            cookies = await page.context.cookies()
            
            # Headers (approximation)
            headers = await page.evaluate('''
                () => {
                    const headers = {};
                    // Essayer de capturer les headers via performance API
                    const perfEntries = performance.getEntriesByType('navigation');
                    if (perfEntries.length > 0) {
                        headers['referrer'] = document.referrer;
                        headers['user_agent'] = navigator.userAgent;
                    }
                    return headers;
                }
            ''')
            
            # Éléments de la page
            elements = await page.evaluate('''
                () => {
                    const elements = {
                        inputs: [],
                        buttons: [],
                        forms: [],
                        links: []
                    };
                    
                    // Inputs
                    document.querySelectorAll('input').forEach((input, i) => {
                        elements.inputs.push({
                            index: i,
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            placeholder: input.placeholder,
                            value: input.value,
                            class: input.className
                        });
                    });
                    
                    // Buttons
                    document.querySelectorAll('button').forEach((button, i) => {
                        elements.buttons.push({
                            index: i,
                            text: button.textContent?.trim(),
                            type: button.type,
                            class: button.className,
                            data_test: button.getAttribute('data-test'),
                            data_testid: button.getAttribute('data-testid')
                        });
                    });
                    
                    // Forms
                    document.querySelectorAll('form').forEach((form, i) => {
                        elements.forms.push({
                            index: i,
                            action: form.action,
                            method: form.method,
                            class: form.className
                        });
                    });
                    
                    return elements;
                }
            ''')
            
            step_data = {
                'step_name': step_name,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'page_content': page_content[:2000],  # Limiter la taille
                'page_html': page_html[:5000],  # Limiter la taille
                'cookies': cookies,
                'headers': headers,
                'elements': elements,
                'title': await page.title(),
                'viewport': await page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            }
            
            self.debug_data['steps'].append(step_data)
            
            # Sauvegarder individuellement
            step_file = self.output_dir / f"step_{len(self.debug_data['steps']):02d}_{step_name.replace(' ', '_')}.json"
            with open(step_file, 'w', encoding='utf-8') as f:
                json.dump(step_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📸 Captured step: {step_name} - {url}")
            
        except Exception as e:
            error_data = {
                'step_name': step_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.debug_data['errors'].append(error_data)
            logger.error(f"❌ Error capturing step {step_name}: {e}")
    
    async def analyze_session_flow(self):
        """Analyser le flux de session complet."""
        try:
            logger.info("🔍 Starting session flow analysis...")
            
            # Créer le scraper
            scraper = NoxtoolsScraper()
            
            # Initialisation
            await scraper.initialize()
            page = await scraper.playwright_manager.new_page()
            await self.capture_page_state(page, "01_after_initialize", "initialized")
            
            # Authentification
            auth_success = await scraper.authenticate()
            await self.capture_page_state(page, "02_after_auth", "authenticated")
            
            if not auth_success:
                logger.error("❌ Authentication failed")
                return
            
            # Test de navigation vers Market Overview
            logger.info("🌐 Testing Market Overview navigation...")
            
            # Créer une nouvelle page pour le test
            test_page = await scraper.playwright_manager.new_page()
            await self.capture_page_state(test_page, "03_new_page_created", test_page.url)
            
            # Naviguer vers dashboard
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://noxtools.com/secure/member')
            await self.capture_page_state(test_page, "04_dashboard_reached", test_page.url)
            
            # Naviguer vers bridge
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://semrush.noxtools.com/server3.php')
            await self.capture_page_state(test_page, "05_bridge_reached", test_page.url)
            
            # Naviguer vers Market Overview
            await scraper.playwright_manager.navigate_with_retry(test_page, 'https://semrush1.semrush.pw/analytics/traffic/market-overview/')
            await self.capture_page_state(test_page, "06_market_overview_reached", test_page.url)
            
            # Analyser le contenu de la page Market Overview
            await self.analyze_market_overview_page(test_page)
            
            # Nettoyage
            await scraper.cleanup()
            
            # Sauvegarder les données complètes
            self.save_debug_data()
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            self.debug_data['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def analyze_market_overview_page(self, page):
        """Analyser spécifiquement la page Market Overview."""
        try:
            # Attendre que la page soit chargée
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Capturer l'état après chargement
            await self.capture_page_state(page, "08_market_overview_loaded", page.url)
            
            # Vérifier la présence d'éléments de recherche
            search_elements = await page.evaluate('''
                () => {
                    const elements = {
                        primary_input: !!document.querySelector('input[name="competitors.0"]'),
                        primary_button: !!document.querySelector('button[data-testid="analyze-cta"]'),
                        secondary_input: !!document.querySelector('input[data-test="searchbar_input"]'),
                        secondary_button: !!document.querySelector('button[data-test="searchbar_search_submit"]'),
                        all_inputs: document.querySelectorAll('input').length,
                        all_buttons: document.querySelectorAll('button').length
                    };
                    return elements;
                }
            ''')
            
            logger.info(f"🔍 Search elements found: {search_elements}")
            
            # Vérifier la présence de messages d'erreur
            error_messages = await page.evaluate('''
                () => {
                    const text = document.body.innerText.toLowerCase();
                    const errors = [];
                    
                    if (text.includes('session expired')) errors.push('session_expired');
                    if (text.includes('access again from dashboard')) errors.push('access_again_dashboard');
                    if (text.includes('please login')) errors.push('please_login');
                    if (text.includes('authentication required')) errors.push('auth_required');
                    if (text.includes('unauthorized')) errors.push('unauthorized');
                    if (text.includes('forbidden')) errors.push('forbidden');
                    
                    return errors;
                }
            ''')
            
            logger.info(f"🚨 Error messages found: {error_messages}")
            
            # Capturer l'état final
            await self.capture_page_state(page, "09_market_overview_analysis", page.url)
            
        except Exception as e:
            logger.error(f"❌ Market overview analysis error: {e}")
    
    def save_debug_data(self):
        """Sauvegarder toutes les données de debug."""
        try:
            # Sauvegarder le fichier principal
            main_file = self.output_dir / "debug_session_analysis.json"
            with open(main_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_data, f, indent=2, ensure_ascii=False)
            
            # Créer un résumé
            summary = {
                'total_steps': len(self.debug_data['steps']),
                'total_errors': len(self.debug_data['errors']),
                'analysis_timestamp': self.debug_data['timestamp'],
                'steps_summary': [
                    {
                        'step': step['step_name'],
                        'url': step['url'],
                        'title': step.get('title', 'N/A'),
                        'elements_count': {
                            'inputs': len(step.get('elements', {}).get('inputs', [])),
                            'buttons': len(step.get('elements', {}).get('buttons', []))
                        }
                    }
                    for step in self.debug_data['steps']
                ]
            }
            
            summary_file = self.output_dir / "debug_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Debug data saved to {self.output_dir}")
            logger.info(f"📊 Summary: {summary['total_steps']} steps, {summary['total_errors']} errors")
            
        except Exception as e:
            logger.error(f"❌ Error saving debug data: {e}")

async def main():
    """Fonction principale de debug."""
    debugger = SessionDebugger()
    await debugger.analyze_session_flow()

if __name__ == "__main__":
    asyncio.run(main())
