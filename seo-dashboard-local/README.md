# 🎯 SEO Analytics Dashboard

**Dashboard moderne pour analyser les métriques SEO de vos concurrents** avec NoxTools, SEMrush et plus encore !

![Dashboard](https://img.shields.io/badge/Status-Ready-green) ![Node.js](https://img.shields.io/badge/Node.js-16%2B-blue) ![Playwright](https://img.shields.io/badge/Playwright-Latest-purple)

## ✨ Fonctionnalités

- 🌐 **Interface web moderne** avec design responsive
- 📈 **Analyse du trafic organique** via NoxTools
- 🚗 **Suivi des concurrents** avec smart traffic
- 🎯 **Vue d'ensemble des domaines** complète
- 🧠 **Analyse intelligente** combinant plusieurs sources
- 📊 **Visualisation graphique** des données
- � **Export/Import** des résultats
- ⚡ **Temps réel** avec progression en direct

## � Installation Rapide

```bash
# 1. Cloner ou télécharger le projet
git clone <votre-repo>
cd seo-analytics-dashboard

# 2. Installer les dépendances
npm install

# 3. Installer Playwright (si pas déjà fait)
npx playwright install

# 4. Démarrer le dashboard
node start-dashboard.js
```

## 🎮 Utilisation

### Démarrage Simple

```bash
# Option 1: Script de démarrage (recommandé)
node start-dashboard.js

# Option 2: Serveur direct
cd src && node web-server.js
```

### Interface Web

1. 🌐 Ouvrez votre navigateur sur `http://localhost:3000`
2. 📝 Saisissez le domaine à analyser (ex: `https://the-foldie.com`)
3. ✅ Sélectionnez les types d'analyse souhaités
4. 🚀 Cliquez sur "Lancer l'Analyse"
5. 📊 Visualisez les résultats en temps réel

### Types d'Analyse Disponibles

#### 📈 Trafic Organique
- Analyse via NoxTools
- Métriques de trafic SEO
- Évolution temporelle

#### 🚗 Traffic Competitors  
- Comparaison avec concurrents
- Données de visite
- Sources de trafic

#### 🎯 Domain Overview
- Vue d'ensemble complète
- Métriques techniques
- Analyse de contenu

#### 🧠 Analyse Intelligente
- Combine tous les scrapers
- Rapport consolidé
- Recommandations automatiques

## 📋 API Endpoints

Le serveur expose plusieurs endpoints REST :

```bash
# Analyser le trafic organique
POST /api/organic-traffic
Body: { "domain": "https://example.com" }

# Analyser le smart traffic
POST /api/smart-traffic  
Body: { "domain": "https://example.com" }

# Vue d'ensemble du domaine
POST /api/domain-overview
Body: { "domain": "https://example.com" }

# Analyse intelligente complète
POST /api/smart-analysis
Body: { "domain": "https://example.com" }

# Récupérer les fichiers d'un domaine
GET /api/files/:domain

# Contenu d'un fichier spécifique
GET /api/data/:filename

# Télécharger un fichier
GET /api/download/:filename

# Status de l'API
GET /api/status
```

## 📁 Structure du Projet

```
seo-analytics-dashboard/
├── 📄 README.md                    # Ce fichier
├── 📄 package.json                 # Configuration npm
├── 🚀 start-dashboard.js           # Script de démarrage
├── src/                             # Code source
│   ├── 🌐 web-server.js            # Serveur Express
│   ├── 📈 organic-traffic-scraper.js
│   ├── � smart-traffic-scraper.js
│   └── 🎯 smart-scraper.js
├── public/                          # Interface web
│   ├── 📄 index.html               # Page principale
│   ├── 🎨 style.css                # Styles modernes
│   └── ⚡ script.js                # JavaScript frontend
└── results/                         # Résultats d'analyse
    └── 📊 *.json                   # Données scrappées
```

## 🔧 Configuration

### Variables d'Environnement

```bash
# Port du serveur (défaut: 3000)
PORT=3000

# Timeout des scrapers (défaut: 5 minutes)
SCRAPER_TIMEOUT=300000

# Dossier de sauvegarde (défaut: ./results)
RESULTS_DIR=./results
```

### Personnalisation

Vous pouvez modifier facilement :

- **🎨 Design** : Éditez `public/style.css`
- **⚡ Fonctionnalités** : Modifiez `public/script.js`
- **🔧 API** : Ajoutez des endpoints dans `src/web-server.js`
- **🤖 Scrapers** : Créez de nouveaux scrapers dans `src/`

## � Exemple d'Utilisation

### Via l'Interface Web

1. **Saisie du domaine** : `https://the-foldie.com`
2. **Sélection des analyses** : Toutes cochées
3. **Lancement** : Clic sur "Lancer l'Analyse"
4. **Progression** : Suivi temps réel
5. **Résultats** : Graphiques + données détaillées

### Via API avec cURL

```bash
# Analyse complète
curl -X POST http://localhost:3000/api/smart-analysis \
  -H "Content-Type: application/json" \
  -d '{"domain": "https://the-foldie.com"}'

# Récupérer les résultats
curl http://localhost:3000/api/files/https%3A%2F%2Fthe-foldie.com
```

## 🎯 Métriques Collectées

Le dashboard collecte automatiquement :

### 📈 Trafic Organique
- Nombre de visites organiques
- Mots-clés positionnés
- Pages les plus visitées
- Évolution mensuelle

### 🚗 Analyse Concurrentielle  
- Domaines concurrents
- Comparaison de trafic
- Sources de référence
- Opportunités de mots-clés

### 🔍 Données Techniques
- Vitesse de chargement
- Score SEO
- Méta-données
- Structure technique

### 📊 Visualisations
- Graphiques interactifs (Chart.js)
- Tableaux de données
- Export JSON/CSV
- Comparaisons temporelles

## 🛠️ Dépannage

### Problèmes Courants

#### ❌ Serveur ne démarre pas
```bash
# Vérifier les dépendances
npm install

# Vérifier le port
lsof -i :3000
```

#### ❌ Scrapers ne fonctionnent pas
```bash
# Vérifier Playwright
npx playwright install

# Tester un scraper individuellement
node src/organic-traffic-scraper.js https://example.com
```

#### ❌ Pas de données dans l'interface
```bash
# Vérifier le dossier results
ls -la results/

# Vérifier les logs du serveur
# (regarder la console où vous avez lancé le serveur)
```

### Debug Mode

Pour plus de détails lors du debug :

```bash
# Mode verbose
DEBUG=* node start-dashboard.js

# Logs détaillés des scrapers
NODE_ENV=development node start-dashboard.js
```

## 🔄 Mise à Jour

Pour mettre à jour le dashboard :

```bash
# Sauvegarder vos résultats
cp -r results/ results-backup/

# Mettre à jour le code
git pull origin main

# Réinstaller les dépendances si nécessaire
npm install
```

## � Performances

### Optimisations Incluses

- ⚡ **Scrapers en parallèle** pour l'analyse intelligente
- 🗜️ **Compression gzip** pour les réponses API
- 💾 **Cache des résultats** pour éviter les re-analyses
- 🚀 **Interface responsive** optimisée mobile

### Limites Recommandées

- **Max 5 analyses simultanées** par instance
- **Timeout 5 minutes** par scraper
- **Fichiers < 50MB** pour de bonnes performances

## 🤝 Contribution

Pour améliorer le dashboard :

1. 🍴 Fork le projet
2. 🌟 Créez une branche feature
3. ✨ Ajoutez vos améliorations
4. 🧪 Testez vos modifications
5. 📩 Proposez une Pull Request

### Idées d'Améliorations

- 🔔 **Notifications push** en fin d'analyse
- 📱 **App mobile** companion
- 🤖 **IA pour recommandations** SEO
- 📧 **Rapports automatiques** par email
- 🔄 **Analyses programmées** (cron jobs)

## 📄 Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, le modifier et le redistribuer.

## 🆘 Support

Si vous avez des questions ou des problèmes :

1. 📖 Consultez cette documentation
2. 🔍 Regardez les [Issues](../../issues) existantes
3. 💬 Ouvrez une nouvelle issue si nécessaire
4. 📧 Contactez l'équipe de développement

---

**🎯 Happy scraping! Analysez vos concurrents efficacement avec le SEO Analytics Dashboard!** 🚀
