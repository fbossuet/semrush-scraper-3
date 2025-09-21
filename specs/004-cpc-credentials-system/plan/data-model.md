# Modèle de Données : Système CPC et Credentials Centralisés

**Branche** : `004-cpc-credentials-system`  
**Créé** : 2025-01-18  
**Statut** : Implémenté  

## Vue d'Ensemble

Ce document décrit les modifications du modèle de données pour supporter la métrique CPC et le système de credentials centralisé.

## Modifications de la Base de Données

### Table `analytics` - Champ CPC

#### Ajout du Champ
```sql
-- Le champ cpc existe déjà dans la structure
cpc NUMERIC  -- Coût par clic calculé
```

#### Utilisation
```python
# Récupération des métriques incluant CPC
analytics_data = {
    "organic_traffic": "15000",
    "paid_search_traffic": "5000", 
    "cpc": "2.501",  # Nouveau champ
    "conversion_rate": "3.2"
}
```

### Table `shops` - Pas de Modification

La table `shops` n'a pas été modifiée car le CPC est une métrique d'analytics, pas de shop.

## Modèle de Données des Credentials

### Classe APICredentials

```python
class APICredentials:
    def __init__(self):
        self._credentials = {
            'userId': int,      # ID utilisateur
            'apiKey': str,      # Clé API
            'source': str       # Source: 'environment'|'fallback'|'emergency_fallback'
        }
```

### Structure des Credentials

```python
# Format de retour standardisé
credentials = {
    'userId': 26931056,
    'apiKey': '943cfac719badc2ca14126e08b8fe44f'
}
```

## Flux de Données CPC

### 1. Récupération API
```python
# Données brutes de l'API organic.OverviewTrend
api_data = {
    'adwordsTraffic': 500,        # Trafic payant
    'adwordsTrafficCost': 1250.50 # Coût payant
}
```

### 2. Calcul CPC
```python
# Calcul automatique
paid_traffic = api_data.get('adwordsTraffic', 0)
paid_traffic_cost = api_data.get('adwordsTrafficCost', 0)

if paid_traffic > 0 and paid_traffic_cost > 0:
    cpc = round(paid_traffic_cost / paid_traffic, 4)
else:
    cpc = 0
```

### 3. Stockage
```python
# Stockage dans session_data
session_data['data']['domain_overview']['cpc'] = str(cpc)

# Formatage pour l'API
analytics_data['cpc'] = str(cpc)
```

### 4. Sauvegarde BDD
```sql
-- Insertion/Update dans la table analytics
UPDATE analytics 
SET cpc = 2.501 
WHERE shop_id = 123;
```

## Modèle de Configuration

### Variables d'Environnement
```bash
# Configuration optionnelle
SAM_USER_ID=26931056
SAM_API_KEY=943cfac719badc2ca14126e08b8fe44f
```

### Fallbacks
```python
# Fallbacks sécurisés
DEFAULT_USER_ID = 26931056
DEFAULT_API_KEY = "943cfac719badc2ca14126e08b8fe44f"
```

## Validation des Données

### Validation CPC
```python
def validate_cpc(cpc_value):
    """Valide la valeur CPC"""
    try:
        cpc_float = float(cpc_value)
        return 0 <= cpc_float <= 1000  # Plage raisonnable
    except (ValueError, TypeError):
        return False
```

### Validation Credentials
```python
def validate_credentials(creds):
    """Valide les credentials"""
    return (
        isinstance(creds.get('userId'), int) and
        isinstance(creds.get('apiKey'), str) and
        len(creds.get('apiKey', '')) >= 10
    )
```

## Intégration API

### Endpoint /albert
```json
{
  "id": 123,
  "shop_name": "example.com",
  "organic_traffic": 15000,
  "paid_search_traffic": 5000,
  "cpc": 2.501,
  "conversion_rate": 3.2
}
```

### Format de Réponse
```python
# Structure de retour enrichie
{
    "shops": [
        {
            "id": 123,
            "shop_name": "example.com",
            "analytics": {
                "organic_traffic": 15000,
                "paid_search_traffic": 5000,
                "cpc": 2.501,
                "conversion_rate": 3.2
            }
        }
    ]
}
```

## Gestion des Erreurs

### Erreurs CPC
```python
# Cas d'erreur gérés
if paid_traffic < 0 or paid_traffic_cost < 0:
    cpc = 0  # Valeur par défaut sécurisée
```

### Erreurs Credentials
```python
# Fallback d'urgence
try:
    credentials = load_from_environment()
except Exception:
    credentials = get_emergency_fallback()
```

## Performance et Optimisation

### Cache des Credentials
```python
# Singleton pour éviter les rechargements
_global_credentials = None

def get_api_credentials():
    global _global_credentials
    if _global_credentials is None:
        _global_credentials = APICredentials()
    return _global_credentials
```

### Calcul CPC Optimisé
```python
# Calcul direct sans conversion multiple
cpc = round(paid_traffic_cost / paid_traffic, 4) if paid_traffic > 0 else 0
```

## Tests de Données

### Tests CPC
```python
# Cas de test
test_cases = [
    (500, 1250.50, 2.501),    # Cas normal
    (0, 100, 0),              # Trafic payant = 0
    (100, 0, 0),              # Coût payant = 0
    (1000, 2500, 2.5)         # Cas simple
]
```

### Tests Credentials
```python
# Validation des sources
assert get_credentials().get_source() in ['environment', 'fallback', 'emergency_fallback']
```

## Migration et Compatibilité

### Compatibilité Ascendante
- ✅ Tous les champs existants préservés
- ✅ Aucune modification de structure requise
- ✅ Fonctionnalités existantes intactes

### Migration des Données
- ✅ Aucune migration requise
- ✅ Champ CPC déjà présent dans la structure
- ✅ Remplissage automatique lors du scraping

## Monitoring et Métriques

### Métriques CPC
```python
# Statistiques CPC
cpc_stats = {
    'total_domains': 1000,
    'domains_with_cpc': 750,
    'average_cpc': 2.45,
    'max_cpc': 15.67
}
```

### Métriques Credentials
```python
# Monitoring des credentials
cred_stats = {
    'source_environment': 80,
    'source_fallback': 20,
    'source_emergency': 0
}
```

---

**Data Model Status**: Implemented  
**Implementation Date**: 2025-01-18  
**Validation Date**: 2025-01-18
