import os
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv('config.env')

# NordVPN Configuration
NORDVPN_USERNAME = os.getenv('NORDVPN_USERNAME')
NORDVPN_PASSWORD = os.getenv('NORDVPN_PASSWORD')

# Authentication Method Configuration
AUTH_METHOD = os.getenv('AUTH_METHOD', 'mytoolsplan')

# MyToolsPlan Configuration
MYTOOLSPLAN_USERNAME = os.getenv('MYTOOLSPLAN_USERNAME')
MYTOOLSPLAN_PASSWORD = os.getenv('MYTOOLSPLAN_PASSWORD')
MYTOOLSPLAN_LOGIN_URL = os.getenv('MYTOOLSPLAN_LOGIN_URL', 'https://sam.mytoolsplan.xyz/login')

# Noxtools Configuration (nouvelle méthode)
NOXTOOLS_USERNAME = os.getenv('NOXTOOLS_USERNAME')
NOXTOOLS_PASSWORD = os.getenv('NOXTOOLS_PASSWORD')
NOXTOOLS_LOGIN_URL = os.getenv('NOXTOOLS_LOGIN_URL', 'https://noxtools.com/secure/login')
NOXTOOLS_SEMRUSH_PAGE_URL = os.getenv('NOXTOOLS_SEMRUSH_PAGE_URL', 'https://noxtools.com/secure/page/semrush')

# Browser Configuration
BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '60000'))
PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', '90000'))
NAVIGATION_TIMEOUT = int(os.getenv('NAVIGATION_TIMEOUT', '120000'))

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000/api')
API_KEY = os.getenv('API_KEY', 'your-api-key-here')

class Config:
    """Classe de configuration pour le scraper"""
    
    def __init__(self):
        self.auth_method = AUTH_METHOD
        self.nordvpn_username = NORDVPN_USERNAME
        self.nordvpn_password = NORDVPN_PASSWORD
        self.mytoolsplan_username = MYTOOLSPLAN_USERNAME
        self.mytoolsplan_password = MYTOOLSPLAN_PASSWORD
        self.mytoolsplan_login_url = MYTOOLSPLAN_LOGIN_URL
        self.noxtools_username = NOXTOOLS_USERNAME
        self.noxtools_password = NOXTOOLS_PASSWORD
        self.noxtools_login_url = NOXTOOLS_LOGIN_URL
        self.noxtools_semrush_page_url = NOXTOOLS_SEMRUSH_PAGE_URL
        self.browser_timeout = BROWSER_TIMEOUT
        self.page_load_timeout = PAGE_LOAD_TIMEOUT
        self.navigation_timeout = NAVIGATION_TIMEOUT
        self.api_base_url = API_BASE_URL
        self.api_key = API_KEY
    
    def validate_credentials(self):
        """Valide que les credentials essentiels sont configurés"""
        if self.auth_method == 'mytoolsplan':
            if not self.mytoolsplan_username or not self.mytoolsplan_password:
                raise ValueError("MyToolsPlan credentials manquants dans config.env")
        elif self.auth_method == 'noxtools':
            if not self.noxtools_username or not self.noxtools_password:
                raise ValueError("Noxtools credentials manquants dans config.env")
        else:
            raise ValueError(f"Méthode d'authentification invalide: {self.auth_method}")
        
        # NordVPN est optionnel
        if not self.nordvpn_username or not self.nordvpn_password:
            print("⚠️ NordVPN credentials non configurés (optionnel)")
    
    def print_config_summary(self):
        """Affiche un résumé de la configuration"""
        print("📋 Configuration du scraper:")
        print(f"  • Méthode d'auth: {self.auth_method}")
        print(f"  • MyToolsPlan: {'✅' if self.mytoolsplan_username else '❌'}")
        print(f"  • Noxtools: {'✅' if self.noxtools_username else '❌'}")
        print(f"  • NordVPN: {'✅' if self.nordvpn_username else '❌'}")
        print(f"  • API: {'✅' if self.api_base_url != 'http://localhost:3000/api' else '❌'}")
        print(f"  • Timeouts: {self.browser_timeout}ms/{self.page_load_timeout}ms/{self.navigation_timeout}ms")

def get_nordvpn_credentials():
    """Get NordVPN credentials from environment variables"""
    return NORDVPN_USERNAME, NORDVPN_PASSWORD

def get_mytoolsplan_credentials():
    """Get MyToolsPlan credentials from environment variables"""
    return MYTOOLSPLAN_USERNAME, MYTOOLSPLAN_PASSWORD

def get_noxtools_credentials():
    """Get Noxtools credentials from environment variables"""
    return NOXTOOLS_USERNAME, NOXTOOLS_PASSWORD

def get_auth_method():
    """Get authentication method from environment variables"""
    return AUTH_METHOD

# Instance globale de configuration
config = Config() 