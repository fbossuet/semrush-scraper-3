# Spécification de Fonctionnalité : Scraper Noxtools

**Branche de Fonctionnalité** : `006-noxtools-scraper`  
**Créé** : 2025-01-18  
**Statut** : Version Alpha en cours  
**Entrée** : Description utilisateur : "Créer un nouveau scraper dans un dossier scraper-noxtools-final qui reproduit les fonctionnalités du scraper SEM existant mais adapté pour Noxtools avec de nouveaux sélecteurs et une navigation vers un autre domaine."

## Versions de Développement

### Version Alpha - Test et Validation
**Objectif** : Récupération des métriques sans enregistrement en BDD
- Initialisation Playwright stealth headless
- Authentification avec nouveaux sélecteurs
- Navigation vers Noxtools
- Scraping des métriques pour validation
- Logs détaillés des données récupérées
- **PAS d'enregistrement en base de données**

### Version Beta - Formatage et Enregistrement
**Objectif** : Formatage des données et enregistrement en BDD
- Toutes les fonctionnalités de la version Alpha
- Formatage des données selon les standards définis
- Enregistrement dans la table analytics
- Correspondance avec la table shops
- Validation de l'intégrité des données
- Gestion des erreurs de sauvegarde

### Version Finale - Optimisation et Parallélisation
**Objectif** : Performance optimale avec scraping parallèle
- Toutes les fonctionnalités des versions Alpha et Beta
- Optimisation des performances
- Scraping parallèle avec workers
- Gestion avancée des timeouts adaptatifs
- Monitoring et métriques de performance
- Déploiement en production

## Environnement et Contraintes

### Répertoire de Travail
- **Répertoire principal** : `/home/ubuntu/projects/shopshopshops/test/`
- **Dossier du scraper** : `scraper-noxtools-final/`
- **Chemins relatifs** : Utiliser `os.getcwd()` + chemins relatifs pour la portabilité
- **Interdiction** : Ne jamais aller dans `/home/ubuntu/trendtrack-scraper-final/` ou autres répertoires

### Bases de Données
- **Base de production** : `trendtrack-scraper-final/data/trendtrack.db` (chemin relatif)
- **Endpoint principal** : Utilise `trendtrack.db` (production) pour les données réelles
- **Scraper TrendTrack** : Utilise la base de production (`trendtrack.db`)
- **Scraper SEM** : Utilise la base de production (`trendtrack.db`)
- **Scraper Noxtools** : Utilise la base de production (`trendtrack.db`)

### Contraintes Techniques
- **Développement** : Exclusivement sur le VPS, jamais en local
- **Validation** : L'utilisateur valide chaque modification via test sur le VPS
- **Logs immutables** : Jamais modifier les messages de logs existants
- **Approche adaptative** : Validation des métriques par comptage dynamique
- **Nettoyage post-validation** : Supprimer les fichiers de test/rapports après validation utilisateur

### Procédure de Développement
- **Architecture modulaire** : Chaque fonctionnalité dans un module séparé
- **Tests temporaires** : Commandes Python en ligne pour tester chaque module individuellement
- **Script final** : Fichier `main.py` qui orchestre tous les modules ensemble
- **Workflow de test** : Test temporaire → Validation → Intégration dans script final
- **Validation utilisateur** : Chaque modification doit être validée par l'utilisateur via test sur le VPS

### Structure du Script Final
Le script `main.py` doit être le reflet du test temporaire le plus abouti et inclure :

#### Modules à Intégrer
- `core/server_manager.py` - Gestion des serveurs Semrush
- `core/playwright_manager.py` - Navigation et anti-détection
- `core/auth_manager.py` - Authentification Noxtools
- `core/session_manager.py` - Gestion des sessions
- `core/metrics_extractor.py` - Extraction des métriques
- `core/market_overview_navigator.py` - Navigation Market Overview
- `services/shop_repository.py` - Récupération des boutiques
- `services/database_saver.py` - Sauvegarde des métriques en BDD
- `services/formatter.py` - Formatage des données
- `services/status_manager.py` - Gestion des statuts

#### Workflow du Script Final
1. **Initialisation** : Créer et configurer tous les modules
2. **Authentification** : S'authentifier sur Noxtools
3. **Récupération** : Récupérer les boutiques éligibles depuis la base de données
4. **Scraping** : Pour chaque boutique (navigation → extraction unifiée → formatage)
5. **Sauvegarde** : Enregistrer les métriques en base de données
6. **Gestion d'erreurs** : Gérer les erreurs et le fallback automatique
7. **Nettoyage** : Nettoyer les ressources et fermer les connexions

#### Workflow de Scraping Détaillé

##### Workflow Principal
```
1. ACCÈS À LA PAGE DE LOGIN
   ↓
   https://noxtools.com/secure/login
   ↓
2. AUTHENTIFICATION
   ↓
   Remplir formulaire (username/password)
   ↓
3. REDIRECTION VERS DASHBOARD
   ↓
   https://noxtools.com/secure/member
   ↓
4. TEST D'ACCÈS DIRECT À SEMRUSH
   ↓
   Tentative navigation vers Market-Overview
   ↓
5. VÉRIFICATION DE LA SESSION
   ↓
   Test Market-Overview → Vérification contenu page
   ↓
   ┌─────────────────────────────────────┐
   │ SI ÉCHEC DÉTECTÉ                   │
   │ ↓                                  │
   │ 6A. RETOUR À LA PAGE DE LOGIN      │
   │ ↓                                  │
   │ 7A. RÉAUTHENTIFICATION             │
   │ ↓                                  │
   │ 8A. RETOUR AU DASHBOARD            │
   │ ↓                                  │
   │ 9A. UTILISATION DU BRIDGE          │
   │ ↓                                  │
   │ https://semrush.noxtools.com/server1.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server2.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server3.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server4.php │
   │ ↓                                  │
   │ SI ÉCHEC → https://semrush.noxtools.com/server5.php │
   │ ↓                                  │
   │ SI TOUS ÉCHEC → ERREUR CRITIQUE    │
   └─────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────┐
   │ SI SUCCÈS                           │
   │ ↓                                  │
   │ 6B. CONTINUER SANS BRIDGE          │
   │ ↓                                  │
   │ 7B. NAVIGATION VERS MARKET-OVERVIEW │
   │ ↓                                  │
   │ 8B. EXTRACTION DES MÉTRIQUES       │
   └─────────────────────────────────────┘
```

##### Conditions de Détection d'Échec

**Session Expirée**
```
SI page_content contient :
- "Session expired"
- "access again from Dashboard"
- "session expired"
- "please login again"
- "authentication required"
→ ÉCHEC DÉTECTÉ
```

**Erreur d'Accès**
```
SI page_title contient :
- "403"
- "forbidden"
→ ÉCHEC DÉTECTÉ
```

**Page Vide/Erreur**
```
SI len(page_content) <= 1000 caractères
→ ÉCHEC DÉTECTÉ
```

**Exception de Navigation**
```
SI timeout ou erreur de chargement
→ ÉCHEC DÉTECTÉ
```

##### Correspondance Bridge → Serveur Final avec URLs

```
Bridge server1.php → Navigation automatique vers https://semrush1.semrush.pw/analytics/traffic/market-overview/
Bridge server2.php → Navigation automatique vers https://semrush2.semrush.pw/analytics/traffic/market-overview/
Bridge server3.php → Navigation automatique vers https://semrush3.semrush.pw/analytics/traffic/market-overview/
Bridge server4.php → Navigation automatique vers https://semrush4.semrush.pw/analytics/traffic/market-overview/
Bridge server5.php → Navigation automatique vers https://semrush5.semrush.pw/analytics/traffic/market-overview/
```

##### Workflow de Fallback Bridge

```
ÉCHEC DÉTECTÉ
↓
RETOUR AU LOGIN
↓
RÉAUTHENTIFICATION
↓
DASHBOARD
↓
BRIDGE https://semrush.noxtools.com/server1.php
↓
SI ÉCHEC → BRIDGE https://semrush.noxtools.com/server2.php
↓
SI ÉCHEC → BRIDGE https://semrush.noxtools.com/server3.php
↓
SI ÉCHEC → BRIDGE https://semrush.noxtools.com/server4.php
↓
SI ÉCHEC → BRIDGE https://semrush.noxtools.com/server5.php
↓
SI TOUS ÉCHEC → ERREUR CRITIQUE
```

##### Exemple Concret de Fallback

```
1. Test direct : https://semrush2.semrush.pw/analytics/traffic/market-overview/
   ↓
   ÉCHEC DÉTECTÉ : "Session expired, access again from Dashboard"
   ↓
2. Retour au login → Réauthentification → Dashboard
   ↓
3. Bridge : https://semrush.noxtools.com/server3.php
   ↓
4. Navigation automatique vers : https://semrush3.semrush.pw/analytics/traffic/market-overview/
   ↓
5. Maintien de la session entre bridge et serveur final
   ↓
6. Extraction des métriques
```

##### Workflow Final

```
1. Login → Dashboard
2. Test Market-Overview (accès direct)
3. SI ÉCHEC → Retour Login → Bridge server1.php → semrush1.semrush.pw
4. SI ÉCHEC → Bridge server2.php → semrush2.semrush.pw
5. SI ÉCHEC → Bridge server3.php → semrush3.semrush.pw
6. SI ÉCHEC → Bridge server4.php → semrush4.semrush.pw
7. SI ÉCHEC → Bridge server5.php → semrush5.semrush.pw
8. SI TOUS ÉCHEC → ERREUR
9. SI SUCCÈS → Extraction métriques
```

##### Clarification Importante

- **Le bridge** : Utilisé pour **maintenir la session** entre Noxtools et Semrush
- **Le serveur final** : Détermine vers quel serveur Semrush naviguer après le bridge
- **Navigation entre serveurs** : Le bridge navigue vers un autre serveur si l'actuel est inaccessible
- **Maintien de session** : Le bridge maintient la session et les cookies entre le bridge et le serveur Semrush final
- **Navigation automatique** : Une fois redirigé vers une URL, il faut absolument maintenir cette URL (pas de semrush1 puis semrush2 par exemple)

**Le bridge est un intermédiaire de session ET un redirecteur de serveur en cas d'échec, avec maintien strict de l'URL choisie !**

### Exigences de Sécurité et Validation
- **Backup obligatoire** : Avant toute modification
- **Test de compilation** : Python avant upload (`py_compile`)
- **Rollback immédiat** : Si validation échoue
- **Vérification des effets de bord** : Avant de dire "c'est OK"
- **Test de déploiement complet** : Sur le VPS
- **Validation utilisateur** : Obligatoire pour chaque modification
- **NE JAMAIS dire "c'est OK"** : Sans avoir testé tous les composants
- **Nettoyage post-validation** : Supprimer immédiatement les fichiers temporaires après usage
- **Pas de pollution Git** : Ne jamais committer de fichiers de debug/test/temporaires

### Gestion Git et Versioning
- **Fichiers à committer** : Code source principal, configurations, documentation (.md)
- **Fichiers à EXCLURE** : Scripts de debug, de test, fichiers temporaires, logs
- **Règle de commit** : Commiter après validation utilisateur d'un test réussi
- **Timing des commits** : Quand l'utilisateur confirme qu'une modification fonctionne
- **Nettoyage obligatoire** : Supprimer les fichiers temporaires après usage (voir règles de sécurité)

### Règles d'attribution du `scraping_status` (générales)
- **failed (par défaut)** : si aucun statut n'est explicitement fourni par le scraper au moment de l'insert/update dans `analytics`
- **failed** : s'il manque au moins UNE des métriques attendues par ce scraper pour la table `analytics`, ou si une de ces métriques est invalide (format/type incorrect)
- **completed** : uniquement si TOUTES les métriques attendues par ce scraper sont présentes et enregistrées au bon format en base de données

Notes d'implémentation:
1. Construire l'objet complet des métriques attendues avant écriture
2. Valider présence et format/type de chaque champ attendu
3. Déterminer `scraping_status` selon les règles ci-dessus (valeur par défaut = `failed`)
4. Écrire dans `analytics` avec le statut calculé, puis consigner `updated_at`

### Métriques attendues pour ce scraper (référence unique)
- `visits`
- `traffic`
- `organic_traffic`
- `paid_search_traffic`
- `avg_visit_duration`
- `bounce_rate`
- `percent_branded_traffic`
- `conversion_rate`
- `branded_traffic`
- `cpc`
- **Documentation** : TOUS les fichiers .md doivent être committés
- **Code source** : Seulement les modifications validées et testées

### Références Importantes
- **Constitution** : `.specify/memory/constitution.md`
- **Documentation** : `docs/analysis/` et `specs/001-name-trendtrack-scraper/`
- **Procédures** : `docs/procedures/metric_addition_procedure.md`
- **Workspace** : `README_WORKSPACE.md`

### Changements Récents (2025-09-24)
- **Chemins absolus → relatifs** : Conversion complète pour la portabilité
- **Scraper TrendTrack** : Fonctionne avec chemins relatifs (614 boutiques)
- **API** : Port 8001, chemins relatifs, lancement depuis /test/
- **Bases de données** : Chemins relatifs, scraper utilise trendtrack.db
- **Règles de sécurité** : Renforcées avec validation obligatoire

### État Actuel

### Règles de Test et Debug
- **Surveillance des logs en temps réel** : TOUJOURS lancer les scripts en arrière-plan avec redirection vers un fichier de log
- **Arrêt automatique** : Arrêter le script après un certain nombre d'erreurs ou après un temps défini
- **Analyse des logs** : Analyser les logs en temps réel pour identifier les problèmes
- **Workflow de test** :
  1. Lancer le script : `node script.js > test-debug.log 2>&1 &`
  2. Surveiller les logs : `tail -f test-debug.log`
  3. Arrêter après erreurs : `pkill -f "node script.js"`
  4. Analyser les logs : `grep -E "(ERROR|❌|⚠️)" test-debug.log`
- **Nettoyage des logs** : Supprimer les fichiers de log après analyse
- **Pas de tests longs** : Éviter les tests sur 150+ boutiques, privilégier les tests courts et ciblés

### État Actuel du Scraper Noxtools
- ✅ **ServerManager** : Implémenté et testé (gestion serveurs semrush1→semrush5)
- ✅ **Modules** : Tous les modules créés et intégrés
- ✅ **Tests** : Tests complets du ServerManager passent
- ✅ **Documentation** : Mise à jour et cohérente
- 🔄 **Script final** : En cours de création (main.py)
- ✅ **Base de données** : Chemin à corriger pour l'accès
- 📋 **Prochaines étapes** : Créer le script final et tester en production

### Problèmes Identifiés et Résolus
- ✅ **Problème 1** : Session expirée Semrush - Retry avec re-authentification implémenté
- ✅ **Problème 2** : URLs incohérentes - ServerManager avec normalisation automatique
- ✅ **Problème 3** : Fallback serveurs non cohérent - ServerManager dynamique implémenté
- ✅ **Problème 4** : Logique de fallback incorrecte - Corrigée dans server_manager.py
- ✅ **Problème 5** : Incohérence dans les logs - Corrigée dans market_overview_navigator.py
- ✅ **Problème 6** : Incohérence dans les imports - Corrigée dans metrics_extractor.py

### Actions Prioritaires
1. ✅ **Créer ServerManager** : Système dynamique de gestion des serveurs
2. ✅ **Intégrer ServerManager** : Dans tous les modules (market_overview_navigator, metrics_extractor, main)
3. ✅ **Tester ServerManager** : Tests complets et validation
4. ✅ **Mettre à jour documentation** : Spec, plan, tasks avec ServerManager
5. 🔄 **Créer script final** : main.py propre et fonctionnel
6. 📋 **Tester en production** : Validation complète du scraper
7. 📋 **P1 - Validation format visits** : Implémenter la validation du format K/M pour visits et marquer en "failed" si invalide

### Résumé de l'Intégration
**Le contenu du `.cursorrules` a été intégré dans la spécification avec les sections suivantes :**

1. **Environnement et Contraintes** : Répertoire de travail, bases de données, contraintes techniques
2. **Procédure de Développement** : Architecture modulaire, tests temporaires, script final
3. **Structure du Script Final** : Modules à intégrer, workflow du script
4. **Exigences de Sécurité et Validation** : Backup, tests, rollback, validation utilisateur
5. **Gestion Git et Versioning** : Fichiers à committer, règles de commit, nettoyage
6. **Références Importantes** : Constitution, documentation, procédures
7. **Changements Récents** : Chemins relatifs, état des composants
8. **Règles de Test et Debug** : Surveillance des logs, workflow de test
9. **État Actuel** : Projet global et scraper Noxtools
10. **Problèmes Identifiés et Résolus** : Liste des problèmes et solutions
11. **Actions Prioritaires** : Plan d'action et statut des tâches

**La spécification est maintenant complète et cohérente avec les règles de développement.**

## Scénarios Utilisateur & Tests *(obligatoire)*

### Histoire Utilisateur Principale
En tant qu'analyste de données, je veux que le système de scraping Noxtools récupère automatiquement les métriques de performance des boutiques depuis Noxtools, afin de pouvoir analyser les tendances du marché e-commerce et identifier les opportunités commerciales avec des données complémentaires à celles de SEM Rush.

### Scénarios d'Acceptation
1. **Étant donné** un système de scraping Noxtools configuré, **Quand** le système s'initialise, **Alors** il devrait configurer Playwright en mode stealth headless avec les paramètres anti-détection appropriés (xvfb également)
2. **Étant donné** un système de scraping avec des credentials valides, **Quand** le système s'authentifie, **Alors** il devrait remplir le formulaire de connexion avec les nouveaux sélecteurs et maintenir la session
3. **Étant donné** une session authentifiée, **Quand** le système navigue vers Noxtools, **Alors** il devrait maintenir les cookies et la session entre les domaines
4. **Étant donné** une liste de boutiques éligibles, **Quand** le système scrape les métriques, **Alors** il devrait appliquer une logique anti-détection pour chaque boutique
5. **Étant donné** des métriques scrapées, **Quand** le système enregistre les résultats, **Alors** il devrait sauvegarder dans la table analytics avec correspondance avec la table shops
6. **Étant donné** des erreurs de scraping, **Quand** le système rencontre des problèmes, **Alors** il devrait appliquer une logique de retry et timeout adaptatifs

### Cas Limites
- Que se passe-t-il quand l'authentification Noxtools échoue ?
- Comment le système gère-t-il la navigation entre domaines différents ?
- Que se passe-t-il quand les sélecteurs DOM changent ?
- Comment le système gère-t-il les timeouts adaptatifs ?
- Que se passe-t-il quand la base de données est inaccessible ?
- Que se passe-t-il quand la session Semrush expire ?
- Comment le système gère-t-il le fallback entre serveurs Semrush ?
- Que se passe-t-il quand un serveur Semrush devient indisponible ?

## Exigences *(obligatoire)*

### Exigences Fonctionnelles

#### Initialisation et Configuration
- **NOX-001** : Le système DOIT initialiser Playwright en mode asyncio avec stealth headless activé
- **NOX-002** : Le système DOIT configurer les paramètres anti-détection identiques au scraper SEM existant
- **NOX-003** : Le système DOIT gérer la configuration du display virtuel (Xvfb) sur Linux
- **NOX-004** : Le système DOIT appliquer les headers anti-détection et la rotation des User-Agents

#### Authentification et Session
- **NOX-005** : Le système DOIT s'authentifier via un formulaire avec les nouveaux sélecteurs fournis
- **NOX-006** : Le système DOIT maintenir la session et les cookies entre la connexion et la navigation
- **NOX-007** : Le système DOIT gérer la navigation vers un nouveau domaine (Noxtools)
- **NOX-008** : Le système DOIT préserver l'authentification lors du changement de domaine
- **NOX-009** : Le système DOIT gérer la reconnexion automatique en cas de perte de session
- **NOX-010** : Le système DOIT détecter les sessions expirées et relancer l'authentification complète
- **NOX-011** : Le système DOIT gérer le fallback entre serveurs Semrush (semrush1→semrush5)

#### Navigation et Scraping
- **NOX-012** : Le système DOIT naviguer vers la nouvelle page de métriques Noxtools
- **NOX-013** : Le système DOIT récupérer la liste des boutiques éligibles depuis la base de données
- **NOX-014** : Le système DOIT filtrer les boutiques selon les critères d'éligibilité (shops.scraping_status ≠ "failed", details_scraping_status = "details_extracted", analytics.scraping_status = NULL)
- **NOX-015** : Le système DOIT appliquer une logique anti-détection pour chaque boutique scrapée
- **NOX-016** : Le système DOIT extraire les métriques spécifiques avec les nouveaux sélecteurs DOM
- **NOX-017** : Le système DOIT maintenir la cohérence des URLs lors du fallback serveurs

#### Gestion des Données
- **NOX-018** : Le système DOIT enregistrer les résultats dans la table analytics
- **NOX-019** : Le système DOIT respecter la correspondance avec la table shops via les clés étrangères
- **NOX-020** : Le système DOIT gérer les métriques spécifiques à Noxtools
- **NOX-021** : Le système DOIT valider l'intégrité des données avant sauvegarde
- **NOX-022** : Le système DOIT valider le format des métriques visits (doit contenir K ou M) et marquer la boutique en statut "failed" si le format est invalide

#### Robustesse et Performance
- **NOX-023** : Le système DOIT implémenter une logique de retry adaptative
- **NOX-024** : Le système DOIT gérer les timeouts adaptatifs selon le type d'opération
- **NOX-025** : Le système DOIT gérer les erreurs gracieusement sans arrêter le processus global
- **NOX-026** : Le système DOIT fournir des logs détaillés pour le debugging
- **NOX-027** : Le système DOIT optimiser les performances pour le scraping en parallèle

### Exigences par Version

#### Version Alpha - Test et Validation
- **NOX-ALPHA-001** : Le système DOIT initialiser Playwright en mode stealth headless (NOX-001)
- **NOX-ALPHA-002** : Le système DOIT s'authentifier avec les nouveaux sélecteurs (NOX-005)
- **NOX-ALPHA-003** : Le système DOIT naviguer vers Noxtools et maintenir la session (NOX-007, NOX-008)
- **NOX-ALPHA-004** : Le système DOIT extraire les métriques avec les nouveaux sélecteurs (NOX-016)
- **NOX-ALPHA-005** : Le système DOIT logger les données récupérées sans enregistrement en BDD
- **NOX-ALPHA-006** : Le système DOIT gérer les erreurs de scraping gracieusement (NOX-024)
- **NOX-ALPHA-007** : Le système DOIT détecter les sessions expirées et relancer l'authentification (NOX-010)
- **NOX-ALPHA-008** : Le système DOIT gérer le fallback entre serveurs Semrush (NOX-011)
- **NOX-ALPHA-009** : Le système DOIT maintenir la cohérence des URLs lors du fallback (NOX-017)
- **NOX-ALPHA-010** : Le système DOIT appliquer les critères d'éligibilité des shops (NOX-014)
- **NOX-ALPHA-011** : Le système DOIT valider le format des métriques visits (NOX-022)

#### Version Beta - Formatage et Enregistrement
- **NOX-BETA-001** : Le système DOIT implémenter toutes les fonctionnalités de la version Alpha
- **NOX-BETA-002** : Le système DOIT formater les métriques selon les standards définis
- **NOX-BETA-003** : Le système DOIT valider l'intégrité des données avant sauvegarde (NOX-021)
- **NOX-BETA-004** : Le système DOIT enregistrer dans la table analytics (NOX-018)
- **NOX-BETA-005** : Le système DOIT respecter la correspondance avec la table shops (NOX-019)
- **NOX-BETA-006** : Le système DOIT gérer les erreurs de formatage et de sauvegarde

#### Version Finale - Optimisation et Parallélisation
- **NOX-FINAL-001** : Le système DOIT implémenter toutes les fonctionnalités des versions Alpha et Beta
- **NOX-FINAL-002** : Le système DOIT optimiser les performances de scraping (NOX-026)
- **NOX-FINAL-003** : Le système DOIT implémenter le scraping parallèle avec workers
- **NOX-FINAL-004** : Le système DOIT gérer les timeouts adaptatifs avancés (NOX-023)
- **NOX-FINAL-005** : Le système DOIT mettre en place un fallback pour le domaine Noxtools en cas de 404
- **NOX-FINAL-006** : Le système DOIT fournir des métriques de performance et monitoring
- **NOX-FINAL-007** : Le système DOIT être prêt pour le déploiement en production

### Entités Clés *(inclure si la fonctionnalité implique des données)*
- **Boutique Noxtools** : Représente une boutique avec ses métriques Noxtools spécifiques
- **Session Noxtools** : Représente une session de scraping Noxtools avec authentification maintenue
- **Métriques Noxtools** : Représente les données de performance spécifiques à Noxtools
- **Configuration Anti-Détection** : Représente les paramètres de stealth et anti-détection
- **Base de Données Partagée** : Base SQLite partagée entre les systèmes TrendTrack, SEM et Noxtools

### Standards de Format de Données
- **Dates pour logs/métadonnées** : Format ISO 8601 UTC (ex: "2025-01-18T10:30:45.123Z")
- **Dates pour base de données** : Format SQLite TEXT avec format ISO 8601 (métadonnées)
- **Python** : 
  - Logs : `datetime.utcnow().isoformat() + 'Z'`
  - BDD : `datetime.utcnow().date().isoformat()`
- **JavaScript** : Utiliser `new Date().toISOString()`
- **SQLite** : 
  - Champ `scraped_at` : TEXT avec format ISO 8601 (métadonnées)
  - Champ `updated_at` : TEXT avec format ISO 8601 (métadonnées)

### Inputs Nécessaires par Version

#### Version Alpha - Test et Validation
**Inputs Identifiés :**
- ✅ **Sélecteurs et navigation** : Authentification puis navigation
- ✅ **URL finale** : Vers les données à capturer
- ✅ **Sélecteurs des métriques** : Extraction des données Noxtools
- ✅ **Credentials d'authentification** : Login/password Noxtools
- ✅ **Configuration anti-détection** : User-Agents, headers, délais (voir specs 002-headers-anti-detection)
- ✅ **Paramètres de scraping** : Timeouts, retry, délais entre requêtes (voir sem-scraper-final/config.env)

**Inputs Fournis :**
- ✅ **Page de login** : https://noxtools.com/secure/login
- ✅ **Sélecteurs formulaire** : 
  - Identifiant : `id="amember-login"`
  - Mot de passe : `id="amember-pass"`
  - Bouton validation : `type="submit"`
- ✅ **Redirection après login** : https://noxtools.com/secure/member
- ✅ **ÉTAPE 1 - Market-Overview (Autres métriques)** : https://semrush1.semrush.pw/analytics/traffic/market-overview/?date=202507&q=cakesbody.com&searchType=domain&fid=1361959
- ✅ **Gestion session/cookies** : Maintenir entre domaines (noxtools.com → semrush1.semrush.pw)

### 4. Retry avec Scroll
```python
for attempt in range(3):
    best = await page.evaluate(eval_script)
    if best and best.get('cpc') is not None:
        break
    if attempt < 2:  # Don't scroll on last attempt
        await _scroll_grid()
        await asyncio.sleep(0.5)
```

## 🧮 **Calcul CPC**

### Logique de Calcul
```javascript
const ratio = vol / traf;
if (!best || ratio > best.ratio) best = { keyword: kw, ratio, cpc, cpcRaw: cpcT };
```

### Algorithme :
1. **Parcourir** toutes les lignes `div[data-ui-name="Body.Row"]`
2. **Extraire** : keyword, volume, trafficPercent, cpc
3. **Calculer** : ratio = volume / trafficPercent
4. **Sélectionner** : ligne avec le ratio maximum
5. **Retourner** : CPC de la ligne sélectionnée

## 🔄 **Workflow CPC**

### Workflow Simplifié
```
extract_metrics():
Dashboard → Test Market-Overview → Bridge (si échec)
Extraction métriques 
```

- ✅ **Sélecteurs Market-Overview (Autres métriques) - Version 2025-01-25** :
  - visits : `[name="entrances"]` (sélection du 2ème élément pour la valeur)
  - organic search traffic : `[name="entrancesSearchOrganic"]` (sélection du 2ème élément pour la valeur)
  - paid search traffic : `[name="entrancesSearchPaid"]` (sélection du 2ème élément pour la valeur)
  - purchase conversion : `[name="purchasesPerVisit"]` (sélection du 2ème élément pour la valeur)
  - avg visit duration : `[name="avgVisitDuration"]` (sélection du 2ème élément pour la valeur)
  - bounce rate : `[name="bouncesPerVisit"]` (sélection du 2ème élément pour la valeur)
- ✅ **Technologie** : Page chargée en SAP React (à prendre en compte pour l'extraction)

## 🏪 **Critères d'Éligibilité des Boutiques**

### Logique de Sélection
Le scraper Noxtools récupère automatiquement les boutiques éligibles depuis la base de données selon les critères suivants :

#### Critères d'Éligibilité
```sql
SELECT s.id, s.shop_url, s.shop_name, a.scraping_status
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
AND s.details_scraping_status = 'details_extracted'
AND a.scraping_status IS NULL
ORDER BY s.id
LIMIT ? OFFSET ?
```

#### Explication des Critères
- **`s.scraping_status != 'failed'`** : Exclut les boutiques en échec de scraping
- **`s.details_scraping_status = 'details_extracted'`** : Seules les boutiques avec détails extraits
- **`a.scraping_status IS NULL`** : Boutiques sans analytics Noxtools (pas encore scrapées)
- **`ORDER BY s.id`** : Traitement par ordre d'ID pour cohérence
- **`LIMIT ? OFFSET ?`** : Traitement par lots pour performance

#### Gestion des Cas Limites
- **Zéro boutiques éligibles** : Log "📊 Zéro boutiques éligibles pour le scraping Noxtools"
- **Aucun domaine valide** : Log "📊 Aucun domaine valide trouvé dans les boutiques éligibles"
- **Extraction des domaines** : Parsing des URLs pour récupérer les domaines nets

### Services de Gestion des Boutiques

#### ShopRepository
- **Récupération** : `get_shops_to_scrape(limit, offset)`
- **Rate limiting** : Intégration avec `TokenBucket`
- **Batch processing** : Traitement par lots configurable
- **Anti-détection** : Délais adaptatifs entre requêtes

#### DatabaseSaver
- **Sauvegarde** : `save_metrics(shop_id, metrics)`
- **Conversion des types** : int/float pour BDD
- **Gestion des erreurs** : Logs détaillés et rollback
- **Validation** : Intégrité des données avant sauvegarde

**Extraction Unifiée (Refactoring 2025-01-18)**
- **Navigation unique** : Dashboard → Test Market-Overview → Bridge (si échec)
- **Fonctionnalités avancées** :
  - Scroll pour virtualisation SAP React
  - Retry avec scroll progressif
  - Parsing numérique avancé (K/M support)
  - Sélecteurs CPC spécifiques et précis
- **Rate limiting** : Limites/minute et burst maintenues

**Inputs à décider par l'agenrt :**
- **Rate limiting** : Limites de requêtes par minute/heure

**Note Version Beta :**
- **Paramètres URL dynamiques** : Pour la version Beta, il faudra fournir la mécanique de récupération des paramètres URL (fid, dateRange, country) au lieu du hardcoding Alpha

#### Version Beta - Formatage et Enregistrement
**Inputs Identifiés :**
- ✅ **Chemin de la BDD** : À fournir
- ✅ **Mapping des champs** : À fournir
- ✅ **Règles de formatage** : À fournir
- ✅ **Métrique calculée** : À partir des données scrapées

**Inputs à Fournir :**
- **Schéma table analytics** : Structure, contraintes, index (voir specs 001-name-trendtrack-scraper/plan/data-model.md)
- **Validation des données** : Plages de valeurs, formats acceptés
- **Gestion des erreurs** : Fallbacks, valeurs par défaut
- **Métadonnées** : Timestamp, source, version du scraper

#### Version Finale - Optimisation et Parallélisation
**Inputs à Fournir :**
- **Configuration des workers** : Nombre, répartition, priorités
- **Métriques de performance** : KPIs à surveiller
- **Monitoring** : Logs de performance, alertes
- **Déploiement** : Environnement, configuration production

### Configuration Anti-Détection (Extrait des Specs)
**Basé sur specs/002-headers-anti-detection :**
- **User-Agents** : Pool de 5 User-Agents réalistes (Chrome, Firefox, Safari)
- **Headers de navigation** : Accept-Language, Accept-Encoding, Accept
- **Headers de sécurité** : Sec-Fetch-*, Upgrade-Insecure-Requests
- **Rotation** : Intervalle configurable (défaut 1 heure)
- **Randomisation** : Jitter aléatoire pour éviter les patterns

### Paramètres de Scraping (Extrait du Scraper Existant)
**Basé sur sem-scraper-final/config.env :**
- **Timeouts** : Browser (60s), Page Load (90s), Navigation (120s)
- **Retry** : 3 tentatives par défaut
- **Délais** : 2 secondes entre requêtes
- **Rate Limiting** : 60 requêtes/minute, burst de 10
- **Backoff** : 1s initial, x2 multiplicateur, max 10s

### Schéma Table Analytics (Extrait des Specs)
**Basé sur specs/001-name-trendtrack-scraper/plan/data-model.md :**
```sql
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    organic_traffic INTEGER,
    bounce_rate NUMERIC,
    avg_visit_duration TEXT,
    branded_traffic INTEGER,
    conversion_rate TEXT,
    visits INTEGER,
    traffic INTEGER,
    paid_search_traffic INTEGER,
    percent_branded_traffic NUMERIC,
    cpc NUMERIC,
    scraping_status TEXT DEFAULT 'completed',
    updated_at DATE,
    FOREIGN KEY (shop_id) REFERENCES shops (id)
);
```

### Validation du Format des Métriques (Nouvelle Règle P1)
**Validation obligatoire du format des métriques visits** :

#### Règle de Validation Visits
- **Condition** : Si la métrique `visits` ne contient pas de suffixe K ou M
- **Action** : Marquer la boutique en statut "failed"
- **Exemples valides** : "1.5M", "33K", "150K", "2.1M"
- **Exemples invalides** : "1500000", "33000", "1500", "2100000"
- **Implémentation** : Validation dans le StatusManager avant classification du statut

#### Logique de Validation
```python
def validate_visits_format(visits_value: str) -> bool:
    """Valide que visits contient K ou M suffixe."""
    if not visits_value:
        return False
    cleaned = visits_value.strip().upper()
    return cleaned.endswith('K') or cleaned.endswith('M')
```

### Formatage des Données (Version Beta)
**Préparation pour l'enregistrement en base de données** :

#### Métriques Noxtools à Formater
- **Métriques de Performance** : Conversion des valeurs numériques (entiers, décimaux)
- **Métriques de Trafic** : Normalisation des pourcentages et volumes
- **Métriques de Conversion** : Validation des taux de conversion (0-100%)
- **Métriques Temporelles** : 
  - Logs/métadonnées : Format ISO 8601 UTC avec microsecondes
  - Base de données : Format SQLite DATE (YYYY-MM-DD)
- **Métriques Géographiques** : Normalisation des codes pays et régions

#### Validation des Données
- **Vérification des Types** : Validation des types de données avant insertion
- **Vérification des Plages** : Validation des valeurs dans les plages attendues
- **Vérification des Relations** : Validation des clés étrangères avec la table shops
- **Vérification de la Complétude** : Détection des données manquantes ou incomplètes

#### Transformation des Données
- **Nettoyage** : Suppression des caractères spéciaux et normalisation
- **Conversion** : Transformation des formats (string → int, date → ISO)
- **Enrichissement** : Ajout de métadonnées (timestamp ISO 8601, source, version)
- **Structuration** : Organisation des données selon le schéma de la table analytics

#### Gestion des Erreurs de Formatage
- **Logs de Formatage** : Enregistrement des erreurs de conversion
- **Fallbacks** : Valeurs par défaut pour les données manquantes
- **Retry Logic** : Nouvelle tentative de formatage en cas d'échec
- **Validation Finale** : Vérification avant enregistrement en base

---

## Liste de Vérification de Révision & Acceptation
*PORTE : Vérifications automatisées exécutées pendant main()*

### Qualité du Contenu
- [x] Aucun détail d'implémentation (langages, frameworks, APIs)
- [x] Concentré sur la valeur utilisateur et les besoins métier
- [x] Écrit pour les parties prenantes non-techniques
- [x] Toutes les sections obligatoires complétées

### Complétude des Exigences
- [x] Aucun marqueur [BESOIN DE CLARIFICATION] ne reste
- [x] Les exigences sont testables et non ambiguës
- [x] Les critères de succès sont mesurables
- [x] La portée est clairement délimitée
- [x] Les dépendances et suppositions identifiées

---

## Statut d'Exécution
*Mis à jour par main() pendant le traitement*

- [x] Description utilisateur analysée
- [x] Concepts clés extraits
- [x] Ambiguïtés marquées
- [x] Scénarios utilisateur définis
- [x] Exigences générées
- [x] Entités identifiées
- [x] Liste de vérification de révision passée

---

## Rapports d'État

### 📊 **Statut Actuel**
- **Système à créer** : Nouveau scraper Noxtools en développement progressif
- **Base existante** : Scraper SEM opérationnel comme référence
- **Approche** : Développement en 3 versions (Alpha → Beta → Finale)
- **Nouveautés** : Nouveaux sélecteurs et navigation multi-domaines
- **Problèmes identifiés** : Session expirée Semrush, URLs incohérentes, ✅ fallback serveurs résolu (ServerManager implémenté)

### 🎯 **Fonctionnalités par Version**

#### Version Alpha - Test et Validation
- **Scraping Noxtools** : Récupération des métriques sans BDD
- **Authentification** : Nouveaux sélecteurs de formulaire
- **Navigation multi-domaines** : Gestion des sessions entre domaines
- **Logs détaillés** : Validation des données récupérées
- **Gestion d'erreurs** : Scraping gracieux sans arrêt
- **Retry session** : Retour au login en cas de session expirée
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 (ServerManager implémenté)

#### Version Beta - Formatage et Enregistrement
- **Toutes les fonctionnalités Alpha** : Base solide validée
- **Formatage des données** : Conversion selon standards définis
- **Validation d'intégrité** : Vérification avant sauvegarde
- **Enregistrement BDD** : Table analytics avec correspondance shops
- **Gestion d'erreurs** : Formatage et sauvegarde robustes

#### Version Finale - Optimisation et Parallélisation
- **Toutes les fonctionnalités Alpha et Beta** : Base complète
- **Optimisation performances** : Scraping parallèle avec workers
- **Timeouts adaptatifs** : Gestion avancée des délais
- **Fallback Noxtools** : Basculement automatique en cas de 404
- **Monitoring** : Métriques de performance et surveillance
- **Production** : Déploiement et maintenance

### 📋 **Intégration Progressive**
- **Version Alpha** : Focus sur la récupération et validation
- **Version Beta** : Intégration base de données et formatage
- **Version Finale** : Optimisation et déploiement production
- **Workflow Final** : Noxtools → Formatage → Base de données → API

---

**Feature Branch**: `006-noxtools-scraper`  
**Created**: 2025-01-18  
**Status**: Draft  
**Input**: User description: "Créer un nouveau scraper dans un dossier scraper-noxtools-final qui reproduit les fonctionnalités du scraper SEM existant mais adapté pour Noxtools avec de nouveaux sélecteurs et une navigation vers un autre domaine."

- **Gestion d'erreurs** : Scraping gracieux sans arrêt
- **Retry session** : Retour au login en cas de session expirée
- ✅ **Fallback serveurs** : Système dynamique semrush1→semrush5 (ServerManager implémenté)

#### Version Beta - Formatage et Enregistrement
- **Toutes les fonctionnalités Alpha** : Base solide validée
- **Formatage des données** : Conversion selon standards définis
- **Validation d'intégrité** : Vérification avant sauvegarde
- **Enregistrement BDD** : Table analytics avec correspondance shops
- **Gestion d'erreurs** : Formatage et sauvegarde robustes

#### Version Finale - Optimisation et Parallélisation
- **Toutes les fonctionnalités Alpha et Beta** : Base complète
- **Optimisation performances** : Scraping parallèle avec workers
- **Timeouts adaptatifs** : Gestion avancée des délais
- **Fallback Noxtools** : Basculement automatique en cas de 404
- **Monitoring** : Métriques de performance et surveillance
- **Production** : Déploiement et maintenance

### 📋 **Intégration Progressive**
- **Version Alpha** : Focus sur la récupération et validation
- **Version Beta** : Intégration base de données et formatage
- **Version Finale** : Optimisation et déploiement production
- **Workflow Final** : Noxtools → Formatage → Base de données → API

---

**Feature Branch**: `006-noxtools-scraper`  
**Created**: 2025-01-18  
**Status**: Draft  
**Input**: User description: "Créer un nouveau scraper dans un dossier scraper-noxtools-final qui reproduit les fonctionnalités du scraper SEM existant mais adapté pour Noxtools avec de nouveaux sélecteurs et une navigation vers un autre domaine."
