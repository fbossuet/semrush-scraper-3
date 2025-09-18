#!/usr/bin/env python3
"""
Module de gestion des navigateurs pour TrendTrack
Fournit les navigateurs stealth et les systèmes d'anti-détection
"""

from .legacy_browser import StealthBrowser, stealth_browser, create_stealth_browser, get_stealth_page
from utils.anti_detection import (
    AntiDetectionSystem, 
    DelayType, 
    DelayConfig,
    anti_detection,
    random_delay,
    human_typing_delay,
    human_reading_delay,
    human_click_delay
)

# Exports publics
__all__ = [
    # Classes principales
    'StealthBrowser',
    'AntiDetectionSystem',
    'DelayType',
    'DelayConfig',
    
    # Instances globales
    'stealth_browser',
    'anti_detection',
    
    # Fonctions utilitaires
    'create_stealth_browser',
    'get_stealth_page',
    'random_delay',
    'human_typing_delay',
    'human_reading_delay',
    'human_click_delay'
]

# Configuration par défaut
DEFAULT_STEALTH_LEVEL = "medium"
DEFAULT_HEADLESS = True
DEFAULT_TIMEOUT = 30000

def get_browser_config(stealth_level: str = DEFAULT_STEALTH_LEVEL, headless: bool = DEFAULT_HEADLESS) -> dict:
    """
    Obtenir la configuration du navigateur
    
    Args:
        stealth_level: Niveau de furtivité (low, medium, high)
        headless: Mode headless
        
    Returns:
        Dict contenant la configuration
    """
    return {
        'stealth_level': stealth_level,
        'headless': headless,
        'timeout': DEFAULT_TIMEOUT
    }


