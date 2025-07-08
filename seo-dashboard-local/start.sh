#!/bin/bash

echo "🎯 ================================"
echo "   Dashboard SEO Analytics"
echo "   Démarrage Automatique Mac/Linux"
echo "🎯 ================================"
echo ""

echo "🔍 Vérification Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non trouvé !"
    echo "📥 Télécharge depuis: https://nodejs.org/"
    echo "🔄 Relancer ce script après installation"
    read -p "Appuie sur Entrée pour continuer..."
    exit 1
fi

echo "✅ Node.js OK ($(node --version))"
echo ""

echo "📦 Installation des dépendances..."
npm install express cors

echo ""
echo "🚀 Démarrage du dashboard..."
echo "🌐 Interface disponible sur: http://localhost:3000"
echo ""
echo "⏹️  Pour arrêter: Ctrl + C"
echo ""

# Ouvrir automatiquement le navigateur (optionnel)
if command -v open &> /dev/null; then
    # Mac
    sleep 3 && open http://localhost:3000 &
elif command -v xdg-open &> /dev/null; then
    # Linux
    sleep 3 && xdg-open http://localhost:3000 &
fi

npm start