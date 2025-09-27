#!/usr/bin/env python3
"""
Script de Validation Client - ZÉRO RISQUE
==========================================

Ce script garantit la qualité des données pour l'envoi au client
avec des critères de validation ULTRA-STRICTS pour éliminer
tout risque sur la fiabilité des données.

Objectif: PROTECTION TOTALE de la réputation client
Usage: python3 client_validation.py
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class ClientValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.results = {
            'client_ready_shops': [],
            'high_risk_shops': [],
            'critical_risk_shops': [],
            'validation_summary': {}
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
        """Validation ULTRA-STRICTE pour critères client"""
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
        warnings = []
        risk_factors = []
        
        # CRITÈRES ULTRA-STRICTS POUR CLIENT
        
        # 1. VALIDATION DES STATUTS (OBLIGATOIRE)
        if row['table_scraping_status'] != 'table_extracted':
            errors.append(f"STATUT CRITIQUE: table_scraping_status = '{row['table_scraping_status']}' (attendu: 'table_extracted')")
            risk_factors.append("Phase 1 TrendTrack non terminée")
        
        if row['details_scraping_status'] != 'details_extracted':
            errors.append(f"STATUT CRITIQUE: details_scraping_status = '{row['details_scraping_status']}' (attendu: 'details_extracted')")
            risk_factors.append("Phase 3 TrendTrack non terminée")
        
        if row['scraping_status'] != 'completed':
            errors.append(f"STATUT CRITIQUE: scraping_status = '{row['scraping_status']}' (attendu: 'completed')")
            risk_factors.append("Scraping TrendTrack non terminé")
        
        # 2. VALIDATION ANALYTICS (OBLIGATOIRE)
        if not row['analytics_status']:
            errors.append("ANALYTICS MANQUANTES: Aucun enregistrement analytics")
            risk_factors.append("Données Noxtools manquantes")
        elif row['analytics_status'] != 'completed':
            errors.append(f"ANALYTICS INCOMPLÈTES: scraping_status = '{row['analytics_status']}' (attendu: 'completed')")
            risk_factors.append("Scraping Noxtools non terminé")
        
        # 3. VALIDATION DES MÉTRIQUES CRITIQUES (OBLIGATOIRE)
        critical_metrics = {
            'total_products': (row['total_products'], 'Nombre de produits', '> 0'),
            'monthly_visits': (row['monthly_visits'], 'Visites mensuelles', '> 0'),
            'monthly_revenue': (row['monthly_revenue'], 'Revenus mensuels', 'présent et non vide'),
            'aov': (row['aov'], 'Average Order Value', '> 0'),
            'year_founded': (row['year_founded'], 'Année de création', 'présent et non vide')
        }
        
        for field, (value, description, requirement) in critical_metrics.items():
            if not value or (isinstance(value, str) and value.strip() == ''):
                errors.append(f"MÉTRIQUE CRITIQUE MANQUANTE: {description} ({requirement})")
                risk_factors.append(f"Données {description.lower()} manquantes")
            elif field in ['total_products', 'monthly_visits', 'aov'] and value <= 0:
                errors.append(f"MÉTRIQUE CRITIQUE INVALIDE: {description} = {value} ({requirement})")
                risk_factors.append(f"Données {description.lower()} invalides")
        
        # 4. VALIDATION DES PUBLICITÉS (OBLIGATOIRE)
        ad_metrics = {
            'live_ads': (row['live_ads'], 'Publicités actives', '>= 0'),
            'live_ads_7d': (row['live_ads_7d'], 'Publicités 7 jours', '>= 0'),
            'live_ads_30d': (row['live_ads_30d'], 'Publicités 30 jours', '>= 0')
        }
        
        for field, (value, description, requirement) in ad_metrics.items():
            if value is None:
                errors.append(f"PUBLICITÉ MANQUANTE: {description} ({requirement})")
                risk_factors.append(f"Données {description.lower()} manquantes")
            elif isinstance(value, (int, float)) and value < 0:
                errors.append(f"PUBLICITÉ INVALIDE: {description} = {value} ({requirement})")
                risk_factors.append(f"Données {description.lower()} négatives")
        
        # 5. VALIDATION DES PIXELS (OBLIGATOIRE)
        if not row['pixel_google'] or row['pixel_google'].strip() == '':
            errors.append("PIXEL GOOGLE MANQUANT: Détection Google Analytics requise")
            risk_factors.append("Pixel Google manquant")
        
        if not row['pixel_facebook'] or row['pixel_facebook'].strip() == '':
            errors.append("PIXEL FACEBOOK MANQUANT: Détection Facebook Pixel requise")
            risk_factors.append("Pixel Facebook manquant")
        
        # 6. VALIDATION DES MARCHÉS (OBLIGATOIRE)
        market_fields = ['market_us', 'market_uk', 'market_de', 'market_ca', 'market_au', 'market_fr']
        for field in market_fields:
            value = row[field]
            if value is None or not (isinstance(value, (int, float)) and 0 <= value <= 1):
                errors.append(f"MARCHÉ INVALIDE: {field} = {value} (doit être entre 0 et 1)")
                risk_factors.append(f"Données marché {field} invalides")
        
        # 7. VALIDATION DES MÉTRIQUES ANALYTICS (OBLIGATOIRE)
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
                    errors.append(f"ANALYTICS MANQUANTE: {description} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} manquantes")
                elif field in ['bounce_rate', 'conversion_rate'] and isinstance(value, (int, float)) and not (0 <= value <= 1):
                    errors.append(f"ANALYTICS INVALIDE: {description} = {value} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} invalides")
                elif field in ['visits', 'organic_traffic', 'paid_search_traffic', 'branded_traffic', 'cpc'] and isinstance(value, (int, float)) and value < 0:
                    errors.append(f"ANALYTICS INVALIDE: {description} = {value} ({requirement})")
                    risk_factors.append(f"Données {description.lower()} négatives")
                elif field == 'avg_visit_duration' and isinstance(value, (int, float)) and value <= 0:
                    errors.append(f"ANALYTICS INVALIDE: {description} = {value} ({requirement})")
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
            'warnings': warnings,
            'risk_factors': risk_factors,
            'shop_data': dict(row)
        }
    
    def validate_all_shops(self):
        """Validation de toutes les shops pour critères client"""
        print("\n🔍 VALIDATION CLIENT - CRITÈRES ULTRA-STRICTS")
        print("=" * 70)
        print("🎯 OBJECTIF: ZÉRO RISQUE - Protection totale de la réputation client")
        print("=" * 70)
        
        # Récupérer tous les shops
        shops_query = "SELECT id, shop_name FROM shops ORDER BY id"
        shops = self.conn.execute(shops_query).fetchall()
        
        client_ready_shops = []
        high_risk_shops = []
        critical_risk_shops = []
        
        for shop in shops:
            shop_id = shop['id']
            shop_name = shop['shop_name']
            
            print(f"\n📊 Validation shop {shop_id}: {shop_name}")
            print("-" * 50)
            
            # Validation des critères client
            result = self.validate_client_criteria(shop_id)
            
            if result['client_ready']:
                print("✅ RÉSULTAT: PRÊT POUR CLIENT - ZÉRO RISQUE")
                print("   🎯 Cette shop peut être envoyée au client en toute confiance")
                print("   🛡️ Protection totale de la réputation client")
                client_ready_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'risk_level': result['risk_level'],
                    'shop_data': result['shop_data']
                })
            elif result['risk_level'] == 'ÉLEVÉ':
                print("⚠️ RÉSULTAT: RISQUE ÉLEVÉ - NE PAS ENVOYER AU CLIENT")
                print("   🚨 Données incomplètes - Risque de perte de confiance client")
                print("   🔧 Action requise: Corriger les données avant envoi")
                high_risk_shops.append({
                    'id': shop_id,
                    'name': shop_name,
                    'risk_level': result['risk_level'],
                    'errors': result['errors'],
                    'risk_factors': result['risk_factors']
                })
            else:
                print("❌ RÉSULTAT: RISQUE CRITIQUE - INTERDIRE AU CLIENT")
                print("   🚫 Données non fiables - Risque de réputation")
                print("   🔧 Action requise: Refonte complète des données")
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
                for error in result['errors'][:5]:  # Limiter à 5 erreurs pour la lisibilité
                    print(f"     - {error}")
                if len(result['errors']) > 5:
                    print(f"     ... et {len(result['errors']) - 5} autres erreurs")
        
        self.results['client_ready_shops'] = client_ready_shops
        self.results['high_risk_shops'] = high_risk_shops
        self.results['critical_risk_shops'] = critical_risk_shops
        
        return {
            'client_ready': len(client_ready_shops),
            'high_risk': len(high_risk_shops),
            'critical_risk': len(critical_risk_shops),
            'total': len(shops)
        }
    
    def generate_client_report(self):
        """Génération du rapport client"""
        print("\n📊 RAPPORT CLIENT - VALIDATION ULTRA-STRICTE")
        print("=" * 70)
        
        stats = self.results['validation_summary']
        total_shops = len(self.results['client_ready_shops']) + len(self.results['high_risk_shops']) + len(self.results['critical_risk_shops'])
        client_ready_count = len(self.results['client_ready_shops'])
        high_risk_count = len(self.results['high_risk_shops'])
        critical_risk_count = len(self.results['critical_risk_shops'])
        
        print(f"📈 Résultats globaux (CRITÈRES CLIENT ULTRA-STRICTS):")
        print(f"  Total shops analysées: {total_shops}")
        print(f"  ✅ PRÊTES POUR CLIENT (ZÉRO RISQUE): {client_ready_count} ({(client_ready_count/total_shops*100):.1f}%)")
        print(f"  ⚠️ RISQUE ÉLEVÉ (NE PAS ENVOYER): {high_risk_count} ({(high_risk_count/total_shops*100):.1f}%)")
        print(f"  ❌ RISQUE CRITIQUE (INTERDIRE): {critical_risk_count} ({(critical_risk_count/total_shops*100):.1f}%)")
        
        # Recommandations client
        if client_ready_count > 0:
            print(f"\n🎯 RECOMMANDATION CLIENT:")
            print(f"  ✅ Vous pouvez envoyer {client_ready_count} shops au client en toute confiance")
            print(f"  🛡️ ZÉRO RISQUE sur la fiabilité des données")
            print(f"  🏆 Protection totale de votre réputation client")
        else:
            print(f"\n🚨 ALERTE CLIENT CRITIQUE:")
            print(f"  ❌ AUCUNE shop prête pour le client")
            print(f"  🚫 RISQUE ÉLEVÉ de perte de confiance client")
            print(f"  🔧 Action requise: Corriger les données avant envoi")
            print(f"  ⚠️ Ne pas envoyer de données au client dans cet état")
        
        # Détail des shops prêtes pour client
        if client_ready_count > 0:
            print(f"\n✅ SHOPS PRÊTES POUR CLIENT ({client_ready_count}):")
            print("   🎯 Ces shops peuvent être envoyées au client SANS RISQUE")
            for shop in self.results['client_ready_shops']:
                print(f"  - {shop['id']}: {shop['name']} (RISQUE: {shop['risk_level']})")
        
        # Détail des shops à risque élevé
        if high_risk_count > 0:
            print(f"\n⚠️ SHOPS À RISQUE ÉLEVÉ ({high_risk_count}):")
            print("   🚨 NE PAS ENVOYER AU CLIENT - Données incomplètes")
            for shop in self.results['high_risk_shops']:
                print(f"  - {shop['id']}: {shop['name']} (RISQUE: {shop['risk_level']})")
        
        # Détail des shops à risque critique
        if critical_risk_count > 0:
            print(f"\n❌ SHOPS À RISQUE CRITIQUE ({critical_risk_count}):")
            print("   🚫 INTERDIRE AU CLIENT - Données non fiables")
            for shop in self.results['critical_risk_shops']:
                print(f"  - {shop['id']}: {shop['name']} (RISQUE: {shop['risk_level']})")
        
        return {
            'total_shops': total_shops,
            'client_ready_count': client_ready_count,
            'high_risk_count': high_risk_count,
            'critical_risk_count': critical_risk_count,
            'client_ready_percentage': (client_ready_count/total_shops*100) if total_shops > 0 else 0
        }
    
    def export_client_report(self, output_file: str = None):
        """Export du rapport client en Markdown"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"client_validation_report_{timestamp}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 🛡️ Rapport de Validation Client - ZÉRO RISQUE\n\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Objectif:** Protection totale de la réputation client\n\n")
                
                # Statistiques
                stats = self.results['validation_summary']
                total_shops = stats.get('total_shops', 0)
                f.write("## 📈 Résultats Globaux\n\n")
                f.write(f"- **Total shops:** {total_shops}\n")
                if total_shops > 0:
                    f.write(f"- **Prêtes pour client:** {stats.get('client_ready_count', 0)} ({(stats.get('client_ready_count', 0)/total_shops*100):.1f}%)\n")
                    f.write(f"- **Risque élevé:** {stats.get('high_risk_count', 0)} ({(stats.get('high_risk_count', 0)/total_shops*100):.1f}%)\n")
                    f.write(f"- **Risque critique:** {stats.get('critical_risk_count', 0)} ({(stats.get('critical_risk_count', 0)/total_shops*100):.1f}%)\n\n")
                else:
                    f.write(f"- **Prêtes pour client:** {stats.get('client_ready_count', 0)} (0.0%)\n")
                    f.write(f"- **Risque élevé:** {stats.get('high_risk_count', 0)} (0.0%)\n")
                    f.write(f"- **Risque critique:** {stats.get('critical_risk_count', 0)} (0.0%)\n\n")
                
                # Recommandations
                if stats.get('client_ready_count', 0) > 0:
                    f.write("## 🎯 Recommandation Client\n\n")
                    f.write("✅ **Vous pouvez envoyer les shops prêtes au client**\n")
                    f.write("🛡️ **ZÉRO RISQUE sur la fiabilité des données**\n")
                    f.write("🏆 **Protection totale de votre réputation client**\n\n")
                else:
                    f.write("## 🚨 Alerte Client Critique\n\n")
                    f.write("❌ **AUCUNE shop prête pour le client**\n")
                    f.write("🚫 **RISQUE ÉLEVÉ de perte de confiance client**\n")
                    f.write("🔧 **Action requise: Corriger les données avant envoi**\n\n")
                
                # Détail des shops prêtes
                if self.results['client_ready_shops']:
                    f.write("## ✅ Shops Prêtes pour Client\n\n")
                    for shop in self.results['client_ready_shops']:
                        f.write(f"- **{shop['id']}:** {shop['name']} (RISQUE: {shop['risk_level']})\n")
                    f.write("\n")
                
                # Détail des shops à risque
                if self.results['high_risk_shops']:
                    f.write("## ⚠️ Shops à Risque Élevé\n\n")
                    for shop in self.results['high_risk_shops']:
                        f.write(f"- **{shop['id']}:** {shop['name']} (RISQUE: {shop['risk_level']})\n")
                    f.write("\n")
                
                if self.results['critical_risk_shops']:
                    f.write("## ❌ Shops à Risque Critique\n\n")
                    for shop in self.results['critical_risk_shops']:
                        f.write(f"- **{shop['id']}:** {shop['name']} (RISQUE: {shop['risk_level']})\n")
                    f.write("\n")
            
            print(f"📄 Rapport client exporté vers: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
    
    def run_validation(self):
        """Exécution complète de la validation client"""
        print("🚀 DÉMARRAGE DE LA VALIDATION CLIENT")
        print("=" * 70)
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 OBJECTIF: ZÉRO RISQUE - Protection totale de la réputation client")
        
        self.connect()
        
        # Validation des critères client
        stats = self.validate_all_shops()
        self.results['validation_summary'] = stats
        
        # Génération du rapport client
        self.generate_client_report()
        
        # Export du rapport
        self.export_client_report()
        
        print(f"\n✅ VALIDATION CLIENT TERMINÉE")
        print("=" * 70)
        
        if self.conn:
            self.conn.close()

def main():
    """Fonction principale"""
    db_path = "/home/ubuntu/projects/shopshopshops/test/trendtrack-scraper-final/data/trendtrack.db"
    
    validator = ClientValidator(db_path)
    validator.run_validation()

if __name__ == "__main__":
    main()
