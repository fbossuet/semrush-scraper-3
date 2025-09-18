#!/usr/bin/env python3
"""
Configuration pour le système de workers parallèles
Paramètres centralisés pour faciliter la maintenance
"""

from pathlib import Path
from typing import Dict, Any

class ParallelConfig:
    """Configuration du système de workers parallèles"""
    
    # Nombre de workers par défaut
    DEFAULT_NUM_WORKERS = 2
    
    # Répertoires
    LOGS_DIR = Path("logs")
    LOCKS_DIR = Path("locks")
    RESULTS_DIR = Path("results")
    SESSION_DIR = Path("session-profiles")
    
    # Fichiers de statut
    STATUS_FILE = Path("parallel_workers_status.json")
    DISTRIBUTION_FILE = Path("shop_distribution.json")
    PID_FILE = Path("parallel_workers.pid")
    
    # Timeouts et délais
    BROWSER_TIMEOUT = 30000  # 30 secondes
    NAVIGATION_DELAY = 1     # 1 seconde
    WORKER_STARTUP_DELAY = 2 # 2 secondes
    MONITORING_INTERVAL = 5  # 5 secondes
    # Échelonnage quasi simultané (micro-jitter)
    STAGGER_BASE_S = 0.0
    STAGGER_STEP_S = 0.2
    STAGGER_JITTER_S = 0.1
    STAGGER_MAX_S = 1.0
    
    # Configuration du navigateur
    BROWSER_ARGS = [
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--start-maximized',
        '--disable-infobars',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-default-apps',
        '--disable-sync',
        '--disable-translate',
        '--hide-scrollbars',
        '--mute-audio',
        '--no-default-browser-check',
        '--no-experiments',
        '--disable-hang-monitor',
        '--disable-prompt-on-repost',
        '--disable-client-side-phishing-detection',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--memory-pressure-off',
        '--max_old_space_size=4096',
        '--disable-dev-shm-usage',
        '--disable-application-cache',
        '--disable-offline-load-stale-cache',
        '--disk-cache-size=0',
        '--media-cache-size=0'
    ]
    
    # Headers HTTP
    HTTP_HEADERS = {
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }
    
    # URLs
    MYTOOLSPLAN_LOGIN_URL = "https://app.mytoolsplan.com/login"
    MYTOOLSPLAN_BASE_URL = "https://sam.mytoolsplan.xyz"
    MYTOOLSPLAN_DOMAIN_OVERVIEW_URL = "https://sam.mytoolsplan.xyz/analytics/overview/"
    MYTOOLSPLAN_ORGANIC_SEARCH_URL = "https://sam.mytoolsplan.xyz/analytics/organic/overview/"
    MYTOOLSPLAN_TRAFFIC_ANALYSIS_URL = "https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/"
    
    # Sélecteurs CSS
    SELECTORS = {
        'organic_search_traffic': 'a[data-path="overview.summary.click_organic_search_traffic"] span[data-ui-name="Link.Text"]',
        'avg_visit_duration': 'a[data-path="overview.engagement_metrics.visit_duration"] span[data-ui-name="Link.Text"]',
        'bounce_rate': 'a[data-path="overview.engagement_metrics.bounce_rate"] span[data-ui-name="Link.Text"]',
        'branded_traffic': 'div[data-at="summary-branded-traffic"] > div > div > span[data-at="summary-value"][data-ui-name="Text"]',
        'visits': 'div[name="visits"] span[data-ui-name="Text"]',
        'purchase_conversion': 'div[name="conversion"] span[data-ui-name="Text"]'
    }
    
    # Messages de statut
    STATUS_MESSAGES = {
        'starting': '🟡 Démarrage',
        'running': '🟢 En cours',
        'stopped': '🔴 Arrêté',
        'finished': '✅ Terminé',
        'error': '❌ Erreur'
    }
    
    # Limites et seuils
    MAX_WORKERS = 6
    MIN_WORKERS = 1
    MAX_SHOP_DIFFERENCE = 1  # Différence maximale entre workers
    MAX_RETRY_ATTEMPTS = 3
    MAX_MEMORY_MB = 2048  # 2GB par worker
    
    # === SYSTÈME DE DISCRÉTION & THROTTLING ===
    
    # Throttling API - Délais entre requêtes
    API_THROTTLE_BASE_MS = 300      # Délai de base (ms)
    API_THROTTLE_MAX_MS = 800       # Délai maximum (ms)
    API_THROTTLE_JITTER_MS = 100    # Jitter aléatoire (ms)
    
    # Backoff adaptatif sur erreurs
    API_BACKOFF_BASE_S = 1.0        # Délai initial (s)
    API_BACKOFF_MULTIPLIER = 2.0    # Multiplicateur
    API_BACKOFF_MAX_S = 10.0        # Délai maximum (s)
    API_BACKOFF_MAX_ATTEMPTS = 5    # Tentatives max
    
    # Token bucket - Rate limiting
    API_RATE_LIMIT_PER_MINUTE = 60  # Requêtes par minute
    API_RATE_LIMIT_BURST = 10       # Burst autorisé
    
    # User-Agent rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]
    
    # Headers randomisés
    ACCEPT_LANGUAGES = [
        'en-US,en;q=0.9,fr;q=0.8',
        'en-US,en;q=0.9',
        'fr-FR,fr;q=0.9,en;q=0.8',
        'en-GB,en;q=0.9,en-US;q=0.8'
    ]
    
    # Timing patterns humains
    HUMAN_PAUSE_BETWEEN_SESSIONS_S = 2.0    # Pause entre sessions
    HUMAN_PAUSE_JITTER_S = 1.0              # Jitter pause
    HUMAN_SCROLL_DELAY_MS = 500             # Délai scroll
    HUMAN_TYPING_DELAY_MS = 100             # Délai frappe
    
    # Limites de discrétion
    MAX_CONCURRENT_REQUESTS = 3             # Requêtes simultanées max
    SESSION_COOLDOWN_S = 30                 # Cooldown entre sessions
    DAILY_REQUEST_LIMIT = 1000              # Limite quotidienne
    
    @classmethod
    def create_directories(cls):
        """Crée les répertoires nécessaires"""
        for directory in [cls.LOGS_DIR, cls.LOCKS_DIR, cls.RESULTS_DIR, cls.SESSION_DIR]:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def get_worker_session_dir(cls, worker_id: int) -> Path:
        """Retourne le répertoire de session d'un worker"""
        return cls.SESSION_DIR / f"worker-{worker_id}"
    
    @classmethod
    def get_worker_lock_file(cls, worker_id: int) -> Path:
        """Retourne le fichier de lock d'un worker"""
        return cls.LOCKS_DIR / f"scraping_lock_worker_{worker_id}.lock"
    
    @classmethod
    def get_worker_log_file(cls, worker_id: int) -> Path:
        """Retourne le fichier de log d'un worker"""
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()
        return cls.LOGS_DIR / f"worker_{worker_id}_{timestamp}.log"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valide la configuration"""
        try:
            # Vérifier les répertoires
            cls.create_directories()
            
            # Vérifier les limites
            if cls.DEFAULT_NUM_WORKERS < cls.MIN_WORKERS or cls.DEFAULT_NUM_WORKERS > cls.MAX_WORKERS:
                raise ValueError(f"Nombre de workers invalide: {cls.DEFAULT_NUM_WORKERS}")
            
            # Vérifier les timeouts
            if cls.BROWSER_TIMEOUT <= 0:
                raise ValueError(f"Timeout navigateur invalide: {cls.BROWSER_TIMEOUT}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur de configuration: {e}")
            return False
    
    @classmethod
    def print_config(cls):
        """Affiche la configuration actuelle"""
        print("🔧 CONFIGURATION WORKERS PARALLÈLES")
        print("=" * 50)
        print(f"👷 Nombre de workers: {cls.DEFAULT_NUM_WORKERS}")
        print(f"⏱️ Timeout navigateur: {cls.BROWSER_TIMEOUT}ms")
        print(f"📁 Répertoire logs: {cls.LOGS_DIR}")
        print(f"🔒 Répertoire locks: {cls.LOCKS_DIR}")
        print(f"📊 Répertoire résultats: {cls.RESULTS_DIR}")
        print(f"🔄 Intervalle monitoring: {cls.MONITORING_INTERVAL}s")
        print("=" * 50)

# Instance globale de configuration
config = ParallelConfig()

# Validation automatique au chargement
if not config.validate_config():
    raise RuntimeError("Configuration invalide")
