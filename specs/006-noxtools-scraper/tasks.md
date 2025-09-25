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
Initialiser le scraper Noxtools (stealth headless), s'authentifier, naviguer vers la page cible, extraire les métriques, journaliser les résultats (pas d'enregistrement BDD). **Problèmes identifiés** : Session expirée Semrush, URLs incohérentes, nécessité d'un système de fallback serveurs dynamique.

### Tâches
1. ✅ [P0][Feature] Préparer la configuration anti‑détection de base (UA + headers + délais) selon `specs/002-headers-anti-detection`
2. ✅ [P0][Feature] Implémenter l'initialisation Playwright asyncio stealth headless (contexte persistant si requis)
3. ✅ [P0][Feature] Implémenter l'authentification via formulaire (intégration des nouveaux sélecteurs) et vérification succès
4. ✅ [P0][Feature] Implémenter la gestion de session/cookies entre domaines (connexion → Noxtools)
5. ✅ [P0][Feature] Implémenter la navigation vers l'URL finale Noxtools (fournie) avec garde timeouts
6. ✅ [P0][Feature] Implémenter l'extraction des métriques via sélecteurs DOM (fournis)
11. [P0][Feature] Implémenter la récupération du CPC (Alpha) et l'afficher en logs
7. [P1][Infrastructure] Ajouter paramètres timeouts/retry/délais (par défaut: 60s/3/2s) et backoff
8. [P1][Documentation] Ajouter Quickstart Alpha (comment lancer, variables requises, validations attendues)
9. [P1][Infrastructure] Mettre en place le logging (niveau, format ISO, fichier `logs/noxtools.log`) et screenshots sur erreurs critiques
10. [P1][Refactoring] Normaliser structure du projet `scraper-noxtools-final/` (core/models/services/utils)

11. [P1][Feature] Pré‑filtrage boutiques: commencer par market overview; si `visits` sans K/M ⇒ skip shop

12. [P0][Infrastructure] Calcul centralisé des paramètres URL (dateRange/country)
    - date = (date actuelle − 2 mois), jour fixé à 15 (ex: 2025‑09‑24 → 2025‑07‑15)
    - gérer correctement le passage Janvier/Février (année précédente)

13. [P0][Feature] Accès Market Overview par recherche
    - URL de base: `https://semrush1.semrush.pw/analytics/traffic/market-overview/`
    - Si présents: `input[name="competitors.0"]` et `button[data-testid="analyze-cta"]` → saisir domaine et valider
    - Sinon: utiliser `input[data-test="searchbar_input"]` et `button[data-test="searchbar_search_submit"]`
    - À chargement: si `*[data-testid="paywall"]` → fallback serveur (server2 → server5), puis recommencer le process
    - Après recherche: capturer l’URL de landing (ex: `.../market-overview/?searchType=domain&fid=1356045`) puis ajouter `dateRange` (calculée) et `country=us`

14. [P0][Feature] Formatage des données (pipeline dédié)
    - `33.3K` → `333000`; `33.3M` → `333000000` (supprimer séparateurs, appliquer multiplicateur)
    - Conversion des dates : ISO 8601 UTC pour logs/métadonnées, SQLite DATE pour BDD

15. [P0][Infrastructure] Récupération des URLs des shops à scraper
    - Sélectionner `shop_url` depuis `shops` uniquement si `analytics.scraping_status` est NULL (FK shops ↔ analytics)
    - S'inspirer du scraper actuel pour traitement par lots et stratégie anti‑détection (pauses aléatoires, etc.)

24. [P1][Infrastructure] **NOUVEAU** : Critères d'éligibilité des shops
    - Un shop est éligible si :
      - `shops.scraping_status` ≠ "failed"
      - `shops.details_scraping_status` = "details_extracted"
      - `analytics.scraping_status` = NULL (vide)
    - Mettre à jour la requête SQL dans `shop_repository.py`
    - Tester la nouvelle logique d'éligibilité

16. [P0][Feature] Mapping métriques ↔ base de données (TODO détaillé)

17. [P0][Feature] Mise à jour des statuts scraping
    - Toutes métriques valides: `scraping_status = completed`
    - Au moins une manquante: `partial`
    - Toutes manquantes: `failed`
    - Autres cas d’erreur: `failed`

18. [P1][Infrastructure] Fallback serveur (modal crash)
    - Si `*[data-ui-name="Modal.Overlay"]` détecté: renaviguer vers `https://semrush.noxtools.com/server2.php` et recommencer; poursuivre `server3` → `server5` si besoin
    - Si session perdue lors du fallback: repartir de la page de login puis naviguer vers serveur de fallback
    - Déclenchement global (peut survenir à n’importe quelle étape)

19. [P2][Improvement] Amélioration calcul CPC
    - Vérifier correspondance domaine ↔ phrase (sanity check du keyword/domain)

20. [P0][Feature] Scraper la métrique "branded traffic" et mapper → `analytics.branded_traffic`

21. [P0][Feature] **CRITIQUE** : Résoudre le problème de session expirée sur Semrush
    - Détecter "Session expired, access again from Dashboard" dans le contenu de page
    - Implémenter retry avec retour au formulaire de login et re-authentification complète
    - Relancer tout le processus de navigation après re-authentification

22. ✅ [P0][Infrastructure] **CRITIQUE** : Système de fallback serveurs dynamique
    - ✅ Créer ServerManager pour gérer semrush1→semrush5
    - ✅ Détecter l'indisponibilité d'un serveur (timeout, erreur 404, session expirée)
    - ✅ Maintenir la cohérence des URLs lors du switch (toutes les URLs doivent utiliser le même serveur)
    - ✅ Éviter le mélange semrush1/semrush2 dans les URLs

23. [P1][Infrastructure] Harmoniser les URLs avec la documentation
    - Utiliser semrush1.semrush.pw comme serveur principal (conforme à la doc)
    - Tester les deux domaines (semrush1 vs semrush3) pour identifier le bon
    - Mettre à jour toutes les URLs pour utiliser le serveur correct

### 🚨 Problèmes Identifiés (P0 - Critique)

#### Problème 1 : Session Expirée sur Semrush
- **Symptôme** : "Session expired, access again from Dashboard" sur toutes les URLs Semrush
- **Cause** : Session Noxtools ne se transmet pas vers Semrush
- **Impact** : Impossible d'accéder aux métriques
- **Solution** : Retry avec re-authentification complète

#### Problème 2 : URLs Incohérentes
- **Symptôme** : Documentation utilise semrush1, implémentation utilise semrush3
- **Cause** : URLs hardcodées différentes
- **Impact** : Risque de mélange de serveurs dans les URLs
- **Solution** : Système dynamique de serveurs avec cohérence

#### Problème 3 : Fallback Serveurs Non Cohérent ✅ RÉSOLU
- **Symptôme** : Switch de serveur sans mise à jour des URLs
- **Cause** : Pas de gestion centralisée des serveurs
- **Impact** : URLs incohérentes (semrush1 + semrush2)
- **Solution** : ✅ ServerManager implémenté avec URLs dynamiques et normalisation automatique

### 🎯 Actions Prioritaires

#### P0 - Critique (À faire immédiatement)
1. **Résoudre session expirée Semrush** : Implémenter retry avec re-authentification
2. ✅ **Créer ServerManager** : Système dynamique de gestion des serveurs
3. ✅ **Tester URLs Semrush** : Vérifier semrush1 vs semrush3
4. 🔄 **Créer script final main.py** : Orchestrer tous les modules selon la spec

#### P1 - Important (À faire ensuite)
1. **Harmoniser URLs** : Utiliser semrush1 comme dans la documentation
2. **Tester accès direct** : Vérifier si Semrush nécessite une authentification directe
3. **Valider credentials** : Vérifier la validité des credentials Noxtools
4. **Critères d'éligibilité shops** : Mettre à jour la logique de sélection des shops

#### P2 - Normal (À faire plus tard)
1. **Compléter configuration** : Vérifier tous les paramètres de scraping
2. **Tests d'intégration** : Valider le workflow complet
3. **Documentation** : Mettre à jour la documentation technique

### Inputs Fournis pour Alpha
- **Page de login** : https://noxtools.com/secure/login
- **Sélecteurs formulaire** : 
  - Identifiant : `#amember-login`
  - Mot de passe : `#amember-pass`
  - Bouton validation : `[type="submit"]`
- **Redirection après login** : https://noxtools.com/secure/member
- **URL finale avec paramètres** : https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507
- **Gestion session/cookies** : Maintenir entre domaines (noxtools.com → semrush1.semrush.pw)

### Note Version Beta
- **Paramètres URL dynamiques** : Pour la version Beta, il faudra rendre les paramètres de l'URL configurables (searchType, q, db, date) au lieu du hardcoding Alpha
- **Mécanique récupération paramètres URL** : Fournir la mécanique de récupération des paramètres URL (fid, dateRange, country) pour les métriques

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
4. [P0][Infrastructure] Mettre en place fallback pour domaine Noxtools en cas de 404 (domaines alternatifs, retry avec différents endpoints)
5. [P1][Infrastructure] Ajouter KPIs performance (latences, throughput, succès/échec) et export métriques
6. [P1][Infrastructure] Ajouter monitoring/alertes (logs de performance agrégés, seuils)
7. [P1][Documentation] Quickstart Finale (déploiement, tuning workers, seuils KPIs)

### Critères d'acceptation
- Débit amélioré avec contraintes respectées (rate limit, backoff)
- Aucun conflit de session/cookies, pas de corruption de données
- Fallback Noxtools opérationnel (détection 404, basculement automatique vers domaines alternatifs)
- KPIs disponibles et consultables, seuils et alertes opérationnels

---

## 🔗 Références
- Anti‑détection: `specs/002-headers-anti-detection/`
- Schéma & validation BDD: `specs/001-name-trendtrack-scraper/plan/data-model.md`
- Paramètres timeouts/retry: `sem-scraper-final/config.env`, `sem-scraper-final/parallel_config.py`

## 📝 Notes
- Respect des logs immuables; ajouter sans modifier l’existant
- Tests sur VPS uniquement, pas de scripts de test autonomes
- Nettoyage des fichiers temporaires/logs après validation utilisateur

#### Problème 3 : Fallback Serveurs Non Cohérent ✅ RÉSOLU
- **Symptôme** : Switch de serveur sans mise à jour des URLs
- **Cause** : Pas de gestion centralisée des serveurs
- **Impact** : URLs incohérentes (semrush1 + semrush2)
- **Solution** : ✅ ServerManager implémenté avec URLs dynamiques et normalisation automatique

### 🎯 Actions Prioritaires

#### P0 - Critique (À faire immédiatement)
1. **Résoudre session expirée Semrush** : Implémenter retry avec re-authentification
2. ✅ **Créer ServerManager** : Système dynamique de gestion des serveurs
3. ✅ **Tester URLs Semrush** : Vérifier semrush1 vs semrush3
4. 🔄 **Créer script final main.py** : Orchestrer tous les modules selon la spec

#### P1 - Important (À faire ensuite)
1. **Harmoniser URLs** : Utiliser semrush1 comme dans la documentation
2. **Tester accès direct** : Vérifier si Semrush nécessite une authentification directe
3. **Valider credentials** : Vérifier la validité des credentials Noxtools
4. **Critères d'éligibilité shops** : Mettre à jour la logique de sélection des shops

#### P2 - Normal (À faire plus tard)
1. **Compléter configuration** : Vérifier tous les paramètres de scraping
2. **Tests d'intégration** : Valider le workflow complet
3. **Documentation** : Mettre à jour la documentation technique

### Inputs Fournis pour Alpha
- **Page de login** : https://noxtools.com/secure/login
- **Sélecteurs formulaire** : 
  - Identifiant : `#amember-login`
  - Mot de passe : `#amember-pass`
  - Bouton validation : `[type="submit"]`
- **Redirection après login** : https://noxtools.com/secure/member
- **URL finale avec paramètres** : https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507
- **Gestion session/cookies** : Maintenir entre domaines (noxtools.com → semrush1.semrush.pw)

### Note Version Beta
- **Paramètres URL dynamiques** : Pour la version Beta, il faudra rendre les paramètres de l'URL configurables (searchType, q, db, date) au lieu du hardcoding Alpha
- **Mécanique récupération paramètres URL** : Fournir la mécanique de récupération des paramètres URL (fid, dateRange, country) pour les métriques

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
4. [P0][Infrastructure] Mettre en place fallback pour domaine Noxtools en cas de 404 (domaines alternatifs, retry avec différents endpoints)
5. [P1][Infrastructure] Ajouter KPIs performance (latences, throughput, succès/échec) et export métriques
6. [P1][Infrastructure] Ajouter monitoring/alertes (logs de performance agrégés, seuils)
7. [P1][Documentation] Quickstart Finale (déploiement, tuning workers, seuils KPIs)

### Critères d'acceptation
- Débit amélioré avec contraintes respectées (rate limit, backoff)
- Aucun conflit de session/cookies, pas de corruption de données
- Fallback Noxtools opérationnel (détection 404, basculement automatique vers domaines alternatifs)
- KPIs disponibles et consultables, seuils et alertes opérationnels

---

## 🔗 Références
- Anti‑détection: `specs/002-headers-anti-detection/`
- Schéma & validation BDD: `specs/001-name-trendtrack-scraper/plan/data-model.md`
- Paramètres timeouts/retry: `sem-scraper-final/config.env`, `sem-scraper-final/parallel_config.py`

## 📝 Notes
- Respect des logs immuables; ajouter sans modifier l’existant
- Tests sur VPS uniquement, pas de scripts de test autonomes
- Nettoyage des fichiers temporaires/logs après validation utilisateur
