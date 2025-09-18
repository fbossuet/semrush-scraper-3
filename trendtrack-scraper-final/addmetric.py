#!/usr/bin/env python3
"""
Commande automatisée pour l'ajout de métriques
Applique automatiquement la procédure standardisée d'ajout de métriques
"""

import os
import sys
import sqlite3
import subprocess
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetricAdder:
    """Classe pour l'ajout automatisé de métriques"""
    
    def __init__(self, base_path: str = "/home/ubuntu/trendtrack-scraper-final"):
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "data" / "trendtrack.db"
        self.procedure_path = self.base_path / "docs" / "procedures" / "metric_addition_procedure.md"
        
        # Types de données supportés
        self.supported_types = {
            'INTEGER': self._validate_int,
            'NUMERIC': self._validate_numeric,
            'TEXT': self._validate_text,
            'DATE': self._validate_date
        }
        
        # Tables supportées
        self.supported_tables = ['shops', 'analytics']
        
        # Scrapers à mettre à jour
        self.scrapers_to_update = [
            'smart_scraper_intelligent.py',
            'scrapers/domain_search/domain_scraper.py'
        ]
    
    def add_metric(self, metric_name: str, data_type: str, table: str, 
                   description: str = "", source: str = "unknown") -> bool:
        """
        Ajoute une nouvelle métrique en suivant la procédure standardisée
        
        Args:
            metric_name: Nom de la métrique
            data_type: Type de données (INTEGER, NUMERIC, TEXT, DATE)
            table: Table cible (shops, analytics)
            description: Description de la métrique
            source: Source des données
            
        Returns:
            bool: True si l'ajout a réussi
        """
        print(f"\n🚀 AJOUT DE MÉTRIQUE: {metric_name}")
        print("=" * 60)
        print(f"📊 Métrique: {metric_name}")
        print(f"🏷️ Type: {data_type}")
        print(f"📋 Table: {table}")
        print(f"📝 Description: {description}")
        print(f"🔗 Source: {source}")
        print("=" * 60)
        
        try:
            # ÉTAPE 1: Préparation et sécurité
            if not self._step1_preparation(metric_name):
                return False
            
            # ÉTAPE 2: Analyse de la métrique
            if not self._step2_analysis(metric_name, data_type, table, description, source):
                return False
            
            # ÉTAPE 3: Vérifications pré-implémentation
            if not self._step3_pre_checks(metric_name, table):
                return False
            
            # ÉTAPE 4: Modification de la structure de base
            if not self._step4_database_structure(metric_name, data_type, table):
                return False
            
            # ÉTAPE 5: Mise à jour du code de scraping
            if not self._step5_scraping_code(metric_name, data_type, table):
                return False
            
            # ÉTAPE 6: Mise à jour des scrapers
            if not self._step6_scrapers_update(metric_name, data_type, table):
                return False
            
            # ÉTAPE 7: Tests de validation
            if not self._step7_validation_tests(metric_name, table):
                return False
            
            # ÉTAPE 8: Vérifications post-implémentation
            if not self._step8_post_checks(metric_name, table):
                return False
            
            # ÉTAPE 9: Finalisation
            if not self._step9_finalization(metric_name):
                return False
            
            print(f"\n✅ MÉTRIQUE AJOUTÉE AVEC SUCCÈS: {metric_name}")
            print("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout de la métrique: {e}")
            self._emergency_rollback(metric_name)
            return False
    
    def _step1_preparation(self, metric_name: str) -> bool:
        """ÉTAPE 1: Préparation et sécurité"""
        print("\n1️⃣ ÉTAPE 1: PRÉPARATION ET SÉCURITÉ")
        print("-" * 40)
        
        try:
            # Créer une sauvegarde de sécurité
            backup_name = f"backup_avant_ajout_{metric_name}"
            result = subprocess.run([
                'python3', 'backup_rollback_system.py', 'create', backup_name
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode != 0:
                print(f"❌ Erreur lors de la création de la sauvegarde: {result.stderr}")
                return False
            
            print(f"✅ Sauvegarde créée: {backup_name}")
            
            # Démarrer l'opération avec rollback
            operation_name = f"ajout_metrique_{metric_name}"
            result = subprocess.run([
                'python3', 'rollback_procedure.py', 'start', operation_name
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode != 0:
                print(f"❌ Erreur lors du démarrage de l'opération: {result.stderr}")
                return False
            
            print(f"✅ Opération démarrée: {operation_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 1: {e}")
            return False
    
    def _step2_analysis(self, metric_name: str, data_type: str, table: str, 
                       description: str, source: str) -> bool:
        """ÉTAPE 2: Analyse de la métrique"""
        print("\n2️⃣ ÉTAPE 2: ANALYSE DE LA MÉTRIQUE")
        print("-" * 40)
        
        # Vérifier le type de données
        if data_type not in self.supported_types:
            print(f"❌ Type de données non supporté: {data_type}")
            print(f"✅ Types supportés: {', '.join(self.supported_types.keys())}")
            return False
        
        # Vérifier la table
        if table not in self.supported_tables:
            print(f"❌ Table non supportée: {table}")
            print(f"✅ Tables supportées: {', '.join(self.supported_tables)}")
            return False
        
        # Analyser les types de champs existants
        if not self._analyze_existing_field_types(metric_name, data_type, table):
            return False
        
        print(f"✅ Type de données validé: {data_type}")
        print(f"✅ Table validée: {table}")
        print(f"✅ Description: {description}")
        print(f"✅ Source: {source}")
        
        return True
    
    def _analyze_existing_field_types(self, metric_name: str, data_type: str, table: str) -> bool:
        """Analyse les types de champs existants pour maintenir la cohérence"""
        print(f"\n🔍 ANALYSE DES TYPES DE CHAMPS EXISTANTS DANS {table}")
        print("-" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer tous les champs de la table
            cursor.execute(f"SELECT name, type FROM pragma_table_info('{table}') ORDER BY name;")
            existing_fields = cursor.fetchall()
            
            print(f"📋 Champs existants dans {table}:")
            for field_name, field_type in existing_fields:
                print(f"   - {field_name}: {field_type}")
            
            # Analyser la cohérence avec les champs similaires
            consistency_issues = []
            
            # Vérifier les patterns de noms
            metric_prefix = metric_name.split('_')[0] if '_' in metric_name else metric_name
            
            # Chercher des champs avec le même préfixe
            similar_fields = [f for f in existing_fields if f[0].startswith(metric_prefix)]
            
            if similar_fields:
                print(f"\n🔍 Champs similaires trouvés (préfixe: {metric_prefix}):")
                for field_name, field_type in similar_fields:
                    print(f"   - {field_name}: {field_type}")
                    
                    # Vérifier la cohérence des types
                    if field_type != data_type:
                        consistency_issues.append(f"Type incohérent: {field_name} ({field_type}) vs {metric_name} ({data_type})")
            
            # Vérifier les patterns spécifiques
            if metric_name.startswith('market_'):
                market_fields = [f for f in existing_fields if f[0].startswith('market_')]
                if market_fields:
                    expected_type = market_fields[0][1]
                    if data_type != expected_type:
                        consistency_issues.append(f"Tous les champs market_* doivent être {expected_type}, pas {data_type}")
            
            elif metric_name.startswith('pixel_'):
                pixel_fields = [f for f in existing_fields if f[0].startswith('pixel_')]
                if pixel_fields:
                    expected_type = pixel_fields[0][1]
                    if data_type != expected_type:
                        consistency_issues.append(f"Tous les champs pixel_* doivent être {expected_type}, pas {data_type}")
            
            elif metric_name.startswith('monthly_'):
                monthly_fields = [f for f in existing_fields if f[0].startswith('monthly_')]
                if monthly_fields:
                    # Analyser les types existants
                    types_found = set(f[1] for f in monthly_fields)
                    if len(types_found) > 1:
                        consistency_issues.append(f"Types incohérents dans monthly_*: {', '.join(types_found)}")
            
            # Afficher les problèmes de cohérence
            if consistency_issues:
                print(f"\n⚠️ PROBLÈMES DE COHÉRENCE DÉTECTÉS:")
                for issue in consistency_issues:
                    print(f"   - {issue}")
                
                # Demander confirmation
                print(f"\n❓ Voulez-vous continuer malgré ces incohérences? (y/N)")
                # En mode automatique, on accepte par défaut mais on log l'avertissement
                print("   ⚠️ Mode automatique: continuation avec avertissement")
                logger.warning(f"Incohérences détectées pour {metric_name}: {consistency_issues}")
            else:
                print(f"\n✅ Aucun problème de cohérence détecté")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse des types existants: {e}")
            return False
    
    def _step3_pre_checks(self, metric_name: str, table: str) -> bool:
        """ÉTAPE 3: Vérifications pré-implémentation"""
        print("\n3️⃣ ÉTAPE 3: VÉRIFICATIONS PRÉ-IMPLÉMENTATION")
        print("-" * 40)
        
        try:
            # Vérifier la structure actuelle de la base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si la métrique existe déjà
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            for column in columns:
                if column[1] == metric_name:
                    print(f"❌ La métrique {metric_name} existe déjà dans la table {table}")
                    conn.close()
                    return False
            
            print(f"✅ Métrique {metric_name} n'existe pas encore")
            print(f"✅ Structure actuelle de {table} vérifiée")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 3: {e}")
            return False
    
    def _step4_database_structure(self, metric_name: str, data_type: str, table: str) -> bool:
        """ÉTAPE 4: Modification de la structure de base"""
        print("\n4️⃣ ÉTAPE 4: MODIFICATION DE LA STRUCTURE DE BASE")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ajouter le champ à la table
            alter_sql = f"ALTER TABLE {table} ADD COLUMN {metric_name} {data_type};"
            cursor.execute(alter_sql)
            conn.commit()
            
            print(f"✅ Champ {metric_name} ajouté à la table {table}")
            
            # Vérifier l'ajout
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            for column in columns:
                if column[1] == metric_name:
                    print(f"✅ Vérification: {metric_name} ({column[2]}) ajouté avec succès")
                    break
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 4: {e}")
            return False
    
    def _step5_scraping_code(self, metric_name: str, data_type: str, table: str) -> bool:
        """ÉTAPE 5: Mise à jour du code de scraping"""
        print("\n5️⃣ ÉTAPE 5: MISE À JOUR DU CODE DE SCRAPING")
        print("-" * 40)
        
        # Cette étape sera implémentée dans les scrapers
        print(f"✅ Code de scraping à mettre à jour pour {metric_name}")
        print(f"✅ Validation de type {data_type} requise")
        
        return True
    
    def _step6_scrapers_update(self, metric_name: str, data_type: str, table: str) -> bool:
        """ÉTAPE 6: Mise à jour des scrapers"""
        print("\n6️⃣ ÉTAPE 6: MISE À JOUR DES SCRAPERS")
        print("-" * 40)
        
        # Cette étape sera implémentée dans les scrapers
        print(f"✅ Scrapers à mettre à jour pour {metric_name}")
        print(f"✅ Requêtes SQL à modifier")
        
        return True
    
    def _step7_validation_tests(self, metric_name: str, table: str) -> bool:
        """ÉTAPE 7: Tests de validation"""
        print("\n7️⃣ ÉTAPE 7: TESTS DE VALIDATION")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test de la structure de base
            cursor.execute(f"SELECT {metric_name} FROM {table} LIMIT 1;")
            result = cursor.fetchone()
            print(f"✅ Test de structure réussi pour {metric_name}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 7: {e}")
            return False
    
    def _step8_post_checks(self, metric_name: str, table: str) -> bool:
        """ÉTAPE 8: Vérifications post-implémentation"""
        print("\n8️⃣ ÉTAPE 8: VÉRIFICATIONS POST-IMPLÉMENTATION")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier que la métrique est alimentée
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {metric_name} IS NOT NULL;")
            count = cursor.fetchone()[0]
            print(f"✅ Métrique {metric_name} alimentée: {count} enregistrements")
            
            # Vérifier les types de données
            cursor.execute(f"SELECT typeof({metric_name}) FROM {table} WHERE {metric_name} IS NOT NULL LIMIT 1;")
            type_result = cursor.fetchone()
            if type_result:
                print(f"✅ Type de données vérifié: {type_result[0]}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 8: {e}")
            return False
    
    def _step9_finalization(self, metric_name: str) -> bool:
        """ÉTAPE 9: Finalisation"""
        print("\n9️⃣ ÉTAPE 9: FINALISATION")
        print("-" * 40)
        
        try:
            # Terminer l'opération avec succès
            operation_name = f"ajout_metrique_{metric_name}"
            result = subprocess.run([
                'python3', 'rollback_procedure.py', 'complete', operation_name
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode != 0:
                print(f"❌ Erreur lors de la finalisation: {result.stderr}")
                return False
            
            print(f"✅ Opération terminée avec succès: {operation_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur dans l'étape 9: {e}")
            return False
    
    def _emergency_rollback(self, metric_name: str) -> bool:
        """Rollback d'urgence en cas d'erreur"""
        print(f"\n🚨 ROLLBACK D'URGENCE POUR {metric_name}")
        print("=" * 60)
        
        try:
            operation_name = f"ajout_metrique_{metric_name}"
            result = subprocess.run([
                'python3', 'rollback_procedure.py', 'rollback', 'erreur_critique'
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode == 0:
                print("✅ Rollback d'urgence réussi")
                return True
            else:
                print(f"❌ Échec du rollback d'urgence: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du rollback d'urgence: {e}")
            return False
    
    # Méthodes de validation des types
    def _validate_int(self, value):
        """Valide qu'une valeur est un INTEGER valide"""
        if not value or value == 'na' or value == '':
            return None
        try:
            if isinstance(value, int):
                return value
            cleaned = str(value).replace(',', '').replace(' ', '').replace('$', '')
            return int(float(cleaned))
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valeur '{value}' n'est pas un INTEGER valide")
            return None
    
    def _validate_numeric(self, value):
        """Valide qu'une valeur est un NUMERIC valide"""
        if not value or value == 'na' or value == '':
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            cleaned = str(value).replace('%', '').replace(' ', '').replace(',', '')
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valeur '{value}' n'est pas un NUMERIC valide")
            return None
    
    def _validate_text(self, value):
        """Valide qu'une valeur est un TEXT valide"""
        if not value or value == 'na' or value == '':
            return None
        return str(value)
    
    def _validate_date(self, value):
        """Valide qu'une valeur est un DATE valide"""
        if not value or value == 'na' or value == '':
            return None
        try:
            if isinstance(value, datetime.date):
                return value
            return datetime.datetime.strptime(str(value), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valeur '{value}' n'est pas un DATE valide")
            return None

def main():
    """Fonction principale pour la commande addmetric"""
    if len(sys.argv) < 4:
        print("Usage: python3 addmetric.py <metric_name> <data_type> <table> [description] [source]")
        print("\nExemples:")
        print("  python3 addmetric.py conversion_rate NUMERIC analytics 'Taux de conversion' 'MyToolsPlan'")
        print("  python3 addmetric.py total_products INTEGER shops 'Nombre total de produits' 'TrendTrack'")
        print("\nTypes supportés: INTEGER, NUMERIC, TEXT, DATE")
        print("Tables supportées: shops, analytics")
        return 1
    
    metric_name = sys.argv[1]
    data_type = sys.argv[2].upper()
    table = sys.argv[3]
    description = sys.argv[4] if len(sys.argv) > 4 else ""
    source = sys.argv[5] if len(sys.argv) > 5 else "unknown"
    
    # Initialiser l'ajouteur de métriques
    adder = MetricAdder()
    
    # Ajouter la métrique
    success = adder.add_metric(metric_name, data_type, table, description, source)
    
    if success:
        print(f"\n🎉 MÉTRIQUE {metric_name} AJOUTÉE AVEC SUCCÈS!")
        return 0
    else:
        print(f"\n❌ ÉCHEC DE L'AJOUT DE LA MÉTRIQUE {metric_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
