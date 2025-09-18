#!/usr/bin/env python3
"""
Authentification API pour TrendTrack
Remplace l'authentification DOM par une authentification API plus robuste
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# Configuration du logging
logger = logging.getLogger(__name__)

class TrendTrackAuth:
    def __init__(self, base_url: str = "https://app.trendtrack.io"):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False
        self.auth_timestamp = None
        
        # Headers de base pour l'authentification
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)

    def authenticate(self, email: str = None, password: str = None) -> bool:
        """
        Authentification sur TrendTrack
        
        Args:
            email: Email de connexion (optionnel si déjà en session)
            password: Mot de passe (optionnel si déjà en session)
            
        Returns:
            bool: True si authentifié, False sinon
        """
        try:
            logger.info("🔐 Début de l'authentification TrendTrack")
            
            # 1. Récupérer la page de login pour obtenir les tokens
            login_page_url = f"{self.base_url}/fr/login"
            
            # Charger la page de login
            login_page = self.session.get(login_page_url)
            login_page.raise_for_status()
            logger.info(f"✅ Page de login récupérée: {login_page.status_code}")
            
            # Extraire le Next-Action token
            next_action_token = self._extract_next_action_token(login_page.text)
            if not next_action_token:
                logger.error("❌ Impossible d'extraire le token d'authentification")
                return False
            
            # 2. Si email/password fournis, faire la connexion
            if email and password:
                # Headers pour la requête de login (basés sur l'exemple qui fonctionne)
                login_headers = {
                    "Accept": "text/x-component",
                    "Next-Action": next_action_token,
                    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%5B%22locale%22%2C%22fr%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22(dynamic-pages)%22%2C%7B%22children%22%3A%5B%22(login-pages)%22%2C%7B%22children%22%3A%5B%22login%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2F%22%2C%22refresh%22%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
                    "Content-Type": "text/plain;charset=UTF-8",
                    "Referer": f"{self.base_url}/fr/login",
                    "Priority": "u=0"
                }
                
                # Body de la requête au format JSON
                import json
                login_body = json.dumps([{
                    "email": email,
                    "password": password,
                    "next": "$undefined"
                }])
                
                logger.info(f"🔍 Données de login: {login_body}")
                logger.info(f"🔍 Next-Action: {next_action_token}")
                
                # Envoyer la requête de login
                login_response = self.session.post(
                    login_page_url,
                    headers=login_headers,
                    data=login_body
                )
                
                logger.info(f"📡 Login response: {login_response.status_code}")
                
                # Vérifier la réponse
                if login_response.status_code == 200:
                    # Vérifier si on a été redirigé ou si on a reçu des cookies
                    if self._check_authentication_success(login_response):
                        self.authenticated = True
                        self.auth_timestamp = datetime.now(timezone.utc)
                        logger.info("✅ Authentification réussie!")
                        return True
                    else:
                        logger.error("❌ Échec de l'authentification - Vérifiez vos identifiants")
                        return False
                else:
                    logger.error(f"❌ Erreur HTTP: {login_response.status_code}")
                    return False
            
            else:
                # 3. Vérifier si déjà authentifié (cookies de session existants)
                if self._check_authentication_success(login_page):
                    self.authenticated = True
                    self.auth_timestamp = datetime.now(timezone.utc)
                    logger.info("✅ Déjà authentifié (session existante)")
                    return True
                else:
                    logger.warning("❌ Non authentifié - email/password requis")
                    return False
                    
        except requests.RequestException as e:
            logger.error(f"❌ Erreur réseau lors de l'authentification: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur authentification: {e}")
            return False

    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """Extraire le token CSRF depuis le HTML"""
        import re
        
        # Patterns courants pour les tokens CSRF
        patterns = [
            r'<meta name="csrf-token" content="([^"]+)"',
            r'name="_token" value="([^"]+)"',
            r'"csrf_token":"([^"]+)"',
            r'_token["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                token = match.group(1)
                logger.info(f"🔒 Token CSRF trouvé: {token[:10]}...")
                return token
        
        logger.warning("⚠️ Aucun token CSRF trouvé")
        return None

    def _extract_next_action_token(self, html_content: str) -> Optional[str]:
        """
        Extrait le token Next-Action depuis la page de login
        """
        import re
        
        # Chercher dans les scripts ou les meta tags
        patterns = [
            r'Next-Action["\s]*:["\s]*([a-f0-9]+)',
            r'nextAction["\s]*:["\s]*"([a-f0-9]+)"',
            r'action["\s]*:["\s]*"([a-f0-9]{32,})"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                token = match.group(1)
                logger.info(f"🔒 Next-Action token trouvé: {token[:20]}...")
                return token
        
        # Token par défaut trouvé dans votre requête
        default_token = "89867268f974f3c62aec9745607d277f8ef6d99b"
        logger.info(f"🔒 Utilisation du token par défaut: {default_token[:20]}...")
        return default_token

    def _extract_next_router_state(self, html: str) -> Optional[str]:
        """Extraire le Next-Router-State-Tree depuis le HTML"""
        import re
        
        # Patterns pour Next-Router-State-Tree
        patterns = [
            r'"__next_router_state_tree":"([^"]+)"',
            r'router-state-tree["\']:\s*["\']([^"\']+)["\']',
            r'state-tree["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                state = match.group(1)
                logger.info(f"🔒 Next-Router-State trouvé: {state[:30]}...")
                return state
        
        logger.warning("⚠️ Aucun Next-Router-State trouvé")
        return None

    def _check_authentication_success(self, response) -> bool:
        """
        Vérifie si l'authentification a réussi
        """
        # Vérifier la présence de cookies de session
        session_cookies = ['session', 'auth', 'token', '__session']
        has_session_cookie = any(cookie in response.cookies for cookie in session_cookies)
        
        # Vérifier le contenu de la réponse
        response_text = response.text
        success_indicators = ['workspace', 'dashboard', 'trending-shops']
        has_success_content = any(indicator in response_text.lower() for indicator in success_indicators)
        
        # Vérifier les headers de redirection
        is_redirected = response.status_code in [302, 301] or 'Location' in response.headers
        
        logger.info(f"🔍 Vérification auth - Cookies: {has_session_cookie}, Contenu: {has_success_content}, Redirect: {is_redirected}")
        
        return has_session_cookie or has_success_content or is_redirected

    def _check_authentication(self, response) -> bool:
        """
        Vérifier si l'utilisateur est authentifié
        
        Args:
            response: Réponse HTTP à analyser
            
        Returns:
            bool: True si authentifié
        """
        try:
            logger.info(f"🔍 Vérification d'authentification - Status: {response.status_code}")
            
            # Méthodes de vérification de l'authentification
            
            # 1. Vérifier l'URL finale (après redirects)
            if hasattr(response, 'url'):
                current_url = response.url
                logger.info(f"🔍 URL finale: {current_url}")
                
                # Si on est encore sur /login, pas authentifié
                if '/login' in current_url:
                    logger.info("❌ Reste sur la page de login")
                    return False
                # Si on est sur dashboard/workspace, authentifié
                if any(path in current_url for path in ['/dashboard', '/workspace', '/trending-shops']):
                    logger.info("✅ URL de dashboard/workspace détectée")
                    return True
            
            # 2. Vérifier le contenu de la page
            if hasattr(response, 'text'):
                content = response.text
                logger.info(f"🔍 Contenu de la réponse (premiers 500 chars): {content[:500]}")
                
                # Signes d'authentification réussie
                auth_indicators = [
                    'w-al-yakoobs-workspace-x0Qg9st',  # Workspace spécifique
                    'trending-shops',
                    'logout',
                    'dashboard',
                    'workspace',
                    'seif.alyakoob@gmail.com'  # Email de l'utilisateur
                ]
                
                for indicator in auth_indicators:
                    if indicator in content:
                        logger.info(f"✅ Indicateur d'authentification trouvé: {indicator}")
                        return True
                
                # Signes de non-authentification
                unauth_indicators = [
                    'login',
                    'sign in',
                    'email',
                    'password',
                    'forgot password'
                ]
                
                for indicator in unauth_indicators:
                    if indicator in content.lower():
                        logger.info(f"❌ Indicateur de non-authentification trouvé: {indicator}")
                        return False
            
            # 3. Vérifier les cookies de session
            logger.info(f"🔍 Cookies de session: {list(self.session.cookies.keys())}")
            session_cookies = ['session', 'auth', 'token', 'laravel_session', 'next-auth']
            for cookie_name in session_cookies:
                if cookie_name in self.session.cookies:
                    cookie_value = self.session.cookies[cookie_name]
                    if cookie_value and len(cookie_value) > 10:  # Cookie non vide
                        logger.info(f"✅ Cookie de session trouvé: {cookie_name}")
                        return True
            
            # 4. Vérifier le status code et les headers
            if response.status_code == 200:
                # Si on a un 200 et pas d'indicateurs négatifs, considérer comme authentifié
                logger.info("✅ Status 200 sans indicateurs négatifs")
                return True
            
            logger.info("❌ Aucun indicateur d'authentification trouvé")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification auth: {e}")
            return False

    def get_authenticated_session(self):
        """
        Retourner la session authentifiée pour utilisation externe
        
        Returns:
            requests.Session: Session avec cookies d'authentification
        """
        if self.authenticated:
            return self.session
        else:
            raise Exception("Non authentifié - appelez authenticate() d'abord")

    def is_authenticated(self) -> bool:
        """Vérifier si actuellement authentifié"""
        return self.authenticated

    def is_session_valid(self, max_age_hours: int = 24) -> bool:
        """
        Vérifier si la session est encore valide
        
        Args:
            max_age_hours: Âge maximum de la session en heures
            
        Returns:
            bool: True si la session est valide
        """
        if not self.authenticated or not self.auth_timestamp:
            return False
        
        age = datetime.now(timezone.utc) - self.auth_timestamp
        return age < timedelta(hours=max_age_hours)

    def refresh_authentication(self, email: str = None, password: str = None) -> bool:
        """
        Rafraîchir l'authentification si nécessaire
        
        Args:
            email: Email de connexion
            password: Mot de passe
            
        Returns:
            bool: True si authentifié
        """
        if self.is_session_valid():
            logger.info("✅ Session encore valide")
            return True
        
        logger.info("🔄 Session expirée, nouvelle authentification...")
        return self.authenticate(email, password)

    def logout(self) -> bool:
        """
        Se déconnecter de TrendTrack
        
        Returns:
            bool: True si déconnexion réussie
        """
        try:
            if self.authenticated:
                # Tenter de faire une requête de logout si l'endpoint existe
                logout_url = f"{self.base_url}/logout"
                response = self.session.post(logout_url)
                
                # Nettoyer la session locale
                self.session.cookies.clear()
                self.authenticated = False
                self.auth_timestamp = None
                
                logger.info("✅ Déconnexion réussie")
                return True
            else:
                logger.info("ℹ️ Pas de session active à déconnecter")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la déconnexion: {e}")
            return False

# Instance globale pour compatibilité
trendtrack_auth = TrendTrackAuth()

# Fonctions de compatibilité
def authenticate_trendtrack(email: str = None, password: str = None) -> bool:
    """Fonction de compatibilité pour l'authentification"""
    return trendtrack_auth.authenticate(email, password)

def get_trendtrack_session():
    """Fonction de compatibilité pour récupérer la session"""
    return trendtrack_auth.get_authenticated_session()

def is_trendtrack_authenticated() -> bool:
    """Fonction de compatibilité pour vérifier l'authentification"""
    return trendtrack_auth.is_authenticated()

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    auth = TrendTrackAuth()
    
    # Tentative d'authentification avec session existante
    if auth.authenticate():
        print("✅ Prêt à utiliser l'API")
        session = auth.get_authenticated_session()
    else:
        # Authentification avec credentials si nécessaire
        email = "ton-email@example.com"  # À remplacer
        password = "ton-mot-de-passe"    # À remplacer
        
        if auth.authenticate(email, password):
            print("✅ Connexion réussie")
            session = auth.get_authenticated_session()
        else:
            print("❌ Impossible de se connecter")


