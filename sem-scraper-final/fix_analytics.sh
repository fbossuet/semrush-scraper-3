#!/bin/bash
# Script d'alias pour la correction des statuts analytics
# Utilisation: ./fix_analytics.sh

echo "🔧 SCRIPT DE CORRECTION DES STATUTS ANALYTICS"
echo "=============================================="
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "fix_analytics_status_permanent.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis /home/ubuntu/sem-scraper-final"
    echo "   Utilisez: cd /home/ubuntu/sem-scraper-final && ./fix_analytics.sh"
    exit 1
fi

echo "📋 Ce script va:"
echo "   1. Vérifier les boutiques avec statut 'completed' mais métriques manquantes"
echo "   2. Les corriger automatiquement en 'partial'"
echo "   3. Sauvegarder les corrections dans un fichier JSON"
echo ""

# Demander confirmation
read -p "Voulez-vous continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Opération annulée"
    exit 0
fi

echo ""
echo "🚀 Lancement de la correction..."
echo ""

# Exécuter le script de correction permanent
python3 fix_analytics_status_permanent.py

echo ""
echo "✅ Script terminé!"
echo ""
echo "💡 Pour vérifier les résultats, exécutez:"
echo "   python3 check_analytics_status.py"
