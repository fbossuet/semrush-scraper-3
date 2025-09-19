# TrendTrack Scraper Constitution
<!-- Constitution pour le projet TrendTrack Scraper - Système de scraping hybride API/DOM -->

## Core Principles

### I. Documentation-First (NON-NEGOTIABLE)
Toute modification commence par la consultation de la documentation; Le guide de développement doit être lu avant chaque action; Les spécifications techniques priment sur les suppositions; Toute incohérence doc/code doit être documentée et corrigée

### II. VPS-Only Development
Développement exclusivement sur le VPS (jamais en local); Workflow obligatoire: télécharger → modifier localement → vérifier syntaxe → uploader → vérifier déploiement; Backup obligatoire avant toute modification; Test de compilation Python avant upload

### III. Validation Utilisateur (NON-NEGOTIABLE)
L'utilisateur valide chaque modification via test sur le VPS; Aucune tâche marquée "terminée" sans validation explicite; L'utilisateur dit "OK" ou "KO" - c'est lui qui décide; Rollback immédiat si validation échoue

### IV. Logs Immutables
JAMAIS modifier les messages de logs existants; Les logs sont une source d'information précieuse qui ne doit pas être corrompue; Ajouter des logs si nécessaire, mais ne pas corriger les existants; Analyse des logs pour diagnostic des problèmes

### V. Approche Adaptative
Validation des métriques par comptage dynamique (pas de hardcoding); Logique évolutive pour ajouter/supprimer des métriques; Système de fallback pour les APIs (sam2.mytoolsplan.xyz); Gestion intelligente des timeouts et erreurs

## Contraintes Techniques

### Stack Technologique
- **Python 3.x** avec Playwright pour le scraping DOM
- **APIs MyToolsPlan** (organic.Summary, organic.OverviewTrend, engagement, projects)
- **SQLite** pour le stockage des données
- **FastAPI** pour les endpoints de test (Port 8001, URL: http://37.59.102.7:8001)
- **Système de workers parallèles** pour la performance
- **Endpoint principal**: /test/shops/with-analytics-ordered (structure standardisée 25 champs)

### Standards de Performance
- **Timeout adaptatif** : Ne pas insister sur les métriques non récupérables
- **Workers intelligents** : Éviter le re-scraping inutile des shops completed
- **Gestion d'erreurs robuste** : Retry avec délais progressifs (3 tentatives max)
- **Logs optimisés** : Réduction de la verbosité, conservation des logs critiques

## Workflow de Développement

### Processus de Modification
1. **Lecture obligatoire** du guide de développement
2. **Backup** du fichier à modifier
3. **Téléchargement** du fichier du VPS
4. **Modification locale** avec outils appropriés (search_replace, MultiEdit)
5. **Vérification syntaxe** Python (py_compile)
6. **Upload** sur le VPS
7. **Vérification déploiement** sur le VPS
8. **Test utilisateur** et validation

### Contrôles Qualité
- **Vérification des effets de bord** avant toute modification
- **Test de compilation** obligatoire avant upload
- **Vérification cohérence** doc/code après modification
- **Rollback automatique** en cas d'échec de validation
- **Système de tâches interne** : tasks.md avec priorités P0-P3 et statuts
- **Workspace de test** : /home/ubuntu/projects/shopshopshops/test/ (développement isolé)

## Governance

### Règles de Gouvernance
Cette constitution prime sur toutes les autres pratiques; Toute modification doit respecter les principes établis; Les incohérences doivent être documentées et corrigées; Le système de rollback doit être maintenu opérationnel

### Amendements
Les amendements nécessitent une documentation complète, une validation utilisateur, et un plan de migration; Toute complexité ajoutée doit être justifiée; Utiliser les fichiers de documentation existants pour le guidage en temps réel

## Structure de l'Endpoint Standardisé

### Endpoint Principal: /test/shops/with-analytics-ordered
**Structure de retour standardisée (25 champs)**:
- **Identité**: id, shop_name, shop_url, category
- **Métriques de base**: monthly_visits, year_founded, total_products, aov
- **Pixels**: pixel_google, pixel_facebook
- **Trafic**: organic_traffic, bounce_rate, avg_visit_duration, visits
- **Analytics**: branded_traffic, percent_branded_traffic, paid_search_traffic, cpc, conversion_rate
- **Marchés**: market_us, market_uk, market_de, market_ca, market_au, market_fr

### Bases de Données
- **Production**: trendtrack.db (structure de base, types TEXT)
- **Test**: trendtrack_test.db (structure optimisée, types INTEGER/DATE)
- **Endpoint utilise**: trendtrack.db (données de production)

**Version**: 1.1.0 | **Ratifié**: 2025-09-16 | **Dernière modification**: 2025-09-18