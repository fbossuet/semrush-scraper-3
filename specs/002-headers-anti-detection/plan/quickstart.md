# Quickstart Guide: Système de Headers Anti-Détection

**Branch**: `002-headers-anti-detection` | **Date**: 2025-09-19 | **Spec**: `/specs/002-headers-anti-detection/spec.md`

## Overview
Ce guide vous permet de tester rapidement le système de headers anti-détection pour valider que l'implémentation fonctionne correctement et évite la détection par les sites distants.

---

## Prerequisites
- Python 3.8+
- Playwright installé et configuré
- Accès au système de scraping existant (sem-scraper-final)
- Connexion internet pour tester avec des sites réels

---

## Quick Test 1: Validation des Headers de Base

### Objectif
Vérifier que le système génère des headers réalistes et cohérents.

### Steps
```bash
# 1. Naviguer vers le répertoire du projet
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final

# 2. Lancer le test de validation des headers
python3 -c "
from stealth_system import StealthIdentity
import json

# Créer une identité de test
identity = StealthIdentity()
headers = identity.get_headers()

# Afficher les headers générés
print('=== HEADERS GÉNÉRÉS ===')
for key, value in headers.items():
    print(f'{key}: {value}')

# Vérifier la présence des headers essentiels
essential_headers = ['User-Agent', 'Accept-Language', 'Accept-Encoding', 'Accept']
missing_headers = [h for h in essential_headers if h not in headers]
if missing_headers:
    print(f'❌ Headers manquants: {missing_headers}')
else:
    print('✅ Tous les headers essentiels sont présents')

# Vérifier les headers Sec-Fetch-*
sec_fetch_headers = [h for h in headers.keys() if h.startswith('Sec-Fetch-')]
if sec_fetch_headers:
    print(f'✅ Headers Sec-Fetch-* présents: {sec_fetch_headers}')
else:
    print('❌ Headers Sec-Fetch-* manquants')
"
```

### Expected Results
- ✅ Tous les headers essentiels sont présents
- ✅ Headers Sec-Fetch-* présents
- ✅ User-Agent réaliste (Chrome/Firefox/Safari)
- ✅ Accept-Language cohérent
- ✅ Accept-Encoding standard

---

## Quick Test 2: Rotation des Headers

### Objectif
Vérifier que le système fait tourner les headers correctement.

### Steps
```bash
# 1. Test de rotation des headers
python3 -c "
from stealth_system import StealthIdentity
import time

# Créer une identité de test
identity = StealthIdentity()

# Capturer les headers initiaux
initial_headers = identity.get_headers()
initial_ua = initial_headers['User-Agent']

print(f'=== HEADERS INITIAUX ===')
print(f'User-Agent initial: {initial_ua}')

# Forcer la rotation (simuler le passage du temps)
identity.rotation_time = time.time() - 3700  # 1h+ dans le passé

# Obtenir les nouveaux headers
new_headers = identity.get_headers()
new_ua = new_headers['User-Agent']

print(f'=== HEADERS APRÈS ROTATION ===')
print(f'User-Agent après rotation: {new_ua}')

# Vérifier la rotation
if initial_ua != new_ua:
    print('✅ Rotation des headers fonctionne')
else:
    print('❌ Rotation des headers ne fonctionne pas')
"
```

### Expected Results
- ✅ Rotation des headers fonctionne
- ✅ User-Agent différent après rotation
- ✅ Autres headers également mis à jour

---

## Quick Test 3: Intégration avec Playwright

### Objectif
Vérifier que les headers sont correctement injectés dans Playwright.

### Steps
```bash
# 1. Test d'intégration Playwright
python3 -c "
import asyncio
from playwright.async_api import async_playwright
from stealth_system import StealthIdentity

async def test_playwright_integration():
    # Créer une identité de test
    identity = StealthIdentity()
    headers = identity.get_headers()
    
    print('=== TEST INTÉGRATION PLAYWRIGHT ===')
    print(f'Headers à injecter: {len(headers)} headers')
    
    # Lancer Playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    
    # Créer un contexte avec les headers
    context = await browser.new_context(
        user_agent=headers['User-Agent'],
        extra_http_headers=headers
    )
    
    page = await context.new_page()
    
    # Tester avec un site simple
    try:
        response = await page.goto('https://httpbin.org/headers', timeout=10000)
        if response and response.status == 200:
            print('✅ Requête réussie avec headers injectés')
            
            # Vérifier que les headers sont présents
            content = await page.content()
            if 'User-Agent' in content:
                print('✅ Headers détectés dans la réponse')
            else:
                print('❌ Headers non détectés dans la réponse')
        else:
            print(f'❌ Requête échouée: {response.status if response else \"Pas de réponse\"}')
    except Exception as e:
        print(f'❌ Erreur lors du test: {e}')
    finally:
        await browser.close()
        await playwright.stop()

# Lancer le test
asyncio.run(test_playwright_integration())
"
```

### Expected Results
- ✅ Requête réussie avec headers injectés
- ✅ Headers détectés dans la réponse
- ✅ Pas d'erreurs de configuration

---

## Quick Test 4: Test Anti-Détection

### Objectif
Vérifier que le système évite la détection sur des sites avec protection anti-bot.

### Steps
```bash
# 1. Test anti-détection
python3 -c "
import asyncio
from playwright.async_api import async_playwright
from stealth_system import StealthIdentity

async def test_anti_detection():
    # Créer une identité de test
    identity = StealthIdentity()
    headers = identity.get_headers()
    
    print('=== TEST ANTI-DÉTECTION ===')
    
    # Lancer Playwright avec configuration stealth
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security'
        ]
    )
    
    context = await browser.new_context(
        user_agent=headers['User-Agent'],
        extra_http_headers=headers,
        viewport={'width': 1920, 'height': 1080}
    )
    
    page = await context.new_page()
    
    # Tester avec des sites connus pour leur protection anti-bot
    test_sites = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
        'https://bot.sannysoft.com/'
    ]
    
    for site in test_sites:
        try:
            print(f'Test avec {site}...')
            response = await page.goto(site, timeout=15000)
            
            if response and response.status == 200:
                print(f'✅ {site}: Accès réussi')
                
                # Vérifier le contenu pour détecter les signes de blocage
                content = await page.content()
                if any(keyword in content.lower() for keyword in ['blocked', 'captcha', 'bot', 'suspicious']):
                    print(f'⚠️ {site}: Signes de détection détectés')
                else:
                    print(f'✅ {site}: Aucun signe de détection')
            else:
                print(f'❌ {site}: Accès échoué ({response.status if response else \"Pas de réponse\"})')
                
        except Exception as e:
            print(f'❌ {site}: Erreur - {e}')
    
    await browser.close()
    await playwright.stop()

# Lancer le test
asyncio.run(test_anti_detection())
"
```

### Expected Results
- ✅ Tous les sites: Accès réussi
- ✅ Aucun signe de détection
- ✅ Pas d'erreurs de configuration

---

## Quick Test 5: Performance et Scalabilité

### Objectif
Vérifier que le système de headers n'impacte pas les performances.

### Steps
```bash
# 1. Test de performance
python3 -c "
import time
from stealth_system import StealthIdentity

# Créer une identité de test
identity = StealthIdentity()

print('=== TEST DE PERFORMANCE ===')

# Test de génération de headers
start_time = time.time()
for i in range(100):
    headers = identity.get_headers()
end_time = time.time()

generation_time = (end_time - start_time) * 1000  # en ms
avg_time = generation_time / 100

print(f'Génération de 100 headers: {generation_time:.2f}ms')
print(f'Temps moyen par header: {avg_time:.2f}ms')

# Vérifier les performances
if avg_time < 10:  # Moins de 10ms par header
    print('✅ Performance excellente')
elif avg_time < 50:  # Moins de 50ms par header
    print('✅ Performance acceptable')
else:
    print('❌ Performance insuffisante')

# Test de rotation
start_time = time.time()
for i in range(10):
    identity.rotation_time = time.time() - 3700  # Forcer la rotation
    headers = identity.get_headers()
end_time = time.time()

rotation_time = (end_time - start_time) * 1000  # en ms
avg_rotation_time = rotation_time / 10

print(f'Rotation de 10 headers: {rotation_time:.2f}ms')
print(f'Temps moyen par rotation: {avg_rotation_time:.2f}ms')

if avg_rotation_time < 100:  # Moins de 100ms par rotation
    print('✅ Performance de rotation excellente')
else:
    print('❌ Performance de rotation insuffisante')
"
```

### Expected Results
- ✅ Performance excellente (temps moyen < 10ms)
- ✅ Performance de rotation excellente (temps moyen < 100ms)
- ✅ Pas de dégradation des performances

---

## Quick Test 6: Test d'Intégration Complet

### Objectif
Tester l'intégration complète avec le système de scraping existant.

### Steps
```bash
# 1. Test d'intégration complet
python3 -c "
import asyncio
from playwright.async_api import async_playwright
from stealth_system import StealthIdentity

async def test_complete_integration():
    print('=== TEST D\'INTÉGRATION COMPLET ===')
    
    # Créer une identité de test
    identity = StealthIdentity()
    
    # Lancer Playwright avec configuration complète
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir='./test-session-profile',
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security'
        ],
        viewport={'width': 1920, 'height': 1080}
    )
    
    page = await browser.new_page()
    
    # Injecter les headers
    headers = identity.get_headers()
    await page.set_extra_http_headers(headers)
    
    print(f'Headers injectés: {len(headers)} headers')
    
    # Test de navigation
    try:
        response = await page.goto('https://httpbin.org/headers', timeout=10000)
        if response and response.status == 200:
            print('✅ Navigation réussie')
            
            # Vérifier les headers dans la réponse
            content = await page.content()
            if 'User-Agent' in content and 'Accept-Language' in content:
                print('✅ Headers correctement transmis')
            else:
                print('❌ Headers non transmis correctement')
        else:
            print(f'❌ Navigation échouée: {response.status if response else \"Pas de réponse\"}')
    except Exception as e:
        print(f'❌ Erreur de navigation: {e}')
    
    # Test de requête API
    try:
        api_response = await page.evaluate('''
            async () => {
                const response = await fetch('/headers', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                return response.ok;
            }
        ''')
        
        if api_response:
            print('✅ Requête API réussie')
        else:
            print('❌ Requête API échouée')
    except Exception as e:
        print(f'❌ Erreur de requête API: {e}')
    
    await browser.close()
    await playwright.stop()

# Lancer le test
asyncio.run(test_complete_integration())
"
```

### Expected Results
- ✅ Navigation réussie
- ✅ Headers correctement transmis
- ✅ Requête API réussie
- ✅ Intégration complète fonctionnelle

---

## Troubleshooting

### Problèmes Courants

#### 1. Headers manquants
```bash
# Vérifier la configuration
python3 -c "from stealth_system import StealthIdentity; print(StealthIdentity().get_headers())"
```

#### 2. Erreurs Playwright
```bash
# Réinstaller Playwright
pip install playwright
playwright install chromium
```

#### 3. Détection par les sites
```bash
# Vérifier les headers Sec-Fetch-*
python3 -c "
from stealth_system import StealthIdentity
headers = StealthIdentity().get_headers()
sec_headers = {k: v for k, v in headers.items() if k.startswith('Sec-Fetch-')}
print('Headers Sec-Fetch-*:', sec_headers)
"
```

### Logs de Debug
```bash
# Activer les logs détaillés
export PYTHONPATH=/home/ubuntu/projects/shopshopshops/test/sem-scraper-final
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from stealth_system import StealthIdentity
identity = StealthIdentity()
headers = identity.get_headers()
"
```

---

## Validation Finale

### Checklist de Validation
- [ ] Headers de base générés correctement
- [ ] Rotation des headers fonctionnelle
- [ ] Intégration Playwright réussie
- [ ] Test anti-détection réussi
- [ ] Performance acceptable
- [ ] Intégration complète fonctionnelle

### Critères de Succès
- ✅ Tous les tests passent sans erreur
- ✅ Aucun signe de détection sur les sites de test
- ✅ Performance < 10ms par génération de headers
- ✅ Rotation < 100ms par rotation
- ✅ Intégration transparente avec le système existant

---

*Quickstart guide completed on 2025-09-19*


