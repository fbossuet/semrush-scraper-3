#!/usr/bin/env python3
"""
Authentification DOM Legacy pour TrendTrack
Maintient la compatibilité avec l'ancien système d'authentification basé sur DOM
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser

# Configuration du logging
logger = logging.getLogger(__name__)

class TrendTrackDOMAuth:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.authenticated = False
        self.auth_timestamp = None

    async def authenticate(self, email: str, password: str) -> bool:
        """
        Authentification DOM sur TrendTrack (méthode legacy)
        
        Args:
            email: Email de connexion
            password: Mot de passe
            
        Returns:
            bool: True si authentifié, False sinon
        """
        try:
            logger.info("🔐 Début de l'authentification DOM TrendTrack")
            
            # Initialiser Playwright
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            self.page = await self.browser.new_page()
            
            # Navigation vers la page de connexion
            await self.page.goto('https://app.trendtrack.io/fr/login', wait_until='domcontentloaded', timeout=30000)
            
            # Attendre que le formulaire soit chargé
            await self.page.wait_for_selector('input[type="email"][name="email"]', timeout=10000)
            
            # Attendre 3 secondes comme dans le test visuel
            await asyncio.sleep(3)
            
            # Remplir le formulaire
            await self.page.fill('input[type="email"][name="email"]', email)
            await self.page.fill('input[type="password"][name="password"]', password)
            
            # Attendre 2 secondes comme dans le test visuel
            await asyncio.sleep(2)
            
            # Cliquer sur le bouton de connexion
            await self.page.click('button[type="submit"]')
            
            # Attendre la redirection comme dans le test visuel
            await asyncio.sleep(5)
            
            # Vérifier que la connexion a réussi
            if await self._check_authentication():
                self.authenticated = True
                self.auth_timestamp = asyncio.get_event_loop().time()
                logger.info("✅ Authentification DOM réussie")
                return True
            else:
                logger.error("❌ Échec de l'authentification DOM")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur authentification DOM: {e}")
            return False

    async def _check_authentication(self) -> bool:
        """
        Vérifier si l'utilisateur est authentifié (méthode DOM)
        
        Returns:
            bool: True si authentifié
        """
        try:
            # Vérifier que la connexion a réussi en cherchant un élément de la page d'accueil
            try:
                await self.page.wait_for_selector('a[href*="trending-shops"]', timeout=10000)
                logger.info("✅ Connexion réussie - Page d'accueil détectée")
                return True
            except:
                logger.warning("⚠️ Connexion possiblement échouée - Vérification de la page...")
                
                # Vérifier l'URL actuelle
                current_url = self.page.url
                logger.info(f"🔍 URL actuelle: {current_url}")
                
                # Si on est toujours sur la page de login, la connexion a échoué
                if '/login' in current_url:
                    logger.error("❌ Connexion échouée - Reste sur la page de login")
                    return False
                
                # Si on a été redirigé ailleurs, considérer comme réussi
                logger.info("✅ Connexion réussie - Redirection détectée")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification auth DOM: {e}")
            return False

    async def get_authenticated_page(self) -> Optional[Page]:
        """
        Retourner la page authentifiée pour utilisation externe
        
        Returns:
            Page: Page avec session d'authentification
        """
        if self.authenticated and self.page:
            return self.page
        else:
            raise Exception("Non authentifié - appelez authenticate() d'abord")

    def is_authenticated(self) -> bool:
        """Vérifier si actuellement authentifié"""
        return self.authenticated

    async def is_session_valid(self, max_age_hours: int = 24) -> bool:
        """
        Vérifier si la session est encore valide
        
        Args:
            max_age_hours: Âge maximum de la session en heures
            
        Returns:
            bool: True si la session est valide
        """
        if not self.authenticated or not self.auth_timestamp:
            return False
        
        current_time = asyncio.get_event_loop().time()
        age_seconds = current_time - self.auth_timestamp
        max_age_seconds = max_age_hours * 3600
        
        return age_seconds < max_age_seconds

    async def refresh_authentication(self, email: str, password: str) -> bool:
        """
        Rafraîchir l'authentification si nécessaire
        
        Args:
            email: Email de connexion
            password: Mot de passe
            
        Returns:
            bool: True si authentifié
        """
        if await self.is_session_valid():
            logger.info("✅ Session DOM encore valide")
            return True
        
        logger.info("🔄 Session DOM expirée, nouvelle authentification...")
        return await self.authenticate(email, password)

    async def logout(self) -> bool:
        """
        Se déconnecter de TrendTrack (méthode DOM)
        
        Returns:
            bool: True si déconnexion réussie
        """
        try:
            if self.authenticated and self.page:
                # Tenter de cliquer sur logout si l'élément existe
                try:
                    await self.page.click('a[href*="logout"]', timeout=5000)
                    await asyncio.sleep(2)
                except:
                    # Si pas de bouton logout, naviguer vers la page de login
                    await self.page.goto('https://app.trendtrack.io/en/login')
                
                # Nettoyer l'état local
                self.authenticated = False
                self.auth_timestamp = None
                
                logger.info("✅ Déconnexion DOM réussie")
                return True
            else:
                logger.info("ℹ️ Pas de session DOM active à déconnecter")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la déconnexion DOM: {e}")
            return False

    async def close(self):
        """Fermer le navigateur et nettoyer les ressources"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                self.page = None
                self.authenticated = False
                self.auth_timestamp = None
                logger.info("✅ Navigateur fermé")
        except Exception as e:
            logger.error(f"❌ Erreur fermeture navigateur: {e}")

    async def __aenter__(self):
        """Support pour async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support pour async context manager"""
        await self.close()

# Instance globale pour compatibilité
trendtrack_dom_auth = TrendTrackDOMAuth()

# Fonctions de compatibilité
async def authenticate_trendtrack_dom(email: str, password: str) -> bool:
    """Fonction de compatibilité pour l'authentification DOM"""
    return await trendtrack_dom_auth.authenticate(email, password)

async def get_trendtrack_dom_page():
    """Fonction de compatibilité pour récupérer la page"""
    return await trendtrack_dom_auth.get_authenticated_page()

def is_trendtrack_dom_authenticated() -> bool:
    """Fonction de compatibilité pour vérifier l'authentification DOM"""
    return trendtrack_dom_auth.is_authenticated()

# Exemple d'utilisation
async def main():
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    async with TrendTrackDOMAuth() as auth:
        email = "ton-email@example.com"  # À remplacer
        password = "ton-mot-de-passe"    # À remplacer
        
        if await auth.authenticate(email, password):
            print("✅ Connexion DOM réussie")
            page = await auth.get_authenticated_page()
            # Utiliser la page pour le scraping...
        else:
            print("❌ Impossible de se connecter via DOM")

if __name__ == "__main__":
    asyncio.run(main())


