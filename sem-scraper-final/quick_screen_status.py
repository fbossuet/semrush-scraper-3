#!/usr/bin/env python3
"""
Script rapide pour voir le statut des sessions screen
"""

import subprocess
import sys
from datetime import datetime, timezone

def get_screen_sessions():
    """Récupère la liste des sessions screen"""
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
        print(f"❌ Erreur: {e}")
        return []

def main():
    """Fonction principale"""
    print("🖥️ STATUT DES SESSIONS SCREEN")
    print("=" * 50)
    print(f"🕒 {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)
    
    sessions = get_screen_sessions()
    
    if not sessions:
        print("ℹ️ Aucune session screen active")
        return
    
    print(f"\n📊 {len(sessions)} session(s) active(s):")
    print("-" * 50)
    print(f"{'Nom':<20} {'ID':<8} {'Statut':<12}")
    print("-" * 50)
    
    for session in sessions:
        status_icon = "🟢" if session['status'] == 'Attached' else "🟡"
        print(f"{session['name']:<20} {session['id']:<8} {status_icon} {session['status']}")
    
    print("-" * 50)
    
    # Compter par statut
    attached = len([s for s in sessions if s['status'] == 'Attached'])
    detached = len([s for s in sessions if s['status'] == 'Detached'])
    
    print(f"🟢 Attachées: {attached}")
    print(f"🟡 Détachées: {detached}")
    
    # Commandes utiles
    print(f"\n💡 COMMANDES UTILES:")
    print("screen -r <nom>     - Se connecter à une session")
    print("screen -S <nom> -X quit - Arrêter une session")
    print("python3 screen_manager.py - Menu complet")

if __name__ == "__main__":
    main()
