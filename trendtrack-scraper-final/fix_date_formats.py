#!/usr/bin/env python3
"""
Script pour corriger automatiquement tous les formats de dates vers ISO 8601 UTC
"""

import os
import re
from pathlib import Path

def fix_date_formats():
    print("🔧 CORRECTION AUTOMATIQUE DES FORMATS DE DATES")
    print("=" * 80)
    
    # Chemins à corriger
    paths_to_fix = [
        "ubuntu/trendtrack-scraper-final/",
        "ubuntu/sem-scraper-final/",
        "ubuntu/trendtrack-scraper-final/src/",
        "ubuntu/trendtrack-scraper-final/scrapers/",
        "ubuntu/trendtrack-scraper-final/python_bridge/"
    ]
    
    # Patterns de remplacement
    replacements = [
        # Python
        {
            'pattern': r'from datetime import datetime, timezone',
            'replacement': 'from datetime import datetime, timezone',
            'description': 'Ajouter timezone import'
        },
        {
            'pattern': r'datetime\.now\(\)',
            'replacement': 'datetime.now(timezone.utc)',
            'description': 'Remplacer datetime.now() par datetime.now(timezone.utc)'
        },
        {
            'pattern': r'datetime\.now\(timezone\.utc\)\.strftime\([^)]+\)',
            'replacement': 'datetime.now(timezone.utc).isoformat()',
            'description': 'Remplacer strftime par isoformat'
        },
        {
            'pattern': r'datetime.now(timezone.utc).isoformat()',
            'replacement': 'datetime.now(timezone.utc).isoformat()',
            'description': 'Remplacer datetime.now(timezone.utc).isoformat() par ISO 8601'
        },
        {
            'pattern': r'datetime.now(timezone.utc).isoformat()',
            'replacement': 'datetime.now(timezone.utc).isoformat()',
            'description': 'Remplacer datetime.now(timezone.utc).isoformat() par ISO 8601'
        },
        
        # JavaScript
        {
            'pattern': r'Date\.now\(\)',
            'replacement': 'new Date().toISOString()',
            'description': 'Remplacer new Date().toISOString() par new Date().toISOString()'
        },
        {
            'pattern': r'new Date\(\)(?!\.toISOString)',
            'replacement': 'new Date().toISOString()',
            'description': 'Remplacer new Date().toISOString() par new Date().toISOString()'
        }
    ]
    
    files_modified = 0
    total_replacements = 0
    
    for path in paths_to_fix:
        if not os.path.exists(path):
            print(f"⚠️  Chemin non trouvé: {path}")
            continue
            
        print(f"\n🔍 Correction de: {path}")
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.py', '.js')):
                    file_path = os.path.join(root, file)
                    file_modified, replacements_count = fix_file(file_path, replacements)
                    
                    if file_modified:
                        files_modified += 1
                        total_replacements += replacements_count
                        print(f"  ✅ {file}: {replacements_count} corrections")
    
    print(f"\n📊 RÉSUMÉ")
    print(f"  Fichiers modifiés: {files_modified}")
    print(f"  Total corrections: {total_replacements}")
    
    if files_modified > 0:
        print(f"\n🎯 PROCHAINES ÉTAPES")
        print(f"  1. Vérifier les corrections avec: python3 audit_date_formats.py")
        print(f"  2. Tester les scripts modifiés")
        print(f"  3. Exécuter le script de migration de base de données")

def fix_file(file_path, replacements):
    """Corrige un fichier avec les patterns de remplacement"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
        
        replacements_count = 0
        
        for replacement in replacements:
            pattern = replacement['pattern']
            new_content = re.sub(pattern, replacement['replacement'], content)
            
            if new_content != content:
                content = new_content
                replacements_count += 1
        
        # Sauvegarder si des changements ont été faits
        if content != original_content:
            # Créer une sauvegarde
            backup_path = f"{file_path}.backup_before_date_fix"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Écrire le nouveau contenu
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, replacements_count
        
        return False, 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction de {file_path}: {e}")
        return False, 0

if __name__ == "__main__":
    fix_date_formats()
