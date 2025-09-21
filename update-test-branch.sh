#!/bin/bash

# Script de mise à jour de la branche test
# Usage: ./update-test-branch.sh

echo "🚀 Mise à jour de la branche test..."

# Vérifier qu'on est dans un dépôt Git
if [ ! -d ".git" ]; then
    echo "❌ Erreur: Ce script doit être exécuté dans un dépôt Git"
    exit 1
fi

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git branch --show-current)
echo "📋 Branche actuelle: $CURRENT_BRANCH"

# Créer une sauvegarde
git branch test-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

# Aller sur la branche test
echo "🔄 Passage à la branche test..."
git checkout test 2>/dev/null || git checkout -b test

# Appliquer le patch si disponible
if [ -f "test-branch-update.patch" ]; then
    echo "📦 Application du patch..."
    git apply test-branch-update.patch
    echo "✅ Patch appliqué"
else
    echo "⚠️  Fichier patch non trouvé"
fi

# Appliquer le bundle si disponible
if [ -f "test-branch-update.bundle" ]; then
    echo "📦 Application du bundle..."
    git fetch test-branch-update.bundle test:test --force
    echo "✅ Bundle appliqué"
else
    echo "⚠️  Fichier bundle non trouvé"
fi

# Vérifier le statut
echo "📊 Statut final:"
git log --oneline -5

echo "✅ Mise à jour terminée!"
echo "📋 Fichiers importants:"
echo "  - rapportdelamort.md"
echo "  - extract-table-working-selectors.js"
echo "  - update-database-parallel-complete.js"
echo "  - ARCHITECTURE_PARALLELE.md"


