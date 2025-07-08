# 🎯 Installation Dashboard SEO - Local

## ⚡ **Démarrage Ultra Rapide (3 étapes)**

### 1️⃣ **Ouvrir un Terminal** 
```bash
# Windows: Win + R → cmd → Entrée
# Mac: Cmd + Espace → terminal → Entrée  
# Linux: Ctrl + Alt + T
```

### 2️⃣ **Aller dans le Dossier**
```bash
# Remplace "chemin-vers-ton-dossier" par le vrai chemin
cd chemin-vers-seo-dashboard-local

# Exemple Windows:
# cd C:\Users\tonnom\Desktop\seo-dashboard-local

# Exemple Mac/Linux:
# cd ~/Desktop/seo-dashboard-local
```

### 3️⃣ **Démarrer** 🚀
```bash
# Installation automatique + démarrage
npm run setup
npm start

# OU en une seule fois
npm install && npm start
```

### 4️⃣ **Ouvrir le Navigateur**
```
http://localhost:3000
```

## 🎯 **Test Rapide**

1. **Saisir un domaine** : `https://the-foldie.com`
2. **Cocher les analyses** souhaitées
3. **Cliquer** "Lancer l'Analyse" 
4. **Regarder** la progression temps réel
5. **Voir** les résultats avec graphiques ! 📊

## 🔧 **Si Problème**

### ❌ "Node.js not found"
```bash
# Installer Node.js depuis:
# https://nodejs.org/
# Prendre la version LTS (recommandée)
```

### ❌ "Port 3000 already in use" 
```bash
# Utiliser un autre port
PORT=3001 npm start

# Puis ouvrir: http://localhost:3001
```

### ❌ "npm not found"
```bash
# Node.js inclut npm normalement
# Redémarrer le terminal après installation Node.js
```

## 🚀 **Scripts Disponibles**

```bash
npm start           # Démarrer le dashboard
npm run setup       # Installation complète
npm run dev         # Mode développement
npm run server      # Serveur seul
```

## 📁 **Structure du Dossier**

```
seo-dashboard-local/
├── 📄 package.json              # Configuration
├── 🚀 start-dashboard.js        # Script de démarrage
├── 📄 INSTALLATION-LOCALE.md    # Ce guide
├── public/                      # Interface web
│   ├── index.html              # Page principale
│   ├── style.css               # Design moderne
│   └── script.js               # JavaScript
├── src/                        # Code serveur
│   └── web-server.js           # Serveur Express
└── results/                    # Résultats (créé auto)
```

## 🎊 **Fonctionnalités**

- ✅ **Interface web moderne** 
- ✅ **Graphiques interactifs**
- ✅ **Progression temps réel**
- ✅ **Export des résultats**
- ✅ **Design responsive**
- ✅ **API REST intégrée**

## 📞 **Support**

Si ça marche pas :

1. **Vérifier** Node.js : `node --version`
2. **Reinstaller** : `npm install`
3. **Autre port** : `PORT=3001 npm start`
4. **Redémarrer** le terminal

---

**🎯 Une fois lancé, direction `http://localhost:3000` pour analyser tes concurrents !** 🚀