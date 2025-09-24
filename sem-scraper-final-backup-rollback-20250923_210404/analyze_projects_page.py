#!/usr/bin/env python3
"""
Script pour analyser la page des projets
"""

import asyncio
import logging
import sys
import os
sys.path.append('/home/ubuntu/sem-scraper-final')
import config

from playwright.async_api import async_playwright

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectsPageAnalyzer:
    def __init__(self):
        self.page = None
        self.context = None
        self.browser = None
    
    async def authenticate_first(self):
        """S'authentifie d'abord sur MyToolsPlan"""
        try:
            logger.info("🔐 Authentification sur MyToolsPlan...")
            
            # Aller directement sur la page de login
            await self.page.goto("https://app.mytoolsplan.com/login", wait_until='domcontentloaded', timeout=30000)
            
            await self.page.wait_for_selector('input[name="amember_login"]', timeout=15000)
            await self.page.wait_for_selector('input[name="amember_pass"]', timeout=15000)
            
            await self.page.fill('input[name="amember_login"]', config.config.mytoolsplan_username)
            await self.page.fill('input[name="amember_pass"]', config.config.mytoolsplan_password)
            
            await self.page.click('input[type="submit"]')
            
            await self.page.wait_for_url("**/member", timeout=15000)
            logger.info("✅ Authentification réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'authentification: {e}")
            return False

    async def analyze_projects_page(self):
        """Analyse la page des projets"""
        
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            try:
                logger.info("🚀 Analyse de la page des projets")
                
                # Étape 1: S'authentifier
                auth_result = await self.authenticate_first()
                
                if auth_result:
                    # Attendre que la page se charge
                    await asyncio.sleep(5)
                    
                    # Vérifier le titre de la page
                    page_title = await self.page.title()
                    logger.info(f"📄 Titre de la page: {page_title}")
                    
                    # Vérifier l'URL actuelle
                    current_url = self.page.url
                    logger.info(f"🌐 URL actuelle: {current_url}")
                    
                    # Analyser les liens sur la page
                    logger.info("🔍 Analyse des liens sur la page")
                    
                    links = await self.page.query_selector_all('a')
                    logger.info(f"📊 {len(links)} liens trouvés")
                    
                    for i, link in enumerate(links[:20]):  # Limiter à 20 liens
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href and text:
                                logger.info(f"   Lien {i+1}: '{text}' -> {href}")
                        except:
                            pass
                    
                    # Analyser les éléments avec data-testid
                    logger.info("🔍 Analyse des éléments data-testid")
                    
                    data_testid_elements = await self.page.query_selector_all('[data-testid]')
                    logger.info(f"📊 {len(data_testid_elements)} éléments avec data-testid trouvés")
                    
                    for i, element in enumerate(data_testid_elements[:10]):  # Limiter à 10 éléments
                        try:
                            testid = await element.get_attribute('data-testid')
                            text = await element.inner_text()
                            if testid and text:
                                logger.info(f"   data-testid {i+1}: '{testid}' -> '{text}'")
                        except:
                            pass
                    
                    # Analyser les éléments avec data-ui-name
                    logger.info("🔍 Analyse des éléments data-ui-name")
                    
                    data_ui_elements = await self.page.query_selector_all('[data-ui-name]')
                    logger.info(f"📊 {len(data_ui_elements)} éléments avec data-ui-name trouvés")
                    
                    for i, element in enumerate(data_ui_elements[:10]):  # Limiter à 10 éléments
                        try:
                            ui_name = await element.get_attribute('data-ui-name')
                            text = await element.inner_text()
                            if ui_name and text:
                                logger.info(f"   data-ui-name {i+1}: '{ui_name}' -> '{text}'")
                        except:
                            pass
                    
                    # Chercher des éléments contenant "archiesfootwear"
                    logger.info("🔍 Recherche d'éléments contenant 'archiesfootwear'")
                    
                    page_content = await self.page.content()
                    if "archiesfootwear" in page_content.lower():
                        logger.info("✅ 'archiesfootwear' trouvé dans le contenu de la page")
                        
                        # Chercher des éléments avec ce texte
                        archies_elements = await self.page.query_selector_all('*:has-text("archiesfootwear")')
                        logger.info(f"📊 {len(archies_elements)} éléments contenant 'archiesfootwear' trouvés")
                        
                        for i, element in enumerate(archies_elements[:5]):  # Limiter à 5 éléments
                            try:
                                tag_name = await element.evaluate('el => el.tagName')
                                text = await element.inner_text()
                                logger.info(f"   Élément {i+1}: {tag_name} -> '{text}'")
                            except:
                                pass
                    else:
                        logger.info("❌ 'archiesfootwear' NON trouvé dans le contenu de la page")
                    
                    # Chercher des éléments contenant "1256655" (ID du projet)
                    logger.info("🔍 Recherche d'éléments contenant '1256655'")
                    
                    if "1256655" in page_content:
                        logger.info("✅ '1256655' trouvé dans le contenu de la page")
                    else:
                        logger.info("❌ '1256655' NON trouvé dans le contenu de la page")
                    
                else:
                    logger.error("❌ Échec de l'authentification")
                
                # Prendre une capture d'écran pour debug
                await self.page.screenshot(path="/home/ubuntu/sem-scraper-final/debug_projects_analysis.png")
                logger.info("📸 Capture d'écran sauvegardée: debug_projects_analysis.png")
                
            except Exception as e:
                logger.error(f"❌ Erreur générale: {str(e)}")
            
            finally:
                await self.browser.close()

async def main():
    analyzer = ProjectsPageAnalyzer()
    await analyzer.analyze_projects_page()

if __name__ == "__main__":
    asyncio.run(main())
