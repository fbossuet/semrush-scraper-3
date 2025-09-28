# Guide de Démarrage TrendTrack MVP Scraper

**Version**: V2  
**Date**: 2025-09-25  
**Statut**: Guide de démarrage officiel MVP

## 🚀 Démarrage Rapide

Ce guide vous permet de démarrer le scraper TrendTrack MVP en quelques minutes.

---

## 📋 Prérequis

### Système
- **OS** : Linux (Ubuntu 20.04+)
- **Node.js** : Version 18 ou supérieure
- **NPM** : Version 8 ou supérieure
- **Playwright** : Installé et configuré

### Base de Données
- **SQLite** : Base `trendtrack.db` configurée
- **Schéma** : Tables `shops` et `analytics` créées
- **Permissions** : Accès en lecture/écriture

### Credentials
- **TrendTrack** : Login et mot de passe valides
- **Variables d'environnement** : Configurées dans `.env`

---

## ⚡ Installation Express

### 1. Vérification de l'Environnement

```bash
# Vérifier Node.js
node --version  # Doit être >= 18

# Vérifier NPM
npm --version   # Doit être >= 8

# Vérifier Playwright
npx playwright --version
```

### 2. Navigation vers le Projet

```bash
cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
```

### 3. Installation des Dépendances

```bash
npm install
```

### 4. Configuration des Credentials

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos credentials
nano .env
```

**Contenu du fichier `.env`** :
```env
TRENDTRACK_EMAIL=votre.email@example.com
TRENDTRACK_PASSWORD=votre_mot_de_passe
DATABASE_PATH=./data/trendtrack.db
LOG_LEVEL=info
```

---

## 🎯 Lancement du Scraper MVP

### Lancement Standard

```bash
node update-database-mvp.js
```

### Lancement avec Logs Détaillés

```bash
# Avec logs en temps réel
node update-database-mvp.js > logs/mvp-scraper-$(date +%Y%m%d_%H%M%S).log 2>&1 &
tail -f logs/mvp-scraper-$(date +%Y%m%d_%H%M%S).log
```

### Lancement avec Configuration Personnalisée

```bash
# Modifier MVP_CONFIG dans le script
nano update-database-mvp.js

# Lancer avec la nouvelle configuration
node update-database-mvp.js
```

---

## 📊 Configuration MVP

### Configuration par Défaut

```javascript
const MVP_CONFIG = {
    // Limites MVP
    maxShopsPerRun: 100,        // Maximum 100 boutiques
    maxPagesPerRun: 1,          // 1 page uniquement
    batchSize: 5,               // 5 boutiques par lot
    
    // Timeouts
    navigationTimeout: 60000,   // 60 secondes
    selectorTimeout: 15000,     // 15 secondes
    pageLoadTimeout: 30000,     // 30 secondes
    
    // Retry
    maxRetries: 3,              // 3 tentatives maximum
    retryDelay: 1000,           // 1 seconde de base
    retryBackoff: 'exponential', // Backoff exponentiel
    
    // Pauses
    pageLoadPause: 3000,        // 3 secondes après navigation
    betweenShopsPause: 2000,    // 2 secondes entre boutiques
    batchPause: 5000            // 5 secondes entre lots
};
```

### Personnalisation

```javascript
// Exemple : Configuration pour test rapide
const MVP_CONFIG = {
    maxShopsPerRun: 10,         // Seulement 10 boutiques
    batchSize: 3,               // Lots de 3
    maxRetries: 2,              // 2 tentatives seulement
    betweenShopsPause: 1000     // 1 seconde entre boutiques
};
```

---

## 📈 Monitoring et Logs

### Logs en Temps Réel

```bash
# Lancer le scraper en arrière-plan
node update-database-mvp.js > logs/mvp-$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Surveiller les logs
tail -f logs/mvp-$(date +%Y%m%d_%H%M%S).log
```

### Types de Logs

| Type | Description | Exemple |
|------|-------------|---------|
| **INFO** | Opérations normales | `✅ Boutique extraite: shop-name` |
| **WARNING** | Avertissements | `⚠️ AOV non trouvé pour shop-name` |
| **ERROR** | Erreurs critiques | `❌ Échec extraction: shop-name` |
| **DEBUG** | Détails techniques | `🔍 Sélecteur utilisé: .selector` |

### Logs de Progrès

```bash
# Fichier de progrès
cat logs/update-mvp-progress.log

# Dernières lignes
tail -20 logs/update-mvp-progress.log
```

---

## 🧪 Tests et Validation

### Test Rapide (10 Boutiques)

```bash
# Modifier la configuration pour test rapide
nano update-database-mvp.js

# Changer maxShopsPerRun à 10
const MVP_CONFIG = {
    maxShopsPerRun: 10,  // Test rapide
    // ... autres paramètres
};

# Lancer le test
node update-database-mvp.js
```

### Validation des Résultats

```bash
# Vérifier la base de données
sqlite3 data/trendtrack.db "SELECT COUNT(*) FROM shops WHERE details_scraping_status = 'details_extracted';"

# Vérifier les dernières boutiques ajoutées
sqlite3 data/trendtrack.db "SELECT shop_name, details_scraping_status FROM shops ORDER BY id DESC LIMIT 10;"
```

---

## 🔧 Dépannage

### Problèmes Courants

#### 1. Erreur de Connexion

```bash
# Vérifier les credentials
cat .env

# Tester la connexion
node -e "
const { TrendTrackExtractor } = require('./src/extractors/trendtrack-extractor.js');
console.log('Test de connexion...');
"
```

#### 2. Erreur de Base de Données

```bash
# Vérifier le fichier de base de données
ls -la data/trendtrack.db

# Vérifier les permissions
ls -la data/

# Tester la connexion SQLite
sqlite3 data/trendtrack.db "SELECT COUNT(*) FROM shops;"
```

#### 3. Erreur Playwright

```bash
# Réinstaller Playwright
npx playwright install

# Vérifier l'installation
npx playwright --version
```

### Logs de Debug

```bash
# Activer les logs de debug
export LOG_LEVEL=debug

# Lancer avec debug
node update-database-mvp.js
```

---

## 📊 Résultats Attendus

### Métriques de Succès

| Métrique | Cible | Description |
|----------|-------|-------------|
| **Phase 1** | 100% | Extraction table réussie |
| **Phase 3** | ≥90% | Extraction détails réussie |
| **AOV** | ≥70% | Average Order Value trouvé |
| **Temps** | <30min | Exécution complète |

### Exemple de Sortie

```
🚀 TRENDTRACK MVP SCRAPER - DÉMARRAGE
============================================================
📊 Configuration MVP:
   - Max shops: 100
   - Batch size: 5
   - Max retries: 3
   - Timeout: 60s

🔍 Phase 1: Extraction table...
✅ 30/30 boutiques extraites de la table
✅ 30/30 external_id générés
✅ 25/30 year_founded trouvés (83%)

🔍 Phase 3: Extraction détails...
✅ 28/30 boutiques traitées avec succès (93%)
✅ 20/30 AOV extraits (67%)
✅ 30/30 live_ads_7d extraits
✅ 30/30 live_ads_30d extraits

📊 Résultats finaux:
   - Boutiques traitées: 30/30
   - Taux de succès: 93%
   - Temps d'exécution: 24 minutes
   - AOV trouvé: 67%

🎉 Scraper MVP terminé avec succès
```

---

## 🔄 Maintenance

### Nettoyage des Logs

```bash
# Supprimer les anciens logs
find logs/ -name "*.log" -mtime +7 -delete

# Archiver les logs importants
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Mise à Jour

```bash
# Sauvegarder la configuration
cp .env .env.backup

# Mettre à jour le code
git pull origin main

# Restaurer la configuration
cp .env.backup .env
```

### Surveillance

```bash
# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les processus
ps aux | grep node
```

---

## 📚 Ressources Supplémentaires

### Documentation

- **Specification complète** : `/specs/007-trendtrack-mvp-scraper/spec.md`
- **Plan d'implémentation** : `/specs/007-trendtrack-mvp-scraper/plan/plan.md`
- **Tâches et roadmap** : `/specs/007-trendtrack-mvp-scraper/tasks.md`

### Support

- **Logs de debug** : `logs/update-mvp-progress.log`
- **Base de données** : `data/trendtrack.db`
- **Configuration** : `update-database-mvp.js`

### Comparaison avec Autres Scrapers

| Scraper | Script | Base de Données | Sauvegarde |
|---------|--------|-----------------|------------|
| **MVP** | `update-database-mvp.js` | `trendtrack.db` | ✅ |
| **Classique** | `update-database.js` | `trendtrack.db` | ✅ |
| **Noxtools Alpha** | `main.py` | ❌ Pas de BDD | ❌ |

---

## 🎯 Prochaines Étapes

### Après le Premier Lancement

1. **Vérifier les résultats** dans la base de données
2. **Analyser les logs** pour identifier les problèmes
3. **Ajuster la configuration** si nécessaire
4. **Planifier les lancements réguliers**

### Optimisation

1. **Ajuster les timeouts** selon votre connexion
2. **Modifier les pauses** selon les performances
3. **Configurer les retries** selon la stabilité
4. **Personnaliser les limites** selon vos besoins

### Intégration

1. **Connecter avec le scraper classique** si nécessaire
2. **Intégrer avec le scraper Noxtools** pour les métriques SEM
3. **Configurer des alertes** pour les échecs
4. **Mettre en place un monitoring** continu
