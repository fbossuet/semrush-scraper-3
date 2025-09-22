# 🧪 Guide de Test - Solution de Mapping des IDs

## 🎯 Objectif

Tester la solution proposée pour résoudre le problème de mapping des IDs entre :
- **ID de la page de liste** : `7fbb404d-63d6-4c5c-b38a-b09e67b7a501`
- **ID de l'API** : `90c2965f-9881-40ce-bcb7-f7da383fd815`

## 📋 Problème à Résoudre

D'après le `RECAPITULATIF_DEVELOPPEUR.md` :
- ✅ L'API des pixels fonctionne avec l'ID de la page de liste
- ❌ L'API des données géographiques ne fonctionne qu'avec l'ID de l'API
- ❌ Impossible d'extraire les données géographiques pour les boutiques de la page de liste

## 🛠️ Solution Proposée

Extraire l'ID API depuis la réponse RSC de l'endpoint `/trending-shops/{shopId}` en utilisant des patterns de recherche.

## 🧪 Fichiers de Test Créés

### 1. `test-api-id-extraction.js`
- **Objectif** : Test complet de l'extraction d'ID API
- **Fonctionnalités** :
  - Extraction de l'ID API depuis la réponse RSC
  - Validation avec l'endpoint géo
  - Debug de la réponse RSC
  - Test des UUIDs candidats

### 2. `trendtrack-extractor-with-api-id.js`
- **Objectif** : Version de test du code principal avec les nouvelles méthodes
- **Fonctionnalités** :
  - `extractApiIdFromRSC()` - Extraction de l'ID API
  - `debugRSCResponse()` - Debug de la réponse RSC
  - `extractShopDetailsWithApiId()` - Version améliorée de extractShopDetails

### 3. `test-id-mapping-solution.js`
- **Objectif** : Test simple et direct de la solution
- **Fonctionnalités** :
  - Test de l'extraction d'ID API
  - Validation avec l'endpoint géo
  - Affichage des données de marché extraites

## 🚀 Comment Tester

### Étape 1 : Test Simple
```bash
cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
node test-id-mapping-solution.js
```

**Instructions** :
1. Le script va ouvrir un navigateur
2. Connectez-vous manuellement sur TrendTrack
3. Appuyez sur Entrée une fois connecté
4. Le script va tester l'extraction d'ID API

### Étape 2 : Test Complet
```bash
node test-api-id-extraction.js
```

**Instructions** :
1. Même processus de connexion
2. Test plus détaillé avec debug
3. Validation de tous les UUIDs candidats

### Étape 3 : Test d'Intégration
```bash
# Utiliser la version de test du code principal
# Remplacer temporairement le fichier original
cp src/extractors/trendtrack-extractor.js src/extractors/trendtrack-extractor.js.backup
cp trendtrack-extractor-with-api-id.js src/extractors/trendtrack-extractor.js

# Tester avec quelques boutiques
node update-database.js
```

## 📊 Critères de Succès

### ✅ Succès Attendu
- L'ID API est extrait depuis la réponse RSC
- L'endpoint `/api/websites/{apiId}` retourne des données géographiques
- Les données de marché sont correctement mappées (US, UK, DE, CA, AU, FR)
- Aucune régression sur l'extraction des pixels

### ❌ Échec Possible
- Aucun ID API trouvé dans la réponse RSC
- L'ID API trouvé ne fonctionne pas avec l'endpoint géo
- Les données géographiques sont vides ou incorrectes
- Régression sur l'extraction des pixels

## 🔍 Patterns de Recherche Utilisés

```javascript
const patterns = [
  /"websiteId":"([a-f0-9-]{36})"/,
  /"siteId":"([a-f0-9-]{36})"/,
  /"website["\.]id["\:]"([a-f0-9-]{36})"/,
  /website[\/:]([a-f0-9-]{36})/,
  /"id":"([a-f0-9-]{36})".*geography/,
  /\/api\/websites\/([a-f0-9-]{36})/
];
```

## 📝 Logs à Surveiller

### Logs de Succès
```
✅ ID API trouvé: 90c2965f-9881-40ce-bcb7-f7da383fd815
🎯 Pattern utilisé: "websiteId":"([a-f0-9-]{36})"
✅ Validation réussie!
🌍 Données géo disponibles: 5 pays
📊 Données de marché extraites:
   US: 74.64%
   UK: 3.32%
   DE: 1.99%
   CA: 5.53%
   AU: 2.64%
   FR: 0.00%
```

### Logs d'Échec
```
⚠️ Aucun ID API trouvé avec les patterns spécifiques
🆔 UUIDs disponibles: 7fbb404d-63d6-4c5c-b38a-b09e67b7a501, ...
❌ Validation échouée: HTTP 404: Not Found
```

## 🚨 Points d'Attention

### Sécurité
- Les cookies de session sont automatiquement gérés
- Ne pas exposer les cookies dans les logs
- Tester avec des données réelles mais non sensibles

### Performance
- L'extraction d'ID API ajoute un appel HTTP supplémentaire
- Tester avec plusieurs boutiques pour valider les performances
- Implémenter un système de retry si nécessaire

### Gestion des Erreurs
- Fallback vers l'ancienne méthode si l'ID API n'est pas trouvé
- Logger les erreurs pour investigation
- Marquer les boutiques avec un statut approprié

## 📋 Checklist de Validation

- [ ] L'ID API est extrait depuis la réponse RSC
- [ ] L'endpoint géo fonctionne avec l'ID API
- [ ] Les données de marché sont correctement mappées
- [ ] L'extraction des pixels continue de fonctionner
- [ ] Aucune régression sur les fonctionnalités existantes
- [ ] Les performances sont acceptables
- [ ] La gestion d'erreurs est robuste

## 🎯 Prochaines Étapes

### Si le Test Réussit
1. Intégrer la solution dans le code principal
2. Tester avec toutes les boutiques
3. Valider les performances
4. Mettre à jour la documentation

### Si le Test Échoue
1. Analyser les logs d'erreur
2. Ajuster les patterns de recherche
3. Explorer d'autres approches
4. Consulter l'utilisateur pour d'autres solutions

## 📞 Support

En cas de problème :
1. Vérifier les logs détaillés
2. Tester avec d'autres IDs de boutique
3. Vérifier la connectivité TrendTrack
4. Consulter le `RECAPITULATIF_DEVELOPPEUR.md` pour le contexte

---

**Date de création** : 2025-09-22  
**Statut** : Prêt pour test  
**Priorité** : P0 (Critique pour résoudre le problème de mapping des IDs)
