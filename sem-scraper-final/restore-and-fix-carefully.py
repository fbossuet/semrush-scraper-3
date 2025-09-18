#!/usr/bin/env python3
"""
Script pour restaurer le fichier original et appliquer les corrections prudemment
"""

import os
import shutil
from pathlib import Path

def restore_original():
    """Restaure le fichier original depuis le backup"""
    
    print("🔄 Restauration du fichier original...")
    
    # Chercher le backup le plus récent
    backup_dir = Path("backups")
    if not backup_dir.exists():
        print("❌ Répertoire backups non trouvé")
        return False
    
    # Lister tous les backups de production_scraper.py
    backups = list(backup_dir.glob("production_scraper.py.backup_*"))
    
    if not backups:
        print("❌ Aucun backup trouvé")
        return False
    
    # Prendre le backup le plus récent
    latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
    
    print(f"📦 Restauration depuis: {latest_backup}")
    
    # Restaurer le fichier
    original_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    shutil.copy2(latest_backup, original_path)
    
    print("✅ Fichier original restauré")
    return True

def apply_corrections_carefully():
    """Applique les corrections une par une avec vérification"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print("🔧 Application prudente des corrections...")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test de syntaxe avant modification
    try:
        compile(content, file_path, 'exec')
        print("✅ Syntaxe valide avant modification")
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe avant modification: {e}")
        return False
    
    # Correction 1: shop.get('domain') -> shop.get('shop_url')
    print("\n1️⃣ Correction: domain -> shop_url")
    
    # Créer un backup avant chaque modification
    backup_path = f"{file_path}.backup_step1"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Appliquer la correction
    new_content = content.replace("shop.get('domain')", "shop.get('shop_url')")
    new_content = new_content.replace("shop['domain']", "shop['shop_url']")
    
    # Tester la syntaxe après correction
    try:
        compile(new_content, file_path, 'exec')
        print("✅ Correction 1 réussie")
        content = new_content
    except SyntaxError as e:
        print(f"❌ Erreur après correction 1: {e}")
        # Restaurer
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return False
    
    # Correction 2: shop.get('name') -> shop.get('shop_name')
    print("\n2️⃣ Correction: name -> shop_name")
    
    backup_path = f"{file_path}.backup_step2"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_content = content.replace("shop.get('name')", "shop.get('shop_name')")
    new_content = new_content.replace("shop['name']", "shop['shop_name']")
    
    try:
        compile(new_content, file_path, 'exec')
        print("✅ Correction 2 réussie")
        content = new_content
    except SyntaxError as e:
        print(f"❌ Erreur après correction 2: {e}")
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return False
    
    # Sauvegarder le fichier final
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Toutes les corrections appliquées avec succès")
    return True

def test_final_syntax():
    """Teste la syntaxe finale"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print("\n🧪 Test de syntaxe finale...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print("✅ Syntaxe Python valide")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe finale: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔄 Restauration et correction prudente")
    print("=" * 50)
    
    # 1. Restaurer le fichier original
    if not restore_original():
        print("❌ Impossible de restaurer le fichier original")
        return
    
    # 2. Appliquer les corrections prudemment
    if apply_corrections_carefully():
        # 3. Tester la syntaxe finale
        if test_final_syntax():
            print("\n🎉 Fichier corrigé avec succès !")
            print("🚀 Vous pouvez maintenant relancer le scraper")
        else:
            print("\n❌ Erreur de syntaxe persistante")
    else:
        print("\n❌ Échec des corrections")

if __name__ == "__main__":
    main() 