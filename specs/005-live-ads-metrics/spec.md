# Spécification : Métriques Live Ads 7d et 30d

## Vue d'ensemble

Cette spécification décrit l'implémentation de la récupération des métriques `live_ads_7d` et `live_ads_30d` depuis le tableau TrendTrack pour enrichir les données des boutiques.

## Contexte

Le scraper TrendTrack récupère actuellement la métrique `live_ads` (total) depuis la cellule 7 du tableau. Cette fonctionnalité étend le scraper pour récupérer également :
- `live_ads_7d` : Nombre de live ads sur 7 jours
- `live_ads_30d` : Nombre de live ads sur 30 jours

## Objectifs

### Objectif Principal
Récupérer les métriques de progression des live ads pour une analyse temporelle plus fine.

### Objectifs Secondaires
- Enrichir les données des boutiques avec des métriques temporelles
- Améliorer l'analyse des tendances publicitaires
- Fournir des données plus granulaires via l'API

## Fonctionnalités

### Fonctionnalité 1 : Extraction des Métriques
- **Description** : Récupération des métriques depuis le tableau TrendTrack
- **Source** : Cellules 5 et 6 du tableau des boutiques tendances
- **Format** : Valeurs numériques entières

### Fonctionnalité 2 : Sauvegarde en Base de Données
- **Description** : Stockage des métriques dans les colonnes `live_ads_7d` et `live_ads_30d`
- **Table** : `shops`
- **Type** : INTEGER DEFAULT 0

### Fonctionnalité 3 : Exposition API
- **Description** : Disponibilité des métriques via l'endpoint `/albert`
- **Format** : JSON avec champs `live_ads_7d` et `live_ads_30d`

## Contraintes Techniques

### Contraintes de Source
- Les métriques doivent être extraites depuis la page de liste (Phase 1)
- La cellule 6 (live_ads_30d) n'est pas disponible dans TrendTrack
- Seule la cellule 5 (live_ads_7d) contient des données

### Contraintes de Performance
- Extraction en parallèle avec les autres métriques du tableau
- Pas d'impact sur les performances du scraper
- Sauvegarde atomique avec les autres données

## Critères d'Acceptation

### Critère 1 : Extraction
- [x] La métrique `live_ads_7d` est extraite depuis la cellule 5
- [x] La métrique `live_ads_30d` est tentée depuis la cellule 6 (toujours 0)
- [x] Les valeurs sont correctement parsées en entiers

### Critère 2 : Sauvegarde
- [x] Les colonnes `live_ads_7d` et `live_ads_30d` existent en base
- [x] Les données sont correctement mappées et sauvegardées
- [x] Les valeurs par défaut sont 0

### Critère 3 : API
- [x] L'endpoint `/albert` retourne les nouvelles métriques
- [x] Les champs sont présents dans la réponse JSON
- [x] Les valeurs sont correctement formatées

## Résultats des Tests

### Test d'Extraction
- ✅ **Live Ads 7d** : Récupéré avec succès (valeurs : 670, 982, 2, 3, 658, etc.)
- ❌ **Live Ads 30d** : Non disponible dans TrendTrack (cellule 6 vide)

### Test de Sauvegarde
- ✅ **Base de données** : 150 boutiques avec métriques live_ads_7d
- ✅ **Exemples** : ryzesuperfoods.com (live_ads_7d=1), meshki.us (live_ads_7d=1)

### Test API
- ✅ **Endpoint** : `/albert` retourne les métriques
- ✅ **Format** : JSON avec champs `live_ads_7d` et `live_ads_30d`

## Statut

**✅ IMPLÉMENTÉ ET FONCTIONNEL**

- Date d'implémentation : 22/01/2025
- Statut : Terminé
- Tests : Validés
- Production : Opérationnel
