import os
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv('config.env')

# NordVPN Configuration
NORDVPN_USERNAME = os.getenv('NORDVPN_USERNAME')
NORDVPN_PASSWORD = os.getenv('NORDVPN_PASSWORD')

# MyToolsPlan Configuration
MYTOOLSPLAN_USERNAME = os.getenv('MYTOOLSPLAN_USERNAME')
MYTOOLSPLAN_PASSWORD = os.getenv('MYTOOLSPLAN_PASSWORD')
MYTOOLSPLAN_LOGIN_URL = os.getenv('MYTOOLSPLAN_LOGIN_URL', 'https://sam.mytoolsplan.xyz/login')

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
        self.nordvpn_username = NORDVPN_USERNAME
        self.nordvpn_password = NORDVPN_PASSWORD
        self.mytoolsplan_username = MYTOOLSPLAN_USERNAME
        self.mytoolsplan_password = MYTOOLSPLAN_PASSWORD
        self.mytoolsplan_login_url = MYTOOLSPLAN_LOGIN_URL
        self.browser_timeout = BROWSER_TIMEOUT
        self.page_load_timeout = PAGE_LOAD_TIMEOUT
        self.navigation_timeout = NAVIGATION_TIMEOUT
        self.api_base_url = API_BASE_URL
        self.api_key = API_KEY
    
    def validate_credentials(self):
        """Valide que les credentials essentiels sont configurés"""
        if not self.mytoolsplan_username or not self.mytoolsplan_password:
            raise ValueError("MyToolsPlan credentials manquants dans config.env")
        
        # NordVPN est optionnel
        if not self.nordvpn_username or not self.nordvpn_password:
            print("⚠️ NordVPN credentials non configurés (optionnel)")
    
    def print_config_summary(self):
        """Affiche un résumé de la configuration"""
        print("📋 Configuration du scraper:")
        print(f"  • MyToolsPlan: {'✅' if self.mytoolsplan_username else '❌'}")
        print(f"  • NordVPN: {'✅' if self.nordvpn_username else '❌'}")
        print(f"  • API: {'✅' if self.api_base_url != 'http://localhost:3000/api' else '❌'}")
        print(f"  • Timeouts: {self.browser_timeout}ms/{self.page_load_timeout}ms/{self.navigation_timeout}ms")

def get_nordvpn_credentials():
    """Get NordVPN credentials from environment variables"""
    return NORDVPN_USERNAME, NORDVPN_PASSWORD

def get_mytoolsplan_credentials():
    """Get MyToolsPlan credentials from environment variables"""
    return MYTOOLSPLAN_USERNAME, MYTOOLSPLAN_PASSWORD

# Instance globale de configuration
config = Config() 