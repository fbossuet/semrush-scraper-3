#!/usr/bin/env python3
"""
Lanceur de workers parallèles par statut
Permet de lancer les workers sur les boutiques avec un statut spécifique
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Configuration du logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure le logging"""
    logger = logging.getLogger()
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Handler fichier
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / f"workers_by_status_{datetime.now(timezone.utc).isoformat()}.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # Désactiver les logs de playwright
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class WorkersByStatusLauncher:
    """Lanceur de workers par statut"""
    
    def __init__(self, status: str, num_workers: int = 2, max_shops_per_worker: int = None):
        self.status = status
        self.num_workers = num_workers
        self.max_shops_per_worker = max_shops_per_worker
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "num_workers": num_workers,
            "results": {}
        }
        
        # Nettoyage préventif avant le lancement
        self.cleanup_before_launch()
    
    def cleanup_before_launch(self):
        """Nettoyage préventif pour éviter les problèmes de session"""
        logger.info("🧹 NETTOYAGE PRÉVENTIF - Début")
        
        try:
            # 1. Vérifier la connectivité
            self.check_connectivity()
            
            # 2. Nettoyer les sessions partagées
            self.cleanup_shared_sessions()
            
            # 3. Tuer les processus chromium orphelins
            self.kill_orphaned_chromium()
            
            logger.info("✅ NETTOYAGE PRÉVENTIF - Terminé avec succès")
            
        except Exception as e:
            logger.error(f"❌ NETTOYAGE PRÉVENTIF - Erreur: {e}")
            logger.warning("⚠️ Continuation malgré l'erreur de nettoyage")
    
    def check_connectivity(self):
        """Vérifie la connectivité vers les services critiques"""
        logger.info("🔍 Vérification de la connectivité...")
        
        critical_urls = [
            "sam.mytoolsplan.xyz",
            "app.mytoolsplan.com"
        ]
        
        for url in critical_urls:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "5", url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"✅ Connectivité OK: {url}")
                else:
                    logger.warning(f"⚠️ Connectivité faible: {url}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de vérifier {url}: {e}")
    
    def cleanup_shared_sessions(self):
        """Nettoie les sessions partagées corrompues"""
        logger.info("🧹 Nettoyage des sessions partagées...")
        
        # Nettoyer la session locale
        shared_session_path = Path("session-profile-shared")
        if shared_session_path.exists():
            try:
                shutil.rmtree(shared_session_path)
                logger.info("✅ Session partagée locale supprimée")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer la session partagée locale: {e}")
        else:
            logger.info("ℹ️ Aucune session partagée locale à nettoyer")
        
        # Nettoyer les sessions Playwright dans le cache
        playwright_cache_path = Path.home() / ".cache" / "ms-playwright" / "session-profile-shared"
        if playwright_cache_path.exists():
            try:
                shutil.rmtree(playwright_cache_path)
                logger.info("✅ Session Playwright dans le cache supprimée")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer la session Playwright: {e}")
        else:
            logger.info("ℹ️ Aucune session Playwright dans le cache à nettoyer")
    
    def kill_orphaned_chromium(self):
        """Tue les processus chromium orphelins"""
        logger.info("🔫 Nettoyage des processus chromium orphelins...")
        
        try:
            # Tuer les processus chromium (plus agressif)
            processes_to_kill = [
                "chromium",
                "chrome",
                "playwright"
            ]
            
            killed_count = 0
            for process in processes_to_kill:
                result = subprocess.run(
                    ["pkill", "-f", process],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    killed_count += 1
                    logger.info(f"✅ Processus {process} supprimés")
            
            if killed_count > 0:
                logger.info(f"✅ {killed_count} types de processus orphelins supprimés")
                # Attendre un peu pour que les processus se terminent
                import time
                time.sleep(2)
            else:
                logger.info("ℹ️ Aucun processus orphelin trouvé")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du nettoyage des processus: {e}")
    
    def get_shops_by_status(self) -> List[Dict]:
        """Récupère les boutiques selon le statut spécifié"""
        try:
            from trendtrack_api_vps_adapted import api
            
            all_shops = api.get_all_shops()
            
            if self.status == "empty":
                # Boutiques sans statut ou avec statut vide
                target_shops = [shop for shop in all_shops if not shop.get('scraping_status') or shop.get('scraping_status') == '']
            elif self.status == "partial":
                # Boutiques avec statut partial
                target_shops = [shop for shop in all_shops if shop.get('scraping_status') == 'partial']
            elif self.status == "failed":
                # Boutiques avec statut failed
                target_shops = [shop for shop in all_shops if shop.get('scraping_status') == 'failed']
            elif self.status == "pending":
                # Boutiques avec statut pending
                target_shops = [shop for shop in all_shops if shop.get("scraping_status") == "pending"]
            elif self.status == "all":
                # Toutes les boutiques éligibles
                target_shops = [shop for shop in all_shops if api.is_shop_eligible_for_scraping(shop)]
            else:
                logger.error(f"❌ Statut invalide: {self.status}")
                return []
            
            logger.info(f"📊 Total boutiques: {len(all_shops)}")
            logger.info(f"🎯 Boutiques avec statut '{self.status}': {len(target_shops)}")
            
            # Limiter le nombre si spécifié
            if self.max_shops_per_worker and self.max_shops_per_worker > 0:
                max_total = self.max_shops_per_worker * self.num_workers
                target_shops = target_shops[:max_total]
                logger.info(f"🔢 Limité à {max_total} boutiques ({self.max_shops_per_worker} par worker)")
            
            return target_shops
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération boutiques: {e}")
            return []
    
    def distribute_shops(self, shops: List[Dict]) -> Dict[int, List[Dict]]:
        """Répartit les boutiques entre les workers"""
        try:
            # Répartition équitable
            worker_shops = {}
            for i in range(self.num_workers):
                worker_shops[i] = shops[i::self.num_workers]
                logger.info(f"👷 Worker {i}: {len(worker_shops[i])} boutiques")
            
            # Sauvegarder la distribution
            distribution = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": self.status,
                "num_workers": self.num_workers,
                "total_shops": len(shops),
                "distribution": {
                    str(worker_id): [
                        {"id": shop["id"], "name": shop.get("shop_name", "N/A"), "url": shop.get("shop_url", "N/A")}
                        for shop in worker_shops[worker_id]
                    ]
                    for worker_id in range(self.num_workers)
                }
            }
            
            filename = f"distribution_{self.status}_{datetime.now(timezone.utc).isoformat()}.json"
            with open(filename, "w") as f:
                json.dump(distribution, f, indent=2)
            
            logger.info(f"💾 Distribution sauvegardée: {filename}")
            return worker_shops
            
        except Exception as e:
            logger.error(f"❌ Erreur distribution: {e}")
            return {}
    
    async def run_worker(self, worker_id: int, shops: List[Dict]) -> Dict:
        """Lance un worker avec sa liste de boutiques"""
        try:
            logger.info(f"🚀 Lancement Worker {worker_id} avec {len(shops)} boutiques...")
            
            # Importer le scraper parallélisé
            from production_scraper_parallel import ParallelProductionScraper
            
            # Créer le worker
            worker = ParallelProductionScraper(worker_id)
            
            # Lancer le worker
            success = await worker.run_worker(shops, "2025-07-01,2025-07-31")
            
            results = {
                "worker_id": worker_id,
                "shops_count": len(shops),
                "success": success,
                "shops": [
                    {
                        "id": shop["id"],
                        "name": shop.get("shop_name", "N/A"),
                        "url": shop.get("shop_url", "N/A")
                    }
                    for shop in shops
                ]
            }
            
            if success:
                logger.info(f"✅ Worker {worker_id} terminé avec succès")
            else:
                logger.error(f"❌ Worker {worker_id} échoué")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur worker {worker_id}: {e}")
            return {
                "worker_id": worker_id,
                "shops_count": len(shops),
                "success": False,
                "error": str(e)
            }
    
    async def launch_workers(self) -> bool:
        """Lance les workers parallèles"""
        try:
            logger.info(f"🚀 LANCEMENT WORKERS PARALLÈLES - STATUT: {self.status.upper()}")
            logger.info("=" * 70)
            
            # Récupérer les boutiques selon le statut
            shops = self.get_shops_by_status()
            if not shops:
                logger.error(f"❌ Aucune boutique trouvée avec le statut '{self.status}'")
                return False
            
            # Répartir les boutiques
            worker_shops = self.distribute_shops(shops)
            if not worker_shops:
                logger.error("❌ Erreur distribution des boutiques")
                return False
            
            # Lancer les workers avec délai d'attente pour éviter les conflits de session partagée
            tasks = []
            for i, (worker_id, worker_shops_list) in enumerate(worker_shops.items()):
                if worker_shops_list:  # Seulement si le worker a des boutiques
                    # Délai d'attente progressif pour éviter les conflits de session partagée
                    delay = i * 10  # 0s, 10s, 20s, etc.
                    if delay > 0:
                        logger.info(f"⏳ Délai d'attente de {delay}s avant le lancement du Worker {worker_id}...")
                        await asyncio.sleep(delay)
                    
                    task = asyncio.create_task(self.run_worker(worker_id, worker_shops_list))
                    tasks.append(task)
            
            if not tasks:
                logger.error("❌ Aucun worker à lancer")
                return False
            
            logger.info(f"🏭 Lancement de {len(tasks)} workers en parallèle...")
            
            # Attendre que tous les workers terminent
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyser les résultats
            total_successes = 0
            total_errors = 0
            total_shops = 0
            total_metrics_found = 0
            total_metrics_not_found = 0
            
            for result in results:
                if isinstance(result, dict):
                    if result.get("success", False):
                        total_successes += 1
                    else:
                        total_errors += 1
                    total_shops += result.get("shops_count", 0)
                    total_metrics_found += result.get("metrics_found", 0)
                    total_metrics_not_found += result.get("metrics_not_found", 0)
                    self.results["results"][f"worker_{result.get('worker_id', 'unknown')}"] = result
                else:
                    logger.error(f"❌ Erreur worker: {result}")
                    total_errors += 1
            
            # Résultats finaux
            logger.info("\n" + "=" * 70)
            logger.info("📊 RÉSULTATS WORKERS PARALLÈLES")
            logger.info("=" * 70)
            logger.info(f"🎯 Statut traité: {self.status}")
            logger.info(f"👷 Workers lancés: {len(tasks)}")
            logger.info(f"🏪 Boutiques traitées: {total_shops}")
            logger.info(f"✅ Workers réussis: {total_successes}")
            logger.info(f"❌ Workers échoués: {total_errors}")
            logger.info(f"📈 Taux de succès: {(total_successes/max(len(tasks), 1)*100):.1f}%")
            
            # Métriques de récupération
            total_metrics = total_metrics_found + total_metrics_not_found
            if total_metrics > 0:
                metrics_success_rate = (total_metrics_found / total_metrics) * 100
                logger.info(f"📊 Métriques récupérées: {total_metrics_found}/{total_metrics} ({metrics_success_rate:.1f}%)")
            else:
                logger.info("📊 Métriques récupérées: 0/0 (N/A)")
            
            if total_errors == 0:
                logger.info("🎉 TOUS LES WORKERS ONT RÉUSSI!")
                self.results["overall_success"] = True
            else:
                logger.warning("⚠️ CERTAINS WORKERS ONT ÉCHOUÉ")
                self.results["overall_success"] = False
            
            # Sauvegarder les résultats
            filename = f"results_{self.status}_{datetime.now(timezone.utc).isoformat()}.json"
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"📄 Résultats sauvegardés: {filename}")
            
            return self.results["overall_success"]
            
        except Exception as e:
            logger.error(f"❌ Erreur lancement workers: {e}")
            return False

def show_help():
    """Affiche l'aide"""
    print("🏭 LANCEUR WORKERS PARALLÈLES PAR STATUT")
    print("=" * 50)
    print("💡 Usage:")
    print("  python3 launch_workers_by_status.py <statut> [options]")
    print()
    print("🎯 Statuts disponibles:")
    print("  empty   - Boutiques sans statut ou statut vide")
    print("  partial - Boutiques avec statut 'partial'")
    print("  failed  - Boutiques avec statut 'failed'")
    print("  all     - Toutes les boutiques éligibles")
    print()
    print("⚙️ Options:")
    print("  --workers N        - Nombre de workers (défaut: 2)")
    print("  --max-per-worker N - Max boutiques par worker (défaut: illimité)")
    print()
    print("📝 Exemples:")
    print("  python3 launch_workers_by_status.py partial")
    print("  python3 launch_workers_by_status.py empty --workers 3")
    print("  python3 launch_workers_by_status.py partial --max-per-worker 10")
    print("  python3 launch_workers_by_status.py all --workers 2 --max-per-worker 5")
    print("=" * 50)

async def main():
    """Fonction principale"""
    setup_logging()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    # Parser les arguments
    status = sys.argv[1].lower()
    num_workers = 2
    max_shops_per_worker = None
    
    # Parser les options
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--workers" and i + 1 < len(sys.argv):
            try:
                num_workers = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                logger.error(f"❌ Nombre de workers invalide: {sys.argv[i + 1]}")
                return
        elif sys.argv[i] == "--max-per-worker" and i + 1 < len(sys.argv):
            try:
                max_shops_per_worker = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                logger.error(f"❌ Max boutiques par worker invalide: {sys.argv[i + 1]}")
                return
        else:
            logger.error(f"❌ Option inconnue: {sys.argv[i]}")
            return
    
    # Valider le statut
    valid_statuses = ["empty", "partial", "failed", "pending", "all"]
    if status not in valid_statuses:
        logger.error(f"❌ Statut invalide: {status}")
        logger.error(f"💡 Statuts valides: {', '.join(valid_statuses)}")
        return
    
    # Afficher la configuration
    logger.info(f"🎯 Statut cible: {status}")
    logger.info(f"👷 Nombre de workers: {num_workers}")
    if max_shops_per_worker:
        logger.info(f"🔢 Max boutiques par worker: {max_shops_per_worker}")
    else:
        logger.info("🔢 Max boutiques par worker: illimité")
    
    # Créer le lanceur
    launcher = WorkersByStatusLauncher(status, num_workers, max_shops_per_worker)
    
    # Lancer les workers
    success = await launcher.launch_workers()
    
    # Code de sortie
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())


