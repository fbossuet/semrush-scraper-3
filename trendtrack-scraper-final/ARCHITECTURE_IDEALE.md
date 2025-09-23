# ARCHITECTURE IDÉALE - TRENDTRACK SCRAPER

## 🎯 Vision d'Architecture

### Principe Fondamental
**Séparation claire des responsabilités** avec une architecture modulaire, résiliente et maintenable.

### Objectifs Architecturaux
1. **Fiabilité** : 99%+ de succès sur les extractions
2. **Performance** : Traitement parallèle optimisé
3. **Maintenabilité** : Code modulaire et testable
4. **Observabilité** : Monitoring et logging complets
5. **Résilience** : Gestion d'erreurs et récupération automatique

---

## 🏗️ Architecture Générale

### Vue d'Ensemble
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ORCHESTRATEUR │────│   EXTRACTEURS   │────│   STOCKAGE      │
│                 │    │                 │    │                 │
│ • Planification │    │ • Phase 1       │    │ • Base SQLite   │
│ • Coordination  │    │ • Phase 2       │    │ • Cache Redis   │
│ • Monitoring    │    │ • Phase 3       │    │ • Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   INFRASTRUCTURE │
                    │                 │
                    │ • Playwright    │
                    │ • VPN Rotation  │
                    │ • Rate Limiting │
                    └─────────────────┘
```

---

## 🔧 Composants Principaux

### 1. ORCHESTRATEUR PRINCIPAL
**Responsabilité** : Coordination globale du processus de scraping

```typescript
class ScrapingOrchestrator {
  // Planification intelligente
  async planExecution(): Promise<ExecutionPlan>
  
  // Coordination des phases
  async executePhase(phase: Phase): Promise<PhaseResult>
  
  // Monitoring en temps réel
  async monitorProgress(): Promise<ProgressReport>
  
  // Gestion d'erreurs globale
  async handleGlobalError(error: Error): Promise<RecoveryAction>
}
```

**Fonctionnalités clés** :
- Planification intelligente basée sur l'état de la base
- Coordination des phases avec dépendances
- Monitoring en temps réel avec métriques
- Gestion d'erreurs et récupération automatique

### 2. EXTRACTEURS SPÉCIALISÉS
**Responsabilité** : Extraction de données selon les spécifications

#### Phase 1 : Extracteur de Liste
```typescript
class ListExtractor {
  // Extraction des données de base
  async extractShopList(page: Page): Promise<ShopData[]>
  
  // Extraction des UUIDs depuis tr#id
  async extractExternalIds(rows: ElementHandle[]): Promise<string[]>
  
  // Validation des données extraites
  async validateExtractedData(data: ShopData[]): Promise<ValidationResult>
}
```

#### Phase 2 : Extracteur de Détails
```typescript
class DetailExtractor {
  // Navigation vers page de détail
  async navigateToDetail(shopId: string): Promise<boolean>
  
  // Extraction des métriques live_ads
  async extractLiveAdsMetrics(): Promise<LiveAdsData>
  
  // Extraction des données géographiques
  async extractGeoData(): Promise<GeoData>
  
  // Extraction des pixels de tracking
  async extractPixels(): Promise<PixelData>
}
```

### 3. GESTIONNAIRE DE CONTEXTE
**Responsabilité** : Gestion robuste des contextes Playwright

```typescript
class ContextManager {
  // Création de contexte isolé
  async createIsolatedContext(): Promise<BrowserContext>
  
  // Rotation automatique des contextes
  async rotateContext(): Promise<BrowserContext>
  
  // Détection de fermeture de contexte
  async detectContextClosure(): Promise<boolean>
  
  // Récupération automatique
  async recoverFromClosure(): Promise<BrowserContext>
}
```

**Stratégies de gestion** :
- **Isolation** : Un contexte par boutique en Phase 3
- **Rotation** : Nouveau contexte toutes les N boutiques
- **Détection** : Monitoring proactif de l'état du contexte
- **Récupération** : Redémarrage automatique en cas de fermeture

### 4. STOCKAGE INTELLIGENT
**Responsabilité** : Gestion optimisée des données

```typescript
class DataManager {
  // Sauvegarde atomique
  async saveAtomic(phase: Phase, data: any): Promise<void>
  
  // Mise à jour incrémentale
  async updateIncremental(shopId: string, updates: Partial<ShopData>): Promise<void>
  
  // Gestion des états
  async updateShopStatus(shopId: string, status: ShopStatus): Promise<void>
  
  // Requêtes optimisées
  async getShopsForPhase(phase: Phase): Promise<ShopData[]>
}
```

### 5. MONITORING ET OBSERVABILITÉ
**Responsabilité** : Surveillance et diagnostic

```typescript
class MonitoringSystem {
  // Métriques en temps réel
  async collectMetrics(): Promise<SystemMetrics>
  
  // Alertes automatiques
  async checkAlerts(): Promise<Alert[]>
  
  // Logs structurés
  async logStructured(event: LogEvent): Promise<void>
  
  // Dashboard de santé
  async getHealthStatus(): Promise<HealthReport>
}
```

---

## 🔄 Workflow Détaillé - Ensemble des Phases

### Vue d'Ensemble du Workflow
```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW COMPLET TRENDTRACK                 │
└─────────────────────────────────────────────────────────────────┘

INITIALISATION
    ↓
PHASE 1: EXTRACTION LISTE (Robuste)
    ↓
PHASE 2: SAUVEGARDE & PRÉPARATION (Atomique)
    ↓
PHASE 3: EXTRACTION DÉTAILS (Résiliente)
    ↓
FINALISATION & RAPPORT
```

### 🔧 Workflow Détaillé par Phase

#### **INITIALISATION**
```typescript
async initializeScraping(): Promise<InitializationResult> {
  // 1. Vérification de l'environnement
  await this.environmentValidator.validate();
  
  // 2. Initialisation des composants
  const contextManager = new ContextManager();
  const dataManager = new DataManager();
  const monitoringSystem = new MonitoringSystem();
  
  // 3. Connexion à TrendTrack
  const authResult = await this.authenticateWithTrendTrack();
  if (!authResult.success) {
    throw new Error('Échec de l\'authentification');
  }
  
  // 4. Vérification de l'état de la base
  const dbState = await dataManager.getDatabaseState();
  
  // 5. Planification de l'exécution
  const executionPlan = await this.planExecution(dbState);
  
  return {
    success: true,
    executionPlan,
    components: { contextManager, dataManager, monitoringSystem }
  };
}
```

**Étapes détaillées :**
1. **Validation environnement** : Vérification des dépendances, VPN, etc.
2. **Initialisation composants** : Création des gestionnaires
3. **Authentification** : Connexion sécurisée à TrendTrack
4. **État de la base** : Analyse des données existantes
5. **Planification** : Détermination des phases à exécuter

---

#### **PHASE 1: EXTRACTION LISTE (Robuste)**
```typescript
async executePhase1(): Promise<Phase1Result> {
  const startTime = Date.now();
  const metrics = new Phase1Metrics();
  
  try {
    // 1. Création du contexte isolé
    const context = await this.contextManager.createIsolatedContext();
    const page = await context.newPage();
    
    // 2. Navigation avec retry intelligent
    const navigationResult = await this.navigateWithRetry(page, {
      url: '/trending-shops',
      retries: 3,
      backoff: 'exponential'
    });
    
    if (!navigationResult.success) {
      throw new Error('Échec de navigation après 3 tentatives');
    }
    
    // 3. Attente du chargement du tableau
    await this.waitForTableLoad(page);
    
    // 4. Extraction des données de base
    const rawShops = await this.listExtractor.extractShopList(page);
    metrics.shopsExtracted = rawShops.length;
    
    // 5. Extraction des UUIDs depuis tr#id
    const shopsWithIds = await this.listExtractor.extractExternalIds(rawShops);
    metrics.shopsWithIds = shopsWithIds.length;
    
    // 6. Validation des données extraites
    const validationResult = await this.listExtractor.validateExtractedData(shopsWithIds);
    metrics.validShops = validationResult.valid.length;
    metrics.invalidShops = validationResult.invalid.length;
    
    // 7. Sauvegarde atomique
    await this.dataManager.saveAtomic('phase1', validationResult.valid);
    
    // 8. Mise à jour des métriques
    metrics.duration = Date.now() - startTime;
    metrics.success = true;
    
    return {
      success: true,
      metrics,
      shops: validationResult.valid
    };
    
  } catch (error) {
    metrics.duration = Date.now() - startTime;
    metrics.success = false;
    metrics.error = error.message;
    
    await this.errorHandler.handlePhase1Error(error, metrics);
    throw error;
  } finally {
    await context.close();
  }
}
```

**Étapes détaillées :**
1. **Contexte isolé** : Création d'un contexte dédié à Phase 1
2. **Navigation robuste** : Retry avec backoff exponentiel
3. **Chargement tableau** : Attente intelligente du DOM
4. **Extraction données** : Récupération des informations de base
5. **Extraction UUIDs** : Récupération depuis `tr#id` selon specs
6. **Validation** : Vérification de la qualité des données
7. **Sauvegarde atomique** : Transaction sécurisée
8. **Métriques** : Collecte des indicateurs de performance

---

#### **PHASE 2: SAUVEGARDE & PRÉPARATION (Atomique)**
```typescript
async executePhase2(): Promise<Phase2Result> {
  const startTime = Date.now();
  const metrics = new Phase2Metrics();
  
  try {
    // 1. Récupération des données Phase 1
    const phase1Shops = await this.dataManager.getShopsForPhase('phase1');
    metrics.shopsToProcess = phase1Shops.length;
    
    // 2. Traitement par batch avec transaction
    await this.dataManager.transaction(async (tx) => {
      for (const shop of phase1Shops) {
        // 3. Mise à jour du statut
        await tx.updateShopStatus(shop.id, 'table_extracted');
        
        // 4. Préparation pour Phase 3
        await tx.prepareForPhase3(shop);
        
        // 5. Validation des prérequis
        if (!shop.external_id) {
          await tx.markShopForReprocessing(shop.id, 'missing_external_id');
          metrics.skippedShops++;
        } else {
          metrics.preparedShops++;
        }
      }
    });
    
    // 6. Vérification de l'intégrité
    const integrityCheck = await this.dataManager.verifyPhase2Integrity();
    if (!integrityCheck.valid) {
      throw new Error(`Intégrité Phase 2 compromise: ${integrityCheck.errors.join(', ')}`);
    }
    
    // 7. Mise à jour des métriques
    metrics.duration = Date.now() - startTime;
    metrics.success = true;
    
    return {
      success: true,
      metrics,
      preparedShops: metrics.preparedShops,
      skippedShops: metrics.skippedShops
    };
    
  } catch (error) {
    metrics.duration = Date.now() - startTime;
    metrics.success = false;
    metrics.error = error.message;
    
    await this.errorHandler.handlePhase2Error(error, metrics);
    throw error;
  }
}
```

**Étapes détaillées :**
1. **Récupération données** : Lecture des résultats Phase 1
2. **Transaction atomique** : Traitement sécurisé par batch
3. **Mise à jour statut** : Passage à `table_extracted`
4. **Préparation Phase 3** : Configuration pour extraction détails
5. **Validation prérequis** : Vérification des UUIDs
6. **Vérification intégrité** : Contrôle de cohérence
7. **Métriques** : Suivi des performances

---

#### **PHASE 3: EXTRACTION DÉTAILS (Résiliente)**
```typescript
async executePhase3(): Promise<Phase3Result> {
  const startTime = Date.now();
  const metrics = new Phase3Metrics();
  
  try {
    // 1. Récupération des boutiques à traiter
    const shopsToProcess = await this.dataManager.getShopsForPhase('phase3');
    metrics.totalShops = shopsToProcess.length;
    
    // 2. Configuration du traitement parallèle
    const batchSize = this.calculateOptimalBatchSize(shopsToProcess.length);
    const batches = this.createBatches(shopsToProcess, batchSize);
    
    // 3. Traitement par batch avec isolation
    for (const [batchIndex, batch] of batches.entries()) {
      const batchResult = await this.processBatch(batch, batchIndex + 1, batches.length);
      
      // 4. Mise à jour des métriques
      metrics.successfulShops += batchResult.success;
      metrics.failedShops += batchResult.failed;
      metrics.errors.push(...batchResult.errors);
      
      // 5. Pause entre batches
      if (batchIndex < batches.length - 1) {
        await this.rateLimiter.waitBetweenBatches();
      }
    }
    
    // 6. Calcul des métriques finales
    metrics.duration = Date.now() - startTime;
    metrics.successRate = (metrics.successfulShops / metrics.totalShops) * 100;
    metrics.success = metrics.successRate >= 95; // Seuil de succès
    
    return {
      success: metrics.success,
      metrics,
      summary: {
        total: metrics.totalShops,
        successful: metrics.successfulShops,
        failed: metrics.failedShops,
        successRate: metrics.successRate
      }
    };
    
  } catch (error) {
    metrics.duration = Date.now() - startTime;
    metrics.success = false;
    metrics.error = error.message;
    
    await this.errorHandler.handlePhase3Error(error, metrics);
    throw error;
  }
}

async processBatch(batch: ShopData[], batchIndex: number, totalBatches: number): Promise<BatchResult> {
  const batchResult = { success: 0, failed: 0, errors: [] };
  
  // Traitement parallèle avec isolation des contextes
  await Promise.allSettled(
    batch.map(async (shop) => {
      const context = await this.contextManager.createIsolatedContext();
      
      try {
        // 1. Navigation vers page de détail
        const navSuccess = await this.detailExtractor.navigateToDetail(shop.external_id);
        if (!navSuccess) {
          throw new Error('Échec de navigation vers page de détail');
        }
        
        // 2. Extraction des métriques live_ads
        const liveAdsData = await this.detailExtractor.extractLiveAdsMetrics();
        
        // 3. Extraction des données géographiques
        const geoData = await this.detailExtractor.extractGeoData();
        
        // 4. Extraction des pixels de tracking
        const pixelData = await this.detailExtractor.extractPixels();
        
        // 5. Compilation des données
        const detailData = {
          ...liveAdsData,
          ...geoData,
          ...pixelData,
          last_updated: new Date().toISOString()
        };
        
        // 6. Sauvegarde incrémentale
        await this.dataManager.updateIncremental(shop.id, detailData);
        await this.dataManager.updateShopStatus(shop.id, 'details_extracted');
        
        batchResult.success++;
        
      } catch (error) {
        batchResult.failed++;
        batchResult.errors.push({
          shopId: shop.id,
          shopName: shop.shopName,
          error: error.message,
          timestamp: new Date().toISOString()
        });
        
        await this.dataManager.updateShopStatus(shop.id, 'phase3_failed');
        
      } finally {
        await context.close();
      }
    })
  );
  
  return batchResult;
}
```

**Étapes détaillées :**
1. **Récupération boutiques** : Lecture des boutiques préparées
2. **Configuration parallèle** : Calcul de la taille optimale des batches
3. **Traitement par batch** : Isolation des contextes par boutique
4. **Navigation détail** : Accès aux pages individuelles
5. **Extraction métriques** : Récupération selon les specs
6. **Sauvegarde incrémentale** : Mise à jour des données
7. **Gestion d'erreurs** : Traitement des échecs individuels
8. **Métriques** : Suivi détaillé des performances

---

#### **FINALISATION & RAPPORT**
```typescript
async finalizeScraping(): Promise<FinalizationResult> {
  const startTime = Date.now();
  
  try {
    // 1. Collecte des métriques finales
    const finalMetrics = await this.monitoringSystem.collectFinalMetrics();
    
    // 2. Génération du rapport
    const report = await this.generateReport(finalMetrics);
    
    // 3. Vérification de l'intégrité finale
    const integrityCheck = await this.dataManager.verifyFinalIntegrity();
    
    // 4. Nettoyage des ressources
    await this.cleanupResources();
    
    // 5. Notification des résultats
    await this.notificationSystem.sendCompletionNotification(report);
    
    return {
      success: true,
      report,
      metrics: finalMetrics,
      integrity: integrityCheck
    };
    
  } catch (error) {
    await this.errorHandler.handleFinalizationError(error);
    throw error;
  }
}
```

**Étapes détaillées :**
1. **Métriques finales** : Collecte des indicateurs complets
2. **Génération rapport** : Création du rapport détaillé
3. **Vérification intégrité** : Contrôle final de cohérence
4. **Nettoyage ressources** : Libération des ressources
5. **Notification** : Envoi des résultats

---

## 🔄 Workflow Optimisé

### Phase 1 : Extraction de Liste (Robuste)
```typescript
async executePhase1(): Promise<Phase1Result> {
  const context = await this.contextManager.createIsolatedContext();
  const page = await context.newPage();
  
  try {
    // Navigation avec retry intelligent
    await this.navigateWithRetry(page, '/trending-shops');
    
    // Extraction avec validation
    const shops = await this.listExtractor.extractShopList(page);
    const validatedShops = await this.listExtractor.validateExtractedData(shops);
    
    // Sauvegarde atomique
    await this.dataManager.saveAtomic('phase1', validatedShops);
    
    return { success: true, count: validatedShops.length };
  } finally {
    await context.close();
  }
}
```

### Phase 2 : Sauvegarde et Préparation (Atomique)
```typescript
async executePhase2(): Promise<Phase2Result> {
  const shops = await this.dataManager.getShopsForPhase('phase1');
  
  // Traitement par batch avec transaction
  await this.dataManager.transaction(async (tx) => {
    for (const shop of shops) {
      await tx.updateShopStatus(shop.id, 'table_extracted');
      await tx.prepareForPhase3(shop);
    }
  });
  
  return { success: true, prepared: shops.length };
}
```

### Phase 3 : Extraction de Détails (Résiliente)
```typescript
async executePhase3(): Promise<Phase3Result> {
  const shops = await this.dataManager.getShopsForPhase('phase3');
  const results = { success: 0, failed: 0, errors: [] };
  
  // Traitement parallèle avec isolation
  await Promise.allSettled(
    shops.map(async (shop) => {
      const context = await this.contextManager.createIsolatedContext();
      
      try {
        const detailData = await this.extractShopDetails(shop, context);
        await this.dataManager.updateIncremental(shop.id, detailData);
        results.success++;
      } catch (error) {
        results.failed++;
        results.errors.push({ shop: shop.id, error: error.message });
        await this.dataManager.updateShopStatus(shop.id, 'phase3_failed');
      } finally {
        await context.close();
      }
    })
  );
  
  return results;
}
```

---

## 🛡️ Stratégies de Résilience

### 1. Gestion des Erreurs
```typescript
class ErrorHandler {
  // Classification des erreurs
  classifyError(error: Error): ErrorType
  
  // Stratégies de récupération
  async recover(error: Error, context: ExecutionContext): Promise<RecoveryAction>
  
  // Escalade automatique
  async escalate(error: Error): Promise<void>
}
```

**Types d'erreurs gérées** :
- **Erreurs de contexte** : Redémarrage automatique
- **Erreurs de navigation** : Retry avec backoff
- **Erreurs de données** : Validation et correction
- **Erreurs système** : Escalade et notification

### 2. Rate Limiting Intelligent
```typescript
class RateLimiter {
  // Limitation adaptative
  async waitIfNeeded(): Promise<void>
  
  // Détection de blocage
  async detectBlocking(): Promise<boolean>
  
  // Rotation automatique
  async rotateIdentity(): Promise<void>
}
```

### 3. Monitoring Proactif
```typescript
class ProactiveMonitor {
  // Détection précoce de problèmes
  async detectAnomalies(): Promise<Anomaly[]>
  
  // Actions préventives
  async takePreventiveAction(anomaly: Anomaly): Promise<void>
  
  // Optimisation continue
  async optimizePerformance(): Promise<OptimizationResult>
}
```

---

## 📊 Métriques et KPIs

### Métriques de Performance
- **Taux de succès par phase** : >99% Phase 1, >95% Phase 3
- **Temps d'exécution** : <2min Phase 1, <5min Phase 3
- **Utilisation des ressources** : <80% CPU, <70% RAM

### Métriques de Qualité
- **Complétude des données** : >98% des champs requis
- **Précision des extractions** : >99% des données correctes
- **Cohérence des données** : 100% des validations passées

### Métriques de Fiabilité
- **Disponibilité** : >99.5% uptime
- **Récupération d'erreurs** : <30s temps de récupération
- **Détection d'anomalies** : <5min temps de détection

---

## 🔧 Implémentation Progressive

### Phase 1 : Fondations (Semaine 1)
- [ ] Architecture de base avec orchestrateur
- [ ] Extracteur Phase 1 robuste
- [ ] Gestionnaire de contexte simple
- [ ] Stockage atomique

### Phase 2 : Résilience (Semaine 2)
- [ ] Gestion d'erreurs avancée
- [ ] Monitoring et alertes
- [ ] Rate limiting intelligent
- [ ] Tests de charge

### Phase 3 : Optimisation (Semaine 3)
- [ ] Traitement parallèle optimisé
- [ ] Cache intelligent
- [ ] Optimisations de performance
- [ ] Dashboard de monitoring

### Phase 4 : Production (Semaine 4)
- [ ] Déploiement en production
- [ ] Monitoring en temps réel
- [ ] Optimisations continues
- [ ] Documentation complète

---

## 🎯 Avantages de cette Architecture

### 1. **Fiabilité Maximale**
- Isolation des contextes élimine les fermetures en cascade
- Gestion d'erreurs granulaire avec récupération automatique
- Monitoring proactif pour détecter les problèmes avant qu'ils n'impactent

### 2. **Performance Optimale**
- Traitement parallèle avec isolation
- Cache intelligent pour éviter les re-extractions
- Rate limiting adaptatif

### 3. **Maintenabilité**
- Code modulaire et testable
- Séparation claire des responsabilités
- Documentation et monitoring complets

### 4. **Observabilité**
- Métriques en temps réel
- Logs structurés
- Dashboard de santé

### 5. **Évolutivité**
- Architecture modulaire pour ajouter de nouvelles phases
- Gestionnaire de contexte extensible
- Monitoring adaptable

---

## 🚀 Migration depuis l'Architecture Actuelle

### Étapes de Migration
1. **Préparation** : Créer les nouvelles classes de base
2. **Migration Phase 1** : Remplacer l'extracteur de liste
3. **Migration Phase 2** : Implémenter le stockage atomique
4. **Migration Phase 3** : Remplacer l'extracteur de détails
5. **Optimisation** : Ajouter le monitoring et les optimisations

### Stratégie de Déploiement
- **Blue-Green** : Déploiement parallèle avec basculement
- **Canary** : Déploiement progressif avec monitoring
- **Rollback** : Retour rapide en cas de problème

Cette architecture idéale résout tous les problèmes identifiés dans l'analyse actuelle tout en offrant une base solide pour l'évolution future du système.
