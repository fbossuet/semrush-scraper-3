#!/bin/bash

# Script de lancement du scraper avec screen et logging
SCRIPT_NAME="trendtrack-scraper"
LOG_DIR="logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/scraper-${TIMESTAMP}.log"

# Créer le dossier logs s'il n'existe pas
mkdir -p ${LOG_DIR}

echo "🚀 Lancement du scraper TrendTrack..."
echo "📝 Log file: ${LOG_FILE}"
echo "🖥️ Session screen: ${SCRIPT_NAME}"

# Vérifier si une session screen existe déjà
if screen -list | grep -q "${SCRIPT_NAME}"; then
    echo "⚠️ Une session screen '${SCRIPT_NAME}' existe déjà"
    echo "Voulez-vous la tuer et en créer une nouvelle ? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        screen -S ${SCRIPT_NAME} -X quit
        echo "✅ Ancienne session terminée"
    else
        echo "❌ Lancement annulé"
        exit 1
    fi
fi

# Lancer le scraper dans un screen avec logging
screen -L -Logfile ${LOG_FILE} -S ${SCRIPT_NAME} -dm bash -c "
echo '🕐 Démarrage: $(date)'
echo '📁 Répertoire: $(pwd)'
echo '🔧 Lancement du scraper...'
node update-database.js
echo '🛑 Arrêt: $(date)'
"

# Attendre un peu pour que le screen démarre
sleep 2

# Vérifier que la session est bien créée
if screen -list | grep -q "${SCRIPT_NAME}"; then
    echo "✅ Scraper lancé avec succès !"
    echo "📊 Sessions screen actives:"
    screen -list
    echo ""
    echo "📝 Pour voir les logs en temps réel:"
    echo "   tail -f ${LOG_FILE}"
    echo ""
    echo "🖥️ Pour rejoindre la session:"
    echo "   screen -r ${SCRIPT_NAME}"
    echo ""
    echo "❌ Pour arrêter la session:"
    echo "   screen -S ${SCRIPT_NAME} -X quit"
else
    echo "❌ Erreur lors du lancement"
    exit 1
fi 