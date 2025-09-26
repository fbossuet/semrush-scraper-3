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
    db_path: str = "../trendtrack-scraper-final/data/trendtrack.db"
    
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
