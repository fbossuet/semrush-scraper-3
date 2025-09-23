#!/usr/bin/env python3
"""
AuthManager - Gestionnaire d'authentification unifié pour MyToolsPlan
Créé le 15 septembre 2025
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Gestionnaire d'authentification unifié pour toutes les APIs MyToolsPlan.
    
    Fonctionnalités :
    - Authentification unique sur app.mytoolsplan.com
    - Synchronisation des cookies cross-domain
    - Auto-refresh des sessions expirées
    - Récupération dynamique des credentials
    - Support des workers parallèles (sans locks)
    """
    
    def __init__(self):
        self.is_authenticated = False
        self.last_auth_time = 0
        # LOCK SUPPRIMÉ - Empêchait les workers parallèles de fonctionner
        self.credentials_cache = {}
        self.session_health_checked = False
        
    async def authenticate(self, page, worker_id: int = 0) -> bool:
        """
        Authentification unifiée pour toutes les APIs
        
        Args:
            page: Page Playwright
            worker_id: ID du worker pour les logs
            
        Returns:
            bool: True si authentification réussie
        """
        # LOCK SUPPRIMÉ - Permet aux workers parallèles de s'authentifier simultanément
        # Vérifier si déjà authentifié récemment
        if self.is_authenticated and (time.time() - self.last_auth_time) < 300:  # 5 minutes
            logger.info(f"🔐 Worker {worker_id}: Session déjà authentifiée (cache)")
            return True
        
        logger.info(f"🔐 Worker {worker_id}: Authentification MyToolsPlan...")
        
        try:
            # 1. Navigation vers la page de login
            await page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # 2. Récupérer les credentials depuis l'environnement
            from config import get_mytoolsplan_credentials
            username, password = get_mytoolsplan_credentials()
            
            # 3. Remplir et soumettre le formulaire
            await page.fill('input[name="amember_login"]', username)
            await page.fill('input[name="amember_pass"]', password)
            
            try:
                await page.click('input[type="submit"][class="frm-submit"]')
            except:
                await page.evaluate('document.querySelector("form[name=\\"login\\"]").submit()')
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # 4. Vérifier le succès du login
            current_url = page.url
            if "member" not in current_url.lower():
                logger.error(f"❌ Worker {worker_id}: Login échoué - Pas sur la page membre")
                return False
            
            logger.info(f"✅ Worker {worker_id}: Login réussi sur app.mytoolsplan.com")
            
            # 5. Synchroniser les cookies avec sam.mytoolsplan.xyz
            await self._sync_cookies_to_sam_domain(page, worker_id)
            
            # 6. Récupérer les credentials dynamiques
            await self._extract_dynamic_credentials(page, worker_id)
            
            self.is_authenticated = True
            self.last_auth_time = time.time()
            self.session_health_checked = True
            
            logger.info(f"✅ Worker {worker_id}: Authentification complète réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur authentification: {e}")
            return False
    
    async def _sync_cookies_to_sam_domain(self, page, worker_id: int):
        """Synchronise les cookies d'authentification avec sam.mytoolsplan.xyz"""
        try:
            logger.info(f"🔄 Worker {worker_id}: Synchronisation des cookies cross-domain...")
            
            # Récupérer les cookies de app.mytoolsplan.com
            cookies = await page.context.cookies()
            
            # Filtrer les cookies d'authentification
            auth_cookies = []
            for cookie in cookies:
                if any(key in cookie['name'].lower() for key in ['session', 'auth', 'login', 'member', 'amember', 'php']):
                    auth_cookies.append(cookie)
            
            logger.info(f"🍪 Worker {worker_id}: {len(auth_cookies)} cookies d'authentification trouvés")
            
            # Naviguer vers sam.mytoolsplan.xyz
            await page.goto("https://sam.mytoolsplan.xyz", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            # Modifier le domaine des cookies pour sam.mytoolsplan.xyz
            sam_cookies = []
            for cookie in auth_cookies:
                sam_cookie = cookie.copy()
                sam_cookie['domain'] = '.mytoolsplan.xyz'  # Domaine parent pour partage
                sam_cookies.append(sam_cookie)
            
            # Appliquer les cookies au contexte
            await page.context.add_cookies(sam_cookies)
            
            logger.info(f"✅ Worker {worker_id}: Cookies synchronisés avec sam.mytoolsplan.xyz")
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur synchronisation cookies: {e}")
    
    async def _extract_dynamic_credentials(self, page, worker_id: int):
        """Extrait les credentials dynamiques depuis la session active"""
        try:
            logger.info(f"🔍 Worker {worker_id}: Extraction des credentials dynamiques...")
            
            # Récupérer les credentials depuis localStorage, sessionStorage, cookies, etc.
            credentials_data = await page.evaluate("""
                () => {
                    const credentials = {};
                    
                    // Chercher dans localStorage
                    const authToken = localStorage.getItem('auth_token') || localStorage.getItem('semrush_token');
                    const userId = localStorage.getItem('user_id') || localStorage.getItem('semrush_user_id');
                    const apiKey = localStorage.getItem('api_key') || localStorage.getItem('semrush_api_key');
                    
                    // Chercher dans sessionStorage
                    const sessionAuth = sessionStorage.getItem('auth_token') || sessionStorage.getItem('semrush_credentials');
                    
                    // Chercher dans les cookies
                    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
                        const [key, value] = cookie.trim().split('=');
                        acc[key] = value;
                        return acc;
                    }, {});
                    
                    // Chercher dans window global
                    const windowAuth = window.user_credentials || window.semrushAuth || window.authData;
                    
                    return {
                        localStorage: {
                            authToken: authToken,
                            userId: userId,
                            apiKey: apiKey
                        },
                        sessionStorage: {
                            auth: sessionAuth
                        },
                        cookies: Object.keys(cookies).filter(k => k.includes('auth') || k.includes('session')),
                        window: !!windowAuth,
                        timestamp: new Date().toISOString()
                    };
                }
            """)
            
            logger.info(f"📊 Worker {worker_id}: Credentials extraits: {credentials_data}")
            
            # Mettre en cache les credentials trouvés
            self.credentials_cache = credentials_data
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur extraction credentials: {e}")
    
    async def check_session_health(self, page, worker_id: int = 0) -> bool:
        """Vérifie la santé de la session et re-authentifie si nécessaire"""
        try:
            current_url = page.url
            
            # Vérifier si on est redirigé vers login
            if "app.mytoolsplan.com" in current_url and "login" in current_url:
                logger.warning(f"⚠️ Worker {worker_id}: Session expirée détectée (redirection login)")
                self.is_authenticated = False
                return False
            
            # Vérifier le contenu de la page pour des messages d'erreur
            try:
                page_content = await page.content()
                if "please login" in page_content.lower() and "registered member" in page_content.lower():
                    logger.warning(f"⚠️ Worker {worker_id}: Session expirée détectée (message login)")
                    self.is_authenticated = False
                    return False
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur vérification session: {e}")
            return False
    
    async def ensure_authenticated(self, page, worker_id: int = 0) -> bool:
        """S'assure que l'utilisateur est authentifié, re-authentifie si nécessaire"""
        # Vérifier la santé de la session
        if not await self.check_session_health(page, worker_id):
            logger.info(f"🔄 Worker {worker_id}: Re-authentification requise...")
            return await self.authenticate(page, worker_id)
        
        # Si déjà authentifié, retourner True
        if self.is_authenticated:
            return True
        
        # Sinon, s'authentifier
        return await self.authenticate(page, worker_id)
    
    def get_cached_credentials(self) -> Dict[str, Any]:
        """Retourne les credentials mis en cache"""
        return self.credentials_cache.copy()
    
    def clear_auth_cache(self):
        """Vide le cache d'authentification"""
        self.is_authenticated = False
        self.last_auth_time = 0
        self.credentials_cache = {}
        self.session_health_checked = False
        logger.info("🧹 Cache d'authentification vidé")

# Instance globale
auth_manager = AuthManager()
