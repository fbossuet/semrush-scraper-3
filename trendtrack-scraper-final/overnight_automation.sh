
# Script d'automatisation nocturne pour TrendTrack et SEM
echo "🌙 Démarrage de l'automatisation nocturne - $(date)"

# Fonction de nettoyage
cleanup() {
    echo "🧹 Nettoyage des processus..."
    pkill -f "node.*update-database" 2>/dev/null || true
    pkill -f "python.*production_scraper_parallel" 2>/dev/null || true
}

# Fonction pour vérifier le nombre de boutiques
check_shops_count() {
    sqlite3 data/trendtrack.db "SELECT COUNT(*) FROM shops;" 2>/dev/null || echo "0"
}

# Fonction pour lancer TrendTrack
launch_trendtrack() {
    echo "🚀 Lancement du scraper TrendTrack..."
    cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
    timeout 300 node update-database.js > logs/overnight-$(date -Iseconds).log 2>&1 &
    local pid=$!
    
    # Attendre jusqu'à 5 minutes
    for i in {1..30}; do
        if ! kill -0 $pid 2>/dev/null; then
            echo "✅ TrendTrack terminé"
            break
        fi
        sleep 10
    done
    
    # Tuer si toujours en cours
    kill -0 $pid 2>/dev/null && kill $pid 2>/dev/null
}

# Fonction pour lancer SEM workers
launch_sem() {
    local shop_count=$1
    if [ $shop_count -gt 10 ]; then
        echo "🔄 Lancement des workers SEM ($shop_count boutiques disponibles)..."
        cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final
        timeout 600 python3 production_scraper_parallel.py > logs/sem-overnight-$(date -Iseconds).log 2>&1 &
        local pid=$!
        
        # Attendre jusqu'à 10 minutes
        for i in {1..60}; do
            if ! kill -0 $pid 2>/dev/null; then
                echo "✅ SEM workers terminés"
                break
            fi
            sleep 10
        done
        
        # Tuer si toujours en cours
        kill -0 $pid 2>/dev/null && kill $pid 2>/dev/null
    else
        echo "⏭️ Pas assez de boutiques pour SEM ($shop_count < 10)"
    fi
}

# Boucle principale
for cycle in {1..10}; do
    echo ""
    echo "🔄 Cycle $cycle/10 - $(date)"
    
    # Nettoyer les processus précédents
    cleanup
    sleep 5
    
    # Vérifier l'état initial
    initial_count=$(check_shops_count)
    echo "📊 Boutiques actuelles: $initial_count"
    
    # Nettoyer la base périodiquement (tous les 3 cycles)
    if [ $((cycle % 3)) -eq 0 ]; then
        echo "🧹 Nettoyage périodique de la base de données..."
        cd /home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final
        sqlite3 data/trendtrack.db "DELETE FROM shops; DELETE FROM analytics;" 2>/dev/null || true
    fi
    
    # Lancer TrendTrack
    launch_trendtrack
    
    # Vérifier les résultats
    new_count=$(check_shops_count)
    echo "📈 Boutiques après TrendTrack: $new_count"
    
    # Lancer SEM si assez de données
    launch_sem $new_count
    
    # Pause entre les cycles
    echo "😴 Pause de 10 minutes avant le prochain cycle..."
    sleep 600
done

echo "🌅 Automatisation nocturne terminée - $(date)"
