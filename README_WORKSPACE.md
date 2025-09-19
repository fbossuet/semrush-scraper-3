# Workspace Configuration - Branche Test

## 🎯 Objectif
Ce répertoire `/home/ubuntu/projects/shopshopshops/test/` est le workspace de développement pour la branche git `test`.

## 📁 Structure
```
/home/ubuntu/projects/shopshopshops/test/
├── .cursorrules                    # Règles pour Cursor
├── check_workspace.sh             # Script de vérification
├── workspace_config.py            # Configuration centralisée
├── database_config.py             # Configuration des bases de données
├── sem-scraper-final/             # API et scrapers
│   ├── api_server.py              # Serveur API principal
│   ├── menu_workers.py            # Menu de gestion des workers
│   └── trendtrack_api.py          # Interface base de données
└── trendtrack-scraper-final/      # Scrapers et données
    └── data/
        ├── trendtrack.db          # Base de données de production
        └── trendtrack_test.db     # Base de données de test
```

## 🚀 Commandes utiles

### Vérification du workspace
```bash
cd /home/ubuntu/projects/shopshopshops/test
./check_workspace.sh
python3 workspace_config.py
```

### Démarrage de l'API
```bash
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
python3 api_server.py
```

### Menu des workers
```bash
cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
python3 menu_workers.py
```

## 🌐 URLs importantes
- **API**: http://37.59.102.7:8001
- **Documentation**: http://37.59.102.7:8001/docs

## ⚠️ Règles importantes
1. **TOUJOURS** travailler dans `/home/ubuntu/projects/shopshopshops/test/`
2. **NE JAMAIS** aller dans `/home/ubuntu/trendtrack-scraper-final/`
3. Utiliser les scripts de vérification avant de commencer
4. Développer dans `/test/`, déployer vers les autres branches quand prêt

## 🔧 Configuration Cursor
Pour éviter les confusions :
1. Ouvrir directement ce répertoire dans Cursor
2. Le fichier `.cursorrules` contient les règles de travail
3. Utiliser les scripts de vérification régulièrement

## 🎯 Ouvrir Cursor dans le bon répertoire

### Méthode 1 : Script automatique
```bash
./open_cursor.sh
```

### Méthode 2 : Commande directe
```bash
cd /home/ubuntu/projects/shopshopshops/test && cursor .
```

### Méthode 3 : Via l'interface Cursor
1. Ouvrir Cursor
2. `Ctrl+O` ou `File > Open Folder`
3. Naviguer vers `/home/ubuntu/projects/shopshopshops/test`

### Méthode 4 : Alias (après setup_aliases.sh)
```bash
./setup_aliases.sh  # Une seule fois
test-cursor         # Ensuite
```
