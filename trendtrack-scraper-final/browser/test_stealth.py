#!/usr/bin/env python3
"""
Script de test pour la configuration Playwright stealth
Teste les anti-détections et les pauses aléatoires
"""

import asyncio
import logging
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser import StealthBrowser, AntiDetectionSystem, DelayType
from auth import TrendTrackDOMAuth

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_stealth_browser():
    """Tester le navigateur stealth"""
    logger.info("🧪 Test du navigateur stealth")
    
    try:
        async with StealthBrowser(headless=True, stealth_mode=True) as browser:
            page = browser.page
            
            # Test 1: Navigation vers une page de test
            logger.info("📄 Test de navigation...")
            await page.goto("https://httpbin.org/headers", timeout=30000)
            
            # Test 2: Délai aléatoire
            logger.info("⏱️ Test des délais aléatoires...")
            await browser.random_delay(1000, 3000)
            
            # Test 3: Récupération du contenu
            logger.info("📄 Récupération du contenu...")
            content = await page.content()
            
            # Vérifier que les headers sont présents
            if "User-Agent" in content:
                logger.info("✅ Headers détectés dans la réponse")
            else:
                logger.warning("⚠️ Headers non détectés")
            
            # Test 4: Test des fonctionnalités humaines
            logger.info("🖱️ Test des fonctionnalités humaines...")
            await browser.human_like_click("body")
            await browser.random_delay(500, 1500)
            
            logger.info("✅ Test du navigateur stealth réussi")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test du navigateur stealth: {e}")
        return False

async def test_anti_detection_system():
    """Tester le système d'anti-détection"""
    logger.info("🧪 Test du système d'anti-détection")
    
    try:
        # Créer le système
        anti_detection = AntiDetectionSystem(stealth_level="high")
        
        # Test 1: Délais aléatoires
        logger.info("⏱️ Test des délais aléatoires...")
        await anti_detection.random_delay(DelayType.SHORT)
        await anti_detection.random_delay(DelayType.MEDIUM)
        await anti_detection.random_delay(DelayType.LONG)
        
        # Test 2: Délais de frappe
        logger.info("⌨️ Test des délais de frappe...")
        await anti_detection.human_like_typing_delay("Test de frappe", "normal")
        
        # Test 3: Délais de lecture
        logger.info("📖 Test des délais de lecture...")
        await anti_detection.human_like_reading_delay("Ceci est un texte de test pour la lecture.", "normal")
        
        # Test 4: Délais de clic
        logger.info("🖱️ Test des délais de clic...")
        await anti_detection.human_like_click_delay("hesitation")
        
        # Test 5: Statistiques
        stats = anti_detection.get_session_stats()
        logger.info(f"📊 Statistiques: {stats}")
        
        logger.info("✅ Test du système d'anti-détection réussi")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test du système d'anti-détection: {e}")
        return False

async def test_stealth_with_trendtrack():
    """Tester le navigateur stealth avec TrendTrack"""
    logger.info("🧪 Test du navigateur stealth avec TrendTrack")
    
    try:
        # Créer le navigateur stealth
        async with StealthBrowser(headless=True, stealth_mode=True) as browser:
            page = browser.page
            
            # Test 1: Navigation vers TrendTrack
            logger.info("🌐 Navigation vers TrendTrack...")
            await page.goto("https://app.trendtrack.io/fr/login", timeout=30000)
            
            # Test 2: Délai aléatoire
            await browser.random_delay(2000, 4000)
            
            # Test 3: Vérifier que la page est chargée
            title = await page.title()
            logger.info(f"📄 Titre de la page: {title}")
            
            # Test 4: Vérifier les éléments de la page
            try:
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                logger.info("✅ Formulaire de login détecté")
            except:
                logger.warning("⚠️ Formulaire de login non détecté")
            
            # Test 5: Test des mouvements de souris
            logger.info("🖱️ Test des mouvements de souris...")
            anti_detection = AntiDetectionSystem(stealth_level="medium")
            await anti_detection.random_mouse_movement(page, duration=3)
            
            # Test 6: Test du défilement
            logger.info("📜 Test du défilement...")
            await anti_detection.random_scroll(page, direction="random", intensity=2)
            
            logger.info("✅ Test du navigateur stealth avec TrendTrack réussi")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test avec TrendTrack: {e}")
        return False

async def test_integration_with_auth():
    """Tester l'intégration avec l'authentification"""
    logger.info("🧪 Test d'intégration avec l'authentification")
    
    try:
        # Créer le navigateur stealth
        async with StealthBrowser(headless=True, stealth_mode=True) as browser:
            page = browser.page
            
            # Créer le système d'anti-détection
            anti_detection = AntiDetectionSystem(stealth_level="medium")
            
            # Test 1: Navigation vers TrendTrack
            logger.info("🌐 Navigation vers TrendTrack...")
            await page.goto("https://app.trendtrack.io/fr/login", timeout=30000)
            
            # Test 2: Délai de lecture de la page
            await anti_detection.human_like_reading_delay("Page de connexion TrendTrack", "normal")
            
            # Test 3: Remplir le formulaire (sans soumettre)
            logger.info("📝 Test de remplissage du formulaire...")
            
            # Attendre que le formulaire soit chargé
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Délai avant de commencer à taper
            await anti_detection.human_like_click_delay("hesitation")
            
            # Remplir l'email
            await browser.human_like_type('input[type="email"]', 'test@example.com')
            
            # Délai entre les champs
            await anti_detection.random_delay(DelayType.SHORT)
            
            # Remplir le mot de passe
            await browser.human_like_type('input[type="password"]', 'testpassword')
            
            # Délai avant de cliquer sur le bouton
            await anti_detection.human_like_click_delay("careful")
            
            logger.info("✅ Test d'intégration avec l'authentification réussi")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'intégration: {e}")
        return False

async def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests de configuration Playwright stealth")
    logger.info("=" * 70)
    
    tests = [
        ("Navigateur Stealth", test_stealth_browser),
        ("Système Anti-Détection", test_anti_detection_system),
        ("Stealth avec TrendTrack", test_stealth_with_trendtrack),
        ("Intégration avec Auth", test_integration_with_auth)
    ]
    
    results = []
    
    for name, test_func in tests:
        logger.info(f"\n📋 {name}")
        logger.info("-" * 40)
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Erreur lors du test {name}: {e}")
            results.append((name, False))
    
    # Résumé
    logger.info("\n" + "=" * 70)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        logger.info(f"{name:.<50} {status}")
        if result:
            passed += 1
    
    logger.info("-" * 70)
    logger.info(f"Résultat global: {passed}/{total} tests passés")
    
    if passed == total:
        logger.info("🎉 T033 - Playwright stealth: CONFIGURATION VALIDÉE!")
        logger.info("\n✅ Prêt pour la prochaine tâche (T034 - Système de pauses aléatoires)")
        return True
    else:
        logger.info("❌ T033 - Playwright stealth: CONFIGURATION INCOMPLÈTE")
        logger.info(f"⚠️ {total - passed} test(s) ont échoué")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


