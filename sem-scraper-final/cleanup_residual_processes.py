#!/usr/bin/env python3
"""
Script de surveillance et nettoyage des processus résiduels
Surveille les processus tail -f et autres processus suspects
Nettoyage sécurisé pour éviter de tout péter
"""

import subprocess
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessCleaner:
    """Nettoyeur de processus résiduels sécurisé"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.safe_processes = [
            'systemd',
            'kernel',
            'dbus',
            'network',
            'ssh',
            'cron',
            'rsyslog',
            'postfix',
            'apache',
            'nginx',
            'mysql',
            'postgresql',
            'redis',
            'mongodb',
            'docker',
            'kube',
            'containerd',
            'runc'
        ]
        
        self.suspicious_patterns = [
            r'tail -f.*\.log',
            r'python.*menu',
            r'python.*launch',
            r'bash.*test',
            r'node.*update-database',
            r'playwright',
            r'chromium.*headless'
        ]
    
    def get_processes(self) -> List[Dict[str, str]]:
        """Récupère la liste des processus"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ Erreur ps aux: {result.stderr}")
                return []
            
            processes = []
            lines = result.stdout.strip().split('\n')
            
            # Ignorer la ligne d'en-tête
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 11:
                    processes.append({
                        'user': parts[0],
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'vsz': parts[4],
                        'rss': parts[5],
                        'tty': parts[6],
                        'stat': parts[7],
                        'start': parts[8],
                        'time': parts[9],
                        'command': ' '.join(parts[10:])
                    })
            
            return processes
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération processus: {e}")
            return []
    
    def is_safe_process(self, process: Dict[str, str]) -> bool:
        """Vérifie si un processus est sûr à tuer"""
        command = process['command'].lower()
        
        # Vérifier les processus système sûrs
        for safe in self.safe_processes:
            if safe in command:
                return True
        
        # Vérifier les processus critiques
        critical_patterns = [
            'systemd',
            'kernel',
            'init',
            'dbus',
            'network',
            'ssh',
            'cron',
            'rsyslog'
        ]
        
        for pattern in critical_patterns:
            if pattern in command:
                return True
        
        return False
    
    def is_suspicious_process(self, process: Dict[str, str]) -> bool:
        """Vérifie si un processus est suspect"""
        command = process['command']
        
        # Vérifier les patterns suspects
        for pattern in self.suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        # Vérifier les processus tail -f anciens
        if 'tail -f' in command:
            # Extraire la date du nom de fichier si possible
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', command)
            if date_match:
                file_date = date_match.group(1)
                if file_date != self.today:
                    return True
        
        return False
    
    def get_tail_f_processes(self) -> List[Dict[str, str]]:
        """Récupère les processus tail -f"""
        processes = self.get_processes()
        tail_processes = []
        
        for process in processes:
            if 'tail -f' in process['command']:
                tail_processes.append(process)
        
        return tail_processes
    
    def get_suspicious_processes(self) -> List[Dict[str, str]]:
        """Récupère les processus suspects"""
        processes = self.get_processes()
        suspicious = []
        
        for process in processes:
            if self.is_suspicious_process(process) and not self.is_safe_process(process):
                suspicious.append(process)
        
        return suspicious
    
    def kill_process_safely(self, process: Dict[str, str], force: bool = False) -> bool:
        """Tue un processus de manière sécurisée"""
        try:
            pid = process['pid']
            command = process['command']
            
            # Vérifier une dernière fois que c'est sûr
            if self.is_safe_process(process):
                logger.warning(f"⚠️ Processus système détecté, ignoré: {command}")
                return False
            
            # Utiliser SIGTERM d'abord, puis SIGKILL si nécessaire
            signal = 'SIGKILL' if force else 'SIGTERM'
            
            logger.info(f"🔫 Envoi {signal} au processus {pid}: {command}")
            
            if force:
                result = subprocess.run(['kill', '-9', pid], capture_output=True, text=True)
            else:
                result = subprocess.run(['kill', '-15', pid], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Processus {pid} tué avec succès")
                return True
            else:
                logger.error(f"❌ Erreur tuer processus {pid}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur tuer processus: {e}")
            return False
    
    def cleanup_tail_f_processes(self, dry_run: bool = True) -> int:
        """Nettoie les processus tail -f anciens"""
        logger.info("🧹 Nettoyage des processus tail -f")
        
        tail_processes = self.get_tail_f_processes()
        killed_count = 0
        
        for process in tail_processes:
            command = process['command']
            pid = process['pid']
            
            # Vérifier si le fichier de log est ancien
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', command)
            if date_match:
                file_date = date_match.group(1)
                if file_date != self.today:
                    logger.info(f"🗑️ Processus tail -f ancien détecté: {command}")
                    
                    if not dry_run:
                        if self.kill_process_safely(process):
                            killed_count += 1
                    else:
                        logger.info(f"🔍 DRY RUN: Tuerait le processus {pid}")
                        killed_count += 1
                else:
                    logger.info(f"✅ Processus tail -f récent, conservé: {command}")
            else:
                logger.info(f"ℹ️ Processus tail -f sans date, conservé: {command}")
        
        return killed_count
    
    def cleanup_suspicious_processes(self, dry_run: bool = True) -> int:
        """Nettoie les processus suspects"""
        logger.info("🧹 Nettoyage des processus suspects")
        
        suspicious_processes = self.get_suspicious_processes()
        killed_count = 0
        
        for process in suspicious_processes:
            command = process['command']
            pid = process['pid']
            
            logger.info(f"🔍 Processus suspect détecté: {command}")
            
            if not dry_run:
                if self.kill_process_safely(process):
                    killed_count += 1
            else:
                logger.info(f"🔍 DRY RUN: Tuerait le processus {pid}")
                killed_count += 1
        
        return killed_count
    
    def run_cleanup(self, dry_run: bool = True) -> Dict[str, int]:
        """Exécute le nettoyage complet"""
        logger.info("🚀 DÉMARRAGE DU NETTOYAGE DES PROCESSUS RÉSIDUELS")
        logger.info("=" * 60)
        
        if dry_run:
            logger.info("🔍 MODE DRY RUN - Aucun processus ne sera tué")
        else:
            logger.info("⚠️ MODE RÉEL - Les processus seront tués")
        
        logger.info(f"📅 Date du jour: {self.today}")
        logger.info("=" * 60)
        
        # Nettoyage des processus tail -f
        tail_killed = self.cleanup_tail_f_processes(dry_run)
        
        # Nettoyage des processus suspects
        suspicious_killed = self.cleanup_suspicious_processes(dry_run)
        
        # Résumé
        total_killed = tail_killed + suspicious_killed
        
        logger.info("=" * 60)
        logger.info("📊 RÉSUMÉ DU NETTOYAGE")
        logger.info("=" * 60)
        logger.info(f"Processus tail -f nettoyés: {tail_killed}")
        logger.info(f"Processus suspects nettoyés: {suspicious_killed}")
        logger.info(f"Total processus nettoyés: {total_killed}")
        
        if dry_run:
            logger.info("🔍 Mode DRY RUN - Aucun processus n'a été tué")
        else:
            logger.info("✅ Nettoyage terminé")
        
        return {
            'tail_killed': tail_killed,
            'suspicious_killed': suspicious_killed,
            'total_killed': total_killed
        }
    
    def monitor_processes(self, interval: int = 60):
        """Surveille les processus en continu"""
        logger.info(f"👁️ Surveillance des processus (intervalle: {interval}s)")
        
        while True:
            try:
                # Afficher les processus suspects
                suspicious = self.get_suspicious_processes()
                if suspicious:
                    logger.warning(f"⚠️ {len(suspicious)} processus suspects détectés")
                    for process in suspicious:
                        logger.warning(f"   - {process['pid']}: {process['command']}")
                else:
                    logger.info("✅ Aucun processus suspect détecté")
                
                # Afficher les processus tail -f
                tail_processes = self.get_tail_f_processes()
                if tail_processes:
                    logger.info(f"📺 {len(tail_processes)} processus tail -f actifs")
                    for process in tail_processes:
                        logger.info(f"   - {process['pid']}: {process['command']}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Surveillance arrêtée par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"❌ Erreur surveillance: {e}")
                time.sleep(interval)

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nettoyage des processus résiduels')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Mode dry run (par défaut)')
    parser.add_argument('--force', action='store_true', default=False,
                       help='Mode réel (tue les processus)')
    parser.add_argument('--monitor', action='store_true', default=False,
                       help='Mode surveillance continue')
    parser.add_argument('--interval', type=int, default=60,
                       help='Intervalle de surveillance en secondes')
    
    args = parser.parse_args()
    
    cleaner = ProcessCleaner()
    
    if args.monitor:
        cleaner.monitor_processes(args.interval)
    else:
        dry_run = not args.force
        cleaner.run_cleanup(dry_run)

if __name__ == "__main__":
    main()
