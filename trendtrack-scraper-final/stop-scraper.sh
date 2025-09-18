#!/bin/bash

# Script d'arrêt du scraper
SCRIPT_NAME="trendtrack-scraper"

echo "🛑 Arrêt du scraper TrendTrack..."

# Vérifier si la session screen existe
if screen -list | grep -q "${SCRIPT_NAME}"; then
    echo "📊 Session trouvée, arrêt en cours..."
    
    # Envoyer Ctrl+C pour arrêter proprement le processus
    screen -S ${SCRIPT_NAME} -X stuff $'\003'
    
    # Attendre un peu
    sleep 3
    
    # Tuer la session screen
    screen -S ${SCRIPT_NAME} -X quit
    
    echo "✅ Scraper arrêté avec succès"
else
    echo "⚠️ Aucune session screen '${SCRIPT_NAME}' trouvée"
    
    # Vérifier s'il y a des processus Node.js liés au scraper
    PIDS=$(pgrep -f "node.*scraper")
    if [ ! -z "$PIDS" ]; then
        echo "🔍 Processus Node.js trouvés: $PIDS"
        echo "Voulez-vous les tuer ? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            kill $PIDS
            echo "✅ Processus tués"
        fi
    else
        echo "✅ Aucun processus à arrêter"
    fi
fi

echo "📊 Sessions screen restantes:"
screen -list 