# 🎯 Guide Rapide - Dashboard SEO Analytics

## 🚀 Démarrage en 30 secondes

```bash
# 1. Installer les dépendances (si pas déjà fait)
npm install

# 2. Démarrer le dashboard
npm run dashboard

# 3. Ouvrir le navigateur
# → http://localhost:3000
```

## 🎮 Utilisation Simple

### Via l'Interface Web (Recommandé)

1. **Ouvrir** : `http://localhost:3000`
2. **Saisir** le domaine : `https://the-foldie.com`
3. **Cocher** les analyses souhaitées :
   - ✅ Trafic Organique
   - ✅ Traffic Competitors 
   - ✅ Domain Overview
   - ✅ Analyse Intelligente
4. **Cliquer** sur "Lancer l'Analyse" 🚀
5. **Attendre** la progression temps réel
6. **Voir** les résultats avec graphiques 📊

### Interface Visuelle Complète

- 📊 **Graphiques interactifs** (Chart.js)
- 📈 **Stats en temps réel**
- 📁 **Téléchargement** des résultats
- 🔄 **Progression live** des scrapers
- 📱 **Design responsive** (mobile-friendly)

## ⚡ Scripts NPM Disponibles

```bash
# Interface web complète
npm run dashboard              # Démarrer le dashboard
npm run dashboard-dev          # Mode développement avec logs

# Serveur uniquement  
npm run server                 # Juste l'API sans vérifications

# Scrapers individuels (ancienne méthode)
npm run organic-traffic        # Trafic organique uniquement
npm run smart-traffic          # Traffic competitors uniquement
npm run analyze-domain         # Analyse complète

# Utilitaires
npm run install-playwright     # Installer navigateurs
```

## 🔧 Commandes de Test Rapide

### Test API Direct

```bash
# Status de l'API
curl http://localhost:3000/api/status

# Lancer analyse complète
curl -X POST http://localhost:3000/api/smart-analysis \
  -H "Content-Type: application/json" \
  -d '{"domain": "https://the-foldie.com"}'

# Voir les fichiers générés
curl http://localhost:3000/api/files/https%3A%2F%2Fthe-foldie.com
```

## 📊 Ce Que Vous Obtenez

### Métriques Automatiques
- **Trafic Organique** : 60.1k (exemple)
- **Visits Concurrents** : 846.6k
- **Mots-clés** : 450+
- **Backlinks** : 1.2k

### Fichiers de Résultats
- `organic-traffic-[domain]-[timestamp].json`
- `smart-traffic-[domain]-[timestamp].json`  
- `smart-analysis-[domain]-[timestamp].json`
- `analytics-[domain]-[timestamp].json`

### Visualisations
- 🍩 **Graphique en donut** des métriques principales
- 📊 **Graphique en barres** des nombres trouvés
- 📋 **Tableaux** de données détaillées
- 💾 **Export JSON** complet

## 🎯 Workflow Recommandé

### 1. Analyse Rapide (5 minutes)
```bash
npm run dashboard
# → Interface web → Saisir domaine → Lancer analyse
```

### 2. Analyse Personnalisée
- Décocher certaines analyses pour aller plus vite
- Se concentrer sur le trafic organique uniquement
- Utiliser l'API directement pour automatiser

### 3. Analyse en Masse
```bash
# Pour plusieurs domaines via l'API
for domain in "site1.com" "site2.com" "site3.com"; do
  curl -X POST http://localhost:3000/api/smart-analysis \
    -H "Content-Type: application/json" \
    -d "{\"domain\": \"$domain\"}"
done
```

## 🔍 Que Chercher dans les Résultats

### 📈 Trafic Organique
- **Nombre** exact de visites mensuelles
- **Source** de la donnée (NoxTools, SEMrush)
- **Tendance** d'évolution

### 🚗 Concurrents
- **Liste** des domaines similaires
- **Comparaison** de trafic
- **Opportunités** de mots-clés

### 🎯 Insights Business
- **Pages** les plus performantes
- **Mots-clés** rentables
- **Stratégies** des concurrents

## 🚨 Troubleshooting Rapide

### ❌ Erreur "Port already in use"
```bash
# Tuer les processus sur le port 3000
lsof -ti:3000 | xargs kill -9
npm run dashboard
```

### ❌ Scrapers ne fonctionnent pas
```bash
# Réinstaller Playwright
npm run install-playwright
npx playwright install chromium
```

### ❌ Interface blanche
- Vérifier la console du navigateur (F12)
- S'assurer que le serveur est démarré
- Tester `http://localhost:3000/api/status`

## 🎊 Fonctionnalités Bonus

### 📱 Mobile Ready
- Interface optimisée mobile
- Graphiques adaptatifs
- Navigation tactile

### ⚡ Temps Réel
- Progression en direct
- Notifications visuelles
- Annulation possible

### 💾 Persistance
- Résultats sauvegardés automatiquement
- Historique des analyses
- Export/import facile

### 🎨 Personnalisable
- Thème moderne avec variables CSS
- Graphiques Chart.js configurables
- API REST extensible

## 🚀 Prochaines Étapes

1. **Tester** avec vos domaines
2. **Explorer** les différents types d'analyse
3. **Automatiser** vos workflow via l'API
4. **Personnaliser** selon vos besoins
5. **Intégrer** dans vos outils existants

---

**🎯 Dashboard SEO Analytics - L'analyse concurrentielle simplifiée !** 📊✨

*Happy scraping!* 🚀