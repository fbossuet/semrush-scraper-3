#!/bin/bash

# Script pour corriger l'ordre des routes FastAPI
# Date: $(date)

echo "🔧 Correction de l'ordre des routes FastAPI"
echo "=========================================="

# Variables
PROJECT_PATH="/home/ubuntu/sem-scraper-final"
API_SERVER_FILE="$PROJECT_PATH/api_server.py"
BACKUP_FILE="$PROJECT_PATH/api_server_backup_before_route_fix_$(date +%Y%m%d_%H%M%S).py"

echo "📋 Étape 1: Sauvegarde du serveur API actuel..."
cp "$API_SERVER_FILE" "$BACKUP_FILE"
echo "✅ Sauvegarde créée: $(basename $BACKUP_FILE)"

echo ""
echo "🔍 Étape 2: Recherche des lignes de routes..."
# Trouver les lignes des routes problématiques
SHOP_ID_LINE=$(grep -n "@app.get(\"/shops/{shop_id}\")" "$API_SERVER_FILE" | cut -d: -f1)
COMPLETED_LINE=$(grep -n "@app.get(\"/shops/completed\")" "$API_SERVER_FILE" | cut -d: -f1)
URL_LINE=$(grep -n "@app.get(\"/shops/url/{shop_url:path}\")" "$API_SERVER_FILE" | cut -d: -f1)

echo "📍 Ligne /shops/{shop_id}: $SHOP_ID_LINE"
echo "📍 Ligne /shops/completed: $COMPLETED_LINE"
echo "📍 Ligne /shops/url/{shop_url}: $URL_LINE"

echo ""
echo "🛠️  Étape 3: Extraction des nouvelles routes..."

# Extraire les nouvelles routes (de la ligne completed à la fin, avant uvicorn.run)
UVICORN_LINE=$(grep -n "uvicorn.run" "$API_SERVER_FILE" | cut -d: -f1)
NEW_ROUTES_END=$((UVICORN_LINE - 1))

# Sauvegarder les nouvelles routes
sed -n "${COMPLETED_LINE},${NEW_ROUTES_END}p" "$API_SERVER_FILE" > /tmp/new_routes.py

echo ""
echo "🛠️  Étape 4: Suppression des nouvelles routes de leur position actuelle..."

# Supprimer les nouvelles routes de leur position actuelle
head -n $((COMPLETED_LINE - 1)) "$API_SERVER_FILE" > /tmp/api_part1.py

echo ""
echo "🛠️  Étape 5: Insertion des nouvelles routes avant /shops/{shop_id}..."

# Insérer les nouvelles routes avant /shops/{shop_id}
head -n $((SHOP_ID_LINE - 1)) /tmp/api_part1.py > /tmp/api_part2.py
cat /tmp/new_routes.py >> /tmp/api_part2.py
tail -n +$SHOP_ID_LINE /tmp/api_part1.py >> /tmp/api_part2.py

# Remplacer le fichier original
mv /tmp/api_part2.py "$API_SERVER_FILE"

echo ""
echo "✅ Étape 6: Vérification de l'ordre des routes..."
NEW_ORDER=$(grep -n "@app\.get.*shops" "$API_SERVER_FILE")
echo "📋 Nouvel ordre des routes:"
echo "$NEW_ORDER"

echo ""
echo "🎯 Routes corrigées!"
echo "📁 Sauvegarde: $(basename $BACKUP_FILE)"
echo ""
echo "🚀 Pour redémarrer l'API:"
echo "   pkill -f api_server.py"
echo "   cd /home/ubuntu/sem-scraper-final && python3 api_server.py"
