#!/usr/bin/env python3
"""
Système de pauses aléatoires et anti-détection pour TrendTrack
Implémente des délais intelligents et des patterns de comportement humain
"""

import asyncio
import random
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Configuration du logging
logger = logging.getLogger(__name__)

class DelayType(Enum):
    """Types de délais disponibles"""
    SHORT = "short"      # 500ms - 2s
    MEDIUM = "medium"    # 1s - 5s
    LONG = "long"        # 3s - 10s
    VERY_LONG = "very_long"  # 5s - 20s
    CUSTOM = "custom"    # Délai personnalisé

@dataclass
class DelayConfig:
    """Configuration des délais"""
    min_ms: int
    max_ms: int
    description: str

class AntiDetectionSystem:
    """
    Système d'anti-détection avec pauses aléatoires et patterns de comportement humain
    """
    
    def __init__(self, stealth_level: str = "medium"):
        self.stealth_level = stealth_level
        self.session_start_time = time.time()
        self.action_count = 0
        self.last_action_time = 0
        
        # Configuration des délais selon le niveau de furtivité
        self.delay_configs = {
            "low": {
                DelayType.SHORT: DelayConfig(300, 1000, "Délai court"),
                DelayType.MEDIUM: DelayConfig(800, 2000, "Délai moyen"),
                DelayType.LONG: DelayConfig(1500, 4000, "Délai long"),
                DelayType.VERY_LONG: DelayConfig(3000, 8000, "Délai très long")
            },
            "medium": {
                DelayType.SHORT: DelayConfig(500, 2000, "Délai court"),
                DelayType.MEDIUM: DelayConfig(1000, 5000, "Délai moyen"),
                DelayType.LONG: DelayConfig(3000, 10000, "Délai long"),
                DelayType.VERY_LONG: DelayConfig(5000, 20000, "Délai très long")
            },
            "high": {
                DelayType.SHORT: DelayConfig(1000, 3000, "Délai court"),
                DelayType.MEDIUM: DelayConfig(2000, 8000, "Délai moyen"),
                DelayType.LONG: DelayConfig(5000, 15000, "Délai long"),
                DelayType.VERY_LONG: DelayConfig(10000, 30000, "Délai très long")
            }
        }
        
        # Patterns de comportement humain
        self.human_patterns = {
            "reading_speed": {
                "fast": (100, 300),      # ms par caractère
                "normal": (200, 500),    # ms par caractère
                "slow": (400, 800)       # ms par caractère
            },
            "click_patterns": {
                "immediate": (0, 200),   # Clic immédiat
                "hesitation": (500, 1500), # Hésitation avant clic
                "careful": (1000, 3000)  # Clic réfléchi
            },
            "typing_speed": {
                "fast": (50, 150),       # ms par caractère
                "normal": (100, 300),    # ms par caractère
                "slow": (200, 500)       # ms par caractère
            }
        }

    async def random_delay(self, delay_type: DelayType = DelayType.MEDIUM, custom_min: int = None, custom_max: int = None) -> float:
        """
        Ajouter un délai aléatoire basé sur le type et le niveau de furtivité
        
        Args:
            delay_type: Type de délai à appliquer
            custom_min: Délai minimum personnalisé (pour DelayType.CUSTOM)
            custom_max: Délai maximum personnalisé (pour DelayType.CUSTOM)
            
        Returns:
            float: Délai appliqué en secondes
        """
        try:
            # Calculer le délai
            if delay_type == DelayType.CUSTOM:
                if custom_min is None or custom_max is None:
                    raise ValueError("custom_min et custom_max sont requis pour DelayType.CUSTOM")
                min_ms, max_ms = custom_min, custom_max
            else:
                config = self.delay_configs[self.stealth_level][delay_type]
                min_ms, max_ms = config.min_ms, config.max_ms
            
            # Ajouter de la variation basée sur l'heure et l'activité
            variation = self._calculate_variation()
            min_ms = int(min_ms * variation)
            max_ms = int(max_ms * variation)
            
            # Générer le délai aléatoire
            delay_ms = random.randint(min_ms, max_ms)
            delay_seconds = delay_ms / 1000
            
            # Log du délai
            logger.info(f"⏱️ Délai aléatoire ({delay_type.value}): {delay_ms}ms ({delay_seconds:.2f}s)")
            
            # Appliquer le délai
            await asyncio.sleep(delay_seconds)
            
            # Mettre à jour les statistiques
            self._update_action_stats()
            
            return delay_seconds
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du délai aléatoire: {e}")
            # Délai de fallback
            await asyncio.sleep(1)
            return 1.0

    def _calculate_variation(self) -> float:
        """
        Calculer la variation du délai basée sur l'heure et l'activité
        """
        current_hour = time.localtime().tm_hour
        
        # Variation basée sur l'heure (plus lent la nuit)
        if 22 <= current_hour or current_hour <= 6:
            hour_variation = random.uniform(1.2, 1.8)  # Plus lent la nuit
        elif 9 <= current_hour <= 17:
            hour_variation = random.uniform(0.8, 1.2)  # Plus rapide en journée
        else:
            hour_variation = random.uniform(1.0, 1.4)  # Normal
        
        # Variation basée sur l'activité récente
        if self.action_count > 10:
            activity_variation = random.uniform(1.1, 1.5)  # Plus lent si beaucoup d'actions
        elif self.action_count < 3:
            activity_variation = random.uniform(0.9, 1.1)  # Plus rapide si peu d'actions
        else:
            activity_variation = 1.0
        
        return hour_variation * activity_variation

    def _update_action_stats(self):
        """Mettre à jour les statistiques d'action"""
        self.action_count += 1
        self.last_action_time = time.time()

    async def human_like_typing_delay(self, text: str, speed: str = "normal") -> float:
        """
        Simuler un délai de frappe humaine
        
        Args:
            text: Texte à taper
            speed: Vitesse de frappe (fast, normal, slow)
            
        Returns:
            float: Délai total appliqué
        """
        try:
            if speed not in self.human_patterns["typing_speed"]:
                speed = "normal"
            
            min_ms, max_ms = self.human_patterns["typing_speed"][speed]
            total_delay = 0
            
            for char in text:
                # Délai par caractère
                char_delay = random.randint(min_ms, max_ms) / 1000
                await asyncio.sleep(char_delay)
                total_delay += char_delay
                
                # Pause occasionnelle (simuler la réflexion)
                if random.random() < 0.1:  # 10% de chance
                    pause_delay = random.randint(200, 800) / 1000
                    await asyncio.sleep(pause_delay)
                    total_delay += pause_delay
            
            logger.info(f"⌨️ Délai de frappe simulé: {total_delay:.2f}s pour {len(text)} caractères")
            return total_delay
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du délai de frappe: {e}")
            return 0

    async def human_like_reading_delay(self, text: str, speed: str = "normal") -> float:
        """
        Simuler un délai de lecture humaine
        
        Args:
            text: Texte à "lire"
            speed: Vitesse de lecture (fast, normal, slow)
            
        Returns:
            float: Délai total appliqué
        """
        try:
            if speed not in self.human_patterns["reading_speed"]:
                speed = "normal"
            
            min_ms, max_ms = self.human_patterns["reading_speed"][speed]
            
            # Calculer le délai basé sur la longueur du texte
            char_count = len(text)
            total_delay_ms = char_count * random.randint(min_ms, max_ms)
            
            # Ajouter des pauses de réflexion
            reflection_pauses = char_count // 50  # Une pause tous les 50 caractères
            for _ in range(reflection_pauses):
                total_delay_ms += random.randint(500, 2000)
            
            total_delay = total_delay_ms / 1000
            await asyncio.sleep(total_delay)
            
            logger.info(f"📖 Délai de lecture simulé: {total_delay:.2f}s pour {char_count} caractères")
            return total_delay
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du délai de lecture: {e}")
            return 0

    async def human_like_click_delay(self, hesitation: str = "normal") -> float:
        """
        Simuler un délai avant un clic (hésitation humaine)
        
        Args:
            hesitation: Niveau d'hésitation (immediate, hesitation, careful)
            
        Returns:
            float: Délai appliqué
        """
        try:
            if hesitation not in self.human_patterns["click_patterns"]:
                hesitation = "normal"
            
            min_ms, max_ms = self.human_patterns["click_patterns"][hesitation]
            delay_ms = random.randint(min_ms, max_ms)
            delay_seconds = delay_ms / 1000
            
            await asyncio.sleep(delay_seconds)
            
            logger.info(f"🖱️ Délai de clic simulé ({hesitation}): {delay_ms}ms")
            return delay_seconds
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du délai de clic: {e}")
            return 0

    async def session_break(self, min_duration: int = 30, max_duration: int = 120):
        """
        Prendre une pause de session (simuler une pause humaine)
        
        Args:
            min_duration: Durée minimum de la pause en secondes
            max_duration: Durée maximum de la pause en secondes
        """
        try:
            session_duration = time.time() - self.session_start_time
            
            # Calculer la durée de pause basée sur la durée de session
            if session_duration > 1800:  # Plus de 30 minutes
                pause_duration = random.randint(max_duration, max_duration * 2)
            elif session_duration > 900:  # Plus de 15 minutes
                pause_duration = random.randint(min_duration, max_duration)
            else:
                pause_duration = random.randint(min_duration // 2, min_duration)
            
            logger.info(f"☕ Pause de session: {pause_duration}s (session: {session_duration:.0f}s)")
            await asyncio.sleep(pause_duration)
            
            # Réinitialiser les statistiques après la pause
            self.action_count = 0
            self.session_start_time = time.time()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la pause de session: {e}")

    async def random_mouse_movement(self, page, duration: int = 5):
        """
        Simuler des mouvements de souris aléatoires
        
        Args:
            page: Page Playwright
            duration: Durée du mouvement en secondes
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Position aléatoire
                x = random.randint(0, 1920)
                y = random.randint(0, 1080)
                
                # Mouvement de souris
                await page.mouse.move(x, y)
                
                # Délai aléatoire entre les mouvements
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            logger.info(f"🖱️ Mouvements de souris simulés pendant {duration}s")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors des mouvements de souris: {e}")

    async def random_scroll(self, page, direction: str = "down", intensity: int = 3):
        """
        Simuler un défilement aléatoire
        
        Args:
            page: Page Playwright
            direction: Direction du défilement (up, down, random)
            intensity: Intensité du défilement (1-5)
        """
        try:
            scroll_count = random.randint(2, 5) * intensity
            
            for _ in range(scroll_count):
                if direction == "random":
                    scroll_direction = random.choice(["up", "down"])
                else:
                    scroll_direction = direction
                
                # Distance de défilement
                scroll_distance = random.randint(100, 500)
                
                if scroll_direction == "down":
                    await page.mouse.wheel(0, scroll_distance)
                else:
                    await page.mouse.wheel(0, -scroll_distance)
                
                # Délai entre les défilements
                await asyncio.sleep(random.uniform(0.3, 1.0))
            
            logger.info(f"📜 Défilement simulé: {scroll_count} mouvements ({direction})")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du défilement: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques de la session
        
        Returns:
            Dict contenant les statistiques
        """
        session_duration = time.time() - self.session_start_time
        
        return {
            "session_duration": session_duration,
            "action_count": self.action_count,
            "actions_per_minute": (self.action_count / session_duration) * 60 if session_duration > 0 else 0,
            "stealth_level": self.stealth_level,
            "last_action_time": self.last_action_time
        }

# Instance globale pour compatibilité
anti_detection = AntiDetectionSystem()

# Fonctions de compatibilité
async def random_delay(delay_type: DelayType = DelayType.MEDIUM, stealth_level: str = "medium") -> float:
    """Fonction de compatibilité pour les délais aléatoires"""
    system = AntiDetectionSystem(stealth_level)
    return await system.random_delay(delay_type)

async def human_typing_delay(text: str, speed: str = "normal") -> float:
    """Fonction de compatibilité pour les délais de frappe"""
    return await anti_detection.human_like_typing_delay(text, speed)

async def human_reading_delay(text: str, speed: str = "normal") -> float:
    """Fonction de compatibilité pour les délais de lecture"""
    return await anti_detection.human_like_reading_delay(text, speed)

async def human_click_delay(hesitation: str = "normal") -> float:
    """Fonction de compatibilité pour les délais de clic"""
    return await anti_detection.human_like_click_delay(hesitation)

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du système d'anti-détection"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Créer le système
    anti_detection = AntiDetectionSystem(stealth_level="high")
    
    # Test des différents types de délais
    print("🧪 Test des délais aléatoires...")
    
    await anti_detection.random_delay(DelayType.SHORT)
    await anti_detection.random_delay(DelayType.MEDIUM)
    await anti_detection.random_delay(DelayType.LONG)
    
    # Test des délais de frappe
    print("⌨️ Test des délais de frappe...")
    await anti_detection.human_like_typing_delay("Hello World!", "normal")
    
    # Test des délais de lecture
    print("📖 Test des délais de lecture...")
    await anti_detection.human_like_reading_delay("Ceci est un texte de test pour simuler la lecture humaine.", "normal")
    
    # Test des délais de clic
    print("🖱️ Test des délais de clic...")
    await anti_detection.human_like_click_delay("hesitation")
    
    # Afficher les statistiques
    stats = anti_detection.get_session_stats()
    print(f"📊 Statistiques de session: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
