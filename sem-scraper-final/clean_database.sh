#!/bin/bash

echo "🧹 Nettoyage complet de la base de données..."

# Chemin de la base de données
DB_PATH="/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"

# Vérifier que la base existe
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Base de données non trouvée: $DB_PATH"
    exit 1
fi

# Créer une sauvegarde
BACKUP_PATH="/home/ubuntu/trendtrack-scraper-final/data/trendtrack_backup_$(date +%Y%m%d_%H%M%S).db"
echo "💾 Création de la sauvegarde: $BACKUP_PATH"
cp "$DB_PATH" "$BACKUP_PATH"

# Nettoyer toutes les tables
echo "🗑️ Suppression de toutes les données..."

sqlite3 "$DB_PATH" << 'EOF'
-- Supprimer toutes les données des tables
DELETE FROM analytics;
DELETE FROM shops;
DELETE FROM scraping_sessions;
DELETE FROM scraping_results;
DELETE FROM scraping_errors;
DELETE FROM selector_performance;
DELETE FROM processing_locks;

-- Réinitialiser les séquences auto-increment
DELETE FROM sqlite_sequence WHERE name IN ('analytics', 'shops', 'scraping_sessions', 'scraping_results', 'scraping_errors', 'selector_performance', 'processing_locks');

-- Vérifier que les tables sont vides
SELECT 'analytics' as table_name, COUNT(*) as count FROM analytics
UNION ALL
SELECT 'shops' as table_name, COUNT(*) as count FROM shops
UNION ALL
SELECT 'scraping_sessions' as table_name, COUNT(*) as count FROM scraping_sessions
UNION ALL
SELECT 'scraping_results' as table_name, COUNT(*) as count FROM scraping_results
UNION ALL
SELECT 'scraping_errors' as table_name, COUNT(*) as count FROM scraping_errors
UNION ALL
SELECT 'selector_performance' as table_name, COUNT(*) as count FROM selector_performance
UNION ALL
SELECT 'processing_locks' as table_name, COUNT(*) as count FROM processing_locks;
EOF

echo "✅ Nettoyage terminé!"
echo "📊 Base de données vide et prête pour les tests"
