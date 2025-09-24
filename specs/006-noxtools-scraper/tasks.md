# Tâches : Scraper Noxtools

**Branche** : `006-noxtools-scraper`  
**Créé** : 2025-09-24  
**Statut** : Planifié (Alpha → Beta → Finale)

## 🔀 Organisation
- Priorités: P0 (critique), P1 (important), P2 (normal), P3 (faible)
- Types: Feature, Infrastructure, Documentation, Refactoring
- Statuts: En cours, En attente, Terminée, Annulée

---

## 🧪 Version Alpha — Test et Validation (sans BDD)

### Objectif
Initialiser le scraper Noxtools (stealth headless), s’authentifier, naviguer vers la page cible, extraire les métriques, journaliser les résultats (pas d’enregistrement BDD).

### Tâches
1. [P0][Feature] Préparer la configuration anti‑détection de base (UA + headers + délais) selon `specs/002-headers-anti-detection`
2. [P0][Feature] Implémenter l’initialisation Playwright asyncio stealth headless (contexte persistant si requis)
3. [P0][Feature] Implémenter l’authentification via formulaire (intégration des nouveaux sélecteurs) et vérification succès
4. [P0][Feature] Implémenter la gestion de session/cookies entre domaines (connexion → Noxtools)
5. [P0][Feature] Implémenter la navigation vers l’URL finale Noxtools (fournie) avec garde timeouts
6. [P0][Feature] Implémenter l’extraction des métriques via sélecteurs DOM (fournis)
7. [P1][Infrastructure] Ajouter paramètres timeouts/retry/délais (par défaut: 60s/3/2s) et backoff
8. [P1][Documentation] Ajouter Quickstart Alpha (comment lancer, variables requises, validations attendues)
9. [P1][Infrastructure] Mettre en place le logging (niveau, format ISO, fichier `logs/noxtools.log`) et screenshots sur erreurs critiques
10. [P1][Refactoring] Normaliser structure du projet `scraper-noxtools-final/` (core/models/services/utils)

### Critères d’acceptation
- Démarrage ok en headless stealth, login passe, navigation atteint l’URL cible
- Métriques affichées en logs (DEBUG/INFO), erreurs gérées sans crash global
- Paramètres (timeouts, retry, délais) configurables
- Aucun write en BDD

---

## 🧩 Version Beta — Formatage et Enregistrement BDD

### Objectif
Formater les données, valider, mapper et enregistrer dans `analytics` avec correspondance `shops`.

### Tâches
1. [P0][Infrastructure] Définir chemin BDD (variable de config) et vérification d’accès
2. [P0][Feature] Définir mapping Noxtools → `analytics` (champ à champ) et documenter dans `spec.md`
3. [P0][Feature] Implémenter le module de formatage (types, plages, normalisation, ISO dates)
4. [P0][Feature] Ajouter la validation (types, ranges, relations FK vers `shops`, complétude)
5. [P0][Feature] Implémenter l’enregistrement en BDD (insert/update idempotent par `shop_id`)
6. [P1][Feature] Implémenter 1 métrique calculée à partir des données scrapées (définition fournie)
7. [P1][Infrastructure] Gestion d’erreurs de sauvegarde (fallbacks, rollback local, logs)
8. [P1][Documentation] Mettre à jour Quickstart Beta (pré‑requis BDD, vérifications, commandes)

### Critères d’acceptation
- Données formatées selon standards (INTEGER/NUMERIC/ISO)
- Écriture réussie dans `analytics` avec FK valide `shops.shop_id`
- Métrique calculée ajoutée et tracée
- Stratégie d’erreurs documentée et testée (cas d’échec de write)

---

## ⚡ Version Finale — Optimisation et Parallélisation

### Objectif
Optimiser les performances et paralléliser le scraping avec monitoring et limites.

### Tâches
1. [P0][Infrastructure] Définir configuration des workers (nombre, répartition, priorités, staggering)
2. [P0][Feature] Implémenter exécution parallèle sécurisée (locks, profiling sessions, isolation cookies)
3. [P0][Infrastructure] Implémenter rate‑limit/token bucket (p/min, burst) et backoff adaptatif
4. [P1][Infrastructure] Ajouter KPIs performance (latences, throughput, succès/échec) et export métriques
5. [P1][Infrastructure] Ajouter monitoring/alertes (logs de performance agrégés, seuils)
6. [P1][Documentation] Quickstart Finale (déploiement, tuning workers, seuils KPIs)

### Critères d’acceptation
- Débit amélioré avec contraintes respectées (rate limit, backoff)
- Aucun conflit de session/cookies, pas de corruption de données
- KPIs disponibles et consultables, seuils et alertes opérationnels

---

## 🔗 Références
- Anti‑détection: `specs/002-headers-anti-detection/`
- Schéma & validation BDD: `specs/001-name-trendtrack-scraper/plan/prod_schema.sql`
- Paramètres timeouts/retry: `sem-scraper-final/config.env`, `sem-scraper-final/parallel_config.py`

## 📝 Notes
- Respect des logs immuables; ajouter sans modifier l’existant
- Tests sur VPS uniquement, pas de scripts de test autonomes
- Nettoyage des fichiers temporaires/logs après validation utilisateur
