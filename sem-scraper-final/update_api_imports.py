#!/usr/bin/env python3
"""
Script pour mettre à jour tous les imports de l'API TrendTrack
"""

import os
import re
from pathlib import Path

def update_api_imports():
    """Met à jour tous les imports de trendtrack_api_vps_adapted vers trendtrack_api"""
    
    print("🔄 MISE À JOUR DES IMPORTS DE L'API TRENDTRACK")
    print("=" * 60)
    
    # Répertoires à traiter
    directories = [
        '/home/ubuntu/sem-scraper-final',
        '/home/ubuntu/trendtrack-scraper-final'
    ]
    
    # Patterns de remplacement
    replacements = [
        # Import simple
        (r'from trendtrack_api import', 'from trendtrack_api import'),
        # Import avec alias
        (r'import trendtrack_api', 'import trendtrack_api'),
        # Dans les commentaires
        (r'# trendtrack_api', '# trendtrack_api'),
        # Dans les chaînes de caractères
        (r"'trendtrack_api'", "'trendtrack_api'"),
        (r'"trendtrack_api"', '"trendtrack_api"'),
        # Dans les chemins de fichiers
        (r'trendtrack_api_vps_adapted\.py', 'trendtrack_api.py'),
        # Dans les noms de modules
        (r'trendtrack_api_vps_adapted\.', 'trendtrack_api.'),
    ]
    
    total_files_updated = 0
    total_replacements = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"⚠️ Répertoire non trouvé: {directory}")
            continue
            
        print(f"\n📁 Traitement de {directory}")
        
        # Parcourir tous les fichiers Python
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Lire le contenu du fichier
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        original_content = content
                        file_updated = False
                        
                        # Appliquer tous les remplacements
                        for old_pattern, new_pattern in replacements:
                            if old_pattern in content:
                                content = re.sub(old_pattern, new_pattern, content)
                                file_updated = True
                        
                        # Si le fichier a été modifié, l'écrire
                        if file_updated:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            # Compter les remplacements
                            replacements_count = 0
                            for old_pattern, new_pattern in replacements:
                                replacements_count += len(re.findall(old_pattern, original_content))
                            
                            print(f"   ✅ {file}: {replacements_count} remplacements")
                            total_files_updated += 1
                            total_replacements += replacements_count
                        else:
                            print(f"   ℹ️ {file}: Aucun changement nécessaire")
                            
                    except Exception as e:
                        print(f"   ❌ {file}: Erreur {e}")
    
    print(f"\n🎯 RÉSULTAT DU RENOMMAGE:")
    print(f"   📁 Fichiers modifiés: {total_files_updated}")
    print(f"   🔄 Remplacements effectués: {total_replacements}")
    print(f"   ✅ Renommage terminé!")
    
    return total_files_updated, total_replacements

if __name__ == "__main__":
    update_api_imports()
