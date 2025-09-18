#!/usr/bin/env python3
"""
Lanceur de workers parallèles pour le scraping MyToolsPlan
Gère le démarrage, l'arrêt et le monitoring des workers
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import psutil

# Configuration du logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure le logging"""
    logger = logging.getLogger()
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Handler fichier
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / f"parallel_workers_{datetime.now(timezone.utc).isoformat()}.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # Désactiver les logs de playwright
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class ParallelWorkerManager:
    """Gestionnaire des workers parallèles"""
    
    def __init__(self, num_workers: int = 2):
        self.num_workers = num_workers
        self.worker_processes: Dict[int, subprocess.Popen] = {}
        self.worker_status: Dict[int, Dict] = {}
        self.start_time = None
        self.status_file = Path("parallel_workers_status.json")
        self.pid_file = Path("parallel_workers.pid")
        
        # Créer les répertoires nécessaires
        Path("logs").mkdir(exist_ok=True)
        Path("locks").mkdir(exist_ok=True)
        Path("results").mkdir(exist_ok=True)
    
    def save_status(self):
        """Sauvegarde le statut des workers"""
        try:
            status_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "num_workers": self.num_workers,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "worker_status": self.worker_status,
                "active_processes": len([p for p in self.worker_processes.values() if p.poll() is None])
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde statut: {e}")
    
    def load_status(self) -> bool:
        """Charge le statut des workers"""
        try:
            if not self.status_file.exists():
                return False
            
            with open(self.status_file, 'r') as f:
                status_data = json.load(f)
            
            self.num_workers = status_data.get("num_workers", 2)
            self.worker_status = status_data.get("worker_status", {})
            
            if status_data.get("start_time"):
                self.start_time = datetime.fromisoformat(status_data["start_time"])
            
            logger.info(f"📂 Statut chargé: {len(self.worker_status)} workers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement statut: {e}")
            return False
    
    def start_workers(self) -> bool:
        """Démarre les workers parallèles"""
        try:
            logger.info(f"🚀 Démarrage de {self.num_workers} workers parallèles...")
            
            # Vérifier si des workers sont déjà en cours
            if self.worker_processes:
                logger.warning("⚠️ Des workers sont déjà en cours")
                return False
            
            # Démarrer les workers
            for worker_id in range(self.num_workers):
                logger.info(f"👷 Démarrage Worker {worker_id}...")
                
                # Commande pour lancer le worker
                cmd = [
                    sys.executable, 
                    "production_scraper_parallel.py",
                    "--worker-id", str(worker_id),
                    "--num-workers", str(self.num_workers)
                ]
                
                # Lancer le processus
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd()
                )
                
                self.worker_processes[worker_id] = process
                self.worker_status[worker_id] = {
                    "pid": process.pid,
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "status": "starting",
                    "shops_processed": 0,
                    "errors": 0
                }
                
                logger.info(f"✅ Worker {worker_id} démarré (PID: {process.pid})")
            
            self.start_time = datetime.now(timezone.utc)
            self.save_status()
            
            # Sauvegarder le PID du gestionnaire
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            logger.info(f"🎉 {self.num_workers} workers démarrés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage workers: {e}")
            return False
    
    def stop_workers(self) -> bool:
        """Arrête tous les workers"""
        try:
            logger.info("🛑 Arrêt des workers...")
            
            stopped_count = 0
            for worker_id, process in self.worker_processes.items():
                try:
                    if process.poll() is None:  # Processus encore en cours
                        logger.info(f"🛑 Arrêt Worker {worker_id} (PID: {process.pid})...")
                        
                        # Essayer d'arrêter proprement
                        process.terminate()
                        
                        # Attendre 5 secondes
                        try:
                            process.wait(timeout=5)
                            logger.info(f"✅ Worker {worker_id} arrêté proprement")
                        except subprocess.TimeoutExpired:
                            # Forcer l'arrêt
                            process.kill()
                            logger.warning(f"⚠️ Worker {worker_id} forcé à s'arrêter")
                        
                        stopped_count += 1
                    
                    # Mettre à jour le statut
                    self.worker_status[worker_id]["status"] = "stopped"
                    self.worker_status[worker_id]["stop_time"] = datetime.now(timezone.utc).isoformat()
                    
                except Exception as e:
                    logger.error(f"❌ Erreur arrêt Worker {worker_id}: {e}")
            
            self.worker_processes.clear()
            self.save_status()
            
            # Supprimer le fichier PID
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info(f"🎉 {stopped_count} workers arrêtés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt workers: {e}")
            return False
    
    def monitor_workers(self) -> bool:
        """Surveille les workers en cours"""
        try:
            logger.info("👁️ Surveillance des workers...")
            
            active_workers = 0
            for worker_id, process in self.worker_processes.items():
                if process.poll() is None:  # Processus encore en cours
                    active_workers += 1
                    
                    # Mettre à jour le statut
                    self.worker_status[worker_id]["status"] = "running"
                    
                    # Vérifier l'utilisation des ressources
                    try:
                        proc = psutil.Process(process.pid)
                        cpu_percent = proc.cpu_percent()
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        
                        self.worker_status[worker_id]["cpu_percent"] = cpu_percent
                        self.worker_status[worker_id]["memory_mb"] = memory_mb
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                else:
                    # Processus terminé
                    return_code = process.returncode
                    self.worker_status[worker_id]["status"] = "finished"
                    self.worker_status[worker_id]["return_code"] = return_code
                    self.worker_status[worker_id]["end_time"] = datetime.now(timezone.utc).isoformat()
                    
                    if return_code == 0:
                        logger.info(f"✅ Worker {worker_id} terminé avec succès")
                    else:
                        logger.error(f"❌ Worker {worker_id} terminé avec erreur (code: {return_code})")
            
            self.save_status()
            
            if active_workers == 0:
                logger.info("🏁 Tous les workers sont terminés")
                return False
            
            logger.info(f"👁️ {active_workers} workers actifs")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur surveillance: {e}")
            return False

    def print_workers_recap(self):
        """Affiche un mini récap par worker (durée, shops traités, erreurs)."""
        try:
            logger.info("\n======================================================================")
            logger.info("📊 RÉCAP PAR WORKER")
            logger.info("======================================================================")
            for worker_id, status in sorted(self.worker_status.items()):
                start = status.get("start_time")
                end = status.get("end_time") or status.get("stop_time")
                shops = status.get("shops_processed", 0)
                errors = status.get("errors", 0)
                return_code = status.get("return_code", "N/A")
                # Durée lisible si timestamps ISO dispo
                duration_str = "N/A"
                try:
                    if start and end:
                        from datetime import datetime, timezone
                        start_dt = datetime.fromisoformat(start)
                        end_dt = datetime.fromisoformat(end)
                        duration = (end_dt - start_dt).total_seconds()
                        duration_str = f"{int(duration)}s"
                except Exception:
                    pass
                logger.info(f"👷 Worker {worker_id}: durée={duration_str}, shops={shops}, erreurs={errors}, code_retour={return_code}")
        except Exception as e:
            logger.error(f"❌ Erreur récap workers: {e}")
    
    def get_worker_logs(self, worker_id: int) -> List[str]:
        """Récupère les logs d'un worker"""
        try:
            if worker_id not in self.worker_processes:
                return []
            
            process = self.worker_processes[worker_id]
            if process.poll() is None:
                # Processus encore en cours, pas de logs disponibles
                return []
            
            # Lire les logs depuis les fichiers
            log_dir = Path("logs")
            log_files = list(log_dir.glob(f"worker_{worker_id}_*.log"))
            
            logs = []
            for log_file in sorted(log_files):
                try:
                    with open(log_file, 'r') as f:
                        logs.extend(f.readlines())
                except Exception as e:
                    logger.error(f"❌ Erreur lecture logs Worker {worker_id}: {e}")
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération logs Worker {worker_id}: {e}")
            return []
    
    def cleanup(self):
        """Nettoyage des fichiers temporaires"""
        try:
            # Supprimer les locks
            lock_dir = Path("locks")
            if lock_dir.exists():
                for lock_file in lock_dir.glob("*.lock"):
                    lock_file.unlink()
            
            # Supprimer le fichier de statut
            if self.status_file.exists():
                self.status_file.unlink()
            
            # Supprimer le fichier PID
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info("🧹 Nettoyage terminé")
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage: {e}")

def signal_handler(signum, frame):
    """Gestionnaire de signaux pour l'arrêt propre"""
    logger.info(f"📡 Signal {signum} reçu, arrêt des workers...")
    
    # Arrêter les workers
    manager.stop_workers()
    manager.cleanup()
    
    logger.info("👋 Arrêt terminé")
    sys.exit(0)

async def main():
    """Fonction principale"""
    global manager
    
    setup_logging()
    logger.info("🏭 DÉMARAGE DU GESTIONNAIRE DE WORKERS PARALLÈLES")
    
    # Configuration des signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Créer le gestionnaire
    num_workers = 2  # Commencer par 2 workers
    manager = ParallelWorkerManager(num_workers)
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            # Démarrer les workers
            if manager.start_workers():
                logger.info("🎉 Workers démarrés avec succès")
                
                # Surveillance continue
                while manager.monitor_workers():
                    await asyncio.sleep(10)  # Vérifier toutes les 10 secondes

                logger.info("🏁 Surveillance terminée")
                # Impression du récapitulatif en fin de run
                manager.print_workers_recap()
            else:
                logger.error("❌ Échec du démarrage des workers")
        
        elif command == "stop":
            # Arrêter les workers
            if manager.load_status():
                manager.stop_workers()
                manager.cleanup()
                logger.info("🛑 Workers arrêtés")
            else:
                logger.info("ℹ️ Aucun worker en cours")
        
        elif command == "status":
            # Afficher le statut
            if manager.load_status():
                logger.info("📊 STATUT DES WORKERS:")
                for worker_id, status in manager.worker_status.items():
                    logger.info(f"  Worker {worker_id}: {status['status']} (PID: {status.get('pid', 'N/A')})")
                # Mini récap par worker
                manager.print_workers_recap()
            else:
                logger.info("ℹ️ Aucun worker en cours")
        
        elif command == "restart":
            # Redémarrer les workers
            if manager.load_status():
                manager.stop_workers()
                await asyncio.sleep(2)
            
            if manager.start_workers():
                logger.info("🔄 Workers redémarrés avec succès")
            else:
                logger.error("❌ Échec du redémarrage des workers")
        
        else:
            logger.error(f"❌ Commande inconnue: {command}")
            logger.info("💡 Commandes disponibles: start, stop, status, restart")
    
    else:
        # Mode interactif
        logger.info("🎮 MODE INTERACTIF")
            logger.info("ℹ️ Échelonnage: le lancement des workers est effectué par paliers (ex: +10s par worker) afin d'éviter les pics de charge et les collisions de session.")
        logger.info("💡 Commandes disponibles:")
        logger.info("  - start: Démarrer les workers")
        logger.info("  - stop: Arrêter les workers")
        logger.info("  - status: Afficher le statut")
        logger.info("  - restart: Redémarrer les workers")
        logger.info("  - quit: Quitter")
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command == "start":
                    if manager.start_workers():
                        logger.info("🎉 Workers démarrés")
                    else:
                        logger.error("❌ Échec du démarrage")
                
                elif command == "stop":
                    if manager.load_status():
                        manager.stop_workers()
                        logger.info("🛑 Workers arrêtés")
                    else:
                        logger.info("ℹ️ Aucun worker en cours")
                
                elif command == "status":
                    if manager.load_status():
                        logger.info("📊 STATUT DES WORKERS:")
                        for worker_id, status in manager.worker_status.items():
                            logger.info(f"  Worker {worker_id}: {status['status']}")
                        # Mini récap par worker
                        manager.print_workers_recap()
                    else:
                        logger.info("ℹ️ Aucun worker en cours")
                
                elif command == "restart":
                    if manager.load_status():
                        manager.stop_workers()
                        await asyncio.sleep(2)
                    
                    if manager.start_workers():
                        logger.info("🔄 Workers redémarrés")
                    else:
                        logger.error("❌ Échec du redémarrage")
                
                elif command in ["quit", "exit", "q"]:
                    if manager.load_status():
                        manager.stop_workers()
                    manager.cleanup()
                    logger.info("👋 Au revoir!")
                    break
                
                else:
                    logger.info("❌ Commande inconnue")
                
            except KeyboardInterrupt:
                logger.info("\n📡 Interruption clavier, arrêt...")
                if manager.load_status():
                    manager.stop_workers()
                manager.cleanup()
                break
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(main())
