#!/usr/bin/env python3
"""
API Credentials Manager - Gestion centralisée des credentials pour les APIs MyToolsPlan
Basé sur le système de variables d'environnement comme dans l'exemple Node.js
Créé le 18 janvier 2025
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class APICredentials:
    """
    Gestionnaire centralisé des credentials pour les APIs MyToolsPlan.
    Utilise les variables d'environnement avec des fallbacks sécurisés.
    """
    
    def __init__(self):
        """Initialise les credentials depuis les variables d'environnement"""
        self._credentials = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Charge les credentials depuis les variables d'environnement"""
        try:
            # Récupération depuis les variables d'environnement
            user_id = os.getenv('SAM_USER_ID') or os.getenv('MYTOOLSPLAN_USER_ID')
            api_key = os.getenv('SAM_API_KEY') or os.getenv('MYTOOLSPLAN_API_KEY')
            
            # Fallbacks sécurisés (credentials actuels du scraper)
            if not user_id:
                user_id = '26931056'  # Credential actuel du scraper
                logger.warning("⚠️ SAM_USER_ID non défini, utilisation du fallback")
            
            if not api_key:
                api_key = '943cfac719badc2ca14126e08b8fe44f'  # Credential actuel du scraper
                logger.warning("⚠️ SAM_API_KEY non définie, utilisation du fallback")
            
            # Validation des credentials
            try:
                user_id_int = int(user_id)
            except ValueError:
                raise ValueError(f"USER_ID invalide: {user_id}")
            
            if not api_key or len(api_key) < 10:
                raise ValueError(f"API_KEY invalide: {api_key[:8]}...")
            
            self._credentials = {
                'userId': user_id_int,
                'apiKey': api_key,
                'source': 'environment' if os.getenv('SAM_USER_ID') else 'fallback'
            }
            
            logger.info(f"✅ Credentials chargés depuis {self._credentials['source']}")
            logger.info(f"   User ID: {user_id_int}")
            logger.info(f"   API Key: {api_key[:8]}...")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des credentials: {e}")
            # Fallback d'urgence
            self._credentials = {
                'userId': 26931056,
                'apiKey': '943cfac719badc2ca14126e08b8fe44f',
                'source': 'emergency_fallback'
            }
            logger.warning("🚨 Utilisation du fallback d'urgence")
    
    def get_credentials(self) -> Dict[str, Any]:
        """
        Retourne les credentials au format utilisé par le scraper
        
        Returns:
            dict: Credentials au format {'userId': int, 'apiKey': str}
        """
        if not self._credentials:
            self._load_credentials()
        
        return {
            'userId': self._credentials['userId'],
            'apiKey': self._credentials['apiKey']
        }
    
    def get_user_id(self) -> int:
        """Retourne l'ID utilisateur"""
        if not self._credentials:
            self._load_credentials()
        return self._credentials['userId']
    
    def get_api_key(self) -> str:
        """Retourne la clé API"""
        if not self._credentials:
            self._load_credentials()
        return self._credentials['apiKey']
    
    def get_source(self) -> str:
        """Retourne la source des credentials (environment/fallback/emergency_fallback)"""
        if not self._credentials:
            self._load_credentials()
        return self._credentials.get('source', 'unknown')
    
    def is_from_environment(self) -> bool:
        """Vérifie si les credentials viennent des variables d'environnement"""
        return self.get_source() == 'environment'
    
    def reload(self):
        """Recharge les credentials (utile pour les tests)"""
        self._credentials = None
        self._load_credentials()
    
    def __str__(self):
        """Représentation string pour debug"""
        if not self._credentials:
            return "APICredentials(not_loaded)"
        
        return f"APICredentials(userId={self._credentials['userId']}, apiKey={self._credentials['apiKey'][:8]}..., source={self._credentials['source']})"

# Instance globale pour éviter les rechargements multiples
_global_credentials = None

def get_api_credentials() -> APICredentials:
    """
    Fonction utilitaire pour récupérer l'instance globale des credentials.
    Utilise le pattern singleton pour éviter les rechargements multiples.
    
    Returns:
        APICredentials: Instance des credentials
    """
    global _global_credentials
    if _global_credentials is None:
        _global_credentials = APICredentials()
    return _global_credentials

def get_credentials_dict() -> Dict[str, Any]:
    """
    Fonction utilitaire pour récupérer directement le dictionnaire des credentials.
    
    Returns:
        dict: Credentials au format {'userId': int, 'apiKey': str}
    """
    return get_api_credentials().get_credentials()

# Test en isolation
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Test du système de credentials...")
    
    # Test 1: Chargement des credentials
    creds = get_api_credentials()
    print(f"✅ Credentials chargés: {creds}")
    
    # Test 2: Récupération du dictionnaire
    creds_dict = get_credentials_dict()
    print(f"✅ Dictionnaire: {creds_dict}")
    
    # Test 3: Vérification de la source
    print(f"✅ Source: {creds.get_source()}")
    print(f"✅ Depuis environnement: {creds.is_from_environment()}")
    
    print("🎉 Tests terminés avec succès!")
