#!/usr/bin/env python3
"""
Script de mise à jour des credentials MyToolsPlan
Demande les credentials à l'utilisateur et les met à jour dans config.env
"""

import os
import sys
from pathlib import Path

def upsert_env_var(content: str, key: str, value: str) -> str:
    """Met à jour ou ajoute une variable d'environnement dans le contenu"""
    line = f"{key}={value}"
    lines = content.split('\n')
    
    # Chercher la ligne existante
    for i, existing_line in enumerate(lines):
        if existing_line.startswith(f"{key}="):
            lines[i] = line
            return '\n'.join(lines)
    
    # Si pas trouvé, ajouter à la fin
    if content.strip():
        return content.rstrip() + '\n' + line + '\n'
    else:
        return line + '\n'

def main():
    """Fonction principale"""
    try:
        # Chemin vers le fichier config.env
        config_path = Path(__file__).parent / "config.env"
        
        print("🔐 Configuration des credentials MyToolsPlan")
        print("=" * 50)
        
        # 1) Récupération des credentials auprès de l'utilisateur
        api_key = input("Entrez votre SAM_API_KEY: ").strip()
        user_id = input("Entrez votre SAM_USER_ID: ").strip()
        
        # Validation
        if not api_key:
            raise ValueError("SAM_API_KEY manquante")
        if not user_id:
            raise ValueError("SAM_USER_ID manquant")
        
        # Validation du format user_id (doit être numérique)
        try:
            int(user_id)
        except ValueError:
            raise ValueError("SAM_USER_ID doit être un nombre")
        
        # 2) Lecture du fichier config.env existant
        env_content = ""
        if config_path.exists():
            env_content = config_path.read_text(encoding='utf-8')
        
        # 3) Mise à jour des variables
        env_content = upsert_env_var(env_content, "SAM_API_KEY", api_key)
        env_content = upsert_env_var(env_content, "SAM_USER_ID", user_id)
        
        # 4) Sauvegarde du fichier
        config_path.write_text(env_content, encoding='utf-8')
        
        print("✅ Credentials mis à jour dans config.env")
        print(f"   SAM_USER_ID: {user_id}")
        print(f"   SAM_API_KEY: {api_key[:8]}...")
        
        # 5) Mise à jour des variables d'environnement pour la session courante
        os.environ['SAM_USER_ID'] = user_id
        os.environ['SAM_API_KEY'] = api_key
        
        print("✅ Variables d'environnement mises à jour pour cette session")
        
    except KeyboardInterrupt:
        print("\n❌ Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
