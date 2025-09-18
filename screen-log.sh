#!/bin/bash

# Script pour réutiliser un screen existant avec nouveau log à chaque exécution
# Usage: ./screen-log-reuse.sh <nom_screen> <commande>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <nom_screen> <commande>"
    echo "Exemple: $0 trendtrack-scraper 'cd /home/ubuntu/trendtrack-scraper-final && node update-database.js'"
    exit 1
fi

SCREEN_NAME="$1"
shift
COMMAND="$@"

# Créer le répertoire logs s'il n'existe pas
mkdir -p logs

# Nom du fichier de log avec timestamp
LOG_FILE="logs/${SCREEN_NAME}-$(date +%Y%m%d-%H%M%S).log"

echo "🚀 Exécution dans le screen '$SCREEN_NAME'"
echo "📝 Logs seront écrits dans: $LOG_FILE"
echo "🔧 Commande: $COMMAND"

# Vérifier si le screen existe déjà
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "✅ Screen '$SCREEN_NAME' existe déjà, réutilisation..."
    
    # Envoyer la commande au screen existant avec logging
    screen -S "$SCREEN_NAME" -X stuff "
echo '=== Nouvelle exécution $(date) ===' | tee -a '$LOG_FILE'
echo 'Commande: $COMMAND' | tee -a '$LOG_FILE'
echo '================================' | tee -a '$LOG_FILE'

$COMMAND 2>&1 | tee -a '$LOG_FILE'

echo '=== Fin d'\''exécution $(date) ===' | tee -a '$LOG_FILE'
"
    
    echo "✅ Commande envoyée au screen existant"
else
    echo "🆕 Screen '$SCREEN_NAME' n'existe pas, création..."
    
    # Créer un nouveau screen avec logging
    screen -dmS "$SCREEN_NAME" bash -c "
        echo '=== Début de session $(date) ===' | tee -a '$LOG_FILE'
        echo 'Commande: $COMMAND' | tee -a '$LOG_FILE'
        echo '================================' | tee -a '$LOG_FILE'
        
        # Exécuter la commande et logger tout
        $COMMAND 2>&1 | tee -a '$LOG_FILE'
        
        echo '=== Fin d'\''exécution $(date) ===' | tee -a '$LOG_FILE'
    "
    
    echo "✅ Nouveau screen créé avec logging"
fi

echo "📋 Pour voir les logs en temps réel: tail -f $LOG_FILE"
echo "🔍 Pour lister les screens: screen -ls"
echo "📺 Pour rejoindre le screen: screen -r $SCREEN_NAME"
