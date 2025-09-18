#!/usr/bin/env python3
"""
Script rapide pour corriger l'erreur de guillemets à la ligne 4
"""

import os

def fix_line_4():
    """Corrige l'erreur de guillemets à la ligne 4"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    print("🔧 Correction rapide de la ligne 4...")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Afficher les premières lignes
    print("📄 Premières lignes du fichier:")
    for i in range(min(10, len(lines))):
        print(f"   {i+1:2d}: {lines[i].rstrip()}")
    
    # Créer un backup
    backup_path = f"{file_path}.backup_quick_fix"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Backup créé: {backup_path}")
    
    # Corriger la ligne 4
    if len(lines) >= 4:
        line_4 = lines[3]  # Index 3 = ligne 4
        
        print(f"🔍 Ligne 4 actuelle: {line_4.rstrip()}")
        
        # Corriger les guillemets problématiques
        if '""""' in line_4:
            # Remplacer les guillemets quadruples par des guillemets doubles
            fixed_line = line_4.replace('""""', '"""')
            lines[3] = fixed_line
            print(f"✅ Ligne 4 corrigée: {fixed_line.rstrip()}")
        elif line_4.count('"') % 2 != 0:
            # Ajouter un guillemet fermant
            fixed_line = line_4.rstrip() + '"'
            lines[3] = fixed_line
            print(f"✅ Ligne 4 corrigée: {fixed_line.rstrip()}")
        else:
            print("⚠️ Problème non identifié sur la ligne 4")
            return False
        
        # Sauvegarder le fichier corrigé
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Fichier corrigé et sauvegardé")
        return True
    else:
        print("❌ Fichier trop court")
        return False

def test_syntax():
    """Teste la syntaxe après correction"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print("\n🧪 Test de syntaxe après correction...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print("✅ Syntaxe Python valide")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe persistante: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Correction rapide de l'erreur de syntaxe")
    print("=" * 50)
    
    # Corriger la ligne 4
    if fix_line_4():
        # Tester la syntaxe
        if test_syntax():
            print("\n🎉 Erreur de syntaxe corrigée !")
            print("🚀 Vous pouvez maintenant relancer le scraper")
        else:
            print("\n❌ Erreur de syntaxe persistante")
            print("💡 Vérifiez manuellement le fichier")
    else:
        print("\n❌ Impossible de corriger l'erreur")

if __name__ == "__main__":
    main() 