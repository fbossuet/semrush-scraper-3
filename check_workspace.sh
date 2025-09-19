#!/bin/bash
# Script de vérification du workspace

echo "🔍 Vérification du workspace..."
echo "================================"

# Vérifier le répertoire courant
echo "📁 Répertoire courant: $(pwd)"
echo "📁 Répertoire attendu: /home/ubuntu/projects/shopshopshops/test"

if [ "$(pwd)" = "/home/ubuntu/projects/shopshopshops/test" ]; then
    echo "✅ Répertoire correct"
else
    echo "❌ MAUVAIS RÉPERTOIRE! Aller dans /home/ubuntu/projects/shopshopshops/test"
    exit 1
fi

echo ""
echo "🗄️ Vérification des bases de données:"
python3 database_config.py

echo ""
echo "🚀 Vérification de l'API:"
if pgrep -f "api_server.py" > /dev/null; then
    echo "✅ API en cours d'exécution"
    echo "🌐 URL: http://37.59.102.7:8001"
else
    echo "❌ API non démarrée"
    echo "💡 Pour démarrer: cd sem-scraper-final && python3 api_server.py"
fi

echo ""
echo "📋 Fichiers importants:"
echo "  - API: sem-scraper-final/api_server.py"
echo "  - Config: database_config.py"
echo "  - Menu: sem-scraper-final/menu_workers.py"
