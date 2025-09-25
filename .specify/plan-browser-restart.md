# Plan d'implémentation - Solution 4 (Browser Restart)

## 🎯 Objectif
Implémenter la **Solution 4 (Browser Restart)** pour gérer la fermeture complète du navigateur Playwright, identifiée comme cause principale des échecs du MVP V2.

## 🔍 Problème identifié
- **Erreur**: `browser.newContext: Target page, context or browser has been closed`
- **Impact**: 46.2% d'échecs après ~7 boutiques traitées
- **Cause**: Le navigateur Playwright se ferme complètement, rendant impossible la recréation de contextes

## 📋 Plan d'implémentation

### Étape 1: Créer MVPBrowserManager
- **Fichier**: `src/mvp/mvp-browser-manager.js`
- **Responsabilités**:
  - Détecter la fermeture du navigateur
  - Redémarrer automatiquement le navigateur Playwright
  - Recréer le contexte et la page
  - Relogger automatiquement
  - Gérer les états de récupération

### Étape 2: Intégrer dans MVPRetryHandler
- **Modifier**: `src/mvp/mvp-retry-handler.js`
- **Ajouts**:
  - Détection des erreurs de browser fermé
  - Intégration de `MVPBrowserManager`
  - Orchestration avec les solutions existantes

### Étape 3: Mettre à jour MVPScraper
- **Modifier**: `src/mvp/mvp-scraper.js`
- **Ajouts**:
  - Initialisation de `MVPBrowserManager`
  - Intégration dans le workflow principal

### Étape 4: Tests et validation
- **Tester**: Le redémarrage automatique
- **Valider**: La continuité du scraping après redémarrage
- **Mesurer**: L'amélioration du taux de succès

## 🔧 Détails techniques

### Détection de fermeture
```javascript
detectBrowserClosed(error) {
  const browserClosedMessages = [
    'Target page, context or browser has been closed',
    'browser.newContext: Target page, context or browser has been closed',
    'Browser has been closed'
  ];
  return browserClosedMessages.some(msg => error.message.includes(msg));
}
```

### Redémarrage automatique
```javascript
async restartBrowser() {
  console.log('🔄 Browser fermé détecté, redémarrage...');
  
  // Fermer le navigateur existant si possible
  if (this.browser) {
    try { await this.browser.close(); } catch (e) {}
  }
  
  // Redémarrer le navigateur
  this.browser = await playwright.chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  // Recréer le contexte et la page
  await this.recreateContext();
  
  // Relogger
  await this.relogin();
  
  console.log('✅ Browser redémarré avec succès');
}
```

## 📊 Critères de succès
- **Taux de succès**: ≥90% (vs 53.8% actuel)
- **Continuité**: Aucune interruption après redémarrage
- **Performance**: Temps de récupération <30 secondes
- **Stabilité**: Gestion robuste des erreurs de redémarrage

## 🚀 Ordre d'implémentation
1. Créer `MVPBrowserManager`
2. Intégrer dans `MVPRetryHandler`
3. Mettre à jour `MVPScraper`
4. Tester et valider
5. Mettre à jour la documentation
