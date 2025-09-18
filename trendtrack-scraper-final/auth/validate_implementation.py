#!/usr/bin/env python3
"""
Script de validation de l'implémentation T032
Vérifie que l'authentification TrendTrack est correctement implémentée
"""

import sys
import os
import importlib.util

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_file_structure():
    """Valider la structure des fichiers"""
    print("🔍 Validation de la structure des fichiers...")
    
    required_files = [
        'auth/__init__.py',
        'auth/api_auth_client.py',
        'auth/dom_auth_client.py',
        'auth/config.py',
        'auth/test_auth.py',
        'auth/integration_example.py',
        'auth/README.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {missing_files}")
        return False
    else:
        print("✅ Tous les fichiers requis sont présents")
        return True

def validate_imports():
    """Valider les imports"""
    print("🔍 Validation des imports...")
    
    try:
        # Test des imports principaux
        from auth import TrendTrackAuth, TrendTrackDOMAuth
        print("✅ Import des classes principales réussi")
        
        from auth import get_auth_client, is_authenticated
        print("✅ Import des fonctions utilitaires réussi")
        
        from auth.config import config, credentials, configured
        print("✅ Import de la configuration réussi")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def validate_class_structure():
    """Valider la structure des classes"""
    print("🔍 Validation de la structure des classes...")
    
    try:
        from auth import TrendTrackAuth, TrendTrackDOMAuth
        
        # Vérifier TrendTrackAuth
        auth_api = TrendTrackAuth()
        required_methods_api = [
            'authenticate', 'get_authenticated_session', 'is_authenticated',
            'is_session_valid', 'refresh_authentication', 'logout'
        ]
        
        for method in required_methods_api:
            if not hasattr(auth_api, method):
                print(f"❌ Méthode manquante dans TrendTrackAuth: {method}")
                return False
        
        print("✅ Structure de TrendTrackAuth validée")
        
        # Vérifier TrendTrackDOMAuth
        auth_dom = TrendTrackDOMAuth()
        required_methods_dom = [
            'authenticate', 'get_authenticated_page', 'is_authenticated',
            'is_session_valid', 'refresh_authentication', 'logout', 'close'
        ]
        
        for method in required_methods_dom:
            if not hasattr(auth_dom, method):
                print(f"❌ Méthode manquante dans TrendTrackDOMAuth: {method}")
                return False
        
        print("✅ Structure de TrendTrackDOMAuth validée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation des classes: {e}")
        return False

def validate_configuration():
    """Valider la configuration"""
    print("🔍 Validation de la configuration...")
    
    try:
        from auth.config import config, credentials, configured
        
        # Vérifier les clés de configuration requises
        required_config_keys = [
            'base_url', 'login_url', 'dashboard_url', 'auth_method',
            'session_timeout_hours', 'user_agent'
        ]
        
        for key in required_config_keys:
            if key not in config:
                print(f"❌ Clé de configuration manquante: {key}")
                return False
        
        print("✅ Configuration validée")
        
        # Vérifier les credentials
        if 'email' not in credentials or 'password' not in credentials:
            print("❌ Structure des credentials invalide")
            return False
        
        print("✅ Structure des credentials validée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation de la configuration: {e}")
        return False

def validate_compatibility():
    """Valider la compatibilité"""
    print("🔍 Validation de la compatibilité...")
    
    try:
        from auth import get_auth_client, is_authenticated, TrendTrackAuth, TrendTrackDOMAuth
        
        # Test des fonctions de compatibilité
        api_client = get_auth_client('api')
        dom_client = get_auth_client('dom')
        
        if not isinstance(api_client, TrendTrackAuth):
            print("❌ get_auth_client('api') ne retourne pas TrendTrackAuth")
            return False
        
        if not isinstance(dom_client, TrendTrackDOMAuth):
            print("❌ get_auth_client('dom') ne retourne pas TrendTrackDOMAuth")
            return False
        
        # Test des fonctions de vérification
        api_auth = is_authenticated('api')
        dom_auth = is_authenticated('dom')
        
        print("✅ Compatibilité validée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation de la compatibilité: {e}")
        return False

def validate_tests():
    """Valider les tests"""
    print("🔍 Validation des tests...")
    
    try:
        # Vérifier que le fichier de test existe et est exécutable
        test_file = os.path.join(os.path.dirname(__file__), 'test_auth.py')
        
        if not os.path.exists(test_file):
            print("❌ Fichier de test manquant")
            return False
        
        # Vérifier que le fichier peut être importé
        spec = importlib.util.spec_from_file_location("test_auth", test_file)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Vérifier que les fonctions de test existent
        required_test_functions = [
            'test_api_auth', 'test_dom_auth', 'test_auth_module'
        ]
        
        for func_name in required_test_functions:
            if not hasattr(test_module, func_name):
                print(f"❌ Fonction de test manquante: {func_name}")
                return False
        
        print("✅ Tests validés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation des tests: {e}")
        return False

def main():
    """Fonction principale de validation"""
    print("🚀 Validation de l'implémentation T032 - Authentification TrendTrack")
    print("=" * 70)
    
    validations = [
        ("Structure des fichiers", validate_file_structure),
        ("Imports", validate_imports),
        ("Structure des classes", validate_class_structure),
        ("Configuration", validate_configuration),
        ("Compatibilité", validate_compatibility),
        ("Tests", validate_tests)
    ]
    
    results = []
    
    for name, validation_func in validations:
        print(f"\n📋 {name}")
        print("-" * 40)
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erreur lors de la validation {name}: {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA VALIDATION")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{name:.<50} {status}")
        if result:
            passed += 1
    
    print("-" * 70)
    print(f"Résultat global: {passed}/{total} validations passées")
    
    if passed == total:
        print("🎉 T032 - Authentification TrendTrack: IMPLÉMENTATION VALIDÉE!")
        print("\n✅ Prêt pour la prochaine tâche (T033 - Playwright stealth)")
        return True
    else:
        print("❌ T032 - Authentification TrendTrack: IMPLÉMENTATION INCOMPLÈTE")
        print(f"⚠️ {total - passed} validation(s) ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


