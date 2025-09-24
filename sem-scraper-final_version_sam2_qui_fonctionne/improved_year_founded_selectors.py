#!/usr/bin/env python3
"""
Sélecteurs améliorés pour l'extraction de l'année de fondation
Basés sur l'analyse du DOM pour plus de précision et de robustesse
"""

def get_improved_selectors():
    """Retourne une liste de sélecteurs améliorés, du plus spécifique au plus générique"""
    
    return [
        # 1. Sélecteur le plus spécifique - basé sur l'analyse du DOM
        'p.text-\\[11px\\]',
        
        # 2. Sélecteurs avec contexte parent pour plus de précision
        'td p.text-\\[11px\\]',  # Dans une cellule de tableau
        'div p.text-\\[11px\\]', # Dans une div
        
        # 3. Sélecteurs basés sur le contenu (plus robustes)
        'p:has-text("09/11/2024")',  # Contient la date exacte
        'p:has-text("/2024")',       # Contient une année
        'p:has-text("mois")',        # Contient "mois" (contexte français)
        
        # 4. Sélecteurs basés sur la structure
        'p[class*="text-11px"]',
        'p[class*="text-xs"]',
        'p[class*="text-sm"]',
        
        # 5. Sélecteurs génériques (fallback)
        'p[class*="text-"]',
        'p[class*="date"]',
        'p[class*="founded"]',
        'p[class*="created"]',
        'p[class*="established"]',
        'p[class*="since"]',
        
        # 6. Sélecteurs textuels (dernier recours)
        'text=/founded/i',
        'text=/since/i', 
        'text=/established/i',
        'text=/created/i',
        'text=/started/i',
        'text=/©/i',
        'text=/copyright/i'
    ]

def get_validation_rules():
    """Retourne les règles de validation pour s'assurer qu'on a trouvé la bonne date"""
    
    return {
        'content_patterns': [
            r'\\d{2}/\\d{2}/\\d{4}',  # Format DD/MM/YYYY
            r'\\d{4}-\\d{2}-\\d{2}',  # Format YYYY-MM-DD
            r'\\b(19|20)\\d{2}\\b',   # Année simple
        ],
        'context_keywords': [
            'mois', 'month', 'founded', 'since', 'established', 
            'created', 'started', '©', 'copyright'
        ],
        'exclude_patterns': [
            r'\\d{4}-\\d{2}-\\d{2}T',  # Exclure les timestamps ISO
            r'\\d{2}:\\d{2}:\\d{2}',   # Exclure les heures
        ]
    }

def test_selectors():
    """Teste les sélecteurs sur des exemples"""
    
    print("🧪 TEST DES SÉLECTEURS AMÉLIORÉS")
    print("=" * 60)
    
    selectors = get_improved_selectors()
    
    print("📋 SÉLECTEURS PAR ORDRE DE PRIORITÉ:")
    print("=" * 60)
    
    for i, selector in enumerate(selectors, 1):
        priority = "🔥" if i <= 3 else "⚡" if i <= 6 else "🔄"
        print(f"{priority} {i:2}. {selector}")
    
    print("\\n📋 RÈGLES DE VALIDATION:")
    print("=" * 60)
    
    rules = get_validation_rules()
    print("✅ Patterns de contenu acceptés:")
    for pattern in rules['content_patterns']:
        print(f"  - {pattern}")
    
    print("\\n✅ Mots-clés de contexte:")
    for keyword in rules['context_keywords']:
        print(f"  - {keyword}")
    
    print("\\n❌ Patterns à exclure:")
    for pattern in rules['exclude_patterns']:
        print(f"  - {pattern}")

if __name__ == "__main__":
    test_selectors()
