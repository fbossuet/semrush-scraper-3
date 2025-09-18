#!/bin/bash

# Script pour corriger les formats de dates dans SQLite
# Date: $(date)

echo "🗄️  Correction des formats de dates dans SQLite"
echo "==============================================="

# Variables
PROJECT_PATH="/home/ubuntu/trendtrack-scraper-final"
DB_PATH="$PROJECT_PATH/data/trendtrack.db"

echo "📋 Étape 1: Sauvegarde de la base..."
BACKUP_NAME="trendtrack_backup_before_sqlite_date_fix_$(date +%Y%m%d_%H%M%S).db"
cp "$DB_PATH" "$PROJECT_PATH/data/$BACKUP_NAME"
echo "✅ Sauvegarde créée: $BACKUP_NAME"

echo ""
echo "🔍 Étape 2: Vérification du format actuel..."
echo "Format actuel des dates:"
sqlite3 "$DB_PATH" "SELECT creation_date, scraping_last_update FROM shops LIMIT 3;"

echo ""
echo "🛠️  Étape 3: Correction des formats dans SQLite..."

# Correction des formats de dates dans SQLite
sqlite3 "$DB_PATH" << 'EOF'
-- Mise à jour creation_date pour avoir le format YYYY-MM-DD HH:MM:SS
UPDATE shops 
SET creation_date = CASE 
    WHEN creation_date IS NULL THEN datetime('now', 'localtime')
    WHEN length(creation_date) = 10 THEN creation_date || ' 00:00:00'
    WHEN creation_date LIKE '%.%' THEN substr(creation_date, 1, 19)
    WHEN creation_date LIKE '%+%' THEN substr(creation_date, 1, 19)
    ELSE creation_date
END
WHERE creation_date IS NOT NULL;

-- Mise à jour scraping_last_update pour avoir le format YYYY-MM-DD HH:MM:SS
UPDATE shops 
SET scraping_last_update = CASE 
    WHEN scraping_last_update IS NULL THEN NULL
    WHEN scraping_last_update LIKE '%.%' THEN substr(scraping_last_update, 1, 19)
    WHEN scraping_last_update LIKE '%+%' THEN substr(scraping_last_update, 1, 19)
    ELSE scraping_last_update
END
WHERE scraping_last_update IS NOT NULL;

-- Mise à jour updated_at pour avoir le format YYYY-MM-DD HH:MM:SS
UPDATE shops 
SET updated_at = CASE 
    WHEN updated_at IS NULL THEN NULL
    WHEN updated_at LIKE '%.%' THEN substr(updated_at, 1, 19)
    WHEN updated_at LIKE '%+%' THEN substr(updated_at, 1, 19)
    ELSE updated_at
END
WHERE updated_at IS NOT NULL;

-- Mise à jour scraped_at pour avoir le format YYYY-MM-DD HH:MM:SS
UPDATE shops 
SET scraped_at = CASE 
    WHEN scraped_at IS NULL THEN NULL
    WHEN scraped_at LIKE '%.%' THEN substr(scraped_at, 1, 19)
    WHEN scraped_at LIKE '%+%' THEN substr(scraped_at, 1, 19)
    ELSE scraped_at
END
WHERE scraped_at IS NOT NULL;
EOF

echo ""
echo "✅ Étape 4: Vérification du nouveau format..."
echo "Nouveau format des dates:"
sqlite3 "$DB_PATH" "SELECT creation_date, scraping_last_update FROM shops LIMIT 3;"

echo ""
echo "📊 Résumé des modifications:"
echo "---------------------------"
echo "✅ creation_date: Format uniformisé vers YYYY-MM-DD HH:MM:SS"
echo "✅ scraping_last_update: Format uniformisé vers YYYY-MM-DD HH:MM:SS"
echo "✅ updated_at: Format uniformisé vers YYYY-MM-DD HH:MM:SS"
echo "✅ scraped_at: Format uniformisé vers YYYY-MM-DD HH:MM:SS"
echo "💾 Sauvegarde: $BACKUP_NAME"

echo ""
echo "🎯 Format uniformisé: 2025-08-12 09:03:57"
