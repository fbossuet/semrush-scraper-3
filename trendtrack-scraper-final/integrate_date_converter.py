#!/usr/bin/env python3
"""
Script pour intégrer le convertisseur de dates dans tous les scrapers
"""

import os
import re
from pathlib import Path

def integrate_date_converter():
    print("🔧 INTÉGRATION DU CONVERTISSEUR DE DATES")
    print("=" * 60)
    
    # Chemins à modifier
    paths_to_update = [
        "ubuntu/trendtrack-scraper-final/",
        "ubuntu/sem-scraper-final/",
    ]
    
    # Fichiers spécifiques à modifier
    target_files = [
        "production_scraper_parallel.py",
        "domain_scraper.py",
        "trendtrack_api_vps_adapted.py",
        "api_client.py",
        "mytools_api_with_auth.py"
    ]
    
    # Template d'import et d'utilisation
    import_template = """
# Import du convertisseur de dates centralisé
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trendtrack-scraper-final', 'utils'))
from date_converter import DateConverter, convert_api_response_dates
"""
    
    # Template de remplacement pour les fonctions de date
    replacement_templates = [
        {
            'pattern': r'def parse_date_robust\([^)]*\):.*?return None',
            'replacement': '''def parse_date_robust(date_string):
    """Parse une date de manière robuste avec gestion des timezones - DÉPRÉCIÉ"""
    # Utiliser le convertisseur centralisé
    iso_string = DateConverter.convert_to_iso8601_utc(date_string)
    if iso_string:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return None''',
            'description': 'Remplacer parse_date_robust par le convertisseur centralisé'
        },
        {
            'pattern': r'datetime\.now\(timezone\.utc\)\.isoformat\(\)',
            'replacement': 'DateConverter.convert_to_iso8601_utc(datetime.now(timezone.utc))',
            'description': 'Utiliser le convertisseur pour les dates actuelles'
        }
    ]
    
    files_modified = 0
    
    for path in paths_to_update:
        if not os.path.exists(path):
            print(f"⚠️  Chemin non trouvé: {path}")
            continue
            
        print(f"\n🔍 Traitement de: {path}")
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file in target_files and file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if integrate_in_file(file_path, import_template, replacement_templates):
                        files_modified += 1
                        print(f"  ✅ {file}: Intégration réussie")
    
    print(f"\n📊 RÉSUMÉ")
    print(f"  Fichiers modifiés: {files_modified}")
    
    if files_modified > 0:
        print(f"\n🎯 PROCHAINES ÉTAPES")
        print(f"  1. Tester les scrapers avec le nouveau convertisseur")
        print(f"  2. Valider les conversions de dates")
        print(f"  3. Mettre à jour la documentation")

def integrate_in_file(file_path, import_template, replacement_templates):
    """Intègre le convertisseur dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
        
        # Ajouter l'import si pas déjà présent
        if 'from date_converter import' not in content:
            # Trouver la position pour insérer l'import
            import_lines = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(i)
            
            if import_lines:
                # Insérer après le dernier import
                last_import = max(import_lines)
                lines.insert(last_import + 1, import_template.strip())
                content = '\n'.join(lines)
        
        # Appliquer les remplacements
        for template in replacement_templates:
            pattern = template['pattern']
            replacement = template['replacement']
            
            # Utiliser re.DOTALL pour les patterns multilignes
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
        
        # Sauvegarder si des changements ont été faits
        if content != original_content:
            # Créer une sauvegarde
            backup_path = f"{file_path}.backup_before_date_converter"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Écrire le nouveau contenu
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration dans {file_path}: {e}")
        return False

if __name__ == "__main__":
    integrate_date_converter()
