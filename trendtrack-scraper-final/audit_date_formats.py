#!/usr/bin/env python3
"""
Script d'audit des formats de dates dans tout le code
Vérifie que toutes les dates sont au format ISO 8601 UTC
"""

import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def audit_date_formats():
    print("🔍 AUDIT DES FORMATS DE DATES")
    print("=" * 80)
    
    # Chemins à auditer
    paths_to_audit = [
        "ubuntu/trendtrack-scraper-final/",
        "ubuntu/sem-scraper-final/",
        "ubuntu/trendtrack-scraper-final/src/",
        "ubuntu/trendtrack-scraper-final/scrapers/",
        "ubuntu/trendtrack-scraper-final/python_bridge/"
    ]
    
    # Patterns à rechercher
    date_patterns = {
        "datetime.now(timezone.utc)": r"datetime\.now\(\)",
        "datetime.now(timezone.utc).isoformat()": r"datetime.now(timezone.utc).isoformat()",
        "new Date().toISOString()": r"new Date\(\)",
        "new Date().toISOString()": r"Date\.now\(\)",
        "toISOString()": r"\.toISOString\(\)",
        "strftime": r"strftime\(",
        "strptime": r"strptime\(",
        "timestamp": r"timestamp",
        "created_at": r"created_at",
        "updated_at": r"updated_at",
        "scraped_at": r"scraped_at",
        "creation_date": r"creation_date",
        "year_founded": r"year_founded"
    }
    
    issues_found = []
    
    print("📁 1. AUDIT DES FICHIERS DE CODE")
    print("-" * 40)
    
    for path in paths_to_audit:
        if not os.path.exists(path):
            print(f"⚠️  Chemin non trouvé: {path}")
            continue
            
        print(f"\n🔍 Audit de: {path}")
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.py', '.js', '.sql')):
                    file_path = os.path.join(root, file)
                    audit_file(file_path, date_patterns, issues_found)
    
    print("\n📊 2. AUDIT DE LA BASE DE DONNÉES")
    print("-" * 40)
    
    audit_database_dates(issues_found)
    
    print("\n📋 3. RÉSUMÉ DES PROBLÈMES")
    print("-" * 40)
    
    if issues_found:
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")
    else:
        print("✅ Aucun problème de format de date détecté!")
    
    print("\n🎯 4. RECOMMANDATIONS")
    print("-" * 40)
    print("✅ Format recommandé: ISO 8601 UTC (ex: '2025-09-18T10:30:45.123Z')")
    print("✅ Python: datetime.now(timezone.utc).isoformat()")
    print("✅ JavaScript: new Date().toISOString()")
    print("✅ SQLite: TEXT avec format ISO 8601")

def audit_file(file_path, date_patterns, issues_found):
    """Audite un fichier pour les formats de dates"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in date_patterns.items():
                if re.search(pattern, line):
                    # Vérifier si c'est un format ISO 8601
                    if not is_iso8601_format(line):
                        issue = f"{file_path}:{line_num} - {pattern_name} détecté: {line.strip()}"
                        issues_found.append(issue)
                        
    except Exception as e:
        print(f"❌ Erreur lors de l'audit de {file_path}: {e}")

def is_iso8601_format(line):
    """Vérifie si la ligne utilise le format ISO 8601"""
    iso_patterns = [
        r"\.isoformat\(\)",
        r"\.toISOString\(\)",
        r"ISO.*8601",
        r"UTC.*timestamp",
        r"timezone\.utc"
    ]
    
    for pattern in iso_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def audit_database_dates(issues_found):
    """Audite les dates dans la base de données"""
    db_path = "ubuntu/trendtrack-scraper-final/data/trendtrack.db"
    
    if not os.path.exists(db_path):
        print(f"⚠️  Base de données non trouvée: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier la structure des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name in ['shops', 'analytics']:
                audit_table_dates(cursor, table_name, issues_found)
                
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'audit de la base de données: {e}")

def audit_table_dates(cursor, table_name, issues_found):
    """Audite les dates dans une table spécifique"""
    print(f"\n📊 Table: {table_name}")
    
    # Obtenir la structure de la table
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    date_columns = []
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        if 'date' in col_name.lower() or 'time' in col_name.lower() or col_type == 'TEXT':
            date_columns.append(col_name)
    
    if date_columns:
        print(f"  Colonnes de dates: {', '.join(date_columns)}")
        
        # Vérifier quelques exemples de données
        for col in date_columns:
            cursor.execute(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 5;")
            samples = cursor.fetchall()
            
            if samples:
                print(f"  Exemples {col}:")
                for sample in samples:
                    value = sample[0]
                    if value:
                        print(f"    - {value}")
                        if not is_valid_iso8601(str(value)):
                            issues_found.append(f"Base de données - {table_name}.{col}: Format non ISO 8601: {value}")

def is_valid_iso8601(date_string):
    """Vérifie si une chaîne est au format ISO 8601 valide"""
    try:
        # Patterns ISO 8601
        iso_patterns = [
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$',  # 2025-09-18T10:30:45.123Z
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',              # 2025-09-18T10:30:45Z
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'                # 2025-09-18T10:30:45
        ]
        
        for pattern in iso_patterns:
            if re.match(pattern, date_string):
                return True
        return False
    except:
        return False

if __name__ == "__main__":
    audit_date_formats()
