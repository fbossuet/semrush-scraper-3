#!/bin/bash

# Script pour corriger le format des dates dans le code source
# Date: $(date)

echo "🔧 Correction du format des dates dans le code source"
echo "===================================================="

# Variables
PROJECT_PATH="/home/ubuntu/trendtrack-scraper-final"
BACKUP_DIR="$PROJECT_PATH/backups_code_$(date +%Y%m%d_%H%M%S)"

echo "📋 Étape 1: Création du backup du code..."
mkdir -p "$BACKUP_DIR"
cp -r "$PROJECT_PATH/src" "$BACKUP_DIR/"
cp -r "$PROJECT_PATH/*.py" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$PROJECT_PATH/*.js" "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup créé: $BACKUP_DIR"

echo ""
echo "🛠️  Étape 2: Correction des fichiers JavaScript..."

# Correction du shop-repository.js
echo "📝 Correction de src/database/shop-repository.js..."
sed -i 's/CURRENT_TIMESTAMP/datetime(\"now\", \"localtime\")/g' "$PROJECT_PATH/src/database/shop-repository.js"

# Correction du schema.js
echo "📝 Correction de src/database/schema.js..."
sed -i 's/DEFAULT CURRENT_TIMESTAMP/DEFAULT (datetime(\"now\", \"localtime\"))/g' "$PROJECT_PATH/src/database/schema.js"

echo ""
echo "🐍 Étape 3: Correction des fichiers Python..."

# Correction du trendtrack_api.py
echo "📝 Correction de trendtrack_api.py..."
sed -i 's/datetime\.now()/datetime.now().strftime("%Y-%m-%d %H:%M:%S")/g' "$PROJECT_PATH/trendtrack_api.py"

# Correction des autres fichiers Python
find "$PROJECT_PATH" -name "*.py" -exec sed -i 's/datetime\.now()/datetime.now().strftime("%Y-%m-%d %H:%M:%S")/g' {} \;

echo ""
echo "📊 Étape 4: Vérification des corrections..."

echo "🔍 Vérification des CURRENT_TIMESTAMP dans shop-repository.js:"
grep -n "CURRENT_TIMESTAMP" "$PROJECT_PATH/src/database/shop-repository.js" || echo "✅ Aucun CURRENT_TIMESTAMP trouvé"

echo ""
echo "🔍 Vérification des datetime.now() dans trendtrack_api.py:"
grep -n "datetime\.now()" "$PROJECT_PATH/trendtrack_api.py" || echo "✅ Aucun datetime.now() trouvé"

echo ""
echo "📋 Étape 5: Création d'un script de test..."

# Créer un script de test pour vérifier le format
cat > "$PROJECT_PATH/test_date_format.js" << 'EOF'
// Script de test pour vérifier le format des dates
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./data/trendtrack.db');

console.log('🧪 Test du format des dates');
console.log('==========================');

db.all("SELECT creation_date, scraping_last_update, updated_at FROM shops LIMIT 3", [], (err, rows) => {
    if (err) {
        console.error('❌ Erreur:', err);
        return;
    }
    
    console.log('📊 Format actuel des dates:');
    rows.forEach((row, index) => {
        console.log(`Ligne ${index + 1}:`);
        console.log(`  creation_date: ${row.creation_date}`);
        console.log(`  scraping_last_update: ${row.scraping_last_update}`);
        console.log(`  updated_at: ${row.updated_at}`);
        console.log('');
    });
    
    console.log('🎯 Format attendu: 2025-08-12 09:03:57');
    db.close();
});
EOF

echo ""
echo "✅ Corrections appliquées!"
echo "📁 Backup disponible: $BACKUP_DIR"
echo "🧪 Script de test créé: test_date_format.js"
echo ""
echo "🎯 Format uniformisé: 2025-08-12 09:03:57"
