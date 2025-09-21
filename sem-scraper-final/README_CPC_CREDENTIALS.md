# 🚀 Système CPC et Credentials Centralisés

## 📋 Résumé des modifications

### ✅ **Implémenté le 18 janvier 2025**

1. **Système de credentials centralisé** avec support des variables d'environnement
2. **Récupération automatique de la métrique CPC** via l'API organic.OverviewTrend
3. **Intégration complète** dans le scraper de production

---

## 🔑 **Système de Credentials**

### **Fichier principal**: `api_credentials.py`

Le système utilise les variables d'environnement avec des fallbacks sécurisés :

```bash
# Variables d'environnement supportées
SAM_USER_ID=26931056
SAM_API_KEY=943cfac719badc2ca14126e08b8fe44f

# Alternative
MYTOOLSPLAN_USER_ID=26931056
MYTOOLSPLAN_API_KEY=943cfac719badc2ca14126e08b8fe44f
```

### **Utilisation dans le code**:

```python
from api_credentials import get_credentials_dict, get_api_credentials

# Récupération directe du dictionnaire
credentials = get_credentials_dict()
# {'userId': 26931056, 'apiKey': '943cfac719badc2ca14126e08b8fe44f'}

# Récupération de l'instance complète
creds = get_api_credentials()
print(creds.get_source())  # 'environment' ou 'fallback'
```

### **Fallbacks sécurisés**:
- Si les variables d'environnement ne sont pas définies, le système utilise automatiquement les credentials par défaut du scraper
- Aucune interruption de service

---

## 💰 **Métrique CPC (Cost Per Click)**

### **Calcul automatique**:
```
CPC = paid_traffic_cost / paid_traffic
```

### **Intégration dans le scraper**:

1. **Récupération via API**: `organic.OverviewTrend` retourne `adwordsTrafficCost` et `adwordsTraffic`
2. **Calcul automatique**: Dans `api_client_refactored.py`
3. **Stockage**: Dans `session_data['data']['domain_overview']['cpc']`
4. **Sauvegarde**: Dans la base de données via `format_analytics_for_api()`

### **Logs enrichis**:
```
✅ Worker 1: Domain Overview terminé - Organic: 15000, Paid: 5000, Traffic: 20000, Branded: 3000, CPC: 2.45, Conversion: 3.2%
```

---

## 🧪 **Tests et Validation**

### **Script de test**: `test_cpc_implementation.py`

```bash
cd sem-scraper-final
python3 test_cpc_implementation.py
```

**Tests inclus**:
1. ✅ Système de credentials
2. ✅ API Client avec récupération CPC
3. ✅ Intégration Production Scraper

---

## 📁 **Fichiers modifiés**

### **Nouveaux fichiers**:
- `api_credentials.py` - Système de credentials centralisé
- `env_example.txt` - Exemple de configuration
- `test_cpc_implementation.py` - Script de test
- `README_CPC_CREDENTIALS.md` - Cette documentation

### **Fichiers modifiés**:
- `api_client_refactored.py` - Calcul CPC + credentials centralisés
- `production_scraper_parallel.py` - Intégration CPC + credentials centralisés

---

## 🔧 **Configuration**

### **Option 1: Variables d'environnement (recommandé)**
```bash
export SAM_USER_ID=26931056
export SAM_API_KEY=943cfac719badc2ca14126e08b8fe44f
```

### **Option 2: Fichier .env**
```bash
# Copier env_example.txt vers .env
cp env_example.txt .env
# Éditer .env avec vos vraies valeurs
```

### **Option 3: Fallback automatique**
Si aucune variable n'est définie, le système utilise automatiquement les credentials par défaut.

---

## 🚀 **Utilisation**

### **Lancement normal du scraper**:
```bash
cd sem-scraper-final
python3 production_scraper_parallel.py
```

Le système récupère automatiquement :
- ✅ Les credentials (depuis l'environnement ou fallback)
- ✅ La métrique CPC pour chaque domaine
- ✅ Toutes les autres métriques existantes

### **Vérification des credentials**:
```python
from api_credentials import get_api_credentials
creds = get_api_credentials()
print(f"Source: {creds.get_source()}")
print(f"User ID: {creds.get_user_id()}")
```

---

## 📊 **Métriques CPC dans la base de données**

### **Table analytics**:
```sql
-- Le champ cpc est maintenant rempli automatiquement
SELECT shop_id, cpc, paid_search_traffic, organic_traffic 
FROM analytics 
WHERE cpc IS NOT NULL AND cpc > 0;
```

### **Endpoint API**:
```bash
# L'endpoint /albert retourne maintenant le CPC
curl "http://37.59.102.7:8001/albert?since=2025-01-01T00:00:00Z"
```

---

## ⚠️ **Notes importantes**

1. **Compatibilité**: Toutes les fonctionnalités existantes sont préservées
2. **Performance**: Aucun impact sur les performances (même API call)
3. **Sécurité**: Les credentials par défaut sont conservés comme fallback
4. **Logs**: Le CPC apparaît maintenant dans tous les logs de scraping

---

## 🎯 **Prochaines étapes**

1. **Test en production** avec quelques domaines
2. **Validation** des calculs CPC
3. **Monitoring** des performances
4. **Documentation** des métriques CPC dans l'API

---

## 📞 **Support**

En cas de problème :
1. Vérifier les logs du scraper
2. Exécuter `test_cpc_implementation.py`
3. Vérifier les variables d'environnement
4. Consulter cette documentation
