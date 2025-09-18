#!/bin/bash

# Script de vérification du nettoyage de la base de données
# Date: $(date)

echo "🔍 Vérification du nettoyage de la base de données"
echo "=================================================="

# Variables
DB_PATH="/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"

echo "📊 État actuel des tables:"
echo "-------------------------"

sqlite3 "$DB_PATH" << 'EOF'
.headers on
.mode column

SELECT 
    'shops' as table_name, 
    COUNT(*) as row_count,
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END as status
FROM shops

UNION ALL

SELECT 
    'analytics', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM analytics

UNION ALL

SELECT 
    'scraping_sessions', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM scraping_sessions

UNION ALL

SELECT 
    'scraping_results', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM scraping_results

UNION ALL

SELECT 
    'scraping_errors', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM scraping_errors

UNION ALL

SELECT 
    'selector_performance', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM selector_performance

UNION ALL

SELECT 
    'processing_locks', 
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ VIDE' ELSE '❌ NON VIDE' END
FROM processing_locks

ORDER BY table_name;
EOF

echo ""
echo "🎯 Résumé:"
echo "----------"

TOTAL_ROWS=$(sqlite3 "$DB_PATH" "SELECT SUM(count) FROM (
    SELECT COUNT(*) as count FROM shops
    UNION ALL SELECT COUNT(*) FROM analytics
    UNION ALL SELECT COUNT(*) FROM scraping_sessions
    UNION ALL SELECT COUNT(*) FROM scraping_results
    UNION ALL SELECT COUNT(*) FROM scraping_errors
    UNION ALL SELECT COUNT(*) FROM selector_performance
    UNION ALL SELECT COUNT(*) FROM processing_locks
);")

if [ "$TOTAL_ROWS" -eq 0 ]; then
    echo "✅ Base de données complètement nettoyée!"
    echo "🎉 Prête pour un nouveau cycle de scraping"
else
    echo "❌ Il reste encore $TOTAL_ROWS lignes dans la base"
    echo "⚠️  Le nettoyage n'est pas complet"
fi

echo ""
echo "📁 Sauvegardes disponibles:"
ls -la /home/ubuntu/trendtrack-scraper-final/data/backups/ 2>/dev/null || echo "Aucune sauvegarde trouvée"
