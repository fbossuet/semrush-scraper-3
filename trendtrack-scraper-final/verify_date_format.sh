#!/bin/bash

# Script de vérification du format des dates
# Date: $(date)

echo "🔍 Vérification du format des dates"
echo "==================================="

# Variables
DB_PATH="/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"

echo "📊 État actuel des formats de dates:"
echo "-----------------------------------"

sqlite3 "$DB_PATH" << 'EOF'
.headers on
.mode column

-- Vérifier les formats de creation_date
SELECT 
    'creation_date' as field_name,
    CASE 
        WHEN creation_date IS NULL THEN 'NULL'
        WHEN length(creation_date) = 10 THEN 'DATE ONLY (YYYY-MM-DD)'
        WHEN length(creation_date) = 19 THEN 'DATETIME (YYYY-MM-DD HH:MM:SS)'
        WHEN creation_date LIKE '%.%' THEN 'WITH MICROSECONDS'
        ELSE 'OTHER FORMAT'
    END as format_type,
    COUNT(*) as count
FROM shops 
GROUP BY 
    CASE 
        WHEN creation_date IS NULL THEN 'NULL'
        WHEN length(creation_date) = 10 THEN 'DATE ONLY (YYYY-MM-DD)'
        WHEN length(creation_date) = 19 THEN 'DATETIME (YYYY-MM-DD HH:MM:SS)'
        WHEN creation_date LIKE '%.%' THEN 'WITH MICROSECONDS'
        ELSE 'OTHER FORMAT'
    END

UNION ALL

-- Vérifier les formats de scraping_last_update
SELECT 
    'scraping_last_update' as field_name,
    CASE 
        WHEN scraping_last_update IS NULL THEN 'NULL'
        WHEN length(scraping_last_update) = 10 THEN 'DATE ONLY (YYYY-MM-DD)'
        WHEN length(scraping_last_update) = 19 THEN 'DATETIME (YYYY-MM-DD HH:MM:SS)'
        WHEN scraping_last_update LIKE '%.%' THEN 'WITH MICROSECONDS'
        ELSE 'OTHER FORMAT'
    END as format_type,
    COUNT(*) as count
FROM shops 
GROUP BY 
    CASE 
        WHEN scraping_last_update IS NULL THEN 'NULL'
        WHEN length(scraping_last_update) = 10 THEN 'DATE ONLY (YYYY-MM-DD)'
        WHEN length(scraping_last_update) = 19 THEN 'DATETIME (YYYY-MM-DD HH:MM:SS)'
        WHEN scraping_last_update LIKE '%.%' THEN 'WITH MICROSECONDS'
        ELSE 'OTHER FORMAT'
    END

ORDER BY field_name, format_type;
EOF

echo ""
echo "📋 Exemples de dates actuelles:"
echo "-------------------------------"
sqlite3 "$DB_PATH" "SELECT shop_name, creation_date, scraping_last_update FROM shops LIMIT 5;"

echo ""
echo "🎯 Format cible: 2025-08-12 09:03:57"
echo "✅ Vérification terminée!"
