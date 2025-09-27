#!/usr/bin/env python3
"""
Workflow Client - Validation Sans Correction
===========================================

Ce script propose un workflow pour identifier les shops prêtes
pour le client SANS correction automatique et SANS rapport client.

Usage: python3 workflow_client.py
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class ClientWorkflow:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.results = {
            'client_ready_shops': [],
            'high_risk_shops': [],
            'critical_risk_shops': [],
            'workflow_summary': {}
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
    
    def validate_client_criteria(self, shop_id: int) -> Dict[str, Any]:
        """Validation des critères client SANS correction"""
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
        
        cursor = self.conn.execute(query, (shop_id,))
        row = cursor.fetchone()
        
        if not row:
            return {'client_ready': False, 'risk_level': 'CRITIQUE', 'errors': ['Shop non trouvé']}
        
        errors = []
        risk_factors = []
        
        # CRITÈRES CLIENT - VALIDATION SEULEMENT
        
        # 1. VALIDATION DES STATUTS
        if row['table_scraping_status'] != 'table_extracted':
            errors.append(f"table_scraping_status: '{row['table_scraping_status']}' (attendu: 'table_extracted')")
            risk_factors.append("Phase 1 TrendTrack non terminée")
        
        if row['details_scraping_status'] != 'details_extracted':
            errors.append(f"details_scraping_status: '{row['details_scraping_status']}' (attendu: 'details_extracted')")
            risk_factors.append("Phase 3 TrendTrack non terminée")
        
        if row['scraping_status'] != 'completed':
            errors.append(f"scraping_status: '{row['scraping_status']}' (attendu: 'completed')")
            risk_factors.append("Scraping TrendTrack non terminé")
        
        # 2. VALIDATION ANALYTICS
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
        elif len(errors) <= 3:
            risk_level = 'ÉLEVÉ'
            client_ready = False
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
    
    def run_workflow(self):
        """Exécution du workflow client"""
        print("🚀 WORKFLOW CLIENT - VALIDATION SANS CORRECTION")
        print("=" * 60)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 OBJECTIF: Identifier les shops prêtes pour client")
        print("⚠️ CONTRAINTE: Aucune correction automatique")
        print("=" * 60)
        
        self.connect()
        
        # Récupérer tous les shops
        shops_query = "SELECT id, shop_name FROM shops ORDER BY id"
        shops = self.conn.execute(shops_query).fetchall()
        
        client_ready_shops = []
        high_risk_shops = []
        critical_risk_shops = []
        
        print(f"\n🔍 VALIDATION DE {len(shops)} SHOPS")
        print("=" * 60)
        
        for shop in shops:
            shop_id = shop['id']
            shop_name = shop['shop_name']
            
            print(f"\n📊 Shop {shop_id}: {shop_name}")
            print("-" * 40)
            
            # Validation des critères client
            result = self.validate_client_criteria(shop_id)
            
            if result['client_ready']:
                print("✅ PRÊT POUR CLIENT - ZÉRO RISQUE")
                print("   🎯 Cette shop peut être envoyée au client")
                client_ready_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'risk_level': result['risk_level'],
                    'shop_data': result['shop_data']
                })
            elif result['risk_level'] == 'ÉLEVÉ':
                print("⚠️ RISQUE ÉLEVÉ - NE PAS ENVOYER")
                print("   🚨 Données incomplètes")
                high_risk_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'risk_level': result['risk_level'],
                    'errors': result['errors'],
                    'risk_factors': result['risk_factors']
                })
            else:
                print("❌ RISQUE CRITIQUE - INTERDIRE")
                print("   🚫 Données non fiables")
                critical_risk_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'risk_level': result['risk_level'],
                    'errors': result['errors'],
                    'risk_factors': result['risk_factors']
                })
            
            # Affichage des erreurs si présentes
            if result['errors']:
                print("   📋 Erreurs détectées:")
                for error in result['errors'][:3]:  # Limiter à 3 erreurs pour la lisibilité
                    print(f"     - {error}")
                if len(result['errors']) > 3:
                    print(f"     ... et {len(result['errors']) - 3} autres erreurs")
        
        self.results['client_ready_shops'] = client_ready_shops
        self.results['high_risk_shops'] = high_risk_shops
        self.results['critical_risk_shops'] = critical_risk_shops
        
        # Génération du résumé
        self.generate_summary()
        
        print(f"\n✅ WORKFLOW TERMINÉ")
        print("=" * 60)
        
        if self.conn:
            self.conn.close()
    
    def generate_summary(self):
        """Génération du résumé du workflow"""
        print("\n📊 RÉSUMÉ DU WORKFLOW CLIENT")
        print("=" * 60)
        
        total_shops = len(self.results['client_ready_shops']) + len(self.results['high_risk_shops']) + len(self.results['critical_risk_shops'])
        client_ready_count = len(self.results['client_ready_shops'])
        high_risk_count = len(self.results['high_risk_shops'])
        critical_risk_count = len(self.results['critical_risk_shops'])
        
        print(f"📈 Résultats globaux:")
        print(f"  Total shops analysées: {total_shops}")
        print(f"  ✅ PRÊTES POUR CLIENT: {client_ready_count} ({(client_ready_count/total_shops*100):.1f}%)")
        print(f"  ⚠️ RISQUE ÉLEVÉ: {high_risk_count} ({(high_risk_count/total_shops*100):.1f}%)")
        print(f"  ❌ RISQUE CRITIQUE: {critical_risk_count} ({(critical_risk_count/total_shops*100):.1f}%)")
        
        # Recommandations
        if client_ready_count > 0:
            print(f"\n🎯 RECOMMANDATION:")
            print(f"  ✅ Vous pouvez envoyer {client_ready_count} shops au client")
            print(f"  🛡️ ZÉRO RISQUE sur la fiabilité des données")
            
            print(f"\n📋 SHOPS PRÊTES POUR CLIENT:")
            for shop in self.results['client_ready_shops']:
                print(f"  - {shop['id']}: {shop['name']}")
        else:
            print(f"\n🚨 ALERTE:")
            print(f"  ❌ AUCUNE shop prête pour le client")
            print(f"  🚫 RISQUE ÉLEVÉ de perte de confiance client")
            print(f"  🔧 Action requise: Corriger les données manuellement")
        
        # Actions recommandées
        if high_risk_count > 0 or critical_risk_count > 0:
            print(f"\n🔧 ACTIONS RECOMMANDÉES:")
            print(f"  • Corriger les données des shops à risque")
            print(f"  • Re-exécuter le workflow après corrections")
            print(f"  • Valider chaque correction manuellement")
        
        return {
            'total_shops': total_shops,
            'client_ready_count': client_ready_count,
            'high_risk_count': high_risk_count,
            'critical_risk_count': critical_risk_count,
            'client_ready_percentage': (client_ready_count/total_shops*100) if total_shops > 0 else 0
        }

def main():
    """Fonction principale"""
    db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    
    workflow = ClientWorkflow(db_path)
    workflow.run_workflow()

if __name__ == "__main__":
    main()
