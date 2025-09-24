#!/usr/bin/env python3
"""
Gestionnaire d'URLs dynamiques pour les différentes méthodes d'authentification
Adapte automatiquement les URLs selon la méthode d'authentification active
Créé le 23 septembre 2025
"""

import logging
from config import get_auth_method

logger = logging.getLogger(__name__)

class URLManager:
    """
    Gestionnaire d'URLs dynamiques pour les différentes méthodes d'authentification.
    
    Méthodes supportées :
    - mytoolsplan : URLs classiques (app.mytoolsplan.com, sam.mytoolsplan.xyz)
    - noxtools : URLs Noxtools (semrush1.semrush.pw)
    """
    
    def __init__(self):
        self.auth_method = get_auth_method()
        logger.info(f"🔗 URLManager initialisé avec méthode: {self.auth_method}")
    
    def get_base_url(self) -> str:
        """Retourne l'URL de base selon la méthode d'authentification"""
        if self.auth_method == "noxtools":
            return "https://semrush1.semrush.pw"
        else:  # mytoolsplan
            return "https://sam.mytoolsplan.xyz"
    
    def get_analytics_url(self) -> str:
        """Retourne l'URL de la page analytics"""
        if self.auth_method == "noxtools":
            return "https://semrush1.semrush.pw/analytics/overview/?searchType=domain"
        else:  # mytoolsplan
            return "https://sam.mytoolsplan.xyz/analytics/"
    
    def get_organic_overview_url(self, domain: str, date_range: str) -> str:
        """Retourne l'URL pour l'overview organique"""
        if self.auth_method == "noxtools":
            # Pour Noxtools, utiliser l'URL de base avec les paramètres
            return f"https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q={domain}&date={date_range}"
        else:  # mytoolsplan
            return f"https://app.mytoolsplan.com/analytics/organic/overview/?db=us&q={domain}&searchType=domain&date={date_range}"
    
    def get_traffic_overview_url(self, domain: str, date_range: str) -> str:
        """Retourne l'URL pour l'overview du trafic"""
        if self.auth_method == "noxtools":
            return f"https://semrush1.semrush.pw/analytics/traffic/overview/?searchType=domain&q={domain}&date={date_range}"
        else:  # mytoolsplan
            return f"https://app.mytoolsplan.com/analytics/traffic/traffic-overview/?db=us&q={domain}&searchType=domain&date={date_range}"
    
    def get_engagement_url(self) -> str:
        """Retourne l'URL pour les métriques d'engagement"""
        if self.auth_method == "noxtools":
            return "https://semrush1.semrush.pw/analytics/overview/?searchType=domain"
        else:  # mytoolsplan
            return "https://sam.mytoolsplan.xyz/analytics/"
    
    def get_conversion_url(self, domain: str, date_range: str) -> str:
        """Retourne l'URL pour les métriques de conversion"""
        if self.auth_method == "noxtools":
            return f"https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q={domain}&date={date_range}"
        else:  # mytoolsplan
            return f"https://app.mytoolsplan.com/analytics/traffic/traffic-overview/?db=us&q={domain}&searchType=domain&date={date_range}"
    
    def get_folders_api_url(self) -> str:
        """Retourne l'URL pour l'API des dossiers/projets"""
        if self.auth_method == "noxtools":
            return "/apis/v4-raw/folders/api/v0/folders/selector-list?limit=2000&offset=0"
        else:  # mytoolsplan
            return "/apis/v4-raw/folders/api/v0/folders/selector-list?limit=2000&offset=0"
    
    def get_organic_summary_api_url(self) -> str:
        """Retourne l'URL pour l'API organic.Summary"""
        if self.auth_method == "noxtools":
            return "/apis/v4-raw/organic/api/v0/organic/summary"
        else:  # mytoolsplan
            return "/apis/v4-raw/organic/api/v0/organic/summary"
    
    def get_engagement_api_url(self) -> str:
        """Retourne l'URL pour l'API d'engagement"""
        if self.auth_method == "noxtools":
            return "/apis/v4-raw/organic/api/v0/organic/overview-trend"
        else:  # mytoolsplan
            return "/apis/v4-raw/organic/api/v0/organic/overview-trend"
    
    def should_navigate_to_analytics(self) -> bool:
        """Détermine si on doit naviguer vers la page analytics avant les appels API"""
        if self.auth_method == "noxtools":
            return False  # Noxtools est déjà sur la bonne page
        else:  # mytoolsplan
            return True  # MyToolsPlan nécessite une navigation
    
    def get_navigation_target(self) -> str:
        """Retourne l'URL vers laquelle naviguer avant les appels API"""
        if self.auth_method == "noxtools":
            return None  # Pas de navigation nécessaire
        else:  # mytoolsplan
            return "https://sam.mytoolsplan.xyz/analytics/"
    
    def is_noxtools(self) -> bool:
        """Vérifie si la méthode active est Noxtools"""
        return self.auth_method == "noxtools"
    
    def is_mytoolsplan(self) -> bool:
        """Vérifie si la méthode active est MyToolsPlan"""
        return self.auth_method == "mytoolsplan"
    
    def get_auth_method(self) -> str:
        """Retourne la méthode d'authentification active"""
        return self.auth_method

# Instance globale
url_manager = URLManager()
