#!/usr/bin/env python3
"""
Script de basculement entre les méthodes d'authentification
Permet de changer facilement entre MyToolsPlan et Noxtools
Créé le 23 septembre 2025
"""

import os
import sys
from pathlib import Path

def switch_auth_method(method: str):
    """
    Bascule entre les méthodes d'authentification
    
    Args:
        method: "mytoolsplan" ou "noxtools"
    """
    if method not in ["mytoolsplan", "noxtools"]:
        print("❌ Méthode invalide. Utilisez 'mytoolsplan' ou 'noxtools'")
        return False
    
    config_file = Path("config.env")
    
    if not config_file.exists():
        print("❌ Fichier config.env non trouvé")
        return False
    
    # Lire le fichier actuel
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Modifier la ligne AUTH_METHOD
    modified = False
    for i, line in enumerate(lines):
        if line.startswith('AUTH_METHOD='):
            lines[i] = f'AUTH_METHOD={method}\n'
            modified = True
            break
    
    if not modified:
        print("❌ Ligne AUTH_METHOD non trouvée dans config.env")
        return False
    
    # Sauvegarder le fichier modifié
    with open(config_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Méthode d'authentification changée vers: {method}")
    print(f"📋 Configuration mise à jour dans config.env")
    
    # Afficher les instructions
    if method == "mytoolsplan":
        print("\n🔧 Méthode MyToolsPlan activée:")
        print("  • Authentification sur app.mytoolsplan.com")
        print("  • Synchronisation avec sam.mytoolsplan.xyz")
        print("  • Credentials: MYTOOLSPLAN_USERNAME/PASSWORD")
    else:
        print("\n🔧 Méthode Noxtools activée:")
        print("  • Authentification sur noxtools.com")
        print("  • Navigation vers semrush1.semrush.pw")
        print("  • Credentials: NOXTOOLS_USERNAME/PASSWORD")
    
    return True

def show_current_method():
    """Affiche la méthode d'authentification actuelle"""
    config_file = Path("config.env")
    
    if not config_file.exists():
        print("❌ Fichier config.env non trouvé")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('AUTH_METHOD='):
                method = line.strip().split('=')[1]
                print(f"📋 Méthode d'authentification actuelle: {method}")
                
                if method == "mytoolsplan":
                    print("  • MyToolsPlan (méthode classique)")
                else:
                    print("  • Noxtools (nouvelle méthode)")
                return
    
    print("❌ AUTH_METHOD non trouvé dans config.env")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("🔧 Script de basculement des méthodes d'authentification")
        print("\nUsage:")
        print("  python3 switch_auth_method.py show          # Afficher la méthode actuelle")
        print("  python3 switch_auth_method.py mytoolsplan   # Basculer vers MyToolsPlan")
        print("  python3 switch_auth_method.py noxtools      # Basculer vers Noxtools")
        print("\nExemples:")
        print("  python3 switch_auth_method.py show")
        print("  python3 switch_auth_method.py noxtools")
        return
    
    command = sys.argv[1].lower()
    
    if command == "show":
        show_current_method()
    elif command in ["mytoolsplan", "noxtools"]:
        switch_auth_method(command)
    else:
        print(f"❌ Commande invalide: {command}")
        print("Utilisez 'show', 'mytoolsplan' ou 'noxtools'")

if __name__ == "__main__":
    main()
