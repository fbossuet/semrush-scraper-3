# Guide de Démarrage Rapide : Système CPC et Credentials Centralisés

**Branche** : `004-cpc-credentials-system`  
**Créé** : 2025-01-18  
**Statut** : Implémenté  

## 🚀 Démarrage en 5 Minutes

### 1. Vérification de l'Installation
```bash
cd sem-scraper-final
ls -la api_credentials.py
# ✅ Le fichier doit exister
```

### 2. Test du Système de Credentials
```bash
python3 -c "
from api_credentials import get_api_credentials
creds = get_api_credentials()
print(f'✅ Credentials: {creds}')
print(f'✅ Source: {creds.get_source()}')
"
```

### 3. Test de l'Implémentation CPC
```bash
python3 test_cpc_implementation.py
```

### 4. Lancement du Scraper
```bash
python3 production_scraper_parallel.py
```

## ⚙️ Configuration (Optionnelle)

### Variables d'Environnement
```bash
# Configuration recommandée pour la production
export SAM_USER_ID=26931056
export SAM_API_KEY=943cfac719badc2ca14126e08b8fe44f
```

### Fichier .env
```bash
# Copier l'exemple
cp env_example.txt .env
# Éditer avec vos vraies valeurs
nano .env
```

## 📊 Vérification du Fonctionnement

### 1. Logs avec CPC
```bash
# Rechercher les logs avec CPC
grep "CPC:" sem-scraper-final/api.log
# ✅ Doit afficher: CPC: 2.501
```

### 2. Base de Données
```sql
-- Vérifier les données CPC
SELECT shop_id, cpc, paid_search_traffic 
FROM analytics 
WHERE cpc IS NOT NULL 
LIMIT 5;
```

### 3. Endpoint API
```bash
# Tester l'endpoint enrichi
curl "http://37.59.102.7:8001/albert?since=2025-01-01T00:00:00Z" | jq '.[0].cpc'
```

## 🔧 Utilisation Avancée

### Credentials Personnalisés
```python
from api_credentials import APICredentials

# Créer une instance personnalisée
creds = APICredentials()
print(creds.get_credentials())
```

### Test CPC Manuel
```python
from api_client_refactored import APIClientRefactored

async def test_cpc():
    client = APIClientRefactored()
    await client.initialize()
    
    metrics = await client.get_all_metrics_via_api("example.com", "20250115")
    print(f"CPC: {metrics.get('cpc', 'N/A')}")
    
    await client.close()
```

## 🐛 Dépannage

### Problème : Credentials non trouvés
```bash
# Vérifier les variables d'environnement
echo $SAM_USER_ID
echo $SAM_API_KEY

# Le système utilise automatiquement les fallbacks
```

### Problème : CPC = 0
```bash
# Vérifier les logs
grep "paid_traffic" sem-scraper-final/api.log
# Le CPC est 0 si pas de trafic payant
```

### Problème : Erreur d'import
```bash
# Vérifier le PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 test_cpc_implementation.py
```

## 📈 Monitoring

### Métriques à Surveiller
```bash
# Taux de succès CPC
grep "CPC:" sem-scraper-final/api.log | wc -l

# Source des credentials
grep "Credentials chargés" sem-scraper-final/api.log | tail -1
```

### Logs Importants
```bash
# Succès CPC
grep "Métriques organic.OverviewTrend récupérées (incluant CPC)"

# Erreurs
grep "❌.*CPC\|❌.*credentials"
```

## 🎯 Cas d'Usage

### Scraping avec CPC
```python
# Le CPC est automatiquement calculé et stocké
# Aucune action supplémentaire requise
```

### API avec CPC
```python
# L'endpoint /albert retourne maintenant le CPC
response = requests.get("http://37.59.102.7:8001/albert")
data = response.json()
cpc = data[0]['cpc']  # Nouveau champ
```

### Analyse CPC
```sql
-- Requêtes d'analyse CPC
SELECT 
    AVG(cpc) as avg_cpc,
    MAX(cpc) as max_cpc,
    COUNT(*) as domains_with_cpc
FROM analytics 
WHERE cpc > 0;
```

## 🔒 Sécurité

### Bonnes Pratiques
- ✅ Utiliser les variables d'environnement en production
- ✅ Ne pas commiter les credentials dans le code
- ✅ Rotation régulière des API keys

### Vérification Sécurité
```bash
# Vérifier qu'aucun credential n'est en dur
grep -r "26931056\|943cfac719badc2ca14126e08b8fe44f" sem-scraper-final/ --exclude="*.pyc"
# ✅ Seuls les fallbacks doivent apparaître
```

## 📚 Documentation Complète

### Fichiers de Documentation
- `README_CPC_CREDENTIALS.md` - Documentation complète
- `env_example.txt` - Exemple de configuration
- `test_cpc_implementation.py` - Tests de validation

### Support
- Consulter les logs pour le debugging
- Exécuter les tests de validation
- Vérifier la documentation complète

---

**Quickstart Status**: Ready  
**Last Updated**: 2025-01-18  
**Tested**: ✅
