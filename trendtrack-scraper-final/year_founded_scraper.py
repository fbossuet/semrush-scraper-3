#!/usr/bin/env python3
"""
Scraper spécialisé pour récupérer l'année de fondation des boutiques
via interception d'API avec Playwright
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YearFoundedScraper:
    """Scraper pour récupérer l'année de fondation des boutiques via API"""
    
    def __init__(self, db_path: str = None):
        """Initialise le scraper"""
        self.db_path = db_path or self._get_database_path()
        self.browser: Optional[Browser] = None
        self.concurrency = 3
        self.delay = 2000  # ms
        self.timeout = 30000  # ms
        
    def _get_database_path(self) -> str:
        """Détermine le chemin de la base de données selon l'environnement"""
        # Vérifier si on est sur le VPS par la présence d'un fichier spécifique
        vps_detected = os.path.exists("/home/ubuntu")
        
        if vps_detected:
            # VPS Linux - utiliser la base existante
            db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
            return db_path
        else:
            # macOS local
            db_path = "/Users/infusion/Desktop/trendtrack-scrapper/data/trendtrack.db"
            return db_path
    
    async def init(self):
        """Initialise le navigateur Playwright"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("✅ Navigateur Playwright initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation navigateur: {e}")
            raise
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape une boutique pour récupérer l'année de fondation"""
        if not self.browser:
            await self.init()
            
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"🔍 Scraping année de fondation: {url}")
            
            api_data = []
            
            # Intercepter les requêtes API avec Playwright
            async def handle_response(response):
                try:
                    response_url = response.url
                    
                    if self._is_relevant_api(response_url):
                        try:
                            data = await response.json()
                            if self._contains_target_data(data):
                                api_data.append({
                                    'url': response_url,
                                    'method': response.request.method,
                                    'status': response.status,
                                    'data': data
                                })
                                logger.info(f"📡 API pertinente trouvée: {response_url}")
                        except Exception as e:
                            # Ignore les erreurs de parsing JSON
                            pass
                except Exception as e:
                    pass
            
            page.on('response', handle_response)
            
            # Navigation avec timeout
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Attendre le chargement des données dynamiques
            await page.wait_for_timeout(3000)
            
            load_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Extraire les données du DOM pour les dates
            dom_data = await page.evaluate("""
                () => {
                    const findDates = () => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        return elements
                            .filter(el => el.textContent && el.textContent.match(/\\d{2}\\/\\d{2}\\/\\d{4}|\\d{4}-\\d{2}-\\d{2}|\\d{4}/))
                            .map(el => ({
                                text: el.textContent.trim(),
                                tag: el.tagName
                            }))
                            .slice(0, 10); // Limiter à 10 résultats
                    };

                    return {
                        title: document.title || '',
                        url: window.location.href,
                        dates: findDates(),
                        metaDescription: document.querySelector('meta[name="description"]')?.content || '',
                        h1Count: document.querySelectorAll('h1').length,
                        imageCount: document.querySelectorAll('img').length
                    };
                }
            """)
            
            # Extraire l'année de fondation des données collectées
            year_founded = self._extract_year_founded(api_data, dom_data)
            
            # Sauvegarder en base
            result = await self._save_year_founded(url, year_founded, api_data, dom_data, load_time)
            
            return {
                'url': url,
                'success': True,
                'year_founded': year_founded,
                'api_count': len(api_data),
                'load_time': load_time,
                'shop_id': result.get('shop_id')
            }
            
        except Exception as error:
            logger.error(f"❌ Erreur pour {url}: {error}")
            await self._save_error(url, str(error), type(error).__name__)
            return {'url': url, 'success': False, 'error': str(error)}
        finally:
            await context.close()
    
    def _is_relevant_api(self, url: str) -> bool:
        """Filtre les APIs pertinentes"""
        static_extensions = r'\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico|webp)(\?.*)?$'
        relevant_paths = r'(api|data|ajax|json|graphql|analytics|metrics|stats|company|about|founded)'
        
        import re
        return not re.search(static_extensions, url, re.IGNORECASE) and \
               re.search(relevant_paths, url, re.IGNORECASE)
    
    def _contains_target_data(self, data: Any) -> bool:
        """Vérifie si les données contiennent des informations pertinentes"""
        if not data or not isinstance(data, (dict, list)):
            return False
        
        json_str = json.dumps(data).lower()
        target_keywords = [
            'shop_created_at',
            'website',
            'domain',
            'traffic',
            'visitors',
            'analytics',
            'created_at',
            'launch_date',
            'founded',
            'established',
            'year',
            'company',
            'about'
        ]
        
        return any(keyword in json_str for keyword in target_keywords) or \
               bool(re.search(r'\d{4}-\d{2}-\d{2}|\d{4}', json_str))
    
    def _extract_year_founded(self, api_data: List[Dict], dom_data: Dict) -> Optional[str]:
        """Extrait l'année de fondation des données collectées"""
        # Chercher dans les données API
        for api in api_data:
            data = api['data']
            
            # Chercher des champs spécifiques
            year_fields = [
                'shop_created_at', 'created_at', 'launch_date', 
                'founded', 'established', 'year_founded', 'founding_year'
            ]
            
            for field in year_fields:
                if field in data:
                    year_value = data[field]
                    if year_value:
                        year = self._extract_year_from_string(str(year_value))
                        if year:
                            logger.info(f"📅 Année trouvée dans API ({field}): {year}")
                            return year
            
            # Chercher dans les structures imbriquées
            if isinstance(data, dict):
                year = self._search_year_in_dict(data)
                if year:
                    return year
        
        # Chercher dans les données DOM
        if dom_data.get('dates'):
            for date_info in dom_data['dates']:
                year = self._extract_year_from_string(date_info['text'])
                if year and self._is_valid_founding_year(year):
                    logger.info(f"📅 Année trouvée dans DOM: {year}")
                    return year
        
        return None
    
    def _search_year_in_dict(self, data: Dict, max_depth: int = 3) -> Optional[str]:
        """Recherche récursive d'année dans un dictionnaire"""
        if max_depth <= 0:
            return None
        
        for key, value in data.items():
            if isinstance(value, dict):
                year = self._search_year_in_dict(value, max_depth - 1)
                if year:
                    return year
            elif isinstance(value, str):
                year = self._extract_year_from_string(value)
                if year and self._is_valid_founding_year(year):
                    return year
        
        return None
    
    def _extract_year_from_string(self, text: str) -> Optional[str]:
        """Extrait une année d'une chaîne de caractères"""
        import re
        
        # Patterns pour différents formats de dates
        patterns = [
            r'\b(19|20)\d{2}\b',  # Année simple (1900-2099)
            r'\d{4}-\d{2}-\d{2}',  # Format ISO
            r'\d{2}/\d{2}/\d{4}',   # Format MM/DD/YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Prendre la première année trouvée
                if isinstance(matches[0], tuple):
                    year = matches[0][0] + matches[0][1] if len(matches[0]) > 1 else matches[0][0]
                else:
                    year = matches[0]
                
                if self._is_valid_founding_year(year):
                    return year
        
        return None
    
    def _is_valid_founding_year(self, year: str) -> bool:
        """Vérifie si l'année est valide pour une fondation d'entreprise"""
        try:
            year_int = int(year)
            current_year = datetime.now(timezone.utc).year
            # Accepter les années entre 1800 et l'année actuelle
            return 1800 <= year_int <= current_year
        except (ValueError, TypeError):
            return False
    
    async def _save_year_founded(self, url: str, year_founded: Optional[str], 
                                api_data: List[Dict], dom_data: Dict, load_time: float) -> Dict:
        """Sauvegarde l'année de fondation en base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Trouver le shop_id correspondant à l'URL
            cursor.execute("SELECT id FROM shops WHERE shop_url = ?", (url,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"⚠️ Boutique non trouvée pour l'URL: {url}")
                return {}
            
            shop_id = result[0]
            
            # Mettre à jour la colonne year_founded
            cursor.execute(
                "UPDATE shops SET year_founded = ?, updated_at = ? WHERE id = ?",
                (year_founded, datetime.now(timezone.utc).isoformat(), shop_id)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Année de fondation sauvegardée pour {url}: {year_founded}")
            return {'shop_id': shop_id, 'year_founded': year_founded}
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde pour {url}: {e}")
            return {}
    
    async def _save_error(self, url: str, error_message: str, error_type: str = 'unknown'):
        """Sauvegarde les erreurs en base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Créer la table d'erreurs si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    error_message TEXT,
                    error_type TEXT,
                    scraped_at DATETIME DEFAULT datetime.now(timezone.utc).isoformat()
                )
            """)
            
            cursor.execute(
                "INSERT INTO scraping_errors (url, error_message, error_type) VALUES (?, ?, ?)",
                (url, error_message, error_type)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde erreur: {e}")
    
    async def scrape_all_shops(self, limit: int = None) -> Dict[str, Any]:
        """Scrape toutes les boutiques pour récupérer l'année de fondation"""
        await self.init()
        
        try:
            # Récupérer les URLs des boutiques
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT id, shop_url FROM shops WHERE shop_url IS NOT NULL AND shop_url != ''"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            shops = cursor.fetchall()
            conn.close()
            
            logger.info(f"📊 {len(shops)} boutiques à traiter")
            
            # Traitement par batches
            batches = self._chunk_array(shops, self.concurrency)
            total_processed = 0
            total_successful = 0
            results = []
            
            for i, batch in enumerate(batches):
                logger.info(f"📦 Traitement du batch {i + 1}/{len(batches)}")
                
                tasks = []
                for shop_id, url in batch:
                    if self.delay > 0:
                        await asyncio.sleep(self.delay / 1000)
                    tasks.append(self.scrape_website(url))
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                successful = sum(1 for r in batch_results if isinstance(r, dict) and r.get('success'))
                total_processed += len(batch)
                total_successful += successful
                
                results.extend([r for r in batch_results if isinstance(r, dict)])
                
                logger.info(f"📊 Batch {i + 1} terminé: {successful}/{len(batch)} succès")
                logger.info(f"📈 Total: {total_successful}/{total_processed} ({((total_successful/total_processed)*100):.1f}%)")
            
            await self.browser.close()
            
            # Statistiques finales
            stats = await self._get_stats()
            logger.info(f"🎉 Scraping terminé ! Statistiques: {stats}")
            
            return {
                'total_processed': total_processed,
                'total_successful': total_successful,
                'success_rate': (total_successful / total_processed * 100) if total_processed > 0 else 0,
                'results': results,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur globale: {e}")
            if self.browser:
                await self.browser.close()
            raise
    
    def _chunk_array(self, array: List, size: int) -> List[List]:
        """Divise un tableau en chunks"""
        chunks = []
        for i in range(0, len(array), size):
            chunks.append(array[i:i + size])
        return chunks
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de scraping"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = cursor.execute("""
                SELECT 
                    COUNT(*) as total_shops,
                    COUNT(CASE WHEN year_founded IS NOT NULL AND year_founded != '' THEN 1 END) as with_year_founded,
                    COUNT(CASE WHEN scraping_status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN scraping_status = 'partial' THEN 1 END) as partial
                FROM shops
            """).fetchone()
            
            conn.close()
            
            return {
                'total_shops': stats[0],
                'with_year_founded': stats[1],
                'completed': stats[2],
                'partial': stats[3]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération stats: {e}")
            return {}

# Fonction principale pour l'utilisation
async def main():
    """Fonction principale pour tester le scraper"""
    scraper = YearFoundedScraper()
    
    try:
        # Test avec quelques boutiques
        results = await scraper.scrape_all_shops(limit=5)
        
        print(f"\n📊 Résultats du scraping:")
        print(f"   Total traité: {results['total_processed']}")
        print(f"   Succès: {results['total_successful']}")
        print(f"   Taux de succès: {results['success_rate']:.1f}%")
        
        # Afficher les résultats détaillés
        for result in results['results']:
            if result.get('success'):
                print(f"   ✅ {result['url']}: {result.get('year_founded', 'Non trouvé')}")
            else:
                print(f"   ❌ {result['url']}: {result.get('error', 'Erreur inconnue')}")
        
    except Exception as e:
        logger.error(f"❌ Erreur dans main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
