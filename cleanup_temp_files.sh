#!/bin/bash
# Script de nettoyage des fichiers temporaires - ENVIRONNEMENT TEST
# Tâche P3 : Nettoyer les fichiers temporaires de test, d'analyse, d'audit

echo "🧹 NETTOYAGE DES FICHIERS TEMPORAIRES - ENVIRONNEMENT TEST"
echo "=========================================================="
echo "📅 Date: $(date)"
echo "📁 Répertoire: $(pwd)"
echo ""

# Créer un dossier de sauvegarde pour les fichiers importants
BACKUP_DIR="backup_cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Dossier de sauvegarde créé: $BACKUP_DIR"

# Fonction pour sauvegarder un fichier avant suppression
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local dir=$(dirname "$file")
        local name=$(basename "$file")
        mkdir -p "$BACKUP_DIR/$dir"
        cp "$file" "$BACKUP_DIR/$file"
        echo "💾 Sauvegardé: $file"
    fi
}

# Fonction pour supprimer un fichier
remove_file() {
    local file="$1"
    if [ -f "$file" ]; then
        rm "$file"
        echo "🗑️ Supprimé: $file"
    fi
}

echo ""
echo "🔍 PHASE 1: SAUVEGARDE DES FICHIERS IMPORTANTS"
echo "=============================================="

# Sauvegarder les fichiers de test importants
backup_file "test_incremental_saving.js"
backup_file "audit_api_endpoint.py"

# Sauvegarder les fichiers de configuration de test
backup_file "specs/001-name-trendtrack-scraper/plan/test_schema.sql"

echo ""
echo "🗑️ PHASE 2: SUPPRESSION DES FICHIERS TEMPORAIRES"
echo "================================================"

# 1. Supprimer les logs anciens (garder seulement les 5 plus récents)
echo "📋 Nettoyage des logs..."
cd logs
if [ -d "logs" ]; then
    # Garder seulement les 5 logs les plus récents
    ls -t *.log 2>/dev/null | tail -n +6 | while read logfile; do
        remove_file "logs/$logfile"
    done
fi
cd ..

# 2. Supprimer les fichiers de backup
echo "📋 Nettoyage des fichiers de backup..."
find . -name "*.backup" -type f | while read file; do
    remove_file "$file"
done

find . -name "*.bak" -type f | while read file; do
    remove_file "$file"
done

# 3. Supprimer les fichiers de test temporaires
echo "📋 Nettoyage des fichiers de test temporaires..."
find . -name "*_test_*" -type f | while read file; do
    remove_file "$file"
done

find . -name "test_*" -type f | grep -v "test_schema.sql" | while read file; do
    remove_file "$file"
done

# 4. Supprimer les fichiers de debug
echo "📋 Nettoyage des fichiers de debug..."
find . -name "*debug*" -type f | while read file; do
    remove_file "$file"
done

find . -name "*_debug_*" -type f | while read file; do
    remove_file "$file"
done

# 5. Supprimer les fichiers d'audit temporaires
echo "📋 Nettoyage des fichiers d'audit temporaires..."
find . -name "*audit*" -type f | grep -v "audit_api_endpoint.py" | while read file; do
    remove_file "$file"
done

# 6. Supprimer les fichiers temporaires de session
echo "📋 Nettoyage des fichiers de session..."
if [ -d "session-profile-shared" ]; then
    rm -rf session-profile-shared
    echo "🗑️ Supprimé: session-profile-shared/"
fi

# 7. Nettoyer les logs du scraper TrendTrack
echo "📋 Nettoyage des logs TrendTrack..."
if [ -d "trendtrack-scraper-final/logs" ]; then
    cd trendtrack-scraper-final/logs
    # Garder seulement les 3 logs les plus récents
    ls -t *.log 2>/dev/null | tail -n +4 | while read logfile; do
        remove_file "trendtrack-scraper-final/logs/$logfile"
    done
    cd ../..
fi

# 8. Supprimer les bases de données de test temporaires
echo "📋 Nettoyage des bases de données de test..."
if [ -f "trendtrack-scraper-final/data/trendtrack_test.db" ]; then
    backup_file "trendtrack-scraper-final/data/trendtrack_test.db"
    remove_file "trendtrack-scraper-final/data/trendtrack_test.db"
fi

# 9. Supprimer les fichiers d'export debug
echo "📋 Nettoyage des fichiers d'export debug..."
find . -name "export-debug.json" -type f | while read file; do
    remove_file "$file"
done

find . -name "*export*debug*" -type f | while read file; do
    remove_file "$file"
done

echo ""
echo "📊 PHASE 3: RÉSUMÉ DU NETTOYAGE"
echo "==============================="

# Compter les fichiers supprimés
BACKUP_COUNT=$(find "$BACKUP_DIR" -type f | wc -l)
echo "💾 Fichiers sauvegardés: $BACKUP_COUNT"
echo "📁 Dossier de sauvegarde: $BACKUP_DIR"

# Vérifier l'espace libéré
echo "💾 Espace disque libéré:"
du -sh "$BACKUP_DIR" 2>/dev/null || echo "Impossible de calculer l'espace libéré"

echo ""
echo "✅ NETTOYAGE TERMINÉ !"
echo "======================"
echo "📋 Les fichiers importants ont été sauvegardés dans: $BACKUP_DIR"
echo "🗑️ Les fichiers temporaires ont été supprimés"
echo "💡 Vous pouvez supprimer le dossier de sauvegarde si tout fonctionne correctement"
echo ""
echo "🔍 Vérification finale:"
echo "Fichiers temporaires restants:"
find . -name "*.log" -o -name "*.tmp" -o -name "*.temp" -o -name "*debug*" -o -name "*test*" -o -name "*audit*" -o -name "*backup*" -o -name "*.bak" | grep -v ".git" | grep -v "node_modules" | wc -l



