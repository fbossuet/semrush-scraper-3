#!/usr/bin/env python3
"""
Script pour analyser la page Traffic Analytics et identifier les nouveaux sélecteurs
"""

import asyncio
import logging
from playwright.async_api import async_playwright
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrafficAnalyticsAnalyzer:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def setup(self):
        """Configuration du navigateur"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        
    async def login(self):
        """Connexion à l'application"""
        try:
            logger.info("🔐 Connexion à l'application...")
            await self.page.goto("https://app.mytoolsplan.com/login", timeout=30000)
            await asyncio.sleep(2)
            
            # Remplir les identifiants
            await self.page.fill('input[name="email"]', 'infusion@trendtrack.io')
            await self.page.fill('input[name="password"]', 'L1dwich!hafni')
            await self.page.click('button[type="submit"]')
            
            # Attendre la redirection
            await asyncio.sleep(5)
            
            current_url = self.page.url
            logger.info(f"📍 URL après login: {current_url}")
            
            if "member" in current_url:
                logger.info("✅ Login réussi")
                return True
            else:
                logger.error("❌ Login échoué")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur login: {e}")
            return False
    
    async def navigate_to_traffic_analytics(self, domain="https://us.ohpolly.com"):
        """Navigation vers Traffic Analytics"""
        try:
            logger.info("🌐 Navigation vers Traffic Analytics...")
            
            # Aller sur Traffic Analytics
            await self.page.goto("https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/", timeout=30000)
            await asyncio.sleep(3)
            
            # Chercher le projet existant
            domain_clean = domain.replace("https://", "").replace("http://", "")
            
            # Appel API pour récupérer les dossiers
            response = await self.page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/apis/v4-raw/folders/api/v0/folders/selector-list?limit=2000&offset=0', {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            return data;
                        } else {
                            return null;
                        }
                    } catch (error) {
                        return null;
                    }
                }
            """)
            
            if response and 'data' in response:
                folders = response['data']
                logger.info(f"📊 {len(folders)} dossiers trouvés")
                
                # Chercher le domaine
                target_fid = None
                for folder in folders:
                    if domain_clean in folder.get('name', ''):
                        target_fid = folder.get('id')
                        logger.info(f"🎯 Domaine trouvé avec FID: {target_fid}")
                        break
                
                if target_fid:
                    # Naviguer vers le FID
                    await self.page.goto(f"https://sam.mytoolsplan.xyz/analytics/traffic/traffic-overview/?fid={target_fid}", timeout=30000)
                    await asyncio.sleep(5)
                    logger.info(f"✅ Navigation vers FID: {target_fid}")
                    return True
                    
            logger.warning("⚠️ Aucun dossier trouvé")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur navigation: {e}")
            return False
    
    async def analyze_page_structure(self):
        """Analyse de la structure de la page"""
        logger.info("🔍 Analyse de la structure de la page...")
        
        # Attendre que la page se charge
        await asyncio.sleep(5)
        
        # Récupérer le HTML de la page
        page_content = await self.page.content()
        
        # Sauvegarder le HTML pour analyse
        with open('traffic_analytics_detailed.html', 'w', encoding='utf-8') as f:
            f.write(page_content)
        logger.info("💾 HTML détaillé sauvegardé dans traffic_analytics_detailed.html")
        
        # Analyser les patterns
        patterns_to_analyze = [
            'visits',
            'conversion',
            'purchase',
            'traffic',
            'analytics',
            'summary',
            'cell',
            'value',
            'text',
            'number',
            'metric',
            'stat',
            'data'
        ]
        
        logger.info("🔍 ANALYSE DES PATTERNS:")
        for pattern in patterns_to_analyze:
            count = page_content.lower().count(pattern.lower())
            if count > 0:
                logger.info(f"   ✅ '{pattern}': {count} occurrences")
            else:
                logger.info(f"   ❌ '{pattern}': 0 occurrence")
        
        # Chercher les sélecteurs potentiels
        logger.info("\n🔍 RECHERCHE DE SÉLECTEURS POTENTIELS:")
        
        # Sélecteurs basés sur les classes
        class_selectors = [
            '.visits',
            '.conversion',
            '.purchase',
            '.traffic',
            '.analytics',
            '.summary',
            '.cell',
            '.value',
            '.text',
            '.number',
            '.metric',
            '.stat',
            '.data',
            '[class*="visits"]',
            '[class*="conversion"]',
            '[class*="purchase"]',
            '[class*="traffic"]',
            '[class*="analytics"]',
            '[class*="summary"]',
            '[class*="cell"]',
            '[class*="value"]',
            '[class*="text"]',
            '[class*="number"]',
            '[class*="metric"]',
            '[class*="stat"]',
            '[class*="data"]'
        ]
        
        for selector in class_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    logger.info(f"   ✅ {selector}: {len(elements)} éléments trouvés")
                    for i, element in enumerate(elements[:3]):  # Limiter à 3
                        try:
                            text = await element.inner_text()
                            if text.strip():
                                logger.info(f"      📝 Élément {i+1}: '{text.strip()}'")
                        except:
                            pass
                else:
                    logger.info(f"   ❌ {selector}: 0 élément")
            except Exception as e:
                logger.info(f"   ❌ {selector}: Erreur - {e}")
        
        # Chercher les éléments avec des attributs data-*
        logger.info("\n🔍 RECHERCHE D'ATTRIBUTS DATA-*:")
        data_attributes = await self.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('[data-*]');
                const attributes = new Set();
                elements.forEach(el => {
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-')) {
                            attributes.add(attr.name);
                        }
                    }
                });
                return Array.from(attributes);
            }
        """)
        
        for attr in data_attributes:
            logger.info(f"   📋 Attribut trouvé: {attr}")
        
        # Chercher les éléments avec des IDs
        logger.info("\n🔍 RECHERCHE D'IDS:")
        ids = await self.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('[id]');
                return Array.from(elements).map(el => el.id).slice(0, 20);
            }
        """)
        
        for id_name in ids:
            logger.info(f"   📋 ID trouvé: {id_name}")
        
        # Chercher les éléments avec des classes contenant des mots-clés
        logger.info("\n🔍 RECHERCHE DE CLASSES AVEC MOTS-CLÉS:")
        classes = await self.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const classes = new Set();
                elements.forEach(el => {
                    if (el.className) {
                        el.className.split(' ').forEach(cls => {
                            if (cls && (cls.includes('visit') || cls.includes('conversion') || 
                                       cls.includes('purchase') || cls.includes('traffic') || 
                                       cls.includes('analytics') || cls.includes('summary') || 
                                       cls.includes('cell') || cls.includes('value') || 
                                       cls.includes('text') || cls.includes('number') || 
                                       cls.includes('metric') || cls.includes('stat') || 
                                       cls.includes('data'))) {
                                classes.add(cls);
                            }
                        });
                    }
                });
                return Array.from(classes);
            }
        """)
        
        for class_name in classes:
            logger.info(f"   📋 Classe trouvée: {class_name}")
        
        return True
        
    async def close(self):
        """Fermeture du navigateur"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    """Fonction principale"""
    analyzer = TrafficAnalyticsAnalyzer()
    
    try:
        await analyzer.setup()
        
        # Login
        if not await analyzer.login():
            logger.error("❌ Impossible de se connecter")
            return
        
        # Navigation
        if not await analyzer.navigate_to_traffic_analytics():
            logger.error("❌ Impossible de naviguer vers Traffic Analytics")
            return
        
        # Analyse
        await analyzer.analyze_page_structure()
        
        logger.info("✅ Analyse terminée")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main())
