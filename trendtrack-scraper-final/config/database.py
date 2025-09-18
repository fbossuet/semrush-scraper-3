"""Configuration de la base de données"""
import os
from pathlib import Path

def get_database_path():
    """Détermine le chemin de la base selon l environnement"""
    vps_detected = os.path.exists("/home/ubuntu")
    if vps_detected:
        return "../trendtrack-scraper-final/data/trendtrack.db"
    else:
        return "/Users/infusion/Desktop/trendtrack-scrapper/data/trendtrack.db"

DATABASE_CONFIG = {
    "path": get_database_path(),
    "timeout": 30,
    "backup_retention": 50,
    "auto_backup": True
}
