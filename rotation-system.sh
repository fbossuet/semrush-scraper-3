#!/bin/bash

# Script de rotation automatique pour sem-scraper-final
LOG_FILE="/home/ubuntu/rotation-system.log"
PROJECT_DIR="/home/ubuntu/sem-scraper-final"
MAX_ERROR_FILES=100

log_message() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a $LOG_FILE
}

log_message "=== DÉBUT ROTATION AUTOMATIQUE ==="

# Rotation des fichiers d erreurs
if [ -d "$PROJECT_DIR/error_pages" ]; then
    ERROR_COUNT=$(ls $PROJECT_DIR/error_pages/*.txt 2>/dev/null | wc -l)
    log_message "Fichiers d erreurs trouvés: $ERROR_COUNT"
    if [ $ERROR_COUNT -gt $MAX_ERROR_FILES ]; then
        ls -t $PROJECT_DIR/error_pages/*.txt 2>/dev/null | tail -n +$((MAX_ERROR_FILES + 1)) | xargs rm -f
        log_message "Rotation error_pages terminée"
    fi
fi

# Nettoyage du cache navigateur
if [ -d "$PROJECT_DIR/session-profile-production" ]; then
    CACHE_SIZE=$(du -s $PROJECT_DIR/session-profile-production | cut -f1)
    CACHE_SIZE_MB=$((CACHE_SIZE / 1024))
    if [ $CACHE_SIZE_MB -gt 500 ]; then
        rm -rf $PROJECT_DIR/session-profile-production
        log_message "Cache navigateur nettoyé"
    fi
fi

log_message "=== FIN ROTATION AUTOMATIQUE ==="
