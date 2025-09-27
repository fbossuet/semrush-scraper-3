# Spécification Technique : Refactoring Metrics Extractor

**Date** : 2025-01-18  
**Objectif** : Intégrer les fonctionnalités permettant de scraper le cpc dans `_extract_metrics_from_page()` 

## 🎯 Objectifs

- **Maintenir la robustesse** : scroll pour virtualisation, retry avec scroll
- **Conserver la précision** : sélecteurs CPC spécifiques, parsing numérique avancé
- **Nouvelle logique de calcul** : Algorithme de similarité phrase ↔ domaine avec seuil 70%
- **Fallback** : Valeur CPC existante en BDD si aucune correspondance ≥ 70%

## 🔧 Spécificartion Techniques

### 1. Algorithme de Similarité CPC (NOUVEAU)

#### 1.1 Principe de Fonctionnement
**Objectif** : Trouver la correspondance la plus précise entre le domaine de la boutique et les phrases extraites du grid CPC.

**Algorithme** :
1. **Extraction du domaine** : Sous-domaine extrait du `shop_url`
2. **Tokenisation intelligente** : Division des domaines composés (ex: "fashionnova" → ["fashion", "nova"])
3. **Calcul multi-méthodes** :
   - Correspondance exacte de tokens
   - Correspondance partielle (sous-chaînes)
   - Similarité Jaro-Winkler (chaînes complètes)
4. **Sélection** : Meilleure similarité parmi les méthodes
5. **Seuil** : 70% minimum requis
6. **Fallback** : Valeur CPC existante en BDD si aucune correspondance

#### 1.2 Fonctions Implémentées
```python
def tokenize_domain(domain: str) -> List[str]:
    """Tokenise un domaine en mots individuels avec gestion des mots composés"""

def calculate_domain_phrase_similarity(shop_url: str, phrase: str) -> float:
    """Calcule la similarité entre le domaine et la phrase (0.0 à 1.0)"""

async def extract_cpc_by_similarity(page, playwright_manager, session_manager, shop_url):
    """Extraction CPC avec algorithme de similarité et fallback BDD"""
```

#### 1.3 Exemple de Résultat
```
✅ Correspondance trouvée: 'cakes body' → 94.7%
✅ CPC extrait: 0.57 (keyword: cakes body)
```

### 2. Intégration des Fonctionnalités Avancées

#### 1.1 Scroll pour Virtualisation
**Source** : `extract_cpc_best_ratio()` lignes 405-423  
**Destination** : `_extract_metrics_from_page()`  
**Fonctionnalité** :
```javascript
// Méthode 1 : Scroll du conteneur SAP React
const cont = document.querySelector('[data-ui-name="Body"]') || document.scrollingElement || document.body;
let y = 0; let steps = 0;
const max = (cont.scrollHeight || 0) - (cont.clientHeight || 0);
while (y < max && steps < 8) { 
    y += Math.max(200, (cont.clientHeight||0)/2); 
    cont.scrollTo(0, y); 
    steps++; 
}

// Méthode 2 : Scroll de la fenêtre (fallback)
for _ in range(6):
    await page.evaluate('window.scrollBy(0, Math.max(300, window.innerHeight/2))')
    await asyncio.sleep(0.25)
```

#### 1.2 Sélecteurs CPC Spécifiques
**Source** : `extract_cpc_best_ratio()` lignes 441-448  
**Destination** : `_extract_metrics_from_page()`  
**Sélecteurs** :
```javascript
const rows = document.querySelectorAll('div[data-ui-name="Body.Row"]');
const kw   = q('div[name="phrase"] a');
const vol  = parseNum(q('div[name="volume"][role="gridcell"] [data-at="value-volume"]'));
const traf = parseNum(q('div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]'));
const cpcT = q('div[name="cpc"][role="gridcell"] [data-at="value-cpc"]');
```

#### 1.3 Parsing Numérique Avancé
**Source** : `extract_cpc_best_ratio()` lignes 428-439  
**Destination** : `_extract_metrics_from_page()`  
**Fonctionnalité** :
```javascript
const parseNum = (s) => {
    if (!s) return NaN;
    const t = s.trim().replace(/[,%]/g,'').replace(/[, ]/g,'');
    const m = t.match(/^([\d.]+)([KkMm])?$/);
    if (!m) {
        const v = parseFloat(t);
        return isFinite(v) ? v : NaN;
    }
    const n = parseFloat(m[1]);
    const mul = m[2] ? (m[2].toLowerCase()==='k' ? 1e3 : 1e6) : 1;
    return n * mul;
};
```

#### 1.4 Retry avec Scroll
**Source** : `extract_cpc_best_ratio()` lignes 456-469  
**Destination** : `_extract_metrics_from_page()`  
**Logique** :
```python
for attempt in range(3):
    best = await page.evaluate(eval_script)
    if best and best.get('cpc') is not None:
        break
    if attempt < 2:  # Don't scroll on last attempt
        await _scroll_grid()
        await asyncio.sleep(0.5)
```

#### 1.5 Logique de Calcul CPC
**Source** : `extract_cpc_best_ratio()` lignes 449-451  
**Destination** : `_extract_metrics_from_page()`  
**Algorithme** :
```javascript
const ratio = vol / traf;
if (!best || ratio > best.ratio) best = { keyword: kw, ratio, cpc, cpcRaw: cpcT };
```

#### 2.2 Modifier `extract_metrics()`
**Fichier** : `src/core/metrics_extractor.py`  
**Lignes** : 296-309  
**Modification** :
```python
# AVANT
cpc_data = await self.extract_cpc_best_ratio(page, playwright_manager, session_manager, domain)

# APRÈS
# L'extraction CPC est maintenant intégrée dans _extract_metrics_from_page()
# Plus besoin d'appel séparé
```

#### 2.3 Enrichir `_extract_metrics_from_page()`
**Fichier** : `src/core/metrics_extractor.py`  
**Action** : Intégrer les fonctionnalités avancées de CPC dans la méthode existante

#### 3 Workflow de navigation détaillé

##### 3.1 Workflow Principal Complet (Market-Overview + Overview)
```
1. ACCÈS À LA PAGE DE LOGIN
   ↓
   https://noxtools.com/secure/login
   ↓
2. AUTHENTIFICATION
   ↓
   Remplir formulaire (username/password)
   ↓
3. REDIRECTION VERS DASHBOARD
   ↓
   https://noxtools.com/secure/member
   ↓
4. TEST D'ACCÈS DIRECT À SEMRUSH
   ↓
   Tentative navigation vers Market-Overview
   ↓
5. VÉRIFICATION DE LA SESSION
   ↓
   Test Market-Overview → Vérification contenu page
   ↓
   ┌─────────────────────────────────────┐
   │ SI ÉCHEC DÉTECTÉ                   │
   │ ↓                                  │
   │ 6A. RETOUR À LA PAGE DE LOGIN      │
   │ ↓                                  │
   │ 7A. RÉAUTHENTIFICATION             │
   │ ↓                                  │
   │ 8A. RETOUR AU DASHBOARD            │
   │ ↓                                  │
   │ 9A. UTILISATION DU BRIDGE          │
   │ ↓                                  │
   │ https://semrush.noxtools.com/server1.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server2.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server3.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server4.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server5.php │
   │ ↓                                  │
   │ SI TOUS ÉCHEC → ERREUR CRITIQUE    │
   └─────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────┐
   │ SI SUCCÈS                           │
   │ ↓                                  │
   │ 6B. CONTINUER SANS BRIDGE          │
   │ ↓                                  │
   │ 7B. NAVIGATION VERS MARKET-OVERVIEW │
   │ ↓                                  │
   │ 8B. EXTRACTION DES MÉTRIQUES       │
   │ ↓                                  │
   │ 9B. NAVIGATION VERS OVERVIEW       │
   │ ↓                                  │
   │ 10B. EXTRACTION CPC                │
   └─────────────────────────────────────┘
```

##### 3.1.1 Workflow de Navigation Overview avec Fallback
```
APRÈS EXTRACTION MARKET-OVERVIEW
↓
NAVIGATION VERS OVERVIEW
↓
https://semrush1.semrush.pw/analytics/overview/
↓
VÉRIFICATION DE LA SESSION
↓
Test Overview → Vérification contenu page
↓
┌─────────────────────────────────────┐
│ SI ÉCHEC DÉTECTÉ                   │
│ ↓                                  │
│ RETOUR AU LOGIN                    │
│ ↓                                  │
│ RÉAUTHENTIFICATION                 │
│ ↓                                  │
│ DASHBOARD                          │
│ ↓                                  │
│ BRIDGE https://semrush.noxtools.com/server1.php │
│ ↓                                  │
│ SI ÉCHEC → BRIDGE server2.php      │
│ ↓                                  │
│ SI ÉCHEC → BRIDGE server3.php      │
│ ↓                                  │
│ SI ÉCHEC → BRIDGE server4.php      │
│ ↓                                  │
│ SI ÉCHEC → BRIDGE server5.php      │
│ ↓                                  │
│ SI TOUS ÉCHEC → ERREUR CRITIQUE    │
└─────────────────────────────────────┘
↓
┌─────────────────────────────────────┐
│ SI SUCCÈS                           │
│ ↓                                  │
│ EXTRACTION CPC SUR OVERVIEW        │
└─────────────────────────────────────┘
```

##### 3.2 Conditions de Détection d'Échec

**Session Expirée**
```
SI page_content contient :
- "Session expired"
- "access again from Dashboard"
- "session expired"
- "please login again"
- "authentication required"
→ ÉCHEC DÉTECTÉ
```

**Erreur d'Accès**
```
SI page_title contient :
- "403"
- "forbidden"
→ ÉCHEC DÉTECTÉ
```

**Page Vide/Erreur**
```
SI len(page_content) <= 1000 caractères
→ ÉCHEC DÉTECTÉ
```

**Exception de Navigation**
```
SI timeout ou erreur de chargement
→ ÉCHEC DÉTECTÉ
```

##### 3.3 Correspondance Serveurs avec URLs Complètes

**Pour Market-Overview :**
```
Bridge server1.php → https://semrush1.semrush.pw/analytics/traffic/market-overview/
Bridge server2.php → https://semrush2.semrush.pw/analytics/traffic/market-overview/
Bridge server3.php → https://semrush3.semrush.pw/analytics/traffic/market-overview/
Bridge server4.php → https://semrush4.semrush.pw/analytics/traffic/market-overview/
Bridge server5.php → https://semrush5.semrush.pw/analytics/traffic/market-overview/
```

**Pour Overview (CPC) :**
```
Bridge server1.php → https://semrush1.semrush.pw/analytics/overview/
Bridge server2.php → https://semrush2.semrush.pw/analytics/overview/
Bridge server3.php → https://semrush3.semrush.pw/analytics/overview/
Bridge server4.php → https://semrush4.semrush.pw/analytics/overview/
Bridge server5.php → https://semrush5.semrush.pw/analytics/overview/
```

##### 3.4 Workflow de Fallback Serveurs Complet

**Pour Market-Overview :**
```
ÉCHEC DÉTECTÉ SUR MARKET-OVERVIEW
↓
RETOUR AU LOGIN
↓
RÉAUTHENTIFICATION
↓
DASHBOARD
↓
BRIDGE https://semrush.noxtools.com/server1.php
↓
Navigation automatique vers https://semrush1.semrush.pw/analytics/traffic/market-overview/
↓
SI ÉCHEC → BRIDGE server2.php → https://semrush2.semrush.pw/analytics/traffic/market-overview/
↓
SI ÉCHEC → BRIDGE server3.php → https://semrush3.semrush.pw/analytics/traffic/market-overview/
↓
SI ÉCHEC → BRIDGE server4.php → https://semrush4.semrush.pw/analytics/traffic/market-overview/
↓
SI ÉCHEC → BRIDGE server5.php → https://semrush5.semrush.pw/analytics/traffic/market-overview/
↓
SI TOUS ÉCHEC → ERREUR CRITIQUE
```

**Pour Overview (CPC) :**
```
ÉCHEC DÉTECTÉ SUR OVERVIEW
↓
RETOUR AU LOGIN
↓
RÉAUTHENTIFICATION
↓
DASHBOARD
↓
BRIDGE https://semrush.noxtools.com/server1.php
↓
Navigation automatique vers https://semrush1.semrush.pw/analytics/overview/
↓
SI ÉCHEC → BRIDGE server2.php → https://semrush2.semrush.pw/analytics/overview/
↓
SI ÉCHEC → BRIDGE server3.php → https://semrush3.semrush.pw/analytics/overview/
↓
SI ÉCHEC → BRIDGE server4.php → https://semrush4.semrush.pw/analytics/overview/
↓
SI ÉCHEC → BRIDGE server5.php → https://semrush5.semrush.pw/analytics/overview/
↓
SI TOUS ÉCHEC → ERREUR CRITIQUE
```

##### 3.5 Maintien de Session entre Pages

**Critères de Maintien de Session :**
- **Même serveur** : Si Market-Overview est sur semrush1, Overview doit être sur semrush1
- **Même bridge** : Si bridge server1.php utilisé pour Market-Overview, utiliser server1.php pour Overview
- **Cookies partagés** : Les cookies de session sont maintenus entre les deux pages
- **Pas de changement de serveur** : Éviter semrush1 → semrush2 entre les pages

**Exemple de Maintien de Session :**
```
1. Market-Overview : https://semrush1.semrush.pw/analytics/traffic/market-overview/
   ↓ (maintien de session)
2. Overview : https://semrush1.semrush.pw/analytics/overview/
   ↓ (même serveur, même session)
3. Extraction CPC réussie
```

**Exemple de Fallback avec Maintien :**
```
1. Market-Overview : semrush1 (succès)
   ↓
2. Overview : semrush1 (échec session)
   ↓
3. Retour login → Bridge server1.php → semrush1/overview (succès)
   ↓
4. Extraction CPC réussie
```

#### 3.6 Méthodes à Modifier pour Workflow Complet

**Script principal à modifier : `main.py`**

**Méthodes Principales dans `main.py` :**
1. **`extract_metrics()`** : 
   - Intégrer navigation vers Market-Overview
   - Ajouter navigation vers Overview après extraction métriques
   - Gérer le maintien de session entre les deux pages

2. **`_extract_metrics_from_page()`** : 
   - Enrichir avec les fonctionnalités CPC avancées
   - Gérer l'extraction sur la page Overview

3. **`_navigate_to_overview()`** (nouvelle méthode dans `main.py`) :
   - Navigation vers Overview avec maintien de session
   - Gestion du fallback si session expirée
   - Utilisation du même serveur que Market-Overview

4. **`_extract_cpc_from_overview()`** (nouvelle méthode dans `main.py`) :
   - Extraction CPC avec scroll et retry
   - Parsing numérique avancé
   - Calcul du meilleur ratio CPC

#### 3.3 Fonctionnalités à Intégrer dans `_extract_metrics_from_page()`
1. **Scroll pour virtualisation** : Fonction `_scroll_grid()`
2. **Parsing numérique avancé** : Fonction `_parse_numeric()`
3. **Extraction CPC avec retry** : Logique intégrée dans la méthode

## 📋 Plan d'Implémentation

### Phase 1 : Préparation
1. **Backup** du code actuel
2. **Tests** de validation du comportement actuel
3. **Documentation** des fonctionnalités à conserver

### Phase 2 : Intégration Workflow Complet (dans `main.py`)
1. **Ajouter** les fonctionnalités avancées dans `_extract_metrics_from_page()` du script `main.py`
2. **Ajouter** la logique pour l'extraction CPC dans `main.py`
3. **Implémenter** `_navigate_to_overview()` avec maintien de session dans `main.py`
4. **Implémenter** `_extract_cpc_from_overview()` avec scroll et retry dans `main.py`
5. **Modifier** `extract_metrics()` dans `main.py` pour le workflow complet (Market-Overview → Overview)
6. **Implémenter** le workflow de fallback avec détection d'échec pour les deux pages dans `main.py`
7. **Intégrer** la correspondance serveurs (server1.php → semrush1, etc.) dans `main.py`
8. **Tester** le fallback automatique entre serveurs
9. **Tester** le maintien de session entre Market-Overview et Overview

### Phase 4 : Validation
1. **Tests** de fonctionnement complet
2. **Vérification** des performances
3. **Validation** de la robustesse

## 🎯 Résultats Attendus

### Enregistrement en Base de Données

#### Table Analytics - Champ CPC
**Destination** : Table `analytics` dans `trendtrack.db`  
**Champ** : `cpc` (type REAL)  
**Mapping** : `NOXTOOLS_TO_ANALYTICS_MAP['cpc'] = 'cpc'`

#### Format de Données CPC
```python
# Format attendu pour l'enregistrement
analytics_data = {
    'shop_id': shop_id,
    'cpc': float(cpc_value),  # Valeur numérique du CPC
    'scraping_status': 'completed',
    'updated_at': datetime.now(timezone.utc),
    # ... autres métriques
}
```

#### Requête SQL d'Enregistrement
```sql
INSERT OR REPLACE INTO analytics 
(shop_id, organic_traffic, bounce_rate, avg_visit_duration, branded_traffic, 
 conversion_rate, paid_search_traffic, visits, traffic, percent_branded_traffic, 
 cpc, scraping_status, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
```

#### Pipeline de Formatage CPC
```python
# Dans formatter.py - NOXTOOLS_TO_ANALYTICS_MAP
'cpc': 'cpc'  # Mapping direct

# Formatage spécifique CPC
elif noxtools_key == 'cpc':
    # CPC: keep as float (no special formatting needed)
    try:
        formatted[analytics_key] = float(str(value).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        formatted[analytics_key] = None
```

#### Validation d'Enregistrement
- ✅ **Type de données** : REAL (float) dans SQLite
- ✅ **Formatage** : Suppression des virgules et espaces
- ✅ **Gestion d'erreur** : NULL si conversion échoue
- ✅ **Timestamp** : `updated_at` automatique
- ✅ **Attribution du statut** : Voir règles ci-dessous

#### Règles d'Attribution du `scraping_status`
- **failed (par défaut)** : si aucun statut n'est explicitement fourni côté scraper
- **failed** : s'il manque au moins UNE métrique attendue parmi celles que ce scraper doit enregistrer dans `analytics` (ex. `visits`, `traffic`, `organic_traffic`, `paid_search_traffic`, `avg_visit_duration`, `bounce_rate`, `percent_branded_traffic`, `conversion_rate`, `cpc`)
- **completed** : uniquement si TOUTES les métriques attendues sont présentes et enregistrées au bon format en base de données

Exécution recommandée dans l'orchestrateur:
1. Construire l'objet `analytics_data` complet
2. Vérifier la présence/validité de chaque métrique attendue
3. Déterminer `scraping_status` selon les règles ci-dessus (default = `failed`)
4. Écrire dans `analytics` avec le statut calculé

#### Exemple d'Enregistrement Réussi
```python
# Données extraites
cpc_data = {
    'keyword': 'best keyword',
    'cpc': 2.45,
    'ratio': 0.85,
    'cpcRaw': '$2.45'
}

# Enregistrement en BDD
analytics_record = {
    'shop_id': 12345,
    'cpc': 2.45,  # Valeur formatée
    'scraping_status': 'completed',  # car toutes les métriques attendues sont présentes et valides
    'updated_at': '2025-01-18 15:30:00'
}
```

## ⚠️ Risques et Mitigation

### Risques
1. **Perte de fonctionnalités** : Fonctionnalités avancées non intégrées
2. **Régression** : Comportement différent après refactoring
3. **Complexité** : Code plus complexe à maintenir
4. **Fallback défaillant** : Échec du système de fallback entre serveurs
5. **Détection d'échec incorrecte** : Faux positifs ou faux négatifs

### Mitigation
1. **Tests exhaustifs** : Validation de chaque fonctionnalité
2. **Backup** : Possibilité de rollback
3. **Documentation** : Code commenté et documenté
4. **Validation utilisateur** : Tests sur le VPS avant déploiement
5. **Tests de fallback** : Validation du système de fallback avec tous les serveurs
6. **Monitoring** : Surveillance des détections d'échec en production

## 📝 Checklist de Validation

### Fonctionnalités à Vérifier
- [ ] Scroll pour virtualisation fonctionne
- [ ] Sélecteurs CPC spécifiques fonctionnent
- [ ] Parsing numérique avancé fonctionne
- [ ] Retry avec scroll fonctionne
- [ ] Logique de calcul CPC fonctionne
- [ ] Extraction des métriques fonctionne
- [ ] Pas de double navigation
- [ ] Enregistrement CPC en base de données
- [ ] Formatage correct des données CPC
- [ ] Mapping NOXTOOLS_TO_ANALYTICS_MAP fonctionne
- [ ] Status 'completed' après extraction CPC

### Référence des métriques attendues
Se référer à la liste unique dans `specs/006-noxtools-scraper/spec.md` (section "Métriques attendues pour ce scraper").

### Tests à Effectuer
- [ ] Test avec domaine `cakesbody.com`
- [ ] Test avec différents domaines
- [ ] Test de robustesse (erreurs réseau)
- [ ] Test de performance (temps d'exécution)
- [ ] Test de validation des données
- [ ] Test de maintien de session entre Market-Overview et Overview
- [ ] Test de fallback sur Overview avec même serveur
- [ ] Test de fallback sur Overview avec changement de serveur
- [ ] Test d'extraction CPC avec scroll et retry
- [ ] Test de parsing numérique avancé
- [ ] Test d'enregistrement CPC en base de données
- [ ] Test de formatage des données CPC
- [ ] Test de validation des données en BDD

## 🚀 Déploiement

### Prérequis
- ✅ Code source modifié et testé
- ✅ Tests de validation passés
- ✅ Documentation mise à jour
- ✅ Validation utilisateur

### Étapes
1. **Backup** du code actuel
2. **Déploiement** du code refactorisé
3. **Tests** de validation sur le VPS
4. **Monitoring** des performances
5. **Validation** utilisateur finale

---

**Cette spécification technique détaille précisément les modifications à apporter pour éliminer la duplication tout en conservant toutes les fonctionnalités avancées.**
