#!/usr/bin/env python3
"""
Scraper traditionnel pour les métriques Visits et Purchase Conversion
Inspiré du code SemrushLegoScraper fourni par l'utilisateur
"""

import asyncio
from playwright.async_api import async_playwright
import re
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TraditionalVisitsConversionScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.page = None
        self.browser = None
        self.playwright = None
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ]
        )
        self.page = await self.browser.new_page()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def login_semrush(self, email: str, password: str):
        """Se connecter à Semrush"""
        logger.info("🔑 Connexion à Semrush...")
        
        try:
            await self.page.goto("https://sam.mytoolsplan.xyz/login/")
            
            # Remplir le formulaire de login
            await self.page.fill('input[name="email"]', email)
            await self.page.fill('input[name="password"]', password)
            
            # Cliquer sur le bouton de connexion
            await self.page.click('button[type="submit"]')
            
            # Attendre la redirection
            await self.page.wait_for_url("**/dashboard**", timeout=30000)
            logger.info("✅ Connecté avec succès!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return False
        
    async def scrape_visits_conversion_metrics(self, domain: str) -> Dict:
        """Scraper les métriques Visits et Purchase Conversion pour un domaine"""
        logger.info(f"🎯 Scraping des métriques Visits/Conversion pour {domain}...")
        
        try:
            # Aller sur la page Traffic Analytics
            url = f"https://sam.mytoolsplan.xyz/analytics/traffic/overview/?q={domain}"
            await self.page.goto(url, wait_until="networkidle")
            
            # Attendre le chargement des données
            logger.info("⏳ Attente du chargement des données...")
            await asyncio.sleep(5)
            
            # Attendre que le tableau soit visible
            try:
                await self.page.wait_for_selector('[role="grid"], table, [data-testid*="table"]', timeout=20000)
            except:
                logger.warning("⚠️ Tableau non trouvé, tentative avec sélecteurs alternatifs...")
            
            # Exécuter le script JavaScript pour extraire les données
            metrics_data = await self.page.evaluate(f"""
                () => {{
                    const result = {{
                        domain: '{domain}',
                        visits: null,
                        purchaseConversion: null,
                        allData: [],
                        found: false,
                        timestamp: new Date().toISOString()
                    }};
                    
                    console.log('🔍 Recherche données pour {domain}...');
                    
                    // Fonction pour parser les valeurs de trafic
                    function parseTrafficValue(text) {{
                        const cleanText = text.replace(/[↑↓\\s]/g, '');
                        const multipliers = {{ 'K': 1000, 'M': 1000000, 'B': 1000000000 }};
                        
                        const match = cleanText.match(/^(\\d+\\.?\\d*)([KMB]?)$/);
                        if (match) {{
                            const number = parseFloat(match[1]);
                            const multiplier = multipliers[match[2]] || 1;
                            return Math.round(number * multiplier);
                        }}
                        return 0;
                    }}
                    
                    // 1. Chercher dans toutes les lignes de tableau
                    const allRows = document.querySelectorAll('tr, [role="row"], .table-row');
                    
                    for (const row of allRows) {{
                        const rowText = row.textContent || '';
                        
                        if (rowText.toLowerCase().includes('{domain.lower()}')) {{
                            console.log('🎯 Ligne {domain} trouvée!');
                            result.found = true;
                            result.domain = '{domain}';
                            
                            // Extraire toutes les cellules
                            const cells = row.querySelectorAll('td, [role="gridcell"], [role="cell"], .cell');
                            const cellTexts = Array.from(cells).map(cell => cell.textContent.trim());
                            
                            result.allData = cellTexts;
                            console.log('📊 Cellules trouvées:', cellTexts);
                            
                            // Parser chaque cellule
                            cellTexts.forEach((cellText, index) => {{
                                // Visits (grands nombres avec M/B)
                                if (cellText.match(/^\\d+\\.?\\d*[MB]/)) {{
                                    const number = parseTrafficValue(cellText);
                                    if (number > 10000000 && !result.visits) {{ // > 10M
                                        result.visits = number;
                                    }}
                                }}
                                
                                // Pourcentages de conversion (petits %)
                                if (cellText.match(/^\\d+\\.\\d+%/) && cellText.includes('.')) {{
                                    const rate = parseFloat(cellText.replace('%', '').replace(/[↑↓]/, ''));
                                    if (rate < 10 && !result.purchaseConversion) {{
                                        result.purchaseConversion = rate;
                                    }}
                                }}
                            }});
                            
                            break;
                        }}
                    }}
                    
                    // 2. Si pas trouvé, chercher dans les métriques générales
                    if (!result.found) {{
                        const summaryCards = document.querySelectorAll('[data-testid*="metric"], [data-testid*="summary"], .metric-card');
                        
                        summaryCards.forEach(card => {{
                            const text = card.textContent;
                            if (text.toLowerCase().includes('{domain.lower()}')) {{
                                result.found = true;
                                result.allData.push(text);
                            }}
                        }});
                    }}
                    
                    return result;
                }}
            """)
            
            return metrics_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping de {domain}: {e}")
            return {
                'domain': domain,
                'visits': None,
                'purchaseConversion': None,
                'allData': [],
                'found': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def parse_traffic_value(self, text: str) -> int:
        """Parse les valeurs de trafic (45.6M -> 45600000)"""
        if not text:
            return 0
            
        clean_text = re.sub(r'[↑↓\s]', '', text)
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        match = re.match(r'^(\d+\.?\d*)([KMB]?)$', clean_text)
        if match:
            number = float(match.group(1))
            multiplier = multipliers.get(match.group(2), 1)
            return int(number * multiplier)
        return 0

    async def scrape_multiple_domains(self, domains: list) -> Dict:
        """Scraper les métriques pour plusieurs domaines"""
        results = {}
        
        for domain in domains:
            logger.info(f"🔄 Traitement de {domain}...")
            metrics = await self.scrape_visits_conversion_metrics(domain)
            results[domain] = metrics
            
            # Pause entre les requêtes pour éviter la détection
            await asyncio.sleep(2)
        
        return results

    async def take_screenshot(self, filename: str = "traffic_analytics.png"):
        """Prendre une capture d'écran"""
        try:
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"📸 Capture d'écran sauvée: {filename}")
        except Exception as e:
            logger.error(f"❌ Erreur capture d'écran: {e}")

# 🎯 FONCTION PRINCIPALE DE TEST
async def test_scraper():
    """Test du scraper avec quelques domaines"""
    
    # Domaines de test
    test_domains = [
        "spanx.com",
        "cakesbody.com", 
        "lego.com",
        "nike.com"
    ]
    
    async with TraditionalVisitsConversionScraper(headless=True) as scraper:
        # Optionnel: Se connecter (décommentez et ajoutez vos credentials)
        # await scraper.login_semrush("your_email@example.com", "your_password")
        
        logger.info("🚀 Début du test du scraper traditionnel...")
        
        # Scraper les données pour tous les domaines
        results = await scraper.scrape_multiple_domains(test_domains)
        
        # Afficher les résultats
        logger.info("\n🎉 === RÉSULTATS DU SCRAPING ===")
        
        for domain, data in results.items():
            logger.info(f"\n🌐 Domaine: {domain}")
            logger.info(f"📊 Visits: {data['visits']:,}" if data['visits'] else "📊 Visits: N/A")
            logger.info(f"💰 Purchase Conversion: {data['purchaseConversion']}%" if data['purchaseConversion'] else "💰 Purchase Conversion: N/A")
            logger.info(f"✅ Trouvé: {'Oui' if data['found'] else 'Non'}")
            
            if data.get('error'):
                logger.error(f"❌ Erreur: {data['error']}")
        
        # Capture d'écran
        await scraper.take_screenshot("traffic_analytics_test.png")
        
        # Sauvegarder en JSON
        with open('visits_conversion_metrics.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("💾 Données sauvées dans visits_conversion_metrics.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(test_scraper())
