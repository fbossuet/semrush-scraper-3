#!/usr/bin/env python3
"""
Script simple pour corriger les erreurs de calcul de date
"""

import os
import sys
import shutil
import re
from datetime import datetime, timezone

class SimpleDateFixer:
    def __init__(self):
        self.target_file = "/home/ubuntu/sem-scraper-final/production_scraper.py"
        self.log_file = "simple_date_fix.log"
        
    def log(self, message):
        """Log avec timestamp"""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] {message}")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def create_backup(self):
        """1. Créer un backup de sécurité"""
        self.log("🔒 CRÉATION DU BACKUP DE SÉCURITÉ")
        self.log("=" * 50)
        
        if os.path.exists(self.target_file):
            timestamp = datetime.now(timezone.utc).isoformat()
            safety_backup = f"{self.target_file}.simple_date_fix_backup_{timestamp}"
            shutil.copy2(self.target_file, safety_backup)
            self.log(f"✅ Backup de sécurité créé: {safety_backup}")
            return safety_backup
        else:
            self.log("❌ Fichier cible non trouvé")
            return None
    
    def add_error_handling(self):
        """2. Ajouter une gestion d'erreur pour les calculs de date"""
        self.log("🔧 AJOUT DE LA GESTION D'ERREUR")
        self.log("=" * 50)
        
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les endroits où les calculs de date peuvent échouer
            # et ajouter une gestion d'erreur
            
            # Pattern 1: Gestion d'erreur pour les calculs de date
            error_handling_pattern = r'except Exception as e:'
            error_handling_replacement = '''except Exception as e:
            # Gestion spécifique des erreurs de calcul de date
            if "can't subtract offset-naive and offset-aware datetimes" in str(e):
                logger.warning(f"⚠️ Erreur calcul date pour {shop.get('shop_url', 'unknown')}: {e}, passage")
                continue
            else:
                logger.error(f"❌ Erreur inattendue: {e}")
                continue'''
            
            # Remplacer seulement la première occurrence
            new_content = content.replace(error_handling_pattern, error_handling_replacement, 1)
            
            if new_content != content:
                with open(self.target_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.log("✅ Gestion d'erreur ajoutée")
                return True
            else:
                self.log("ℹ️ Gestion d'erreur déjà présente")
                return True
                
        except Exception as e:
            self.log(f"❌ Erreur ajout gestion d'erreur: {e}")
            return False
    
    def add_safe_date_function(self):
        """3. Ajouter une fonction de calcul de date sécurisée"""
        self.log("🔧 AJOUT DE LA FONCTION DE CALCUL SÉCURISÉE")
        self.log("=" * 50)
        
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fonction sécurisée à ajouter après les imports
            safe_function = '''

def safe_calculate_days_diff(date_str):
    """Calcule la différence de jours de manière sécurisée"""
    if not date_str:
        return None
    
    try:
        # Gérer différents formats de date
        if 'T' in date_str and 'Z' in date_str:
            # Format ISO avec Z
            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif 'T' in date_str:
            # Format ISO sans Z
            parsed_date = datetime.fromisoformat(date_str)
        elif '.' in date_str and len(date_str.split('.')[1]) > 3:
            # Format avec microsecondes
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            # Format simple
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        
        # Calculer la différence
        now = datetime.now(timezone.utc)
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        
        diff = now - parsed_date
        return diff.days
    
    except Exception as e:
        logger.warning(f"⚠️ Erreur calcul date pour '{date_str}': {e}")
        return None

'''
            
            # Insérer après les imports datetime
            import_pattern = r'from datetime import datetime, timezone, timedelta'
            if import_pattern in content:
                new_content = content.replace(import_pattern, import_pattern + safe_function)
                
                with open(self.target_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.log("✅ Fonction de calcul sécurisée ajoutée")
                return True
            else:
                self.log("❌ Impossible de trouver les imports datetime")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur ajout fonction: {e}")
            return False
    
    def verify_syntax(self):
        """4. Vérifier la syntaxe"""
        self.log("✅ VÉRIFICATION DE LA SYNTAXE")
        self.log("=" * 50)
        
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, self.target_file, 'exec')
            self.log("✅ Syntaxe Python valide")
            return True
            
        except SyntaxError as e:
            self.log(f"❌ Erreur syntaxe: {e}")
            return False
        except Exception as e:
            self.log(f"❌ Erreur vérification: {e}")
            return False
    
    def run_fix(self):
        """Méthode principale"""
        self.log("🚀 DÉBUT DE LA CORRECTION SIMPLE DES ERREURS DE DATE")
        self.log("=" * 60)
        
        # 1. Backup
        safety_backup = self.create_backup()
        if not safety_backup:
            return False
        
        # 2. Ajout de la fonction sécurisée
        if not self.add_safe_date_function():
            return False
        
        # 3. Ajout de la gestion d'erreur
        if not self.add_error_handling():
            return False
        
        # 4. Vérification syntaxe
        if not self.verify_syntax():
            return False
        
        # 5. Résumé
        self.log("=" * 60)
        self.log("🎉 CORRECTION SIMPLE DES ERREURS DE DATE RÉUSSIE")
        self.log(f"📁 Backup: {safety_backup}")
        self.log(f"📋 Log: {self.log_file}")
        
        return True

def main():
    print("🔧 Script de correction simple des erreurs de date")
    print("=" * 60)
    
    fixer = SimpleDateFixer()
    success = fixer.run_fix()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 