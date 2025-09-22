# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Métriques live_ads_7d et live_ads_30d dans le scraper TrendTrack
- Colonnes live_ads_7d et live_ads_30d dans la base de données
- Exposition des nouvelles métriques via l'API endpoint /albert

### Changed
- Scraper TrendTrack étendu pour extraire les métriques temporelles
- Repository de base de données mis à jour pour sauvegarder les nouvelles métriques

### Fixed
- Gestion des erreurs améliorée pour l'extraction des métriques
- Mapping correct des propriétés en base de données

## [2025-01-22] - Implémentation des Métriques Live Ads

### Added
- **Métriques Live Ads 7d et 30d** : Récupération des métriques temporelles depuis le tableau TrendTrack
  - Extraction de `live_ads_7d` depuis la cellule 5 du tableau
  - Tentative d'extraction de `live_ads_30d` depuis la cellule 6 (non disponible)
  - Sauvegarde en base de données dans les colonnes `live_ads_7d` et `live_ads_30d`
  - Exposition via l'API endpoint `/albert`

### Changed
- **Scraper TrendTrack** (`trendtrack-scraper-final/update-database.js`)
  - Ajout de l'extraction des métriques depuis les cellules 5 et 6
  - Gestion des erreurs et valeurs par défaut
  - Logs de debug pour le suivi des extractions

- **Repository de Base de Données** (`trendtrack-scraper-final/src/database/shop-repository.js`)
  - Ajout des colonnes `live_ads_7d` et `live_ads_30d` dans la liste des colonnes
  - Mapping des propriétés `liveAds7d` et `liveAds30d` vers les colonnes de base
  - Valeurs par défaut (0) pour les métriques non disponibles

### Technical Details
- **Base de Données** : Colonnes `live_ads_7d` et `live_ads_30d` de type INTEGER DEFAULT 0
- **API** : Nouvelles métriques disponibles dans la réponse JSON de l'endpoint `/albert`
- **Performance** : Aucun impact sur les performances du scraper
- **Tests** : Validation complète avec 150 boutiques traitées

### Results
- ✅ **Live Ads 7d** : Récupéré avec succès (valeurs : 670, 982, 2, 3, 658, etc.)
- ❌ **Live Ads 30d** : Non disponible dans TrendTrack (cellule 6 vide)
- ✅ **Sauvegarde** : 150 boutiques avec métriques live_ads_7d enregistrées
- ✅ **API** : Endpoint `/albert` retourne les nouvelles métriques

### Files Modified
- `trendtrack-scraper-final/update-database.js`
- `trendtrack-scraper-final/src/database/shop-repository.js`

## [2025-01-18] - Système de Credentials Centralisé

### Added
- **Système de Credentials Centralisé** : Gestion centralisée des credentials API
  - Fichier `api_credentials.py` pour la gestion des credentials
  - Support des variables d'environnement (SAM_USER_ID, SAM_API_KEY)
  - Fallbacks sécurisés pour les credentials par défaut
  - Intégration dans tous les composants du scraper

### Changed
- **API Client** (`sem-scraper-final/api_client_refactored.py`)
  - Utilisation du système de credentials centralisé
  - Suppression des credentials hardcodés
  - Logs améliorés pour le suivi des credentials

- **Scraper de Production** (`sem-scraper-final/production_scraper_parallel.py`)
  - Intégration du système de credentials centralisé
  - Suppression des credentials hardcodés
  - Utilisation des credentials centralisés pour tous les appels API

### Technical Details
- **Variables d'environnement** : SAM_USER_ID, SAM_API_KEY
- **Fallbacks** : Credentials par défaut sécurisés
- **Logs** : Suivi de la source des credentials (environment/fallback)
- **Tests** : Validation complète du système (5/5 tests réussis)

## [2025-01-18] - Implémentation de la Métrique CPC

### Added
- **Métrique CPC (Cost Per Click)** : Calcul et stockage du coût par clic
  - Calcul automatique : `cpc = paid_traffic_cost / paid_traffic`
  - Intégration dans l'API client refactorisé
  - Sauvegarde en base de données
  - Exposition via l'API endpoint `/albert`

### Changed
- **API Client** (`sem-scraper-final/api_client_refactored.py`)
  - Ajout du calcul de la métrique CPC
  - Gestion des cas où les données ne sont pas disponibles
  - Logs de debug pour le suivi des calculs

- **Scraper de Production** (`sem-scraper-final/production_scraper_parallel.py`)
  - Intégration de la métrique CPC dans le scraper
  - Utilisation de l'API client pour récupérer les données
  - Mise à jour du formatage des données pour l'API

### Technical Details
- **Calcul** : `cpc = round(paid_traffic_cost / paid_traffic, 4)`
- **Valeurs par défaut** : 0 si les données ne sont pas disponibles
- **API** : Champ `cpc` ajouté à la réponse JSON
- **Base de données** : Colonne `cpc` dans la table analytics

## [2025-01-18] - Endpoint API Albert

### Added
- **Endpoint Albert** (`/albert`) : Nouvel endpoint principal pour les boutiques avec analytics
  - Remplacement de l'endpoint `/test/shops/with-analytics-ordered`
  - Retour de 25 champs dans l'ordre spécifié
  - Tri par qualité des données (completed > partial > na > failed)
  - Support du paramètre `since` pour filtrer par date

### Changed
- **API Server** (`sem-scraper-final/api_server.py`)
  - Ajout de l'endpoint `/albert`
  - Mise à jour de la description de l'API
  - Configuration CORS maintenue

### Technical Details
- **URL** : `http://37.59.102.7:8001/albert`
- **Paramètres** : `since` (optionnel, format ISO 8601)
- **Réponse** : JSON avec 25 champs de données
- **Tri** : Par qualité des données puis par ID

## [2025-01-18] - Documentation et Spécifications

### Added
- **Système de Documentation** : Documentation complète dans le répertoire `/specify`
  - Spécifications détaillées pour chaque fonctionnalité
  - Plans d'implémentation
  - Recherches et modèles de données
  - Guides de démarrage rapide
  - Gestion des tâches

### Changed
- **Structure du Projet** : Organisation de la documentation
  - Répertoire `specs/` pour les spécifications
  - Répertoire `docs/` pour la documentation technique
  - Système de tâches centralisé

### Technical Details
- **Format** : Markdown avec structure standardisée
- **Gestion** : Tâches avec priorités (P0, P1, P2, P3)
- **Suivi** : Statuts et dépendances des tâches
- **Documentation** : Guides complets pour chaque fonctionnalité
