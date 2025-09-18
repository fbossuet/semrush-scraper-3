#!/usr/bin/env python3
"""
Menu interactif pour les workers parallèles
Interface simple et complète pour gérer les workers
"""

import asyncio
import json
import logging
import os
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

class WorkersMenu:
    """Menu interactif pour les workers parallèles"""
    
    def __init__(self):
        self.lock_dir = Path("locks")
        self.results_dir = Path("results")
        self.logs_dir = Path("logs")
        self.distribution_dir = Path(".")
        
    def clear_screen(self):
        """Efface l'écran"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_banner(self):
        """Affiche la bannière"""
        print("=" * 70)
        print("🏭 MENU WORKERS PARALLÈLES - TRENDTRACK")
        print("=" * 70)
        print(f"🕒 {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
    
    def print_main_menu(self):
        """Affiche le menu principal"""
        print("\n📋 MENU PRINCIPAL:")
        print("1. 🚀 Lancer les workers SEM")
        print("2. 🎯 Lancer le scraper TrendTrack")
        print("3. 🧹 Nettoyer les locks")
        print("4. 📁 Voir les fichiers récents")
        print("5. 🔍 Voir les logs")
        print("6. 📈 Monitoring en temps réel")
        print("7. 📊 Statistiques par statut")
        print("8. ⚙️ Configuration")
        print("9. 📖 Aide")
        print("10. 👋 Quitter")
        print("-" * 50)
    
    def get_user_choice(self, min_choice: int = 1, max_choice: int = 10) -> int:
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
                return 8
    
    def get_status_choice(self) -> str:
        """Récupère le choix du statut"""
        print("\n🎯 CHOIX DU STATUT:")
        print("1. 🆕 Boutiques vides (sans statut)")
        print("2. ⚠️ Boutiques partial (à compléter)")
        print("3. ⏳ Boutiques pending (en attente)")
        print("4. 🌐 Toutes les boutiques éligibles")
        print("5. 🔙 Retour au menu principal")
        
        choice = self.get_user_choice(1, 5)
        
        status_map = {
            1: "empty",
            2: "partial",
            3: "pending",
            4: "all"
        }
        
        if choice == 5:
            return None
        
        return status_map[choice]
    
    def get_workers_config(self) -> tuple:
        """Récupère la configuration des workers"""
        print("\n⚙️ CONFIGURATION DES WORKERS:")
        
        # Nombre de workers
        while True:
            try:
                num_workers = input("👷 Nombre de workers (1-6, défaut: 2): ").strip()
                if not num_workers:
                    num_workers = 2
                else:
                    num_workers = int(num_workers)
                    if 1 <= num_workers <= 6:
                        break
                    print("❌ Nombre de workers doit être entre 1 et 6")
            except ValueError:
                print("❌ Nombre invalide")
        
        # Max boutiques par worker
        while True:
            try:
                max_per_worker = input("🔢 Max boutiques par worker (défaut: illimité): ").strip()
                if not max_per_worker:
                    max_per_worker = None
                else:
                    max_per_worker = int(max_per_worker)
                    if max_per_worker > 0:
                        break
                    print("❌ Nombre doit être positif")
            except ValueError:
                print("❌ Nombre invalide")
        
        return num_workers, max_per_worker
    
    def show_configuration_summary(self, status: str, num_workers: int, max_per_worker: Optional[int]):
        """Affiche le résumé de la configuration"""
        status_names = {
            "empty": "boutiques vides",
            "partial": "boutiques partial",
            "pending": "boutiques pending",
            "all": "toutes les boutiques éligibles"
        }
        
        print("\n📋 RÉSUMÉ DE LA CONFIGURATION:")
        print(f"🎯 Statut: {status_names[status]}")
        print(f"👷 Workers: {num_workers}")
        if max_per_worker:
            print(f"🔢 Max par worker: {max_per_worker}")
        else:
            print("🔢 Max par worker: illimité")
        print("-" * 50)
    
    def confirm_launch(self) -> bool:
        """Demande confirmation pour le lancement"""
        confirm = input("\n✅ Confirmer le lancement? (o/N): ").strip().lower()
        return confirm in ["o", "oui", "y", "yes"]
    
    async def launch_workers(self, status: str, num_workers: int, max_per_worker: Optional[int]):
        """Lance les workers dans un screen"""
        try:
            import subprocess
            import time
            from datetime import datetime, timezone
            
            print(f"\n🚀 LANCEMENT DES WORKERS DANS UN SCREEN...")
            print("=" * 50)
            
            # Vérifier si une session existe déjà
            session_name = f"workers-{status}"
            result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if session_name in result.stdout:
                print(f"⚠️ Une session '{session_name}' existe déjà")
                print("Voulez-vous la tuer et en créer une nouvelle ? (y/N)")
                response = input().strip().lower()
                if response in ['y', 'yes', 'oui', 'o']:
                    subprocess.run(['screen', '-S', session_name, '-X', 'quit'])
                    print("✅ Ancienne session terminée")
                    time.sleep(2)
                else:
                    print("❌ Lancement annulé")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
            
            # Créer le dossier logs s'il n'existe pas
            os.makedirs("logs", exist_ok=True)
            
            # Nom du fichier log avec timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            log_file = f"logs/workers-{status}-{timestamp}.log"
            
            # Construire la commande
            cmd_parts = [
                "python3", "launch_workers_by_status.py", status,
                "--workers", str(num_workers)
            ]
            if max_per_worker:
                cmd_parts.extend(["--max-per-worker", str(max_per_worker)])
            
            cmd = " ".join(cmd_parts)
            
            # Lancer dans un screen
            screen_cmd = [
                'screen', '-dmS', session_name,
                '-L', '-Logfile', log_file,
                'bash', '-c', f'cd /home/ubuntu/sem-scraper-final && {cmd}'
            ]
            
            print(f"🖥️ Session screen: {session_name}")
            print(f"📝 Log file: {log_file}")
            print(f"🔧 Commande: {cmd}")
            print()
            
            # Exécuter la commande screen
            result = subprocess.run(screen_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ WORKERS LANCÉS AVEC SUCCÈS!")
                print("=" * 50)
                print("📋 Commandes utiles:")
                print(f"   screen -r {session_name}        # Attacher au scraper")
                print(f"   screen -ls                      # Voir toutes les sessions")
                print(f"   tail -f {log_file}              # Suivre les logs")
                print(f"   screen -S {session_name} -X quit # Arrêter le scraper")
                print()
                print("💡 Le scraper tourne maintenant en arrière-plan")
                print("💡 Vous pouvez fermer ce terminal sans problème")
            else:
                print(f"❌ Erreur lors du lancement: {result.stderr}")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        except Exception as e:
            print(f"❌ Erreur lors du lancement: {e}")
            input("\nAppuyez sur Entrée pour continuer...")
    
    async def launch_trendtrack_scraper(self):
        """Lance le scraper TrendTrack de production"""
        try:
            import subprocess
            import time
            from datetime import datetime, timezone
            
            print(f"\n🎯 LANCEMENT DU SCRAPER TRENDTRACK...")
            print("=" * 50)
            
            # Vérifier si une session existe déjà
            session_name = "trendtrack-scraper"
            result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if session_name in result.stdout:
                print(f"⚠️ Une session '{session_name}' existe déjà")
                print("Voulez-vous la tuer et en créer une nouvelle ? (y/N)")
                response = input().strip().lower()
                if response in ['y', 'yes', 'oui', 'o']:
                    subprocess.run(['screen', '-S', session_name, '-X', 'quit'])
                    print("✅ Ancienne session terminée")
                    time.sleep(2)
                else:
                    print("❌ Lancement annulé")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
            
            # Créer le dossier logs s'il n'existe pas
            os.makedirs("logs", exist_ok=True)
            
            # Nom du fichier log avec timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            log_file = f"logs/trendtrack-scraper-{timestamp}.log"
            
            # Construire la commande pour le scraper TrendTrack
            cmd = "node update-database.js"
            
            # Lancer dans un screen
            screen_cmd = [
                'screen', '-dmS', session_name,
                '-L', '-Logfile', log_file,
                'bash', '-c', f'cd /home/ubuntu/trendtrack-scraper-final && {cmd}'
            ]
            
            print(f"🖥️ Session screen: {session_name}")
            print(f"📝 Log file: {log_file}")
            print(f"🔧 Commande: {cmd}")
            print()
            
            # Exécuter la commande screen
            result = subprocess.run(screen_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ SCRAPER TRENDTRACK LANCÉ AVEC SUCCÈS!")
                print("=" * 50)
                print("📋 Commandes utiles:")
                print(f"   screen -r {session_name}        # Attacher au scraper")
                print(f"   screen -ls                      # Voir toutes les sessions")
                print(f"   tail -f {log_file}              # Suivre les logs")
                print(f"   screen -S {session_name} -X quit # Arrêter le scraper")
                print()
                print("💡 Le scraper TrendTrack tourne maintenant en arrière-plan")
                print("💡 Vous pouvez fermer ce terminal sans problème")
            else:
                print(f"❌ Erreur lors du lancement: {result.stderr}")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        except Exception as e:
            print(f"❌ Erreur lors du lancement: {e}")
            input("\nAppuyez sur Entrée pour continuer...")
    
    def clean_locks(self):
        """Nettoie les locks"""
        try:
            if self.lock_dir.exists():
                lock_files = list(self.lock_dir.glob("*.lock"))
                if lock_files:
                    for lock_file in lock_files:
                        lock_file.unlink()
                    print(f"✅ {len(lock_files)} fichier(s) de lock supprimé(s)")
                else:
                    print("ℹ️ Aucun fichier de lock trouvé")
            else:
                print("ℹ️ Répertoire locks n'existe pas")
                
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_recent_files(self):
        """Affiche les fichiers récents"""
        try:
            print("\n📁 FICHIERS RÉCENTS:")
            
            # Fichiers de résultats
            results_files = sorted(Path(".").glob("results_*.json"), 
                                 key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            if results_files:
                print("\n📄 Résultats récents:")
                for f in results_files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    print(f"  {f.name} ({mtime.strftime('%H:%M:%S')})")
            
            # Fichiers de distribution
            distribution_files = sorted(Path(".").glob("distribution_*.json"), 
                                      key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            if distribution_files:
                print("\n📦 Distributions récentes:")
                for f in distribution_files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    print(f"  {f.name} ({mtime.strftime('%H:%M:%S')})")
            
        except Exception as e:
            print(f"❌ Erreur fichiers récents: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_logs(self):
        """Affiche les logs"""
        try:
            print("\n🔍 LOGS:")
            
            # Logs dans le répertoire principal
            log_files = sorted(Path(".").glob("*.log"), 
                             key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            if log_files:
                print("\n📝 Logs récents:")
                for f in log_files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    size = f.stat().st_size
                    print(f"  {f.name} ({mtime.strftime('%H:%M:%S')}, {size} bytes)")
            
            # Logs dans le répertoire logs
            if self.logs_dir.exists():
                logs_files = sorted(self.logs_dir.glob("*.log"), 
                                  key=lambda f: f.stat().st_mtime, reverse=True)[:5]
                if logs_files:
                    print("\n📂 Logs dans logs/:")
                    for f in logs_files:
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        size = f.stat().st_size
                        print(f"  {f.name} ({mtime.strftime('%H:%M:%S')}, {size} bytes)")
            
        except Exception as e:
            print(f"❌ Erreur logs: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_configuration(self):
        """Affiche la configuration"""
        try:
            print("\n⚙️ CONFIGURATION ACTUELLE:")
            
            # Vérifier les répertoires
            dirs = ["locks", "logs", "results"]
            for dir_name in dirs:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    files_count = len(list(dir_path.glob("*")))
                    print(f"📁 {dir_name}/: {files_count} fichiers")
                else:
                    print(f"📁 {dir_name}/: n'existe pas")
            
            # Vérifier les fichiers principaux
            main_files = [
                "launch_workers_by_status.py",
                "production_scraper_parallel.py",
                "trendtrack_api_vps_adapted.py"
            ]
            
            print("\n📄 Fichiers principaux:")
            for file_name in main_files:
                file_path = Path(file_name)
                if file_path.exists():
                    print(f"✅ {file_name}")
                else:
                    print(f"❌ {file_name}")
            
        except Exception as e:
            print(f"❌ Erreur configuration: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def show_realtime_monitoring(self):
        """Affiche le monitoring en temps réel (comme simple_monitor.py)"""
        try:
            print("\n📈 MONITORING EN TEMPS RÉEL:")
            print("💡 Appuyez sur Ctrl+C pour quitter")
            print("-" * 50)
            
            import time
            
            while True:
                self.clear_screen()
                print("=" * 60)
                print("🏭 MONITEUR SIMPLE WORKERS PARALLÈLES")
                print("=" * 60)
                print(f"🕒 {datetime.now(timezone.utc).isoformat()}")
                print()
                
                # Statut général
                status = self.load_workers_status()
                if status:
                    print("📊 STATUT GÉNÉRAL:")
                    print(f"  👷 Workers configurés: {status.get('num_workers', 0)}")
                    print(f"  🚀 Démarrage: {status.get('start_time', 'N/A')}")
                    print(f"  🔄 Workers actifs: {status.get('active_processes', 0)}")
                    print()
                    
                    # Statut des workers
                    worker_status_dict = status.get('worker_status', {})
                    if worker_status_dict:
                        print("👷 STATUT DES WORKERS:")
                        for worker_id, worker_status in worker_status_dict.items():
                            status_icon = "🟢" if worker_status.get('status') == 'running' else "🔴"
                            print(f"  {status_icon} Worker {worker_id}: {worker_status.get('status', 'unknown')}")
                    else:
                        print("❌ Aucun worker en cours")
                        print()
                
                
                # Statut des locks
                lock_status = self.get_lock_status()
                if lock_status:
                    print("🔒 STATUT DES LOCKS:")
                    for worker_id, is_locked in lock_status.items():
                        lock_icon = "🔒" if is_locked else "🔓"
                        print(f"  {lock_icon} Worker {worker_id}: {'Verrouillé' if is_locked else 'Libre'}")
                    print()
                
                # Métriques de performance
                performance = self.calculate_performance_metrics()
                if performance:
                    print("📊 MÉTRIQUES DE PERFORMANCE:")
                    print(f"  🏪 Boutiques traitées: {performance['session_shops_processed']}")
                    print(f"  ✅ Métriques trouvées: {performance['session_metrics_found']}")
                    print(f"  ❌ Métriques non trouvées: {performance['session_metrics_not_found']}")
                    print(f"  🚀 Vitesse: {performance['session_speed_per_hour']:.1f} boutiques/h")
                    print(f"  ⏱️ Temps restant estimé: {performance['estimated_time_remaining']}")
                    print(f"  📊 Progression: {performance['progress_percentage']:.1f}%")
                    print()
                
                # Logs récents
                logs = self.get_recent_logs(3)
                if logs:
                    print("📝 LOGS RÉCENTS:")
                    for log_line in logs:
                        print(f"  {log_line.strip()}")
                    print()
                
                print("=" * 60)
                print("💡 Appuyez sur Ctrl+C pour quitter")
                print("=" * 60)
                
                time.sleep(5)  # Rafraîchir toutes les 5 secondes
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring arrêté")
        except Exception as e:
            print(f"❌ Erreur monitoring: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def get_lock_status(self):
        """Vérifie le statut des locks (comme le système original)"""
        lock_status = {}
        
        try:
            if self.lock_dir.exists():
                # Chercher les locks de workers (système original)
                for lock_file in self.lock_dir.glob("scraping_lock_worker_*.lock"):
                    try:
                        worker_id = int(lock_file.stem.split('_')[-1])
                        lock_status[worker_id] = True
                    except (ValueError, IndexError):
                        continue
                
                # Chercher aussi les locks globaux
                for lock_file in self.lock_dir.glob("*global*.lock"):
                    lock_status["global"] = True
                        
        except Exception as e:
            print(f"❌ Erreur vérification locks: {e}")
        
        return lock_status
    
    def get_recent_logs(self, lines: int = 5):
        """Récupère les logs récents"""
        try:
            if not self.logs_dir.exists():
                return []
            
            # Chercher les fichiers de logs les plus récents
            log_files = list(self.logs_dir.glob("*.log"))
            if not log_files:
                return []
            
            # Prendre le fichier le plus récent
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # Lire les dernières lignes
            with open(latest_log, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except Exception as e:
            print(f"❌ Erreur lecture logs: {e}")
            return []
    
    def load_workers_status(self):
        """Charge le statut des workers (comme le système original)"""
        try:
            # Chercher le fichier de statut original
            status_file = Path("parallel_workers_status.json")
            if not status_file.exists():
                # Si pas de fichier de statut, vérifier les sessions screen actives
                return self.get_screen_sessions_status()
            
            with open(status_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"❌ Erreur chargement statut workers: {e}")
            return None
    
    def get_screen_sessions_status(self):
        """Récupère le statut des sessions screen (comme auto_monitor.py)"""
        try:
            import subprocess
            
            result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            output = result.stdout
            
            # Chercher les sessions de workers
            worker_sessions = []
            for line in output.split('\n'):
                if 'workers-' in line or 'sem-scraper-worker-' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        session_name = parts[0].replace('\t', '')
                        status = "running" if '.' in parts[0] else "detached"
                        worker_sessions.append({
                            "name": session_name,
                            "status": status
                        })
            
            # Si pas de sessions screen, essayer de détecter depuis les logs
            if not worker_sessions:
                # Essayer de déterminer le nombre de workers depuis la distribution
                distribution = self.load_distribution()
                num_workers = 0
                if distribution and 'distribution' in distribution:
                    num_workers = len(distribution['distribution'])
                
                # Analyser les logs récents pour détecter les workers actifs
                latest_log_file = self.get_latest_log_file()
                active_workers = set()
                if latest_log_file:
                    try:
                        with open(latest_log_file, 'r', encoding='utf-8') as f:
                            log_content = f.read()
                            import re
                            # Chercher tous les workers dans le log
                            worker_matches = re.findall(r'Worker (\d+)', log_content)
                            active_workers = set(int(w) for w in worker_matches)
                    except:
                        pass
                
                # Utiliser le nombre de workers détectés dans les logs ou la distribution
                if active_workers:
                    detected_workers = max(active_workers) + 1
                    # Prendre le maximum entre la distribution et les workers détectés
                    num_workers = max(num_workers, detected_workers)
                
                # Calculer les boutiques traitées par worker
                worker_shops_processed = {}
                if latest_log_file:
                    try:
                        with open(latest_log_file, 'r', encoding='utf-8') as f:
                            log_content = f.read()
                            import re
                            # Compter les boutiques par worker
                            for worker_id in active_workers:
                                pattern = f'Worker {worker_id}: Boutique \\d+/\\d+'
                                matches = re.findall(pattern, log_content)
                                worker_shops_processed[str(worker_id)] = len(matches)
                    except:
                        pass
                
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "num_workers": num_workers,
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "worker_status": {
                        str(i): {
                            "status": "running" if i in active_workers else "starting",
                            "pid": "N/A",
                            "shops_processed": worker_shops_processed.get(i, 0),
                            "errors": 0
                        }
                        for i in range(num_workers)
                    },
                    "active_processes": len(active_workers) if active_workers else len(worker_sessions)
                }
            else:
                # Cas où il n'y a pas de workers détectés
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "num_workers": 0,
                    "start_time": "N/A",
                    "active_processes": 0,
                    "worker_status": {}
                }
                
        except Exception as e:
            print(f"❌ Erreur récupération sessions screen: {e}")
            return None
    
    def load_distribution(self):
        """Charge la distribution des boutiques (comme le système original)"""
        try:
            # D'abord chercher le fichier original shop_distribution.json
            original_file = Path("shop_distribution.json")
            if original_file.exists():
                with open(original_file, 'r') as f:
                    return json.load(f)
            
            # Sinon chercher les fichiers de distribution récents
            distribution_files = list(Path(".").glob("distribution_*.json"))
            if not distribution_files:
                return None
            
            # Prendre le fichier le plus récent
            latest_distribution = max(distribution_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_distribution, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"❌ Erreur chargement distribution: {e}")
            return None
    
    def get_latest_log_file(self):
        """Trouve le dernier fichier de log en cours d'écriture"""
        try:
            import os
            from pathlib import Path
            
            logs_dir = Path("/home/ubuntu/sem-scraper-final/logs")
            if not logs_dir.exists():
                return None
            
            # Trouver tous les fichiers de log d'aujourd'hui
            today = datetime.now(timezone.utc).isoformat()
            log_files = list(logs_dir.glob(f"workers_by_status_{today}_*.log"))
            
            if not log_files:
                return None
            
            # Retourner le plus récent
            return str(max(log_files, key=os.path.getmtime))
            
        except Exception as e:
            print(f"❌ Erreur recherche log: {e}")
            return None

    def calculate_performance_metrics(self):
        """Calcule les métriques de performance basées sur le dernier fichier de log en cours d'écriture"""
        try:
            metrics = {
                "total_shops_processed": 0,
                "total_metrics_found": 0,
                "total_metrics_not_found": 0,
                "total_metrics": 0,
                "session_shops_processed": 0,
                "session_metrics_found": 0,
                "session_metrics_not_found": 0,
                "session_start_time": None,
                "average_speed_per_hour": 0,
                "session_speed_per_hour": 0,
                "estimated_time_remaining": "N/A",
                "progress_percentage": 0
            }
            
            # Trouver le dernier fichier de log en cours d'écriture
            latest_log_file = self.get_latest_log_file()
            if not latest_log_file:
                return metrics
            
            # Lire le contenu du dernier fichier de log
            try:
                with open(latest_log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            except:
                return metrics

            # Analyser le contenu du log
            import re
            
            # 1. COMPTER LES BOUTIQUES TRAITÉES (pattern correct)
            # Pattern pour "Worker X: Boutique Y/Z" - chaque ligne = 1 boutique traitée
            shop_patterns = re.findall(r'Worker \d+: Boutique \d+/\d+', log_content)
            metrics["session_shops_processed"] = len(shop_patterns)
            
            # 2. COMPTER LES MÉTRIQUES TROUVÉES ET NON TROUVÉES (comptage correct)
            # Compter tous les ✅ sauf ceux des messages de worker
            all_checkmarks = log_content.count("✅")
            worker_checkmarks = log_content.count("✅ Worker")
            metrics["session_metrics_found"] = all_checkmarks - worker_checkmarks
            
            # Compter tous les ❌ sauf ceux des messages de worker et d'erreur
            all_crosses = log_content.count("❌")
            worker_crosses = log_content.count("❌ Worker")
            error_crosses = log_content.count("❌ Erreur")
            metrics["session_metrics_not_found"] = all_crosses - worker_crosses - error_crosses
            
            # Calculer les totaux (identiques aux session maintenant)
            metrics["total_shops_processed"] = metrics["session_shops_processed"]
            metrics["total_metrics_found"] = metrics["session_metrics_found"]
            metrics["total_metrics_not_found"] = metrics["session_metrics_not_found"]
            metrics["total_metrics"] = metrics["total_metrics_found"] + metrics["total_metrics_not_found"]
            
            # 3. CALCULER LA VITESSE (basée sur les timestamps réels)
            if metrics["session_shops_processed"] > 0:
                try:
                    from datetime import datetime, timezone
                    
                    # Extraire tous les timestamps du log
                    timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
                    timestamps = re.findall(timestamp_pattern, log_content)
                    
                    if len(timestamps) >= 2:
                        start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
                        end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
                        
                        duration_hours = (end_time - start_time).total_seconds() / 3600
                        if duration_hours > 0.01:  # Plus de 36 secondes
                            metrics["session_speed_per_hour"] = metrics["session_shops_processed"] / duration_hours
                        else:
                            metrics["session_speed_per_hour"] = 0
                    else:
                        metrics["session_speed_per_hour"] = 0
                        
                except Exception as e:
                    metrics["session_speed_per_hour"] = 0
            
            # Vitesse moyenne = vitesse de session
            metrics["average_speed_per_hour"] = metrics["session_speed_per_hour"]
            
            # 4. CALCULER LA PROGRESSION (basée sur les boutiques éligibles)
            distribution = self.load_distribution()
            if distribution:
                eligible_shops = distribution.get('eligible_shops', 0)
                if eligible_shops > 0:
                    metrics["progress_percentage"] = (metrics["session_shops_processed"] / eligible_shops) * 100
                    
                    # Estimation du temps restant
                    if metrics["session_speed_per_hour"] > 0:
                        remaining_shops = eligible_shops - metrics["session_shops_processed"]
                        hours_remaining = remaining_shops / metrics["session_speed_per_hour"]
                        metrics["estimated_time_remaining"] = f"{hours_remaining:.1f}h"
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erreur calcul métriques: {e}")
            return None
    
    def show_shop_status_stats(self):
        """Affiche les statistiques des boutiques par statut"""
        try:
            print("\n📊 STATISTIQUES DES BOUTIQUES PAR STATUT")
            print("=" * 60)
            
            # Connexion à la base de données
            import sqlite3
            db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
            
            if not os.path.exists(db_path):
                print("❌ Base de données non trouvée")
                return
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Requête pour compter les boutiques par statut
            query = """
            SELECT 
                scraping_status,
                COUNT(*) as count
            FROM shops 
            WHERE scraping_status IS NOT NULL 
            GROUP BY scraping_status
            ORDER BY count DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            if results:
                total_shops = sum(row[1] for row in results)
                print(f"📈 Total boutiques avec statut: {total_shops}")
                print()
                
                for status, count in results:
                    percentage = (count / total_shops) * 100
                    status_icon = {
                        'completed': '✅',
                        'partial': '⚠️',
                        'na': '🌐',
                        'failed': '❌',
                        'empty': '🆕'
                    }.get(status, '📊')
                    
                    print(f"  {status_icon} {status.upper()}: {count} boutiques ({percentage:.1f}%)")
                
                print()
                
                # Statistiques supplémentaires
                cursor.execute("SELECT COUNT(*) FROM shops WHERE scraping_status IS NULL OR scraping_status = ''")
                empty_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM shops")
                total_all = cursor.fetchone()[0]
                
                print(f"📊 RÉSUMÉ:")
                print(f"  🏪 Total boutiques: {total_all}")
                print(f"  📊 Avec statut: {total_shops}")
                print(f"  🆕 Sans statut: {empty_count}")
                print(f"  📈 Taux de traitement: {(total_shops/total_all*100):.1f}%")
                
            else:
                print("❌ Aucune donnée trouvée")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")

    def show_help(self):
        """Affiche l'aide"""
        print("\n📖 AIDE - MENU WORKERS PARALLÈLES")
        print("=" * 60)
        print("🎯 OBJECTIF:")
        print("   Interface simple pour gérer les workers parallèles")
        print()
        print("📋 MENU PRINCIPAL:")
        print("   1. 🚀 Lancer les workers SEM - Démarre le scraping SEM")
        print("   2. 🎯 Lancer le scraper TrendTrack - Démarre le scraper TrendTrack")
        print("   3. 🧹 Nettoyer les locks - Supprime les fichiers de lock")
        print("   4. 📁 Fichiers récents - Liste les fichiers récents")
        print("   5. 🔍 Logs - Affiche les logs disponibles")
        print("   6. 📈 Monitoring temps réel - Surveillance en direct")
        print("   7. 📊 Statistiques par statut - Affiche les boutiques par statut")
        print("   8. ⚙️ Configuration - Vérifie la configuration")
        print("   9. 📖 Aide - Affiche cette aide")
        print("   10. 👋 Quitter - Ferme le menu")
        print()
        print("🎯 TYPES DE SCRAPERS:")
        print("   🚀 Workers SEM - Scraping parallèle des métriques MyToolsPlan")
        print("   🎯 TrendTrack - Scraping des boutiques depuis trendtrack.io")
        print()
        print("🎯 STATUTS DISPONIBLES (Workers SEM):")
        print("   🆕 Empty   - Boutiques sans statut ou statut vide")
        print("   ⚠️ Partial - Boutiques avec statut 'partial'")
        print("   🌐 All     - Toutes les boutiques éligibles")
        print()
        print("⚙️ CONFIGURATION:")
        print("   👷 Workers - Nombre de workers parallèles (1-6)")
        print("   🔢 Max par worker - Limite le nombre de boutiques")
        print()
        print("📁 FICHIERS GÉNÉRÉS:")
        print("   📄 results_*.json - Résultats détaillés du scraping")
        print("   📦 distribution_*.json - Répartition des boutiques")
        print("   🔒 locks/*.lock - Fichiers de verrouillage")
        print("   📝 logs/*.log - Logs des workers")
        print()
        print("💡 CONSEILS:")
        print("   - Commencez par 'partial' pour tester")
        print("   - Utilisez 2-4 workers pour commencer")
        print("   - Limitez le nombre pour les tests")
        print("   - Nettoyez les locks en cas de problème")
        print("   - Utilisez Ctrl+C pour arrêter le scraping")
        print("   - Délai d'authentification automatique entre workers")
        print("   - Monitoring temps réel pour surveiller l'avancement")
        print("=" * 60)
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    async def run_menu(self):
        """Lance le menu principal"""
        while True:
            try:
                self.clear_screen()
                self.print_banner()
                self.print_main_menu()
                
                choice = self.get_user_choice()
                
                if choice == 1:  # Lancer les workers SEM
                    status = self.get_status_choice()
                    if status:
                        num_workers, max_per_worker = self.get_workers_config()
                        self.show_configuration_summary(status, num_workers, max_per_worker)
                        
                        if self.confirm_launch():
                            await self.launch_workers(status, num_workers, max_per_worker)
                
                elif choice == 2:  # Lancer le scraper TrendTrack
                    print("\n🎯 LANCEMENT DU SCRAPER TRENDTRACK")
                    print("=" * 50)
                    print("⚠️ ATTENTION: Ce scraper va traiter les boutiques TrendTrack")
                    print("📊 Il utilisera la base de données vide récemment créée")
                    print("🔧 Le scraper s'exécutera en arrière-plan dans un screen")
                    print()
                    
                    if self.confirm_launch():
                        await self.launch_trendtrack_scraper()
                
                elif choice == 3:  # Nettoyer les locks
                    self.clean_locks()
                
                elif choice == 4:  # Fichiers récents
                    self.show_recent_files()
                
                elif choice == 5:  # Logs
                    self.show_logs()
                
                elif choice == 6:  # Monitoring en temps réel
                    self.show_realtime_monitoring()
                
                elif choice == 7:  # Statistiques par statut
                    self.show_shop_status_stats()
                
                elif choice == 8:  # Configuration
                    self.show_configuration()
                
                elif choice == 9:  # Aide
                    self.show_help()
                
                elif choice == 10:  # Quitter
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
        menu = WorkersMenu()
        asyncio.run(menu.run_menu())
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    finally:
        print("\n👋 Au revoir!")

if __name__ == "__main__":
    main()
