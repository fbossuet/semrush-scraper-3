#!/usr/bin/env python3
"""
Script d'Identification des Shops Prêtes pour Client
====================================================

Ce script identifie quelles shops peuvent être envoyées au client
SANS RISQUE sur la fiabilité des données, garantissant une qualité
professionnelle et une confiance totale.

Objectif: ZÉRO RISQUE pour le client - Données 100% fiables
Usage: python3 identify_success.py
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class SuccessIdentifier:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.results = {
            'successful_shops': [],
            'failed_shops': [],
            'partial_shops': [],
            'statistics': {}
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
    
    def check_shops_criteria(self, shop_id: int) -> Dict[str, Any]:
        """Vérification des critères pour la table shops"""
        query = """
        SELECT 
            id, shop_name, shop_url, external_id,
            table_scraping_status, details_scraping_status, scraping_status,
            total_products, monthly_visits, monthly_revenue, live_ads, aov, year_founded,
            live_ads_7d, live_ads_30d, pixel_google, pixel_facebook,
            market_us, market_uk, market_de, market_ca, market_au, market_fr
        FROM shops 
        WHERE id = ?
        """
        
        cursor = self.conn.execute(query, (shop_id,))
        shop = cursor.fetchone()
        
        if not shop:
            return {'valid': False, 'errors': ['Shop non trouvé']}
        
        errors = []
        warnings = []
        
        # 1. Validation des statuts
        if shop['table_scraping_status'] != 'table_extracted':
            errors.append(f"table_scraping_status: {shop['table_scraping_status']} (attendu: 'table_extracted')")
        
        if shop['details_scraping_status'] != 'details_extracted':
            errors.append(f"details_scraping_status: {shop['details_scraping_status']} (attendu: 'details_extracted')")
        
        if shop['scraping_status'] != 'completed':
            errors.append(f"scraping_status: {shop['scraping_status']} (attendu: 'completed')")
        
        # 2. Validation des formats
        if not shop['shop_url'] or not shop['shop_url'].startswith(('http://', 'https://')):
            errors.append(f"shop_url: {shop['shop_url']} (format URL invalide)")
        
        if not shop['external_id'] or len(shop['external_id']) != 36:
            errors.append(f"external_id: {shop['external_id']} (format UUID invalide)")
        
        # 3. Validation des métriques de base
        if not shop['total_products'] or shop['total_products'] <= 0:
            errors.append(f"total_products: {shop['total_products']} (doit être > 0)")
        
        if not shop['monthly_visits'] or shop['monthly_visits'] <= 0:
            errors.append(f"monthly_visits: {shop['monthly_visits']} (doit être > 0)")
        
        if not shop['monthly_revenue'] or shop['monthly_revenue'].strip() == '':
            errors.append(f"monthly_revenue: {shop['monthly_revenue']} (doit être présent)")
        
        if shop['live_ads'] is None or (isinstance(shop['live_ads'], (int, float)) and shop['live_ads'] < 0):
            errors.append(f"live_ads: {shop['live_ads']} (doit être >= 0)")
        
        if not shop['aov'] or shop['aov'] <= 0:
            errors.append(f"aov: {shop['aov']} (doit être > 0)")
        
        if not shop['year_founded'] or shop['year_founded'].strip() == '':
            errors.append(f"year_founded: {shop['year_founded']} (doit être présent)")
        
        # 4. Validation des métriques de publicité
        if shop['live_ads_7d'] is None or (isinstance(shop['live_ads_7d'], (int, float)) and shop['live_ads_7d'] < 0):
            errors.append(f"live_ads_7d: {shop['live_ads_7d']} (doit être >= 0)")
        
        if shop['live_ads_30d'] is None or (isinstance(shop['live_ads_30d'], (int, float)) and shop['live_ads_30d'] < 0):
            errors.append(f"live_ads_30d: {shop['live_ads_30d']} (doit être >= 0)")
        
        # 5. Validation des pixels
        if not shop['pixel_google'] or shop['pixel_google'].strip() == '':
            errors.append(f"pixel_google: {shop['pixel_google']} (doit être présent)")
        
        if not shop['pixel_facebook'] or shop['pixel_facebook'].strip() == '':
            errors.append(f"pixel_facebook: {shop['pixel_facebook']} (doit être présent)")
        
        # 6. Validation des marchés (0-1)
        market_fields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr']
        for field in market_fields:
            value = shop[field]
            if value is None or not (isinstance(value, (int, float)) and 0 <= value <= 1):
                errors.append(f"{field}: {value} (doit être entre 0 et 1)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'shop_data': dict(shop)
        }
    
    def check_analytics_criteria(self, shop_id: int) -> Dict[str, Any]:
        """Vérification des critères pour la table analytics"""
        query = """
        SELECT 
            id, shop_id, scraping_status,
            visits, organic_traffic, paid_search_traffic, cpc,
            bounce_rate, avg_visit_duration, branded_traffic, conversion_rate
        FROM analytics 
        WHERE shop_id = ?
        """
        
        cursor = self.conn.execute(query, (shop_id,))
        analytics = cursor.fetchone()
        
        if not analytics:
            return {'valid': False, 'errors': ['Aucun enregistrement analytics trouvé']}
        
        errors = []
        warnings = []
        
        # 1. Validation du statut
        if analytics['scraping_status'] != 'completed':
            errors.append(f"scraping_status: {analytics['scraping_status']} (attendu: 'completed')")
        
        # 2. Validation des métriques obligatoires
        required_metrics = {
            'visits': 'Visites totales',
            'organic_traffic': 'Trafic organique',
            'paid_search_traffic': 'Trafic payant',
            'cpc': 'Coût par clic',
            'bounce_rate': 'Taux de rebond',
            'avg_visit_duration': 'Durée moyenne des visites',
            'branded_traffic': 'Trafic de marque',
            'conversion_rate': 'Taux de conversion'
        }
        
        for field, description in required_metrics.items():
            if analytics[field] is None:
                errors.append(f"{field}: {description} manquante")
        
        # 3. Validation des formats numériques
        numeric_fields = ['visits', 'organic_traffic', 'paid_search_traffic', 'branded_traffic']
        for field in numeric_fields:
            if analytics[field] is not None and isinstance(analytics[field], (int, float)) and analytics[field] < 0:
                errors.append(f"{field}: {analytics[field]} (doit être >= 0)")
        
        decimal_fields = ['bounce_rate', 'conversion_rate']
        for field in decimal_fields:
            if analytics[field] is not None and isinstance(analytics[field], (int, float)) and not (0 <= analytics[field] <= 1):
                errors.append(f"{field}: {analytics[field]} (doit être entre 0 et 1)")
        
        if analytics['cpc'] is not None and isinstance(analytics['cpc'], (int, float)) and analytics['cpc'] < 0:
            errors.append(f"cpc: {analytics['cpc']} (doit être >= 0)")
        
        if analytics['avg_visit_duration'] is not None and isinstance(analytics['avg_visit_duration'], (int, float)) and analytics['avg_visit_duration'] <= 0:
            errors.append(f"avg_visit_duration: {analytics['avg_visit_duration']} (doit être > 0)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'analytics_data': dict(analytics)
        }
    
    def identify_successful_shops(self):
        """Identification des shops prêtes pour client (ZÉRO RISQUE)"""
        print("\n🔍 IDENTIFICATION DES SHOPS PRÊTES POUR CLIENT")
        print("=" * 60)
        print("🎯 OBJECTIF: ZÉRO RISQUE - Données 100% fiables pour le client")
        print("=" * 60)
        
        # Récupérer tous les shops
        shops_query = "SELECT id, shop_name FROM shops ORDER BY id"
        shops = self.conn.execute(shops_query).fetchall()
        
        successful_shops = []
        failed_shops = []
        partial_shops = []
        
        for shop in shops:
            shop_id = shop['id']
            shop_name = shop['shop_name']
            
            print(f"\n📊 Analyse shop {shop_id}: {shop_name}")
            print("-" * 40)
            
            # Vérifier les critères shops
            shops_result = self.check_shops_criteria(shop_id)
            shops_valid = shops_result['valid']
            shops_errors = shops_result['errors']
            
            if shops_valid:
                print("✅ Critères shops: VALIDES")
            else:
                print("❌ Critères shops: ÉCHEC")
                for error in shops_errors:
                    print(f"  - {error}")
            
            # Vérifier les critères analytics
            analytics_result = self.check_analytics_criteria(shop_id)
            analytics_valid = analytics_result['valid']
            analytics_errors = analytics_result['errors']
            
            if analytics_valid:
                print("✅ Critères analytics: VALIDES")
            else:
                print("❌ Critères analytics: ÉCHEC")
                for error in analytics_errors:
                    print(f"  - {error}")
            
            # Déterminer le statut final (CRITÈRES CLIENT)
            if shops_valid and analytics_valid:
                print("✅ RÉSULTAT: PRÊT POUR CLIENT - ZÉRO RISQUE")
                print("   🎯 Cette shop peut être envoyée au client en toute confiance")
                successful_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'shops_data': shops_result['shop_data'],
                    'analytics_data': analytics_result['analytics_data'],
                    'client_ready': True,
                    'risk_level': 'ZÉRO'
                })
            elif shops_valid or analytics_valid:
                print("⚠️ RÉSULTAT: RISQUE ÉLEVÉ - NE PAS ENVOYER AU CLIENT")
                print("   🚨 Données incomplètes - Risque de perte de confiance client")
                partial_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'shops_valid': shops_valid,
                    'analytics_valid': analytics_valid,
                    'shops_errors': shops_errors,
                    'analytics_errors': analytics_errors,
                    'client_ready': False,
                    'risk_level': 'ÉLEVÉ'
                })
            else:
                print("❌ RÉSULTAT: RISQUE CRITIQUE - INTERDIRE AU CLIENT")
                print("   🚫 Données non fiables - Risque de réputation")
                failed_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'shops_errors': shops_errors,
                    'analytics_errors': analytics_errors,
                    'client_ready': False,
                    'risk_level': 'CRITIQUE'
                })
        
        self.results['successful_shops'] = successful_shops
        self.results['failed_shops'] = failed_shops
        self.results['partial_shops'] = partial_shops
        
        return {
            'successful': len(successful_shops),
            'failed': len(failed_shops),
            'partial': len(partial_shops),
            'total': len(shops)
        }
    
    def generate_statistics(self):
        """Génération des statistiques détaillées"""
        print("\n📊 STATISTIQUES DÉTAILLÉES")
        print("=" * 50)
        
        stats = self.results['statistics']
        
        # Statistiques générales
        total_shops = len(self.results['successful_shops']) + len(self.results['failed_shops']) + len(self.results['partial_shops'])
        successful_count = len(self.results['successful_shops'])
        failed_count = len(self.results['failed_shops'])
        partial_count = len(self.results['partial_shops'])
        
        print(f"📈 Résultats globaux (CRITÈRES CLIENT):")
        print(f"  Total shops analysées: {total_shops}")
        print(f"  ✅ PRÊTES POUR CLIENT (ZÉRO RISQUE): {successful_count} ({(successful_count/total_shops*100):.1f}%)")
        print(f"  ⚠️ RISQUE ÉLEVÉ (NE PAS ENVOYER): {partial_count} ({(partial_count/total_shops*100):.1f}%)")
        print(f"  ❌ RISQUE CRITIQUE (INTERDIRE): {failed_count} ({(failed_count/total_shops*100):.1f}%)")
        
        # Recommandations client
        if successful_count > 0:
            print(f"\n🎯 RECOMMANDATION CLIENT:")
            print(f"  ✅ Vous pouvez envoyer {successful_count} shops au client en toute confiance")
            print(f"  🛡️ ZÉRO RISQUE sur la fiabilité des données")
        else:
            print(f"\n🚨 ALERTE CLIENT:")
            print(f"  ❌ AUCUNE shop prête pour le client")
            print(f"  🚫 RISQUE ÉLEVÉ de perte de confiance client")
            print(f"  🔧 Action requise: Corriger les données avant envoi")
        
        # Détail des shops prêtes pour client
        if successful_count > 0:
            print(f"\n✅ SHOPS PRÊTES POUR CLIENT ({successful_count}):")
            print("   🎯 Ces shops peuvent être envoyées au client SANS RISQUE")
            for shop in self.results['successful_shops']:
                print(f"  - {shop['id']}: {shop['name']} (RISQUE: {shop.get('risk_level', 'ZÉRO')})")
        
        # Détail des shops à risque élevé
        if partial_count > 0:
            print(f"\n⚠️ SHOPS À RISQUE ÉLEVÉ ({partial_count}):")
            print("   🚨 NE PAS ENVOYER AU CLIENT - Données incomplètes")
            for shop in self.results['partial_shops']:
                status = []
                if shop['shops_valid']:
                    status.append("shops ✅")
                else:
                    status.append("shops ❌")
                if shop['analytics_valid']:
                    status.append("analytics ✅")
                else:
                    status.append("analytics ❌")
                print(f"  - {shop['id']}: {shop['name']} ({', '.join(status)}) - RISQUE: {shop.get('risk_level', 'ÉLEVÉ')}")
        
        # Détail des shops à risque critique
        if failed_count > 0:
            print(f"\n❌ SHOPS À RISQUE CRITIQUE ({failed_count}):")
            print("   🚫 INTERDIRE AU CLIENT - Données non fiables")
            for shop in self.results['failed_shops']:
                print(f"  - {shop['id']}: {shop['name']} - RISQUE: {shop.get('risk_level', 'CRITIQUE')}")
        
        return {
            'total_shops': total_shops,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'partial_count': partial_count,
            'success_rate': (successful_count/total_shops*100) if total_shops > 0 else 0
        }
    
    def export_results(self, output_file: str = None):
        """Export des résultats vers un fichier Markdown"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"success_analysis_{timestamp}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 📊 Analyse des Shops Scrapées avec Succès\n\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Statistiques
                stats = self.results['statistics']
                total_shops = stats.get('total_shops', 0)
                f.write("## 📈 Résultats Globaux\n\n")
                f.write(f"- **Total shops:** {total_shops}\n")
                if total_shops > 0:
                    f.write(f"- **Succès total:** {stats.get('successful_count', 0)} ({(stats.get('successful_count', 0)/total_shops*100):.1f}%)\n")
                    f.write(f"- **Succès partiel:** {stats.get('partial_count', 0)} ({(stats.get('partial_count', 0)/total_shops*100):.1f}%)\n")
                    f.write(f"- **Échec total:** {stats.get('failed_count', 0)} ({(stats.get('failed_count', 0)/total_shops*100):.1f}%)\n\n")
                else:
                    f.write(f"- **Succès total:** {stats.get('successful_count', 0)} (0.0%)\n")
                    f.write(f"- **Succès partiel:** {stats.get('partial_count', 0)} (0.0%)\n")
                    f.write(f"- **Échec total:** {stats.get('failed_count', 0)} (0.0%)\n\n")
                
                # Détail des succès
                if self.results['successful_shops']:
                    f.write("## ✅ Shops avec Succès Total\n\n")
                    for shop in self.results['successful_shops']:
                        f.write(f"- **{shop['id']}:** {shop['name']}\n")
                    f.write("\n")
                
                # Détail des succès partiels
                if self.results['partial_shops']:
                    f.write("## ⚠️ Shops avec Succès Partiel\n\n")
                    for shop in self.results['partial_shops']:
                        status = []
                        if shop['shops_valid']:
                            status.append("shops ✅")
                        else:
                            status.append("shops ❌")
                        if shop['analytics_valid']:
                            status.append("analytics ✅")
                        else:
                            status.append("analytics ❌")
                        f.write(f"- **{shop['id']}:** {shop['name']} ({', '.join(status)})\n")
                    f.write("\n")
                
                # Détail des échecs
                if self.results['failed_shops']:
                    f.write("## ❌ Shops en Échec Total\n\n")
                    for shop in self.results['failed_shops']:
                        f.write(f"### {shop['id']}: {shop['name']}\n\n")
                        if shop['shops_errors']:
                            f.write("**Erreurs shops:**\n")
                            for error in shop['shops_errors']:
                                f.write(f"- {error}\n")
                            f.write("\n")
                        if shop['analytics_errors']:
                            f.write("**Erreurs analytics:**\n")
                            for error in shop['analytics_errors']:
                                f.write(f"- {error}\n")
                            f.write("\n")
            
            print(f"📄 Résultats exportés vers: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
    
    def run_analysis(self):
        """Exécution complète de l'analyse"""
        print("🚀 DÉMARRAGE DE L'IDENTIFICATION DES SUCCÈS")
        print("=" * 60)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.connect()
        
        # Identification des succès
        stats = self.identify_successful_shops()
        self.results['statistics'] = stats
        
        # Génération des statistiques
        self.generate_statistics()
        
        # Export des résultats
        self.export_results()
        
        print(f"\n✅ ANALYSE TERMINÉE")
        print("=" * 60)
        
        if self.conn:
            self.conn.close()

def main():
    """Fonction principale"""
    db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    
    identifier = SuccessIdentifier(db_path)
    identifier.run_analysis()

if __name__ == "__main__":
    main()
