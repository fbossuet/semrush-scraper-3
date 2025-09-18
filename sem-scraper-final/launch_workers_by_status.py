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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Configuration du logging
logger = logging.getLogger(__name__)

def get_available_screen_name(base_name: str) -> str:
    """
    Trouve un nom de screen disponible en ajoutant un suffixe numérique si nécessaire
    """
    session_name = base_name
    counter = 1
    
    while True:
        try:
            # Vérifier si le screen existe
            result = subprocess.run(
                ["screen", "-list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if session_name not in result.stdout:
                return session_name
            
            # Le screen existe, essayer avec un suffixe
            session_name = f"{base_name}-{counter}"
            counter += 1
            
            # Sécurité pour éviter une boucle infinie
            if counter > 100:
                logger.warning(f"⚠️ Impossible de trouver un nom de screen libre pour {base_name}")
                return f"{base_name}-{datetime.now(timezone.utc).isoformat()}"
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout lors de la vérification des screens")
            return f"{base_name}-{datetime.now(timezone.utc).isoformat()}"
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la vérification des screens: {e}")
            return f"{base_name}-{datetime.now(timezone.utc).isoformat()}"

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
                "metrics_found": getattr(worker, 'metrics_found', 0),
                "metrics_not_found": getattr(worker, 'metrics_not_found', 0),
                "metrics_count": getattr(worker, 'metrics_count', {}),
                "statuses": getattr(worker, 'status_count', {}),
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
            # Enregistrement du temps de début pour le calcul des performances
            start_time = time.time()
            
            logger.info(f"🚀 LANCEMENT WORKERS PARALLÈLES - STATUT: {self.status.upper()}")
            logger.info("=" * 70)
            
            # Initialiser le bootstrap global (Xvfb + navigateur)
            logger.info("🚀 Initialisation bootstrap global...")
            from global_bootstrap import global_bootstrap
            if not await global_bootstrap.initialize():
                logger.error("❌ Échec initialisation bootstrap global")
                return False
            
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
            
            # Lancer les workers avec micro-jitter quasi simultané (éviter conflits session partagée)
            tasks = []
            for i, (worker_id, worker_shops_list) in enumerate(worker_shops.items()):
                if worker_shops_list:  # Seulement si le worker a des boutiques
                    # Micro-échelonnage configurable (parallel_config)
                    try:
                        from parallel_config import ParallelConfig
                        base = getattr(ParallelConfig, 'STAGGER_BASE_S', 0.0)
                        step = getattr(ParallelConfig, 'STAGGER_STEP_S', 0.2)
                        jitter = getattr(ParallelConfig, 'STAGGER_JITTER_S', 0.1)
                        max_s = getattr(ParallelConfig, 'STAGGER_MAX_S', 1.0)
                    except Exception:
                        base, step, jitter, max_s = 0.0, 0.2, 0.1, 1.0

                    import random
                    delay = min(base + i * step + random.uniform(-jitter, jitter), max_s)
                    if delay > 0:
                        logger.info(f"⏳ Délai d'attente de {delay:.2f}s avant le lancement du Worker {worker_id}...")
                        await asyncio.sleep(max(delay, 0))
                    
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
            # Agrégation des métriques détaillées
            detailed_metrics = {
                'organic_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
                'paid_search_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
                'visits': {'found': 0, 'not_found': 0, 'skipped': 0},
                'bounce_rate': {'found': 0, 'not_found': 0, 'skipped': 0},
                'average_visit_duration': {'found': 0, 'not_found': 0, 'skipped': 0},  # Utiliser le nom du worker
                'branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0},
                'conversion_rate': {'found': 0, 'not_found': 0, 'skipped': 0},
                'percent_branded_traffic': {'found': 0, 'not_found': 0, 'skipped': 0}
            }
            # Comptage des statuts attribués
            status_count = {
                'completed': 0,
                'partial': 0,
                'na': 0,
                'failed': 0
            }
            
            for result in results:
                if isinstance(result, dict):
                    if result.get("success", False):
                        total_successes += 1
                    else:
                        total_errors += 1
                    total_shops += result.get("shops_count", 0)
                    total_metrics_found += result.get("metrics_found", 0)
                    total_metrics_not_found += result.get("metrics_not_found", 0)
                    
                    # Agrégation des métriques détaillées
                    worker_metrics = result.get("metrics_count", {})
                    for metric_name, counts in worker_metrics.items():
                        if metric_name in detailed_metrics:
                            detailed_metrics[metric_name]['found'] += counts.get('found', 0)
                            detailed_metrics[metric_name]['not_found'] += counts.get('not_found', 0)
                            detailed_metrics[metric_name]['skipped'] += counts.get('skipped', 0)
                    
                    # Comptage des statuts
                    worker_statuses = result.get("statuses", {})
                    for status, count in worker_statuses.items():
                        if status in status_count:
                            status_count[status] += count
                    
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
            
            # Métriques de récupération (en excluant les skippées)
            total_metrics_found_detailed = sum(counts.get('found', 0) for counts in detailed_metrics.values())
            total_metrics_not_found_detailed = sum(counts.get('not_found', 0) for counts in detailed_metrics.values())
            total_metrics_attempts = total_metrics_found_detailed + total_metrics_not_found_detailed
            
            if total_metrics_attempts > 0:
                metrics_success_rate = (total_metrics_found_detailed / total_metrics_attempts) * 100
                logger.info(f"📊 Métriques récupérées: {total_metrics_found_detailed}/{total_metrics_attempts} ({metrics_success_rate:.1f}%)")
            else:
                logger.info("📊 Métriques récupérées: 0/0 (N/A)")
            
            # Bilan des performances
            if total_shops > 0:
                # Calcul de la durée totale d'exécution
                end_time = time.time()
                total_duration_seconds = end_time - start_time
                total_duration_hours = total_duration_seconds / 3600
                
                # Calcul des domaines/heure
                if total_duration_hours > 0:
                    domains_per_hour = total_shops / total_duration_hours
                else:
                    domains_per_hour = total_shops  # Si très rapide, on assume au moins 1 heure
                
                # Formatage de la durée
                if total_duration_seconds < 60:
                    duration_str = f"{total_duration_seconds:.1f}s"
                elif total_duration_seconds < 3600:
                    duration_str = f"{total_duration_seconds/60:.1f}min"
                else:
                    duration_str = f"{total_duration_hours:.1f}h"
                
                logger.info("🚀 BILAN DES PERFORMANCES:")
                logger.info(f"   ⏱️ Durée totale: {duration_str}")
                logger.info(f"   🏪 Boutiques traitées: {total_shops}")
                logger.info(f"   📈 Vitesse moyenne: {domains_per_hour:.1f} domaines/heure")
            
            # Détail par métrique
            logger.info("📈 DÉTAIL PAR MÉTRIQUE:")
            # Mapping pour l'affichage des noms de métriques
            display_names = {
                'average_visit_duration': 'avg_visit_duration',
                'organic_traffic': 'organic_traffic',
                'paid_search_traffic': 'paid_search_traffic',
                'visits': 'visits',
                'bounce_rate': 'bounce_rate',
                'branded_traffic': 'branded_traffic',
                'conversion_rate': 'conversion_rate',
                'percent_branded_traffic': 'percent_branded_traffic'
            }
            
            # Mapping inverse pour récupérer les données avec le bon nom
            data_names = {
                'avg_visit_duration': 'average_visit_duration',  # Les données sont stockées avec 'average_visit_duration'
                'organic_traffic': 'organic_traffic',
                'paid_search_traffic': 'paid_search_traffic',
                'visits': 'visits',
                'bounce_rate': 'bounce_rate',
                'branded_traffic': 'branded_traffic',
                'conversion_rate': 'conversion_rate',
                'percent_branded_traffic': 'percent_branded_traffic'
            }
            
            for metric_name, counts in detailed_metrics.items():
                # Utiliser le mapping inverse pour récupérer les bonnes données
                data_key = data_names.get(metric_name, metric_name)
                actual_counts = detailed_metrics.get(data_key, counts)
                
                found_count = actual_counts.get('found', 0)
                not_found_count = actual_counts.get('not_found', 0)
                skipped_count = actual_counts.get('skipped', 0)
                total_attempts = found_count + not_found_count + skipped_count
                display_name = display_names.get(metric_name, metric_name)
                
                
                if total_attempts > 0:
                    # Calcul du taux de succès uniquement sur les métriques réellement tentées (excluant les skippées)
                    attempted_count = total_attempts - skipped_count
                    if attempted_count > 0:
                        success_rate = (found_count / attempted_count) * 100
                    else:
                        success_rate = 0.0
                    logger.info(f"   🔹 {display_name}:")
                    logger.info(f"      📊 Total: {total_attempts} | Skipées: {skipped_count} | Succès: {found_count} | Échecs: {not_found_count} | Taux: {success_rate:.1f}%")
                else:
                    logger.info(f"   🔹 {display_name}: Aucune tentative")
            
            # Détail par statut
            logger.info("📊 STATUTS ATTRIBUÉS:")
            total_statuses = sum(status_count.values())
            for status, count in status_count.items():
                if total_statuses > 0:
                    percentage = (count / total_statuses) * 100
                    status_emoji = {
                        'completed': '✅',
                        'partial': '⚠️',
                        'na': 'ℹ️',
                        'failed': '❌'
                    }.get(status, '🔹')
                    logger.info(f"   {status_emoji} {status}: {count} ({percentage:.1f}%)")
                else:
                    logger.info(f"   🔹 {status}: 0 (0.0%)")
            
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
            
            # Nettoyer le bootstrap global
            logger.info("🧹 Nettoyage bootstrap global...")
            from global_bootstrap import global_bootstrap
            await global_bootstrap.cleanup()
            
            return self.results["overall_success"]
            
        except Exception as e:
            logger.error(f"❌ Erreur lancement workers: {e}")
            # Nettoyer le bootstrap global en cas d'erreur
            try:
                from global_bootstrap import global_bootstrap
                await global_bootstrap.cleanup()
            except:
                pass
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
    print("  --domain-filter X  - Filtrer par domaine (ex: funnyfuzzy.com)")
    print("  --screen           - Lancer en screen avec nom intelligent")
    print()
    print("📝 Exemples:")
    print("  python3 launch_workers_by_status.py partial")
    print("  python3 launch_workers_by_status.py empty --workers 3")
    print("  python3 launch_workers_by_status.py partial --max-per-worker 10")
    print("  python3 launch_workers_by_status.py all --workers 2 --max-per-worker 5")
    print("  python3 launch_workers_by_status.py partial --screen")
    print("  python3 launch_workers_by_status.py partial --domain-filter funnyfuzzy.com --screen")
    print("=" * 50)

def launch_in_screen(status: str, workers: int = 2, max_per_worker: Optional[int] = None, domain_filter: Optional[str] = None):
    """
    Lance le script en screen avec un nom intelligent
    """
    # Générer un nom de base pour le screen
    base_name = f"workers-{status}"
    if domain_filter:
        base_name += f"-{domain_filter.replace('.', '_')}"
    
    # Trouver un nom de screen disponible
    screen_name = get_available_screen_name(base_name)
    
    # Construire la commande
    cmd_parts = ["python3", "launch_workers_by_status.py", status, "--workers", str(workers)]
    if max_per_worker:
        cmd_parts.extend(["--max-per-worker", str(max_per_worker)])
    if domain_filter:
        cmd_parts.extend(["--domain-filter", domain_filter])
    
    cmd = " ".join(cmd_parts)
    
    # Générer le nom du log
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = f"logs/workers_by_status_{timestamp}.log"
    
    # Commande screen
    screen_cmd = f"""
    echo '🚀 Démarrage workers {status} à $(date)'
    echo '📊 Workers: {workers}'
    echo '📁 Log: {log_file}'
    echo '🖥️ Screen: {screen_name}'
    echo
    {cmd} 2>&1 | tee {log_file}
    echo
    echo '✅ Workers terminés à $(date)'
    echo 'Appuyez sur Entrée pour fermer cette session...'
    read
    """
    
    try:
        # Lancer en screen
        subprocess.run([
            "screen", "-dmS", screen_name, "bash", "-c", screen_cmd
        ], check=True)
        
        print(f"✅ Workers lancés en screen: {screen_name}")
        print(f"📁 Log: {log_file}")
        print(f"🔍 Pour voir la session: screen -r {screen_name}")
        print(f"📊 Pour voir les logs: tail -f {log_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement en screen: {e}")
        return False
    
    return True

async def main():
    """Fonction principale"""
    setup_logging()
    
    # Enregistrement du temps de début pour le calcul des performances
    start_time = time.time()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    # Parser les arguments
    status = sys.argv[1].lower()
    num_workers = 2
    max_shops_per_worker = None
    domain_filter = None
    use_screen = False
    
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
        elif sys.argv[i] == "--domain-filter" and i + 1 < len(sys.argv):
            domain_filter = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--screen":
            use_screen = True
            i += 1
        else:
            logger.error(f"❌ Option inconnue: {sys.argv[i]}")
            return
    
    # Valider le statut
    valid_statuses = ["empty", "partial", "failed", "pending", "all"]
    if status not in valid_statuses:
        logger.error(f"❌ Statut invalide: {status}")
        logger.error(f"💡 Statuts valides: {', '.join(valid_statuses)}")
        return
    
    # Si l'option --screen est activée, lancer en screen
    if use_screen:
        print("🖥️ Lancement en screen...")
        success = launch_in_screen(status, num_workers, max_shops_per_worker, domain_filter)
        if success:
            print("✅ Lancement en screen réussi")
        else:
            print("❌ Échec du lancement en screen")
        return
    
    # Afficher la configuration
    logger.info(f"🎯 Statut cible: {status}")
    logger.info(f"👷 Nombre de workers: {num_workers}")
    if max_shops_per_worker:
        logger.info(f"🔢 Max boutiques par worker: {max_shops_per_worker}")
    else:
        logger.info("🔢 Max boutiques par worker: illimité")
    if domain_filter:
        logger.info(f"🔍 Filtre domaine: {domain_filter}")
    
    # Créer le lanceur
    launcher = WorkersByStatusLauncher(status, num_workers, max_shops_per_worker)
    
    # Lancer les workers
    success = await launcher.launch_workers()
    
    # Code de sortie
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())



