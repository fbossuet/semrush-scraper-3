#!/usr/bin/env python3
"""
Scraper Noxtools Alpha - Point d'entrée principal
- Orchestration de tous les modules core
- Gestion des credentials et configuration
- Workflow complet de scraping
- Intégration avec la base de données TrendTrack
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.server_manager import get_server_manager, reset_server_manager
from core.auth_manager import AuthManager, AuthConfig
from core.playwright_manager import PlaywrightManager
from core.metrics_extractor import MetricsExtractor, MetricsConfig
from core.navigation_manager import NavigationManager, NavigationConfig
from core.session_manager import SessionManager, SessionConfig
from services.formatter import format_metrics
from utils.url_params import get_url_params_info, build_market_overview_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/noxtools_alpha_main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """Configuration principale du scraper Noxtools Alpha."""
    # Credentials
    username: str = "johnychareon"
    password: str = "fbossuetg"
    
    # Configuration de scraping
    max_shops_per_run: int = 10
    max_retries: int = 3
    timeout_ms: int = 60000
    
    # Base de données
    db_path: str = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    
    # Logs
    log_level: str = "INFO"
    log_file: str = "logs/noxtools_alpha_main.log"

class NoxtoolsScraper:
    """
    Scraper principal Noxtools Alpha.
    
    Orchestre tous les modules pour effectuer le scraping complet :
    1. Authentification Noxtools
    2. Navigation vers les métriques
    3. Extraction des données
    4. Formatage et sauvegarde
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """Initialise le scraper avec la configuration."""
        self.config = config or ScraperConfig()
        
        # Initialiser les managers
        self.server_manager = get_server_manager()
        self.auth_manager = AuthManager()
        self.playwright_manager = PlaywrightManager()
        self.metrics_extractor = MetricsExtractor()
        self.navigation_manager = NavigationManager()
        self.session_manager = SessionManager()
        
        # État du scraper
        self.is_initialized = False
        self.is_authenticated = False
        self.current_page = None
        
        logger.info(f"🚀 NoxtoolsScraper initialisé avec {self.config.max_shops_per_run} boutiques max")
    
    async def initialize(self) -> bool:
        """Initialise le scraper et tous ses composants."""
        try:
            logger.info("🔧 Initialisation du scraper...")
            
            # Créer le dossier logs
            Path("logs").mkdir(exist_ok=True)
            
            # Initialiser Playwright
            await self.playwright_manager.initialize()
            logger.info("✅ Playwright initialisé")
            
            # Créer une nouvelle page
            self.current_page = await self.playwright_manager.new_page()
            logger.info("✅ Page créée")
            
            self.is_initialized = True
            logger.info("🎉 Scraper initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authentifie le scraper sur Noxtools."""
        try:
            if not self.is_initialized:
                logger.error("❌ Scraper non initialisé")
                return False
            
            logger.info("🔐 Authentification sur Noxtools...")
            logger.info(f"📧 Username: {self.config.username}")
            logger.info(f"🔑 Password: {'*' * len(self.config.password)}")
            
            # Authentification
            auth_result = await self.auth_manager.authenticate(
                self.current_page,
                self.config.username,
                self.config.password,
                self.playwright_manager
            )
            
            if auth_result:
                self.is_authenticated = True
                logger.info("✅ Authentification réussie")
                return True
            else:
                logger.error("❌ Authentification échouée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur d'authentification: {e}")
            return False
    
    async def scrape_shop_metrics(self, domain: str) -> Optional[Dict[str, Any]]:
        """Scrape les métriques pour un domaine spécifique."""
        try:
            logger.info(f"📊 [DEBUG] Starting shop metrics scraping for: {domain}")
            logger.info(f"📊 [DEBUG] Authentication status: {self.is_authenticated}")
            logger.info(f"📊 [DEBUG] Current page URL: {self.current_page.url}")
            logger.info(f"📊 [DEBUG] Current page title: {await self.current_page.title()}")
            
            if not self.is_authenticated:
                logger.error("❌ [DEBUG] Not authenticated")
                return None
            
            logger.info(f"📊 [DEBUG] Scraping des métriques pour: {domain}")
            
            # Le MetricsExtractor gère maintenant la navigation avec FID dynamique
            logger.info(f"🌐 [DEBUG] Navigation vers métriques avec FID dynamique...")
            
            # Extraire les métriques
            logger.info(f"🔍 [DEBUG] Starting metrics extraction...")
            metrics = await self.metrics_extractor.extract_metrics(
                self.current_page,
                self.playwright_manager,
                self.session_manager,
                shop_url=domain
            )
            logger.info(f"🔍 [DEBUG] Metrics extraction result: {metrics}")
            
            # ===== DEBUG FID DANS L'URL =====
            logger.info("🔍 [DEBUG] ===== FID DEBUG ANALYSIS =====")
            if hasattr(metrics, 'url') and metrics.url:
                logger.info(f"📍 [DEBUG] Final metrics URL used: {metrics.url}")
                if 'fid=' in metrics.url:
                    import re
                    fid_match = re.search(r'fid=([^&]+)', metrics.url)
                    if fid_match:
                        used_fid = fid_match.group(1)
                        logger.info(f"🔢 [DEBUG] FID used in URL: {used_fid}")
                        logger.warning(f"⚠️ [DEBUG] FID {used_fid} might be invalid for domain {domain}")
                        logger.warning(f"⚠️ [DEBUG] This could explain why no metrics are found")
                    else:
                        logger.warning("⚠️ [DEBUG] No FID found in metrics URL")
                else:
                    logger.warning("⚠️ [DEBUG] No FID parameter in metrics URL")
            else:
                logger.warning("⚠️ [DEBUG] No metrics URL available for FID analysis")
            logger.info("✅ [DEBUG] FID debug analysis completed")
            # ===== FIN DEBUG FID =====
            
            # ===== DEBUG DÉTAILLÉ DE LA PAGE =====
            logger.info("🔍 [DEBUG] ===== DETAILED PAGE ANALYSIS =====")
            
            # Analyse du contenu de la page après extraction
            try:
                page_title = await self.current_page.title()
                page_url = self.current_page.url
                logger.info(f"📄 [DEBUG] Page title after extraction: {page_title}")
                logger.info(f"📍 [DEBUG] Page URL after extraction: {page_url}")
                
                # Contenu visible de la page
                visible_text = await self.current_page.evaluate("document.body.innerText")
                logger.info(f"📄 [DEBUG] Visible text length: {len(visible_text)} characters")
                logger.info(f"📄 [DEBUG] Visible text preview (first 500 chars):")
                logger.info("=" * 80)
                logger.info(visible_text[:500])
                logger.info("=" * 80)
                
                # Vérification de session expirée
                session_expired_indicators = [
                    "Session expired", "session expired", 
                    "access again from Dashboard", "Dashboard",
                    "Please log in", "Login required",
                    "Authentication required"
                ]
                
                session_expired = any(indicator.lower() in visible_text.lower() for indicator in session_expired_indicators)
                
                if session_expired:
                    logger.warning("🚫 [DEBUG] SESSION EXPIRED DETECTED in visible text!")
                    logger.warning("🚫 [DEBUG] This explains why metrics are not extracted")
                    logger.warning(f"🚫 [DEBUG] Visible text contains session expired indicators")
                elif len(visible_text) < 1000:  # Page très courte = probablement session expirée
                    logger.warning("🚫 [DEBUG] SUSPECTED SESSION EXPIRED - Page content very short")
                    logger.warning(f"🚫 [DEBUG] Page content length: {len(visible_text)} characters")
                    session_expired = True
                
                # Recherche de mots-clés liés aux métriques
                metric_keywords = ["visits", "traffic", "organic", "paid", "search", "conversion", "duration", "bounce", "rate", "entrances", "purchases"]
                logger.info("🔍 [DEBUG] Searching for metric keywords in visible text:")
                found_keywords = []
                for keyword in metric_keywords:
                    if keyword.lower() in visible_text.lower():
                        found_keywords.append(keyword)
                        logger.info(f"✅ [DEBUG] Found keyword: '{keyword}'")
                    else:
                        logger.info(f"❌ [DEBUG] Missing keyword: '{keyword}'")
                
                logger.info(f"📊 [DEBUG] Total metric keywords found: {len(found_keywords)}/{len(metric_keywords)}")
                
                # Analyse des éléments DOM
                logger.info("🔍 [DEBUG] ===== DOM ELEMENT ANALYSIS =====")
                
                # Vérification des tables
                tables = await self.current_page.query_selector_all("table")
                logger.info(f"📊 [DEBUG] Found {len(tables)} tables on page")
                
                # Vérification des sélecteurs spécifiques
                selectors_to_check = [
                    '[data-ui-name="Flex"][role="gridcell"]',
                    '[name="entrances"]',
                    '[name="entrancesSearchOrganic"]',
                    '[name="entrancesSearchPaid"]',
                    '[name="purchasesPerVisit"]',
                    '[name="avgVisitDuration"]',
                    '[name="bouncesPerVisit"]',
                    'input[name*="entrance"]',
                    'input[name*="visit"]',
                    'input[name*="bounce"]',
                    '.metric-value',
                    '.data-value'
                ]
                
                logger.info("🔍 [DEBUG] Checking specific selectors:")
                total_elements_found = 0
                for selector in selectors_to_check:
                    try:
                        elements = await self.current_page.query_selector_all(selector)
                        if len(elements) > 0:
                            total_elements_found += len(elements)
                            logger.info(f"✅ [DEBUG] Selector '{selector}': {len(elements)} elements found")
                            # Afficher le contenu des premiers éléments
                            for i, element in enumerate(elements[:2]):
                                try:
                                    text = await element.inner_text()
                                    logger.info(f"   📝 [DEBUG] Element {i+1}: '{text[:100]}...'")
                                except:
                                    logger.info(f"   📝 [DEBUG] Element {i+1}: [Could not get text]")
                        else:
                            logger.info(f"❌ [DEBUG] Selector '{selector}': 0 elements found")
                    except Exception as e:
                        logger.warning(f"⚠️ [DEBUG] Error checking selector '{selector}': {e}")
                
                logger.info(f"📊 [DEBUG] Total metric elements found: {total_elements_found}")
                
                # Vérification des indicateurs de chargement
                loading_indicators = ["loading", "Loading", "LOADING", "spinner", "Spinner", "wait", "Wait", "Just a moment", "please wait"]
                logger.info("🔍 [DEBUG] Checking for loading indicators:")
                loading_found = False
                for indicator in loading_indicators:
                    if indicator in visible_text:
                        loading_found = True
                        logger.warning(f"⏳ [DEBUG] Found loading indicator: '{indicator}'")
                
                if not loading_found:
                    logger.info("✅ [DEBUG] No loading indicators found - page appears to be loaded")
                
                # Analyse finale
                logger.info("🔍 [DEBUG] ===== FINAL ANALYSIS =====")
                if len(tables) == 0:
                    logger.warning("⚠️ [DEBUG] NO TABLES FOUND - This might be why metrics are not extracted")
                if len(found_keywords) == 0:
                    logger.warning("⚠️ [DEBUG] NO METRIC KEYWORDS FOUND - Page might not be loaded correctly")
                if total_elements_found == 0:
                    logger.warning("⚠️ [DEBUG] NO METRIC ELEMENTS FOUND - Selectors might be incorrect")
                
                logger.info("✅ [DEBUG] Detailed page analysis completed")
                
                # ===== CAPTURE HTML COMPLET POUR DEBUG =====
                try:
                    logger.info("🔍 [DEBUG] ===== CAPTURING FULL HTML FOR DEBUG =====")
                    
                    # Capturer le HTML complet de la page
                    full_html = await self.current_page.content()
                    logger.info(f"📄 [DEBUG] Full HTML length: {len(full_html)} characters")
                    
                    # Sauvegarder le HTML pour analyse
                    import os
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    html_filename = f"debug_market_overview_{domain.replace('.', '_')}_{timestamp}.html"
                    html_path = f"/home/ubuntu/projects/shopshopshops/test/{html_filename}"
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(full_html)
                    
                    logger.info(f"💾 [DEBUG] Full HTML saved to: {html_path}")
                    
                    # Analyser les éléments React potentiels
                    react_elements = await self.current_page.query_selector_all("[data-reactroot], [id*='react'], [class*='react'], [data-*='react']")
                    logger.info(f"⚛️ [DEBUG] Found {len(react_elements)} React-related elements")
                    
                    # Analyser les scripts chargés
                    scripts = await self.current_page.query_selector_all("script")
                    logger.info(f"📜 [DEBUG] Found {len(scripts)} script elements")
                    
                    # Vérifier les erreurs JavaScript
                    js_errors = await self.current_page.evaluate("""
                        () => {
                            const errors = [];
                            window.addEventListener('error', (e) => {
                                errors.push({
                                    message: e.message,
                                    filename: e.filename,
                                    lineno: e.lineno,
                                    colno: e.colno
                                });
                            });
                            return errors;
                        }
                    """)
                    logger.info(f"🚨 [DEBUG] JavaScript errors detected: {len(js_errors)}")
                    
                    # Analyser les requêtes réseau
                    network_requests = await self.current_page.evaluate("""
                        () => {
                            return performance.getEntriesByType('navigation').concat(
                                performance.getEntriesByType('resource')
                            ).map(entry => ({
                                name: entry.name,
                                type: entry.initiatorType,
                                duration: entry.duration,
                                transferSize: entry.transferSize
                            }));
                        }
                    """)
                    logger.info(f"🌐 [DEBUG] Network requests: {len(network_requests)}")
                    
                    # Vérifier si la page contient des données JSON
                    json_data = await self.current_page.evaluate("""
                        () => {
                            const scripts = Array.from(document.querySelectorAll('script'));
                            const jsonData = [];
                            scripts.forEach(script => {
                                try {
                                    const content = script.textContent;
                                    if (content && (content.includes('"data"') || content.includes('"metrics"') || content.includes('"traffic"'))) {
                                        jsonData.push(content.substring(0, 200) + '...');
                                    }
                                } catch (e) {
                                    // Ignore parsing errors
                                }
                            });
                            return jsonData;
                        }
                    """)
                    logger.info(f"📊 [DEBUG] Found {len(json_data)} scripts with potential data")
                    
                    logger.info("✅ [DEBUG] Full HTML capture and analysis completed")
                    
                except Exception as e:
                    logger.error(f"❌ [DEBUG] Error during HTML capture: {e}")
                
                # ===== FIN CAPTURE HTML COMPLET =====
                
                # ===== GESTION SESSION EXPIRÉE =====
                if 'session_expired' in locals() and session_expired:
                    logger.warning("🚫 [SESSION EXPIRED] Détection d'une session expirée - déclenchement du fallback")
                    logger.warning("🚫 [SESSION EXPIRED] Les métriques ne peuvent pas être extraites avec une session expirée")
                    
                    # Marquer la session comme expirée pour le prochain cycle
                    self.is_authenticated = False
                    logger.info("🔄 [SESSION EXPIRED] Authentication status reset to False for next attempt")
                    
                    # Retourner None pour forcer un retry avec authentification
                    return None
                
            except Exception as e:
                logger.error(f"❌ [DEBUG] Error during detailed page analysis: {e}")
            
            # ===== FIN DEBUG DÉTAILLÉ =====
            
            if metrics and metrics.success:
                logger.info(f"✅ [DEBUG] Metrics extracted successfully for {domain}")
                logger.info(f"✅ [DEBUG] Metrics data: {metrics.to_dict()}")
                
                # Formater les métriques
                logger.info(f"📝 [DEBUG] Formatting metrics...")
                formatted_metrics = format_metrics(metrics.to_dict())
                formatted_metrics['domain'] = domain
                logger.info(f"📝 [DEBUG] Formatted metrics: {formatted_metrics}")
                
                return formatted_metrics
            else:
                logger.warning(f"⚠️ [DEBUG] No metrics extracted for {domain}")
                logger.warning(f"⚠️ [DEBUG] Metrics success: {metrics.success if metrics else 'None'}")
                logger.warning(f"⚠️ [DEBUG] Metrics error: {metrics.error_message if metrics else 'None'}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [DEBUG] Error during scraping of {domain}: {e}")
            logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] Exception args: {e.args}")
            return None
    
    async def scrape_multiple_shops(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Scrape les métriques pour plusieurs domaines."""
        results = []
        
        logger.info(f"🚀 [DEBUG] Starting scraping of {len(domains)} domains")
        logger.info(f"🚀 [DEBUG] Domains list: {domains}")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📊 [DEBUG] [{i}/{len(domains)}] Scraping: {domain}")
            logger.info(f"📊 [DEBUG] Progress: {i}/{len(domains)} ({i/len(domains)*100:.1f}%)")
            
            metrics = await self.scrape_shop_metrics(domain)
            logger.info(f"📊 [DEBUG] Metrics result for {domain}: {metrics is not None}")
            
            if metrics:
                results.append(metrics)
                logger.info(f"✅ [DEBUG] Added metrics for {domain} to results")
            else:
                logger.warning(f"⚠️ [DEBUG] No metrics for {domain}")
            
            # Délai entre les requêtes
            if i < len(domains):
                logger.info(f"⏳ [DEBUG] Waiting 2 seconds before next domain...")
                await asyncio.sleep(2)
                logger.info(f"⏳ [DEBUG] Wait completed, continuing...")
        
        logger.info(f"✅ [DEBUG] Scraping completed: {len(results)}/{len(domains)} domains processed")
        logger.info(f"✅ [DEBUG] Results summary: {[r.get('domain', 'Unknown') for r in results]}")
        return results
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Retourne le statut du serveur actuel."""
        return self.server_manager.get_server_status_summary()
    
    async def cleanup(self) -> None:
        """Nettoie les ressources du scraper."""
        try:
            logger.info("🧹 Nettoyage des ressources...")
            
            if self.playwright_manager:
                await self.playwright_manager.cleanup()
            
            # Reset du server manager
            reset_server_manager()
            
            logger.info("✅ Nettoyage terminé")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")

async def main():
    """Fonction principale du scraper."""
    print("🚀 SCRAPER NOXTOOLS ALPHA - DÉMARRAGE")
    print("=" * 60)
    
    # Configuration
    config = ScraperConfig()
    
    # Initialiser le scraper
    scraper = NoxtoolsScraper(config)
    
    try:
        # 1. Initialisation
        if not await scraper.initialize():
            logger.error("❌ Échec de l'initialisation")
            return
        
        # 2. Authentification
        if not await scraper.authenticate():
            logger.error("❌ Échec de l'authentification")
            return
        
        # 3. Récupérer les boutiques éligibles depuis la BDD
        from services.shop_repository import ShopRepository
        
        shop_repo = ShopRepository()
        eligible_shops = shop_repo.get_shops_to_scrape(limit=10)
        
        if not eligible_shops:
            logger.info("📊 Zéro boutiques éligibles pour le scraping Noxtools")
            print("📊 Zéro boutiques éligibles pour le scraping Noxtools")
            return
        
        logger.info(f"🧪 {len(eligible_shops)} boutiques éligibles trouvées")
        print(f"🧪 {len(eligible_shops)} boutiques éligibles trouvées")
        
        # Extraire les domaines des boutiques éligibles
        domains = []
        for shop in eligible_shops:
            if shop.shop_url:
                from urllib.parse import urlparse
                parsed_url = urlparse(shop.shop_url)
                domain = parsed_url.netloc
                if domain:
                    domains.append(domain)
        
        if not domains:
            logger.info("📊 Aucun domaine valide trouvé dans les boutiques éligibles")
            print("📊 Aucun domaine valide trouvé dans les boutiques éligibles")
            return
        
        logger.info(f"🧪 Test avec {len(domains)} domaines éligibles")
        print(f"🧪 Test avec {len(domains)} domaines éligibles")
        
        results = await scraper.scrape_multiple_shops(domains)
        
        # 4. Affichage des résultats
        print(f"\n📊 RÉSULTATS DU SCRAPING")
        print("-" * 40)
        for result in results:
            print(f"✅ {result.get('domain', 'N/A')}: {result.get('visits', 'N/A')} visites")
        
        # 5. Statut du serveur
        server_status = await scraper.get_server_status()
        print(f"\n🖥️ SERVEUR ACTUEL: {server_status['current_server']}")
        
    except Exception as e:
        logger.error(f"❌ Erreur dans le main: {e}")
    
    finally:
        # Nettoyage
        await scraper.cleanup()
        print("\n🎉 Scraper terminé")

if __name__ == "__main__":
    # Lancer le scraper
    asyncio.run(main())
