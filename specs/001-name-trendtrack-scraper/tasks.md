# Implementation Tasks: Scraper SEM Parallèle

**Feature**: Scraper SEM Parallèle  
**Branch**: `001-name-trendtrack-scraper`  
**Date**: 2025-09-16  
**Generated from**: plan.md, data-model.md, research.md, quickstart.md, contracts/openapi.yaml

## Task Overview

**Total Tasks**: 46  
**Parallel Tasks**: 15 (marked with [P])  
**Sequential Tasks**: 26  

**Stratégie d'Exécution**: Approche TDD avec tests avant implémentation, exécution ordonnée par dépendances, exécution parallèle quand possible.

## Corrections Appliquées

### ✅ T014-CORRECTION: Correction du comptage des métriques avg_visit_duration
**Date**: 2025-09-17  
**Problème**: La métrique `avg_visit_duration` affichait "Aucune tentative" malgré des données récupérées  
**Cause**: Incohérence entre les noms de clés dans `detailed_metrics` (`'avg_visit_duration'`) et les données du worker (`'average_visit_duration'`)  
**Solution**: 
- Correction de l'initialisation de `detailed_metrics` pour utiliser `'average_visit_duration'`
- Ajout du mapping inverse dans `data_names` pour l'affichage
- Nettoyage des logs de debug temporaires

**Fichiers modifiés**:
- `production_scraper_parallel.py`: Logique de comptage des métriques
- `launch_workers_by_status.py`: Agrégation et affichage des statistiques

**Résultat**: `avg_visit_duration` affiche maintenant correctement `📊 Total: 2 | Skipées: 1 | Succès: 1 | Échecs: 0 | Taux: 100.0%`

### ✅ T014-CORRECTION-2: Investigation problème conversion_rate React SPA
**Date**: 2025-09-17  
**Problème**: La métrique `conversion_rate` n'est jamais récupérée malgré des données visibles en frontend  
**Cause**: Page React SPA se charge mais le contenu est vide - problème de timing et de chargement asynchrone  
**Solution**: 
- Attente progressive pour React SPA (1s, 1.5s, 2s, 2.5s, 3s max)
- Détection des pages vides et attente supplémentaire (5s)
- Debug complet (URL, titre, contenu de la page)
- Vérification des données spécifiques au domaine

**Fichiers modifiés**:
- `production_scraper_parallel.py`: Amélioration du timing React SPA et détection des pages vides

**Résultat**: Correction du timing pour React SPA, détection des problèmes de permissions/session

## 🎯 **NOUVELLES TÂCHES - YEAR_FOUNDED**

### T051: Lancer le scraper TrendTrack pour alimenter la table shops
- **Objectif**: Alimenter la base de données avec des boutiques pour tester year_founded
- **Action**: Exécuter le scraper TrendTrack existant
- **Priorité**: P1
- **Dépendances**: Aucune

### T052: Vérifier que creationDate est bien extrait dans les nouvelles données
- **Objectif**: Confirmer que le scraper extrait bien creationDate (format MM/DD/YYYY)
- **Action**: Vérifier les données scrapées dans la table shops
- **Priorité**: P1
- **Dépendances**: T051

### T053: Tester la conversion creationDate → year_founded avec les scripts existants
- **Objectif**: Utiliser les scripts existants pour convertir creationDate en year_founded
- **Action**: Tester update_year_founded.py et get_shops_without_year_founded.py
- **Priorité**: P1
- **Dépendances**: T052

### T054: Nettoyer les fichiers temporaires créés
- **Objectif**: Supprimer les fichiers de test créés pendant le développement
- **Action**: Nettoyer /tmp/year_founded_dom_scraper.py et autres fichiers temporaires
- **Priorité**: P2
- **Dépendances**: T053

### T055: ✅ Implémenter le scraping des technologies (pixels Google/Facebook) - TERMINÉ
- **Objectif**: Récupérer les données du conteneur "technologies" dans l'interface TrendTrack
- **Action**: Analyser l'interface TrendTrack, ajouter des sélecteurs pour pixel_google et pixel_facebook
- **Contrainte**: Tout doit être fait en Python dans la mesure du possible
- **Priorité**: P1 - ✅ **TERMINÉ LE 18/09/2025**
- **Dépendances**: T051 (après avoir des données de test)
- **Résultat**: 
  - ✅ Scraper Python créé (`pixel_scraper_simple.py`)
  - ✅ Intégration TrendTrack complète avec authentification
  - ✅ Test réussi sur VPS (3 boutiques traitées, 100% de succès)
  - ✅ Champs `pixel_google` et `pixel_facebook` vérifiés en base (TEXT)
  - ✅ Heuristiques robustes pour détecter Google Analytics et Facebook Pixel
  - ✅ Sauvegarde automatique en base de données
  - ✅ Extraction de domaine corrigée (shopify.com, etsy.com, amazon.com)

### T056: ✅ Intégration complète du scraper de pixels dans le workflow principal - TERMINÉ
- **Objectif**: Intégrer le scraper de pixels directement dans TrendTrackExtractor pour automatisation complète
- **Action**: Modifier TrendTrackExtractor pour inclure automatiquement le scraping des pixels
- **Contrainte**: Intégration transparente sans casser le workflow existant
- **Priorité**: P1 - ✅ **TERMINÉ LE 18/09/2025**
- **Dépendances**: T055
- **Résultat**: 
  - ✅ TrendTrackExtractor modifié avec intégration des pixels
  - ✅ Scraper principal lance maintenant automatiquement : métriques de base + market + pixels
  - ✅ Sauvegarde automatique de l'ancienne version
  - ✅ Script de mise à jour créé et testé
  - ✅ Workflow unifié : `bash start-scraper.sh` → tout se lance automatiquement

### T057: Test et validation du scraper unifié en production
- **Objectif**: Tester le scraper unifié sur des données réelles en production
- **Action**: Lancer le scraper principal et valider que toutes les métriques sont extraites
- **Contrainte**: Validation manuelle des résultats par l'utilisateur
- **Priorité**: P1
- **Dépendances**: T056
- **Validation**: 
  - Tester le scraper principal avec `bash start-scraper.sh`
  - Vérifier que les métriques de base, market et pixels sont toutes extraites
  - Confirmer la sauvegarde complète en base de données
  - Valider les performances et la stabilité du workflow unifié

## Priorisation (P0/P1/P2)

- P0 (Critique, à exécuter en premier):
  - T074 (Audit du fonctionnement de l'API endpoint test)
  - T041 (Implémenter la métrique visits manquante)
  - T030 (Créer environnements de test et préproduction)
  - T031 (Ajouter un système de pause entre les requêtes API)
  - T032 (Refactoring authentification API pour TrendTrack)
  - T033 (Architecture Playwright headless + stealth pour TrendTrack)
  - T034 (Système de pauses aléatoires pour TrendTrack)
  - T001, T002 (Audit + comparaison BDD)
  - T006, T007, T008, T009 (Tests de régression/baseline)
  - T016 (Service de validation des métriques)
  - T015 (Service de gestion d'erreurs)
  - T021 (Intégration client API MyToolsPlan)
  - T073 (Vérification format ISO 8601 UTC pour toutes les dates en BDD)
r
- P1 (Important, après P0):
  - T035 (Architecture de fichiers claire pour TrendTrack)
  - T036 (Scraper recherche par domaine)
  - T037 (Intégration base de données pour recherche par domaine)
  - T038 (Tests de régression pour nouvelle fonctionnalité)
  - T010, T011, T012 (Entités et services de base si écarts détectés)
  - T013, T014 (Services scraping de base + workers parallèles)
  - T017, T018, T019, T020 (Endpoints API)

- P2 (Finition/optimisation):
  - T039 (Migration scraper traditionnel vers nouvelle architecture)
  - T040 (Documentation et déploiement)
  - T024, T025, T026, T027, T028 (Unitaires, perf, docs, E2E, déploiement)

## Phase 0: Audit du Projet Existant (REMPLACE le Setup)

### T001: Audit rapide du code et de la doc existants [P]
**Type**: Audit  
**Dependencies**: None  
**Files**: `sem-scraper-final/production_scraper_parallel.py`, `trendtrack-scraper-final/`, `ubuntu/README/*`, `.specify/memory/constitution.md`  
**Description**: Cartographier les composants déjà en place (scraper, APIs, DB, workers, logs) et vérifier leur cohérence avec la constitution `.specify`.

**Implementation**:
- Lister les points d’entrée (scripts de lancement, workers, endpoints)
- Vérifier la présence du système de rollback et l’état des logs
- Valider que la logique de validation métriques est en place et utilisée
- Noter les divergences doc ↔ code

**Validation**: Rapport d’audit bref (10 lignes) + liste de divergences, validés par l’utilisateur.

### T002: Vérification schémas BDD prod/test (sans migration) [P]
**Type**: Audit  
**Dependencies**: T001  
**Files**: `trendtrack-final-scraper/data/trendtrack.db`, `trendtrack-final-scraper/data/trendtrack_test.db`  
**Description**: Comparer les schémas des deux BDD, sans créer de nouvelles migrations.

**Implementation**:
- Exporter la structure des tables (shops, analytics, scraping_sessions, workers)
- Comparer colonnes, types, index
- Lister les écarts éventuels

**Validation**: Rapport de comparaison validé par l’utilisateur; aucune modification appliquée.

## Test Tasks (Régression sur existant)

### T003: Website Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_website_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité Website basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD Website (GET, POST, PUT, DELETE /websites)
- Valider que les schémas request/response correspondent à la spécification OpenAPI
- Tester le filtrage par statut et la pagination
- Tester la gestion d'erreurs (404, 400, 409)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T004: Metrics Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_metrics_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité Metrics basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD metrics (GET, PUT /websites/{id}/metrics)
- Valider le schéma des 8 métriques (organic_traffic, paid_search_traffic, visits, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, percent_branded_traffic)
- Tester les règles de validation des métriques
- Tester la gestion d'erreurs (404, 400)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T005: ScrapingSession Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_session_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité ScrapingSession basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD session (GET, POST, DELETE /scraping/sessions)
- Tester l'endpoint de statut de session (/scraping/sessions/{id}/status)
- Valider le schéma de session et les transitions de statut
- Tester la gestion d'erreurs (404, 400)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T006: Integration Test - Basic Website Scraping [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_basic_scraping.py`  
**Description**: Créer un test d'intégration pour le scénario de scraping de base d'un site web depuis quickstart.md.

**Implémentation**:
- Tester le scraping end-to-end d'un site web unique
- Valider la collecte de métriques et les mises à jour de statut
- Tester la création de session et le monitoring
- Valider les réponses des endpoints API

**Validation**: Doit passer sur le code actuel (sert de baseline), sinon ouvrir bug.

### T007: Integration Test - Parallel Worker Processing [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_parallel_workers.py`  
**Description**: Créer un test d'intégration pour le scénario de traitement parallèle de workers depuis quickstart.md.

**Implémentation**:
- Tester le traitement parallèle de plusieurs sites web
- Valider la distribution de charge des workers
- Tester le monitoring du progrès de session
- Valider le traitement concurrent

**Validation**: Doit passer sur le code actuel (baseline), sinon ouvrir bug.

### T008: Integration Test - Error Handling and Recovery [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_error_handling.py`  
**Description**: Créer un test d'intégration pour le scénario de gestion d'erreurs et de dégradation gracieuse depuis quickstart.md.

**Implémentation**:
- Tester la gestion des sites web invalides
- Valider la dégradation gracieuse avec des échecs partiels
- Tester le logging d'erreurs et les mises à jour de statut
- Valider la completion de session avec des résultats mixtes

**Validation**: Doit passer (baseline), sinon ouvrir bug.

### T009: Integration Test - Metric Validation [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_metric_validation.py`  
**Description**: Créer un test d'intégration pour la logique de validation des métriques depuis quickstart.md.

**Implémentation**:
- Tester la collecte des 8 métriques
- Valider la logique de statut (completed vs partial)
- Tester les métriques calculées (percent_branded_traffic)
- Valider les règles de validation des métriques

**Validation**: Doit passer (baseline), sinon ouvrir bug.

## Core Implementation Tasks

### T010: Website Entity Implementation
**Type**: Core  
**Dependencies**: T003  
**Files**: `models/website.py`, `services/website_service.py`  
**Description**: Implémenter l'entité Website et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle Website avec tous les champs de data-model.md
- Implémenter WebsiteService avec les opérations CRUD
- Ajouter les règles de validation pour shop_url, scraping_status, timestamps
- Implémenter la logique de transition de statut

**Validation**: Les tests de contrats T003 passent, l'entité Website fonctionne correctement.

### T011: Metrics Entity Implementation
**Type**: Core  
**Dependencies**: T004  
**Files**: `models/metrics.py`, `services/metrics_service.py`  
**Description**: Implémenter l'entité Metrics et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle Metrics avec les 8 champs de métriques
- Implémenter MetricsService avec les opérations CRUD
- Ajouter les règles de validation pour les champs numériques et les plages décimales
- Implémenter la logique de champ calculé (percent_branded_traffic)

**Validation**: Les tests de contrats T004 passent, l'entité Metrics fonctionne correctement.

### T012: ScrapingSession Entity Implementation
**Type**: Core  
**Dependencies**: T005  
**Files**: `models/scraping_session.py`, `services/session_service.py`  
**Description**: Implémenter l'entité ScrapingSession et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle ScrapingSession avec tous les champs
- Implémenter SessionService avec les opérations CRUD
- Ajouter les règles de validation pour worker_count, websites_per_worker
- Implémenter la gestion du statut de session

**Validation**: Les tests de contrats T005 passent, l'entité ScrapingSession fonctionne correctement.

### T013: Basic Scraping Service Implementation
**Type**: Core  
**Dependencies**: T006, T010, T011  
**Files**: `services/scraping_service.py`  
**Description**: Implémenter le service de scraping de base pour le traitement d'un site web unique.

**Implémentation**:
- Créer ScrapingService avec traitement d'un site web unique
- Implémenter l'authentification MyToolsPlan et la gestion de session
- Ajouter la collecte de métriques de base (APIs + DOM scraping)
- Implémenter la logique de mise à jour de statut

**Validation**: Le test d'intégration T006 passe, le scraping de base fonctionne.

### T014: Parallel Worker Service Implementation
**Type**: Core  
**Dependencies**: T007, T012, T013  
**Files**: `services/worker_service.py`, `workers/parallel_worker.py`  
**Description**: Implémenter le service de workers parallèles pour le traitement concurrent.

**Implémentation**:
- Créer WorkerService avec la logique de traitement parallèle
- Implémenter la classe ParallelWorker avec asyncio
- Ajouter la gestion du pool de workers et la distribution de charge
- Implémenter le suivi du progrès de session

**Validation**: Le test d'intégration T007 passe, le traitement parallèle fonctionne.

### T015: Error Handling Service Implementation
**Type**: Core  
**Dependencies**: T008, T013  
**Files**: `services/error_handling_service.py`  
**Description**: Implémenter une gestion d'erreurs complète et une dégradation gracieuse.

**Implémentation**:
- Créer ErrorHandlingService avec la logique de retry
- Implémenter la dégradation gracieuse pour les échecs partiels
- Ajouter un logging d'erreurs complet
- Implémenter les mécanismes de récupération d'erreurs

**Validation**: Le test d'intégration T008 passe, la gestion d'erreurs fonctionne correctement.

### T016: Metric Validation Service Implementation
**Type**: Core  
**Dependencies**: T009, T011  
**Files**: `services/metric_validation_service.py`  
**Description**: Implémenter la logique de validation adaptative des métriques.

**Implémentation**:
- Créer MetricValidationService avec validation dynamique
- Implémenter la logique de validation des 8 métriques
- Ajouter la détermination de statut (completed/partial/failed/na)
- Implémenter la validation des métriques calculées

**Validation**: Le test d'intégration T009 passe, la validation des métriques fonctionne correctement.

## API Implementation Tasks

### T017: Website API Endpoints Implementation
**Type**: API  
**Dependencies**: T010  
**Files**: `api/website_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité Website.

**Implémentation**:
- Implémenter GET /websites (liste avec filtrage)
- Implémenter POST /websites (création)
- Implémenter GET /websites/{id} (obtenir détails)
- Implémenter PUT /websites/{id} (mise à jour)
- Implémenter DELETE /websites/{id} (suppression)

**Validation**: Tous les endpoints API Website fonctionnent correctement, correspondent au contrat OpenAPI.

### T018: Metrics API Endpoints Implementation
**Type**: API  
**Dependencies**: T011  
**Files**: `api/metrics_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité Metrics.

**Implémentation**:
- Implémenter GET /websites/{id}/metrics (obtenir métriques)
- Implémenter PUT /websites/{id}/metrics (mettre à jour métriques)
- Ajouter une gestion d'erreurs et validation appropriées
- S'assurer que les schémas de réponse correspondent à OpenAPI

**Validation**: Tous les endpoints API Metrics fonctionnent correctement, correspondent au contrat OpenAPI.

### T019: ScrapingSession API Endpoints Implementation
**Type**: API  
**Dependencies**: T012  
**Files**: `api/session_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité ScrapingSession.

**Implémentation**:
- Implémenter GET /scraping/sessions (lister sessions)
- Implémenter POST /scraping/sessions (démarrer session)
- Implémenter GET /scraping/sessions/{id} (obtenir détails)
- Implémenter DELETE /scraping/sessions/{id} (annuler session)
- Implémenter GET /scraping/sessions/{id}/status (obtenir statut)

**Validation**: Tous les endpoints API ScrapingSession fonctionnent correctement, correspondent au contrat OpenAPI.

### T020: Health Check API Endpoint Implementation
**Type**: API  
**Dependencies**: None  
**Files**: `api/health_endpoints.py`  
**Description**: Implémenter l'endpoint de vérification de santé.

**Implémentation**:
- Implémenter l'endpoint GET /health
- Ajouter la vérification de connectivité base de données
- Ajouter la validation du statut système
- Retourner le statut de santé approprié

**Validation**: L'endpoint de vérification de santé retourne le statut correct.

## Integration Tasks

### T021: MyToolsPlan API Client Integration
**Type**: Integration  
**Dependencies**: T013  
**Files**: `clients/mytoolsplan_client.py`  
**Description**: Implémenter le client API MyToolsPlan avec authentification et gestion de session.

**Implémentation**:
- Créer MyToolsPlanClient avec authentification
- Implémenter la synchronisation de cookies entre domaines
- Ajouter les endpoints API pour organic.Summary, organic.OverviewTrend, engagement
- Implémenter le système de fallback (sam2.mytoolsplan.xyz)

**Validation**: Les APIs MyToolsPlan s'intègrent correctement, l'authentification fonctionne.

### T022: Database Integration Service
**Type**: Integration  
**Dependencies**: T010, T011, T012  
**Files**: `services/database_service.py`  
**Description**: Implémenter l'intégration base de données avec support de double base de données.

**Implémentation**:
- Créer DatabaseService avec basculement base de données production/test
- Implémenter le pool de connexions et la gestion de transactions
- Ajouter le support de migration de base de données
- Implémenter les procédures de sauvegarde et récupération

**Validation**: Les opérations de base de données fonctionnent correctement sur les deux bases.

### T023: Logging and Monitoring Integration
**Type**: Integration  
**Dependencies**: T015  
**Files**: `services/logging_service.py`, `monitoring/metrics_collector.py`  
**Description**: Implémenter un logging et monitoring complets.

**Implémentation**:
- Créer LoggingService avec logging structuré
- Implémenter le monitoring pour les performances de scraping
- Ajouter le suivi d'erreurs et l'alerte
- Implémenter les outils d'analyse de logs et de débogage

**Validation**: Le logging et monitoring fonctionnent correctement, fournissent des insights utiles.

### T031: Système de pause/throttling entre requêtes API (anti-détection) [P0]
**Type**: Integration  
**Dependencies**: T021  
**Files**: `clients/mytoolsplan_client.py`, `parallel_config.py`, `production_scraper_parallel.py`  
**Description**: Ajouter un système de pauses intelligentes (throttling + jitter) entre les requêtes API pour réduire le risque de détection/ban.

**Implémentation**:
- Introduire des délais aléatoires bornés (ex: base 300-800ms + jitter) entre appels API
- Backoff adaptatif sur erreurs 429/5xx (ex: 1s, 2s, 4s, max 10s) avec limite de tentatives
- Respecter un budget de requêtes par fenêtre (token bucket simple en mémoire)
- Paramétrer via `parallel_config.py` (seuils, bornes, max backoff)
- Journaliser les pauses appliquées (sans modifier les messages de logs existants)

**Validation**: Taux d'erreurs 429 en baisse significative sur un run de test; pas d'impact notable sur le débit global (valider sur quickstart scénario 5 et runs partiels).

## Nouvelles Tâches - Fonctionnalité Recherche par Domaine

### T032: Refactoring authentification API pour TrendTrack [P0]
**Type**: Core  
**Dependencies**: T021  
**Files**: `trendtrack-scraper-final/auth/api_auth_client.py`, `trendtrack-scraper-final/auth/dom_auth_client.py`  
**Description**: Remplacer l'authentification DOM par une authentification API pour TrendTrack.

**Implémentation**:
- Créer `api_auth_client.py` avec la requête API de login fournie
- Créer `dom_auth_client.py` pour maintenir la compatibilité (legacy)
- Implémenter la gestion des tokens/sessions API
- Ajouter la validation des réponses d'authentification
- Maintenir la compatibilité avec l'existant

**Validation**: Authentification API fonctionne, compatibilité maintenue avec scraper traditionnel.

### T033: Architecture Playwright headless + stealth pour TrendTrack [P0]
**Type**: Core  
**Dependencies**: T032  
**Files**: `trendtrack-scraper-final/browser/stealth_browser.py`, `trendtrack-scraper-final/browser/legacy_browser.py`  
**Description**: Implémenter Playwright headless avec configuration stealth pour TrendTrack.

**Implémentation**:
- Créer `stealth_browser.py` avec configuration anti-détection
- Ajouter user-agent rotation, viewport randomisation
- Implémenter la gestion des cookies et localStorage
- Créer `legacy_browser.py` pour compatibilité
- Configuration via `trendtrack_config.py`

**Validation**: Navigation furtive fonctionne, pas de détection anti-bot.

### T034: Système de pauses aléatoires pour TrendTrack [P0]
**Type**: Core  
**Dependencies**: T033  
**Files**: `trendtrack-scraper-final/utils/anti_detection.py`, `trendtrack-scraper-final/config/stealth_config.py`  
**Description**: Implémenter un système de pauses aléatoires pour éviter la détection.

**Implémentation**:
- Créer `anti_detection.py` avec pauses configurables
- Implémenter jitter aléatoire (ex: 1-3s + random)
- Ajouter pauses entre requêtes et entre pages
- Configuration via `stealth_config.py`
- Logging des pauses appliquées

**Validation**: Pauses appliquées correctement, pas d'impact sur la performance.

### T035: Architecture de fichiers claire pour TrendTrack [P1]
**Type**: Architecture  
**Dependencies**: T032, T033, T034  
**Files**: `trendtrack-scraper-final/` (restructuration)  
**Description**: Restructurer l'architecture de fichiers pour séparer clairement les responsabilités.

**Implémentation**:
```
trendtrack-scraper-final/
├── auth/                    # Authentification
│   ├── api_auth_client.py
│   └── dom_auth_client.py
├── browser/                 # Gestion navigateur
│   ├── stealth_browser.py
│   └── legacy_browser.py
├── scrapers/               # Scrapers
│   ├── traditional/        # Scraper traditionnel
│   └── domain_search/      # Nouvelle fonctionnalité
├── utils/                  # Utilitaires
│   ├── anti_detection.py
│   └── selectors.py
├── config/                 # Configuration
│   ├── stealth_config.py
│   └── trendtrack_config.py
└── legacy/                 # Code legacy (à migrer)
```

**Validation**: Architecture claire, séparation des responsabilités, pas de régression.

### T036: Scraper recherche par domaine [P1]
**Type**: Core  
**Dependencies**: T035  
**Files**: `trendtrack-scraper-final/scrapers/domain_search/domain_scraper.py`  
**Description**: Implémenter le scraper de recherche par domaine spécifique.

**Implémentation**:
- Créer `domain_scraper.py` pour recherche par domaine
- Réutiliser les sélecteurs HTML existants
- Implémenter la logique de recherche ciblée (1 domaine à la fois)
- Extraire la première ligne correspondante du tableau
- Intégrer le système de pauses aléatoires

**Validation**: Recherche par domaine fonctionne, données extraites correctement.

### T037: Intégration base de données pour recherche par domaine [P1]
**Type**: Integration  
**Dependencies**: T036  
**Files**: `trendtrack-scraper-final/database/domain_integration.py`  
**Description**: Intégrer les résultats de recherche par domaine dans la même base que le scraper traditionnel.

**Implémentation**:
- Créer `domain_integration.py` pour l'intégration BDD
- Réutiliser les tables `shops` et `analytics` existantes
- Implémenter la logique de détection de doublons
- Ajouter le champ `search_method` (traditional/domain_search)
- Maintenir la cohérence des données

**Validation**: Données stockées correctement, pas de doublons, cohérence maintenue.

### T038: Tests de régression pour nouvelle fonctionnalité [P1]
**Type**: Test  
**Dependencies**: T037  
**Files**: `trendtrack-scraper-final/tests/test_domain_search.py`  
**Description**: Créer des tests pour la nouvelle fonctionnalité de recherche par domaine.

**Implémentation**:
- Tester l'authentification API
- Tester la recherche par domaine
- Tester l'extraction des données
- Tester l'intégration base de données
- Tester le système anti-détection

**Validation**: Tous les tests passent, couverture > 90%.

### T039: Migration scraper traditionnel vers nouvelle architecture [P2]
**Type**: Migration  
**Dependencies**: T038  
**Files**: `trendtrack-scraper-final/scrapers/traditional/`  
**Description**: Migrer le scraper traditionnel vers la nouvelle architecture.

**Implémentation**:
- Migrer `smart_scraper_intelligent.py` vers `traditional/`
- Adapter pour utiliser la nouvelle authentification API
- Intégrer le système de pauses aléatoires
- Maintenir la compatibilité avec l'existant
- Tests de régression

**Validation**: Scraper traditionnel fonctionne avec nouvelle architecture.

### T040: Documentation et déploiement [P2]
**Type**: Documentation  
**Dependencies**: T039  
**Files**: `trendtrack-scraper-final/docs/`, `trendtrack-scraper-final/README.md`  
**Description**: Documenter la nouvelle fonctionnalité et préparer le déploiement.

**Implémentation**:
- Documenter l'architecture de fichiers
- Créer le guide d'utilisation
- Documenter les nouvelles configurations
- Préparer les scripts de déploiement
- Mettre à jour le README

**Validation**: Documentation complète, déploiement prêt.

## Tâches de Gouvernance & Validation

### T029: Proposition d’alignement schéma Prod/Test (validation avant migration)
**Type**: Gouvernance/Validation  
**Dependencies**: T002  
**Files**: `specs/001-name-trendtrack-scraper/plan/db-schema-compare.md`, `specs/001-name-trendtrack-scraper/plan/data-model.md`  
**Description**: Préparer une proposition d’alignement des schémas Prod/Test, soumise à validation avant toute migration.

**Implémentation**:
- Synthétiser les écarts (types, colonnes, index) à partir de `db-schema-compare.md`
- Proposer un schéma cible unique (types stricts, index minimaux, champs retenus)
- Documenter les impacts potentiels (lecture/écriture API, scripts, performances)
- Définir un plan de migration sécurisé (étapes, rollback, validations)

**Validation**: Validation explicite de l’utilisateur sur la proposition (OK/KO) avant exécution de toute migration.

## Polish Tasks

### T024: Unit Tests for All Services [P]
**Type**: Polish  
**Dependencies**: T010-T016  
**Files**: `tests/unit/test_*.py`  
**Description**: Créer des tests unitaires complets pour tous les services.

**Implémentation**:
- Créer des tests unitaires pour WebsiteService, MetricsService, SessionService
- Créer des tests unitaires pour ScrapingService, WorkerService, ErrorHandlingService
- Créer des tests unitaires pour MetricValidationService
- Ajouter le reporting de couverture de tests

**Validation**: Tous les tests unitaires passent, couverture > 90%.

### T025: Performance Optimization [P]
**Type**: Polish  
**Dependencies**: T014, T021  
**Files**: `services/performance_service.py`  
**Description**: Optimiser les performances pour le traitement parallèle et les appels API.

**Implémentation**:
- Optimiser les requêtes de base de données et l'indexation
- Implémenter le pool de connexions et la mise en cache
- Optimiser les performances des workers parallèles
- Ajouter le monitoring de performance et les métriques

**Validation**: Les performances répondent aux exigences (1-2 min/site web, 95%+ succès API).

### T026: Documentation and API Documentation [P]
**Type**: Polish  
**Dependencies**: T017-T020  
**Files**: `docs/`, `README.md`  
**Description**: Créer une documentation complète et une documentation API.

**Implémentation**:
- Créer la documentation API avec des exemples
- Créer le guide utilisateur et le guide de dépannage
- Créer la documentation développeur
- Mettre à jour le README avec les instructions de configuration et d'utilisation

**Validation**: La documentation est complète et précise.

### T027: End-to-End Validation [P]
**Type**: Polish  
**Dependencies**: T006-T009  
**Files**: `tests/e2e/test_full_scraping_flow.py`  
**Description**: Créer des tests de validation end-to-end pour le flux de scraping complet.

**Implémentation**:
- Créer un test E2E pour le workflow de scraping complet
- Tester les 5 scénarios de quickstart.md
- Valider les exigences de performance
- Tester les scénarios d'erreur et la récupération

**Validation**: Tous les tests E2E passent, le système fonctionne end-to-end.

### T028: Production Deployment Preparation
**Type**: Polish  
**Dependencies**: T021-T023  
**Files**: `deployment/`, `docker/`  
**Description**: Préparer le système pour le déploiement en production sur VPS.

**Implémentation**:
- Créer les scripts de déploiement et la configuration
- Configurer les variables d'environnement de production
- Créer les procédures de sauvegarde et récupération
- Configurer le monitoring et l'alerte

**Validation**: Le système est prêt pour le déploiement en production.

## Parallel Execution Examples

### Phase 1: Configuration et Tests (Parallèle)
```bash
# Exécuter les tâches de configuration
Tâche T001: Configuration de l'environnement et dépendances
Tâche T002: Configuration du schéma de base de données [P]

# Exécuter les tests de contrats en parallèle
Tâche T003: Tests de contrats de l'entité Website [P]
Tâche T004: Tests de contrats de l'entité Metrics [P]
Tâche T005: Tests de contrats de l'entité ScrapingSession [P]

# Exécuter les tests d'intégration en parallèle
Tâche T006: Test d'intégration - Scraping de base de site web [P]
Tâche T007: Test d'intégration - Traitement parallèle de workers [P]
Tâche T008: Test d'intégration - Gestion d'erreurs et récupération [P]
Tâche T009: Test d'intégration - Validation des métriques [P]
```

### Phase 2: Implémentation Core (Séquentielle)
```bash
# Entités core (séquentiel à cause des dépendances)
Tâche T010: Implémentation de l'entité Website
Tâche T011: Implémentation de l'entité Metrics
Tâche T012: Implémentation de l'entité ScrapingSession

# Services core (séquentiel à cause des dépendances)
Tâche T013: Implémentation du service de scraping de base
Tâche T014: Implémentation du service de workers parallèles
Tâche T015: Implémentation du service de gestion d'erreurs
Tâche T016: Implémentation du service de validation des métriques
```

### Phase 3: Implémentation API (Parallèle)
```bash
# Endpoints API (parallèle - fichiers différents)
Tâche T017: Implémentation des endpoints API Website [P]
Tâche T018: Implémentation des endpoints API Metrics [P]
Tâche T019: Implémentation des endpoints API ScrapingSession [P]
Tâche T020: Implémentation de l'endpoint API de vérification de santé [P]
```

### Phase 4: Intégration (Séquentielle)
```bash
# Services d'intégration (séquentiel à cause des dépendances)
Tâche T021: Intégration du client API MyToolsPlan
Tâche T022: Service d'intégration de base de données
Tâche T023: Intégration du logging et monitoring
```

### Phase 5: Finition (Parallèle)
```bash
# Tâches de finition (parallèle - fichiers différents)
Tâche T024: Tests unitaires pour tous les services [P]
Tâche T025: Optimisation des performances [P]
Tâche T026: Documentation et documentation API [P]
Tâche T027: Validation end-to-end [P]
Tâche T028: Préparation du déploiement en production
```

## Tâches de Correction (P0 - Critique)

### T041: Implémenter la métrique visits manquante
**Type**: Correction  
**Dependencies**: T014 (Correction avg_visit_duration)  
**Files**: `production_scraper_parallel.py`, `launch_workers_by_status.py`  
**Description**: La métrique `visits` affiche "Aucune tentative" car elle n'est pas implémentée dans le scraper.  
**Problème**: Métrique importante manquante dans les statistiques de scraping.  
**Solution**: 
- Analyser où la métrique `visits` devrait être récupérée (API ou DOM scraping)
- Implémenter la logique de récupération
- Ajouter la métrique dans `format_analytics_for_api()`
- Tester et valider le fonctionnement

**Acceptance Criteria**:
- [ ] La métrique `visits` n'affiche plus "Aucune tentative"
- [ ] Les données de `visits` sont correctement récupérées et stockées
- [ ] Les statistiques de comptage incluent `visits`
- [ ] Tests de validation passent

## Nouvelles Tâches - Migration Base de Données

### T046: Migration des types de données [P0]
**Type**: Core  
**Dependencies**: T045  
**Files**: `trendtrack-scraper-final/data/migration_*.sql`  
**Description**: Corriger les 7 types de données incorrects identifiés dans l'analyse.
**Implémentation**:
```sql
-- Table shops
ALTER TABLE shops ALTER COLUMN monthly_visits TYPE INTEGER;
ALTER TABLE shops ALTER COLUMN live_ads TYPE TEXT;
ALTER TABLE shops ALTER COLUMN page_number TYPE TEXT;
ALTER TABLE shops ALTER COLUMN scraped_at TYPE TEXT;
ALTER TABLE shops ALTER COLUMN updated_at TYPE DATE;
ALTER TABLE shops ALTER COLUMN creation_date TYPE DATE;
ALTER TABLE shops ALTER COLUMN year_founded TYPE DATE;

-- Table analytics
ALTER TABLE analytics ALTER COLUMN organic_traffic TYPE INTEGER;
ALTER TABLE analytics ALTER COLUMN bounce_rate TYPE NUMERIC;
ALTER TABLE analytics ALTER COLUMN branded_traffic TYPE INTEGER;
ALTER TABLE analytics ALTER COLUMN visits TYPE INTEGER;
ALTER TABLE analytics ALTER COLUMN traffic TYPE INTEGER;
ALTER TABLE analytics ALTER COLUMN paid_search_traffic TYPE INTEGER;
ALTER TABLE analytics ALTER COLUMN percent_branded_traffic TYPE NUMERIC;
ALTER TABLE analytics ALTER COLUMN updated_at TYPE DATE;
```

### T047: Ajout des champs manquants [P1]
**Type**: Core  
**Dependencies**: T046  
**Files**: `trendtrack-scraper-final/data/migration_*.sql`  
**Description**: Ajouter les 11 champs manquants identifiés dans l'analyse.
**Implémentation**:
```sql
-- Nouveaux champs shops (10 champs)
ALTER TABLE shops ADD COLUMN total_products INTEGER;
ALTER TABLE shops ADD COLUMN pixel_google INTEGER;
ALTER TABLE shops ADD COLUMN pixel_facebook INTEGER;
ALTER TABLE shops ADD COLUMN aov NUMERIC;
ALTER TABLE shops ADD COLUMN market_us NUMERIC;
ALTER TABLE shops ADD COLUMN market_uk NUMERIC;
ALTER TABLE shops ADD COLUMN market_de NUMERIC;
ALTER TABLE shops ADD COLUMN market_ca NUMERIC;
ALTER TABLE shops ADD COLUMN market_au NUMERIC;
ALTER TABLE shops ADD COLUMN market_fr NUMERIC;

-- Nouveau champ analytics (1 champ)
ALTER TABLE analytics ADD COLUMN cpc NUMERIC;
```

### T048: Mise à jour du code de scraping [P1]
**Type**: Core  
**Dependencies**: T047  
**Files**: `trendtrack-scraper-final/scrapers/`, `trendtrack-scraper-final/src/`  
**Description**: Adapter tous les scrapers pour les nouveaux types et champs.
**Implémentation**:
- Modifier les scrapers JavaScript (TrendTrack)
- Modifier les scrapers Python (MyToolsPlan, Domain Search)
- Adapter les types de données dans le code
- Ajouter la logique pour alimenter les nouveaux champs
- Mettre à jour les requêtes SQL

### T049: Script de migration de base de données [P0]
**Type**: Core  
**Dependencies**: T048  
**Files**: `trendtrack-scraper-final/data/migrate_to_final_structure.py`  
**Description**: Créer un script complet de migration de la structure actuelle vers la finale.
**Implémentation**:
- Script Python avec sauvegarde automatique
- Migration des types de données
- Ajout des nouveaux champs
- Validation de l'intégrité des données
- Rollback en cas d'erreur
- Tests de validation post-migration

### T050: Validation des données après migration [P1]
**Type**: Test  
**Dependencies**: T049  
**Files**: `trendtrack-scraper-final/test_migration_validation.py`  
**Description**: Vérifier que tous les champs sont correctement alimentés après migration.
**Implémentation**:
- Tests de validation des types
- Tests de validation des nouveaux champs
- Tests de performance post-migration
- Tests d'intégrité des données
- Comparaison avant/après migration

### T073: Vérification format ISO 8601 UTC pour toutes les dates en BDD [P0]
**Type**: Correction  
**Dependencies**: T049  
**Files**: `trendtrack-scraper-final/`, `sem-scraper-final/`  
**Description**: Vérifier que toutes les dates enregistrées en base de données sont au format ISO 8601 UTC timestamp.
**Problème**: Incohérence dans les formats de dates entre les scrapers TrendTrack et SEM.
**Solution**: 
- Auditer tous les enregistrements de dates dans le code
- Vérifier les formats utilisés (datetime.now(), CURRENT_TIMESTAMP, etc.)
- Standardiser sur le format ISO 8601 UTC (ex: "2025-09-18T10:30:45.123Z")
- Corriger tous les scrapers (TrendTrack JavaScript + SEM Python)
- Tests de validation des formats de dates

**Acceptance Criteria**:
- [ ] Toutes les dates en BDD sont au format ISO 8601 UTC
- [ ] Le code TrendTrack utilise le format ISO 8601 UTC
- [ ] Le code SEM utilise le format ISO 8601 UTC
- [ ] Tests de validation des formats de dates passent
- [ ] Documentation des formats de dates mise à jour

### T074: Audit du fonctionnement de l'API endpoint test [P0]
**Type**: Audit  
**Dependencies**: Aucune  
**Files**: `http://37.59.102.7:8001/test/shops/with-analytics-ordered?since=2025-07-10T00:00:00Z`  
**Description**: Auditer le fonctionnement de l'API endpoint de test pour valider la qualité des données et la performance.
**Objectif**: S'assurer que l'API de test fonctionne correctement et fournit des données cohérentes pour l'environnement de test.

**Implémentation**:
- Tester l'endpoint API avec différents paramètres de filtrage
- Valider la structure des données retournées (180 boutiques avec métriques complètes)
- Vérifier la cohérence des métriques (organic_traffic, paid_search_traffic, visits, etc.)
- Analyser les performances de l'API (temps de réponse, stabilité)
- Tester les cas limites (dates invalides, paramètres manquants)
- Valider l'environnement de test (database: "trendtrack_test.db")

**Validation**:
- [ ] L'API répond correctement avec un statut 200
- [ ] Les 180 boutiques sont retournées avec toutes les métriques
- [ ] La structure JSON est cohérente et valide
- [ ] Les métriques numériques sont dans les plages attendues
- [ ] L'environnement de test est correctement identifié
- [ ] Les performances sont acceptables (< 2 secondes de réponse)
- [ ] La gestion d'erreurs fonctionne pour les cas limites

**Données de référence** (basées sur l'audit initial):
- **URL**: http://37.59.102.7:8001/test/shops/with-analytics-ordered?since=2025-07-10T00:00:00Z
- **Environnement**: TEST
- **Base de données**: trendtrack_test.db
- **Nombre de boutiques**: 180
- **Métriques disponibles**: monthly_visits, year_founded, total_products, aov, pixel_google, pixel_facebook, organic_traffic, bounce_rate, avg_visit_duration, visits, traffic, branded_traffic, percent_branded_traffic, paid_search_traffic, cpc, conversion_rate, market_* (us, uk, de, ca, au, fr)

## Task Dependencies Summary

**Chemin Critique**: T074 → T001 → T002 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040 → T046 → T047 → T048 → T049 → T050

**Opportunités Parallèles**: 
- Audit API (T074) peut s'exécuter en parallèle avec les autres tâches P0
- Tests de contrats (T003-T009) peuvent s'exécuter en parallèle après T002
- Endpoints API (T017-T020) peuvent s'exécuter en parallèle après les entités core
- Tâches de finition (T024-T027) peuvent s'exécuter en parallèle après l'intégration
- Nouvelles tâches TrendTrack (T032-T034) peuvent s'exécuter en parallèle après T021
- Tâches de correction (T041) peuvent s'exécuter en parallèle avec les autres P0
- Tâches de migration (T046-T050) peuvent s'exécuter en parallèle après T045

**Timeline Estimé**: 
- Configuration et Tests: 2-3 jours
- Implémentation Core: 5-7 jours  
- Implémentation API: 2-3 jours
- Intégration: 3-4 jours
- **Nouvelle fonctionnalité TrendTrack**: 4-6 jours
- **Migration base de données**: 3-4 jours
- Finition: 2-3 jours
- **Total**: 21-30 jours

---

*Tâches générées: 2025-09-16*
*Prêt pour l'implémentation suivant les principes constitutionnels*

# Implementation Tasks: Scraper SEM Parallèle

**Feature**: Scraper SEM Parallèle  
**Branch**: `001-name-trendtrack-scraper`  
**Date**: 2025-09-16  
**Generated from**: plan.md, data-model.md, research.md, quickstart.md, contracts/openapi.yaml

## Task Overview

**Total Tasks**: 28  
**Parallel Tasks**: 15 (marked with [P])  
**Sequential Tasks**: 13  

**Stratégie d'Exécution**: Approche TDD avec tests avant implémentation, exécution ordonnée par dépendances, exécution parallèle quand possible.

## Priorisation (P0/P1/P2)

- P0 (Critique, à exécuter en premier):
  - T001, T002 (Audit + comparaison BDD)
  - T006, T007, T008, T009 (Tests de régression/baseline)
  - T016 (Service de validation des métriques)
  - T015 (Service de gestion d'erreurs)
  - T021 (Intégration client API MyToolsPlan)

- P1 (Important, après P0):
  - T010, T011, T012 (Entités et services de base si écarts détectés)
  - T013, T014 (Services scraping de base + workers parallèles)
  - T017, T018, T019, T020 (Endpoints API)

- P2 (Finition/optimisation):
  - T024, T025, T026, T027, T028 (Unitaires, perf, docs, E2E, déploiement)

## Phase 0: Audit du Projet Existant (REMPLACE le Setup)

### T001: Audit rapide du code et de la doc existants [P]
**Type**: Audit  
**Dependencies**: None  
**Files**: `sem-scraper-final/production_scraper_parallel.py`, `trendtrack-scraper-final/`, `ubuntu/README/*`, `.specify/memory/constitution.md`  
**Description**: Cartographier les composants déjà en place (scraper, APIs, DB, workers, logs) et vérifier leur cohérence avec la constitution `.specify`.

**Implementation**:
- Lister les points d’entrée (scripts de lancement, workers, endpoints)
- Vérifier la présence du système de rollback et l’état des logs
- Valider que la logique de validation métriques est en place et utilisée
- Noter les divergences doc ↔ code

**Validation**: Rapport d’audit bref (10 lignes) + liste de divergences, validés par l’utilisateur.

### T002: Vérification schémas BDD prod/test (sans migration) [P]
**Type**: Audit  
**Dependencies**: T001  
**Files**: `trendtrack-final-scraper/data/trendtrack.db`, `trendtrack-final-scraper/data/trendtrack_test.db`  
**Description**: Comparer les schémas des deux BDD, sans créer de nouvelles migrations.

**Implementation**:
- Exporter la structure des tables (shops, analytics, scraping_sessions, workers)
- Comparer colonnes, types, index
- Lister les écarts éventuels

**Validation**: Rapport de comparaison validé par l’utilisateur; aucune modification appliquée.

## Test Tasks (Régression sur existant)

### T003: Website Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_website_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité Website basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD Website (GET, POST, PUT, DELETE /websites)
- Valider que les schémas request/response correspondent à la spécification OpenAPI
- Tester le filtrage par statut et la pagination
- Tester la gestion d'erreurs (404, 400, 409)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T004: Metrics Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_metrics_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité Metrics basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD metrics (GET, PUT /websites/{id}/metrics)
- Valider le schéma des 8 métriques (organic_traffic, paid_search_traffic, visits, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, percent_branded_traffic)
- Tester les règles de validation des métriques
- Tester la gestion d'erreurs (404, 400)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T005: ScrapingSession Entity Contract Tests [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/contracts/test_session_contracts.py`  
**Description**: Créer des tests de contrats pour l'entité ScrapingSession basés sur le schéma OpenAPI.

**Implémentation**:
- Tester les opérations CRUD session (GET, POST, DELETE /scraping/sessions)
- Tester l'endpoint de statut de session (/scraping/sessions/{id}/status)
- Valider le schéma de session et les transitions de statut
- Tester la gestion d'erreurs (404, 400)

**Validation**: Tests ciblent l’API/implémentation actuelle; servent de filet de régression.

### T006: Integration Test - Basic Website Scraping [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_basic_scraping.py`  
**Description**: Créer un test d'intégration pour le scénario de scraping de base d'un site web depuis quickstart.md.

**Implémentation**:
- Tester le scraping end-to-end d'un site web unique
- Valider la collecte de métriques et les mises à jour de statut
- Tester la création de session et le monitoring
- Valider les réponses des endpoints API

**Validation**: Doit passer sur le code actuel (sert de baseline), sinon ouvrir bug.

### T007: Integration Test - Parallel Worker Processing [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_parallel_workers.py`  
**Description**: Créer un test d'intégration pour le scénario de traitement parallèle de workers depuis quickstart.md.

**Implémentation**:
- Tester le traitement parallèle de plusieurs sites web
- Valider la distribution de charge des workers
- Tester le monitoring du progrès de session
- Valider le traitement concurrent

**Validation**: Doit passer sur le code actuel (baseline), sinon ouvrir bug.

### T008: Integration Test - Error Handling and Recovery [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_error_handling.py`  
**Description**: Créer un test d'intégration pour le scénario de gestion d'erreurs et de dégradation gracieuse depuis quickstart.md.

**Implémentation**:
- Tester la gestion des sites web invalides
- Valider la dégradation gracieuse avec des échecs partiels
- Tester le logging d'erreurs et les mises à jour de statut
- Valider la completion de session avec des résultats mixtes

**Validation**: Doit passer (baseline), sinon ouvrir bug.

### T009: Integration Test - Metric Validation [P]
**Type**: Test  
**Dependencies**: T002  
**Files**: `tests/integration/test_metric_validation.py`  
**Description**: Créer un test d'intégration pour la logique de validation des métriques depuis quickstart.md.

**Implémentation**:
- Tester la collecte des 8 métriques
- Valider la logique de statut (completed vs partial)
- Tester les métriques calculées (percent_branded_traffic)
- Valider les règles de validation des métriques

**Validation**: Doit passer (baseline), sinon ouvrir bug.

## Core Implementation Tasks

### T010: Website Entity Implementation
**Type**: Core  
**Dependencies**: T003  
**Files**: `models/website.py`, `services/website_service.py`  
**Description**: Implémenter l'entité Website et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle Website avec tous les champs de data-model.md
- Implémenter WebsiteService avec les opérations CRUD
- Ajouter les règles de validation pour shop_url, scraping_status, timestamps
- Implémenter la logique de transition de statut

**Validation**: Les tests de contrats T003 passent, l'entité Website fonctionne correctement.

### T011: Metrics Entity Implementation
**Type**: Core  
**Dependencies**: T004  
**Files**: `models/metrics.py`, `services/metrics_service.py`  
**Description**: Implémenter l'entité Metrics et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle Metrics avec les 8 champs de métriques
- Implémenter MetricsService avec les opérations CRUD
- Ajouter les règles de validation pour les champs numériques et les plages décimales
- Implémenter la logique de champ calculé (percent_branded_traffic)

**Validation**: Les tests de contrats T004 passent, l'entité Metrics fonctionne correctement.

### T012: ScrapingSession Entity Implementation
**Type**: Core  
**Dependencies**: T005  
**Files**: `models/scraping_session.py`, `services/session_service.py`  
**Description**: Implémenter l'entité ScrapingSession et le service basés sur le modèle de données.

**Implémentation**:
- Créer le modèle ScrapingSession avec tous les champs
- Implémenter SessionService avec les opérations CRUD
- Ajouter les règles de validation pour worker_count, websites_per_worker
- Implémenter la gestion du statut de session

**Validation**: Les tests de contrats T005 passent, l'entité ScrapingSession fonctionne correctement.

### T013: Basic Scraping Service Implementation
**Type**: Core  
**Dependencies**: T006, T010, T011  
**Files**: `services/scraping_service.py`  
**Description**: Implémenter le service de scraping de base pour le traitement d'un site web unique.

**Implémentation**:
- Créer ScrapingService avec traitement d'un site web unique
- Implémenter l'authentification MyToolsPlan et la gestion de session
- Ajouter la collecte de métriques de base (APIs + DOM scraping)
- Implémenter la logique de mise à jour de statut

**Validation**: Le test d'intégration T006 passe, le scraping de base fonctionne.

### T014: Parallel Worker Service Implementation
**Type**: Core  
**Dependencies**: T007, T012, T013  
**Files**: `services/worker_service.py`, `workers/parallel_worker.py`  
**Description**: Implémenter le service de workers parallèles pour le traitement concurrent.

**Implémentation**:
- Créer WorkerService avec la logique de traitement parallèle
- Implémenter la classe ParallelWorker avec asyncio
- Ajouter la gestion du pool de workers et la distribution de charge
- Implémenter le suivi du progrès de session

**Validation**: Le test d'intégration T007 passe, le traitement parallèle fonctionne.

### T015: Error Handling Service Implementation
**Type**: Core  
**Dependencies**: T008, T013  
**Files**: `services/error_handling_service.py`  
**Description**: Implémenter une gestion d'erreurs complète et une dégradation gracieuse.

**Implémentation**:
- Créer ErrorHandlingService avec la logique de retry
- Implémenter la dégradation gracieuse pour les échecs partiels
- Ajouter un logging d'erreurs complet
- Implémenter les mécanismes de récupération d'erreurs

**Validation**: Le test d'intégration T008 passe, la gestion d'erreurs fonctionne correctement.

### T016: Metric Validation Service Implementation
**Type**: Core  
**Dependencies**: T009, T011  
**Files**: `services/metric_validation_service.py`  
**Description**: Implémenter la logique de validation adaptative des métriques.

**Implémentation**:
- Créer MetricValidationService avec validation dynamique
- Implémenter la logique de validation des 8 métriques
- Ajouter la détermination de statut (completed/partial/failed/na)
- Implémenter la validation des métriques calculées

**Validation**: Le test d'intégration T009 passe, la validation des métriques fonctionne correctement.

## API Implementation Tasks

### T017: Website API Endpoints Implementation
**Type**: API  
**Dependencies**: T010  
**Files**: `api/website_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité Website.

**Implémentation**:
- Implémenter GET /websites (liste avec filtrage)
- Implémenter POST /websites (création)
- Implémenter GET /websites/{id} (obtenir détails)
- Implémenter PUT /websites/{id} (mise à jour)
- Implémenter DELETE /websites/{id} (suppression)

**Validation**: Tous les endpoints API Website fonctionnent correctement, correspondent au contrat OpenAPI.

### T018: Metrics API Endpoints Implementation
**Type**: API  
**Dependencies**: T011  
**Files**: `api/metrics_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité Metrics.

**Implémentation**:
- Implémenter GET /websites/{id}/metrics (obtenir métriques)
- Implémenter PUT /websites/{id}/metrics (mettre à jour métriques)
- Ajouter une gestion d'erreurs et validation appropriées
- S'assurer que les schémas de réponse correspondent à OpenAPI

**Validation**: Tous les endpoints API Metrics fonctionnent correctement, correspondent au contrat OpenAPI.

### T019: ScrapingSession API Endpoints Implementation
**Type**: API  
**Dependencies**: T012  
**Files**: `api/session_endpoints.py`  
**Description**: Implémenter les endpoints FastAPI pour l'entité ScrapingSession.

**Implémentation**:
- Implémenter GET /scraping/sessions (lister sessions)
- Implémenter POST /scraping/sessions (démarrer session)
- Implémenter GET /scraping/sessions/{id} (obtenir détails)
- Implémenter DELETE /scraping/sessions/{id} (annuler session)
- Implémenter GET /scraping/sessions/{id}/status (obtenir statut)

**Validation**: Tous les endpoints API ScrapingSession fonctionnent correctement, correspondent au contrat OpenAPI.

### T020: Health Check API Endpoint Implementation
**Type**: API  
**Dependencies**: None  
**Files**: `api/health_endpoints.py`  
**Description**: Implémenter l'endpoint de vérification de santé.

**Implémentation**:
- Implémenter l'endpoint GET /health
- Ajouter la vérification de connectivité base de données
- Ajouter la validation du statut système
- Retourner le statut de santé approprié

**Validation**: L'endpoint de vérification de santé retourne le statut correct.

## Integration Tasks

### T021: MyToolsPlan API Client Integration
**Type**: Integration  
**Dependencies**: T013  
**Files**: `clients/mytoolsplan_client.py`  
**Description**: Implémenter le client API MyToolsPlan avec authentification et gestion de session.

**Implémentation**:
- Créer MyToolsPlanClient avec authentification
- Implémenter la synchronisation de cookies entre domaines
- Ajouter les endpoints API pour organic.Summary, organic.OverviewTrend, engagement
- Implémenter le système de fallback (sam2.mytoolsplan.xyz)

**Validation**: Les APIs MyToolsPlan s'intègrent correctement, l'authentification fonctionne.

### T022: Database Integration Service
**Type**: Integration  
**Dependencies**: T010, T011, T012  
**Files**: `services/database_service.py`  
**Description**: Implémenter l'intégration base de données avec support de double base de données.

**Implémentation**:
- Créer DatabaseService avec basculement base de données production/test
- Implémenter le pool de connexions et la gestion de transactions
- Ajouter le support de migration de base de données
- Implémenter les procédures de sauvegarde et récupération

**Validation**: Les opérations de base de données fonctionnent correctement sur les deux bases.

### T023: Logging and Monitoring Integration
**Type**: Integration  
**Dependencies**: T015  
**Files**: `services/logging_service.py`, `monitoring/metrics_collector.py`  
**Description**: Implémenter un logging et monitoring complets.

**Implémentation**:
- Créer LoggingService avec logging structuré
- Implémenter le monitoring pour les performances de scraping
- Ajouter le suivi d'erreurs et l'alerte
- Implémenter les outils d'analyse de logs et de débogage

**Validation**: Le logging et monitoring fonctionnent correctement, fournissent des insights utiles.

## Polish Tasks

### T024: Unit Tests for All Services [P]
**Type**: Polish  
**Dependencies**: T010-T016  
**Files**: `tests/unit/test_*.py`  
**Description**: Créer des tests unitaires complets pour tous les services.

**Implémentation**:
- Créer des tests unitaires pour WebsiteService, MetricsService, SessionService
- Créer des tests unitaires pour ScrapingService, WorkerService, ErrorHandlingService
- Créer des tests unitaires pour MetricValidationService
- Ajouter le reporting de couverture de tests

**Validation**: Tous les tests unitaires passent, couverture > 90%.

### T025: Performance Optimization [P]
**Type**: Polish  
**Dependencies**: T014, T021  
**Files**: `services/performance_service.py`  
**Description**: Optimiser les performances pour le traitement parallèle et les appels API.

**Implémentation**:
- Optimiser les requêtes de base de données et l'indexation
- Implémenter le pool de connexions et la mise en cache
- Optimiser les performances des workers parallèles
- Ajouter le monitoring de performance et les métriques

**Validation**: Les performances répondent aux exigences (1-2 min/site web, 95%+ succès API).

### T026: Documentation and API Documentation [P]
**Type**: Polish  
**Dependencies**: T017-T020  
**Files**: `docs/`, `README.md`  
**Description**: Créer une documentation complète et une documentation API.

**Implémentation**:
- Créer la documentation API avec des exemples
- Créer le guide utilisateur et le guide de dépannage
- Créer la documentation développeur
- Mettre à jour le README avec les instructions de configuration et d'utilisation

**Validation**: La documentation est complète et précise.

### T027: End-to-End Validation [P]
**Type**: Polish  
**Dependencies**: T006-T009  
**Files**: `tests/e2e/test_full_scraping_flow.py`  
**Description**: Créer des tests de validation end-to-end pour le flux de scraping complet.

**Implémentation**:
- Créer un test E2E pour le workflow de scraping complet
- Tester les 5 scénarios de quickstart.md
- Valider les exigences de performance
- Tester les scénarios d'erreur et la récupération

**Validation**: Tous les tests E2E passent, le système fonctionne end-to-end.

### T028: Production Deployment Preparation
**Type**: Polish  
**Dependencies**: T021-T023  
**Files**: `deployment/`, `docker/`  
**Description**: Préparer le système pour le déploiement en production sur VPS.

**Implémentation**:
- Créer les scripts de déploiement et la configuration
- Configurer les variables d'environnement de production
- Créer les procédures de sauvegarde et récupération
- Configurer le monitoring et l'alerte

**Validation**: Le système est prêt pour le déploiement en production.

## Parallel Execution Examples

### Phase 1: Configuration et Tests (Parallèle)
```bash
# Exécuter les tâches de configuration
Tâche T001: Configuration de l'environnement et dépendances
Tâche T002: Configuration du schéma de base de données [P]

# Exécuter les tests de contrats en parallèle
Tâche T003: Tests de contrats de l'entité Website [P]
Tâche T004: Tests de contrats de l'entité Metrics [P]
Tâche T005: Tests de contrats de l'entité ScrapingSession [P]

# Exécuter les tests d'intégration en parallèle
Tâche T006: Test d'intégration - Scraping de base de site web [P]
Tâche T007: Test d'intégration - Traitement parallèle de workers [P]
Tâche T008: Test d'intégration - Gestion d'erreurs et récupération [P]
Tâche T009: Test d'intégration - Validation des métriques [P]
```

### Phase 2: Implémentation Core (Séquentielle)
```bash
# Entités core (séquentiel à cause des dépendances)
Tâche T010: Implémentation de l'entité Website
Tâche T011: Implémentation de l'entité Metrics
Tâche T012: Implémentation de l'entité ScrapingSession

# Services core (séquentiel à cause des dépendances)
Tâche T013: Implémentation du service de scraping de base
Tâche T014: Implémentation du service de workers parallèles
Tâche T015: Implémentation du service de gestion d'erreurs
Tâche T016: Implémentation du service de validation des métriques
```

### Phase 3: Implémentation API (Parallèle)
```bash
# Endpoints API (parallèle - fichiers différents)
Tâche T017: Implémentation des endpoints API Website [P]
Tâche T018: Implémentation des endpoints API Metrics [P]
Tâche T019: Implémentation des endpoints API ScrapingSession [P]
Tâche T020: Implémentation de l'endpoint API de vérification de santé [P]
```

### Phase 4: Intégration (Séquentielle)
```bash
# Services d'intégration (séquentiel à cause des dépendances)
Tâche T021: Intégration du client API MyToolsPlan
Tâche T022: Service d'intégration de base de données
Tâche T023: Intégration du logging et monitoring
```

### Phase 5: Finition (Parallèle)
```bash
# Tâches de finition (parallèle - fichiers différents)
Tâche T024: Tests unitaires pour tous les services [P]
Tâche T025: Optimisation des performances [P]
Tâche T026: Documentation et documentation API [P]
Tâche T027: Validation end-to-end [P]
Tâche T028: Préparation du déploiement en production
```

## Task Dependencies Summary

**Chemin Critique**: T001 → T002 → T003 → T010 → T013 → T014 → T021 → T022 → T023 → T028

**Opportunités Parallèles**: 
- Tests de contrats (T003-T009) peuvent s'exécuter en parallèle après T002
- Endpoints API (T017-T020) peuvent s'exécuter en parallèle après les entités core
- Tâches de finition (T024-T027) peuvent s'exécuter en parallèle après l'intégration

**Timeline Estimé**: 
- Configuration et Tests: 2-3 jours
- Implémentation Core: 5-7 jours  
- Implémentation API: 2-3 jours
- Intégration: 3-4 jours
- Finition: 2-3 jours
- **Total**: 14-20 jours

---

## 🏗️ MIGRATION TECHNIQUE (PRIORITÉ BASSE)

### Phase 1: Migration des Extractors (1-2 semaines)
```bash
# Migration progressive des extractors JavaScript vers Python
T058: Migration de BaseExtractor vers Python - base_extractor.py
T059: Migration de TrendTrackExtractor vers Python - trendtrack_extractor.py
T060: Migration des sélecteurs vers Python - selectors.py
T061: Tests de validation des extractors Python vs JavaScript
T062: Optimisation des performances des extractors Python
```

### Phase 2: Migration de l'Orchestrateur (1 semaine)
```bash
# Migration complète du scraper principal
T063: Migration de TrendTrackScraper vers Python - trendtrack_scraper.py
T064: Migration de WebScraper vers Python - web_scraper.py
T065: Migration de ErrorHandler vers Python - error_handler.py
T066: Tests d'intégration complets du système Python
T067: Validation des performances du système Python
```

### Phase 3: Finalisation et Nettoyage (3-5 jours)
```bash
# Suppression du code JavaScript legacy
T068: Suppression du code JavaScript legacy
T069: Mise à jour de la documentation technique
T070: Tests de régression finaux
T071: Optimisation finale des performances
T072: Documentation de l'architecture Python finale
```

### Notes sur la Migration
- **Priorité**: Basse (après stabilisation de l'approche hybride)
- **Stratégie**: Migration progressive avec tests de validation
- **Rollback**: Possible à chaque étape
- **Architecture hybride**: Maintenue jusqu'à migration complète

---

*Tâches générées: 2025-09-16*
*Prêt pour l'implémentation suivant les principes constitutionnels*

