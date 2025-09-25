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
            if not self.is_authenticated:
                logger.error("❌ Non authentifié")
                return None
            
            logger.info(f"📊 Scraping des métriques pour: {domain}")
            
            # Le MetricsExtractor gère maintenant la navigation avec FID dynamique
            logger.info(f"🌐 Navigation vers métriques avec FID dynamique...")
            
            # Extraire les métriques (le MetricsExtractor gère maintenant la navigation)
            metrics = await self.metrics_extractor.extract_metrics(
                self.current_page,
                self.playwright_manager,
                self.session_manager,
                f"https://{domain}"  # URL du domaine pour l'extraction CPC
            )
            
            if metrics and metrics.success:
                logger.info(f"✅ Métriques extraites pour {domain}")
                
                # Formater les métriques
                formatted_metrics = format_metrics(metrics.to_dict())
                formatted_metrics['domain'] = domain
                
                return formatted_metrics
            else:
                logger.warning(f"⚠️ Aucune métrique extraite pour {domain}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping de {domain}: {e}")
            return None
    
    async def scrape_multiple_shops(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Scrape les métriques pour plusieurs domaines."""
        results = []
        
        logger.info(f"🚀 Début du scraping de {len(domains)} domaines")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📊 [{i}/{len(domains)}] Scraping: {domain}")
            
            metrics = await self.scrape_shop_metrics(domain)
            if metrics:
                results.append(metrics)
            
            # Délai entre les requêtes
            if i < len(domains):
                await asyncio.sleep(2)
        
        logger.info(f"✅ Scraping terminé: {len(results)}/{len(domains)} domaines traités")
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
        
        # 3. Test avec un domaine
        test_domains = ["example.com", "google.com"]
        logger.info(f"🧪 Test avec {len(test_domains)} domaines")
        
        results = await scraper.scrape_multiple_shops(test_domains)
        
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
