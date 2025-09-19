#!/bin/bash

# Script de lancement pour l'architecture parallèle TrendTrack
# Usage: ./launch-parallel-scraper.sh

echo "🚀 LANCEMENT - Architecture Parallèle TrendTrack"
echo "================================================"

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "update-database-parallel.js" ]; then
    echo "❌ Erreur: Script update-database-parallel.js non trouvé"
    echo "   Assurez-vous d'être dans le répertoire trendtrack-scraper-final/"
    exit 1
fi

# Créer le répertoire logs s'il n'existe pas
mkdir -p logs

# Vérifier que Node.js est installé
if ! command -v node &> /dev/null; then
    echo "❌ Erreur: Node.js n'est pas installé"
    exit 1
fi

# Vérifier que les dépendances sont installées
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances..."
    npm install
fi

echo "🔧 Configuration:"
echo "   - Architecture: Parallèle (2 phases)"
echo "   - Phase 1: Extraction données tableau uniquement"
echo "   - Phase 2: Extraction détails en parallèle"
echo "   - Log: logs/update-progress-parallel.log"
echo ""

# Demander confirmation
read -p "Voulez-vous lancer le scraper parallèle ? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Lancement annulé"
    exit 0
fi

echo "🚀 Lancement du scraper parallèle..."
echo "   Surveillez le log: tail -f logs/update-progress-parallel.log"
echo ""

# Lancer le script
node update-database-parallel.js

echo ""
echo "✅ Script terminé"
echo "📊 Consultez le log pour les détails: logs/update-progress-parallel.log"


