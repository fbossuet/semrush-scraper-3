# Plan d'Implémentation : Scraper Noxtools

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
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

### Version Alpha - Test et Validation ✅ IMPLÉMENTÉE
- ✅ Initialisation Playwright stealth headless
- ✅ Authentification via formulaire (nouveaux sélecteurs)
- ✅ Navigation vers Noxtools avec maintien de session/cookies inter-domaine
- ✅ Scraping des métriques (sans enregistrement BDD)
- ✅ Logs détaillés de validation
- 🔄 **Retry session** : Détection session expirée et re-authentification complète
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 avec cohérence URLs (ServerManager implémenté)
- ✅ **Éligibilité shops** : Critères précis (shops.scraping_status ≠ "failed", details_scraping_status = "details_extracted", analytics.scraping_status = NULL)

### Version Beta - Formatage et Enregistrement
- Formatage des données selon standards
- Validation d'intégrité avant sauvegarde
- Enregistrement dans `analytics` avec correspondance `shops`
- Gestion robuste des erreurs de sauvegarde

### Version Finale - Optimisation et Parallélisation
- Optimisation performance et parallélisation par workers
- Timeouts adaptatifs avancés, throttling et backoff
- Monitoring de performance et préparation déploiement

## Inputs Requis par Version

### Alpha (✅ Fournis/Validés)
- ✅ Sélecteurs auth + navigation, URL finale, sélecteurs des métriques
- ✅ Credentials d'authentification Noxtools
- ✅ Domaine source Noxtools (URL de base)
- ✅ Sessions: gestion cookies entre domaines
- ✅ Anti-détection: User-Agents, headers, délais (ref. specs/002)
- ✅ **ServerManager** : Gestion centralisée des serveurs semrush1→semrush5
- ✅ **Formatage** : Pipeline de normalisation des données
- ✅ **Éligibilité shops** : Critères précis et testés

### Beta (À fournir/valider)
- Règles de formatage et validation
- Schéma `analytics` (structure/contraintes/index)
- 1 métrique calculée à partir des données scrapées
- Gestion d'erreurs (fallbacks, valeurs par défaut)
- Métadonnées (timestamp ISO 8601 pour logs, SQLite DATE pour BDD, source, version scraper)

### Finale (À fournir/valider)
- Configuration des workers (nombre, répartition, priorités)
- Rate-limit/token bucket (p/min, burst) et backoff adaptatif
- KPIs performance (latences, throughput, succès/échec)
- Monitoring/alertes (logs de performance agrégés, seuils)
- Déploiement et maintenance

## Architecture Implémentée

### Modules Principaux ✅
```
src/
├── core/
│   ├── server_manager.py      # ✅ Gestion serveurs semrush1→semrush5
│   ├── playwright_manager.py  # ✅ Navigation et anti-détection
│   ├── auth_manager.py        # ✅ Authentification Noxtools
│   ├── session_manager.py     # ✅ Gestion sessions cross-domain
│   ├── metrics_extractor.py   # ✅ Extraction métriques DOM
│   └── market_overview_navigator.py  # ✅ Navigation Market Overview
├── services/
│   ├── shop_repository.py     # ✅ Récupération shops éligibles
│   ├── formatter.py           # ✅ Formatage des données
│   └── status_manager.py      # ✅ Gestion statuts scraping
└── utils/
    └── url_params.py          # ✅ Calcul paramètres URL
```

### ServerManager ✅
- **Gestion centralisée** : 5 serveurs semrush1→semrush5
- **Fallback automatique** : Switch en cas d'échec
- **Normalisation URLs** : Cohérence garantie
- **Détection d'erreurs** : Session expirée, paywall, timeout
- **Intégration complète** : Tous les modules intégrés

## Fonctionnalités par Version

### Version Alpha ✅ IMPLÉMENTÉE
- **Scraping Noxtools** : Récupération des métriques sans BDD
- **Authentification** : Nouveaux sélecteurs de formulaire
- **Navigation multi-domaines** : Gestion des sessions entre domaines
- **Logs détaillés** : Validation des données récupérées
- **Gestion d'erreurs** : Scraping gracieux sans arrêt
- **Retry session** : Retour au login en cas de session expirée
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 (ServerManager implémenté)

### Version Beta - Formatage et Enregistrement
- **Toutes les fonctionnalités Alpha** : Base solide validée
- **Formatage des données** : Conversion selon standards définis
- **Validation d'intégrité** : Vérification avant sauvegarde
- **Enregistrement BDD** : Insertion/update des métriques
- **Gestion d'erreurs** : Fallbacks et rollback
- **Métadonnées** : Timestamps et traçabilité

### Version Finale - Optimisation et Parallélisation
- **Toutes les fonctionnalités Alpha et Beta** : Base complète
- **Optimisation performances** : Scraping parallèle avec workers
- **Timeouts adaptatifs** : Gestion avancée des délais
- **Fallback Noxtools** : Basculement automatique en cas de 404
- **Monitoring** : Métriques de performance et surveillance
- **Production** : Déploiement et maintenance

## Gestion des Erreurs

### Classes d'Erreurs
- **AuthError** : Échec d'authentification
- **NavigationError** : Problème de navigation
- **SelectorError** : Sélecteurs non trouvés
- **RateLimitError** : Limite de requêtes atteinte
- **FormatError** : Erreur de formatage
- **SaveError** : Erreur de sauvegarde

### Fallbacks
- **ServerManager** : ✅ Switch automatique entre serveurs
- **Re-essais exponentiels** : Backoff adaptatif
- **Délais humains** : Anti-détection
- **Valeurs par défaut** : Pour champs non critiques

### Politique d'Arrêt
- **Continuer par boutique** : Pas d'arrêt global
- **Compteur d'échecs** : Max par session
- **Logs détaillés** : Pour debugging

## Métadonnées

### Standards
- **`scraper_source`** : 'noxtools'
- **`scraper_version`** : Version du scraper
- **`scraped_at`** : ISO 8601 UTC pour logs/métadonnées
- **`updated_at`** : SQLite DATE pour BDD
- **`server_used`** : Serveur utilisé pour le scraping

### Traçabilité
- **`session_id`** : Identifiant de session
- **`worker_id`** : Identifiant du worker (version finale)
- **`server_used`** : Serveur Semrush utilisé
- **`fallback_count`** : Nombre de fallbacks effectués

## Vérification Constitution
*PORTE : Doit passer avant la Phase 0 recherche. Re-vérifier après la Phase 1 design.*

### ✅ Constitution Vérifiée
- **Spécification** : ✅ Complète et détaillée
- **Plan** : ✅ Architecture et roadmap définis
- **Tasks** : ✅ Tâches détaillées et priorités
- **Data Model** : ✅ Modèle de données défini
- **Quickstart** : ✅ Guide de démarrage rapide
- **Research** : ✅ Recherche et analyse effectuées

### ✅ Implémentation Alpha
- **ServerManager** : ✅ Implémenté et testé
- **Modules** : ✅ Tous les modules intégrés
- **Tests** : ✅ Tests complets passent
- **Documentation** : ✅ Mise à jour et cohérente

## Prochaines Étapes

### Version Beta (Prochaine)
1. **Formatage** : Pipeline de normalisation des données
2. **Base de données** : Insertion des métriques
3. **Validation** : Contrôles d'intégrité
4. **Tests** : Validation complète

### Version Finale (Future)
1. **Parallélisation** : Workers multiples
2. **Performance** : Optimisation des requêtes
3. **Monitoring** : Métriques de performance
4. **Production** : Déploiement et maintenance

## Statut Actuel

### ✅ Réalisé
- **ServerManager** : Gestion centralisée des serveurs
- **Architecture** : Modules complets et intégrés
- **Tests** : Validation complète
- **Documentation** : Mise à jour et cohérente

### 🔄 En Cours
- **Session retry** : Re-authentification complète
- **URLs harmonisées** : Test semrush1 vs semrush3

### 📋 À Faire
- **Version Beta** : Formatage et base de données
- **Version Finale** : Parallélisation et monitoring

**Statut global** : ✅ **Version Alpha opérationnelle avec ServerManager** 🎉

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
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

### Version Alpha - Test et Validation ✅ IMPLÉMENTÉE
- ✅ Initialisation Playwright stealth headless
- ✅ Authentification via formulaire (nouveaux sélecteurs)
- ✅ Navigation vers Noxtools avec maintien de session/cookies inter-domaine
- ✅ Scraping des métriques (sans enregistrement BDD)
- ✅ Logs détaillés de validation
- 🔄 **Retry session** : Détection session expirée et re-authentification complète
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 avec cohérence URLs (ServerManager implémenté)
- ✅ **Éligibilité shops** : Critères précis (shops.scraping_status ≠ "failed", details_scraping_status = "details_extracted", analytics.scraping_status = NULL)

### Version Beta - Formatage et Enregistrement
- Formatage des données selon standards
- Validation d'intégrité avant sauvegarde
- Enregistrement dans `analytics` avec correspondance `shops`
- Gestion robuste des erreurs de sauvegarde

### Version Finale - Optimisation et Parallélisation
- Optimisation performance et parallélisation par workers
- Timeouts adaptatifs avancés, throttling et backoff
- Monitoring de performance et préparation déploiement

## Inputs Requis par Version

### Alpha (✅ Fournis/Validés)
- ✅ Sélecteurs auth + navigation, URL finale, sélecteurs des métriques
- ✅ Credentials d'authentification Noxtools
- ✅ Domaine source Noxtools (URL de base)
- ✅ Sessions: gestion cookies entre domaines
- ✅ Anti-détection: User-Agents, headers, délais (ref. specs/002)
- ✅ **ServerManager** : Gestion centralisée des serveurs semrush1→semrush5
- ✅ **Formatage** : Pipeline de normalisation des données
- ✅ **Éligibilité shops** : Critères précis et testés

### Beta (À fournir/valider)
- Règles de formatage et validation
- Schéma `analytics` (structure/contraintes/index)
- 1 métrique calculée à partir des données scrapées
- Gestion d'erreurs (fallbacks, valeurs par défaut)
- Métadonnées (timestamp ISO 8601 pour logs, SQLite DATE pour BDD, source, version scraper)

### Finale (À fournir/valider)
- Configuration des workers (nombre, répartition, priorités)
- Rate-limit/token bucket (p/min, burst) et backoff adaptatif
- KPIs performance (latences, throughput, succès/échec)
- Monitoring/alertes (logs de performance agrégés, seuils)
- Déploiement et maintenance

## Architecture Implémentée

### Modules Principaux ✅
```
src/
├── core/
│   ├── server_manager.py      # ✅ Gestion serveurs semrush1→semrush5
│   ├── playwright_manager.py  # ✅ Navigation et anti-détection
│   ├── auth_manager.py        # ✅ Authentification Noxtools
│   ├── session_manager.py     # ✅ Gestion sessions cross-domain
│   ├── metrics_extractor.py   # ✅ Extraction métriques DOM
│   └── market_overview_navigator.py  # ✅ Navigation Market Overview
├── services/
│   ├── shop_repository.py     # ✅ Récupération shops éligibles
│   ├── formatter.py           # ✅ Formatage des données
│   └── status_manager.py      # ✅ Gestion statuts scraping
└── utils/
    └── url_params.py          # ✅ Calcul paramètres URL
```

### ServerManager ✅
- **Gestion centralisée** : 5 serveurs semrush1→semrush5
- **Fallback automatique** : Switch en cas d'échec
- **Normalisation URLs** : Cohérence garantie
- **Détection d'erreurs** : Session expirée, paywall, timeout
- **Intégration complète** : Tous les modules intégrés

## Fonctionnalités par Version

### Version Alpha ✅ IMPLÉMENTÉE
- **Scraping Noxtools** : Récupération des métriques sans BDD
- **Authentification** : Nouveaux sélecteurs de formulaire
- **Navigation multi-domaines** : Gestion des sessions entre domaines
- **Logs détaillés** : Validation des données récupérées
- **Gestion d'erreurs** : Scraping gracieux sans arrêt
- **Retry session** : Retour au login en cas de session expirée
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 (ServerManager implémenté)

### Version Beta - Formatage et Enregistrement
- **Toutes les fonctionnalités Alpha** : Base solide validée
- **Formatage des données** : Conversion selon standards définis
- **Validation d'intégrité** : Vérification avant sauvegarde
- **Enregistrement BDD** : Insertion/update des métriques
- **Gestion d'erreurs** : Fallbacks et rollback
- **Métadonnées** : Timestamps et traçabilité

### Version Finale - Optimisation et Parallélisation
- **Toutes les fonctionnalités Alpha et Beta** : Base complète
- **Optimisation performances** : Scraping parallèle avec workers
- **Timeouts adaptatifs** : Gestion avancée des délais
- **Fallback Noxtools** : Basculement automatique en cas de 404
- **Monitoring** : Métriques de performance et surveillance
- **Production** : Déploiement et maintenance

## Gestion des Erreurs

### Classes d'Erreurs
- **AuthError** : Échec d'authentification
- **NavigationError** : Problème de navigation
- **SelectorError** : Sélecteurs non trouvés
- **RateLimitError** : Limite de requêtes atteinte
- **FormatError** : Erreur de formatage
- **SaveError** : Erreur de sauvegarde

### Fallbacks
- **ServerManager** : ✅ Switch automatique entre serveurs
- **Re-essais exponentiels** : Backoff adaptatif
- **Délais humains** : Anti-détection
- **Valeurs par défaut** : Pour champs non critiques

### Politique d'Arrêt
- **Continuer par boutique** : Pas d'arrêt global
- **Compteur d'échecs** : Max par session
- **Logs détaillés** : Pour debugging

## Métadonnées

### Standards
- **`scraper_source`** : 'noxtools'
- **`scraper_version`** : Version du scraper
- **`scraped_at`** : ISO 8601 UTC pour logs/métadonnées
- **`updated_at`** : SQLite DATE pour BDD
- **`server_used`** : Serveur utilisé pour le scraping

### Traçabilité
- **`session_id`** : Identifiant de session
- **`worker_id`** : Identifiant du worker (version finale)
- **`server_used`** : Serveur Semrush utilisé
- **`fallback_count`** : Nombre de fallbacks effectués

## Vérification Constitution
*PORTE : Doit passer avant la Phase 0 recherche. Re-vérifier après la Phase 1 design.*

### ✅ Constitution Vérifiée
- **Spécification** : ✅ Complète et détaillée
- **Plan** : ✅ Architecture et roadmap définis
- **Tasks** : ✅ Tâches détaillées et priorités
- **Data Model** : ✅ Modèle de données défini
- **Quickstart** : ✅ Guide de démarrage rapide
- **Research** : ✅ Recherche et analyse effectuées

### ✅ Implémentation Alpha
- **ServerManager** : ✅ Implémenté et testé
- **Modules** : ✅ Tous les modules intégrés
- **Tests** : ✅ Tests complets passent
- **Documentation** : ✅ Mise à jour et cohérente

## Prochaines Étapes

### Version Beta (Prochaine)
1. **Formatage** : Pipeline de normalisation des données
2. **Base de données** : Insertion des métriques
3. **Validation** : Contrôles d'intégrité
4. **Tests** : Validation complète

### Version Finale (Future)
1. **Parallélisation** : Workers multiples
2. **Performance** : Optimisation des requêtes
3. **Monitoring** : Métriques de performance
4. **Production** : Déploiement et maintenance

## Statut Actuel

### ✅ Réalisé
- **ServerManager** : Gestion centralisée des serveurs
- **Architecture** : Modules complets et intégrés
- **Tests** : Validation complète
- **Documentation** : Mise à jour et cohérente

### 🔄 En Cours
- **Session retry** : Re-authentification complète
- **URLs harmonisées** : Test semrush1 vs semrush3

### 📋 À Faire
- **Version Beta** : Formatage et base de données
- **Version Finale** : Parallélisation et monitoring

**Statut global** : ✅ **Version Alpha opérationnelle avec ServerManager** 🎉
