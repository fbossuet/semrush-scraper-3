#!/usr/bin/env python3
"""
Script de Validation des Règles de Cohérence
============================================

Ce script vérifie que les champs ont des valeurs valides et des statuts cohérents
en fonction des règles d'attribution définies dans les spécifications.

Usage: python3 validate_rules.py
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class DatabaseValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.results = {
            'shops_validation': {},
            'analytics_validation': {},
            'coherence_validation': {},
            'summary': {}
        }
    
    def connect(self):
        """Connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Connexion à la base de données: {self.db_path}")
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion: {e}")
            sys.exit(1)
    
    def validate_shops_rules(self) -> Dict[str, Any]:
        """Validation des règles pour la table shops"""
        print("\n🔍 VALIDATION DES RÈGLES SHOPS")
        print("=" * 50)
        
        # Règles de statuts
        status_rules = {
            'table_scraping_status': {
                'valid_values': ['table_extracted', 'failed', 'pending'],
                'required_for_success': 'table_extracted'
            },
            'details_scraping_status': {
                'valid_values': ['details_extracted', 'failed', 'pending'],
                'required_for_success': 'details_extracted'
            },
            'scraping_status': {
                'valid_values': ['completed', 'partial', 'failed', 'na', 'pending', ''],
                'required_for_success': 'completed'
            }
        }
        
        # Validation des statuts
        status_results = {}
        for field, rules in status_rules.items():
            query = f"""
            SELECT 
                {field},
                COUNT(*) as count
            FROM shops 
            GROUP BY {field}
            ORDER BY count DESC
            """
            
            cursor = self.conn.execute(query)
            values = cursor.fetchall()
            
            print(f"\n📊 Statuts {field}:")
            valid_count = 0
            total_count = 0
            
            for row in values:
                value = row[0] if row[0] is not None else 'NULL'
                count = row[1]
                total_count += count
                
                if row[0] in rules['valid_values']:
                    status = "✅ VALIDE"
                    valid_count += count
                else:
                    status = "❌ INVALIDE"
                
                print(f"  {value}: {count} ({status})")
            
            status_results[field] = {
                'valid_count': valid_count,
                'total_count': total_count,
                'valid_percentage': (valid_count / total_count * 100) if total_count > 0 else 0,
                'success_count': self.conn.execute(f"SELECT COUNT(*) FROM shops WHERE {field} = ?", (rules['required_for_success'],)).fetchone()[0]
            }
        
        # Règles de format et valeurs
        format_rules = {
            'shop_url': {
                'query': "shop_url LIKE 'http%://%'",
                'description': 'URL valide (http/https)'
            },
            'external_id': {
                'query': "external_id LIKE '________-____-____-____-____________'",
                'description': 'UUID valide (format UUID v4)'
            },
            'total_products': {
                'query': 'total_products > 0',
                'description': 'Nombre de produits > 0'
            },
            'monthly_visits': {
                'query': 'monthly_visits > 0',
                'description': 'Visites mensuelles > 0'
            },
            'monthly_revenue': {
                'query': "monthly_revenue IS NOT NULL AND monthly_revenue != ''",
                'description': 'Revenus mensuels présents'
            },
            'live_ads': {
                'query': 'live_ads >= 0',
                'description': 'Publicités actives >= 0'
            },
            'aov': {
                'query': 'aov > 0',
                'description': 'Average Order Value > 0'
            },
            'year_founded': {
                'query': "year_founded IS NOT NULL AND year_founded != ''",
                'description': 'Année de création présente'
            },
            'live_ads_7d': {
                'query': 'live_ads_7d >= 0',
                'description': 'Publicités 7 jours >= 0'
            },
            'live_ads_30d': {
                'query': 'live_ads_30d >= 0',
                'description': 'Publicités 30 jours >= 0'
            },
            'pixel_google': {
                'query': "pixel_google IS NOT NULL AND pixel_google != ''",
                'description': 'Pixel Google détecté'
            },
            'pixel_facebook': {
                'query': "pixel_facebook IS NOT NULL AND pixel_facebook != ''",
                'description': 'Pixel Facebook détecté'
            }
        }
        
        # Validation des formats
        format_results = {}
        print(f"\n📋 Validation des formats et valeurs:")
        
        for field, rules in format_rules.items():
            try:
                # Compter les valeurs valides
                valid_query = f"SELECT COUNT(*) FROM shops WHERE {rules['query']}"
                valid_count = self.conn.execute(valid_query).fetchone()[0]
                
                # Compter le total
                total_query = f"SELECT COUNT(*) FROM shops WHERE {field} IS NOT NULL"
                total_count = self.conn.execute(total_query).fetchone()[0]
                
                percentage = (valid_count / total_count * 100) if total_count > 0 else 0
                status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
                
                print(f"  {field}: {valid_count}/{total_count} ({percentage:.1f}%) {status}")
                
                format_results[field] = {
                    'valid_count': valid_count,
                    'total_count': total_count,
                    'percentage': percentage,
                    'status': status
                }
                
            except sqlite3.Error as e:
                print(f"  {field}: ❌ Erreur - {e}")
                format_results[field] = {
                    'valid_count': 0,
                    'total_count': 0,
                    'percentage': 0,
                    'status': '❌'
                }
        
        # Validation des marchés (pourcentages 0-1)
        market_fields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr']
        market_results = {}
        
        print(f"\n🌍 Validation des marchés (0-1):")
        for field in market_fields:
            try:
                valid_query = f"SELECT COUNT(*) FROM shops WHERE {field} BETWEEN 0 AND 1"
                valid_count = self.conn.execute(valid_query).fetchone()[0]
                
                total_query = f"SELECT COUNT(*) FROM shops WHERE {field} IS NOT NULL"
                total_count = self.conn.execute(total_query).fetchone()[0]
                
                percentage = (valid_count / total_count * 100) if total_count > 0 else 0
                status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
                
                print(f"  {field}: {valid_count}/{total_count} ({percentage:.1f}%) {status}")
                
                market_results[field] = {
                    'valid_count': valid_count,
                    'total_count': total_count,
                    'percentage': percentage,
                    'status': status
                }
                
            except sqlite3.Error as e:
                print(f"  {field}: ❌ Erreur - {e}")
                market_results[field] = {
                    'valid_count': 0,
                    'total_count': 0,
                    'percentage': 0,
                    'status': '❌'
                }
        
        return {
            'status_rules': status_results,
            'format_rules': format_results,
            'market_rules': market_results
        }
    
    def validate_analytics_rules(self) -> Dict[str, Any]:
        """Validation des règles pour la table analytics"""
        print("\n🔍 VALIDATION DES RÈGLES ANALYTICS")
        print("=" * 50)
        
        # Règles de statuts analytics
        status_rules = {
            'scraping_status': {
                'valid_values': ['completed', 'partial', 'failed'],
                'required_for_success': 'completed'
            }
        }
        
        # Validation des statuts
        status_results = {}
        for field, rules in status_rules.items():
            query = f"""
            SELECT 
                {field},
                COUNT(*) as count
            FROM analytics 
            GROUP BY {field}
            ORDER BY count DESC
            """
            
            cursor = self.conn.execute(query)
            values = cursor.fetchall()
            
            print(f"\n📊 Statuts {field}:")
            valid_count = 0
            total_count = 0
            
            for row in values:
                value = row[0] if row[0] is not None else 'NULL'
                count = row[1]
                total_count += count
                
                if row[0] in rules['valid_values']:
                    status = "✅ VALIDE"
                    valid_count += count
                else:
                    status = "❌ INVALIDE"
                
                print(f"  {value}: {count} ({status})")
            
            status_results[field] = {
                'valid_count': valid_count,
                'total_count': total_count,
                'valid_percentage': (valid_count / total_count * 100) if total_count > 0 else 0,
                'success_count': self.conn.execute(f"SELECT COUNT(*) FROM analytics WHERE {field} = ?", (rules['required_for_success'],)).fetchone()[0]
            }
        
        # Règles de métriques analytics
        metrics_rules = {
            'visits': {
                'query': 'visits IS NOT NULL',
                'description': 'Visites présentes'
            },
            'organic_traffic': {
                'query': 'organic_traffic IS NOT NULL',
                'description': 'Trafic organique présent'
            },
            'paid_search_traffic': {
                'query': 'paid_search_traffic IS NOT NULL',
                'description': 'Trafic payant présent'
            },
            'cpc': {
                'query': 'cpc IS NOT NULL',
                'description': 'CPC présent'
            },
            'bounce_rate': {
                'query': 'bounce_rate IS NOT NULL',
                'description': 'Taux de rebond présent'
            },
            'avg_visit_duration': {
                'query': 'avg_visit_duration IS NOT NULL',
                'description': 'Durée moyenne présente'
            },
            'branded_traffic': {
                'query': 'branded_traffic IS NOT NULL',
                'description': 'Trafic de marque présent'
            },
            'conversion_rate': {
                'query': 'conversion_rate IS NOT NULL',
                'description': 'Taux de conversion présent'
            }
        }
        
        # Validation des métriques
        metrics_results = {}
        print(f"\n📈 Validation des métriques analytics:")
        
        for field, rules in metrics_rules.items():
            try:
                # Compter les valeurs présentes
                valid_query = f"SELECT COUNT(*) FROM analytics WHERE {rules['query']}"
                valid_count = self.conn.execute(valid_query).fetchone()[0]
                
                # Compter le total
                total_count = self.conn.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
                
                percentage = (valid_count / total_count * 100) if total_count > 0 else 0
                status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
                
                print(f"  {field}: {valid_count}/{total_count} ({percentage:.1f}%) {status}")
                
                metrics_results[field] = {
                    'valid_count': valid_count,
                    'total_count': total_count,
                    'percentage': percentage,
                    'status': status
                }
                
            except sqlite3.Error as e:
                print(f"  {field}: ❌ Erreur - {e}")
                metrics_results[field] = {
                    'valid_count': 0,
                    'total_count': 0,
                    'percentage': 0,
                    'status': '❌'
                }
        
        return {
            'status_rules': status_results,
            'metrics_rules': metrics_results
        }
    
    def validate_coherence_rules(self) -> Dict[str, Any]:
        """Validation des règles de cohérence entre tables"""
        print("\n🔍 VALIDATION DES RÈGLES DE COHÉRENCE")
        print("=" * 50)
        
        coherence_results = {}
        
        # 1. Clé étrangère valide
        try:
            query = """
            SELECT COUNT(*) 
            FROM analytics a 
            LEFT JOIN shops s ON a.shop_id = s.id 
            WHERE s.id IS NULL
            """
            invalid_fk = self.conn.execute(query).fetchone()[0]
            
            if invalid_fk == 0:
                print("✅ Clé étrangère: Toutes les analytics ont un shop_id valide")
                coherence_results['foreign_key'] = {'status': '✅', 'invalid_count': 0}
            else:
                print(f"❌ Clé étrangère: {invalid_fk} analytics avec shop_id invalide")
                coherence_results['foreign_key'] = {'status': '❌', 'invalid_count': invalid_fk}
        except sqlite3.Error as e:
            print(f"❌ Erreur validation clé étrangère: {e}")
            coherence_results['foreign_key'] = {'status': '❌', 'error': str(e)}
        
        # 2. Unicité analytics par shop
        try:
            query = """
            SELECT shop_id, COUNT(*) as count
            FROM analytics 
            GROUP BY shop_id 
            HAVING COUNT(*) > 1
            """
            duplicates = self.conn.execute(query).fetchall()
            
            if len(duplicates) == 0:
                print("✅ Unicité: Un seul enregistrement analytics par shop")
                coherence_results['uniqueness'] = {'status': '✅', 'duplicate_count': 0}
            else:
                print(f"❌ Unicité: {len(duplicates)} shops avec plusieurs analytics")
                coherence_results['uniqueness'] = {'status': '❌', 'duplicate_count': len(duplicates)}
        except sqlite3.Error as e:
            print(f"❌ Erreur validation unicité: {e}")
            coherence_results['uniqueness'] = {'status': '❌', 'error': str(e)}
        
        # 3. Cohérence des statuts (workflow logique)
        try:
            query = """
            SELECT COUNT(*) 
            FROM shops 
            WHERE details_scraping_status = 'details_extracted' 
            AND table_scraping_status != 'table_extracted'
            """
            inconsistent_status = self.conn.execute(query).fetchone()[0]
            
            if inconsistent_status == 0:
                print("✅ Cohérence statuts: Workflow logique respecté")
                coherence_results['status_coherence'] = {'status': '✅', 'inconsistent_count': 0}
            else:
                print(f"❌ Cohérence statuts: {inconsistent_status} shops avec statuts incohérents")
                coherence_results['status_coherence'] = {'status': '❌', 'inconsistent_count': inconsistent_status}
        except sqlite3.Error as e:
            print(f"❌ Erreur validation cohérence: {e}")
            coherence_results['status_coherence'] = {'status': '❌', 'error': str(e)}
        
        return coherence_results
    
    def generate_summary(self):
        """Génération du résumé des validations"""
        print("\n📊 RÉSUMÉ DES VALIDATIONS")
        print("=" * 50)
        
        # Compter les shops
        total_shops = self.conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
        total_analytics = self.conn.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
        
        print(f"📈 Statistiques générales:")
        print(f"  Total shops: {total_shops}")
        print(f"  Total analytics: {total_analytics}")
        print(f"  Taux de couverture analytics: {(total_analytics/total_shops*100):.1f}%")
        
        # Compter les succès par phase
        table_extracted = self.conn.execute("SELECT COUNT(*) FROM shops WHERE table_scraping_status = 'table_extracted'").fetchone()[0]
        details_extracted = self.conn.execute("SELECT COUNT(*) FROM shops WHERE details_scraping_status = 'details_extracted'").fetchone()[0]
        scraping_completed = self.conn.execute("SELECT COUNT(*) FROM shops WHERE scraping_status = 'completed'").fetchone()[0]
        analytics_completed = self.conn.execute("SELECT COUNT(*) FROM analytics WHERE scraping_status = 'completed'").fetchone()[0]
        
        print(f"\n📊 Progression par phase:")
        print(f"  Phase 1 (table_extracted): {table_extracted}/{total_shops} ({(table_extracted/total_shops*100):.1f}%)")
        print(f"  Phase 3 (details_extracted): {details_extracted}/{total_shops} ({(details_extracted/total_shops*100):.1f}%)")
        print(f"  Scraping complet: {scraping_completed}/{total_shops} ({(scraping_completed/total_shops*100):.1f}%)")
        print(f"  Analytics complet: {analytics_completed}/{total_analytics} ({(analytics_completed/total_analytics*100):.1f}%)")
        
        return {
            'total_shops': total_shops,
            'total_analytics': total_analytics,
            'coverage_rate': (total_analytics/total_shops*100) if total_shops > 0 else 0,
            'table_extracted': table_extracted,
            'details_extracted': details_extracted,
            'scraping_completed': scraping_completed,
            'analytics_completed': analytics_completed
        }
    
    def export_validation_report(self, output_file: str = None):
        """Export du rapport de validation en Markdown"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"validation_rules_report_{timestamp}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 🔍 Rapport de Validation des Règles\n\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Statistiques générales
                summary = self.results['summary']
                f.write("## 📈 Statistiques Générales\n\n")
                f.write(f"- **Total shops:** {summary.get('total_shops', 0)}\n")
                f.write(f"- **Total analytics:** {summary.get('total_analytics', 0)}\n")
                f.write(f"- **Taux de couverture analytics:** {summary.get('coverage_rate', 0):.1f}%\n\n")
                
                # Progression par phase
                f.write("## 📊 Progression par Phase\n\n")
                f.write(f"- **Phase 1 (table_extracted):** {summary.get('table_extracted', 0)}/{summary.get('total_shops', 0)} ({summary.get('table_extracted', 0)/summary.get('total_shops', 1)*100:.1f}%)\n")
                f.write(f"- **Phase 3 (details_extracted):** {summary.get('details_extracted', 0)}/{summary.get('total_shops', 0)} ({summary.get('details_extracted', 0)/summary.get('total_shops', 1)*100:.1f}%)\n")
                f.write(f"- **Scraping complet:** {summary.get('scraping_completed', 0)}/{summary.get('total_shops', 0)} ({summary.get('scraping_completed', 0)/summary.get('total_shops', 1)*100:.1f}%)\n")
                f.write(f"- **Analytics complet:** {summary.get('analytics_completed', 0)}/{summary.get('total_analytics', 0)} ({summary.get('analytics_completed', 0)/summary.get('total_analytics', 1)*100:.1f}%)\n\n")
                
                # Validation des règles shops
                shops_validation = self.results['shops_validation']
                f.write("## 🏪 Validation des Règles Shops\n\n")
                
                # Statuts
                f.write("### 📊 Statuts\n\n")
                for field, rules in shops_validation['status_rules'].items():
                    f.write(f"**{field}:**\n")
                    f.write(f"- Valid: {rules['valid_count']}/{rules['total_count']} ({rules['valid_percentage']:.1f}%)\n")
                    f.write(f"- Success: {rules['success_count']}\n\n")
                
                # Formats
                f.write("### 📋 Formats et Valeurs\n\n")
                for field, rules in shops_validation['format_rules'].items():
                    status_icon = "✅" if rules['status'] == "✅" else "⚠️" if rules['status'] == "⚠️" else "❌"
                    f.write(f"- **{field}:** {rules['valid_count']}/{rules['total_count']} ({rules['percentage']:.1f}%) {status_icon}\n")
                f.write("\n")
                
                # Marchés
                f.write("### 🌍 Marchés (0-1)\n\n")
                for field, rules in shops_validation['market_rules'].items():
                    status_icon = "✅" if rules['status'] == "✅" else "⚠️" if rules['status'] == "⚠️" else "❌"
                    f.write(f"- **{field}:** {rules['valid_count']}/{rules['total_count']} ({rules['percentage']:.1f}%) {status_icon}\n")
                f.write("\n")
                
                # Validation des règles analytics
                analytics_validation = self.results['analytics_validation']
                f.write("## 📈 Validation des Règles Analytics\n\n")
                
                # Statuts analytics
                f.write("### 📊 Statuts Analytics\n\n")
                for field, rules in analytics_validation['status_rules'].items():
                    f.write(f"**{field}:**\n")
                    f.write(f"- Valid: {rules['valid_count']}/{rules['total_count']} ({rules['valid_percentage']:.1f}%)\n")
                    f.write(f"- Success: {rules['success_count']}\n\n")
                
                # Métriques analytics
                f.write("### 📈 Métriques Analytics\n\n")
                for field, rules in analytics_validation['metrics_rules'].items():
                    status_icon = "✅" if rules['status'] == "✅" else "⚠️" if rules['status'] == "⚠️" else "❌"
                    f.write(f"- **{field}:** {rules['valid_count']}/{rules['total_count']} ({rules['percentage']:.1f}%) {status_icon}\n")
                f.write("\n")
                
                # Validation de cohérence
                coherence_validation = self.results['coherence_validation']
                f.write("## 🔗 Validation de Cohérence\n\n")
                
                for rule, result in coherence_validation.items():
                    status_icon = "✅" if result['status'] == "✅" else "❌"
                    f.write(f"- **{rule}:** {status_icon} {result.get('invalid_count', 0)} erreurs\n")
                f.write("\n")
            
            print(f"📄 Rapport de validation exporté vers: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
    
    def run_validation(self):
        """Exécution complète de la validation"""
        print("🚀 DÉMARRAGE DE LA VALIDATION DES RÈGLES")
        print("=" * 60)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.connect()
        
        # Validation des règles
        self.results['shops_validation'] = self.validate_shops_rules()
        self.results['analytics_validation'] = self.validate_analytics_rules()
        self.results['coherence_validation'] = self.validate_coherence_rules()
        self.results['summary'] = self.generate_summary()
        
        # Export du rapport
        self.export_validation_report()
        
        print(f"\n✅ VALIDATION TERMINÉE")
        print("=" * 60)
        
        if self.conn:
            self.conn.close()

def main():
    """Fonction principale"""
    db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    
    validator = DatabaseValidator(db_path)
    validator.run_validation()

if __name__ == "__main__":
    main()
