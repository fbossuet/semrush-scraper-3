#!/bin/bash

echo '📊 RÉSUMÉ FINAL DU SCRAPING'  
echo '=========================='
echo

# Dernière exécution
LAST_LOG=$(ls -t logs/smart_scraper_partial_*log 2>/dev/null | head -1)

if [ -n "$LAST_LOG" ]; then
    echo "📁 Dernier log: $LAST_LOG"
    echo
    
    # Statistiques finales
    echo '📈 STATISTIQUES:'
    BOUTIQUES=$(grep -c 'TRAITEMENT.*/' "$LAST_LOG" 2>/dev/null || echo 0)
    SUCCES=$(grep -c 'SUCCES:' "$LAST_LOG" 2>/dev/null || echo 0)
    ECHECS=$(grep -c 'ÉCHEC:' "$LAST_LOG" 2>/dev/null || echo 0)
    
    echo "   - Boutiques traitées: $BOUTIQUES"
    echo "   - Succès: $SUCCES"
    echo "   - Échecs: $ECHECS"
    echo
    
    # Boutiques traitées
    echo '🏪 BOUTIQUES TRAITÉES:'
    grep 'SUCCES:' "$LAST_LOG" | sed 's/.*SUCCES: /   ✅ /' || echo '   Aucune'
    echo
    
    # Heure de fin
    END_TIME=$(tail -1 "$LAST_LOG" | grep 'TERMINÉ À' | sed 's/.*TERMINÉ À //')
    if [ -n "$END_TIME" ]; then
        echo "⏰ Terminé à: $END_TIME"
    fi
else
    echo '❌ Aucun log trouvé'
fi

echo
echo '🔧 COMMANDES UTILES:'
echo '   - Nouveau scraping: ./launch_scraper.sh partial'
echo '   - Monitoring: ./monitor_scraper.sh'  
echo '   - Voir sessions: screen -list'
