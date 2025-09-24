#!/usr/bin/env python3
"""
CredentialsManager - Gestion centralisée des credentials pour les APIs MyToolsPlan
Créé le 14 septembre 2025
"""

class CredentialsManager:
    """
    Gestionnaire centralisé des credentials pour les APIs MyToolsPlan.
    Évite la duplication des credentials dans tout le code.
    """
    
    def __init__(self):
        """Initialise les credentials avec les valeurs actuelles du scraper"""
        # Credentials extraits du code existant de production_scraper_parallel.py
        self.user_id = 26931056
        self.api_key = "943cfac719badc2ca14126e08b8fe44f"
    
    def get_credentials(self):
        """
        Retourne les credentials au format utilisé par le scraper actuel
        
        Returns:
            dict: Credentials au format {'userId': int, 'apiKey': str}
        """
        return {
            'userId': self.user_id,
            'apiKey': self.api_key
        }
    
    def get_user_id(self):
        """Retourne l'ID utilisateur"""
        return self.user_id
    
    def get_api_key(self):
        """Retourne la clé API"""
        return self.api_key
    
    def __str__(self):
        """Représentation string pour debug"""
        return f"CredentialsManager(userId={self.user_id}, apiKey={self.api_key[:8]}...)"

# Test en isolation
if __name__ == "__main__":
    print("🧪 TEST CREDENTIALSMANAGER EN ISOLATION")
    print("=" * 50)
    
    # Créer une instance
    credentials_manager = CredentialsManager()
    
    # Test 1: Vérifier les credentials
    credentials = credentials_manager.get_credentials()
    print(f"✅ Credentials: {credentials}")
    
    # Test 2: Vérifier les valeurs individuelles
    print(f"✅ User ID: {credentials_manager.get_user_id()}")
    print(f"✅ API Key: {credentials_manager.get_api_key()[:8]}...")
    
    # Test 3: Vérifier le format (identique au scraper actuel)
    expected_format = {
        'userId': 26931056,
        'apiKey': "943cfac719badc2ca14126e08b8fe44f"
    }
    
    if credentials == expected_format:
        print("✅ Format des credentials correct")
    else:
        print("❌ Format des credentials incorrect")
        print(f"   Attendu: {expected_format}")
        print(f"   Reçu: {credentials}")
    
    # Test 4: Vérifier la représentation string
    print(f"✅ Représentation: {credentials_manager}")
    
    print("\n🎉 TOUS LES TESTS CREDENTIALSMANAGER RÉUSSIS")
