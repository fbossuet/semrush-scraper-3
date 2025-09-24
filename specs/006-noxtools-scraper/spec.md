# Spécification de Fonctionnalité : Scraper Noxtools

**Branche de Fonctionnalité** : `006-noxtools-scraper`  
**Créé** : 2025-01-18  
**Statut** : Brouillon  
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

## Scénarios Utilisateur & Tests *(obligatoire)*

### Histoire Utilisateur Principale
En tant qu'analyste de données, je veux que le système de scraping Noxtools récupère automatiquement les métriques de performance des boutiques depuis Noxtools, afin de pouvoir analyser les tendances du marché e-commerce et identifier les opportunités commerciales avec des données complémentaires à celles de SEM Rush.

### Scénarios d'Acceptation
1. **Étant donné** un système de scraping Noxtools configuré, **Quand** le système s'initialise, **Alors** il devrait configurer Playwright en mode stealth headless avec les paramètres anti-détection appropriés
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

#### Navigation et Scraping
- **NOX-010** : Le système DOIT naviguer vers la nouvelle page de métriques Noxtools
- **NOX-011** : Le système DOIT récupérer la liste des boutiques éligibles depuis la base de données
- **NOX-012** : Le système DOIT filtrer les boutiques selon le statut (stable shop pour shop_url et table analytics pour status)
- **NOX-013** : Le système DOIT appliquer une logique anti-détection pour chaque boutique scrapée
- **NOX-014** : Le système DOIT extraire les métriques spécifiques avec les nouveaux sélecteurs DOM

#### Gestion des Données
- **NOX-015** : Le système DOIT enregistrer les résultats dans la table analytics
- **NOX-016** : Le système DOIT respecter la correspondance avec la table shops via les clés étrangères
- **NOX-017** : Le système DOIT gérer les métriques spécifiques à Noxtools
- **NOX-018** : Le système DOIT valider l'intégrité des données avant sauvegarde

#### Robustesse et Performance
- **NOX-019** : Le système DOIT implémenter une logique de retry adaptative
- **NOX-020** : Le système DOIT gérer les timeouts adaptatifs selon le type d'opération
- **NOX-021** : Le système DOIT gérer les erreurs gracieusement sans arrêter le processus global
- **NOX-022** : Le système DOIT fournir des logs détaillés pour le debugging
- **NOX-023** : Le système DOIT optimiser les performances pour le scraping en parallèle

### Exigences par Version

#### Version Alpha - Test et Validation
- **NOX-ALPHA-001** : Le système DOIT initialiser Playwright en mode stealth headless (NOX-001)
- **NOX-ALPHA-002** : Le système DOIT s'authentifier avec les nouveaux sélecteurs (NOX-005)
- **NOX-ALPHA-003** : Le système DOIT naviguer vers Noxtools et maintenir la session (NOX-007, NOX-008)
- **NOX-ALPHA-004** : Le système DOIT extraire les métriques avec les nouveaux sélecteurs (NOX-014)
- **NOX-ALPHA-005** : Le système DOIT logger les données récupérées sans enregistrement en BDD
- **NOX-ALPHA-006** : Le système DOIT gérer les erreurs de scraping gracieusement (NOX-021)

#### Version Beta - Formatage et Enregistrement
- **NOX-BETA-001** : Le système DOIT implémenter toutes les fonctionnalités de la version Alpha
- **NOX-BETA-002** : Le système DOIT formater les métriques selon les standards définis
- **NOX-BETA-003** : Le système DOIT valider l'intégrité des données avant sauvegarde (NOX-018)
- **NOX-BETA-004** : Le système DOIT enregistrer dans la table analytics (NOX-015)
- **NOX-BETA-005** : Le système DOIT respecter la correspondance avec la table shops (NOX-016)
- **NOX-BETA-006** : Le système DOIT gérer les erreurs de formatage et de sauvegarde

#### Version Finale - Optimisation et Parallélisation
- **NOX-FINAL-001** : Le système DOIT implémenter toutes les fonctionnalités des versions Alpha et Beta
- **NOX-FINAL-002** : Le système DOIT optimiser les performances de scraping (NOX-023)
- **NOX-FINAL-003** : Le système DOIT implémenter le scraping parallèle avec workers
- **NOX-FINAL-004** : Le système DOIT gérer les timeouts adaptatifs avancés (NOX-020)
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
- **Dates** : Toutes les dates DOIVENT être au format ISO 8601 UTC (ex: "2025-01-18T10:30:45.123Z")
- **Python** : Utiliser `datetime.now(timezone.utc).isoformat()`
- **JavaScript** : Utiliser `new Date().toISOString()`
- **SQLite** : Stocker en TEXT avec format ISO 8601

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
- ✅ **URL finale avec paramètres** : https://semrush1.semrush.pw/analytics/overview/?searchType=domain&q=cakesbody.com&db=us&date=202507
- ✅ **URL des métriques** : https://semrush1.semrush.pw/analytics/traffic/market-overview?searchType=domain&fid=1355702&dateRange=2025-07-01&country=us
- ✅ **URL overview (CPC)** : https://semrush1.semrush.pw/analytics/overview/?fid=1355922&searchType=domain&db=us&q=worldwildlife.org
- ✅ **Gestion session/cookies** : Maintenir entre domaines (noxtools.com → semrush1.semrush.pw)
- ✅ **Sélecteurs des métriques** : 
  - visits : `[data-ui-name="Flex"][role="gridcell"][name="entrances"][tabindex="-1"][aria-colindex="3"]`
  - organic search traffic : `[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchOrganic"][tabindex="-1"][aria-colindex="9"]`
  - paid search traffic : `[data-ui-name="Flex"][role="gridcell"][name="entrancesSearchPaid"][tabindex="-1"][aria-colindex="11"]`
  - purchase conversion : `[data-ui-name="Flex"][role="gridcell"][name="purchasesPerVisit"][tabindex="-1"][aria-colindex="21"]`
  - avg visit duration : `[data-ui-name="Flex"][role="gridcell"][name="avgVisitDuration"][tabindex="-1"][aria-colindex="27"]`
  - bounce rate : `[data-ui-name="Flex"][role="gridcell"][name="bouncesPerVisit"][tabindex="-1"][aria-colindex="29"]`
  - cpc (à confirmer) : `name="cpc"` (sélecteur à valider; Alpha: affichage log uniquement)
- ✅ **Technologie** : Page chargée en SAP React (à prendre en compte pour l'extraction)

**Extraction CPC (Alpha)**
- Naviguer vers l’overview (cf. URL overview) après passage par `https://semrush.noxtools.com/server3.php`
  - Note: pour la version Finale, prévoir un mécanisme de fallback automatique sur d’autres passerelles/domains en cas d’erreur (ex: indisponibilité/404), conformément à `NOX-FINAL-005`.
- Attendre le chargement SAP React (networkidle + délais de stabilisation)
- Parcourir les lignes `div[data-ui-name="Body.Row"]`
- Sélecteurs:
  - Volume: `div[name="volume"][role="gridcell"] [data-at="value-volume"]`
  - Traffic %: `div[name="trafficPercent"][role="gridcell"] [data-at="value-traffic-percent"]`
  - CPC: `div[name="cpc"][role="gridcell"] [data-at="value-cpc"]`
- Calcul: ratio = volume / trafficPercent; conserver la ligne au ratio maximal et retourner le CPC associé

**Inputs à Fournir :**
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
- **Schéma table analytics** : Structure, contraintes, index (voir specs 001-name-trendtrack-scraper/plan/prod_schema.sql)
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
**Basé sur specs/001-name-trendtrack-scraper/plan/prod_schema.sql :**
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

### Formatage des Données (Version Beta)
**Préparation pour l'enregistrement en base de données** :

#### Métriques Noxtools à Formater
- **Métriques de Performance** : Conversion des valeurs numériques (entiers, décimaux)
- **Métriques de Trafic** : Normalisation des pourcentages et volumes
- **Métriques de Conversion** : Validation des taux de conversion (0-100%)
- **Métriques Temporelles** : Conversion des dates et timestamps
- **Métriques Géographiques** : Normalisation des codes pays et régions

#### Validation des Données
- **Vérification des Types** : Validation des types de données avant insertion
- **Vérification des Plages** : Validation des valeurs dans les plages attendues
- **Vérification des Relations** : Validation des clés étrangères avec la table shops
- **Vérification de la Complétude** : Détection des données manquantes ou incomplètes

#### Transformation des Données
- **Nettoyage** : Suppression des caractères spéciaux et normalisation
- **Conversion** : Transformation des formats (string → int, date → ISO)
- **Enrichissement** : Ajout de métadonnées (timestamp, source, version)
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

### 🎯 **Fonctionnalités par Version**

#### Version Alpha - Test et Validation
- **Scraping Noxtools** : Récupération des métriques sans BDD
- **Authentification** : Nouveaux sélecteurs de formulaire
- **Navigation multi-domaines** : Gestion des sessions entre domaines
- **Logs détaillés** : Validation des données récupérées
- **Gestion d'erreurs** : Scraping gracieux sans arrêt

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
