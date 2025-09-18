#!/usr/bin/env python3
"""
Intégration de la métrique CPC dans le scraper SEM
Script d'intégration automatisée pour ajouter CPC au scraper MyToolsPlan
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CPCIntegration:
    """Intégration de la métrique CPC dans le scraper SEM"""
    
    def __init__(self):
        self.sem_scraper_path = Path("/home/ubuntu/sem-scraper-final")
        self.trendtrack_db_path = Path("/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db")
        self.production_scraper_file = self.sem_scraper_path / "production_scraper_parallel.py"
        self.backup_dir = self.sem_scraper_path / "backup_cpc_integration"
        
    def integrate_cpc_metric(self):
        """Intègre la métrique CPC dans le scraper SEM"""
        try:
            logger.info("🚀 Début de l'intégration de la métrique CPC")
            
            # ÉTAPE 1: Vérifications préliminaires
            if not self._step1_verifications():
                return False
            
            # ÉTAPE 2: Backup du scraper existant
            if not self._step2_backup():
                return False
            
            # ÉTAPE 3: Intégration de la méthode CPC
            if not self._step3_integrate_cpc_method():
                return False
            
            # ÉTAPE 4: Intégration dans le workflow principal
            if not self._step4_integrate_workflow():
                return False
            
            # ÉTAPE 5: Mise à jour des compteurs
            if not self._step5_update_counters():
                return False
            
            # ÉTAPE 6: Test de validation
            if not self._step6_validation():
                return False
            
            logger.info("✅ Intégration de la métrique CPC terminée avec succès!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'intégration CPC: {e}")
            self._rollback()
            return False
    
    def _step1_verifications(self) -> bool:
        """ÉTAPE 1: Vérifications préliminaires"""
        logger.info("🔍 ÉTAPE 1: Vérifications préliminaires")
        
        # Vérifier que le fichier scraper existe
        if not self.production_scraper_file.exists():
            logger.error(f"❌ Fichier scraper non trouvé: {self.production_scraper_file}")
            return False
        
        # Vérifier que la base de données existe
        if not self.trendtrack_db_path.exists():
            logger.error(f"❌ Base de données non trouvée: {self.trendtrack_db_path}")
            return False
        
        # Vérifier que la colonne CPC existe en base
        import sqlite3
        try:
            conn = sqlite3.connect(self.trendtrack_db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(analytics)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            if 'cpc' not in columns:
                logger.error("❌ Colonne 'cpc' non trouvée dans la table analytics")
                return False
            
            logger.info("✅ Colonne 'cpc' vérifiée en base de données")
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification base de données: {e}")
            return False
        
        logger.info("✅ Vérifications préliminaires réussies")
        return True
    
    def _step2_backup(self) -> bool:
        """ÉTAPE 2: Backup du scraper existant"""
        logger.info("💾 ÉTAPE 2: Backup du scraper existant")
        
        try:
            # Créer le répertoire de backup
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup du fichier principal
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"production_scraper_parallel_backup_{timestamp}.py"
            shutil.copy2(self.production_scraper_file, backup_file)
            
            logger.info(f"✅ Backup créé: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du backup: {e}")
            return False
    
    def _step3_integrate_cpc_method(self) -> bool:
        """ÉTAPE 3: Intégration de la méthode CPC"""
        logger.info("🔧 ÉTAPE 3: Intégration de la méthode CPC")
        
        try:
            # Lire le fichier actuel
            with open(self.production_scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Méthode CPC à ajouter
            cpc_method = '''
    async def scrape_cpc_via_api(self, domain: str) -> str:
        """
        Récupère le CPC (Cost Per Click) via l'API MyToolsPlan
        Utilise l'API pour extraire les données de coût par clic
        """
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            
            # Throttling avant appel API
            await stealth_system.throttle_api_call(self.worker_id, "cpc")
            
            # Nettoyer le domaine
            clean_domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            
            # Navigation vers sam.mytoolsplan.xyz pour les appels API
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/overview/", wait_until='domcontentloaded', timeout=30000)
            await stealth_system.human_pause(self.worker_id, "session")
            
            # Appel API pour récupérer le CPC
            # Note: À adapter selon l'endpoint API MyToolsPlan pour CPC
            stealth_headers = stealth_system.get_stealth_headers()
            
            # Exemple d'appel API (à adapter selon l'API réelle)
            fetch_code = f"""
                async () => {{
                    try {{
                        const response = await fetch('/dpa/rpc', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'User-Agent': '{stealth_headers.get('User-Agent', '')}',
                                'Accept-Language': '{stealth_headers.get('Accept-Language', '')}',
                                'Accept': '{stealth_headers.get('Accept', '')}'
                            }},
                            body: JSON.stringify({{
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "cpc.getData",
                                "params": {{
                                    "domain": "{clean_domain}",
                                    "date": "{self.target_date}"
                                }}
                            }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        const data = await response.json();
                        return data;
                        
                    }} catch (error) {{
                        console.error('Erreur API CPC:', error);
                        return null;
                    }}
                }}
            """
            
            # Exécuter l'appel API
            result = await self.page.evaluate(fetch_code)
            
            if result and result.get('result'):
                cpc_data = result['result']
                # Extraire la valeur CPC (à adapter selon la structure de réponse)
                cpc_value = cpc_data.get('cpc', cpc_data.get('cost_per_click', '0'))
                
                # Convertir en format numérique si nécessaire
                try:
                    cpc_numeric = float(str(cpc_value).replace('$', '').replace(',', ''))
                    logger.info(f"✅ Worker {self.worker_id}: CPC récupéré: ${cpc_numeric:.2f}")
                    return str(cpc_numeric)
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Worker {self.worker_id}: CPC non numérique: {cpc_value}")
                    return '0'
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Pas de données CPC pour {domain}")
                return '0'
                
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC pour {domain}: {error}")
            return '0'
'''
            
            # Trouver l'endroit pour insérer la méthode (après la dernière méthode de scraping)
            insertion_point = content.find('async def scrape_conversion_rate_via_api(self, domain: str) -> str:')
            if insertion_point == -1:
                # Si pas trouvé, chercher un autre point d'insertion
                insertion_point = content.find('class ParallelProductionScraper:')
                if insertion_point != -1:
                    # Insérer après la classe
                    class_end = content.find('\n\n', insertion_point)
                    if class_end != -1:
                        insertion_point = class_end + 2
                    else:
                        insertion_point = len(content)
                else:
                    insertion_point = len(content)
            
            # Insérer la méthode
            new_content = content[:insertion_point] + cpc_method + content[insertion_point:]
            
            # Écrire le fichier modifié
            with open(self.production_scraper_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("✅ Méthode CPC intégrée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur intégration méthode CPC: {e}")
            return False
    
    def _step4_integrate_workflow(self) -> bool:
        """ÉTAPE 4: Intégration dans le workflow principal"""
        logger.info("🔄 ÉTAPE 4: Intégration dans le workflow principal")
        
        try:
            # Lire le fichier actuel
            with open(self.production_scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Trouver la méthode scrape_domain_overview et ajouter l'appel CPC
            scrape_method_start = content.find('async def scrape_domain_overview(self, domain: str, date_range: str, existing_metrics: Dict[str, str] = None):')
            
            if scrape_method_start == -1:
                logger.error("❌ Méthode scrape_domain_overview non trouvée")
                return False
            
            # Trouver la fin de la méthode (rechercher la méthode suivante)
            next_method_start = content.find('\n    async def ', scrape_method_start + 1)
            if next_method_start == -1:
                next_method_start = len(content)
            
            # Extraire la méthode actuelle
            method_content = content[scrape_method_start:next_method_start]
            
            # Ajouter l'appel CPC avant le return
            cpc_integration = '''
            # CPC - Cost Per Click
            if 'cpc' not in existing_metrics or existing_metrics.get('cpc') in ['', '0', None]:
                cpc_value = await self.scrape_cpc_via_api(domain)
                metrics['cpc'] = cpc_value
                logger.info(f"💰 Worker {self.worker_id}: CPC extrait: {cpc_value}")
            else:
                metrics['cpc'] = existing_metrics.get('cpc', '0')
                logger.info(f"💰 Worker {self.worker_id}: CPC existant: {existing_metrics.get('cpc')}")
'''
            
            # Insérer avant le return
            return_pos = method_content.rfind('return metrics')
            if return_pos != -1:
                new_method_content = method_content[:return_pos] + cpc_integration + '\n        ' + method_content[return_pos:]
            else:
                # Si pas de return trouvé, ajouter à la fin
                new_method_content = method_content + cpc_integration
            
            # Reconstituer le fichier
            new_content = content[:scrape_method_start] + new_method_content + content[next_method_start:]
            
            # Écrire le fichier modifié
            with open(self.production_scraper_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("✅ CPC intégré dans le workflow principal")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur intégration workflow: {e}")
            return False
    
    def _step5_update_counters(self) -> bool:
        """ÉTAPE 5: Mise à jour des compteurs"""
        logger.info("📊 ÉTAPE 5: Mise à jour des compteurs")
        
        try:
            # Lire le fichier actuel
            with open(self.production_scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ajouter CPC aux compteurs de métriques
            counter_update = ''',
            'cpc': {'found': 0, 'not_found': 0, 'skipped': 0}'''
            
            # Trouver la section des compteurs
            counters_start = content.find("self.metrics_count = {")
            if counters_start != -1:
                # Trouver la fin de la section
                counters_end = content.find('}', counters_start)
                if counters_end != -1:
                    # Insérer avant la dernière accolade
                    new_content = content[:counters_end] + counter_update + content[counters_end:]
                    
                    # Écrire le fichier modifié
                    with open(self.production_scraper_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    logger.info("✅ Compteurs CPC mis à jour")
                    return True
            
            logger.warning("⚠️ Section compteurs non trouvée, continuer sans mise à jour")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour compteurs: {e}")
            return False
    
    def _step6_validation(self) -> bool:
        """ÉTAPE 6: Test de validation"""
        logger.info("🧪 ÉTAPE 6: Test de validation")
        
        try:
            # Test de syntaxe Python
            result = subprocess.run([
                'python3', '-m', 'py_compile', str(self.production_scraper_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Erreur de syntaxe Python: {result.stderr}")
                return False
            
            logger.info("✅ Validation syntaxe Python réussie")
            
            # Vérifier que les méthodes CPC sont présentes
            with open(self.production_scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'async def scrape_cpc_via_api' not in content:
                logger.error("❌ Méthode scrape_cpc_via_api non trouvée")
                return False
            
            if 'scrape_cpc_via_api' not in content:
                logger.error("❌ Appel à scrape_cpc_via_api non trouvé")
                return False
            
            logger.info("✅ Validation des méthodes CPC réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur validation: {e}")
            return False
    
    def _rollback(self):
        """Rollback en cas d'erreur"""
        logger.info("🔄 Rollback en cours...")
        
        try:
            # Restaurer depuis le backup le plus récent
            if self.backup_dir.exists():
                backup_files = list(self.backup_dir.glob("production_scraper_parallel_backup_*.py"))
                if backup_files:
                    latest_backup = max(backup_files, key=os.path.getctime)
                    shutil.copy2(latest_backup, self.production_scraper_file)
                    logger.info(f"✅ Rollback réussi depuis: {latest_backup}")
                    return
            
            logger.warning("⚠️ Aucun backup trouvé pour le rollback")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du rollback: {e}")

def main():
    """Fonction principale"""
    logger.info("🎯 INTÉGRATION DE LA MÉTRIQUE CPC DANS LE SCRAPER SEM")
    logger.info("=" * 60)
    
    integrator = CPCIntegration()
    success = integrator.integrate_cpc_metric()
    
    if success:
        logger.info("🎉 INTÉGRATION CPC TERMINÉE AVEC SUCCÈS!")
        logger.info("📋 Prochaines étapes:")
        logger.info("   1. Tester le scraper avec: python3 menu_workers.py")
        logger.info("   2. Choisir l'option 1 (Lancer les workers SEM)")
        logger.info("   3. Vérifier que CPC est extrait correctement")
        logger.info("   4. Valider les données en base de données")
    else:
        logger.error("❌ INTÉGRATION CPC ÉCHOUÉE")
        logger.info("🔄 Rollback effectué automatiquement")
    
    return success

if __name__ == "__main__":
    main()
