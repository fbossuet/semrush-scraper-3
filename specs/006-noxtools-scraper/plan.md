# Plan d'Implémentation : Scraper Noxtools

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [spec.md](./spec.md)  
**Input** : Spécification de fonctionnalité depuis `/specs/006-noxtools-scraper/spec.md`

## Résumé
Créer un nouveau scraper Noxtools dans le dossier `scraper-noxtools-final` qui reproduit les fonctionnalités du scraper SEM existant mais adapté pour Noxtools avec de nouveaux sélecteurs, une navigation vers un autre domaine, et des métriques spécifiques à Noxtools. **Problèmes identifiés** : Session expirée Semrush, URLs incohérentes, ✅ système de fallback serveurs dynamique implémenté.

## Contexte Technique
**Language/Version** : Python 3.x avec Playwright asyncio  
**Dépendances Principales** : Playwright, SQLite, asyncio, anti-détection  
**Stockage** : SQLite (base partagée avec TrendTrack et SEM)  
**Tests** : pytest, tests d'intégration  
**Plateforme Cible** : Linux VPS avec Xvfb  
**Type de Projet** : single (scraper autonome)  
**Objectifs de Performance** : Scraping parallèle, gestion des timeouts adaptatifs  
**Contraintes** : Anti-détection, navigation multi-domaines, session persistante, ✅ fallback serveurs dynamique implémenté  
**Échelle/Portée** : Scraping de centaines de boutiques avec métriques Noxtools

## Roadmap des Versions

### Version Alpha - Test et Validation
- Initialisation Playwright stealth headless
- Authentification via formulaire (nouveaux sélecteurs)
- Navigation vers Noxtools avec maintien de session/cookies inter-domaine
- Scraping des métriques (sans enregistrement BDD)
- Logs détaillés de validation
- **Retry session** : Détection session expirée et re-authentification complète
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 avec cohérence URLs (ServerManager implémenté)
- **Éligibilité shops** : Critères précis (shops.scraping_status ≠ "failed", details_scraping_status = "details_extracted", analytics.scraping_status = NULL)

### Version Beta - Formatage et Enregistrement
- Formatage des données selon standards
- Validation d’intégrité avant sauvegarde
- Enregistrement dans `analytics` avec correspondance `shops`
- Gestion robuste des erreurs de sauvegarde

### Version Finale - Optimisation et Parallélisation
- Optimisation performance et parallélisation par workers
- Timeouts adaptatifs avancés, throttling et backoff
- Monitoring de performance et préparation déploiement

## Inputs Requis par Version

### Alpha (à fournir/valider)
- ✅ Sélecteurs auth + navigation, URL finale, sélecteurs des métriques
- ✅ Credentials d'authentification Noxtools
- ✅ Domaine source Noxtools (URL de base)
- ✅ Sessions: gestion cookies entre domaines
- ✅ Anti-détection: User-Agents, headers, délais (ref. specs/002)
- ✅ Paramètres scraping: timeouts, retry, délais (ref. `sem-scraper-final/config.env`)
- ✅ **Inputs fournis** :
  - Page login: https://noxtools.com/secure/login
  - Sélecteurs: `#amember-login`, `#amember-pass`, `[type="submit"]`
  - Redirection: https://noxtools.com/secure/member
  - **ÉTAPE 1 - Overview (CPC)** : https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507
    - Sélecteurs Overview (SAP React grid) :
      - Lignes: `div[data-ui-name="Body.Row"]`
      - Keywords: `div[name="phrase"] a`
      - Volume: `div[name="volume"][role="gridcell"] [data-at="value-volume"]`
      - Traffic: `div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]`
      - CPC: `div[name="cpc"][role="gridcell"] [data-at="value-cpc"]`
    - Logique CPC : ratio = volume / trafficPercent → sélection max(ratio)
  - **ÉTAPE 2 - Market-Overview (Autres métriques)** : https://semrush1.semrush.pw/analytics/traffic/market-overview/?date=202507&q=cakesbody.com&searchType=domain&fid=1361959
    - Sélecteurs métriques (SAP React gridcell):
      - visits: `[data-ui-name="Flex"][role="gridcell"][name="entrances"][tabindex="-1"][aria-colindex="3"]`
      - organic: `[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchOrganic"][tabindex="-1"][aria-colindex="9"]`
      - paid: `[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchPaid"][tabindex="-1"][aria-colindex="11"]`
      - purchase conversion: `[data-ui-name="Flex"][role="gridcell"][name="purchasesPerVisit"][tabindex="-1"][aria-colindex="21"]`
      - avg visit duration: `[data-ui-name="Flex"][role="gridcell"][name="avgVisitDuration"][tabindex="-1"][aria-colindex="27"]`
      - bounce rate: `[data-ui-name="Flex"][role="gridcell"][name="bouncesPerVisit"][tabindex="-1"][aria-colindex="29"]`
  - Technologie: SAP React (extraction adaptée)

### Workflow en 2 Étapes Distinctes (Alpha)

#### **ÉTAPE 1 - Overview (CPC Extraction)**
- **Navigation** : Dashboard → Bridge `https://semrush.noxtools.com/server3.php` → Overview
- **URL** : `https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507`
- **Attentes** : `networkidle` + délai 2s
- **Extraction CPC** :
  - Lignes: `div[data-ui-name="Body.Row"]`
  - Keywords: `div[name="phrase"] a`
  - Volume: `div[name="volume"][role="gridcell"] [data-at="value-volume"]`
  - Traffic: `div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]`
  - CPC: `div[name="cpc"][role="gridcell"] [data-at="value-cpc"]`
  - **Logique** : ratio = volume / trafficPercent → sélection max(ratio)
- **Rate limiting** : limites/minute et burst

#### **ÉTAPE 2 - Market-Overview (Autres Métriques)**
- **Navigation** : Depuis Overview → Market-Overview avec FID
- **URL** : `https://semrush1.semrush.pw/analytics/traffic/market-overview/?date=202507&q=cakesbody.com&searchType=domain&fid=1361959`
- **Extraction** : Toutes les autres métriques (visits, organic, paid, etc.)
- **Remarque** : en Version Finale, ajouter un fallback automatique (domaines/passerelles alternatifs) si indisponible (cf. `NOX-FINAL-005`).

### Beta (à fournir/valider)
- Chemin de la BDD
- Mapping des champs (Noxtools → analytics)
- Règles de formatage et validation
- Schéma `analytics` (structure/contraintes/index)
- 1 métrique calculée à partir des données scrapées
- Gestion d’erreurs (fallbacks, valeurs par défaut)
- Métadonnées (timestamp ISO 8601 pour logs, SQLite DATE pour BDD, source, version scraper)

### Finale (à fournir/valider)
- Configuration des workers (nombre, répartition, priorités)
- KPIs performance à suivre, monitoring/alertes
- Paramètres de déploiement (environnement, prod)

## Références Config existantes (extraites)

### Anti-détection (specs/002-headers-anti-detection)
- Pools User-Agent réalistes (Chrome, Firefox, Safari)
- Headers navigation: Accept-Language, Accept-Encoding, Accept
- Headers sécurité: Sec-Fetch-*, Upgrade-Insecure-Requests
- Rotation configurable (défaut ~1h) + jitter aléatoire

### Paramètres Scraping (sem-scraper-final)
- Timeouts (config.env): Browser 60s, Page Load 90s, Navigation 120s
- Retry: 3 tentatives; délai entre requêtes: 2s
- Rate limiting (parallel_config.py): 60 req/min, burst 10; backoff 1s ×2 max 10s

### Schéma Analytics (specs/001-name-trendtrack-scraper/plan/data-model.md)
- Table `analytics` avec indexes `shop_id`, `scraping_status`, unique `shop_id`
- Champs numériques typés (INTEGER/NUMERIC) pour performance/qualité

## Propositions (Logs, Erreurs, Métadonnées)

### Logs
- Niveaux: DEBUG/INFO/WARNING/ERROR (configurable)
- Format: ISO 8601 timestamp, level, message; sortie console + fichier `logs/noxtools.log`
- Captures conditionnelles (screenshots) sur erreurs critiques (alpha/beta)

### Gestion des erreurs
- Classes d’erreurs: AuthError, NavigationError, SelectorError, RateLimitError, FormatError, SaveError
- Fallbacks: re-essais exponentiels, délais humains, valeurs par défaut pour champs non critiques
- Politique d’arrêt: continuer par boutique; compteur d’échecs max/session

### Métadonnées
- `scraper_source='noxtools'`, `scraper_version`, `scraped_at` (ISO 8601 UTC), `updated_at` (SQLite DATE)
- Conserver `session_id` et `worker_id` (version finale) pour traçabilité

## Vérification Constitution
*PORTE : Doit passer avant la Phase 0 recherche. Re-vérifier après la Phase 1 design.*

### Principes Fondamentaux Respectés
- ✅ **Documentation-First** : Spécification complète créée
- ✅ **VPS-Only Development** : Développement sur VPS uniquement
- ✅ **Validation Utilisateur** : Validation obligatoire pour chaque modification
- ✅ **Logs Immutables** : Conservation des messages de logs existants
- ✅ **Approche Adaptative** : Validation des métriques par comptage dynamique

### Contraintes Techniques Respectées
- ✅ **Stack Technologique** : Python + Playwright + SQLite
- ✅ **Standards de Performance** : Timeout adaptatif, workers intelligents
- ✅ **Workflow de Développement** : Contrôles qualité, rollback automatique
- ✅ **Gouvernance** : Constitution respectée, système de rollback opérationnel

## Structure du Projet

### Documentation (cette fonctionnalité)
```
specs/006-noxtools-scraper/
├── plan.md              # Ce fichier (sortie commande /plan)
├── research.md          # Sortie Phase 0 (commande /plan)
├── data-model.md        # Sortie Phase 1 (commande /plan)
├── quickstart.md        # Sortie Phase 1 (commande /plan)
├── contracts/           # Sortie Phase 1 (commande /plan)
└── tasks.md             # Sortie Phase 2 (commande /tasks - PAS créé par /plan)
```

### Code Source (racine du repository)
```
scraper-noxtools-final/
├── src/
│   ├── core/
│   │   ├── scraper.py           # Scraper principal Noxtools
│   │   ├── auth_manager.py      # Gestion authentification
│   │   ├── session_manager.py   # Gestion sessions multi-domaines
│   │   └── anti_detection.py   # Logique anti-détection
│   ├── models/
│   │   ├── boutique.py          # Modèle boutique Noxtools
│   │   └── metrics.py           # Modèle métriques Noxtools
│   ├── services/
│   │   ├── database.py          # Gestion base de données
│   │   └── metrics_extractor.py # Extraction métriques
│   └── utils/
│       ├── config.py            # Configuration
│       └── logger.py            # Logging
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Décision de Structure** : Option 1 (projet unique) - Scraper autonome avec structure modulaire

## Phase 0 : Recherche et Analyse
1. **Extraire les inconnues du Contexte Technique** :
   - Analyser le scraper SEM existant pour comprendre l'architecture
   - Identifier les sélecteurs DOM spécifiques à Noxtools
   - Rechercher les meilleures pratiques pour navigation multi-domaines
   - Analyser les métriques spécifiques à Noxtools

2. **Générer et dispatcher les agents de recherche** :
   ```
   Pour chaque inconnue dans le Contexte Technique :
     Tâche : "Rechercher {inconnue} pour le contexte scraper Noxtools"
   Pour chaque choix technologique :
     Tâche : "Trouver les meilleures pratiques pour {tech} dans le domaine scraping"
   ```

3. **Consolider les résultats** dans `research.md` avec le format :
   - Décision : [ce qui a été choisi]
   - Justification : [pourquoi choisi]
   - Alternatives considérées : [ce qui a été évalué]

**Sortie** : research.md avec toutes les inconnues résolues

## Phase 1 : Design et Contrats
*Prérequis : research.md complet*

1. **Extraire les entités de la spec de fonctionnalité** → `data-model.md` :
   - Nom d'entité, champs, relations
   - Règles de validation des exigences
   - Transitions d'état si applicable

2. **Générer les contrats API** depuis les exigences fonctionnelles :
   - Pour chaque action utilisateur → endpoint
   - Utiliser les patterns REST/GraphQL standards
   - Sortie schéma OpenAPI/GraphQL vers `/contracts/`

3. **Générer les tests de contrat** depuis les contrats :
   - Un fichier de test par endpoint
   - Assertion des schémas request/response
   - Les tests doivent échouer (pas d'implémentation encore)

4. **Extraire les scénarios de test** depuis les histoires utilisateur :
   - Chaque histoire → scénario de test d'intégration
   - Test quickstart = étapes de validation d'histoire

5. **Mettre à jour le fichier agent de manière incrémentale** (opération O(1)) :
   - Exécuter `.specify/scripts/bash/update-agent-context.sh cursor` pour votre assistant IA
   - Si existe : Ajouter seulement les NOUVELLES tech du plan actuel
   - Préserver les ajouts manuels entre les marqueurs
   - Mettre à jour les changements récents (garder les 3 derniers)
   - Garder sous 150 lignes pour l'efficacité des tokens
   - Sortie vers la racine du repository

**Sortie** : data-model.md, /contracts/*, tests qui échouent, quickstart.md, fichier spécifique à l'agent

## Phase 2 : Approche de Planification des Tâches
*Cette section décrit ce que la commande /tasks fera - NE PAS exécuter pendant /plan*

**Stratégie de Génération des Tâches** :
- Charger `.specify/templates/tasks-template.md` comme base
- Générer les tâches depuis les docs de design Phase 1 (contrats, modèle de données, quickstart)
- Chaque contrat → tâche de test de contrat [P]
- Chaque entité → tâche de création de modèle [P]
- Chaque histoire utilisateur → tâche de test d'intégration
- Tâches d'implémentation pour faire passer les tests

**Stratégie d'Ordre** :
- Ordre TDD : Tests avant implémentation
- Ordre de dépendance : Modèles avant services avant UI
- Marquer [P] pour exécution parallèle (fichiers indépendants)

**Sortie Estimée** : 25-30 tâches numérotées, ordonnées dans tasks.md

**IMPORTANT** : Cette phase est exécutée par la commande /tasks, PAS par /plan

## Phase 3+ : Implémentation Future
*Ces phases sont au-delà de la portée de la commande /plan*

**Phase 3** : Exécution des tâches (commande /tasks crée tasks.md)  
**Phase 4** : Implémentation (exécuter tasks.md en suivant les principes constitutionnels)  
**Phase 5** : Validation (exécuter tests, exécuter quickstart.md, validation performance)

## Suivi de Complexité
*Remplir SEULEMENT si la Vérification Constitution a des violations qui doivent être justifiées*

| Violation | Pourquoi Nécessaire | Alternative Plus Simple Rejetée Parce Que |
|-----------|---------------------|-------------------------------------------|
| [Aucune violation détectée] | [N/A] | [N/A] |

## Suivi des Progrès
*Cette checklist est mise à jour pendant le flux d'exécution*

**Statut des Phases** :
- [x] Phase 0 : Recherche complète (commande /plan)
- [x] Phase 1 : Design complet (commande /plan)
- [x] Phase 2 : Planification des tâches complète (commande /plan - décrire approche seulement)
- [ ] Phase 3 : Tâches générées (commande /tasks)
- [ ] Phase 4 : Implémentation complète
- [ ] Phase 5 : Validation passée

**Statut des Portes** :
- [x] Vérification Constitution Initiale : PASS
- [x] Vérification Constitution Post-Design : PASS
- [x] Toutes les inconnues résolues
- [x] Déviances de complexité documentées

---

*Basé sur Constitution v2.1.1 - Voir `/memory/constitution.md`*


**Statut des Phases** :
- [x] Phase 0 : Recherche complète (commande /plan)
- [x] Phase 1 : Design complet (commande /plan)
- [x] Phase 2 : Planification des tâches complète (commande /plan - décrire approche seulement)
- [ ] Phase 3 : Tâches générées (commande /tasks)
- [ ] Phase 4 : Implémentation complète
- [ ] Phase 5 : Validation passée

**Statut des Portes** :
- [x] Vérification Constitution Initiale : PASS
- [x] Vérification Constitution Post-Design : PASS
- [x] Toutes les inconnues résolues
- [x] Déviances de complexité documentées

---

*Basé sur Constitution v2.1.1 - Voir `/memory/constitution.md`*
