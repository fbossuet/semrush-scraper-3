#!/bin/bash

# Script de lancement rapide des scrapers
echo '🚀 LANCEMENT RAPIDE SCRAPERS TrendTrack'
echo '======================================'

# Fonction pour générer timestamp
get_timestamp() {
    date +"%Y%m%d_%H%M%S"
}

# Vérifier les arguments
if [ $# -eq 0 ]; then
    echo
    echo 'Usage: ./launch_scraper.sh <mode> [scraper]'
    echo
    echo 'Modes disponibles:'
    echo '  partial  - Traiter les boutiques avec statut "partial"'
    echo '  empty    - Traiter les boutiques sans données'  
    echo '  all      - Traiter toutes les boutiques'
    echo
    echo 'Scrapers disponibles:'
    echo '  smart    - smart_scraper_fixed.py (par défaut)'
    echo '  prod     - production_scraper.py'
    echo
    echo 'Exemples:'
    echo '  ./launch_scraper.sh partial'
    echo '  ./launch_scraper.sh all prod'
    exit 1
fi

MODE=$1
SCRAPER=${2:-smart}

# Sélectionner le fichier scraper
case $SCRAPER in
    "smart")
        SCRAPER_FILE="smart_scraper_fixed.py"
        SESSION_NAME="smart-$MODE"
        ;;
    "prod")
        SCRAPER_FILE="production_scraper.py"
        SESSION_NAME="prod-$MODE"
        ;;
    *)
        echo "❌ Scraper invalide: $SCRAPER"
        exit 1
        ;;
esac

# Générer nom de log avec timestamp
TIMESTAMP=$(get_timestamp)
LOG_FILE="logs/${SESSION_NAME}_${TIMESTAMP}.log"

echo "📋 Configuration:"
echo "   - Mode: $MODE"
echo "   - Scraper: $SCRAPER_FILE"
echo "   - Session: $SESSION_NAME"
echo "   - Log: $LOG_FILE"
echo

# Vérifier si session existe déjà et trouver un nom libre
ORIGINAL_SESSION_NAME="$SESSION_NAME"
SESSION_COUNTER=1

while screen -list | grep -q "$SESSION_NAME"; do
    echo "⚠️  Session '$SESSION_NAME' existe déjà"
    SESSION_NAME="${ORIGINAL_SESSION_NAME}-${SESSION_COUNTER}"
    SESSION_COUNTER=$((SESSION_COUNTER + 1))
done

if [ "$SESSION_NAME" != "$ORIGINAL_SESSION_NAME" ]; then
    echo "🔄 Utilisation du nom de session: $SESSION_NAME"
fi

# Lancer en screen avec logging structuré
echo "🚀 Lancement en cours..."
screen -dmS "$SESSION_NAME" bash -c "
    echo '🔄 Démarrage du scraper à $(date)'
    echo '📊 Mode: $MODE'
    echo '📁 Log: $LOG_FILE'
    echo
    python3 $SCRAPER_FILE --mode $MODE 2>&1 | tee $LOG_FILE
    echo
    echo '✅ Scraper terminé à $(date)'
    echo 'Appuyez sur Entrée pour fermer cette session...'
    read
"

sleep 2
echo "✅ Session '$SESSION_NAME' lancée avec succès"
echo
echo "🔍 Commands utiles:"
echo "   - Voir la session: screen -r $SESSION_NAME"
echo "   - Monitoring: ./monitor_scraper.sh (à adapter)"
echo "   - Logs temps réel: tail -f $LOG_FILE"
echo
