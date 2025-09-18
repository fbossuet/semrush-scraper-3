#!/usr/bin/env python3
"""
Procédure de rollback pour les opérations critiques
Assure la sécurité des modifications majeures
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path
from backup_rollback_system import BackupRollbackSystem

class RollbackProcedure:
    """Procédure de rollback sécurisée"""
    
    def __init__(self, base_path: str = "/home/ubuntu/trendtrack-scraper-final"):
        self.base_path = Path(base_path)
        self.backup_system = BackupRollbackSystem(base_path)
        self.current_backup = None
    
    def start_operation(self, operation_name: str) -> str:
        """
        Démarre une opération critique avec sauvegarde automatique
        
        Args:
            operation_name: Nom de l'opération
            
        Returns:
            str: Nom de la sauvegarde créée
        """
        print(f"\n🚀 DÉMARRAGE DE L'OPÉRATION: {operation_name}")
        print("=" * 60)
        
        # Créer une sauvegarde automatique
        self.current_backup = self.backup_system.create_quick_backup(operation_name)
        print(f"✅ Sauvegarde automatique créée: {self.current_backup}")
        
        # Vérifier l'intégrité de la sauvegarde
        if not self.backup_system.verify_backup(self.current_backup):
            print("❌ ERREUR: La sauvegarde n'est pas valide!")
            sys.exit(1)
        
        print(f"✅ Sauvegarde vérifiée et valide")
        print(f"📝 Opération: {operation_name}")
        print(f"⏰ Début: {datetime.datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        
        return self.current_backup
    
    def rollback_operation(self, reason: str = "Erreur détectée") -> bool:
        """
        Effectue un rollback de l'opération en cours
        
        Args:
            reason: Raison du rollback
            
        Returns:
            bool: True si le rollback a réussi
        """
        if not self.current_backup:
            print("❌ ERREUR: Aucune sauvegarde disponible pour le rollback!")
            return False
        
        print(f"\n🔄 ROLLBACK EN COURS")
        print("=" * 60)
        print(f"📝 Raison: {reason}")
        print(f"📦 Sauvegarde: {self.current_backup}")
        print(f"⏰ Début rollback: {datetime.datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        
        # Effectuer le rollback
        success = self.backup_system.restore_backup(self.current_backup, confirm=True)
        
        if success:
            print("✅ ROLLBACK RÉUSSI")
            print("=" * 60)
            print(f"📦 Système restauré depuis: {self.current_backup}")
            print(f"⏰ Fin rollback: {datetime.datetime.now(timezone.utc).isoformat()}")
            print("=" * 60)
        else:
            print("❌ ÉCHEC DU ROLLBACK")
            print("=" * 60)
            print("🚨 ATTENTION: Le système pourrait être dans un état incohérent!")
            print("🔧 Intervention manuelle requise")
            print("=" * 60)
        
        return success
    
    def complete_operation(self, operation_name: str) -> bool:
        """
        Termine une opération avec succès
        
        Args:
            operation_name: Nom de l'opération
            
        Returns:
            bool: True si l'opération est terminée avec succès
        """
        print(f"\n✅ OPÉRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print(f"📝 Opération: {operation_name}")
        print(f"📦 Sauvegarde de sécurité: {self.current_backup}")
        print(f"⏰ Fin: {datetime.datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        
        # Optionnel: garder la sauvegarde ou la supprimer
        keep_backup = input("\n💾 Garder la sauvegarde de sécurité? (y/N): ").lower() == 'y'
        
        if not keep_backup and self.current_backup:
            try:
                import shutil
                backup_path = Path(self.backup_system.backup_dir) / self.current_backup
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    print(f"🗑️ Sauvegarde supprimée: {self.current_backup}")
            except Exception as e:
                print(f"⚠️ Impossible de supprimer la sauvegarde: {e}")
        
        return True
    
    def emergency_rollback(self, backup_name: str) -> bool:
        """
        Rollback d'urgence vers une sauvegarde spécifique
        
        Args:
            backup_name: Nom de la sauvegarde
            
        Returns:
            bool: True si le rollback a réussi
        """
        print(f"\n🚨 ROLLBACK D'URGENCE")
        print("=" * 60)
        print(f"📦 Sauvegarde cible: {backup_name}")
        print(f"⏰ Début: {datetime.datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        
        # Confirmation d'urgence
        confirm = input("⚠️ Êtes-vous sûr de vouloir effectuer un rollback d'urgence? (yes/NO): ")
        if confirm.lower() != 'yes':
            print("❌ Rollback d'urgence annulé")
            return False
        
        success = self.backup_system.restore_backup(backup_name, confirm=True)
        
        if success:
            print("✅ ROLLBACK D'URGENCE RÉUSSI")
            print("=" * 60)
            print(f"📦 Système restauré depuis: {backup_name}")
            print(f"⏰ Fin: {datetime.datetime.now(timezone.utc).isoformat()}")
            print("=" * 60)
        else:
            print("❌ ÉCHEC DU ROLLBACK D'URGENCE")
            print("=" * 60)
            print("🚨 ATTENTION: Le système pourrait être dans un état incohérent!")
            print("🔧 Intervention manuelle requise")
            print("=" * 60)
        
        return success

def main():
    """Fonction principale pour les opérations de rollback"""
    if len(sys.argv) < 2:
        print("Usage: python rollback_procedure.py <command> [args]")
        print("Commands:")
        print("  start <operation>  - Démarrer une opération avec sauvegarde")
        print("  rollback          - Rollback de l'opération en cours")
        print("  complete <op>     - Terminer une opération avec succès")
        print("  emergency <name>  - Rollback d'urgence vers une sauvegarde")
        return
    
    procedure = RollbackProcedure()
    command = sys.argv[1]
    
    if command == "start":
        if len(sys.argv) < 3:
            print("❌ Nom d'opération requis")
            return
        operation_name = sys.argv[2]
        backup_name = procedure.start_operation(operation_name)
        print(f"✅ Opération démarrée avec sauvegarde: {backup_name}")
    
    elif command == "rollback":
        reason = sys.argv[2] if len(sys.argv) > 2 else "Rollback manuel"
        success = procedure.rollback_operation(reason)
        if success:
            print("✅ Rollback réussi")
        else:
            print("❌ Échec du rollback")
    
    elif command == "complete":
        if len(sys.argv) < 3:
            print("❌ Nom d'opération requis")
            return
        operation_name = sys.argv[2]
        procedure.complete_operation(operation_name)
    
    elif command == "emergency":
        if len(sys.argv) < 3:
            print("❌ Nom de sauvegarde requis")
            return
        backup_name = sys.argv[2]
        success = procedure.emergency_rollback(backup_name)
        if success:
            print("✅ Rollback d'urgence réussi")
        else:
            print("❌ Échec du rollback d'urgence")
    
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()

