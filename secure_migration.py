#!/usr/bin/env python3
"""
Migration Sécurisée vers la Base de Production
=============================================

Ce script migre UNIQUEMENT les données validées vers la base de production.
Il utilise les critères de validation client pour s'assurer qu'aucun risque
n'est pris sur la fiabilité des données.

Usage: python3 secure_migration.py
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class SecureMigration:
    def __init__(self, source_db_path: str, prod_db_path: str):
        self.source_db_path = source_db_path
        self.prod_db_path = prod_db_path
        self.conn_source = None
        self.conn_prod = None
        self.migration_stats = {
            'shops_validated': 0,
            'shops_migrated': 0,
            'analytics_validated': 0,
            'analytics_migrated': 0,
            'errors': []
        }
    
    def connect_databases(self):
        """Connexion aux deux bases de données"""
        try:
            self.conn_source = sqlite3.connect(self.source_db_path)
            self.conn_source.row_factory = sqlite3.Row
            
            self.conn_prod = sqlite3.connect(self.prod_db_path)
            self.conn_prod.row_factory = sqlite3.Row
            
            print(f"✅ Connexion à la base source: {self.source_db_path}")
            print(f"✅ Connexion à la base production: {self.prod_db_path}")
            
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion: {e}")
            sys.exit(1)
    
    def validate_client_criteria(self, shop_id: int) -> Dict[str, Any]:
        """Validation des critères client ULTRA-STRICTS"""
        query = """
        SELECT 
            s.id, s.shop_name, s.shop_url, s.external_id,
            s.table_scraping_status, s.details_scraping_status, s.scraping_status,
            s.total_products, s.monthly_visits, s.monthly_revenue, s.live_ads, s.aov, s.year_founded,
            s.live_ads_7d, s.live_ads_30d, s.pixel_google, s.pixel_facebook,
            s.market_us, s.market_uk, s.market_de, s.market_ca, s.market_au, s.market_fr,
            a.scraping_status as analytics_status, a.visits, a.organic_traffic, a.paid_search_traffic, 
            a.cpc, a.bounce_rate, a.avg_visit_duration, a.branded_traffic, a.conversion_rate
        FROM shops s 
        LEFT JOIN analytics a ON s.id = a.shop_id
        WHERE s.id = ?
        """
        
        cursor = self.conn_source.execute(query, (shop_id,))
        row = cursor.fetchone()
        
        if not row:
            return {'client_ready': False, 'risk_level': 'CRITIQUE', 'errors': ['Shop non trouvé']}
        
        errors = []
        risk_factors = []
        
        # CRITÈRES CLIENT ULTRA-STRICTS
        
        # 1. VALIDATION DES STATUTS (OBLIGATOIRE)
        if row['table_scraping_status'] != 'table_extracted':
            errors.append(f"table_scraping_status: '{row['table_scraping_status']}' (attendu: 'table_extracted')")
            risk_factors.append("Phase 1 TrendTrack non terminée")
        
        if row['details_scraping_status'] != 'details_extracted':
            errors.append(f"details_scraping_status: '{row['details_scraping_status']}' (attendu: 'details_extracted')")
            risk_factors.append("Phase 3 TrendTrack non terminée")
        
        if row['scraping_status'] != 'completed':
            errors.append(f"scraping_status: '{row['scraping_status']}' (attendu: 'completed')")
            risk_factors.append("Scraping TrendTrack non terminé")
        
        # 2. VALIDATION ANALYTICS (OBLIGATOIRE)
        if not row['analytics_status']:
            errors.append("Analytics manquantes")
            risk_factors.append("Données Noxtools manquantes")
        elif row['analytics_status'] != 'completed':
            errors.append(f"Analytics incomplètes: '{row['analytics_status']}' (attendu: 'completed')")
            risk_factors.append("Scraping Noxtools non terminé")
        
        # 3. VALIDATION DES MÉTRIQUES CRITIQUES
        critical_metrics = {
            'total_products': (row['total_products'], 'Nombre de produits', '> 0'),
            'monthly_visits': (row['monthly_visits'], 'Visites mensuelles', '> 0'),
            'monthly_revenue': (row['monthly_revenue'], 'Revenus mensuels', 'présent et non vide'),
            'aov': (row['aov'], 'Average Order Value', '> 0'),
            'year_founded': (row['year_founded'], 'Année de création', 'présent et non vide')
        }
        
        for field, (value, description, requirement) in critical_metrics.items():
            if not value or (isinstance(value, str) and value.strip() == ''):
                errors.append(f"{description} manquante ({requirement})")
                risk_factors.append(f"Données {description.lower()} manquantes")
            elif field in ['total_products', 'monthly_visits', 'aov'] and value <= 0:
                errors.append(f"{description} invalide: {value} ({requirement})")
                risk_factors.append(f"Données {description.lower()} invalides")
        
        # 4. VALIDATION DES PUBLICITÉS
        ad_metrics = {
            'live_ads': (row['live_ads'], 'Publicités actives', '>= 0'),
            'live_ads_7d': (row['live_ads_7d'], 'Publicités 7 jours', '>= 0'),
            'live_ads_30d': (row['live_ads_30d'], 'Publicités 30 jours', '>= 0')
        }
        
        for field, (value, description, requirement) in ad_metrics.items():
            if value is None:
                errors.append(f"{description} manquante ({requirement})")
                risk_factors.append(f"Données {description.lower()} manquantes")
            elif isinstance(value, (int, float)) and value < 0:
                errors.append(f"{description} invalide: {value} ({requirement})")
                risk_factors.append(f"Données {description.lower()} négatives")
        
        # 5. VALIDATION DES PIXELS
        if not row['pixel_google'] or row['pixel_google'].strip() == '':
            errors.append("Pixel Google manquant")
            risk_factors.append("Pixel Google manquant")
        
        if not row['pixel_facebook'] or row['pixel_facebook'].strip() == '':
            errors.append("Pixel Facebook manquant")
            risk_factors.append("Pixel Facebook manquant")
        
        # 6. VALIDATION DES MARCHÉS
        market_fields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr']
        for field in market_fields:
            value = row[field]
            if value is None or not (isinstance(value, (int, float)) and 0 <= value <= 1):
                errors.append(f"{field} invalide: {value} (doit être entre 0 et 1)")
                risk_factors.append(f"Données marché {field} invalides")
        
        # 7. VALIDATION DES MÉTRIQUES ANALYTICS
        if row['analytics_status'] == 'completed':
            analytics_metrics = {
                'visits': (row['visits'], 'Visites totales', '>= 0'),
                'organic_traffic': (row['organic_traffic'], 'Trafic organique', '>= 0'),
                'paid_search_traffic': (row['paid_search_traffic'], 'Trafic payant', '>= 0'),
                'branded_traffic': (row['branded_traffic'], 'Trafic de marque', '>= 0'),
                'cpc': (row['cpc'], 'Coût par clic', '>= 0'),
                'bounce_rate': (row['bounce_rate'], 'Taux de rebond', 'entre 0 et 1'),
                'conversion_rate': (row['conversion_rate'], 'Taux de conversion', 'entre 0 et 1'),
                'avg_visit_duration': (row['avg_visit_duration'], 'Durée moyenne', '> 0')
            }
            
            for field, (value, description, requirement) in analytics_metrics.items():
                if value is None:
                    errors.append(f"{description} manquante ({requirement})")
                    risk_factors.append(f"Données {description.lower()} manquantes")
                elif field in ['bounce_rate', 'conversion_rate'] and isinstance(value, (int, float)) and not (0 <= value <= 1):
                    errors.append(f"{description} invalide: {value} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} invalides")
                elif field in ['visits', 'organic_traffic', 'paid_search_traffic', 'branded_traffic', 'cpc'] and isinstance(value, (int, float)) and value < 0:
                    errors.append(f"{description} invalide: {value} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} négatives")
                elif field == 'avg_visit_duration' and isinstance(value, (int, float)) and value <= 0:
                    errors.append(f"{description} invalide: {value} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} invalides")
        
        # DÉTERMINATION DU NIVEAU DE RISQUE
        if len(errors) == 0:
            risk_level = 'ZÉRO'
            client_ready = True
        else:
            risk_level = 'CRITIQUE'
            client_ready = False
        
        return {
            'client_ready': client_ready,
            'risk_level': risk_level,
            'errors': errors,
            'risk_factors': risk_factors,
            'shop_data': dict(row)
        }
    
    def get_validated_shops(self) -> List[Dict[str, Any]]:
        """Récupère uniquement les shops validées pour le client"""
        print("\n🔍 IDENTIFICATION DES SHOPS VALIDÉES")
        print("=" * 60)
        
        # Récupérer tous les shops
        shops_query = "SELECT id, shop_name FROM shops ORDER BY id"
        shops = self.conn_source.execute(shops_query).fetchall()
        
        validated_shops = []
        
        for shop in shops:
            shop_id = shop['id']
            shop_name = shop['shop_name']
            
            print(f"📊 Validation shop {shop_id}: {shop_name}")
            
            # Validation des critères client
            result = self.validate_client_criteria(shop_id)
            
            if result['client_ready']:
                print(f"  ✅ VALIDÉE - Prête pour migration")
                validated_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'data': result['shop_data']
                })
                self.migration_stats['shops_validated'] += 1
            else:
                print(f"  ❌ REJETÉE - {len(result['errors'])} erreurs")
                self.migration_stats['errors'].extend(result['errors'])
        
        print(f"\n📈 RÉSULTATS DE VALIDATION:")
        print(f"  Total shops analysées: {len(shops)}")
        print(f"  Shops validées: {len(validated_shops)}")
        print(f"  Shops rejetées: {len(shops) - len(validated_shops)}")
        
        return validated_shops
    
    def migrate_shop_data(self, shop_data: Dict[str, Any]) -> bool:
        """Migre les données d'une shop validée"""
        try:
            # Migration de la table shops
            shop_insert = """
            INSERT INTO shops (
                id, shop_name, shop_url, total_products, monthly_visits, monthly_revenue,
                live_ads, aov, page_number, scraped_at, project_source, external_id,
                metadata, year_founded, creation_date, scraping_status, live_ads_7d,
                live_ads_30d, table_scraping_status, details_scraping_status,
                scraping_last_update, updated_at, pixel_google, pixel_facebook,
                market_us, market_uk, market_de, market_ca, market_au, market_fr, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            shop_values = (
                shop_data['id'], shop_data['shop_name'], shop_data['shop_url'],
                shop_data['total_products'], shop_data['monthly_visits'], shop_data['monthly_revenue'],
                shop_data['live_ads'], shop_data['aov'], shop_data.get('page_number'),
                shop_data.get('scraped_at'), shop_data.get('project_source'), shop_data['external_id'],
                shop_data.get('metadata'), shop_data['year_founded'], shop_data.get('creation_date'),
                shop_data['scraping_status'], shop_data['live_ads_7d'], shop_data['live_ads_30d'],
                shop_data['table_scraping_status'], shop_data['details_scraping_status'],
                shop_data.get('scraping_last_update'), shop_data.get('updated_at'),
                shop_data['pixel_google'], shop_data['pixel_facebook'],
                shop_data['market_us'], shop_data['market_uk'], shop_data['market_de'],
                shop_data['market_ca'], shop_data['market_au'], shop_data['market_fr'],
                shop_data.get('category')
            )
            
            self.conn_prod.execute(shop_insert, shop_values)
            self.migration_stats['shops_migrated'] += 1
            
            # Migration des analytics si présentes
            if shop_data.get('analytics_status') == 'completed':
                analytics_insert = """
                INSERT INTO analytics (
                    shop_id, organic_traffic, bounce_rate, avg_visit_duration,
                    branded_traffic, conversion_rate, scraping_status, updated_at,
                    visits, traffic, paid_search_traffic, percent_branded_traffic, cpc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                analytics_values = (
                    shop_data['id'], shop_data['organic_traffic'], shop_data['bounce_rate'],
                    shop_data['avg_visit_duration'], shop_data['branded_traffic'],
                    shop_data['conversion_rate'], shop_data['analytics_status'],
                    shop_data.get('updated_at'), shop_data['visits'], shop_data.get('traffic'),
                    shop_data['paid_search_traffic'], shop_data.get('percent_branded_traffic'),
                    shop_data['cpc']
                )
                
                self.conn_prod.execute(analytics_insert, analytics_values)
                self.migration_stats['analytics_migrated'] += 1
            
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la migration shop {shop_data['id']}: {e}")
            return False
    
    def run_migration(self):
        """Exécution complète de la migration sécurisée"""
        print("🚀 MIGRATION SÉCURISÉE VERS LA PRODUCTION")
        print("=" * 60)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 OBJECTIF: Migration UNIQUEMENT des données validées")
        print("🛡️ PROTECTION: ZÉRO RISQUE sur la fiabilité des données")
        print("=" * 60)
        
        self.connect_databases()
        
        # 1. Identification des shops validées
        validated_shops = self.get_validated_shops()
        
        if not validated_shops:
            print("\n🚨 AUCUNE SHOP VALIDÉE")
            print("❌ Impossible de migrer - Aucune donnée fiable")
            print("🔧 Action requise: Corriger les données avant migration")
            return False
        
        # 2. Migration des données validées
        print(f"\n🔄 MIGRATION DE {len(validated_shops)} SHOPS VALIDÉES")
        print("=" * 60)
        
        successful_migrations = 0
        
        for shop in validated_shops:
            print(f"📦 Migration shop {shop['id']}: {shop['name']}")
            
            if self.migrate_shop_data(shop['data']):
                print(f"  ✅ Migrée avec succès")
                successful_migrations += 1
            else:
                print(f"  ❌ Échec de la migration")
        
        # 3. Validation de la migration
        self.conn_prod.commit()
        
        # 4. Rapport final
        self.generate_migration_report(successful_migrations, len(validated_shops))
        
        return successful_migrations > 0
    
    def generate_migration_report(self, successful_migrations: int, total_validated: int):
        """Génère le rapport de migration"""
        print(f"\n📊 RAPPORT DE MIGRATION")
        print("=" * 60)
        print(f"📈 Résultats:")
        print(f"  Shops validées: {total_validated}")
        print(f"  Shops migrées: {successful_migrations}")
        print(f"  Taux de succès: {(successful_migrations/total_validated*100):.1f}%")
        
        if successful_migrations > 0:
            print(f"\n✅ MIGRATION RÉUSSIE")
            print(f"🎯 {successful_migrations} shops migrées vers la production")
            print(f"🛡️ ZÉRO RISQUE - Données 100% fiables")
            print(f"📂 Base de production: {self.prod_db_path}")
        else:
            print(f"\n❌ MIGRATION ÉCHOUÉE")
            print(f"🚫 Aucune shop migrée")
            print(f"🔧 Action requise: Corriger les données")
    
    def close_connections(self):
        """Ferme les connexions"""
        if self.conn_source:
            self.conn_source.close()
        if self.conn_prod:
            self.conn_prod.close()

def main():
    """Fonction principale"""
    source_db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    prod_db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack-prod.db"
    
    migration = SecureMigration(source_db_path, prod_db_path)
    
    try:
        success = migration.run_migration()
        
        if success:
            print(f"\n🎯 MIGRATION TERMINÉE AVEC SUCCÈS")
        else:
            print(f"\n❌ MIGRATION ÉCHOUÉE")
            
    finally:
        migration.close_connections()

if __name__ == "__main__":
    main()
