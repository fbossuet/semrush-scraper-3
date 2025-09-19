#!/bin/bash
# Script de nettoyage des fichiers de lock
# Date: 2025-09-19
# Description: Supprime tous les fichiers de lock existants dans l'environnement test

echo "🧹 Nettoyage des fichiers de lock dans l'environnement test..."

# Répertoire de travail
WORK_DIR="/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final"

# Aller dans le répertoire de travail
cd "$WORK_DIR" || exit 1

# Supprimer les fichiers de lock
echo "🔍 Recherche des fichiers de lock..."

# Fichiers de lock connus
LOCK_FILES=(
    "trendtrack-db.lock"
    "*.lock"
    "locks/*.lock"
)

# Supprimer les fichiers de lock
for pattern in "${LOCK_FILES[@]}"; do
    if ls $pattern 2>/dev/null; then
        echo "🗑️  Suppression des fichiers: $pattern"
        rm -f $pattern
    else
        echo "✅ Aucun fichier trouvé pour: $pattern"
    fi
done

# Vérifier les processus qui pourraient utiliser la base de données
echo "🔍 Vérification des processus utilisant la base de données..."
if command -v lsof >/dev/null 2>&1; then
    DB_PROCESSES=$(lsof data/trendtrack.db 2>/dev/null || echo "Aucun processus trouvé")
    echo "📊 Processus utilisant la base: $DB_PROCESSES"
else
    echo "⚠️  lsof non disponible, impossible de vérifier les processus"
fi

# Nettoyer les locks SQLite
echo "🔧 Nettoyage des locks SQLite..."
sqlite3 data/trendtrack.db "PRAGMA journal_mode=DELETE; VACUUM;" 2>/dev/null || echo "⚠️  Impossible de nettoyer les locks SQLite"

# Vérifier l'accès à la base
echo "✅ Test d'accès à la base de données..."
if sqlite3 data/trendtrack.db "SELECT COUNT(*) FROM shops;" >/dev/null 2>&1; then
    echo "✅ Base de données accessible"
else
    echo "❌ Problème d'accès à la base de données"
    exit 1
fi

echo "🎉 Nettoyage des locks terminé !"
echo "📋 Résumé:"
echo "  - Fichiers de lock supprimés"
echo "  - Locks SQLite nettoyés"
echo "  - Base de données accessible"
echo ""
echo "💡 Les locks sont maintenant désactivés dans l'environnement test"

