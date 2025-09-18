#!/usr/bin/env python3
"""
Script pour restaurer le fichier original depuis un backup plus ancien
AVEC VÉRIFICATION FINALE AUTOMATIQUE
"""

import os
import shutil
from pathlib import Path

def list_all_backups():
    """Liste tous les backups disponibles"""
    
    print("📋 Backups disponibles:")
    print("=" * 50)
    
    backup_dir = Path("backups")
    if not backup_dir.exists():
        print("❌ Répertoire backups non trouvé")
        return []
    
    # Lister tous les backups de production_scraper.py
    backups = list(backup_dir.glob("production_scraper.py.backup_*"))
    
    if not backups:
        print("❌ Aucun backup trouvé")
        return []
    
    # Trier par date de modification (plus ancien en premier)
    backups.sort(key=lambda x: x.stat().st_mtime)
    
    for i, backup in enumerate(backups):
        mtime = backup.stat().st_mtime
        size = backup.stat().st_size
        print(f"   {i+1}. {backup.name}")
        print(f"      Taille: {size} bytes")
        print(f"      Date: {os.path.getmtime(backup)}")
        print()
    
    return backups

def test_backup_syntax(backup_path):
    """Teste la syntaxe d'un backup"""
    
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, str(backup_path), 'exec')
        return True
    except SyntaxError as e:
        print(f"   ❌ Erreur de syntaxe: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Autre erreur: {e}")
        return False

def find_best_backup():
    """Trouve le meilleur backup (plus ancien avec syntaxe valide)"""
    
    print("🔍 Recherche du meilleur backup...")
    
    backups = list_all_backups()
    if not backups:
        return None
    
    # Tester chaque backup en commençant par le plus ancien
    for i, backup in enumerate(backups):
        print(f"\n🧪 Test du backup {i+1}: {backup.name}")
        
        if test_backup_syntax(backup):
            print(f"✅ Backup {i+1} valide !")
            return backup
        else:
            print(f"❌ Backup {i+1} invalide")
    
    return None

def restore_from_backup(backup_path):
    """Restaure le fichier depuis un backup"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print(f"🔄 Restauration depuis: {backup_path}")
    
    # Créer un backup de l'état actuel (au cas où)
    current_backup = f"{file_path}.corrupted_backup"
    if os.path.exists(file_path):
        shutil.copy2(file_path, current_backup)
        print(f"💾 Backup de l'état actuel: {current_backup}")
    
    # Restaurer le fichier
    shutil.copy2(backup_path, file_path)
    
    print("✅ Fichier restauré")
    
    # Tester la syntaxe du fichier restauré
    if test_backup_syntax(file_path):
        print("✅ Syntaxe du fichier restauré valide")
        return True
    else:
        print("❌ Syntaxe du fichier restauré invalide")
        return False

def apply_minimal_fixes():
    """Applique les corrections minimales nécessaires"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print("\n🔧 Application des corrections minimales...")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Créer un backup avant modification
    backup_path = f"{file_path}.before_minimal_fixes"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Backup avant corrections: {backup_path}")
    
    # Corrections minimales seulement
    fixes_applied = 0
    
    # 1. Corriger les noms de colonnes (seulement si syntaxe valide)
    try:
        compile(content, file_path, 'exec')
        
        # Appliquer les corrections de colonnes
        old_content = content
        content = content.replace("shop.get('domain')", "shop.get('shop_url')")
        content = content.replace("shop['domain']", "shop['shop_url']")
        content = content.replace("shop.get('name')", "shop.get('shop_name')")
        content = content.replace("shop['name']", "shop['shop_name']")
        
        if content != old_content:
            fixes_applied += 1
            print("   ✅ Noms de colonnes corrigés")
        
        # Sauvegarder le fichier corrigé
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {fixes_applied} correction(s) appliquée(s)")
        return True
        
    except SyntaxError:
        print("   ⚠️ Syntaxe invalide, corrections de colonnes ignorées")
        return False

def final_verification():
    """VÉRIFICATION FINALE AUTOMATIQUE - S'assure qu'il ne reste plus d'erreurs"""
    
    file_path = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION FINALE AUTOMATIQUE")
    print("="*70)
    
    # 1. Test de syntaxe Python
    print("1️⃣ Test de syntaxe Python...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print("   ✅ Syntaxe Python valide")
        syntax_ok = True
    except SyntaxError as e:
        print(f"   ❌ Erreur de syntaxe: {e}")
        print(f"      Ligne: {e.lineno}, Colonne: {e.offset}")
        syntax_ok = False
    except Exception as e:
        print(f"   ❌ Autre erreur: {e}")
        syntax_ok = False
    
    # 2. Vérification des colonnes corrigées
    print("\n2️⃣ Vérification des colonnes corrigées...")
    column_checks = [
        ("shop.get('shop_url')", "✅ Colonne shop_url correcte"),
        ("shop['shop_url']", "✅ Colonne shop_url correcte"),
        ("shop.get('shop_name')", "✅ Colonne shop_name correcte"),
        ("shop['shop_name']", "✅ Colonne shop_name correcte"),
    ]
    
    columns_ok = True
    for pattern, message in column_checks:
        if pattern in content:
            print(f"   {message}")
        else:
            print(f"   ⚠️ Pattern non trouvé: {pattern}")
            columns_ok = False
    
    # 3. Vérification des anciennes colonnes (ne doivent plus exister)
    print("\n3️⃣ Vérification des anciennes colonnes (ne doivent plus exister)...")
    old_column_checks = [
        ("shop.get('domain')", "❌ Ancienne colonne domain trouvée"),
        ("shop['domain']", "❌ Ancienne colonne domain trouvée"),
        ("shop.get('name')", "❌ Ancienne colonne name trouvée"),
        ("shop['name']", "❌ Ancienne colonne name trouvée"),
    ]
    
    old_columns_found = False
    for pattern, message in old_column_checks:
        if pattern in content:
            print(f"   {message}")
            old_columns_found = True
    
    if not old_columns_found:
        print("   ✅ Aucune ancienne colonne trouvée")
    
    # 4. Vérification de la taille du fichier
    print("\n4️⃣ Vérification de la taille du fichier...")
    file_size = os.path.getsize(file_path)
    print(f"   📄 Taille du fichier: {file_size} bytes")
    
    if file_size > 1000:  # Fichier non vide
        print("   ✅ Fichier de taille normale")
        size_ok = True
    else:
        print("   ❌ Fichier trop petit (possiblement corrompu)")
        size_ok = False
    
    # 5. Résumé final
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION FINALE")
    print("="*70)
    
    all_checks_passed = syntax_ok and columns_ok and not old_columns_found and size_ok
    
    print(f"   • Syntaxe Python: {'✅' if syntax_ok else '❌'}")
    print(f"   • Colonnes corrigées: {'✅' if columns_ok else '❌'}")
    print(f"   • Anciennes colonnes: {'✅' if not old_columns_found else '❌'}")
    print(f"   • Taille du fichier: {'✅' if size_ok else '❌'}")
    
    print("\n" + "="*70)
    if all_checks_passed:
        print("🎉 VÉRIFICATION FINALE RÉUSSIE !")
        print("✅ Le fichier est prêt à être utilisé")
        print("🚀 Vous pouvez maintenant relancer le scraper")
    else:
        print("❌ VÉRIFICATION FINALE ÉCHOUÉE !")
        print("⚠️ Des problèmes persistent dans le fichier")
        print("💡 Vérifiez manuellement ou restaurez un autre backup")
    
    print("="*70)
    
    return all_checks_passed

def main():
    """Fonction principale"""
    print("🔄 Restauration du fichier original avec vérification finale")
    print("=" * 70)
    
    # 1. Trouver le meilleur backup
    best_backup = find_best_backup()
    
    if not best_backup:
        print("❌ Aucun backup valide trouvé")
        return False
    
    # 2. Restaurer depuis le backup
    if not restore_from_backup(best_backup):
        print("❌ Échec de la restauration")
        return False
    
    # 3. Appliquer les corrections minimales
    if not apply_minimal_fixes():
        print("⚠️ Corrections minimales non appliquées")
    
    # 4. VÉRIFICATION FINALE AUTOMATIQUE
    success = final_verification()
    
    return success

if __name__ == "__main__":
    success = main()
    
    # Code de sortie pour les scripts automatisés
    if success:
        print("\n✅ Script terminé avec succès")
        exit(0)
    else:
        print("\n❌ Script terminé avec des erreurs")
        exit(1) 