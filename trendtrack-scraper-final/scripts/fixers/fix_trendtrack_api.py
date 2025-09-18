#!/usr/bin/env python3
"""
Script pour corriger trendtrack_api.py et ajouter les champs manquants
"""

import re

def fix_trendtrack_api():
    """Corrige le fichier trendtrack_api.py"""
    
    # Lire le fichier
    with open('trendtrack_api.py', 'r') as f:
        content = f.read()
    
    # Trouver et remplacer la section visits
    pattern = r'(\s+)"visits": row\[21\](\s+)\)'
    replacement = r'\1"visits": row[21],\n\1"traffic": row[22],\n\1"percent_branded_traffic": row[23],\n\1"paid_search_traffic": row[24]\2)'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Écrire le fichier corrigé
    with open('trendtrack_api.py', 'w') as f:
        f.write(new_content)
    
    print("✅ trendtrack_api.py corrigé avec succès")

if __name__ == "__main__":
    fix_trendtrack_api()
