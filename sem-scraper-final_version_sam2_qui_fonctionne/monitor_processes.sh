#!/bin/bash
"""
Script de surveillance des processus résiduels
Surveille les processus tail -f et autres processus suspects
Nettoyage sécurisé pour éviter de tout péter
"""

# Configuration
TODAY=$(date +%Y-%m-%d)
LOG_FILE="process_monitor.log"
DRY_RUN=true

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

# Fonction pour vérifier si un processus est sûr
is_safe_process() {
    local command="$1"
    
    # Liste des processus système sûrs
    local safe_processes=(
        "systemd"
        "kernel"
        "dbus"
        "network"
        "ssh"
        "cron"
        "rsyslog"
        "postfix"
        "apache"
        "nginx"
        "mysql"
        "postgresql"
        "redis"
        "mongodb"
        "docker"
        "kube"
        "containerd"
        "runc"
    )
    
    for safe in "${safe_processes[@]}"; do
        if [[ "$command" == *"$safe"* ]]; then
            return 0  # Sûr
        fi
    done
    
    return 1  # Pas sûr
}

# Fonction pour vérifier si un processus est suspect
is_suspicious_process() {
    local command="$1"
    
    # Patterns suspects
    local suspicious_patterns=(
        "tail -f.*\.log"
        "python.*menu"
        "python.*launch"
        "bash.*test"
        "node.*update-database"
        "playwright"
        "chromium.*headless"
    )
    
    for pattern in "${suspicious_patterns[@]}"; do
        if [[ "$command" =~ $pattern ]]; then
            return 0  # Suspect
        fi
    done
    
    return 1  # Pas suspect
}

# Fonction pour tuer un processus de manière sécurisée
kill_process_safely() {
    local pid="$1"
    local command="$2"
    local force="$3"
    
    # Vérifier une dernière fois que c'est sûr
    if is_safe_process "$command"; then
        log_warning "Processus système détecté, ignoré: $command"
        return 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Tuerait le processus $pid: $command"
        return 0
    fi
    
    # Utiliser SIGTERM d'abord, puis SIGKILL si nécessaire
    if [[ "$force" == "true" ]]; then
        log "Envoi SIGKILL au processus $pid: $command"
        kill -9 "$pid" 2>/dev/null
    else
        log "Envoi SIGTERM au processus $pid: $command"
        kill -15 "$pid" 2>/dev/null
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Processus $pid tué avec succès"
        return 0
    else
        log_error "Erreur tuer processus $pid"
        return 1
    fi
}

# Fonction pour nettoyer les processus tail -f
cleanup_tail_f_processes() {
    log "Nettoyage des processus tail -f"
    
    local killed_count=0
    
    # Récupérer les processus tail -f
    ps aux | grep "tail -f" | grep -v grep | while read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        
        # Vérifier si le fichier de log est ancien
        if [[ "$command" =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
            local file_date="${BASH_REMATCH[1]}"
            if [[ "$file_date" != "$TODAY" ]]; then
                log_warning "Processus tail -f ancien détecté: $command"
                if kill_process_safely "$pid" "$command" false; then
                    ((killed_count++))
                fi
            else
                log "Processus tail -f récent, conservé: $command"
            fi
        else
            log "Processus tail -f sans date, conservé: $command"
        fi
    done
    
    log "Processus tail -f nettoyés: $killed_count"
    return $killed_count
}

# Fonction pour nettoyer les processus suspects
cleanup_suspicious_processes() {
    log "Nettoyage des processus suspects"
    
    local killed_count=0
    
    # Récupérer tous les processus
    ps aux | while read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        
        # Vérifier si le processus est suspect
        if is_suspicious_process "$command" && ! is_safe_process "$command"; then
            log_warning "Processus suspect détecté: $command"
            if kill_process_safely "$pid" "$command" false; then
                ((killed_count++))
            fi
        fi
    done
    
    log "Processus suspects nettoyés: $killed_count"
    return $killed_count
}

# Fonction pour surveiller les processus
monitor_processes() {
    local interval="${1:-60}"
    
    log "Surveillance des processus (intervalle: ${interval}s)"
    
    while true; do
        # Afficher les processus suspects
        local suspicious_count=0
        ps aux | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            
            if is_suspicious_process "$command" && ! is_safe_process "$command"; then
                ((suspicious_count++))
                log_warning "Processus suspect: $pid - $command"
            fi
        done
        
        if [[ $suspicious_count -eq 0 ]]; then
            log_success "Aucun processus suspect détecté"
        fi
        
        # Afficher les processus tail -f
        local tail_count=0
        ps aux | grep "tail -f" | grep -v grep | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            ((tail_count++))
            log "Processus tail -f actif: $pid - $command"
        done
        
        if [[ $tail_count -eq 0 ]]; then
            log "Aucun processus tail -f actif"
        fi
        
        sleep "$interval"
    done
}

# Fonction principale
main() {
    log "DÉMARRAGE DU NETTOYAGE DES PROCESSUS RÉSIDUELS"
    log "=============================================="
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "MODE DRY RUN - Aucun processus ne sera tué"
    else
        log "MODE RÉEL - Les processus seront tués"
    fi
    
    log "Date du jour: $TODAY"
    log "=============================================="
    
    # Nettoyage des processus tail -f
    cleanup_tail_f_processes
    local tail_killed=$?
    
    # Nettoyage des processus suspects
    cleanup_suspicious_processes
    local suspicious_killed=$?
    
    # Résumé
    local total_killed=$((tail_killed + suspicious_killed))
    
    log "=============================================="
    log "RÉSUMÉ DU NETTOYAGE"
    log "=============================================="
    log "Processus tail -f nettoyés: $tail_killed"
    log "Processus suspects nettoyés: $suspicious_killed"
    log "Total processus nettoyés: $total_killed"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "Mode DRY RUN - Aucun processus n'a été tué"
    else
        log_success "Nettoyage terminé"
    fi
}

# Gestion des arguments
case "${1:-}" in
    "monitor")
        monitor_processes "${2:-60}"
        ;;
    "cleanup")
        main
        ;;
    "force")
        DRY_RUN=false
        main
        ;;
    *)
        echo "Usage: $0 {monitor|cleanup|force} [interval]"
        echo "  monitor [interval]  - Surveiller les processus (défaut: 60s)"
        echo "  cleanup            - Nettoyer en mode dry run"
        echo "  force              - Nettoyer en mode réel"
        exit 1
        ;;
esac
