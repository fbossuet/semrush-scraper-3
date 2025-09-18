#!/usr/bin/env python3
"""
Scraper de recherche par domaine spécifique pour TrendTrack
Intégration avec le système existant et la base de données partagée
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote
from datetime import datetime, timezone

# Imports du système existant
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from auth import TrendTrackDOMAuth
from utils.anti_detection import AntiDetectionSystem
from config.stealth_config import STEALTH_CONFIG, TRENDTRACK_CONFIG
from config.trendtrack_config import SELECTORS, METRICS_CONFIG, SCRAPING_CONFIG

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainSearchScraper:
    """
    Scraper pour la recherche par domaine spécifique sur TrendTrack
    Réutilise l'architecture existante et s'intègre avec la base de données
    """
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.auth_client = None
        self.browser = None
        self.anti_detection = None
        
        # Configuration workspace (fixe)
        self.workspace = "w-al-yakoobs-workspace-x0Qg9st"
        self.base_url = TRENDTRACK_CONFIG['base_url']
        
        # Headers pour l'API (basés sur votre exemple)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': '*/*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'RSC': '1',
            'Next-Router-State-Tree': '%5B%22%22%2C%7B%22children%22%3A%5B%5B%22locale%22%2C%22fr%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22(dynamic-pages)%22%2C%7B%22children%22%3A%5B%22(authenticated-pages)%22%2C%7B%22children%22%3A%5B%22(application-pages)%22%2C%7B%22children%22%3A%5B%22workspace%22%2C%7B%22children%22%3A%5B%5B%22workspaceSlug%22%2C%22w-al-yakoobs-workspace-x0Qg9st%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22trending-shops%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fworkspace%2Fw-al-yakoobs-workspace-x0Qg9st%2Ftrending-shops%22%2C%22refresh%22%5D%7D%2Cnull%2Cnull%2Ctrue%5D%2C%22navbar%22%3A%5B%22__DEFAULT__%22%2C%7B%7D%5D%2C%22sidebar%22%3A%5B%22__DEFAULT__%22%2C%7B%7D%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=4'
        }

    async def initialize(self) -> bool:
        """Initialise l'authentification et le navigateur"""
        try:
            logger.info("🔐 Initialisation de l'authentification TrendTrack")
            
            # 1. Authentification via notre système existant
            self.auth_client = TrendTrackDOMAuth(headless=True)
            auth_success = await self.auth_client.authenticate(
                self.credentials['email'], 
                self.credentials['password']
            )
            
            if not auth_success:
                logger.error("❌ Échec de l'authentification")
                return False
            
            # 2. Récupérer la page authentifiée
            self.page = await self.auth_client.get_authenticated_page()
            
            # 3. Initialiser le système anti-détection
            self.anti_detection = AntiDetectionSystem(stealth_level="medium")
            
            logger.info("✅ Initialisation réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            return False

    async def trigger_search(self, domain: str) -> bool:
        """Lance la recherche via navigation directe (même mécanique que le scraper traditionnel)"""
        try:
            logger.info(f"🚀 Déclenchement recherche pour {domain}")
            
            # Construction de l'URL de recherche (basée sur le scraper traditionnel)
            search_domain = quote(domain)
            # URL de base du scraper traditionnel + paramètre search
            search_url = f"{self.base_url}/fr/workspace/{self.workspace}/trending-shops?include=true&tab=websites&search={search_domain}&minTraffic=500000&languages=en&currencies=USD&creationCountry=US=include&orderBy=liveAds"
            
            logger.info(f"🌐 URL de recherche: {search_url}")
            
            # Navigation directe vers la page de recherche (même mécanique que le scraper traditionnel)
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
            
            # Attendre que la page se charge
            await self.page.wait_for_timeout(3000)
            
            # Vérifier si la recherche a fonctionné
            content = await self.page.content()
            
            if "No websites found for this filters" in content:
                logger.info("ℹ️ Aucun résultat trouvé pour ce domaine")
                return True  # La recherche a fonctionné, mais pas de résultats
            elif "table" in content.lower() and domain in content:
                logger.info("✅ Résultats trouvés pour ce domaine")
                return True
            else:
                logger.warning("⚠️ Résultat de recherche ambigu")
                return True  # On continue quand même
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return False

    async def scrape_results(self, domain: str) -> Dict[str, Any]:
        """Scrape les résultats depuis le DOM après chargement"""
        try:
            # Structure de base des données
            data = {
                "domain": domain,
                "shop_url": f"https://{domain}",
                "shop_name": domain,
                "scraping_status": "empty",  # Statut vide comme demandé
                "search_method": "domain_specific",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Appliquer des pauses anti-détection
            await self.anti_detection.random_delay()
            
            # Vérifier le contenu de la page
            content = await self.page.content()
            
            # Vérifier si "No websites found for this filters"
            if "No websites found for this filters" in content:
                logger.info("ℹ️ Message 'No websites found' détecté - aucun résultat")
                data["search_result"] = "no_results"
                data["error"] = "No websites found for this filters"
                return data
            
            # ========================================
            # 🎯 ZONE DE SCRAPING DOM - Sélecteurs basés sur l'HTML analysé
            # ========================================
            
            try:
                logger.info("🔍 Extraction des données du DOM...")
                
                # Chercher le tableau de résultats (basé sur l'HTML analysé)
                table_selector = "table.w-full.caption-bottom"
                await self.page.wait_for_selector(table_selector, timeout=10000)
                
                # Extraire les lignes du tableau
                rows = await self.page.locator("tbody tr").all()
                
                if rows:
                    logger.info(f"📊 {len(rows)} lignes trouvées dans le tableau")
                    
                    # Prendre la première ligne (comme spécifié)
                    first_row = rows[0]
                    
                    # Extraire les données de base
                    try:
                        # Nom du site (colonne 2)
                        site_name_element = first_row.locator("td:nth-child(2)")
                        if await site_name_element.count() > 0:
                            site_name = await site_name_element.inner_text()
                            data["site_name"] = site_name.strip()
                        
                        # Catégorie (colonne 4)
                        category_element = first_row.locator("td:nth-child(4)")
                        if await category_element.count() > 0:
                            category = await category_element.inner_text()
                            data["category"] = category.strip()
                        
                        # Visites mensuelles (colonne 5)
                        traffic_element = first_row.locator("td:nth-child(5)")
                        if await traffic_element.count() > 0:
                            traffic = await traffic_element.inner_text()
                            data["monthly_traffic"] = traffic.strip()
                        
                        # Revenu mensuel (colonne 6)
                        revenue_element = first_row.locator("td:nth-child(6)")
                        if await revenue_element.count() > 0:
                            revenue = await revenue_element.inner_text()
                            data["monthly_revenue"] = revenue.strip()
                        
                        # Marché (colonne 7)
                        market_element = first_row.locator("td:nth-child(7)")
                        if await market_element.count() > 0:
                            market = await market_element.inner_text()
                            data["market"] = market.strip()
                        
                        # Publicités en cours (colonne 8)
                        ads_element = first_row.locator("td:nth-child(8)")
                        if await ads_element.count() > 0:
                            ads = await ads_element.inner_text()
                            data["current_ads"] = ads.strip()
                        
                        data["search_result"] = "found"
                        logger.info("✅ Données extraites du DOM avec succès")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur lors de l'extraction des colonnes: {e}")
                        data["search_result"] = "partial"
                
                else:
                    logger.warning("⚠️ Aucune ligne trouvée dans le tableau")
                    data["search_result"] = "no_table"
                
            except Exception as selector_error:
                logger.error(f"❌ Erreur lors de l'extraction DOM: {selector_error}")
                
                # Debug - sauvegarder le HTML pour analyse
                html_content = await self.page.content()
                debug_filename = f"debug_{domain.replace('.', '_')}_{int(time.time())}.html"
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"💾 HTML sauvegardé dans {debug_filename} pour debug")
                
                data["search_result"] = "error"
                data["error"] = str(selector_error)
            
            return data
                
        except Exception as e:
            logger.error(f"❌ Erreur générale lors du scraping: {e}")
            return {"domain": domain, "error": str(e), "search_result": "error"}

    async def search_domain(self, domain: str) -> Dict[str, Any]:
        """
        Processus complet: Recherche + Scraping DOM
        
        Args:
            domain (str): Le domaine à rechercher (ex: "cakesbody.com")
        """
        logger.info(f"🎯 Début de la recherche pour: {domain}")
        
        # 1. Déclencher la recherche via navigation directe
        search_success = await self.trigger_search(domain)
        
        if not search_success:
            logger.error("❌ Impossible de déclencher la recherche")
            return {"domain": domain, "error": "Search failed"}
        
        # 2. Scraper les résultats depuis le DOM
        results = await self.scrape_results(domain)
        
        return results

    async def close(self):
        """Fermer le navigateur"""
        if self.auth_client:
            await self.auth_client.close()
            logger.info("🔐 Navigateur fermé")

# ========================================
# 🎯 INTÉGRATION AVEC LA BASE DE DONNÉES
# ========================================

class DomainSearchIntegration:
    """Intégration avec la base de données partagée"""
    
    def __init__(self, db_path: str = "./data/trendtrack.db"):
        self.db_path = db_path
    
    def store_domain_result(self, result: Dict[str, Any]) -> bool:
        """Stocke le résultat dans la base de données partagée (même mécanique que le scraper traditionnel)"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si le shop existe déjà (même mécanique que le scraper traditionnel)
            cursor.execute("SELECT id FROM shops WHERE shop_url = ?", (result['shop_url'],))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"ℹ️ Shop {result['domain']} existe déjà, mise à jour...")
                # Mettre à jour avec toutes les métriques extraites
                cursor.execute("""
                    UPDATE shops 
                    SET scraping_status = ?, 
                        shop_name = ?,
                        monthly_visits = ?,
                        monthly_revenue = ?,
                        live_ads = ?,
                        project_source = ?,
                        updated_at = ?
                    WHERE shop_url = ?
                """, (
                    result['scraping_status'],
                    result.get('site_name', result['shop_name']),
                    self._validate_int(result.get('monthly_traffic')),
                    result.get('monthly_revenue'),
                    result.get('current_ads'),
                    'semtotrendtrack',  # Source pour la nouvelle fonctionnalité
                    datetime.now(timezone.utc).isoformat(),
                    result['shop_url']
                ))
            else:
                logger.info(f"➕ Nouveau shop {result['domain']}, insertion...")
                # Insérer nouveau shop avec toutes les métriques
                cursor.execute("""
                    INSERT INTO shops (
                        shop_url, shop_name, scraping_status, 
                        monthly_visits, monthly_revenue, live_ads, project_source,
                   updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['shop_url'], 
                    result.get('site_name', result['shop_name']),
                    result['scraping_status'],
                    self._validate_int(result.get('monthly_traffic')),
                    result.get('monthly_revenue'),
                    result.get('current_ads'),
                    'semtotrendtrack',  # Source pour la nouvelle fonctionnalité
                    datetime.now(timezone.utc).isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Shop {result['domain']} stocké avec succès (source: semtotrendtrack)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage: {e}")
            return False
    
    def _validate_int(self, value):
        """Valide qu'une valeur est un INTEGER valide"""
        if not value or value == 'na' or value == '':
            return None
        try:
            if isinstance(value, int):
                return value
            cleaned = str(value).replace(',', '').replace(' ', '').replace('$', '')
            return int(float(cleaned))
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valeur '{value}' n'est pas un INTEGER valide")
            return None

# ========================================
# 🎯 FONCTION PRINCIPALE D'INTÉGRATION
# ========================================

async def search_and_store_domain(domain: str, credentials: Dict[str, str]) -> Dict[str, Any]:
    """
    Fonction principale pour rechercher un domaine et le stocker
    
    Args:
        domain (str): Le domaine à rechercher
        credentials (Dict[str, str]): Credentials TrendTrack
    
    Returns:
        Dict[str, Any]: Résultat de la recherche
    """
    scraper = DomainSearchScraper(credentials)
    integration = DomainSearchIntegration()
    
    try:
        # Initialiser le scraper
        if not await scraper.initialize():
            return {"domain": domain, "error": "Initialization failed"}
        
        # Rechercher le domaine
        result = await scraper.search_domain(domain)
        
        if "error" not in result:
            # Stocker dans la base de données
            store_success = integration.store_domain_result(result)
            result["stored"] = store_success
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur dans search_and_store_domain: {e}")
        return {"domain": domain, "error": str(e)}
        
    finally:
        await scraper.close()

# ========================================
# 🎯 EXEMPLE D'UTILISATION
# ========================================

async def main():
    """Fonction principale d'exemple"""
    
    # Credentials TrendTrack
    credentials = {
        'email': 'seif.alyakoob@gmail.com',
        'password': 'Toulouse31!'
    }
    
    # Domaine à rechercher
    domain = "cakesbody.com"
    
    logger.info(f"🚀 Lancement de la recherche pour: {domain}")
    
    # Lancer la recherche complète
    result = await search_and_store_domain(domain, credentials)
    
    # Afficher les résultats
    if result and "error" not in result:
        logger.info("\n✅ 🎯 RÉSULTATS FINAUX:")
        logger.info("=" * 50)
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        logger.error("\n❌ Aucune donnée trouvée ou erreur:")
        logger.error(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())


