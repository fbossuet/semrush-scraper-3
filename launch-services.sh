#!/bin/bash

# Script principal pour lancer tous les services TrendTrack et SEM
echo "🚀 Script de lancement des services TrendTrack et SEM"
echo "=================================================="
echo ""
echo "Choisissez l'action à effectuer :"
echo ""
echo "📊 GESTION BASE DE DONNÉES :"
echo "1. Clean & update base"
echo "2. Dataset : 4 shops"
echo "3. Dataset : 8 shops"
echo ""
echo "🕷️ SCRAPERS :"
echo "4. Scraper SEM"
echo "5. Scraper TrendTrack"
echo ""
echo "🔒 GESTION LOCKS :"
echo "6. Vérifier le lock"
echo "7. Supprimer le lock"
echo ""
echo "⚙️ GESTION PROCESSUS :"
echo "8. Voir tous les processus qui tournent"
echo "9. Tuer un processus"
echo "10. Lister les scripts en cours d'exécution"
echo ""
echo "📺 LOGS ET MONITORING :"
echo "11. Voir les logs en temps réel"
echo "12. Lister les screens actifs"
echo ""
echo "🚀 SERVICES COMPLETS :"
echo "13. Dashboard TrendTrack (Node.js)"
echo "14. API TrendTrack (Python)"
echo "15. Tous les services (Dashboard + API + Scrapers)"
echo "16. Arrêter tous les services"
echo ""
read -p "Votre choix (1-16): " choice

case $choice in
    1)
        echo "🧹 Clean & update base..."
        cd /home/ubuntu/sem-scraper-final && chmod +x clean_database.sh && ./clean_database.sh
        ;;
    2)
        echo "📊 Ajout dataset : 4 shops..."
        echo "🔒 Vérification et suppression des locks..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM processing_locks;"
        echo "🧹 Nettoyage de la base de données..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM shops;"
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM analytics;"
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM selector_performance;"
        echo "📊 Insertion du dataset 4 shops..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" \
        "INSERT INTO shops (shop_name, shop_url, project_source, creation_date) VALUES \
        ('archiesfootwear.com', 'https://archiesfootwear.com', 'manuel', datetime('now', 'localtime')), \
        ('hismileteeth.com', 'https://hismileteeth.com', 'manuel', datetime('now', 'localtime')), \
        ('skims.com', 'https://skims.com', 'manuel', datetime('now', 'localtime')), \
        ('blendjet.com', 'https://blendjet.com', 'manuel', datetime('now', 'localtime'));"
        echo "✅ Dataset 4 shops ajouté (base nettoyée)"
        ;;
    3)
        echo "📊 Ajout dataset : 8 shops..."
        echo "🔒 Vérification et suppression des locks..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM processing_locks;"
        echo "🧹 Nettoyage de la base de données..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM shops;"
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM analytics;"
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" "DELETE FROM selector_performance;"
        echo "📊 Insertion du dataset 8 shops..."
        sqlite3 "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db" \
        "INSERT INTO shops (shop_name, shop_url, project_source, creation_date) VALUES \
        ('spanx.com', 'https://spanx.com', 'manuel', datetime('now', 'localtime')), \
        ('shopbala.com', 'https://shopbala.com', 'manuel', datetime('now', 'localtime')), \
        ('ridge.com', 'https://ridge.com', 'manuel', datetime('now', 'localtime')), \
        ('trtltravel.com', 'https://trtltravel.com', 'manuel', datetime('now', 'localtime')), \
        ('archiesfootwear.com', 'https://archiesfootwear.com', 'manuel', datetime('now', 'localtime')), \
        ('hismileteeth.com', 'https://hismileteeth.com', 'manuel', datetime('now', 'localtime')), \
        ('skims.com', 'https://skims.com', 'manuel', datetime('now', 'localtime')), \
        ('blendjet.com', 'https://blendjet.com', 'manuel', datetime('now', 'localtime'));"
        echo "✅ Dataset 8 shops ajouté (base nettoyée)"
        ;;
    4)
        echo "🕷️ Vérification du Scraper SEM..."
        
        # Vérifier si un scraper SEM tourne déjà
        if ps aux | grep -v grep | grep -q "python3.*production_scraper.py"; then
            echo "⚠️ Un scraper SEM est déjà en cours d'exécution !"
            echo "📊 Processus en cours :"
            ps aux | grep -v grep | grep "python3.*production_scraper.py"
            echo ""
            read -p "Voulez-vous forcer l'arrêt et relancer ? (y/N): " force_restart
            if [ "$force_restart" = "y" ] || [ "$force_restart" = "Y" ]; then
                echo "🛑 Arrêt forcé du scraper SEM..."
                pkill -f "python3.*production_scraper.py"
                screen -S sem-prod -X quit 2>/dev/null
                sleep 3
            else
                echo "❌ Lancement annulé"
                exit 0
            fi
        fi
        
        echo "🕷️ Lancement du Scraper SEM..."
        /home/ubuntu/screen-log.sh sem-prod 'cd /home/ubuntu/sem-scraper-final && python3 production_scraper.py'
        echo "📺 Attente de 3 secondes pour la création du log..."
        sleep 3
        echo "📺 Suivi du log en temps réel..."
        tail -f /home/ubuntu/sem-scraper-final/logs/sem-prod-$(ls -t /home/ubuntu/sem-scraper-final/logs/sem-prod-*.log 2>/dev/null | head -1 | xargs basename 2>/dev/null)
        ;;
    5)
        echo "🕷️ Vérification du Scraper TrendTrack..."
        
        # Vérifier si un scraper TrendTrack tourne déjà
        if ps aux | grep -v grep | grep -q "node.*update-database.js"; then
            echo "⚠️ Un scraper TrendTrack est déjà en cours d'exécution !"
            echo "📊 Processus en cours :"
            ps aux | grep -v grep | grep "node.*update-database.js"
            echo ""
            read -p "Voulez-vous forcer l'arrêt et relancer ? (y/N): " force_restart
            if [ "$force_restart" = "y" ] || [ "$force_restart" = "Y" ]; then
                echo "🛑 Arrêt forcé du scraper TrendTrack..."
                pkill -f "node.*update-database.js"
                screen -S trendtrack-prod -X quit 2>/dev/null
                sleep 3
            else
                echo "❌ Lancement annulé"
                exit 0
            fi
        fi
        
        echo "🕷️ Lancement du Scraper TrendTrack..."
        /home/ubuntu/screen-log.sh trendtrack-prod 'cd /home/ubuntu/trendtrack-scraper-final && node update-database.js'
        echo "📺 Attente de 3 secondes pour la création du log..."
        sleep 3
        echo "📺 Suivi du log en temps réel..."
        tail -f /home/ubuntu/trendtrack-scraper-final/logs/trendtrack-prod-$(ls -t /home/ubuntu/trendtrack-scraper-final/logs/trendtrack-prod-*.log 2>/dev/null | head -1 | xargs basename 2>/dev/null)
        ;;
    6)
        echo "🔒 Vérification du lock..."
        sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db "SELECT * FROM processing_locks;"
        ;;
    7)
        echo "🔒 Suppression du lock..."
        sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db "DELETE FROM processing_locks;"
        echo "✅ Lock supprimé"
        ;;
    8)
        echo "⚙️ Processus en cours d'exécution :"
        ps aux | grep -E "(python3|node|screen)" | grep -v grep
        ;;
    9)
        echo "⚙️ Processus en cours d'exécution :"
        ps aux | grep -E "(python3|node|screen)" | grep -v grep
        echo ""
        read -p "Entrez l'ID du processus à tuer: " pid
        if [ ! -z "$pid" ]; then
            echo "🛑 Suppression du processus $pid..."
            kill -9 $pid
            echo "✅ Processus $pid supprimé"
        else
            echo "❌ ID de processus invalide"
        fi
        ;;
    10)
        echo "📋 Scripts en cours d'exécution :"
        screen -ls
        ;;
    11)
        echo "📺 Logs disponibles :"
                            echo "📋 Logs SEM :"
                    ls -lat /home/ubuntu/sem-scraper-final/logs/ | grep -E "sem-prod.*\.(log)$" | head -5
                    echo ""
                    echo "📋 Logs TrendTrack :"
                    ls -lat /home/ubuntu/trendtrack-scraper-final/logs/ | grep -E "trendtrack-prod.*\.(log)$" | head -5
        echo ""
        read -p "Type de log (sem/trendtrack): " logtype
                            if [ "$logtype" = "sem" ]; then
                        echo "📺 Suivi du log SEM le plus récent..."
                        tail -f /home/ubuntu/sem-scraper-final/logs/sem-prod-$(ls -t /home/ubuntu/sem-scraper-final/logs/sem-prod-*.log 2>/dev/null | head -1 | xargs basename 2>/dev/null)
                    elif [ "$logtype" = "trendtrack" ]; then
                        echo "📺 Suivi du log TrendTrack le plus récent..."
                        tail -f /home/ubuntu/trendtrack-scraper-final/logs/trendtrack-prod-$(ls -t /home/ubuntu/trendtrack-scraper-final/logs/trendtrack-prod-*.log 2>/dev/null | head -1 | xargs basename 2>/dev/null)
        else
            echo "❌ Type de log invalide"
        fi
        ;;
    12)
        echo "🔍 Screens actifs :"
        screen -ls
        ;;
    13)
        echo "🚀 Lancement du Dashboard TrendTrack..."
        ./trendtrack-dashboard.sh trendtrack-dashboard "cd /home/ubuntu/trendtrack-scraper-final && npm run dashboard"
        ;;
    14)
        echo "🚀 Lancement de l'API TrendTrack..."
        ./trendtrack-dashboard.sh trendtrack-api "cd /home/ubuntu/trendtrack-scraper-final && python3 trendtrack_api.py"
        ;;
    15)
        echo "🚀 Lancement de tous les services..."
        echo "📊 Démarrage du Dashboard..."
        ./trendtrack-dashboard.sh trendtrack-dashboard "cd /home/ubuntu/trendtrack-scraper-final && npm run dashboard" &
        sleep 3
        echo "🔗 Démarrage de l'API..."
        ./trendtrack-dashboard.sh trendtrack-api "cd /home/ubuntu/trendtrack-scraper-final && python3 trendtrack_api.py" &
        sleep 2
        echo "🕷️ Démarrage du Scraper SEM..."
        ./sem-scraper.sh sem-scraper "cd /home/ubuntu/sem-scraper-final && python3 production_scraper.py" &
        sleep 2
        echo "📈 Démarrage du Scraper TrendTrack..."
        ./trendtrack-dashboard.sh trendtrack-scraper "cd /home/ubuntu/trendtrack-scraper-final && node final-fixed.js" &
        echo "✅ Tous les services ont été lancés"
        echo "📋 Services actifs :"
        echo "   • Dashboard: http://37.59.102.7:3000"
        echo "   • API: Bibliothèque Python"
        echo "   • Scraper SEM: En cours d'exécution"
        echo "   • Scraper TrendTrack: En cours d'exécution"
        ;;
    16)
        echo "🛑 Arrêt de tous les services..."
        screen -S trendtrack-dashboard -X quit 2>/dev/null
        screen -S trendtrack-api -X quit 2>/dev/null
        screen -S sem-scraper -X quit 2>/dev/null
        screen -S trendtrack-scraper -X quit 2>/dev/null
        screen -S sem-prod -X quit 2>/dev/null
        screen -S trendtrack-prod -X quit 2>/dev/null
        echo "✅ Tous les services ont été arrêtés"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "📋 Commandes utiles :"
echo "  • Dashboard web: http://37.59.102.7:3000"
echo "  • API endpoints: http://37.59.102.7:3000/api"
echo ""
echo "🔧 Gestion des screens :"
echo "  • Rejoindre un screen: screen -r trendtrack-dashboard"
echo "  • Rejoindre un screen: screen -r trendtrack-api"
echo "  • Rejoindre un screen: screen -r sem-scraper"
echo "  • Rejoindre un screen: screen -r trendtrack-scraper"
echo "  • Rejoindre un screen: screen -r sem-prod"
echo "  • Rejoindre un screen: screen -r trendtrack-prod"
echo "  • Lister les screens: screen -ls"
echo ""
echo "🛑 Arrêt des screens :"
echo "  • Arrêter un screen: screen -S trendtrack-dashboard -X quit"
echo "  • Arrêter un screen: screen -S trendtrack-api -X quit"
echo "  • Arrêter un screen: screen -S sem-scraper -X quit"
echo "  • Arrêter un screen: screen -S trendtrack-scraper -X quit"
echo "  • Arrêter un screen: screen -S sem-prod -X quit"
echo "  • Arrêter un screen: screen -S trendtrack-prod -X quit"
echo ""
echo "📺 Logs :"
echo "  • Logs SEM: tail -f /home/ubuntu/sem-scraper-final/logs/sem-prod-*.log"
echo "  • Logs TrendTrack: tail -f /home/ubuntu/trendtrack-scraper-final/logs/trendtrack-prod-*.log"
echo "  • Logs Dashboard: tail -f /home/ubuntu/logs/trendtrack-dashboard-*.log"
echo "  • Logs API: tail -f /home/ubuntu/logs/trendtrack-api-*.log"
echo ""
echo "🗂️ Accès aux dossiers :"
echo "  • SEM Scraper: cd /home/ubuntu/sem-scraper-final"
echo "  • TrendTrack: cd /home/ubuntu/trendtrack-scraper-final"
echo "  • Logs: cd /home/ubuntu/logs"
echo ""
echo "📊 Services disponibles :"
echo "  • trendtrack-dashboard - Dashboard web Node.js"
echo "  • trendtrack-api - API Python"
echo "  • sem-scraper - Scraper SEM Python (ancien)"
echo "  • trendtrack-scraper - Scraper TrendTrack Node.js (ancien)"
echo "  • sem-prod - Scraper SEM Python (production)"
echo "  • trendtrack-prod - Scraper TrendTrack Node.js (production)"
