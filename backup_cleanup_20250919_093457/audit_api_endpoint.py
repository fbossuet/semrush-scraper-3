#!/usr/bin/env python3
"""
T074: Audit du fonctionnement de l'API endpoint test
Script d'audit complet pour valider l'API de test
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import statistics

class APIEndpointAuditor:
    """Auditeur pour l'API endpoint de test"""
    
    def __init__(self, base_url: str = "http://37.59.102.7:8001"):
        self.base_url = base_url
        self.test_endpoint = f"{base_url}/test/shops/with-analytics-ordered"
        self.results = {}
        
    def print_banner(self):
        """Affiche la bannière d'audit"""
        print("=" * 80)
        print("🔍 T074: AUDIT DU FONCTIONNEMENT DE L'API ENDPOINT TEST")
        print("=" * 80)
        print(f"🕒 {datetime.now(timezone.utc).isoformat()}")
        print(f"🎯 URL: {self.test_endpoint}")
        print("=" * 80)
    
    def test_basic_endpoint(self) -> Dict[str, Any]:
        """Test de base de l'endpoint avec paramètres par défaut"""
        print("\n📋 TEST 1: Endpoint de base avec paramètres par défaut")
        print("-" * 60)
        
        params = {"since": "2025-07-10T00:00:00Z"}
        start_time = time.time()
        
        try:
            response = requests.get(self.test_endpoint, params=params, timeout=30)
            response_time = time.time() - start_time
            
            result = {
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(response.content) if response.content else 0
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result.update({
                        "data_structure_valid": True,
                        "shop_count": len(data.get("data", [])),
                        "environment": data.get("environment", ""),
                        "database": data.get("database", ""),
                        "filter_applied": data.get("filter_applied", {}),
                        "count": data.get("count", 0)
                    })
                    
                    print(f"✅ Statut: {response.status_code}")
                    print(f"⏱️ Temps de réponse: {response_time:.3f}s")
                    print(f"📊 Nombre de boutiques: {result['shop_count']}")
                    print(f"🌍 Environnement: {result['environment']}")
                    print(f"🗄️ Base de données: {result['database']}")
                    print(f"🔍 Filtre appliqué: {result['filter_applied']}")
                    
                except json.JSONDecodeError as e:
                    result["data_structure_valid"] = False
                    result["json_error"] = str(e)
                    print(f"❌ Erreur JSON: {e}")
            else:
                result["error_message"] = response.text
                print(f"❌ Erreur HTTP: {response.status_code}")
                print(f"📝 Message: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            result = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            print(f"❌ Erreur de requête: {e}")
        
        return result
    
    def validate_shop_metrics(self, shops_data: List[Dict]) -> Dict[str, Any]:
        """Valide la cohérence des métriques des boutiques"""
        print("\n📊 TEST 2: Validation des métriques des boutiques")
        print("-" * 60)
        
        if not shops_data:
            return {"error": "Aucune donnée de boutique disponible"}
        
        metrics_analysis = {
            "total_shops": len(shops_data),
            "metrics_coverage": {},
            "data_quality": {},
            "anomalies": []
        }
        
        # Métriques attendues
        expected_metrics = [
            "monthly_visits", "year_founded", "total_products", "aov",
            "pixel_google", "pixel_facebook", "organic_traffic", "bounce_rate",
            "avg_visit_duration", "visits", "traffic", "branded_traffic",
            "percent_branded_traffic", "paid_search_traffic", "cpc",
            "conversion_rate", "market_us", "market_uk", "market_de",
            "market_ca", "market_au", "market_fr"
        ]
        
        # Analyser la couverture des métriques
        for metric in expected_metrics:
            non_null_count = sum(1 for shop in shops_data if shop.get(metric) is not None)
            coverage_percentage = (non_null_count / len(shops_data)) * 100
            metrics_analysis["metrics_coverage"][metric] = {
                "count": non_null_count,
                "percentage": coverage_percentage,
                "null_count": len(shops_data) - non_null_count
            }
        
        # Analyser la qualité des données
        for metric in ["monthly_visits", "organic_traffic", "visits", "traffic"]:
            values = [shop.get(metric) for shop in shops_data if shop.get(metric) is not None]
            if values:
                metrics_analysis["data_quality"][metric] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "count": len(values)
                }
        
        # Détecter les anomalies
        for i, shop in enumerate(shops_data[:10]):  # Analyser les 10 premières
            shop_id = shop.get("id", i)
            shop_name = shop.get("shop_name", "Unknown")
            
            # Vérifier les valeurs négatives
            for metric in ["monthly_visits", "organic_traffic", "visits", "traffic"]:
                value = shop.get(metric)
                if value is not None and value < 0:
                    metrics_analysis["anomalies"].append({
                        "shop_id": shop_id,
                        "shop_name": shop_name,
                        "metric": metric,
                        "value": value,
                        "issue": "Valeur négative"
                    })
            
            # Vérifier les pourcentages > 100%
            for metric in ["percent_branded_traffic", "bounce_rate"]:
                value = shop.get(metric)
                if value is not None and value > 1.0:
                    metrics_analysis["anomalies"].append({
                        "shop_id": shop_id,
                        "shop_name": shop_name,
                        "metric": metric,
                        "value": value,
                        "issue": "Pourcentage > 100%"
                    })
        
        # Afficher les résultats
        print(f"📈 Total boutiques analysées: {metrics_analysis['total_shops']}")
        print(f"🔍 Anomalies détectées: {len(metrics_analysis['anomalies'])}")
        
        # Afficher la couverture des métriques principales
        main_metrics = ["monthly_visits", "organic_traffic", "visits", "bounce_rate", "conversion_rate"]
        print("\n📊 Couverture des métriques principales:")
        for metric in main_metrics:
            coverage = metrics_analysis["metrics_coverage"].get(metric, {})
            print(f"  {metric}: {coverage.get('percentage', 0):.1f}% ({coverage.get('count', 0)}/{len(shops_data)})")
        
        # Afficher les anomalies
        if metrics_analysis["anomalies"]:
            print("\n⚠️ Anomalies détectées:")
            for anomaly in metrics_analysis["anomalies"][:5]:  # Afficher les 5 premières
                print(f"  Shop {anomaly['shop_id']} ({anomaly['shop_name']}): {anomaly['metric']} = {anomaly['value']} ({anomaly['issue']})")
        
        return metrics_analysis
    
    def test_performance(self, num_requests: int = 5) -> Dict[str, Any]:
        """Test de performance avec plusieurs requêtes"""
        print(f"\n⚡ TEST 3: Test de performance ({num_requests} requêtes)")
        print("-" * 60)
        
        response_times = []
        success_count = 0
        errors = []
        
        params = {"since": "2025-07-10T00:00:00Z"}
        
        for i in range(num_requests):
            start_time = time.time()
            try:
                response = requests.get(self.test_endpoint, params=params, timeout=30)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"  Requête {i+1}: ✅ {response_time:.3f}s")
                else:
                    errors.append(f"Requête {i+1}: HTTP {response.status_code}")
                    print(f"  Requête {i+1}: ❌ HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                errors.append(f"Requête {i+1}: {str(e)}")
                print(f"  Requête {i+1}: ❌ {str(e)}")
        
        # Calculer les statistiques
        if response_times:
            performance_stats = {
                "total_requests": num_requests,
                "successful_requests": success_count,
                "success_rate": (success_count / num_requests) * 100,
                "response_times": {
                    "min": min(response_times),
                    "max": max(response_times),
                    "mean": statistics.mean(response_times),
                    "median": statistics.median(response_times)
                },
                "errors": errors
            }
            
            print(f"\n📊 Statistiques de performance:")
            print(f"  Taux de succès: {performance_stats['success_rate']:.1f}%")
            print(f"  Temps min: {performance_stats['response_times']['min']:.3f}s")
            print(f"  Temps max: {performance_stats['response_times']['max']:.3f}s")
            print(f"  Temps moyen: {performance_stats['response_times']['mean']:.3f}s")
            print(f"  Temps médian: {performance_stats['response_times']['median']:.3f}s")
            
            return performance_stats
        else:
            return {"error": "Aucune requête réussie"}
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """Test des cas limites"""
        print("\n🧪 TEST 4: Test des cas limites")
        print("-" * 60)
        
        edge_cases = [
            {"name": "Date invalide", "params": {"since": "invalid-date"}},
            {"name": "Date future", "params": {"since": "2030-01-01T00:00:00Z"}},
            {"name": "Date très ancienne", "params": {"since": "1900-01-01T00:00:00Z"}},
            {"name": "Paramètre manquant", "params": {}},
            {"name": "Paramètre vide", "params": {"since": ""}},
        ]
        
        results = {}
        
        for case in edge_cases:
            print(f"  Test: {case['name']}")
            try:
                response = requests.get(self.test_endpoint, params=case["params"], timeout=10)
                results[case["name"]] = {
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 400, 422],  # Codes acceptables
                    "response_preview": response.text[:100] if response.text else ""
                }
                
                if response.status_code == 200:
                    print(f"    ✅ {response.status_code} - Réponse valide")
                elif response.status_code in [400, 422]:
                    print(f"    ✅ {response.status_code} - Erreur attendue")
                else:
                    print(f"    ❌ {response.status_code} - Code inattendu")
                    
            except requests.exceptions.RequestException as e:
                results[case["name"]] = {
                    "error": str(e),
                    "success": False
                }
                print(f"    ❌ Erreur: {str(e)}")
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport d'audit complet"""
        print("\n📋 GÉNÉRATION DU RAPPORT D'AUDIT")
        print("=" * 80)
        
        # Exécuter tous les tests
        basic_test = self.test_basic_endpoint()
        
        # Si le test de base réussit, continuer avec les autres tests
        if basic_test.get("success") and basic_test.get("data_structure_valid"):
            # Récupérer les données pour l'analyse des métriques
            try:
                response = requests.get(self.test_endpoint, params={"since": "2025-07-10T00:00:00Z"}, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    shops_data = data.get("data", [])
                    metrics_analysis = self.validate_shop_metrics(shops_data)
                else:
                    metrics_analysis = {"error": "Impossible de récupérer les données"}
            except Exception as e:
                metrics_analysis = {"error": str(e)}
        else:
            metrics_analysis = {"error": "Test de base échoué"}
        
        performance_test = self.test_performance()
        edge_cases_test = self.test_edge_cases()
        
        # Compiler le rapport final
        report = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint_url": self.test_endpoint,
            "basic_test": basic_test,
            "metrics_analysis": metrics_analysis,
            "performance_test": performance_test,
            "edge_cases_test": edge_cases_test,
            "overall_status": "PASS" if basic_test.get("success") else "FAIL"
        }
        
        # Afficher le résumé
        print(f"\n🎯 RÉSUMÉ DE L'AUDIT:")
        print(f"  Statut global: {'✅ PASS' if report['overall_status'] == 'PASS' else '❌ FAIL'}")
        print(f"  Endpoint accessible: {'✅ Oui' if basic_test.get('success') else '❌ Non'}")
        print(f"  Structure JSON valide: {'✅ Oui' if basic_test.get('data_structure_valid') else '❌ Non'}")
        print(f"  Nombre de boutiques: {basic_test.get('shop_count', 'N/A')}")
        print(f"  Environnement: {basic_test.get('environment', 'N/A')}")
        print(f"  Base de données: {basic_test.get('database', 'N/A')}")
        
        if "response_times" in performance_test:
            print(f"  Temps de réponse moyen: {performance_test['response_times']['mean']:.3f}s")
            print(f"  Taux de succès: {performance_test['success_rate']:.1f}%")
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Sauvegarde le rapport d'audit"""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"api_audit_report_{timestamp}.json"
        
        filepath = f"/home/ubuntu/projects/shopshopshops/test/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Rapport sauvegardé: {filepath}")
        except Exception as e:
            print(f"\n❌ Erreur sauvegarde: {e}")

def main():
    """Fonction principale"""
    auditor = APIEndpointAuditor()
    auditor.print_banner()
    
    try:
        report = auditor.generate_report()
        auditor.save_report(report)
        
        print("\n🎉 AUDIT TERMINÉ AVEC SUCCÈS!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE L'AUDIT: {e}")
        print("=" * 80)

if __name__ == "__main__":
    main()
