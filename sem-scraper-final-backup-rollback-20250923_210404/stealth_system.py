#!/usr/bin/env python3
"""
Système de discrétion et throttling pour éviter la détection
Gestion centralisée des délais, rotation d'identité, et rate limiting
"""

import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import deque
import threading

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket pour rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consomme des tokens, retourne True si possible"""
        with self.lock:
            now = time.time()
            # Refill tokens
            time_passed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1) -> float:
        """Calcule le temps d'attente nécessaire"""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            
            needed = tokens - self.tokens
            return needed / self.refill_rate

class StealthIdentity:
    """Gestion de l'identité pour éviter la détection"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.accept_languages = [
            'en-US,en;q=0.9,fr;q=0.8',
            'en-US,en;q=0.9',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'en-GB,en;q=0.9,en-US;q=0.8'
        ]
        
        self.current_ua = random.choice(self.user_agents)
        self.current_lang = random.choice(self.accept_languages)
        self.rotation_time = time.time()
        self.rotation_interval = 3600  # 1 heure
    
    def get_headers(self) -> Dict[str, str]:
        """Retourne les headers avec identité randomisée"""
        # Rotation périodique
        if time.time() - self.rotation_time > self.rotation_interval:
            self.current_ua = random.choice(self.user_agents)
            self.current_lang = random.choice(self.accept_languages)
            self.rotation_time = time.time()
            logger.debug(f"🔄 Rotation identité: UA={self.current_ua[:50]}...")
        
        return {
            'User-Agent': self.current_ua,
            'Accept-Language': self.current_lang,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
    
    def get_user_agent(self) -> str:
        """Retourne le User-Agent actuel"""
        return self.current_ua

class StealthThrottler:
    """Système de throttling intelligent"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.identity = StealthIdentity()
        
        # Token bucket pour rate limiting
        self.token_bucket = TokenBucket(
            capacity=60,  # 60 requêtes
            refill_rate=1.0  # 1 requête par seconde
        )
        
        # Backoff adaptatif
        self.backoff_attempts = {}
        self.max_backoff = 10.0
        self.base_backoff = 1.0
        self.backoff_multiplier = 2.0
        
        # Historique des requêtes
        self.request_history = deque(maxlen=100)
        self.daily_requests = 0
        self.daily_reset = datetime.now(timezone.utc).date()
        
        # Statistiques
        self.total_requests = 0
        self.throttled_requests = 0
        self.backoff_requests = 0
    
    async def throttle_request(self, request_type: str = "api") -> None:
        """Applique le throttling avant une requête"""
        # Vérifier la limite quotidienne
        if self._check_daily_limit():
            await asyncio.sleep(60)  # Attendre 1 minute si limite atteinte
        
        # Token bucket
        if not self.token_bucket.consume():
            wait_time = self.token_bucket.wait_for_tokens()
            if wait_time > 0:
                logger.debug(f"⏳ Worker {self.worker_id}: Rate limit - attente {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.throttled_requests += 1
        
        # Délai aléatoire entre requêtes
        base_delay = random.uniform(0.3, 0.8)  # 300-800ms
        jitter = random.uniform(-0.1, 0.1)     # ±100ms
        delay = max(0, base_delay + jitter)
        
        if delay > 0:
            logger.debug(f"⏳ Worker {self.worker_id}: Throttling {request_type} - {delay:.3f}s")
            await asyncio.sleep(delay)
        
        # Enregistrer la requête
        self.request_history.append(time.time())
        self.total_requests += 1
        self.daily_requests += 1
    
    async def handle_error_backoff(self, error: Exception, request_type: str = "api") -> bool:
        """Gère le backoff adaptatif sur erreur"""
        error_key = f"{request_type}_{type(error).__name__}"
        
        # Compter les tentatives
        if error_key not in self.backoff_attempts:
            self.backoff_attempts[error_key] = 0
        
        self.backoff_attempts[error_key] += 1
        attempts = self.backoff_attempts[error_key]
        
        # Calculer le délai de backoff
        backoff_delay = min(
            self.base_backoff * (self.backoff_multiplier ** (attempts - 1)),
            self.max_backoff
        )
        
        # Ajouter du jitter
        jitter = random.uniform(0.1, 0.3) * backoff_delay
        total_delay = backoff_delay + jitter
        
        logger.warning(f"⚠️ Worker {self.worker_id}: Backoff {request_type} - tentative {attempts}, attente {total_delay:.1f}s")
        await asyncio.sleep(total_delay)
        
        self.backoff_requests += 1
        
        # Reset après succès (géré par l'appelant)
        return attempts < 5  # Max 5 tentatives
    
    def reset_backoff(self, request_type: str = "api") -> None:
        """Reset le backoff après succès"""
        error_key = f"{request_type}_{type(Exception).__name__}"
        if error_key in self.backoff_attempts:
            del self.backoff_attempts[error_key]
    
    def _check_daily_limit(self) -> bool:
        """Vérifie si la limite quotidienne est atteinte"""
        today = datetime.now(timezone.utc).date()
        if today != self.daily_reset:
            self.daily_requests = 0
            self.daily_reset = today
        
        return self.daily_requests >= 1000  # Limite quotidienne
    
    async def human_like_pause(self, pause_type: str = "session") -> None:
        """Simule des pauses humaines"""
        if pause_type == "session":
            base_delay = 2.0
            jitter = random.uniform(-0.5, 0.5)
        elif pause_type == "scroll":
            base_delay = 0.5
            jitter = random.uniform(-0.1, 0.1)
        elif pause_type == "typing":
            base_delay = 0.1
            jitter = random.uniform(-0.05, 0.05)
        else:
            base_delay = 1.0
            jitter = random.uniform(-0.2, 0.2)
        
        delay = max(0, base_delay + jitter)
        if delay > 0:
            logger.debug(f"⏳ Worker {self.worker_id}: Pause humaine {pause_type} - {delay:.3f}s")
            await asyncio.sleep(delay)
    
    def get_stats(self) -> Dict[str, any]:
        """Retourne les statistiques de throttling"""
        return {
            "total_requests": self.total_requests,
            "throttled_requests": self.throttled_requests,
            "backoff_requests": self.backoff_requests,
            "daily_requests": self.daily_requests,
            "active_backoffs": len(self.backoff_attempts),
            "current_ua": self.identity.current_ua[:50] + "..."
        }

class StealthSystem:
    """Système central de discrétion"""
    
    def __init__(self):
        self.throttlers: Dict[int, StealthThrottler] = {}
        self.global_identity = StealthIdentity()
        self.session_cooldowns: Dict[str, float] = {}
        self.max_concurrent = 3
        self.active_requests = 0
        self.lock = threading.Lock()
    
    def get_throttler(self, worker_id: int) -> StealthThrottler:
        """Récupère ou crée un throttler pour un worker"""
        if worker_id not in self.throttlers:
            self.throttlers[worker_id] = StealthThrottler(worker_id)
        return self.throttlers[worker_id]
    
    async def throttle_api_call(self, worker_id: int, api_type: str = "generic") -> None:
        """Throttle un appel API"""
        throttler = self.get_throttler(worker_id)
        await throttler.throttle_request(f"api_{api_type}")
    
    async def handle_api_error(self, worker_id: int, error: Exception, api_type: str = "generic") -> bool:
        """Gère les erreurs API avec backoff"""
        throttler = self.get_throttler(worker_id)
        return await throttler.handle_error_backoff(error, f"api_{api_type}")
    
    def reset_api_backoff(self, worker_id: int, api_type: str = "generic") -> None:
        """Reset le backoff après succès API"""
        throttler = self.get_throttler(worker_id)
        throttler.reset_backoff(f"api_{api_type}")
    
    async def human_pause(self, worker_id: int, pause_type: str = "session") -> None:
        """Pause humaine"""
        throttler = self.get_throttler(worker_id)
        await throttler.human_like_pause(pause_type)
    
    def get_stealth_headers(self) -> Dict[str, str]:
        """Retourne les headers de discrétion"""
        return self.global_identity.get_headers()
    
    def get_stealth_user_agent(self) -> str:
        """Retourne le User-Agent de discrétion"""
        return self.global_identity.get_user_agent()
    
    async def check_concurrent_limit(self) -> None:
        """Vérifie la limite de requêtes simultanées"""
        with self.lock:
            if self.active_requests >= self.max_concurrent:
                wait_time = random.uniform(0.5, 2.0)
                logger.debug(f"⏳ Limite concurrente atteinte - attente {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
    
    def get_global_stats(self) -> Dict[str, any]:
        """Retourne les statistiques globales"""
        stats = {
            "active_throttlers": len(self.throttlers),
            "active_requests": self.active_requests,
            "session_cooldowns": len(self.session_cooldowns)
        }
        
        # Agréger les stats des throttlers
        for worker_id, throttler in self.throttlers.items():
            stats[f"worker_{worker_id}"] = throttler.get_stats()
        
        return stats

# Instance globale
stealth_system = StealthSystem()
