#!/usr/bin/env python3
"""
Correction de l'intégration CPC - Fix des erreurs de syntaxe
"""

import re
from pathlib import Path

def fix_cpc_integration():
    """Corrige les erreurs de syntaxe dans l'intégration CPC"""
    
    scraper_file = Path("/home/ubuntu/sem-scraper-final/production_scraper_parallel.py")
    
    # Lire le fichier
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corriger la section metrics_count
    # Trouver la section problématique
    metrics_count_pattern = r"self\.metrics_count = \{[^}]+\}"
    
    # Nouvelle section corrigée
    new_metrics_count = """self.metrics_count = {
            'organic_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
            'paid_search_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
            'visits': {'found': 0, 'not_found': 0, 'skipped': 0},
            'bounce_rate': {'found': 0, 'not_found': 0, 'skipped': 0},
            'average_visit_duration': {'found': 0, 'not_found': 0, 'skipped': 0},
            'branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
            'conversion_rate': {'found': 0, 'not_found': 0, 'skipped': 0},
            'percent_branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
            'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}
        }"""
    
    # Remplacer la section
    content = re.sub(metrics_count_pattern, new_metrics_count, content, flags=re.DOTALL)
    
    # Écrire le fichier corrigé
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier corrigé avec succès")

if __name__ == "__main__":
    fix_cpc_integration()
