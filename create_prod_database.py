#!/usr/bin/env python3
"""
Création de la Base de Données de Production
===========================================

Ce script crée la base de données de production trendtrack-prod.db
avec exactement la même structure que la base de test.

Usage: python3 create_prod_database.py
"""

import sqlite3
import os
import shutil
from datetime import datetime

class ProductionDatabaseCreator:
    def __init__(self, source_db_path: str, prod_db_path: str):
        self.source_db_path = source_db_path
        self.prod_db_path = prod_db_path
        self.conn_source = None
        self.conn_prod = None
    
    def connect_source(self):
        """Connexion à la base source"""
        try:
            self.conn_source = sqlite3.connect(self.source_db_path)
            self.conn_source.row_factory = sqlite3.Row
            print(f"✅ Connexion à la base source: {self.source_db_path}")
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion source: {e}")
            raise
    
    def create_production_database(self):
        """Création de la base de production avec la même structure"""
        try:
            # Supprimer l'ancienne base si elle existe
            if os.path.exists(self.prod_db_path):
                os.remove(self.prod_db_path)
                print(f"🗑️ Ancienne base supprimée: {self.prod_db_path}")
            
            # Créer la nouvelle base
            self.conn_prod = sqlite3.connect(self.prod_db_path)
            self.conn_prod.row_factory = sqlite3.Row
            print(f"✅ Base de production créée: {self.prod_db_path}")
            
            # Récupérer le schéma de la base source
            schema_queries = self.get_schema_queries()
            
            # Exécuter toutes les requêtes de création
            for query in schema_queries:
                if query.strip():
                    self.conn_prod.execute(query)
            
            self.conn_prod.commit()
            print("✅ Structure de la base de production créée")
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la création: {e}")
            raise
    
    def get_schema_queries(self):
        """Récupère toutes les requêtes de création du schéma"""
        queries = []
        
        # Tables principales
        queries.append("""
        CREATE TABLE IF NOT EXISTS "shops" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT NOT NULL,
            shop_url TEXT,
            total_products INTEGER,
            monthly_visits INTEGER,
            monthly_revenue TEXT,
            live_ads INTEGER,
            aov NUMERIC,
            page_number TEXT,
            scraped_at TEXT,
            project_source TEXT,
            external_id TEXT,
            metadata TEXT,
            year_founded TEXT,
            creation_date TEXT,
            scraping_status TEXT DEFAULT 'pending',
            live_ads_7d INTEGER,
            live_ads_30d INTEGER,
            table_scraping_status TEXT DEFAULT 'pending',
            details_scraping_status TEXT DEFAULT 'pending',
            scraping_last_update TEXT,
            updated_at TEXT,
            pixel_google TEXT,
            pixel_facebook TEXT,
            market_us NUMERIC,
            market_uk NUMERIC,
            market_de NUMERIC,
            market_ca NUMERIC,
            market_au NUMERIC,
            market_fr NUMERIC,
            category TEXT
        )
        """)
        
        queries.append("""
        CREATE TABLE IF NOT EXISTS "analytics" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            organic_traffic INTEGER,
            bounce_rate NUMERIC,
            avg_visit_duration TEXT,
            branded_traffic INTEGER,
            conversion_rate TEXT,
            scraping_status TEXT DEFAULT 'completed',
            updated_at TEXT,
            visits INTEGER,
            traffic INTEGER,
            paid_search_traffic INTEGER,
            percent_branded_traffic NUMERIC,
            cpc NUMERIC,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
        """)
        
        # Tables de support
        queries.append("""
        CREATE TABLE IF NOT EXISTS scraping_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER,
            error_message TEXT,
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
        """)
        
        queries.append("""
        CREATE TABLE IF NOT EXISTS processing_locks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lock_name TEXT UNIQUE NOT NULL,
            process_id INTEGER,
            acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
        """)
        
        queries.append("""
        CREATE TABLE IF NOT EXISTS selector_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            selector_name TEXT NOT NULL,
            success BOOLEAN,
            response_time_ms INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            page_load_time_ms INTEGER
        )
        """)
        
        # Index
        queries.extend([
            "CREATE INDEX IF NOT EXISTS idx_analytics_shop_id ON analytics(shop_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_scraping_status ON analytics(scraping_status)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_shop_id_unique ON analytics(shop_id)",
            "CREATE INDEX IF NOT EXISTS idx_shops_scraping_status ON shops(scraping_status)",
            "CREATE INDEX IF NOT EXISTS idx_shops_scraping_last_update ON shops(scraping_last_update)",
            "CREATE INDEX IF NOT EXISTS idx_shops_shop_url ON shops(shop_url)",
            "CREATE INDEX IF NOT EXISTS idx_processing_locks_lock_name ON processing_locks(lock_name)",
            "CREATE INDEX IF NOT EXISTS idx_selector_performance_selector_name ON selector_performance(selector_name)",
            "CREATE INDEX IF NOT EXISTS idx_selector_performance_timestamp ON selector_performance(timestamp)"
        ])
        
        return queries
    
    def verify_structure(self):
        """Vérifie que la structure est identique"""
        try:
            # Récupérer les tables de la base source (exclure les tables de backup)
            source_tables = self.conn_source.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE '%backup%' 
                ORDER BY name
            """).fetchall()
            
            # Récupérer les tables de la base prod
            prod_tables = self.conn_prod.execute("""
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
            """).fetchall()
            
            source_table_names = [row[0] for row in source_tables]
            prod_table_names = [row[0] for row in prod_tables]
            
            print(f"\n📊 VÉRIFICATION DE LA STRUCTURE:")
            print(f"  Tables source (hors backup): {len(source_table_names)}")
            print(f"  Tables prod: {len(prod_table_names)}")
            
            if source_table_names == prod_table_names:
                print("✅ Structure identique")
                return True
            else:
                print("❌ Structure différente")
                print(f"  Manquantes: {set(source_table_names) - set(prod_table_names)}")
                print(f"  En trop: {set(prod_table_names) - set(source_table_names)}")
                return False
                
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            return False
    
    def create_backup(self):
        """Crée une sauvegarde de la base source"""
        backup_path = f"{self.source_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copy2(self.source_db_path, backup_path)
            print(f"💾 Sauvegarde créée: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None
    
    def run(self):
        """Exécution complète de la création"""
        print("🚀 CRÉATION DE LA BASE DE PRODUCTION")
        print("=" * 60)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Source: {self.source_db_path}")
        print(f"📂 Production: {self.prod_db_path}")
        print("=" * 60)
        
        try:
            # 1. Connexion à la base source
            self.connect_source()
            
            # 2. Création de la base de production
            self.create_production_database()
            
            # 3. Vérification de la structure
            if self.verify_structure():
                print("\n✅ BASE DE PRODUCTION CRÉÉE AVEC SUCCÈS")
                print("=" * 60)
                print("📋 Prochaines étapes:")
                print("  1. Exécuter les scripts de validation")
                print("  2. Identifier les données valides")
                print("  3. Migrer uniquement les données validées")
                print("  4. Vérifier la migration")
            else:
                print("\n❌ ERREUR DANS LA STRUCTURE")
                return False
            
            # 4. Création d'une sauvegarde
            self.create_backup()
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            return False
        
        finally:
            if self.conn_source:
                self.conn_source.close()
            if self.conn_prod:
                self.conn_prod.close()

def main():
    """Fonction principale"""
    source_db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    prod_db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack-prod.db"
    
    creator = ProductionDatabaseCreator(source_db_path, prod_db_path)
    success = creator.run()
    
    if success:
        print(f"\n🎯 BASE DE PRODUCTION PRÊTE: {prod_db_path}")
    else:
        print(f"\n❌ ÉCHEC DE LA CRÉATION")

if __name__ == "__main__":
    main()
