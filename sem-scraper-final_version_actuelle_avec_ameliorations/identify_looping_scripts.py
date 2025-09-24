#!/usr/bin/env python3
"""
Script pour identifier et nettoyer les scripts qui tournent en boucle
Analyse les scripts de menu et de lancement pour détecter les boucles infinies
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

class LoopingScriptDetector:
    """Détecteur de scripts en boucle"""
    
    def __init__(self):
        self.script_dir = Path(".")
        self.looping_patterns = [
            r'while\s+True:',
            r'while\s+1:',
            r'for\s+.*\s+in\s+range\(.*\):',
            r'while\s+.*:',
            r'input\(.*\)',
            r'menu\(\)',
            r'show_menu\(\)',
            r'run_menu\(\)',
            r'\.run\(\)',
            r'asyncio\.run\(\)',
            r'subprocess\.run\(.*python.*\)',
            r'os\.system\(.*python.*\)'
        ]
        
        self.suspicious_files = [
            'menu_workers.py',
            'menu_principal.py',
            'launch_parallel_workers.py',
            'launch_parallel_scrapers.py',
            'launch_workers_by_status.py',
            'quick_launch.py',
            'quick_start_parallel.py'
        ]
    
    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """Analyse un fichier pour détecter les boucles"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'file': str(file_path),
                'size': len(content),
                'lines': len(content.split('\n')),
                'loops_found': [],
                'suspicious_calls': [],
                'risk_level': 'low'
            }
            
            # Détecter les patterns de boucle
            for pattern in self.looping_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis['loops_found'].extend(matches)
            
            # Détecter les appels suspects
            suspicious_calls = [
                r'subprocess\.run\([^)]*python[^)]*\)',
                r'os\.system\([^)]*python[^)]*\)',
                r'exec\([^)]*python[^)]*\)',
                r'eval\([^)]*python[^)]*\)'
            ]
            
            for pattern in suspicious_calls:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis['suspicious_calls'].extend(matches)
            
            # Calculer le niveau de risque
            if analysis['loops_found'] and analysis['suspicious_calls']:
                analysis['risk_level'] = 'high'
            elif analysis['loops_found'] or analysis['suspicious_calls']:
                analysis['risk_level'] = 'medium'
            
            return analysis
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'risk_level': 'unknown'
            }
    
    def find_looping_scripts(self) -> List[Dict[str, any]]:
        """Trouve tous les scripts suspects"""
        results = []
        
        for file_name in self.suspicious_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                analysis = self.analyze_file(file_path)
                results.append(analysis)
        
        return results
    
    def check_running_processes(self) -> List[Dict[str, str]]:
        """Vérifie les processus en cours"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode != 0:
                return []
            
            processes = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines[1:]:  # Ignorer l'en-tête
                parts = line.split()
                if len(parts) >= 11:
                    command = ' '.join(parts[10:])
                    
                    # Vérifier si c'est un script suspect
                    for suspicious_file in self.suspicious_files:
                        if suspicious_file in command:
                            processes.append({
                                'pid': parts[1],
                                'user': parts[0],
                                'command': command,
                                'file': suspicious_file
                            })
            
            return processes
            
        except Exception as e:
            print(f"❌ Erreur vérification processus: {e}")
            return []
    
    def kill_looping_processes(self, dry_run: bool = True) -> int:
        """Tue les processus en boucle"""
        processes = self.check_running_processes()
        killed_count = 0
        
        for process in processes:
            pid = process['pid']
            command = process['command']
            file_name = process['file']
            
            print(f"🔍 Processus suspect détecté: {file_name}")
            print(f"   PID: {pid}")
            print(f"   Commande: {command}")
            
            if not dry_run:
                try:
                    # Essayer SIGTERM d'abord
                    subprocess.run(['kill', '-15', pid], check=True)
                    print(f"✅ Signal SIGTERM envoyé au processus {pid}")
                    killed_count += 1
                except subprocess.CalledProcessError:
                    try:
                        # Si SIGTERM échoue, utiliser SIGKILL
                        subprocess.run(['kill', '-9', pid], check=True)
                        print(f"✅ Signal SIGKILL envoyé au processus {pid}")
                        killed_count += 1
                    except subprocess.CalledProcessError:
                        print(f"❌ Impossible de tuer le processus {pid}")
            else:
                print(f"🔍 DRY RUN: Tuerait le processus {pid}")
                killed_count += 1
        
        return killed_count
    
    def generate_report(self) -> str:
        """Génère un rapport complet"""
        report = []
        report.append("=" * 80)
        report.append("🔍 RAPPORT D'ANALYSE DES SCRIPTS EN BOUCLE")
        report.append("=" * 80)
        report.append("")
        
        # Analyser les fichiers
        report.append("📁 ANALYSE DES FICHIERS SUSPECTS:")
        report.append("-" * 50)
        
        scripts_analysis = self.find_looping_scripts()
        for analysis in scripts_analysis:
            if 'error' in analysis:
                report.append(f"❌ {analysis['file']}: Erreur - {analysis['error']}")
                continue
            
            report.append(f"📄 {analysis['file']}")
            report.append(f"   Taille: {analysis['size']} caractères, {analysis['lines']} lignes")
            report.append(f"   Niveau de risque: {analysis['risk_level'].upper()}")
            
            if analysis['loops_found']:
                report.append(f"   🔄 Boucles détectées: {len(analysis['loops_found'])}")
                for loop in analysis['loops_found'][:3]:  # Limiter à 3 exemples
                    report.append(f"      - {loop}")
            
            if analysis['suspicious_calls']:
                report.append(f"   ⚠️ Appels suspects: {len(analysis['suspicious_calls'])}")
                for call in analysis['suspicious_calls'][:3]:  # Limiter à 3 exemples
                    report.append(f"      - {call}")
            
            report.append("")
        
        # Vérifier les processus en cours
        report.append("🔄 PROCESSUS EN COURS:")
        report.append("-" * 50)
        
        processes = self.check_running_processes()
        if processes:
            for process in processes:
                report.append(f"⚠️ {process['file']} (PID: {process['pid']})")
                report.append(f"   Commande: {process['command']}")
        else:
            report.append("✅ Aucun processus suspect détecté")
        
        report.append("")
        
        # Recommandations
        report.append("💡 RECOMMANDATIONS:")
        report.append("-" * 50)
        
        high_risk_files = [a for a in scripts_analysis if a.get('risk_level') == 'high']
        if high_risk_files:
            report.append("🚨 FICHIERS À RISQUE ÉLEVÉ:")
            for analysis in high_risk_files:
                report.append(f"   - {analysis['file']}")
            report.append("")
            report.append("   Actions recommandées:")
            report.append("   1. Arrêter immédiatement ces scripts")
            report.append("   2. Analyser le code pour identifier les boucles")
            report.append("   3. Corriger ou supprimer les scripts problématiques")
            report.append("   4. Mettre en place des timeouts et des conditions d'arrêt")
        
        if processes:
            report.append("🔄 PROCESSUS À ARRÊTER:")
            for process in processes:
                report.append(f"   - PID {process['pid']}: {process['file']}")
            report.append("")
            report.append("   Commande pour arrêter:")
            report.append("   python3 identify_looping_scripts.py --kill")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Détecteur de scripts en boucle')
    parser.add_argument('--kill', action='store_true', help='Tuer les processus en boucle')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Mode dry run')
    
    args = parser.parse_args()
    
    detector = LoopingScriptDetector()
    
    # Générer le rapport
    report = detector.generate_report()
    print(report)
    
    # Sauvegarder le rapport
    with open('looping_scripts_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Rapport sauvegardé: looping_scripts_report.txt")
    
    # Tuer les processus si demandé
    if args.kill:
        dry_run = not args.kill
        killed_count = detector.kill_looping_processes(dry_run)
        print(f"\n🔫 Processus traités: {killed_count}")

if __name__ == "__main__":
    main()
