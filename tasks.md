# Tasks - Projet ShopShopShops

## Tâches Actives

### T001: Migration BDD - Ajout colonnes live_ads_7d et live_ads_30d [P0]
**Type**: Infrastructure  
**Dependencies**: Aucune  
**Files**: `test/trendtrack-scraper-final/data/update_database_structure.sql`, `test/trendtrack-scraper-final/src/database/schema.js`  
**Description**: Ajouter les colonnes live_ads_7d et live_ads_30d à la base de données pour capturer les variations de progression des Live Ads.

**Objectif**: Permettre le suivi des variations de Live Ads sur 7 jours et 30 jours pour une analyse de tendance.

**Implémentation**:
- [ ] Modifier le schéma SQL pour ajouter les colonnes live_ads_7d et live_ads_30d
- [ ] Mettre à jour le schéma JavaScript dans schema.js
- [ ] Créer un script de migration pour les bases existantes
- [ ] Tester la migration sur la base de test
- [ ] Valider la compatibilité avec les extracteurs existants

**Validation**:
- [ ] Les colonnes sont ajoutées à la table shops
- [ ] Les extracteurs peuvent écrire dans ces colonnes
- [ ] L'API peut lire ces nouvelles données
- [ ] Les requêtes existantes restent compatibles

**Critères de succès**:
- Colonnes live_ads_7d et live_ads_30d ajoutées
- Migration réussie sans perte de données
- Compatibilité maintenue avec le code existant

### T002: Désactivation système de locks dans l'environnement test [P0]
**Type**: Bug Fix  
**Dependencies**: Aucune  
**Files**: `test/trendtrack-scraper-final/update-database.js`, extracteurs JS  
**Description**: Désactiver le système de locks par fichiers qui peut bloquer la concurrence dans l'environnement de test.

**Objectif**: Éliminer les blocages de base de données causés par les verrous de fichiers.

**Implémentation**:
- [ ] Identifier les fichiers utilisant des locks dans l'environnement test
- [ ] Désactiver les mécanismes de locks dans update-database.js
- [ ] Modifier les extracteurs JavaScript pour ignorer les locks
- [ ] Tester la concurrence sans locks
- [ ] Documenter les changements

**Validation**:
- [ ] Aucun fichier de lock généré
- [ ] Accès concurrent à la base de données fonctionnel
- [ ] Pas de corruption de données
- [ ] Performance maintenue ou améliorée

**Critères de succès**:
- Système de locks complètement désactivé
- Accès concurrent sécurisé
- Aucune corruption de données

### T003: Corrections TrendTrack - Navigation et extraction produits [P1]
**Type**: Bug Fix  
**Dependencies**: T001  
**Files**: `test/trendtrack-scraper-final/trendtrack_extractor_vps.js`  
**Description**: Corriger les erreurs de navigation et d'extraction de produits dans les extracteurs TrendTrack.

**Objectif**: Améliorer la fiabilité de l'extraction des données de produits.

**Implémentation**:
- [ ] Analyser les erreurs de navigation actuelles
- [ ] Corriger la logique d'extraction des produits (colonne 2)
- [ ] Améliorer la gestion des timeouts
- [ ] Ajouter une meilleure gestion d'erreurs
- [ ] Tester les corrections sur des boutiques réelles

**Validation**:
- [ ] Extraction de produits fonctionnelle
- [ ] Réduction des timeouts
- [ ] Gestion d'erreurs robuste
- [ ] Données de produits cohérentes

**Critères de succès**:
- Extraction de produits fiable
- Réduction des erreurs de navigation
- Amélioration de la stabilité

### T004: Système de surveillance de l'API [P1]
**Type**: Infrastructure  
**Dependencies**: Aucune  
**Files**: À créer - scripts de monitoring  
**Description**: Ajouter un système de surveillance de l'API pour vérifier qu'elle tourne toujours et détecter les pannes.

**Objectif**: Assurer la disponibilité continue de l'API sur le port 8001 et alerter en cas de problème.

**Implémentation**:
- [ ] Créer un script de monitoring de l'API (check_api_health.sh)
- [ ] Implémenter une vérification de l'endpoint /test/shops/with-analytics-ordered
- [ ] Ajouter un système de notification en cas de panne
- [ ] Configurer un monitoring périodique (cron job)
- [ ] Créer un système de redémarrage automatique si nécessaire
- [ ] Ajouter des logs de surveillance

**Validation**:
- [ ] Le script détecte correctement les pannes de l'API
- [ ] Le système envoie des alertes appropriées
- [ ] Le monitoring fonctionne en continu
- [ ] Les logs de surveillance sont générés
- [ ] Le système peut redémarrer l'API automatiquement

**Critères de succès**:
- Surveillance active 24/7 de l'API
- Détection des pannes en moins de 5 minutes
- Système de notification fonctionnel
- Redémarrage automatique en cas de panne

### T005: Scripts de surveillance de l'intégrité de la base de données [P1]
**Type**: Infrastructure  
**Dependencies**: Aucune  
**Files**: À créer - scripts de monitoring DB  
**Description**: Mettre en place des scripts de surveillance de l'intégrité de la base de données pour détecter les corruptions, les incohérences et les problèmes de performance.

**Objectif**: Assurer l'intégrité et la disponibilité des données dans les bases trendtrack.db et trendtrack_test.db.

**Implémentation**:
- [ ] Créer un script de vérification d'intégrité (check_db_integrity.sh)
- [ ] Implémenter une vérification des contraintes de base de données
- [ ] Ajouter une surveillance de la taille des bases de données
- [ ] Créer un système de détection des corruptions
- [ ] Implémenter une surveillance des performances de requêtes
- [ ] Ajouter un système d'alerte en cas de problème
- [ ] Configurer des sauvegardes automatiques préventives

**Validation**:
- [ ] Le script détecte les corruptions de base de données
- [ ] La surveillance des performances fonctionne
- [ ] Les alertes sont envoyées en cas de problème
- [ ] Les sauvegardes automatiques sont opérationnelles
- [ ] Le système peut réparer automatiquement les problèmes mineurs

**Critères de succès**:
- Surveillance continue de l'intégrité des bases
- Détection des problèmes en moins de 10 minutes
- Système de réparation automatique pour les problèmes mineurs
- Sauvegardes préventives fonctionnelles

### T006: Automatisation des scrapers [P2]
**Type**: Infrastructure  
**Dependencies**: T001, T002  
**Files**: À créer - scripts d'automatisation  
**Description**: Automatiser le lancement et la gestion des scrapers TrendTrack et SEM pour un fonctionnement continu et autonome.

**Objectif**: Rendre le système de scraping complètement autonome avec gestion automatique des cycles, redémarrages et optimisations.

**Implémentation**:
- [ ] Créer un script de gestion automatique des scrapers (auto_scrapers_manager.sh)
- [ ] Implémenter un système de planification des tâches de scraping
- [ ] Ajouter une gestion automatique des workers parallèles
- [ ] Créer un système de redémarrage automatique des scrapers
- [ ] Implémenter une surveillance de l'état des scrapers
- [ ] Ajouter une optimisation automatique des ressources
- [ ] Configurer un système de priorisation des tâches

**Validation**:
- [ ] Les scrapers se lancent automatiquement selon le planning
- [ ] Le système gère les redémarrages en cas de panne
- [ ] La surveillance des scrapers fonctionne
- [ ] L'optimisation des ressources est effective
- [ ] Le système de priorisation fonctionne

**Critères de succès**:
- Fonctionnement 24/7 des scrapers
- Gestion automatique des pannes et redémarrages
- Optimisation continue des performances
- Réduction de l'intervention manuelle à 0%

### T007: Système de surveillance de logs avec alertes [P2]

### T008: Audit complet du code et refactorisation [P2]

**📋 Rapport d'audit syntaxe disponible**: [syntax_audit_report.md](./syntax_audit_report.md)

**✅ Phase 1 terminée**: Audit critique des erreurs de syntaxe (362 → 25 erreurs, -93%)

**🔄 Prochaines étapes**: Corrections automatiques, refactorisation des fonctions dupliquées

**Type**: Refactoring  
**Dependencies**: T001, T002  
**Files**: Tous les fichiers de code du projet  
**Description**: Effectuer un audit complet du code existant pour identifier les problèmes de syntaxe, les améliorations possibles, les optimisations et planifier une refactorisation générale.


**Objectif**: Améliorer la qualité, la maintenabilité et les performances du code en identifiant et corrigeant tous les problèmes existants.


**Implémentation**:
- [x] Audit de la syntaxe et des erreurs de code (linters, syntax checkers)
- [ ] Analyse des performances et optimisation du code
- [ ] Vérification de la conformité aux standards de codage
- [ ] Identification des code smells et anti-patterns
- [ ] Analyse de la sécurité du code
- [ ] Vérification de la gestion des erreurs et exceptions
- [ ] Audit de la documentation du code
- [ ] Planification de la refactorisation par priorité
- [ ] Création d'un plan de migration pour les améliorations
- [ ] Mise en place d'outils de qualité de code (ESLint, Prettier, etc.)
- [ ] Tests de régression après refactorisation
- [ ] Documentation des changements et bonnes pratiques

**Validation**:
- [x] Tous les problèmes de syntaxe sont corrigés
- [ ] Les performances sont améliorées ou maintenues
- [ ] Le code respecte les standards de qualité
- [ ] La sécurité est renforcée
- [ ] La gestion des erreurs est robuste
- [ ] La documentation est complète et à jour
- [ ] Les tests passent après refactorisation

**Critères de succès**:
- Code sans erreurs de syntaxe ni warnings (Phase 1 terminée)
- Amélioration des performances mesurable
- Respect des bonnes pratiques de développement
- Sécurité renforcée
- Documentation complète
- Tests de régression passants
- Outils de qualité de code configurés
- Plan de maintenance préventive établi

**Type**: Infrastructure  
**Dependencies**: T001  
**Files**: À créer - scripts de monitoring de logs  
**Description**: Mettre en place un système de surveillance des logs avec déclenchement d'alertes pour détecter les erreurs, les anomalies et les problèmes de performance.

**Objectif**: Surveiller en temps réel tous les logs du système et alerter immédiatement en cas de problème critique.

**Implémentation**:
- [ ] Créer un script de surveillance des logs (log_monitor.sh)
- [ ] Implémenter une détection d'erreurs en temps réel
- [ ] Ajouter un système de classification des alertes (critique, warning, info)
- [ ] Créer un système de notification multi-canal (email, webhook, etc.)
- [ ] Implémenter une surveillance des patterns d'erreurs
- [ ] Ajouter un système de rotation et archivage des logs
- [ ] Configurer des dashboards de monitoring

**Validation**:
- [ ] La détection d'erreurs fonctionne en temps réel
- [ ] Le système de classification des alertes est opérationnel
- [ ] Les notifications sont envoyées correctement
- [ ] La surveillance des patterns fonctionne
- [ ] Les dashboards affichent les bonnes informations

**Critères de succès**:
- Détection d'erreurs en moins de 2 minutes
- Classification automatique des alertes
- Notifications fiables et rapides
- Dashboards en temps réel opérationnels

## Règles de Gestion

### Priorités
- **P0**: Critique - Doit être fait immédiatement
- **P1**: Important - Doit être fait dans les 24h
- **P2**: Normal - Doit être fait dans la semaine
- **P3**: Faible - Peut être fait plus tard

### Types de Tâches
- **Bug Fix**: Correction d'un problème existant
- **Feature**: Ajout d'une nouvelle fonctionnalité
- **Infrastructure**: Amélioration de l'infrastructure
- **Documentation**: Mise à jour de la documentation
- **Refactoring**: Amélioration du code existant

### Statuts
- **En cours**: Tâche en cours de développement
- **En attente**: Tâche en attente de validation
- **Terminée**: Tâche complétée et validée
- **Annulée**: Tâche annulée ou non nécessaire

## Métriques

- **Total des tâches**: 11
- **Tâches P0**: 2 (T001, T002)
- **Tâches P1**: 2 (T003, T004, T005)
- **Tâches P2**: 4 (T006, T007, T008, T009)
- **Tâches P3**: 1 (T010)
- **Tâches P4**: 1 (T011)
- **Tâches terminées**: 0
- **Tâches en cours**: 11
- **Tâches en attente**: 0

---

**Dernière mise à jour**: 2025-09-19 08:45:00 UTC  
**Version**: 1.2.0

### T009: Sauvegarde incrémentale par lots pour TrendTrack [P2]
**Type**: Feature  
**Dependencies**: T001, T002  
**Files**: À créer - modules de sauvegarde par lots  
**Description**: Implémenter un système de sauvegarde incrémentale par lots pour le scraper TrendTrack afin de sauvegarder les données au fur et à mesure sans impacter les performances.


**Objectif**: Remplacer la sauvegarde en fin de processus par une sauvegarde par lots avec queue asynchrone pour améliorer la résilience et réduire les risques de perte de données.


**Implémentation**:
- [x] Créer la classe BatchSaver avec queue asynchrone
- [x] Implémenter le système de flush automatique périodique
- [x] Modifier le scraper principal pour utiliser la sauvegarde incrémentale
- [ ] Optimiser shop-repository.js avec transactions par lots
- [x] Ajouter un système de retry automatique pour les erreurs
- [x] Implémenter le monitoring et les métriques de sauvegarde
- [x] Tester la compatibilité avec le système existant
- [ ] Documenter les changements de stratégie de sauvegarde

**Validation**:
- [ ] La sauvegarde par lots fonctionne correctement
- [ ] Les performances de scraping sont maintenues ou améliorées
- [ ] La résilience est améliorée (perte max = 1 batch)
- [ ] Le système de retry gère les erreurs temporaires
- [ ] Les métriques de sauvegarde sont disponibles
- [ ] La compatibilité avec le système existant est préservée

**Critères de succès**:
- Sauvegarde incrémentale fonctionnelle (batch de 10 items)
- Réduction des risques de perte de données (max 10 items)
- Maintien des performances de scraping
- Monitoring temps réel des sauvegardes
- Gestion automatique des erreurs et retry
- Documentation complète


**Type**: Feature  
**Dependencies**: T001, T002, T003, T004, T005  
**Files**: À créer - modules d'authentification API  
**Description**: Implémenter une authentification basée sur API au lieu de l'authentification DOM existante pour le système TrendTrack.

**Objectif**: Remplacer l'authentification DOM par une authentification API plus robuste et moins détectable.

**Implémentation**:
- [ ] Analyser l'API TrendTrack pour l'authentification
- [ ] Créer un module d'authentification API
- [ ] Implémenter la gestion des tokens d'authentification
- [ ] Remplacer l'authentification DOM par l'API
- [x] Tester la compatibilité avec le système existant
- [ ] Documenter les changements d'authentification

**Validation**:
- [ ] L'authentification API fonctionne correctement
- [ ] Le système TrendTrack utilise l'API au lieu du DOM
- [ ] Les performances sont maintenues ou améliorées
- [ ] La détectabilité est réduite
- [ ] La compatibilité avec le système existant est préservée

**Critères de succès**:
- Authentification API fonctionnelle
- Remplacement complet de l'authentification DOM
- Réduction de la détectabilité
- Maintien des performances
- Documentation complète


# Tâche personnalisée : /lock
## Libération des locks de base de données

### Commandes de libération automatique :

```bash
# 1. Vérifier les processus utilisant la DB
lsof /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db 2>/dev/null || echo "Aucun processus utilisant la DB"

# 2. Nettoyer les locks SQLite
cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
sqlite3 data/trendtrack.db "PRAGMA journal_mode=DELETE; VACUUM;"

# 3. Vérifier l'accès
sqlite3 data/trendtrack.db "SELECT COUNT(*) FROM shops;"

# 4. Tuer les processus Node.js bloquants si nécessaire
pkill -f "trendtrack" || echo "Aucun processus trendtrack à tuer"
pkill -f "update-database" || echo "Aucun processus update-database à tuer"

```

### Usage :
Exécuter ces commandes quand la base de données est bloquée par un lock.

### T010: Authentification basée sur API pour TrendTrack [P3]
**Type**: Feature  
**Dependencies**: T001, T002, T003, T004, T005  
**Files**: À créer - modules d'authentification API  
**Description**: Implémenter une authentification basée sur API au lieu de l'authentification DOM existante pour le système TrendTrack.

**Objectif**: Remplacer l'authentification DOM par une authentification API plus robuste et moins détectable.

**Implémentation**:
- [ ] Analyser l'API TrendTrack pour l'authentification
- [ ] Créer un module d'authentification API
- [ ] Implémenter la gestion des tokens d'authentification
- [ ] Remplacer l'authentification DOM par l'API
- [ ] Tester la compatibilité avec le système existant
- [ ] Documenter les changements d'authentification

**Validation**:
- [ ] L'authentification API fonctionne correctement
- [ ] Le système TrendTrack utilise l'API au lieu du DOM
- [ ] Les performances sont maintenues ou améliorées
- [ ] La détectabilité est réduite
- [ ] La compatibilité avec le système existant est préservée

**Critères de succès**:
- Authentification API fonctionnelle
- Remplacement complet de l'authentification DOM
- Réduction de la détectabilité
- Maintien des performances
- Documentation complète

### T011: Identification et suppression des fichiers orphelins [P4]
**Type**: Infrastructure  
**Dependencies**: Aucune  
**Files**: Tous les fichiers du projet  
**Description**: Identifier et supprimer les fichiers orphelins qui ne sont plus utilisés par le code actuel.

**Objectif**: Nettoyer le projet en supprimant les fichiers obsolètes, les doublons et les résidus d'anciennes configurations.

**Implémentation**:
- [ ] Analyser tous les fichiers du projet pour identifier les références
- [ ] Identifier les fichiers non référencés dans le code
- [ ] Vérifier les fichiers de configuration obsolètes
- [ ] Identifier les bases de données orphelines (ex: trendtrack.db à la racine)
- [ ] Identifier les scripts de test non utilisés
- [ ] Identifier les fichiers de backup anciens
- [ ] Créer un rapport des fichiers orphelins identifiés
- [ ] Supprimer les fichiers orphelins confirmés
- [ ] Documenter les suppressions effectuées

**Validation**:
- [ ] Aucun fichier critique n'est supprimé par erreur
- [ ] Le projet fonctionne correctement après nettoyage
- [ ] Les performances sont maintenues ou améliorées
- [ ] La structure du projet est plus claire
- [ ] Les fichiers de backup importants sont préservés

**Critères de succès**:
- Fichiers orphelins identifiés et supprimés
- Projet plus propre et organisé
- Aucune régression fonctionnelle
- Documentation des suppressions
- Réduction de la confusion dans la structure du projet

**Exemples de fichiers orphelins identifiés**:
- ✅ `trendtrack-scraper-final/trendtrack.db` (supprimé - base orpheline)
- [ ] Autres fichiers à identifier lors de l'audit complet
