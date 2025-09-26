# Tâches Noxtools Scraper

**Version**: V1  
**Date**: 2025-09-25  
**Statut**: Documentation officielle Noxtools Scraper

## 📋 Vue d'ensemble des Tâches

Ce document répertorie toutes les tâches liées au développement, maintenance et amélioration du scraper Noxtools.

---

## 🚨 Tâches P0 - Critiques (En attente)

### Workflow et Architecture

#### P0: Séparer clairement les 2 extractions - Overview (CPC uniquement) vs Market-Overview (autres métriques)
- **Type**: Bug Fix
- **Statut**: En attente
- **Description**: Le code actuel essaie d'extraire TOUTES les métriques depuis la page Overview (analytics/overview/), alors que selon la spec :
  - Overview → SEULEMENT CPC
  - Market-Overview → TOUTES les autres métriques
- **Problème identifié**: Le code mélange les 2 extractions au lieu de les séparer clairement

#### P0: Modifier extract_metrics() pour extraire SEULEMENT le CPC depuis Overview (analytics/overview/)
- **Type**: Feature
- **Statut**: En attente
- **Description**: Utiliser la page analytics/overview/ uniquement pour l'extraction du CPC
- **Actions**: Supprimer l'extraction des autres métriques depuis Overview

#### P0: Ajouter navigation vers Market-Overview (analytics/traffic/market-overview/) pour extraire toutes les autres métriques
- **Type**: Feature
- **Statut**: En attente
- **Description**: Naviguer vers analytics/traffic/market-overview/ pour extraire visits, organic, paid, conversion, etc.
- **Actions**: Implémenter la navigation vers Market-Overview après extraction CPC

#### P0: Implémenter extraction FID depuis Market-Overview après recherche domaine
- **Type**: Feature
- **Statut**: En attente
- **Description**: Recherche du domaine sur Market-Overview et extraction du FID depuis l'URL mise à jour
- **Actions**: Créer méthode _extract_fid_from_market_overview()

#### P0: Construire URL finale Market-Overview avec FID + paramètres pour extraction métriques
- **Type**: Feature
- **Statut**: En attente
- **Description**: URL finale : ?date=202507&q=cakesbody.com&searchType=domain&fid=1361959
- **Actions**: Créer méthode _build_market_overview_url_with_fid()

#### P0: Workflow complet en 2 étapes distinctes
- **Type**: Refactoring
- **Statut**: En attente
- **Description**: Implémenter le workflow complet :
  - Étape 1: Overview → CPC uniquement
  - Étape 2: Market-Overview → FID + autres métriques
- **Actions**: Modifier extract_metrics() pour séparer clairement les 2 étapes

#### P0: Ajouter la fonctionnalité scraper CPC (nouvelle métrique)
- **Type**: Feature
- **Statut**: En attente
- **Contexte**: Voir `spec.md` (section "Métriques attendues pour ce scraper")
- **Spécification détaillée**: Voir `integration-cpc.md` pour les détails techniques complets
- **Description**: Implémenter l'extraction de la métrique CPC depuis la page Overview avec :
  - Navigation vers `analytics/overview/` après Market-Overview
  - Maintien de session entre les deux pages (même serveur)
  - Scroll pour virtualisation SAP React
  - Parsing numérique avancé (K/M support)
  - Calcul du meilleur ratio CPC (volume/trafficPercent)
  - Retry avec scroll progressif
  - Enregistrement en base de données (champ `cpc` de type REAL)
- **Actions**:
  - Créer `_navigate_to_overview()` avec maintien de session
  - Créer `_extract_cpc_from_overview()` avec scroll et retry
  - Modifier `extract_metrics()` pour workflow complet (Market-Overview → Overview)
  - Implémenter le fallback avec détection d'échec pour Overview
  - Intégrer l'enregistrement CPC en base de données
- **Critères d'acceptation**:
  - [ ] Navigation Overview avec maintien de session
  - [ ] Extraction CPC avec scroll et retry fonctionnelle
  - [ ] Parsing numérique avancé (K/M) opérationnel
  - [ ] Calcul du meilleur ratio CPC correct
  - [ ] Enregistrement en BDD (champ `cpc` REAL)
  - [ ] Fallback Overview avec même mécanique que Market-Overview
  - [ ] Tests de validation CPC complets

#### P0: Documenter les sélecteurs de détection d'échec pour le fallback
- **Type**: Documentation
- **Statut**: En attente
- **Description**: Les sélecteurs de détection d'échec sont présents dans le code mais non documentés dans la spec :
  - "Session expired" dans le contenu de page
  - "access again from Dashboard" dans le contenu de page
  - "403" et "forbidden" dans le titre de page
  - len(page_content) <= 1000 caractères
  - Exceptions de navigation
- **Actions**: Ajouter section détaillée dans spec.md avec conditions de fallback

---

## ✅ Tâches Terminées

### Architecture et Structure
- ✅ **Création du scraper Noxtools** : Structure de base implémentée
- ✅ **Authentification Noxtools** : Login avec nouveaux sélecteurs
- ✅ **Navigation multi-domaines** : noxtools.com → semrush1.semrush.pw
- ✅ **Système de fallback serveurs** : semrush1→semrush5 avec ServerManager
- ✅ **Extraction CPC** : Méthode extract_cpc_best_ratio() fonctionnelle

---

## 📝 Notes de Développement

### Problèmes Identifiés
- **Duplication d'extraction** : Le code fait 2 fois la même chose (Overview + extract_cpc_best_ratio)
- **Mélange des extractions** : Tentative d'extraire toutes les métriques depuis Overview
- **Workflow incorrect** : Pas de séparation claire entre CPC et autres métriques

### Solutions Proposées
- **Séparer les extractions** : Overview pour CPC, Market-Overview pour autres métriques
- **Workflow en 2 étapes** : Navigation séparée pour chaque type de métriques
- **Réutilisation du code** : Utiliser les méthodes existantes sans duplication

---

## 🔄 Changements Récents

### 2025-09-25
- **Identification du problème** : Workflow incorrect identifié
- **Création des tâches P0** : 6 tâches critiques créées
- **Documentation** : Tâches sauvegardées dans tasks.md
- **Règles mises à jour** : .cursorrules modifié pour tasks.md dans spec

---

## 📚 Références

- **Spec principale** : [spec.md](./spec.md)
- **Plan d'implémentation** : [plan.md](./plan.md)
- **Code source** : `/home/ubuntu/projects/shopshopshops/test/scraper-noxtools-final/`
- **Règles de développement** : `/home/ubuntu/projects/shopshopshops/test/.cursorrules`
