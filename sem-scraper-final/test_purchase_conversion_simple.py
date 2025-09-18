#!/usr/bin/env python3
"""
Script de test simplifié pour purchase_conversion
Basé sur le scraper principal - même configuration réseau
Objectif : Tester uniquement purchase_conversion sans BDD
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from global_bootstrap import get_shared_browser_context
from stealth_system import stealth_system

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Domaines de test avec leurs folder_id (basés sur les infos récupérées)
TEST_DOMAINS = [
    {"domain": "shopbala.com", "fid": 1336381},
    {"domain": "ridge.com", "fid": 1336382},  
    {"domain": "trtltravel.com", "fid": 1336616},
    {"domain": "archiesfootwear.com", "fid": 1336614},
    {"domain": "hismileteeth.com", "fid": 1336606}
]

class PurchaseConversionTester:
    def __init__(self, worker_id=0):
        self.worker_id = worker_id
        self.context = None
        self.page = None

    async def setup_browser(self):
        """Configuration du navigateur avec session partagée (copié du scraper principal)"""
        logger.info(f"🔧 Worker {self.worker_id}: Configuration du navigateur...")
        
        try:
            self.context = await get_shared_browser_context()
            self.page = await self.context.new_page()
            logger.info(f"✅ Worker {self.worker_id}: Navigateur configuré (session partagée)")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur configuration navigateur: {e}")
            raise

    async def sync_cookies_with_sam(self):
        """Synchronisation des cookies avec sam.mytoolsplan.xyz (copié du scraper principal)"""
        logger.info(f"🔄 Worker {self.worker_id}: Synchronisation des cookies avec sam.mytoolsplan.xyz...")
        
        try:
            # Récupérer TOUS les cookies (pas seulement les cookies d'auth spécifiques)
            cookies = await self.context.cookies()
            logger.info(f"📊 Worker {self.worker_id}: Cookies récupérés: {len(cookies)} cookies")
            
            # Debug des cookies d'authentification
            auth_cookies = [c for c in cookies if 'auth' in c.get('name', '').lower() or 'session' in c.get('name', '').lower()]
            logger.info(f"🔍 Worker {self.worker_id}: {len(auth_cookies)} cookies d'authentification identifiés")
            
            logger.info(f"🔍 Worker {self.worker_id}: Synchronisation de TOUS les cookies pour l'authentification")
            if cookies:
                await self.context.add_cookies(cookies)
                logger.info(f"✅ Worker {self.worker_id}: {len(cookies)} cookies synchronisés")
            
            # Test de la session sur app.mytoolsplan.com/analytics/
            logger.info(f"🔍 Worker {self.worker_id}: Test de la session sur app.mytoolsplan.com/analytics/...")
            await self.page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            logger.info(f"🔍 Worker {self.worker_id}: URL après test session: {current_url}")
            
            # Navigation vers sam.mytoolsplan.xyz pour synchroniser les cookies sur ce domaine
            logger.info(f"🌐 Worker {self.worker_id}: Synchronisation cookies vers sam.mytoolsplan.xyz/analytics/...")
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            if "analytics" in current_url:
                logger.info(f"✅ Worker {self.worker_id}: Session synchronisée avec succès sur sam.mytoolsplan.xyz")
                return True
            else:
                logger.warning(f"⚠️ Worker {self.worker_id}: Session partiellement synchronisée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur synchronisation cookies: {e}")
            return False

    async def get_folder_id_for_domain(self, domain):
        """Récupération du folder_id pour un domaine (copié du scraper principal)"""
        logger.info(f"🔍 Worker {self.worker_id}: Récupération folder_id pour {domain}")
        
        # Navigation vers sam.mytoolsplan.xyz/analytics/ pour l'API projets
        logger.info(f"🌐 Worker {self.worker_id}: Navigation vers sam.mytoolsplan.xyz/analytics/ pour l'API projets...")
        await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        
        # Nettoyer le domaine
        domain_clean = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Appel API pour récupérer le folder_id
        result = await self.page.evaluate("""
            async (domain) => {
                try {
                    const response = await fetch('/apis/v4-raw/folders/api/v0/folders/selector-list?limit=2000&offset=0', {
                        method: 'GET',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });
                    
                    if (!response.ok) {
                        return {
                            success: false,
                            status: response.status,
                            error: await response.text()
                        };
                    }
                    
                    const data = await response.json();
                    const folders = data.data || [];
                    
                    // Rechercher le dossier correspondant au domaine
                    for (const folder of folders) {
                        if (folder.name && folder.name.value) {
                            const folderName = folder.name.value.toLowerCase();
                            if (folderName.includes(domain.toLowerCase()) || 
                                domain.toLowerCase().includes(folderName.replace('.com', ''))) {
                                return {
                                    success: true,
                                    folder_id: folder.id,
                                    folder_name: folder.name.value
                                };
                            }
                        }
                    }
                    
                    return {
                        success: false,
                        error: 'Folder not found',
                        available_folders: folders.map(f => f.name?.value).filter(Boolean)
                    };
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            }
        """, domain_clean)
        
        if result.get('success'):
            folder_id = result.get('folder_id')
            folder_name = result.get('folder_name')
            logger.info(f"✅ Worker {self.worker_id}: Folder trouvé - ID: {folder_id}, Nom: {folder_name}")
            return folder_id
        else:
            logger.error(f"❌ Worker {self.worker_id}: Erreur récupération folder_id: {result.get('error')}")
            if 'available_folders' in result:
                logger.info(f"🔍 Worker {self.worker_id}: Dossiers disponibles: {result['available_folders'][:5]}")
            return None

    async def scrape_purchase_conversion(self, domain, folder_id):
        """Scraping purchase_conversion (copié du scraper principal)"""
        logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Appel scrape_purchase_conversion pour {domain}")
        logger.info(f"🔍 Worker {self.worker_id}: DEBUG - DÉBUT scrape_purchase_conversion pour {domain}")
        
        try:
            # Récupérer le folder_id si pas fourni
            if not folder_id:
                folder_id = await self.get_folder_id_for_domain(domain)
                if not folder_id:
                    logger.error(f"❌ Worker {self.worker_id}: Impossible de récupérer folder_id pour {domain}")
                    return ""
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - FID récupéré: {folder_id}")
            
            # 2. Navigation vers Traffic Analytics avec FID
            target_url = f"https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/?fid={folder_id}"
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Navigation vers: {target_url}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - folder_id: {folder_id}")
            
            logger.info(f"🌐 Worker {self.worker_id}: Navigation vers Traffic Analytics Conversion")
            await self.page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            # Debug de l'URL et du contenu de la page
            current_url = self.page.url
            page_title = await self.page.title()
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - URL actuelle: {current_url}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Titre de la page: {page_title}")
            
            # Vérifier le contenu de la page
            page_content = await self.page.evaluate("() => document.body.textContent")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Contenu page (premiers 500 chars): {page_content[:500]}")
            
            # Si la page est vide, attendre plus longtemps pour React SPA
            if len(page_content.strip()) < 100:
                logger.warning(f"⚠️ Worker {self.worker_id}: Page vide détectée, attente supplémentaire pour React SPA...")
                await asyncio.sleep(5)  # Attendre 5 secondes supplémentaires
                
                # Vérifier à nouveau
                page_content = await self.page.evaluate("() => document.body.textContent")
                logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Contenu page après attente (premiers 500 chars): {page_content[:500]}")
                
                if len(page_content.strip()) < 100:
                    logger.error(f"❌ Worker {self.worker_id}: Page toujours vide après attente - problème de permissions ou de session")
                    
                    # Debug supplémentaire : vérifier les cookies et la session
                    cookies = await self.context.cookies()
                    logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Cookies disponibles: {len(cookies)}")
                    
                    # Tester la session sur app.mytoolsplan.com
                    try:
                        await self.page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=10000)
                        app_content = await self.page.evaluate("() => document.body.textContent")
                        logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Contenu app.mytoolsplan.com (premiers 200 chars): {app_content[:200]}")
                        
                        if len(app_content.strip()) > 100:
                            logger.warning(f"⚠️ Worker {self.worker_id}: Session OK sur app.mytoolsplan.com mais pas sur sam.mytoolsplan.xyz - problème de synchronisation")
                        else:
                            logger.error(f"❌ Worker {self.worker_id}: Session KO sur app.mytoolsplan.com aussi - problème d'authentification")
                    except Exception as e:
                        logger.error(f"❌ Worker {self.worker_id}: Erreur test session app.mytoolsplan.com: {e}")
                    
                    return ""
            
            # Nettoyer le domaine pour la recherche
            clean_domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '')
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Domaine nettoyé pour JavaScript: '{clean_domain}'")
            
            # Scraping JavaScript (copié du scraper principal)
            conversion_data = await self.page.evaluate(f"""
                () => {{
                    const result = {{
                        purchaseConversion: null,
                        found: false,
                        allData: [],
                        testIdElements: 0,
                        domainElements: 0,
                        tableElements: 0,
                        attempts: 0,
                        allSelectors: {{
                            tables: 0,
                            divs: 0,
                            spans: 0,
                            allElements: 0,
                            gridElements: 0,
                            rowElements: 0,
                            cellElements: 0,
                            testIdElements: 0,
                            reactRoot: false,
                            root: true
                        }}
                    }};
                    
                    // Compter les éléments
                    result.allSelectors.tables = document.querySelectorAll('table').length;
                    result.allSelectors.divs = document.querySelectorAll('div').length;
                    result.allSelectors.spans = document.querySelectorAll('span').length;
                    result.allSelectors.allElements = document.querySelectorAll('*').length;
                    result.allSelectors.gridElements = document.querySelectorAll('[class*="grid"]').length;
                    result.allSelectors.rowElements = document.querySelectorAll('[class*="row"]').length;
                    result.allSelectors.cellElements = document.querySelectorAll('[class*="cell"]').length;
                    result.allSelectors.testIdElements = document.querySelectorAll('[data-testid]').length;
                    
                    // Vérifier React
                    result.allSelectors.reactRoot = !!document.querySelector('#root');
                    
                    // Chercher les données de conversion
                    const domainVariations = [
                        '{clean_domain}',
                        '{clean_domain}'.replace('.com', ''),
                        '{clean_domain}'.replace('www.', ''),
                        '{clean_domain}'.replace('https://', '').replace('http://', '')
                    ];
                    
                    // Compter les éléments contenant le domaine
                    for (const variation of domainVariations) {{
                        const elements = document.querySelectorAll(`*:contains("${{variation}}")`);
                        result.domainElements += elements.length;
                    }}
                    
                    // Chercher dans les tables
                    const tables = document.querySelectorAll('table');
                    result.tableElements = tables.length;
                    
                    for (const table of tables) {{
                        const rows = table.querySelectorAll('tr');
                        for (const row of rows) {{
                            const rowText = row.textContent || '';
                            result.allData.push(rowText.substring(0, 100));
                            
                            // Chercher des données de conversion
                            if (rowText.includes('conversion') || rowText.includes('purchase') || rowText.includes('%')) {{
                                console.log('🔍 Données de conversion trouvées:', rowText);
                            }}
                        }}
                    }}
                    
                    return result;
                }}
            """)
            
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Résultat JavaScript: {conversion_data}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments domaine: {conversion_data.get('domainElements', 0)}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Données trouvées: {conversion_data.get('allData', [])}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Éléments table: {conversion_data.get('tableElements', 0)}")
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Tentatives: {conversion_data.get('attempts', 0)}")
            
            # Extraire la valeur de conversion si trouvée
            conversion_rate = conversion_data.get('purchaseConversion', '')
            logger.info(f"🔍 Worker {self.worker_id}: DEBUG - Résultat scrape_purchase_conversion: '{conversion_rate}'")
            
            return conversion_rate
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scrape_purchase_conversion: {e}")
            return ""

    async def test_domain(self, domain_info):
        """Test complet pour un domaine"""
        domain = domain_info["domain"]
        folder_id = domain_info["fid"]
        
        logger.info(f"🎯 Worker {self.worker_id}: TEST COMPLET pour {domain} (FID: {folder_id})")
        
        try:
            # Synchronisation des cookies (copié du scraper principal)
            await self.sync_cookies_with_sam()
            
            # Test du scraping purchase_conversion
            result = await self.scrape_purchase_conversion(domain, folder_id)
            
            logger.info(f"✅ Worker {self.worker_id}: Test terminé pour {domain}")
            logger.info(f"📊 Worker {self.worker_id}: Résultat conversion_rate: '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur test {domain}: {e}")
            return None

async def main():
    """Fonction principale de test"""
    logger.info("🚀 DÉMARRAGE TEST PURCHASE_CONVERSION SIMPLIFIÉ")
    
    tester = PurchaseConversionTester()
    
    try:
        # Configuration du navigateur
        await tester.setup_browser()
        
        # Test de chaque domaine
        for domain_info in TEST_DOMAINS:
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST DOMAINE: {domain_info['domain']} (FID: {domain_info['fid']})")
            logger.info(f"{'='*60}")
            
            result = await tester.test_domain(domain_info)
            
            if result:
                logger.info(f"✅ Résultat pour {domain_info['domain']}: '{result}'")
            else:
                logger.error(f"❌ Échec pour {domain_info['domain']}")
            
            # Pause entre les tests
            await asyncio.sleep(2)
        
        logger.info("\n🎉 TOUS LES TESTS TERMINÉS")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        logger.info("🔒 Fin du test")

if __name__ == "__main__":
    asyncio.run(main())
