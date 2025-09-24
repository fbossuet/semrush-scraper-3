## V2 Scraper TrendTrack MVP — Spécification (modèle .specify)

### 1) Contexte et Objectif
- Problème originel: Taux d'échec élevé en Phase 3 (contextes Playwright fermés, sessions expirées), métriques manquantes/partielles.
- MVP V1: Architecture et classes présentes mais intégration incomplète; traitement par lots limité; AOV non extrait; 6/30 détails (≈20%).
- Objectif V2: Stabiliser et compléter l’extraction sur 100% des boutiques de la page cible, avec récupération automatique (contexte/session), retries intelligents, persistance correcte, conformité stricte.

### 2) Portée (Scope)
- In: Phase 1 (table) et Phase 3 (détails) TrendTrack, 1 page, 100 shops max/run, lots robustes, reprise après échec, logs, mapping DB, conformité aux règles du dépôt.
- Out: Scraper classique; `monthly_visits` (abandonné); scripts de test externes.

### 3) Invariants et Contraintes
- Documentation-first; VPS-only; logs existants immutables; pas de scripts de test; chemins relatifs depuis le répertoire base `/home/ubuntu/projects/shopshopshops/test`.
- DB: `trendtrack-scraper-final/data/trendtrack.db` (relatif), tables existantes; colonnes additionnelles validées (`live_ads_7d`, `live_ads_30d`).

### 4) Données à extraire
- Phase 1 (table): `shop_name`, `shop_url`, `total_products`, `year_founded` (si dispo), `external_id` (UUID via `<tr id>`), `live_ads` (texte tableau). `category` scrapable mais non persisté (hors schéma actuel).
- Phase 3 (détails): `live_ads_7d`, `live_ads_30d`, `pixel_google`, `pixel_facebook`, marchés (`market_us`, `market_uk`, `market_de`, `market_ca`, `market_au`, `market_fr`), `aov`.

### 5) Sélecteurs (Phase 1 — table)
- Ligne: `tbody tr` (UUID dans l’attribut `id` → `external_id`).
- `shop_name`: 2e `td` → `div:first-child p.text-sm.font-semibold`.
- `shop_url`: 2e `td` → `a[href*="http"]`.
- `total_products`: 3e `td` → `p.text-sm.font-semibold`.
- `category`: 4e `td` → `div div` (scrapable, non persisté).
- `year_founded`: 2e `td` → `p.text-[11px]` (parser l’année si présente).
- `live_ads`: 5e `td` → `p.font-bold` (texte brut).

### 6) Navigation
- Phase 1: Naviguer vers Trending Shops (URL complète avec filtres), `waitUntil: domcontentloaded`, puis `pageLoadPause`.
- Phase 3: Naviguer vers `https://app.trendtrack.io/fr/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops/{UUID}`, attendre `.flex.items-center.gap-2`.

### 7) Gestion Contexte/Session (Solutions obligatoires)
- Solution 1 (Contexte): détecter « Target page/context/browser has been closed », recréer contexte+page de manière transparente, rejouer l’opération via `MVPContextManager.executeWithContextRecovery(operation)`.
- Solution 3 (Session): détecter session expirée (URL/login, champs password, titre/login UI), relogger via `TrendTrackExtractor.login(page)` (`TRENDTRACK_PASSWORD`=Toulouse31!), rejouer via `MVPSessionManager.executeWithSessionRecovery(operation, extractor)`.
- Orchestration: `MVPRetryHandler.executeWithRetry(operation, contextKey, maxRetries)` combinant détection contexte+session et backoff exponentiel.

### 8) Politique de Retry
- `maxRetries`: 3 (configurable par type d’opération), backoff exponentiel (1s, 2s, 4s).
- Retryables: timeouts (navigation/sélecteurs), contexte fermé, session expirée, erreurs transitoires réseau/5xx.
- Non-retryables: auth invalide (4xx), sélecteurs durablement invalides, mapping DB invalide.

### 9) Traitement par lots (Batching & Reprise)
- Découpage par `batchSize` (défaut: 5).
- Continuer même si des boutiques échouent; ne pas interrompre les lots suivants.
- Marquer `failed` avec message; re-tentatives au prochain run.
- Pause inter-boutiques (`betweenShopsPause`) et inter-lots (`batchPause`).
- Ajout V2: « mini-retry » de fin de run pour les `failed` (1 passage, borné).

### 10) Mapping Base de Données
- Phase 1 upsert (table `shops`): `shop_name`, `shop_url` (UNIQUE), `external_id`, `year_founded`, `total_products`, `live_ads`, `scraping_status='table_extracted'`.
- Phase 3 update (table `shops`): `pixel_google`, `pixel_facebook`, `live_ads_7d`, `live_ads_30d`, `aov`, `market_*`, `scraping_status='details_extracted'`, `updated_at`.
- Index: conserver existants (`shop_url`, `external_id`, etc.).

### 11) Critères de Conformité
- Phase 1: 30/30 lignes extraites, 30/30 `external_id`, ≥80% `year_founded`.
- Phase 3: 100% des shops sélectionnés sont tentés; ≥90% succès/run (atteignable avec reprise multi-runs).
- AOV: non-nul sur ≥70% des shops traités (cible V2).
- Robustesse: aucune interruption due à context/session; récupération automatique visible dans les logs.

### 12) Journalisation (Logs)
- Respect immutabilité des logs existants; ajouter des logs V2: URL en cours, sélecteurs attendus, décisions retry, détections contexte/session, sauvegardes DB, comptages finaux (SQL).

### 13) Sécurité et Règles de Travail
- Exécution depuis `/home/ubuntu/projects/shopshopshops/test`.
- Backups avant migration; pas de scripts de test; suppression des scripts temporaires post-validation; pas de pollution git.

### 14) Écarts V1 → V2
- V1: 6/30 shops détails; AOV=0/30; arrêt implicite après échecs de lots; intégration MVP partielle.
- V2: intégration systématique retry+context+session; tolérance aux échecs; mini-retry global; amélioration AOV; vérifications SQL fin de run.

### 15) Plan de Remédiation (Solutions à implémenter)
- Envelopper TOUTES opérations critiques (nav/extract/save) par `MVPRetryHandler` (détection contexte+session).
- Modifier `processBatch` pour ne jamais bloquer les lots suivants; agréger résultats; tenter mini-retry final sur `failed`.
- Améliorer `extractAOV` (sélecteurs robustes, parsing numérique, fallback); logs dédiés.
- Consolider `year_founded` (regex année, fallback via texte "(X années)").
- Ajouter vérifications SQL automatiques fin de run (sans scripts de test dédiés).

### 16) /plan (Implémentation V2)
1. Intégrer `executeWithRetry` autour de: navigation Phase 1/3, extraction table/détails, sauvegardes.
2. Activer dans `MVPRetryHandler` les recouvrements `MVPContextManager` + `MVPSessionManager` (détections + recovery).
3. Refondre `processBatch` pour ignorer les erreurs bloquantes, consigner `failed`, et exécuter un mini-retry final borné.
4. Revoir `TrendTrackExtractor.extractAOV()` (nouveau sélecteur + parsing + fallback). Ajouter logs précis.
5. Renforcer `year_founded` (regex et fallback). Ajouter logs si non trouvé.
6. Ajouter logs décisionnels (retry, recovery, sélecteurs) + requêtes SQL de synthèse en fin de run.
7. Mettre à jour ce document à chaque incrément; valider sur VPS à chaque étape.
