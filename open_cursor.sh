#!/bin/bash
# Script pour ouvrir Cursor dans le bon répertoire

echo "🚀 Ouverture de Cursor dans le répertoire test..."

# Vérifier que nous sommes dans le bon répertoire
if [ "$(pwd)" != "/home/ubuntu/projects/shopshopshops/test" ]; then
    echo "📁 Changement vers le répertoire test..."
    cd /home/ubuntu/projects/shopshopshops/test
fi

echo "📁 Répertoire courant: $(pwd)"

# Essayer différentes commandes pour ouvrir Cursor
if command -v cursor &> /dev/null; then
    echo "✅ Ouverture avec 'cursor .'"
    cursor .
elif command -v code &> /dev/null; then
    echo "✅ Ouverture avec 'code .'"
    code .
else
    echo "❌ Cursor/Code non trouvé dans le PATH"
    echo "💡 Essayez d'ouvrir Cursor manuellement et naviguez vers:"
    echo "   /home/ubuntu/projects/shopshopshops/test"
fi
