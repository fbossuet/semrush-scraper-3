#!/usr/bin/env python3
"""
Script simple pour corriger la ligne problématique dans la fonction d'éligibilité
"""

import os
import sys
import shutil
from datetime import datetime, timezone

class SimpleEligibilityFixer:
    def __init__(self):
        self.target_file = "/home/ubuntu/sem-scraper-final/trendtrack_api_vps_adapted.py"
        self.log_file = "simple_eligibility_fix.log"
        
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
            safety_backup = f"{self.target_file}.simple_eligibility_fix_backup_{timestamp}"
            shutil.copy2(self.target_file, safety_backup)
            self.log(f"✅ Backup de sécurité créé: {safety_backup}")
            return safety_backup
        else:
            self.log("❌ Fichier cible non trouvé")
            return None
    
    def fix_problematic_line(self):
        """2. Corriger la ligne problématique"""
        self.log("🔧 CORRECTION DE LA LIGNE PROBLÉMATIQUE")
        self.log("=" * 50)
        
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Chercher la ligne problématique
            problematic_line = None
            for i, line in enumerate(lines):
                if 'datetime.now(last_update_dt.tzinfo)' in line:
                    problematic_line = i
                    break
            
            if problematic_line is not None:
                self.log(f"✅ Ligne problématique trouvée: {problematic_line + 1}")
                
                # Remplacer la ligne problématique
                old_line = lines[problematic_line]
                new_line = old_line.replace(
                    'datetime.now(last_update_dt.tzinfo)',
                    'datetime.now(timezone.utc)'
                )
                
                lines[problematic_line] = new_line
                
                # Écrire le fichier modifié
                with open(self.target_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                self.log("✅ Ligne problématique corrigée")
                return True
            else:
                self.log("⚠️ Ligne problématique non trouvée")
                return True
                
        except Exception as e:
            self.log(f"❌ Erreur correction: {e}")
            return False
    
    def verify_syntax(self):
        """3. Vérifier la syntaxe"""
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
        self.log("🚀 DÉBUT DE LA CORRECTION SIMPLE DE LA FONCTION D'ÉLIGIBILITÉ")
        self.log("=" * 60)
        
        # 1. Backup
        safety_backup = self.create_backup()
        if not safety_backup:
            return False
        
        # 2. Correction de la ligne
        if not self.fix_problematic_line():
            return False
        
        # 3. Vérification syntaxe
        if not self.verify_syntax():
            return False
        
        # 4. Résumé
        self.log("=" * 60)
        self.log("🎉 CORRECTION SIMPLE DE LA FONCTION D'ÉLIGIBILITÉ RÉUSSIE")
        self.log(f"📁 Backup: {safety_backup}")
        self.log(f"📋 Log: {self.log_file}")
        
        return True

def main():
    print("🔧 Script de correction simple de la fonction d'éligibilité")
    print("=" * 60)
    
    fixer = SimpleEligibilityFixer()
    success = fixer.run_fix()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 