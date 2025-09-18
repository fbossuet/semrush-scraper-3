#!/usr/bin/env python3
"""
Script de test isolé pour diagnostiquer purchase_conversion
Objectif : Accéder à la métrique sans toucher à la BDD
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from global_bootstrap import get_shared_browser_context

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
        """Configuration du navigateur avec session partagée"""
        logger.info(f"🔧 Worker {self.worker_id}: Configuration du navigateur...")
        
        try:
            self.context = await get_shared_browser_context()
            self.page = await self.context.new_page()
            logger.info(f"✅ Worker {self.worker_id}: Navigateur configuré (session partagée)")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur configuration navigateur: {e}")
            raise

    async def authenticate_and_sync(self):
        """Authentification et synchronisation des cookies"""
        logger.info(f"🔍 Worker {self.worker_id}: Authentification et synchronisation...")
        
        # Récupérer TOUS les cookies
        cookies = await self.context.cookies()
        logger.info(f"📊 Worker {self.worker_id}: Cookies récupérés: {len(cookies)} cookies")
        
        if cookies:
            await self.context.add_cookies(cookies)
            logger.info(f"✅ Worker {self.worker_id}: {len(cookies)} cookies synchronisés")
        
        # Navigation vers app.mytoolsplan.com pour authentification
        logger.info(f"🌐 Worker {self.worker_id}: Navigation vers app.mytoolsplan.com pour authentification...")
        await self.page.goto("https://app.mytoolsplan.com/", wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(3)
        
        current_url = self.page.url
        logger.info(f"🔍 Worker {self.worker_id}: URL après authentification: {current_url}")
        
        # Vérifier si on est authentifié
        if "member" in current_url or "analytics" in current_url:
            logger.info(f"✅ Worker {self.worker_id}: Authentification réussie")
            
            # Maintenant essayer d'accéder à sam.mytoolsplan.xyz
            logger.info(f"🌐 Worker {self.worker_id}: Test d'accès à sam.mytoolsplan.xyz...")
            try:
                await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=10000)
                await asyncio.sleep(2)
                sam_url = self.page.url
                logger.info(f"🔍 Worker {self.worker_id}: URL sam.mytoolsplan.xyz: {sam_url}")
                
                if "analytics" in sam_url:
                    logger.info(f"✅ Worker {self.worker_id}: Accès à sam.mytoolsplan.xyz réussi")
                    return True
                else:
                    logger.warning(f"⚠️ Worker {self.worker_id}: Redirection depuis sam.mytoolsplan.xyz vers: {sam_url}")
                    return True  # Redirection OK
            except Exception as e:
                logger.warning(f"⚠️ Worker {self.worker_id}: Erreur accès sam.mytoolsplan.xyz: {e}")
                return False
        else:
            logger.warning(f"⚠️ Worker {self.worker_id}: Authentification échouée - URL: {current_url}")
            return False

    async def get_folder_id_for_domain(self, domain):
        """Récupération du folder_id pour un domaine"""
        logger.info(f"🔍 Worker {self.worker_id}: Récupération folder_id pour {domain}")
        
        # Essayer d'abord sam.mytoolsplan.xyz (API des dossiers)
        try:
            logger.info(f"🌐 Worker {self.worker_id}: Tentative navigation vers sam.mytoolsplan.xyz pour l'API projets...")
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/", wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ Worker {self.worker_id}: Impossible d'accéder à sam.mytoolsplan.xyz: {e}")
            # Fallback vers app.mytoolsplan.com
            logger.info(f"🌐 Worker {self.worker_id}: Fallback vers app.mytoolsplan.com/analytics/...")
            await self.page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=30000)
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

    async def test_purchase_conversion_scraping(self, domain, folder_id):
        """Test du scraping purchase_conversion avec diagnostic complet"""
        logger.info(f"🔍 Worker {self.worker_id}: TEST purchase_conversion pour {domain} (FID: {folder_id})")
        
        # Construction de l'URL (utiliser l'URL du scraper principal qui fonctionne)
        target_url = f"https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/?fid={folder_id}"
        logger.info(f"🌐 Worker {self.worker_id}: Navigation vers: {target_url}")
        
        # Navigation
        await self.page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)
        
        # Debug de l'URL et du contenu de la page
        current_url = self.page.url
        page_title = await self.page.title()
        logger.info(f"🔍 Worker {self.worker_id}: URL actuelle: {current_url}")
        logger.info(f"🔍 Worker {self.worker_id}: Titre de la page: {page_title}")
        
        # Vérifier le contenu de la page
        page_content = await self.page.evaluate("() => document.body.textContent")
        logger.info(f"🔍 Worker {self.worker_id}: Contenu page (premiers 500 chars): {page_content[:500]}")
        
        # Si la page est vide, diagnostic approfondi
        if len(page_content.strip()) < 100:
            logger.warning(f"⚠️ Worker {self.worker_id}: Page vide détectée, diagnostic approfondi...")
            
            # Vérifier les cookies
            cookies = await self.context.cookies()
            logger.info(f"🔍 Worker {self.worker_id}: Cookies disponibles: {len(cookies)}")
            
            # Tester la session sur app.mytoolsplan.com
            try:
                await self.page.goto("https://app.mytoolsplan.com/analytics/", wait_until='domcontentloaded', timeout=10000)
                app_content = await self.page.evaluate("() => document.body.textContent")
                logger.info(f"🔍 Worker {self.worker_id}: Contenu app.mytoolsplan.com (premiers 200 chars): {app_content[:200]}")
                
                if len(app_content.strip()) > 100:
                    logger.warning(f"⚠️ Worker {self.worker_id}: Session OK sur app.mytoolsplan.com mais pas sur sam.mytoolsplan.xyz - problème de synchronisation")
                else:
                    logger.error(f"❌ Worker {self.worker_id}: Session KO sur app.mytoolsplan.com aussi - problème d'authentification")
            except Exception as e:
                logger.error(f"❌ Worker {self.worker_id}: Erreur test session app.mytoolsplan.com: {e}")
            
            return None
        
        # Test du scraping JavaScript
        clean_domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '')
        
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
        
        logger.info(f"🔍 Worker {self.worker_id}: Résultat JavaScript: {conversion_data}")
        
        return conversion_data

    async def test_domain(self, domain_info):
        """Test complet pour un domaine"""
        domain = domain_info["domain"]
        folder_id = domain_info["fid"]
        
        logger.info(f"🎯 Worker {self.worker_id}: TEST COMPLET pour {domain} (FID: {folder_id})")
        
        try:
            # Authentification et synchronisation
            await self.authenticate_and_sync()
            
            # Test du scraping avec le folder_id fourni
            result = await self.test_purchase_conversion_scraping(domain, folder_id)
            
            logger.info(f"✅ Worker {self.worker_id}: Test terminé pour {domain}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: Erreur test {domain}: {e}")
            return None

async def main():
    """Fonction principale de test"""
    logger.info("🚀 DÉMARRAGE TEST PURCHASE_CONVERSION")
    
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
                logger.info(f"✅ Résultat pour {domain_info['domain']}: {result}")
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
