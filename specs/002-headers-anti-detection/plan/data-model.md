# Data Model: Système de Headers Anti-Détection

**Branch**: `002-headers-anti-detection` | **Date**: 2025-09-19 | **Spec**: `/specs/002-headers-anti-detection/spec.md`

## Entity Overview

### Core Entities
1. **HeaderProfile** - Profil complet de headers pour une identité de navigateur
2. **HeaderRotation** - Logique de rotation et timing des headers
3. **StealthIdentity** - Identité complète d'un worker (headers + comportement)
4. **HeaderValidation** - Validation et adaptation des headers

---

## 1. HeaderProfile Entity

### Purpose
Représente une combinaison complète de headers HTTP pour simuler une identité de navigateur spécifique.

### Attributes
```python
class HeaderProfile:
    # Identifiant unique
    profile_id: str                    # UUID unique du profil
    name: str                          # Nom descriptif (ex: "Chrome_Windows_120")
    version: str                       # Version du profil
    
    # Headers de base
    user_agent: str                    # User-Agent string
    accept_language: str               # Accept-Language header
    accept_encoding: str               # Accept-Encoding header
    accept: str                        # Accept header
    
    # Headers de sécurité modernes
    sec_fetch_dest: str                # Sec-Fetch-Dest
    sec_fetch_mode: str                # Sec-Fetch-Mode
    sec_fetch_site: str                # Sec-Fetch-Site
    sec_fetch_user: str                # Sec-Fetch-User
    
    # Headers de navigation
    upgrade_insecure_requests: str     # Upgrade-Insecure-Requests
    cache_control: str                 # Cache-Control
    connection: str                    # Connection
    dnt: str                          # DNT (Do Not Track)
    
    # Headers API spécifiques
    content_type: str                  # Content-Type pour les requêtes API
    x_requested_with: str              # X-Requested-With pour AJAX
    
    # Métadonnées
    browser_family: str                # Chrome, Firefox, Safari, Edge
    os_family: str                     # Windows, macOS, Linux
    device_type: str                   # Desktop, Mobile, Tablet
    created_at: datetime               # Date de création
    last_used: datetime                # Dernière utilisation
    usage_count: int                   # Nombre d'utilisations
    success_rate: float                # Taux de succès (0.0-1.0)
    
    # Configuration
    is_active: bool                    # Profil actif
    priority: int                      # Priorité d'utilisation (1-10)
    tags: List[str]                    # Tags pour catégorisation
```

### Relationships
- **One-to-Many** avec `HeaderRotation` : Un profil peut avoir plusieurs stratégies de rotation
- **Many-to-One** avec `StealthIdentity` : Plusieurs profils peuvent être utilisés par une identité

### Business Rules
- Chaque profil doit avoir un User-Agent unique
- Les headers Sec-Fetch-* doivent être cohérents entre eux
- Le taux de succès doit être mis à jour après chaque utilisation
- Les profils inactifs ne doivent pas être utilisés pour de nouvelles sessions

---

## 2. HeaderRotation Entity

### Purpose
Gère la logique de rotation des headers, incluant le timing, les patterns et les conditions de rotation.

### Attributes
```python
class HeaderRotation:
    # Identifiant
    rotation_id: str                   # UUID unique
    name: str                          # Nom de la stratégie
    
    # Configuration de rotation
    rotation_interval: int             # Intervalle en secondes
    jitter_range: int                  # Variation aléatoire en secondes
    rotation_type: str                 # 'time_based', 'request_based', 'error_based'
    
    # Conditions de rotation
    min_requests_before_rotation: int  # Minimum de requêtes avant rotation
    max_requests_before_rotation: int  # Maximum de requêtes avant rotation
    error_threshold: int               # Seuil d'erreurs pour rotation forcée
    
    # Patterns de comportement humain
    respect_work_hours: bool           # Respecter les heures de travail
    work_start_hour: int               # Heure de début (0-23)
    work_end_hour: int                 # Heure de fin (0-23)
    timezone: str                      # Fuseau horaire
    
    # Gestion des sessions
    session_consistency: bool          # Cohérence pendant une session
    session_duration: int              # Durée de session en secondes
    cooldown_period: int               # Période de cooldown en secondes
    
    # Métadonnées
    created_at: datetime               # Date de création
    last_rotation: datetime            # Dernière rotation
    rotation_count: int                # Nombre de rotations effectuées
    is_active: bool                    # Stratégie active
```

### Relationships
- **Many-to-One** avec `HeaderProfile` : Une stratégie peut gérer plusieurs profils
- **One-to-One** avec `StealthIdentity` : Chaque identité a une stratégie de rotation

### Business Rules
- La rotation ne doit pas se faire pendant une requête active
- Le jitter doit être appliqué pour éviter les patterns prévisibles
- Les rotations basées sur les erreurs ont priorité sur les rotations temporelles
- La cohérence de session doit être respectée sauf en cas d'erreur critique

---

## 3. StealthIdentity Entity

### Purpose
Représente l'identité complète d'un worker, incluant les headers, le comportement et le timing.

### Attributes
```python
class StealthIdentity:
    # Identifiant
    identity_id: str                   # UUID unique
    worker_id: str                     # ID du worker associé
    
    # Profil de headers actuel
    current_profile: HeaderProfile     # Profil de headers actuel
    profile_history: List[str]         # Historique des profils utilisés
    
    # Configuration de rotation
    rotation_strategy: HeaderRotation  # Stratégie de rotation
    next_rotation_time: datetime       # Prochaine rotation programmée
    
    # Comportement et timing
    request_patterns: Dict[str, Any]   # Patterns de requêtes
    timing_behavior: Dict[str, Any]    # Comportement de timing
    human_like_delays: bool            # Délais de type humain
    
    # État de session
    session_start_time: datetime       # Début de session
    session_duration: int              # Durée de session en secondes
    is_session_active: bool            # Session active
    session_requests_count: int        # Nombre de requêtes dans la session
    
    # Métriques de performance
    total_requests: int                # Total des requêtes
    successful_requests: int           # Requêtes réussies
    failed_requests: int               # Requêtes échouées
    blocked_requests: int              # Requêtes bloquées
    success_rate: float                # Taux de succès global
    
    # Détection et adaptation
    last_detection_time: datetime      # Dernière détection
    detection_count: int               # Nombre de détections
    adaptation_strategy: str           # Stratégie d'adaptation
    is_under_suspicion: bool           # Sous suspicion
    
    # Métadonnées
    created_at: datetime               # Date de création
    last_activity: datetime            # Dernière activité
    is_active: bool                    # Identité active
```

### Relationships
- **One-to-One** avec `HeaderProfile` : Une identité utilise un profil à la fois
- **One-to-One** avec `HeaderRotation` : Une identité a une stratégie de rotation
- **One-to-Many** avec `HeaderValidation` : Une identité peut avoir plusieurs validations

### Business Rules
- Une identité ne peut être active que sur un worker à la fois
- Le taux de succès doit être recalculé après chaque requête
- Les identités sous suspicion doivent être mises en quarantaine
- La rotation doit être déclenchée selon la stratégie configurée

---

## 4. HeaderValidation Entity

### Purpose
Gère la validation des headers basée sur les réponses des sites et l'adaptation de la stratégie.

### Attributes
```python
class HeaderValidation:
    # Identifiant
    validation_id: str                 # UUID unique
    identity_id: str                   # ID de l'identité associée
    
    # Contexte de validation
    site_url: str                      # URL du site testé
    request_type: str                  # Type de requête (navigation, api, fetch)
    headers_used: Dict[str, str]       # Headers utilisés pour la requête
    
    # Résultats de validation
    response_status: int               # Code de statut HTTP
    response_headers: Dict[str, str]   # Headers de réponse
    response_time: float               # Temps de réponse en secondes
    is_successful: bool                # Requête réussie
    is_blocked: bool                   # Requête bloquée
    is_suspicious: bool                # Comportement suspect détecté
    
    # Analyse de détection
    detection_signals: List[str]       # Signaux de détection identifiés
    confidence_score: float            # Score de confiance (0.0-1.0)
    risk_level: str                    # 'low', 'medium', 'high', 'critical'
    
    # Recommandations
    recommended_action: str            # Action recommandée
    suggested_headers: Dict[str, str]  # Headers suggérés
    rotation_recommended: bool         # Rotation recommandée
    profile_change_recommended: bool   # Changement de profil recommandé
    
    # Métadonnées
    validated_at: datetime             # Date de validation
    validation_duration: float         # Durée de validation en secondes
    is_processed: bool                 # Validation traitée
```

### Relationships
- **Many-to-One** avec `StealthIdentity` : Plusieurs validations peuvent appartenir à une identité
- **One-to-One** avec `HeaderProfile` : Une validation peut suggérer un profil spécifique

### Business Rules
- Chaque requête doit générer une validation
- Les validations critiques doivent déclencher une action immédiate
- Les recommandations doivent être basées sur des données historiques
- Les validations non traitées doivent être traitées dans les 5 minutes

---

## 5. HeaderConfiguration Entity

### Purpose
Gère la configuration globale du système de headers, incluant les pools de headers et les paramètres système.

### Attributes
```python
class HeaderConfiguration:
    # Identifiant
    config_id: str                     # UUID unique
    name: str                          # Nom de la configuration
    
    # Pools de headers
    user_agent_pool: List[str]         # Pool de User-Agents
    language_pool: List[str]           # Pool de langues
    browser_pool: List[str]            # Pool de navigateurs
    os_pool: List[str]                 # Pool de systèmes d'exploitation
    
    # Paramètres de rotation
    default_rotation_interval: int     # Intervalle de rotation par défaut
    max_rotation_jitter: int           # Jitter maximum
    min_session_duration: int          # Durée minimale de session
    
    # Seuils et limites
    max_detection_rate: float          # Taux de détection maximum acceptable
    min_success_rate: float            # Taux de succès minimum requis
    max_consecutive_failures: int      # Échecs consécutifs maximum
    
    # Configuration de sécurité
    enable_sec_fetch_headers: bool     # Activer les headers Sec-Fetch-*
    enable_dnt_header: bool            # Activer le header DNT
    enable_upgrade_insecure: bool      # Activer Upgrade-Insecure-Requests
    
    # Métadonnées
    created_at: datetime               # Date de création
    updated_at: datetime               # Dernière mise à jour
    is_active: bool                    # Configuration active
    version: str                       # Version de la configuration
```

### Relationships
- **One-to-Many** avec `HeaderProfile` : Une configuration peut générer plusieurs profils
- **One-to-Many** avec `StealthIdentity` : Une configuration peut être utilisée par plusieurs identités

### Business Rules
- Une seule configuration peut être active à la fois
- Les modifications de configuration doivent être validées avant activation
- Les pools de headers doivent contenir au moins 5 éléments chacun
- Les seuils de performance doivent être réalistes et atteignables

---

## Data Model Relationships

```
HeaderConfiguration (1) ──→ (Many) HeaderProfile
HeaderProfile (1) ──→ (Many) HeaderRotation
HeaderRotation (1) ──→ (1) StealthIdentity
StealthIdentity (1) ──→ (Many) HeaderValidation
HeaderValidation (1) ──→ (1) HeaderProfile [suggested]
```

## Business Logic Summary

### Header Profile Management
- Les profils sont créés à partir des pools de configuration
- Chaque profil a un taux de succès qui influence sa sélection
- Les profils inactifs ou à faible taux de succès sont mis en quarantaine

### Rotation Strategy
- La rotation suit des patterns de comportement humain
- Le timing inclut du jitter pour éviter les patterns prévisibles
- Les rotations d'urgence sont déclenchées par les validations critiques

### Identity Management
- Chaque worker a une identité unique avec son propre profil
- Les identités sont isolées pour éviter la corrélation
- Le succès d'une identité influence la sélection des profils futurs

### Validation and Adaptation
- Chaque requête génère une validation automatique
- Les validations critiques déclenchent des actions d'adaptation
- Le système apprend des patterns de succès et d'échec

---

*Data model completed on 2025-09-19*


