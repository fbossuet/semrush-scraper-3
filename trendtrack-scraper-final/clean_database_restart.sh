#!/bin/bash

# Script de nettoyage complet de la base de données et redémarrage
# Date: $(date)

echo "🧹 Nettoyage complet de la base de données"
echo "=========================================="

# Variables
DB_PATH="/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
BACKUP_DIR="/home/ubuntu/trendtrack-scraper-final/data/backups"
BACKUP_NAME="trendtrack_backup_before_clean_$(date +%Y%m%d_%H%M%S).db"

# Créer le répertoire de backup s'il n'existe pas
mkdir -p $BACKUP_DIR

echo "📋 Étape 1: Sauvegarde de la base actuelle..."
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/$BACKUP_NAME"
    echo "✅ Sauvegarde créée: $BACKUP_NAME"
else
    echo "⚠️  Base de données non trouvée, pas de sauvegarde nécessaire"
fi

echo ""
echo "🗑️  Étape 2: Suppression de toutes les données..."

# Supprimer toutes les données de toutes les tables
sqlite3 "$DB_PATH" << 'EOF'
-- Supprimer toutes les données des tables principales
DELETE FROM shops;
DELETE FROM analytics;
DELETE FROM scraping_sessions;
DELETE FROM scraping_results;
DELETE FROM scraping_errors;
DELETE FROM selector_performance;
DELETE FROM processing_locks;

-- Réinitialiser les séquences auto-increment
DELETE FROM sqlite_sequence;

-- Vérifier que tout est vide
SELECT 'shops' as table_name, COUNT(*) as row_count FROM shops
UNION ALL
SELECT 'analytics', COUNT(*) FROM analytics
UNION ALL
SELECT 'scraping_sessions', COUNT(*) FROM scraping_sessions
UNION ALL
SELECT 'scraping_results', COUNT(*) FROM scraping_results
UNION ALL
SELECT 'scraping_errors', COUNT(*) FROM scraping_errors
UNION ALL
SELECT 'selector_performance', COUNT(*) FROM selector_performance
UNION ALL
SELECT 'processing_locks', COUNT(*) FROM processing_locks;
EOF

echo ""
echo "🔄 Étape 3: Redémarrage des services..."

# Arrêter les processus de scraping en cours
echo "⏹️  Arrêt des processus de scraping..."
pkill -f "production_scraper.py" || echo "Aucun processus de scraping en cours"

# Attendre un peu
sleep 2

# Redémarrer les services si nécessaire
echo "▶️  Redémarrage des services..."
# Ici vous pouvez ajouter les commandes de redémarrage de vos services

echo ""
echo "✅ Nettoyage terminé!"
echo "📊 Base de données maintenant vide et propre"
echo "💾 Sauvegarde disponible dans: $BACKUP_DIR/$BACKUP_NAME"
echo ""
echo "🎯 Prêt pour un nouveau cycle de scraping!"
