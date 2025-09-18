#!/usr/bin/env python3
"""
Analyse de la structure HTML de Traffic Analytics
Pour comprendre où sont stockées les métriques Visits et Purchase Conversion
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from production_scraper_current import ProductionScraper
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analyze_traffic_analytics_html.log')
    ]
)
logger = logging.getLogger(__name__)

async def analyze_traffic_analytics_html():
    """Analyse complète de la structure HTML Traffic Analytics"""
    
    scraper = None
    
    try:
        logger.info("🔍 ANALYSE STRUCTURE HTML TRAFFIC ANALYTICS")
        logger.info("=" * 60)
        
        # Initialiser le scraper
        scraper = ProductionScraper()
        await scraper.setup_browser()
        
        # Authentification
        logger.info("🔐 Authentification...")
        await scraper.check_and_authenticate()
        
        # Test avec spanx.com
        domain = "https://spanx.com"
        domain_clean = domain.replace("https://", "").replace("http://", "")
        
        logger.info(f"📊 Analyse pour: {domain}")
        
        # Étape 1: Créer le dossier Traffic Analytics
        logger.info("\n📁 ÉTAPE 1: Création du dossier Traffic Analytics")
        folder_created = await scraper.create_traffic_folder(domain)
        
        if not folder_created:
            logger.error("❌ Impossible de créer le dossier Traffic Analytics")
            return
        
        logger.info("✅ Dossier Traffic Analytics créé/sélectionné")
        
        # Étape 2: Analyser la structure HTML de la page
        logger.info("\n📊 ÉTAPE 2: Analyse de la structure HTML")
        
        current_url = scraper.page.url
        page_title = await scraper.page.title()
        logger.info(f"📍 URL actuelle: {current_url}")
        logger.info(f"📄 Titre de la page: {page_title}")
        
        # Attendre que la page se charge complètement
        await asyncio.sleep(5)
        
        # Analyser les éléments avec data-testid
        logger.info("\n🔍 Analyse des éléments data-testid:")
        testid_elements = await scraper.page.query_selector_all('[data-testid]')
        logger.info(f"📊 {len(testid_elements)} éléments data-testid trouvés")
        
        testid_values = set()
        for element in testid_elements:
            try:
                testid = await element.get_attribute('data-testid')
                if testid:
                    testid_values.add(testid)
            except:
                pass
        
        logger.info(f"📋 Valeurs data-testid uniques: {sorted(testid_values)}")
        
        # Analyser spécifiquement les métriques Visits et Conversion
        logger.info("\n🔍 Analyse spécifique des métriques:")
        
        # Chercher les éléments contenant "visits"
        visits_elements = await scraper.page.query_selector_all('[data-testid*="visit"], [data-testid*="visits"], [class*="visit"], [class*="visits"]')
        logger.info(f"📊 {len(visits_elements)} éléments liés aux visits trouvés")
        
        for i, element in enumerate(visits_elements[:5]):  # Limiter à 5
            try:
                testid = await element.get_attribute('data-testid')
                class_name = await element.get_attribute('class')
                text_content = await element.inner_text()
                logger.info(f"   {i+1}. testid='{testid}' class='{class_name}' text='{text_content[:50]}...'")
            except:
                pass
        
        # Chercher les éléments contenant "conversion"
        conversion_elements = await scraper.page.query_selector_all('[data-testid*="conversion"], [class*="conversion"]')
        logger.info(f"📊 {len(conversion_elements)} éléments liés à la conversion trouvés")
        
        for i, element in enumerate(conversion_elements[:5]):  # Limiter à 5
            try:
                testid = await element.get_attribute('data-testid')
                class_name = await element.get_attribute('class')
                text_content = await element.inner_text()
                logger.info(f"   {i+1}. testid='{testid}' class='{class_name}' text='{text_content[:50]}...'")
            except:
                pass
        
        # Analyser les tableaux HTML
        logger.info("\n🔍 Analyse des tableaux HTML:")
        tables = await scraper.page.query_selector_all('table, [role="table"], [role="grid"]')
        logger.info(f"📊 {len(tables)} tableaux trouvés")
        
        for i, table in enumerate(tables[:3]):  # Limiter à 3
            try:
                rows = await table.query_selector_all('tr, [role="row"]')
                logger.info(f"   Tableau {i+1}: {len(rows)} lignes")
                
                # Analyser les premières lignes
                for j, row in enumerate(rows[:3]):
                    cells = await row.query_selector_all('td, th, [role="cell"], [role="gridcell"]')
                    cell_texts = []
                    for cell in cells:
                        try:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                        except:
                            pass
                    logger.info(f"     Ligne {j+1}: {cell_texts}")
            except:
                pass
        
        # Analyser les cartes de résumé (summary cards)
        logger.info("\n🔍 Analyse des cartes de résumé:")
        summary_cards = await scraper.page.query_selector_all('[class*="summary"], [class*="card"], [class*="metric"]')
        logger.info(f"📊 {len(summary_cards)} cartes de résumé trouvées")
        
        for i, card in enumerate(summary_cards[:10]):  # Limiter à 10
            try:
                class_name = await card.get_attribute('class')
                text_content = await element.inner_text()
                if any(keyword in text_content.lower() for keyword in ['visit', 'conversion', 'traffic', 'metric']):
                    logger.info(f"   {i+1}. class='{class_name}' text='{text_content[:100]}...'")
            except:
                pass
        
        # Analyser le contenu JavaScript/React
        logger.info("\n🔍 Analyse du contenu JavaScript/React:")
        
        # Chercher les données dans window ou des variables globales
        js_data = await scraper.page.evaluate("""
            () => {
                const result = {
                    windowData: {},
                    reactData: {},
                    metrics: []
                };
                
                // Chercher dans window
                if (window.__INITIAL_STATE__) {
                    result.windowData.initialState = window.__INITIAL_STATE__;
                }
                if (window.__NEXT_DATA__) {
                    result.windowData.nextData = window.__NEXT_DATA__;
                }
                
                // Chercher des éléments avec des données React
                const elements = document.querySelectorAll('[data-reactroot], [data-reactid]');
                result.reactData.elementsCount = elements.length;
                
                // Chercher des métriques dans le texte
                const allText = document.body.innerText;
                const metrics = [];
                
                // Patterns pour les métriques
                const patterns = [
                    /(\d+(?:\.\d+)?[KMB]?)\s*(?:visits?|traffic)/gi,
                    /(\d+(?:\.\d+)?%?)\s*(?:conversion|rate)/gi,
                    /(\d+(?:\.\d+)?[KMB]?)\s*(?:organic|paid)/gi
                ];
                
                patterns.forEach(pattern => {
                    const matches = allText.match(pattern);
                    if (matches) {
                        metrics.push(...matches);
                    }
                });
                
                result.metrics = [...new Set(metrics)];
                
                return result;
            }
        """)
        
        logger.info(f"📋 Données JavaScript trouvées:")
        logger.info(f"   • Éléments React: {js_data.get('reactData', {}).get('elementsCount', 0)}")
        logger.info(f"   • Métriques détectées: {js_data.get('metrics', [])}")
        
        # Sauvegarder le HTML complet pour analyse
        logger.info("\n💾 Sauvegarde du HTML pour analyse...")
        html_content = await scraper.page.content()
        
        with open(f'traffic_analytics_html_{domain_clean.replace(".", "_")}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ HTML sauvegardé dans: traffic_analytics_html_{domain_clean.replace('.', '_')}.html")
        
        # Résumé de l'analyse
        logger.info("\n🎯 RÉSUMÉ DE L'ANALYSE")
        logger.info("=" * 60)
        logger.info(f"📊 Éléments data-testid: {len(testid_elements)}")
        logger.info(f"📊 Tableaux HTML: {len(tables)}")
        logger.info(f"📊 Cartes de résumé: {len(summary_cards)}")
        logger.info(f"📊 Métriques JavaScript: {len(js_data.get('metrics', []))}")
        
        # Recommandations
        logger.info("\n💡 RECOMMANDATIONS:")
        if len(testid_elements) > 0:
            logger.info("✅ Utiliser les sélecteurs data-testid pour le scraping")
        if len(tables) > 0:
            logger.info("✅ Analyser les tableaux HTML pour les métriques")
        if len(js_data.get('metrics', [])) > 0:
            logger.info("✅ Les métriques sont présentes dans le contenu JavaScript")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique de l'analyse: {e}")
        
    finally:
        # Nettoyage
        if scraper and scraper.browser:
            logger.info("🧹 Nettoyage...")
            await scraper.browser.close()
        
        logger.info("✅ Analyse terminée")

if __name__ == "__main__":
    asyncio.run(analyze_traffic_analytics_html())
