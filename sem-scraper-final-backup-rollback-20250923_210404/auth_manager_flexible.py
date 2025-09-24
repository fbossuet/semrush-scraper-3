#!/usr/bin/env python3
"""
Gestionnaire d'authentification flexible
Supporte les méthodes MyToolsPlan et Noxtools avec fallback automatique
Créé le 23 septembre 2025
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from config import get_auth_method, get_mytoolsplan_credentials, get_noxtools_credentials

logger = logging.getLogger(__name__)

class FlexibleAuthManager:
    """
    Gestionnaire d'authentification flexible supportant plusieurs méthodes.
    
    Méthodes supportées :
    - mytoolsplan : Authentification classique sur app.mytoolsplan.com
    - noxtools : Nouvelle authentification sur noxtools.com → semrush1.semrush.pw
    
    Fonctionnalités :
    - Fallback automatique en cas d'échec
    - Gestion des sessions cross-domain
    - Récupération dynamique des credentials
    - Support des workers parallèles
    """
    
    def __init__(self):
        self.auth_method = get_auth_method()
        self.is_authenticated = False
        self.last_auth_time = 0
        self.session_health_checked = False
        self.fallback_attempted = False
        
        logger.info(f"🔧 AuthManager initialisé avec méthode: {self.auth_method}")
    
    async def authenticate(self, page, worker_id: int = 0) -> bool:
        """
        Authentification flexible avec fallback automatique
        
        Args:
            page: Page Playwright
            worker_id: ID du worker pour les logs
            
        Returns:
            bool: True si authentification réussie
        """
        logger.info(f"🔐 Worker {worker_id}: Début authentification (méthode: {self.auth_method})")
        
        # Essayer la méthode configurée
        success = await self._try_auth_method(page, worker_id, self.auth_method)
        
        # Si échec et pas encore tenté le fallback, essayer l'autre méthode
        if not success and not self.fallback_attempted:
            logger.warning(f"⚠️ Worker {worker_id}: Échec méthode {self.auth_method}, tentative fallback...")
            self.fallback_attempted = True
            
            fallback_method = "mytoolsplan" if self.auth_method == "noxtools" else "noxtools"
            success = await self._try_auth_method(page, worker_id, fallback_method)
            
            if success:
                logger.info(f"✅ Worker {worker_id}: Fallback vers {fallback_method} réussi")
                self.auth_method = fallback_method  # Mettre à jour la méthode active
        
        if success:
            self.is_authenticated = True
            self.last_auth_time = time.time()
            self.session_health_checked = True
            logger.info(f"✅ Worker {worker_id}: Authentification complète réussie")
        else:
            logger.error(f"❌ Worker {worker_id}: Toutes les méthodes d'authentification ont échoué")
        
        return success
    
    async def _try_auth_method(self, page, worker_id: int, method: str) -> bool:
        """Essaie une méthode d'authentification spécifique"""
        try:
            if method == "mytoolsplan":
                return await self._authenticate_mytoolsplan(page, worker_id)
            elif method == "noxtools":
                return await self._authenticate_noxtools(page, worker_id)
            else:
                logger.error(f"❌ Worker {worker_id}: Méthode d'authentification inconnue: {method}")
                return False
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur méthode {method}: {e}")
            return False
    
    async def _authenticate_mytoolsplan(self, page, worker_id: int) -> bool:
        """Authentification MyToolsPlan classique"""
        try:
            logger.info(f"🔐 Worker {worker_id}: Authentification MyToolsPlan...")
            
            # Navigation vers la page de login
            await page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # Récupérer les credentials
            username, password = get_mytoolsplan_credentials()
            
            # Remplir et soumettre le formulaire
            await page.fill('input[name="amember_login"]', username)
            await page.fill('input[name="amember_pass"]', password)
            
            try:
                await page.click('input[type="submit"][class="frm-submit"]')
            except:
                await page.evaluate('document.querySelector("form[name=\\"login\\"]").submit()')
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Vérifier le succès du login
            current_url = page.url
            if "member" not in current_url.lower():
                logger.error(f"❌ Worker {worker_id}: Login MyToolsPlan échoué")
                return False
            
            logger.info(f"✅ Worker {worker_id}: Login MyToolsPlan réussi")
            
            # Synchroniser les cookies avec sam.mytoolsplan.xyz
            await self._sync_cookies_to_sam_domain(page, worker_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur authentification MyToolsPlan: {e}")
            return False
    
    async def _authenticate_noxtools(self, page, worker_id: int) -> bool:
        """Authentification Noxtools (nouvelle méthode)"""
        try:
            logger.info(f"🔐 Worker {worker_id}: Authentification Noxtools...")
            
            # Étape 1: Login noxtools.com
            await page.goto("https://noxtools.com/secure/login", wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(2)
            
            # Récupérer les credentials
            username, password = get_noxtools_credentials()
            
            # Remplir les champs de login
            await page.wait_for_selector('input[id="amember-login"]', timeout=10000)
            await page.wait_for_selector('input[id="amember-pass"]', timeout=10000)
            
            await page.fill('input[id="amember-login"]', username)
            await page.fill('input[id="amember-pass"]', password)
            
            # Soumettre le formulaire
            await page.click('input[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # Vérifier le succès du login
            current_url = page.url
            if "member" not in current_url.lower():
                logger.error(f"❌ Worker {worker_id}: Login Noxtools échoué")
                return False
            
            logger.info(f"✅ Worker {worker_id}: Login Noxtools réussi")
            
            # Étape 2: Navigation vers page Semrush
            await page.goto("https://noxtools.com/secure/page/semrush", wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(2)
            
            # Étape 3: Navigation vers semrush1.semrush.pw (session maintenue)
            await page.goto("https://semrush1.semrush.pw/analytics/overview/?searchType=domain", 
                          wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(2)
            
            # Vérifier que l'accès fonctionne
            final_url = page.url
            if "login" in final_url.lower() or "signin" in final_url.lower():
                logger.error(f"❌ Worker {worker_id}: Session perdue sur semrush1.semrush.pw")
                return False
            
            # 4. Synchroniser les cookies avec semrush1.semrush.pw
            await self._sync_cookies_to_semrush_domain(page, worker_id)
            
            logger.info(f"✅ Worker {worker_id}: Accès semrush1.semrush.pw réussi")
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur authentification Noxtools: {e}")
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
    
    def get_current_auth_method(self) -> str:
        """Retourne la méthode d'authentification actuellement utilisée"""
        return self.auth_method
    
    def is_auth_valid(self) -> bool:
        """Vérifie si l'authentification est encore valide"""
        if not self.is_authenticated:
            return False
        
        # Vérifier si l'authentification n'est pas trop ancienne (1 heure)
        if time.time() - self.last_auth_time > 3600:
            logger.warning("⚠️ Authentification expirée (plus de 1 heure)")
            self.is_authenticated = False
            return False
        
        return True
    
    async def _sync_cookies_to_semrush_domain(self, page, worker_id: int):
        """Synchronise les cookies d'authentification avec semrush1.semrush.pw"""
        try:
            logger.info(f"🔄 Worker {worker_id}: Synchronisation des cookies cross-domain Noxtools...")
            
            # Récupérer les cookies de noxtools.com
            cookies = await page.context.cookies()
            
            # Filtrer les cookies d'authentification (plus large pour Noxtools)
            auth_cookies = []
            for cookie in cookies:
                # Pour Noxtools, récupérer plus de cookies car l'API peut en avoir besoin
                if any(key in cookie['name'].lower() for key in ['session', 'auth', 'login', 'member', 'amember', 'php', 'semrush', 'cookie', 'token', 'csrf', 'sid']):
                    auth_cookies.append(cookie)
            
            logger.info(f"🍪 Worker {worker_id}: {len(auth_cookies)} cookies d'authentification trouvés")
            
            # Naviguer vers semrush1.semrush.pw pour établir le contexte
            await page.goto("https://semrush1.semrush.pw", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            # Modifier le domaine des cookies pour semrush1.semrush.pw
            semrush_cookies = []
            for cookie in auth_cookies:
                semrush_cookie = cookie.copy()
                # Utiliser le domaine parent pour partage entre noxtools.com et semrush1.semrush.pw
                if 'noxtools.com' in cookie.get('domain', ''):
                    semrush_cookie['domain'] = '.semrush.pw'  # Domaine parent pour partage
                elif 'semrush' in cookie.get('domain', ''):
                    semrush_cookie['domain'] = '.semrush.pw'
                else:
                    semrush_cookie['domain'] = 'semrush1.semrush.pw'
                semrush_cookies.append(semrush_cookie)
            
            # Appliquer les cookies au contexte
            if semrush_cookies:
                await page.context.add_cookies(semrush_cookies)
                logger.info(f"✅ Worker {worker_id}: {len(semrush_cookies)} cookies synchronisés avec semrush1.semrush.pw")
            else:
                logger.warning(f"⚠️ Worker {worker_id}: Aucun cookie à synchroniser")
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur synchronisation cookies Noxtools: {e}")
            return False

    async def ensure_noxtools_session(self, page, worker_id: int) -> bool:
        """Vérifie et renouvelle la session Noxtools si nécessaire"""
        try:
            if self.auth_method != "noxtools":
                return True  # Pas nécessaire pour MyToolsPlan
            
            logger.info(f"🔍 Worker {worker_id}: Vérification session Noxtools...")
            
            # Tester la session sur semrush1.semrush.pw
            await page.goto("https://semrush1.semrush.pw/analytics/overview/?searchType=domain", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(1)
            
            current_url = page.url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                logger.warning(f"⚠️ Worker {worker_id}: Session Noxtools expirée, renouvellement...")
                
                # Renouveler la session
                await self._authenticate_noxtools(page, worker_id)
                return True
            else:
                # Tester l'API directement pour vérifier si elle fonctionne
                try:
                    api_test = await page.evaluate("""
                        async () => {
                            try {
                                const response = await fetch('/dpa/rpc', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    credentials: 'include',
                                    body: JSON.stringify({
                                        "id": 1,
                                        "jsonrpc": "2.0",
                                        "method": "test",
                                        "params": {}
                                    })
                                });
                                const text = await response.text();
                                return { ok: response.ok, status: response.status, text: text.substring(0, 100) };
                            } catch (e) {
                                return { ok: false, error: e.message };
                            }
                        }
                    """)
                    
                    if api_test.get('ok') and 'Session expired' not in api_test.get('text', ''):
                        logger.info(f"✅ Worker {worker_id}: Session Noxtools valide (API test OK)")
                        return True
                    else:
                        logger.warning(f"⚠️ Worker {worker_id}: Session Noxtools expirée (API test failed: {api_test.get('text', 'Unknown error')})")
                        # Renouveler la session
                        await self._authenticate_noxtools(page, worker_id)
                        return True
                        
                except Exception as e:
                    logger.warning(f"⚠️ Worker {worker_id}: Erreur test API: {e}, renouvellement session...")
                    await self._authenticate_noxtools(page, worker_id)
                    return True
                
        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Erreur vérification session Noxtools: {e}")
            return False

    def get_current_auth_method(self) -> str:
        """Retourne la méthode d'authentification actuelle"""
        return self.auth_method

    def reset_auth(self):
        """Remet à zéro l'état d'authentification"""
        self.is_authenticated = False
        self.last_auth_time = 0
        self.session_health_checked = False
        self.fallback_attempted = False
        logger.info("🔄 État d'authentification réinitialisé")

# Instance globale
auth_manager = FlexibleAuthManager()
