#!/bin/bash
"""
Script simple de surveillance des processus résiduels
Basé sur la commande: ps aux | grep "tail -f" | grep -v $(date +%Y-%m-%d)
"""

# Configuration
TODAY=$(date +%Y-%m-%d)
LOG_FILE="process_monitor.log"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

# Fonction pour surveiller les processus tail -f
monitor_tail_f() {
    log "Surveillance des processus tail -f"
    log "Date du jour: $TODAY"
    
    # Récupérer les processus tail -f
    local tail_processes=$(ps aux | grep "tail -f" | grep -v grep)
    
    if [[ -z "$tail_processes" ]]; then
        log_success "Aucun processus tail -f détecté"
        return 0
    fi
    
    log "Processus tail -f détectés:"
    echo "$tail_processes" | while read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        
        # Vérifier si le fichier de log est ancien
        if [[ "$command" =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
            local file_date="${BASH_REMATCH[1]}"
            if [[ "$file_date" != "$TODAY" ]]; then
                log_warning "Processus tail -f ancien détecté: $command"
                log_warning "PID: $pid, Date fichier: $file_date, Date actuelle: $TODAY"
            else
                log "Processus tail -f récent, conservé: $command"
            fi
        else
            log "Processus tail -f sans date, conservé: $command"
        fi
    done
}

# Fonction pour nettoyer les processus tail -f anciens
cleanup_tail_f() {
    log "Nettoyage des processus tail -f anciens"
    
    local killed_count=0
    
    # Récupérer les processus tail -f
    ps aux | grep "tail -f" | grep -v grep | while read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        
        # Vérifier si le fichier de log est ancien
        if [[ "$command" =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
            local file_date="${BASH_REMATCH[1]}"
            if [[ "$file_date" != "$TODAY" ]]; then
                log_warning "Tuer le processus tail -f ancien: $command"
                log_warning "PID: $pid, Date fichier: $file_date, Date actuelle: $TODAY"
                
                # Tuer le processus
                if kill -15 "$pid" 2>/dev/null; then
                    log_success "Processus $pid tué avec succès"
                    ((killed_count++))
                else
                    log_warning "Erreur tuer processus $pid"
                fi
            fi
        fi
    done
    
    log "Processus tail -f anciens nettoyés: $killed_count"
    return $killed_count
}

# Fonction pour surveiller les processus suspects
monitor_suspicious() {
    log "Surveillance des processus suspects"
    
    # Patterns suspects
    local suspicious_patterns=(
        "python.*menu"
        "python.*launch"
        "bash.*test"
        "node.*update-database"
        "playwright"
        "chromium.*headless"
    )
    
    local suspicious_count=0
    
    for pattern in "${suspicious_patterns[@]}"; do
        local processes=$(ps aux | grep -E "$pattern" | grep -v grep)
        if [[ -n "$processes" ]]; then
            log_warning "Processus suspect détecté (pattern: $pattern):"
            echo "$processes" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
                log_warning "  PID: $pid - $command"
                ((suspicious_count++))
            done
        fi
    done
    
    if [[ $suspicious_count -eq 0 ]]; then
        log_success "Aucun processus suspect détecté"
    else
        log_warning "Total processus suspects: $suspicious_count"
    fi
}

# Fonction pour nettoyer les processus suspects
cleanup_suspicious() {
    log "Nettoyage des processus suspects"
    
    local killed_count=0
    
    # Patterns suspects
    local suspicious_patterns=(
        "python.*menu"
        "python.*launch"
        "bash.*test"
        "node.*update-database"
        "playwright"
        "chromium.*headless"
    )
    
    for pattern in "${suspicious_patterns[@]}"; do
        ps aux | grep -E "$pattern" | grep -v grep | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            
            log_warning "Tuer le processus suspect: $command"
            log_warning "PID: $pid, Pattern: $pattern"
            
            # Tuer le processus
            if kill -15 "$pid" 2>/dev/null; then
                log_success "Processus $pid tué avec succès"
                ((killed_count++))
            else
                log_warning "Erreur tuer processus $pid"
            fi
        done
    done
    
    log "Processus suspects nettoyés: $killed_count"
    return $killed_count
}

# Fonction principale
main() {
    log "DÉMARRAGE DE LA SURVEILLANCE DES PROCESSUS RÉSIDUELS"
    log "=================================================="
    
    # Surveiller les processus tail -f
    monitor_tail_f
    
    # Surveiller les processus suspects
    monitor_suspicious
    
    log "=================================================="
    log "Surveillance terminée"
}

# Fonction de nettoyage
cleanup() {
    log "DÉMARRAGE DU NETTOYAGE DES PROCESSUS RÉSIDUELS"
    log "=============================================="
    
    # Nettoyer les processus tail -f anciens
    cleanup_tail_f
    local tail_killed=$?
    
    # Nettoyer les processus suspects
    cleanup_suspicious
    local suspicious_killed=$?
    
    # Résumé
    local total_killed=$((tail_killed + suspicious_killed))
    
    log "=============================================="
    log "RÉSUMÉ DU NETTOYAGE"
    log "=============================================="
    log "Processus tail -f nettoyés: $tail_killed"
    log "Processus suspects nettoyés: $suspicious_killed"
    log "Total processus nettoyés: $total_killed"
    log_success "Nettoyage terminé"
}

# Gestion des arguments
case "${1:-}" in
    "monitor")
        main
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {monitor|cleanup}"
        echo "  monitor  - Surveiller les processus résiduels"
        echo "  cleanup  - Nettoyer les processus résiduels"
        exit 1
        ;;
esac
