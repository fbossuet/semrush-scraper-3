# Quickstart : Scraper Noxtools

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
**Input** : Spécification de fonctionnalité depuis `/specs/006-noxtools-scraper/spec.md`

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.x
- Playwright installé
- Base de données TrendTrack accessible
- Credentials Noxtools valides

### Installation
```bash
cd /home/ubuntu/projects/shopshopshops/test/scraper-noxtools-final
pip install -r requirements.txt
playwright install
```

### Configuration
```bash
# Variables d'environnement (optionnel)
export NOXTOOLS_USERNAME="johnychareon"
export NOXTOOLS_PASSWORD="fbossuetg"
export DB_PATH="trendtrack-scraper-final/data/trendtrack.db"
```

### Lancement Alpha
```bash
# Test complet du scraper
python3 main.py

# Test avec debug
python3 -c "
import sys
sys.path.insert(0, 'src')
from main import NoxtoolsScraper

scraper = NoxtoolsScraper()
print('✅ Scraper initialisé avec ServerManager')
print(f'Serveur actuel: {scraper.server_manager.get_current_server_name()}')
"
```

## 📋 Fonctionnalités Alpha

### ✅ Implémentées
- **ServerManager** : Gestion dynamique des serveurs semrush1→semrush5
- **Authentification** : Formulaire Noxtools avec nouveaux sélecteurs
- **Navigation** : Cross-domain avec maintien de session
- **Extraction métriques** : Sélecteurs DOM pour toutes les métriques
- **Formatage** : Pipeline de normalisation des données
- **Anti-détection** : User-Agents, headers, délais aléatoires
- **Fallback** : Switch automatique entre serveurs

### 🔄 En Cours
- **Session expirée** : Retry avec re-authentification
- **URLs harmonisées** : Test semrush1 vs semrush3

### 📊 Métriques Extraites
- `visits` : Nombre total de visites
- `organic_traffic` : Trafic organique
- `paid_search_traffic` : Trafic payant
- `conversion_rate` : Taux de conversion
- `avg_visit_duration` : Durée moyenne des visites
- `bounce_rate` : Taux de rebond
- `cpc` : Coût par clic
- `branded_traffic` : Trafic de marque

## 🏗️ Architecture

### Modules Principaux
```
src/
├── core/
│   ├── server_manager.py      # ✅ Gestion serveurs semrush1→semrush5
│   ├── playwright_manager.py  # ✅ Navigation et anti-détection
│   ├── auth_manager.py        # ✅ Authentification Noxtools
│   ├── session_manager.py     # ✅ Gestion sessions cross-domain
│   ├── metrics_extractor.py   # ✅ Extraction métriques DOM
│   └── market_overview_navigator.py  # ✅ Navigation Market Overview
├── services/
│   ├── shop_repository.py     # ✅ Récupération shops éligibles
│   ├── formatter.py           # ✅ Formatage des données
│   └── status_manager.py      # ✅ Gestion statuts scraping
└── utils/
    └── url_params.py          # ✅ Calcul paramètres URL
```

### ServerManager
```python
# Gestion centralisée des serveurs
from core.server_manager import get_server_manager

sm = get_server_manager()
print(f"Serveur actuel: {sm.get_current_server_name()}")
print(f"Domaine: {sm.get_current_domain()}")
print(f"Bridge: {sm.get_current_bridge_url()}")

# Normalisation URL
url = "https://semrush3.semrush.pw/analytics/overview/"
normalized = sm.normalize_url_to_current_server(url)
print(f"URL normalisée: {normalized}")
```

## 🧪 Tests

### Test ServerManager
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from core.server_manager import get_server_manager

sm = get_server_manager()
print('✅ ServerManager initialisé')
print(f'Serveurs disponibles: {len(sm.get_available_servers())}')
"
```

### Test Intégration
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from main import NoxtoolsScraper

scraper = NoxtoolsScraper()
print('✅ Scraper avec ServerManager')
print(f'Serveur: {scraper.server_manager.get_current_server_name()}')
"
```

## 📊 Base de Données

### Shops Éligibles
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL;
```

### Métriques Analytics
```sql
-- Table analytics (existante)
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    scraping_status TEXT,  -- 'completed', 'partial', 'failed', NULL
    
    -- Métriques Noxtools
    visits INTEGER,
    organic_traffic INTEGER,
    paid_search_traffic INTEGER,
    conversion_rate REAL,
    avg_visit_duration INTEGER,
    bounce_rate REAL,
    cpc REAL,
    branded_traffic INTEGER,
    
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```

## 🔧 Configuration

### ServerManager
```python
# Configuration des serveurs
servers = [
    "semrush1.semrush.pw",
    "semrush2.semrush.pw", 
    "semrush3.semrush.pw",
    "semrush4.semrush.pw",
    "semrush5.semrush.pw"
]

# Fallback automatique
sm.mark_server_failed("Session expired")
# → Switch automatique vers le serveur suivant
```

### Anti-Détection
```python
# Configuration stealth
stealth_config = {
    'user_agents': ['Mozilla/5.0...', 'Chrome/120.0...'],
    'headers': {'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document'},
    'delays': {'base_ms': 2000, 'jitter_ms': 1000},
    'rate_limiting': {'tokens_per_minute': 30}
}
```

## 🚨 Dépannage

### Problèmes Courants
1. **Session expirée** : Le ServerManager gère automatiquement le fallback
2. **Serveur indisponible** : Switch automatique vers le suivant
3. **URLs incohérentes** : Normalisation automatique par ServerManager

### Logs
```bash
# Logs détaillés
tail -f logs/noxtools.log

# Debug ServerManager
python3 -c "
from core.server_manager import get_server_manager
sm = get_server_manager()
print(sm.get_server_status_summary())
"
```

## 📈 Prochaines Étapes

### Version Beta
- **Formatage** : Application des standards de format
- **Base de données** : Insertion des métriques
- **Validation** : Contrôles d'intégrité

### Version Finale
- **Parallélisation** : Workers multiples
- **Performance** : Optimisation des requêtes
- **Monitoring** : Métriques de performance

## 📚 Documentation

- **Spec** : [spec.md](../spec.md)
- **Plan** : [plan.md](plan.md)
- **Tasks** : [tasks.md](../tasks.md)
- **Data Model** : [data-model.md](data-model.md)

**Branche** : `006-noxtools-scraper` | **Date** : 2025-01-18 | **Spec** : [../spec.md](../spec.md)  
**Input** : Spécification de fonctionnalité depuis `/specs/006-noxtools-scraper/spec.md`

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.x
- Playwright installé
- Base de données TrendTrack accessible
- Credentials Noxtools valides

### Installation
```bash
cd /home/ubuntu/projects/shopshopshops/test/scraper-noxtools-final
pip install -r requirements.txt
playwright install
```

### Configuration
```bash
# Variables d'environnement (optionnel)
export NOXTOOLS_USERNAME="johnychareon"
export NOXTOOLS_PASSWORD="fbossuetg"
export DB_PATH="trendtrack-scraper-final/data/trendtrack.db"
```

### Lancement Alpha
```bash
# Test complet du scraper
python3 main.py

# Test avec debug
python3 -c "
import sys
sys.path.insert(0, 'src')
from main import NoxtoolsScraper

scraper = NoxtoolsScraper()
print('✅ Scraper initialisé avec ServerManager')
print(f'Serveur actuel: {scraper.server_manager.get_current_server_name()}')
"
```

## 📋 Fonctionnalités Alpha

### ✅ Implémentées
- **ServerManager** : Gestion dynamique des serveurs semrush1→semrush5
- **Authentification** : Formulaire Noxtools avec nouveaux sélecteurs
- **Navigation** : Cross-domain avec maintien de session
- **Extraction métriques** : Sélecteurs DOM pour toutes les métriques
- **Formatage** : Pipeline de normalisation des données
- **Anti-détection** : User-Agents, headers, délais aléatoires
- **Fallback** : Switch automatique entre serveurs

### 🔄 En Cours
- **Session expirée** : Retry avec re-authentification
- **URLs harmonisées** : Test semrush1 vs semrush3

### 📊 Métriques Extraites
- `visits` : Nombre total de visites
- `organic_traffic` : Trafic organique
- `paid_search_traffic` : Trafic payant
- `conversion_rate` : Taux de conversion
- `avg_visit_duration` : Durée moyenne des visites
- `bounce_rate` : Taux de rebond
- `cpc` : Coût par clic
- `branded_traffic` : Trafic de marque

## 🏗️ Architecture

### Modules Principaux
```
src/
├── core/
│   ├── server_manager.py      # ✅ Gestion serveurs semrush1→semrush5
│   ├── playwright_manager.py  # ✅ Navigation et anti-détection
│   ├── auth_manager.py        # ✅ Authentification Noxtools
│   ├── session_manager.py     # ✅ Gestion sessions cross-domain
│   ├── metrics_extractor.py   # ✅ Extraction métriques DOM
│   └── market_overview_navigator.py  # ✅ Navigation Market Overview
├── services/
│   ├── shop_repository.py     # ✅ Récupération shops éligibles
│   ├── formatter.py           # ✅ Formatage des données
│   └── status_manager.py      # ✅ Gestion statuts scraping
└── utils/
    └── url_params.py          # ✅ Calcul paramètres URL
```

### ServerManager
```python
# Gestion centralisée des serveurs
from core.server_manager import get_server_manager

sm = get_server_manager()
print(f"Serveur actuel: {sm.get_current_server_name()}")
print(f"Domaine: {sm.get_current_domain()}")
print(f"Bridge: {sm.get_current_bridge_url()}")

# Normalisation URL
url = "https://semrush3.semrush.pw/analytics/overview/"
normalized = sm.normalize_url_to_current_server(url)
print(f"URL normalisée: {normalized}")
```

## 🧪 Tests

### Test ServerManager
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from core.server_manager import get_server_manager

sm = get_server_manager()
print('✅ ServerManager initialisé')
print(f'Serveurs disponibles: {len(sm.get_available_servers())}')
"
```

### Test Intégration
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from main import NoxtoolsScraper

scraper = NoxtoolsScraper()
print('✅ Scraper avec ServerManager')
print(f'Serveur: {scraper.server_manager.get_current_server_name()}')
"
```

## 📊 Base de Données

### Shops Éligibles
```sql
SELECT s.id, s.shop_url, s.shop_name
FROM shops s
JOIN analytics a ON s.id = a.shop_id
WHERE s.scraping_status != 'failed'
  AND s.details_scraping_status = 'details_extracted'
  AND a.scraping_status IS NULL;
```

### Métriques Analytics
```sql
-- Table analytics (existante)
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    scraping_status TEXT,  -- 'completed', 'partial', 'failed', NULL
    
    -- Métriques Noxtools
    visits INTEGER,
    organic_traffic INTEGER,
    paid_search_traffic INTEGER,
    conversion_rate REAL,
    avg_visit_duration INTEGER,
    bounce_rate REAL,
    cpc REAL,
    branded_traffic INTEGER,
    
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```

## 🔧 Configuration

### ServerManager
```python
# Configuration des serveurs
servers = [
    "semrush1.semrush.pw",
    "semrush2.semrush.pw", 
    "semrush3.semrush.pw",
    "semrush4.semrush.pw",
    "semrush5.semrush.pw"
]

# Fallback automatique
sm.mark_server_failed("Session expired")
# → Switch automatique vers le serveur suivant
```

### Anti-Détection
```python
# Configuration stealth
stealth_config = {
    'user_agents': ['Mozilla/5.0...', 'Chrome/120.0...'],
    'headers': {'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document'},
    'delays': {'base_ms': 2000, 'jitter_ms': 1000},
    'rate_limiting': {'tokens_per_minute': 30}
}
```

## 🚨 Dépannage

### Problèmes Courants
1. **Session expirée** : Le ServerManager gère automatiquement le fallback
2. **Serveur indisponible** : Switch automatique vers le suivant
3. **URLs incohérentes** : Normalisation automatique par ServerManager

### Logs
```bash
# Logs détaillés
tail -f logs/noxtools.log

# Debug ServerManager
python3 -c "
from core.server_manager import get_server_manager
sm = get_server_manager()
print(sm.get_server_status_summary())
"
```

## 📈 Prochaines Étapes

### Version Beta
- **Formatage** : Application des standards de format
- **Base de données** : Insertion des métriques
- **Validation** : Contrôles d'intégrité

### Version Finale
- **Parallélisation** : Workers multiples
- **Performance** : Optimisation des requêtes
- **Monitoring** : Métriques de performance

## 📚 Documentation

- **Spec** : [spec.md](../spec.md)
- **Plan** : [plan.md](plan.md)
- **Tasks** : [tasks.md](../tasks.md)
- **Data Model** : [data-model.md](data-model.md)
