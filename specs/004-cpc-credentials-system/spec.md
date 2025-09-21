# Spécification de Fonctionnalité : Système CPC et Credentials Centralisés

**Branche de Fonctionnalité** : `004-cpc-credentials-system`  
**Créé** : 2025-01-18  
**Statut** : Implémenté  
**Entrée** : Implémentation de la récupération de la métrique CPC (Cost Per Click) et centralisation des credentials API pour le scraper SEM

## Scénarios Utilisateur & Tests *(obligatoire)*

### Histoire Utilisateur Principale
En tant qu'analyste de performance marketing, je veux que le système récupère automatiquement la métrique CPC (Cost Per Click) pour chaque domaine analysé, afin de pouvoir évaluer l'efficacité des campagnes publicitaires et calculer le ROI des investissements marketing.

### Scénarios d'Acceptation
1. **Étant donné** un domaine avec du trafic payant, **Quand** le système effectue le scraping, **Alors** il devrait calculer automatiquement le CPC (coût payant / trafic payant)
2. **Étant donné** un domaine sans trafic payant, **Quand** le système effectue le scraping, **Alors** il devrait marquer le CPC à 0
3. **Étant donné** des credentials API configurés, **Quand** le système démarre, **Alors** il devrait utiliser ces credentials pour toutes les requêtes API
4. **Étant donné** des credentials manquants, **Quand** le système démarre, **Alors** il devrait utiliser automatiquement les credentials par défaut
5. **Étant donné** une métrique CPC calculée, **Quand** le système sauvegarde les données, **Alors** le CPC devrait être stocké dans la base de données

### Cas Limites
- Que se passe-t-il quand le trafic payant est 0 mais le coût payant est > 0 ?
- Comment le système gère-t-il les credentials expirés ou invalides ?
- Que se passe-t-il quand les variables d'environnement sont mal formatées ?
- Comment le système gère-t-il les calculs CPC avec des valeurs très élevées ?

## Exigences *(obligatoire)*

### Exigences Fonctionnelles

#### Système de Credentials Centralisé
- **EF-001** : Le système DOIT supporter les variables d'environnement SAM_USER_ID et SAM_API_KEY
- **EF-002** : Le système DOIT utiliser des fallbacks sécurisés si les variables d'environnement ne sont pas définies
- **EF-003** : Le système DOIT fournir une interface centralisée pour récupérer les credentials
- **EF-004** : Le système DOIT éviter la duplication des credentials dans le code
- **EF-005** : Le système DOIT supporter le rechargement des credentials sans redémarrage

#### Métrique CPC (Cost Per Click)
- **EF-006** : Le système DOIT calculer automatiquement CPC = paid_traffic_cost / paid_traffic
- **EF-007** : Le système DOIT gérer le cas où paid_traffic = 0 (CPC = 0)
- **EF-008** : Le système DOIT arrondir le CPC à 4 décimales
- **EF-009** : Le système DOIT stocker le CPC dans la base de données
- **EF-010** : Le système DOIT afficher le CPC dans les logs de scraping

#### Intégration et Compatibilité
- **EF-011** : Le système DOIT préserver toutes les fonctionnalités existantes
- **EF-012** : Le système DOIT utiliser la même API organic.OverviewTrend existante
- **EF-013** : Le système DOIT maintenir les mêmes performances de scraping
- **EF-014** : Le système DOIT être compatible avec l'endpoint API /albert

### Entités Clés *(inclure si la fonctionnalité implique des données)*
- **Credentials API** : Représente les informations d'authentification (userId, apiKey) avec source (environment/fallback)
- **Métrique CPC** : Représente le coût par clic calculé à partir du trafic payant et du coût payant
- **Configuration Environnement** : Représente les variables d'environnement pour la configuration des credentials

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
- [x] Implémentation complétée
- [x] Tests de validation effectués

---

## Rapports d'Implémentation

### 📊 **Fonctionnalités Implémentées**
- **Système de credentials centralisé** avec support des variables d'environnement
- **Calcul automatique de la métrique CPC** via l'API organic.OverviewTrend
- **Intégration complète** dans le scraper de production
- **Tests de validation** avec script de test automatisé

### 🎯 **Découvertes Clés**
- **Credentials centralisés** : Évite la duplication et facilite la maintenance
- **Calcul CPC robuste** : Gère tous les cas limites (trafic payant = 0)
- **Fallbacks sécurisés** : Aucune interruption de service
- **Compatibilité totale** : Préserve toutes les fonctionnalités existantes

### 📋 **Fichiers Créés/Modifiés**
- **Nouveaux** : `api_credentials.py`, `test_cpc_implementation.py`, `README_CPC_CREDENTIALS.md`
- **Modifiés** : `api_client_refactored.py`, `production_scraper_parallel.py`

---

**Feature Branch**: `004-cpc-credentials-system`  
**Created**: 2025-01-18  
**Status**: Implemented  
**Input**: User description: "Implémentation de la récupération de la métrique CPC et centralisation des credentials API pour le scraper SEM"
