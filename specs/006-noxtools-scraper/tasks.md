# Tâches Noxtools Scraper

**Version**: V1  
**Date**: 2025-09-25  
**Statut**: Documentation officielle Noxtools Scraper

## 📋 Vue d'ensemble des Tâches

Ce document répertorie toutes les tâches liées au développement, maintenance et amélioration du scraper Noxtools.

---

## 🚨 Tâches P0 - Critiques (En attente)

### Workflow et Architecture

#### P0: Modifier extract_metrics() pour extraire SEULEMENT le CPC depuis Overview (analytics/overview/)
- **Type**: Feature
- **Statut**: En attente
- **Description**: Utiliser la page analytics/overview/ uniquement pour l'extraction du CPC
- **Actions**: Supprimer l'extraction des autres métriques depuis Overview

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

#### P0: Gérer le fallback spécifique au sélecteur dashboard-container--IPQsK--shell sur Overview
- **Type**: Bug Fix
- **Statut**: En attente
- **Description**: Si le sélecteur `dashboard-container--IPQsK--shell` est détecté sur la page Overview lors de l'extraction CPC, cela indique un problème de serveur et nécessite un fallback vers le bridge pour changer de serveur
- **Contexte**: Cette condition spécifique doit être ajoutée aux conditions de détection d'échec pour la page Overview
- **Actions**:
  - Ajouter la détection du sélecteur `dashboard-container--IPQsK--shell` dans la méthode d'extraction CPC
  - Implémenter le fallback automatique vers le bridge (server suivant) si ce sélecteur est détecté
  - Intégrer cette condition dans le workflow de fallback Overview
  - Tester le fallback avec ce sélecteur spécifique
- **Critères d'acceptation**:
  - [ ] Détection du sélecteur `dashboard-container--IPQsK--shell` sur Overview
  - [ ] Fallback automatique vers bridge si sélecteur détecté
  - [ ] Changement de serveur (server1 → server2, etc.)
  - [ ] Retry de l'extraction CPC sur le nouveau serveur
  - [ ] Tests de validation du fallback avec ce sélecteur

#### P0: Documenter les sélecteurs de détection d'échec pour le fallback
- **Type**: Documentation
- **Statut**: En attente
- **Description**: Les sélecteurs de détection d'échec sont présents dans le code mais non documentés dans la spec :
  - "Session expired" dans le contenu de page
  - "access again from Dashboard" dans le contenu de page
  - "403" et "forbidden" dans le titre de page
  - len(page_content) <= 1000 caractères
  - Exceptions de navigation
  - **NOUVEAU**: `dashboard-container--IPQsK--shell` sur page Overview
- **Actions**: Ajouter section détaillée dans spec.md avec conditions de fallback

---

## ✅ Tâches Terminées

### Architecture et Structure
- ✅ **Création du scraper Noxtools** : Structure de base implémentée
- ✅ **Authentification Noxtools** : Login avec nouveaux sélecteurs
- ✅ **Navigation multi-domaines** : noxtools.com → semrush1.semrush.pw
- ✅ **Système de fallback serveurs** : semrush1→semrush5 avec ServerManager
- ✅ **Extraction CPC** : Méthode extract_cpc_best_ratio() fonctionnelle

### Workflow et Navigation
- ✅ **Navigation vers Market-Overview** : Implémentation de la navigation vers analytics/traffic/market-overview/ pour extraire visits, organic, paid, conversion, etc.
- ✅ **Extraction FID depuis Market-Overview** : Recherche du domaine sur Market-Overview et extraction du FID depuis l'URL mise à jour
- ✅ **Construction URL finale Market-Overview** : URL finale avec FID + paramètres (?date=202507&q=cakesbody.com&searchType=domain&fid=1361959)
- ✅ **Workflow complet en 2 étapes distinctes** : Implémentation du workflow complet (Overview → CPC uniquement, Market-Overview → FID + autres métriques)

---

## 📝 Notes de Développement


---

## 🔄 Changements Récents

### 2025-01-18
- **Mise à jour des tâches terminées** : 4 tâches P0 marquées comme terminées
- **Suppression tâche séparation** : Tâche de séparation des extractions supprimée
- **Documentation** : Section "Workflow et Navigation" ajoutée aux tâches terminées

### 2025-09-25
- **Création des tâches P0** : 6 tâches critiques créées
- **Documentation** : Tâches sauvegardées dans tasks.md
- **Règles mises à jour** : .cursorrules modifié pour tasks.md dans spec

---

## 📚 Références

- **Spec principale** : [spec.md](./spec.md)
- **Plan d'implémentation** : [plan.md](./plan.md)
- **Code source** : `/home/ubuntu/projects/shopshopshops/test/scraper-noxtools-final/`
- **Règles de développement** : `/home/ubuntu/projects/shopshopshops/test/.cursorrules`
