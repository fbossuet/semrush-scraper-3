#!/usr/bin/env python3
"""
ServerManager - Gestion centralisée des serveurs Semrush avec fallback automatique.

Ce module implémente la gestion dynamique des serveurs Semrush (semrush1→semrush5)
selon les spécifications NOX-011 et NOX-017 pour maintenir la cohérence des URLs.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from enum import Enum

logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """Statut d'un serveur."""
    ACTIVE = "active"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class ServerConfig:
    """Configuration d'un serveur Semrush."""
    name: str  # semrush1, semrush2, etc.
    domain: str  # semrush1.semrush.pw
    bridge_url: str  # https://semrush.noxtools.com/server1.php
    status: ServerStatus = ServerStatus.UNKNOWN
    failure_count: int = 0
    last_failure_reason: Optional[str] = None

class ServerManager:
    """
    Gestionnaire centralisé des serveurs Semrush avec fallback automatique.
    
    Implémente les spécifications :
    - NOX-011 : Gestion du fallback entre serveurs Semrush (semrush1→semrush5)
    - NOX-017 : Maintien de la cohérence des URLs lors du fallback serveurs
    """
    
    def __init__(self):
        """Initialise le ServerManager avec la configuration par défaut."""
        self.servers = self._initialize_servers()
        self.current_server_index = 0  # Commence par semrush1
        self.max_failures_per_server = 3
        self.fallback_enabled = True
        
        logger.info(f"ServerManager initialisé avec {len(self.servers)} serveurs")
        logger.info(f"Serveur actuel: {self.get_current_server().name}")
    
    def _initialize_servers(self) -> List[ServerConfig]:
        """Initialise la liste des serveurs disponibles."""
        return [
            ServerConfig(
                name="semrush1",
                domain="semrush1.semrush.pw",
                bridge_url="https://semrush.noxtools.com/server1.php"
            ),
            ServerConfig(
                name="semrush2", 
                domain="semrush2.semrush.pw",
                bridge_url="https://semrush.noxtools.com/server2.php"
            ),
            ServerConfig(
                name="semrush3",
                domain="semrush3.semrush.pw", 
                bridge_url="https://semrush.noxtools.com/server3.php"
            ),
            ServerConfig(
                name="semrush4",
                domain="semrush4.semrush.pw",
                bridge_url="https://semrush.noxtools.com/server4.php"
            ),
            ServerConfig(
                name="semrush5",
                domain="semrush5.semrush.pw",
                bridge_url="https://semrush.noxtools.com/server5.php"
            )
        ]
    
    def get_current_server(self) -> ServerConfig:
        """Retourne le serveur actuellement actif."""
        return self.servers[self.current_server_index]
    
    def get_current_domain(self) -> str:
        """Retourne le domaine du serveur actuel."""
        return self.get_current_server().domain
    
    def get_current_bridge_url(self) -> str:
        """Retourne l'URL du bridge du serveur actuel."""
        return self.get_current_server().bridge_url
    
    def get_current_server_name(self) -> str:
        """Retourne le nom du serveur actuel."""
        return self.get_current_server().name
    
    def normalize_url_to_current_server(self, url: str) -> str:
        """
        Normalise une URL pour utiliser le serveur actuel.
        
        Args:
            url: URL à normaliser (peut contenir n'importe quel serveur semrush)
            
        Returns:
            URL normalisée avec le serveur actuel
        """
        try:
            parsed = urlparse(url)
            
            # Si l'URL n'est pas valide ou n'a pas de netloc, retourner tel quel
            if not parsed.netloc:
                return url
            
            # Si c'est déjà le bon serveur, retourner tel quel
            if parsed.netloc == self.get_current_domain():
                return url
            
            # Si ce n'est pas un domaine semrush, retourner tel quel
            if 'semrush' not in parsed.netloc:
                return url
            
            # Remplacer le domaine par le serveur actuel
            new_parsed = parsed._replace(netloc=self.get_current_domain())
            normalized_url = urlunparse(new_parsed)
            
            logger.debug(f"URL normalisée: {url} → {normalized_url}")
            return normalized_url
            
        except Exception as e:
            logger.warning(f"Erreur lors de la normalisation de l'URL {url}: {e}")
            return url
    
    def mark_server_failed(self, reason: str = "Unknown error"):
        """
        Marque le serveur actuel comme ayant échoué.
        
        Args:
            reason: Raison de l'échec
        """
        current_server = self.get_current_server()
        current_server.status = ServerStatus.FAILED
        current_server.failure_count += 1
        current_server.last_failure_reason = reason
        
        logger.warning(f"❌ Serveur {current_server.name} marqué comme échoué: {reason}")
        logger.warning(f"   Échecs: {current_server.failure_count}/{self.max_failures_per_server}")
        
        # Si on a atteint le max d'échecs, passer au serveur suivant
        if current_server.failure_count >= self.max_failures_per_server:
            self._switch_to_next_server()
    
    def mark_server_success(self):
        """Marque le serveur actuel comme fonctionnel."""
        current_server = self.get_current_server()
        if current_server.status != ServerStatus.ACTIVE:
            current_server.status = ServerStatus.ACTIVE
            current_server.failure_count = 0
            current_server.last_failure_reason = None
            logger.info(f"✅ Serveur {current_server.name} marqué comme fonctionnel")
    
    def _switch_to_next_server(self):
        """Passe au serveur suivant dans la liste."""
        if not self.fallback_enabled:
            logger.warning("⚠️ Fallback désactivé, impossible de changer de serveur")
            return False
        
        old_server = self.get_current_server()
        
        # Trouver le prochain serveur disponible
        for i in range(1, len(self.servers)):
            next_index = (self.current_server_index + i) % len(self.servers)
            next_server = self.servers[next_index]
            
            if next_server.failure_count < self.max_failures_per_server:
                self.current_server_index = next_index
                logger.info(f"🔄 Switch serveur: {old_server.name} → {next_server.name}")
                return True
        
        logger.error("❌ Aucun serveur disponible pour le fallback")
        return False
    
    def get_available_servers(self) -> List[ServerConfig]:
        """Retourne la liste des serveurs disponibles (non échoués)."""
        return [server for server in self.servers 
                if server.failure_count < self.max_failures_per_server]
    
    def get_server_status_summary(self) -> Dict[str, Any]:
        """Retourne un résumé du statut de tous les serveurs."""
        return {
            "current_server": self.get_current_server_name(),
            "current_domain": self.get_current_domain(),
            "current_bridge_url": self.get_current_bridge_url(),
            "fallback_enabled": self.fallback_enabled,
            "servers": [
                {
                    "name": server.name,
                    "domain": server.domain,
                    "status": server.status.value,
                    "failure_count": server.failure_count,
                    "last_failure_reason": server.last_failure_reason
                }
                for server in self.servers
            ],
            "available_servers": len(self.get_available_servers()),
            "total_servers": len(self.servers)
        }
    
    def reset_all_servers(self):
        """Remet à zéro le statut de tous les serveurs."""
        for server in self.servers:
            server.status = ServerStatus.UNKNOWN
            server.failure_count = 0
            server.last_failure_reason = None
        
        self.current_server_index = 0
        logger.info("🔄 Tous les serveurs ont été réinitialisés")
    
    def set_fallback_enabled(self, enabled: bool):
        """Active ou désactive le système de fallback."""
        self.fallback_enabled = enabled
        logger.info(f"🔄 Fallback {'activé' if enabled else 'désactivé'}")
    
    def force_server(self, server_name: str) -> bool:
        """
        Force l'utilisation d'un serveur spécifique.
        
        Args:
            server_name: Nom du serveur (semrush1, semrush2, etc.)
            
        Returns:
            True si le serveur a été trouvé et activé
        """
        for i, server in enumerate(self.servers):
            if server.name == server_name:
                self.current_server_index = i
                logger.info(f"🎯 Serveur forcé: {server_name}")
                return True
        
        logger.warning(f"⚠️ Serveur {server_name} non trouvé")
        return False

# Instance globale du ServerManager
_server_manager_instance: Optional[ServerManager] = None

def get_server_manager() -> ServerManager:
    """Retourne l'instance globale du ServerManager."""
    global _server_manager_instance
    if _server_manager_instance is None:
        _server_manager_instance = ServerManager()
    return _server_manager_instance

def reset_server_manager():
    """Remet à zéro l'instance globale du ServerManager."""
    global _server_manager_instance
    _server_manager_instance = None

if __name__ == '__main__':
    # Test du ServerManager
    print("=== Test ServerManager ===")
    
    sm = ServerManager()
    
    # Test initial
    print(f"Serveur actuel: {sm.get_current_server_name()}")
    print(f"Domaine actuel: {sm.get_current_domain()}")
    print(f"Bridge actuel: {sm.get_current_bridge_url()}")
    
    # Test normalisation URL
    test_url = "https://semrush3.semrush.pw/analytics/overview/?q=test.com"
    normalized = sm.normalize_url_to_current_server(test_url)
    print(f"URL normalisée: {test_url} → {normalized}")
    
    # Test fallback
    print("\n=== Test Fallback ===")
    sm.mark_server_failed("Test failure")
    print(f"Nouveau serveur: {sm.get_current_server_name()}")
    
    # Test résumé
    print("\n=== Résumé ===")
    summary = sm.get_server_status_summary()
    print(f"Résumé: {summary}")

