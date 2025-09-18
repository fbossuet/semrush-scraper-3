#!/usr/bin/env python3
"""
Configuration pour l'authentification TrendTrack
"""

import os
from typing import Dict, Any

# Configuration par défaut
DEFAULT_CONFIG = {
    # URLs
    'base_url': 'https://app.trendtrack.io',
    'login_url': 'https://app.trendtrack.io/fr/login',
    'dashboard_url': 'https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st',
    
    # Authentification
    'auth_method': 'api',  # 'api' ou 'dom'
    'session_timeout_hours': 24,
    'max_retry_attempts': 3,
    'retry_delay_seconds': 5,
    
    # Headers
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    
    # Playwright (pour DOM auth)
    'headless': True,
    'browser_args': ['--no-sandbox', '--disable-dev-shm-usage'],
    
    # Logging
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

def get_config() -> Dict[str, Any]:
    """
    Obtenir la configuration d'authentification
    
    Returns:
        Dict contenant la configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override avec les variables d'environnement si disponibles
    env_overrides = {
        'base_url': os.getenv('TRENDTRACK_BASE_URL'),
        'auth_method': os.getenv('TRENDTRACK_AUTH_METHOD'),
        'session_timeout_hours': os.getenv('TRENDTRACK_SESSION_TIMEOUT_HOURS'),
        'headless': os.getenv('TRENDTRACK_HEADLESS'),
        'log_level': os.getenv('TRENDTRACK_LOG_LEVEL'),
    }
    
    for key, value in env_overrides.items():
        if value is not None:
            # Conversion de type pour les valeurs non-string
            if key in ['session_timeout_hours']:
                config[key] = int(value)
            elif key in ['headless']:
                config[key] = value.lower() in ('true', '1', 'yes', 'on')
            else:
                config[key] = value
    
    return config

def get_credentials() -> Dict[str, str]:
    """
    Obtenir les credentials d'authentification
    
    Returns:
        Dict contenant email et password
    """
    return {
        'email': os.getenv('TRENDTRACK_EMAIL', ''),
        'password': os.getenv('TRENDTRACK_PASSWORD', '')
    }

def is_configured() -> bool:
    """
    Vérifier si la configuration est complète
    
    Returns:
        bool: True si configuré
    """
    credentials = get_credentials()
    return bool(credentials['email'] and credentials['password'])

# Configuration globale
config = get_config()
credentials = get_credentials()
configured = is_configured()

# Exports
__all__ = [
    'DEFAULT_CONFIG',
    'get_config',
    'get_credentials', 
    'is_configured',
    'config',
    'credentials',
    'configured'
]


