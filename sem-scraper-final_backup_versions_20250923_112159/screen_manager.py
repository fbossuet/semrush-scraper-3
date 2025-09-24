#!/usr/bin/env python3
"""
Gestionnaire de sessions screen pour les workers parallèles
Permet de voir, démarrer et arrêter les sessions screen
"""

import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Configuration du logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure le logging"""
    logger = logging.getLogger()
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

class ScreenManager:
    """Gestionnaire de sessions screen"""
    
    def __init__(self):
        self.screen_sessions = {}
        self.worker_sessions = [
            "workers-parallel",
            "api-server", 
            "dashboard",
            "monitor-workers"
        ]
    
    def clear_screen(self):
        """Efface l'écran"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_banner(self):
        """Affiche la bannière"""
        print("=" * 70)
        print("🖥️ GESTIONNAIRE DE SESSIONS SCREEN - TRENDTRACK")
        print("=" * 70)
        print(f"🕒 {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
    
    def print_main_menu(self):
        """Affiche le menu principal"""
        print("\n📋 MENU PRINCIPAL:")
        print("1. 👁️ Voir les sessions actives")
        print("2. 🚀 Démarrer une session")
        print("3. 🛑 Arrêter une session")
        print("4. 🔄 Redémarrer une session")
        print("5. 🧹 Nettoyer toutes les sessions")
        print("6. 📊 Statistiques des sessions")
        print("7. 📝 Voir les logs d'une session")
        print("8. 📖 Aide")
        print("9. 👋 Quitter")
        print("-" * 50)
    
    def get_user_choice(self, min_choice: int = 1, max_choice: int = 9) -> int:
        """Récupère le choix de l'utilisateur"""
        while True:
            try:
                choice = input(f"\nVotre choix ({min_choice}-{max_choice}): ").strip()
                if choice.isdigit():
                    choice = int(choice)
                    if min_choice <= choice <= max_choice:
                        return choice
                print(f"❌ Choix invalide, veuillez choisir entre {min_choice} et {max_choice}")
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                return 9
    
    def get_screen_sessions(self) -> List[Dict]:
        """Récupère la liste des sessions screen actives"""
        try:
            result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if result.returncode != 0:
                return []
            
            sessions = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if '.screen' in line or 'Detached' in line or 'Attached' in line:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        session_id = parts[0].split('.')[0] if '.' in parts[0] else parts[0]
                        session_name = parts[0].split('.')[1] if '.' in parts[0] else 'unnamed'
                        status = parts[1].strip('()')
                        
                        sessions.append({
                            'id': session_id,
                            'name': session_name,
                            'status': status,
                            'full_name': parts[0]
                        })
            
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération sessions: {e}")
            return []
    
    def show_active_sessions(self):
        """Affiche les sessions actives"""
        try:
            print("\n👁️ SESSIONS SCREEN ACTIVES:")
            print("-" * 50)
            
            sessions = self.get_screen_sessions()
            
            if not sessions:
                print("ℹ️ Aucune session screen active")
                return
            
            print(f"{'ID':<8} {'Nom':<20} {'Statut':<12} {'Actions'}")
            print("-" * 50)
            
            for session in sessions:
                status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
                print(f"{session['id']:<8} {session['name']:<20} {status_icon} {session['status']:<10}")
            
            print(f"\n📊 Total: {len(sessions)} session(s)")
            
        except Exception as e:
            print(f"❌ Erreur affichage sessions: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def start_session_menu(self):
        """Menu pour démarrer une session"""
        print("\n🚀 DÉMARRER UNE SESSION:")
        print("1. 🏭 Workers parallèles")
        print("2. 🌐 API Server")
        print("3. 📊 Dashboard")
        print("4. 👁️ Monitor Workers")
        print("5. 🔙 Retour")
        
        choice = self.get_user_choice(1, 5)
        
        if choice == 5:
            return
        
        session_configs = {
            1: {
                'name': 'workers-parallel',
                'command': 'python3 menu_workers.py',
                'description': 'Workers parallèles'
            },
            2: {
                'name': 'api-server',
                'command': 'python3 api_server.py',
                'description': 'API Server'
            },
            3: {
                'name': 'dashboard',
                'command': 'python3 dashboard.py',
                'description': 'Dashboard'
            },
            4: {
                'name': 'monitor-workers',
                'command': 'python3 monitor_parallel_workers.py',
                'description': 'Monitor Workers'
            }
        }
        
        config = session_configs[choice]
        
        # Vérifier si la session existe déjà
        sessions = self.get_screen_sessions()
        existing_session = next((s for s in sessions if s['name'] == config['name']), None)
        
        if existing_session:
            print(f"⚠️ Session '{config['name']}' existe déjà (ID: {existing_session['id']})")
            restart = input("Voulez-vous la redémarrer? (o/N): ").strip().lower()
            if restart in ['o', 'oui', 'y', 'yes']:
                self.stop_session_by_name(config['name'])
            else:
                return
        
        # Démarrer la session
        try:
            print(f"🚀 Démarrage de la session '{config['description']}'...")
            
            # Créer la commande screen
            screen_cmd = [
                'screen', '-dmS', config['name'], 
                'bash', '-c', f'cd /home/ubuntu/sem-scraper-final && {config["command"]}'
            ]
            
            result = subprocess.run(screen_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Session '{config['description']}' démarrée avec succès")
                
                # Attendre un peu et vérifier
                time.sleep(2)
                sessions = self.get_screen_sessions()
                new_session = next((s for s in sessions if s['name'] == config['name']), None)
                
                if new_session:
                    print(f"📋 ID de session: {new_session['id']}")
                    print(f"📋 Statut: {new_session['status']}")
                else:
                    print("⚠️ Session démarrée mais non visible dans la liste")
            else:
                print(f"❌ Erreur démarrage session: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Erreur démarrage session: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def stop_session_menu(self):
        """Menu pour arrêter une session"""
        print("\n🛑 ARRÊTER UNE SESSION:")
        
        sessions = self.get_screen_sessions()
        
        if not sessions:
            print("ℹ️ Aucune session active à arrêter")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print("\nSessions disponibles:")
        for i, session in enumerate(sessions, 1):
            status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
            print(f"{i}. {status_icon} {session['name']} (ID: {session['id']}, {session['status']})")
        
        print(f"{len(sessions) + 1}. 🔙 Retour")
        
        choice = self.get_user_choice(1, len(sessions) + 1)
        
        if choice == len(sessions) + 1:
            return
        
        session = sessions[choice - 1]
        
        # Confirmation
        confirm = input(f"\n⚠️ Arrêter la session '{session['name']}'? (o/N): ").strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print("❌ Annulé")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        # Arrêter la session
        try:
            print(f"🛑 Arrêt de la session '{session['name']}'...")
            
            # Envoyer Ctrl+C à la session
            subprocess.run(['screen', '-S', session['full_name'], '-X', 'stuff', '^C'], 
                         capture_output=True, text=True)
            
            time.sleep(2)
            
            # Tuer la session
            subprocess.run(['screen', '-S', session['full_name'], '-X', 'quit'], 
                         capture_output=True, text=True)
            
            print(f"✅ Session '{session['name']}' arrêtée")
            
        except Exception as e:
            print(f"❌ Erreur arrêt session: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def stop_session_by_name(self, session_name: str):
        """Arrête une session par son nom"""
        try:
            sessions = self.get_screen_sessions()
            session = next((s for s in sessions if s['name'] == session_name), None)
            
            if not session:
                return False
            
            # Envoyer Ctrl+C puis quitter
            subprocess.run(['screen', '-S', session['full_name'], '-X', 'stuff', '^C'], 
                         capture_output=True, text=True)
            time.sleep(2)
            subprocess.run(['screen', '-S', session['full_name'], '-X', 'quit'], 
                         capture_output=True, text=True)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt session {session_name}: {e}")
            return False
    
    def restart_session_menu(self):
        """Menu pour redémarrer une session"""
        print("\n🔄 REDÉMARRER UNE SESSION:")
        
        sessions = self.get_screen_sessions()
        
        if not sessions:
            print("ℹ️ Aucune session active à redémarrer")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print("\nSessions disponibles:")
        for i, session in enumerate(sessions, 1):
            status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
            print(f"{i}. {status_icon} {session['name']} (ID: {session['id']}, {session['status']})")
        
        print(f"{len(sessions) + 1}. 🔙 Retour")
        
        choice = self.get_user_choice(1, len(sessions) + 1)
        
        if choice == len(sessions) + 1:
            return
        
        session = sessions[choice - 1]
        
        # Confirmation
        confirm = input(f"\n⚠️ Redémarrer la session '{session['name']}'? (o/N): ").strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print("❌ Annulé")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        # Redémarrer la session
        try:
            print(f"🔄 Redémarrage de la session '{session['name']}'...")
            
            # Arrêter d'abord
            self.stop_session_by_name(session['name'])
            time.sleep(3)
            
            # Redémarrer selon le type
            session_configs = {
                'workers-parallel': 'python3 menu_workers.py',
                'api-server': 'python3 api_server.py',
                'dashboard': 'python3 dashboard.py',
                'monitor-workers': 'python3 monitor_parallel_workers.py'
            }
            
            if session['name'] in session_configs:
                command = session_configs[session['name']]
                screen_cmd = [
                    'screen', '-dmS', session['name'], 
                    'bash', '-c', f'cd /home/ubuntu/sem-scraper-final && {command}'
                ]
                
                result = subprocess.run(screen_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Session '{session['name']}' redémarrée avec succès")
                else:
                    print(f"❌ Erreur redémarrage: {result.stderr}")
            else:
                print(f"⚠️ Configuration inconnue pour '{session['name']}'")
                
        except Exception as e:
            print(f"❌ Erreur redémarrage session: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def clean_all_sessions(self):
        """Nettoie toutes les sessions"""
        print("\n🧹 NETTOYAGE DE TOUTES LES SESSIONS:")
        
        sessions = self.get_screen_sessions()
        
        if not sessions:
            print("ℹ️ Aucune session à nettoyer")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print(f"📋 {len(sessions)} session(s) trouvée(s):")
        for session in sessions:
            print(f"  - {session['name']} (ID: {session['id']}, {session['status']})")
        
        confirm = input(f"\n⚠️ Arrêter TOUTES les sessions? (o/N): ").strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print("❌ Annulé")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        # Arrêter toutes les sessions
        stopped_count = 0
        for session in sessions:
            try:
                print(f"🛑 Arrêt de '{session['name']}'...")
                if self.stop_session_by_name(session['name']):
                    stopped_count += 1
                time.sleep(1)
            except Exception as e:
                print(f"❌ Erreur arrêt '{session['name']}': {e}")
        
        print(f"\n✅ {stopped_count}/{len(sessions)} session(s) arrêtée(s)")
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_session_stats(self):
        """Affiche les statistiques des sessions"""
        try:
            print("\n📊 STATISTIQUES DES SESSIONS:")
            print("-" * 50)
            
            sessions = self.get_screen_sessions()
            
            if not sessions:
                print("ℹ️ Aucune session active")
                return
            
            # Compter par statut
            attached_count = len([s for s in sessions if s['status'] == 'Attached'])
            detached_count = len([s for s in sessions if s['status'] == 'Detached'])
            
            print(f"📈 Total sessions: {len(sessions)}")
            print(f"🟢 Attachées: {attached_count}")
            print(f"🟡 Détachées: {detached_count}")
            
            # Détails par session
            print(f"\n📋 DÉTAILS:")
            for session in sessions:
                status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
                print(f"  {status_icon} {session['name']} - ID: {session['id']} - {session['status']}")
            
        except Exception as e:
            print(f"❌ Erreur statistiques: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_session_logs(self):
        """Affiche les logs d'une session"""
        print("\n📝 LOGS D'UNE SESSION:")
        
        sessions = self.get_screen_sessions()
        
        if not sessions:
            print("ℹ️ Aucune session active")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print("\nSessions disponibles:")
        for i, session in enumerate(sessions, 1):
            status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
            print(f"{i}. {status_icon} {session['name']} (ID: {session['id']})")
        
        print(f"{len(sessions) + 1}. 🔙 Retour")
        
        choice = self.get_user_choice(1, len(sessions) + 1)
        
        if choice == len(sessions) + 1:
            return
        
        session = sessions[choice - 1]
        
        try:
            print(f"\n📝 Logs de la session '{session['name']}':")
            print("-" * 50)
            
            # Afficher les dernières lignes de la session
            result = subprocess.run([
                'screen', '-S', session['full_name'], '-X', 'hardcopy', '/tmp/screen_log.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Lire le fichier de log
                try:
                    with open('/tmp/screen_log.txt', 'r') as f:
                        lines = f.readlines()
                        # Afficher les 20 dernières lignes
                        for line in lines[-20:]:
                            print(line.rstrip())
                except FileNotFoundError:
                    print("ℹ️ Aucun log disponible")
            else:
                print("❌ Erreur récupération logs")
                
        except Exception as e:
            print(f"❌ Erreur logs: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_help(self):
        """Affiche l'aide"""
        print("\n📖 AIDE - GESTIONNAIRE DE SESSIONS SCREEN")
        print("=" * 60)
        print("🎯 OBJECTIF:")
        print("   Gérer les sessions screen pour les workers parallèles")
        print()
        print("📋 FONCTIONNALITÉS:")
        print("   1. 👁️ Voir les sessions - Liste toutes les sessions actives")
        print("   2. 🚀 Démarrer - Lance une nouvelle session screen")
        print("   3. 🛑 Arrêter - Arrête une session spécifique")
        print("   4. 🔄 Redémarrer - Redémarre une session existante")
        print("   5. 🧹 Nettoyer - Arrête toutes les sessions")
        print("   6. 📊 Statistiques - Affiche les stats des sessions")
        print("   7. 📝 Logs - Affiche les logs d'une session")
        print()
        print("🖥️ SESSIONS DISPONIBLES:")
        print("   🏭 workers-parallel - Menu des workers parallèles")
        print("   🌐 api-server - Serveur API")
        print("   📊 dashboard - Tableau de bord")
        print("   👁️ monitor-workers - Monitoring des workers")
        print()
        print("💡 CONSEILS:")
        print("   - Utilisez 'workers-parallel' pour lancer les workers")
        print("   - Les sessions 'Detached' tournent en arrière-plan")
        print("   - Utilisez 'screen -r <nom>' pour vous connecter à une session")
        print("   - Ctrl+A puis D pour détacher une session")
        print("   - Ctrl+C pour arrêter un processus dans une session")
        print("=" * 60)
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def run_menu(self):
        """Lance le menu principal"""
        while True:
            try:
                self.clear_screen()
                self.print_banner()
                self.print_main_menu()
                
                choice = self.get_user_choice()
                
                if choice == 1:  # Voir les sessions
                    self.show_active_sessions()
                
                elif choice == 2:  # Démarrer une session
                    self.start_session_menu()
                
                elif choice == 3:  # Arrêter une session
                    self.stop_session_menu()
                
                elif choice == 4:  # Redémarrer une session
                    self.restart_session_menu()
                
                elif choice == 5:  # Nettoyer toutes les sessions
                    self.clean_all_sessions()
                
                elif choice == 6:  # Statistiques
                    self.show_session_stats()
                
                elif choice == 7:  # Logs
                    self.show_session_logs()
                
                elif choice == 8:  # Aide
                    self.show_help()
                
                elif choice == 9:  # Quitter
                    print("\n👋 Au revoir!")
                    break
                
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                input("\nAppuyez sur Entrée pour continuer...")

def main():
    """Fonction principale"""
    setup_logging()
    
    try:
        manager = ScreenManager()
        manager.run_menu()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
