#!/usr/bin/env python3
"""
Extracteur Python pour les variations de Live Ads (7d et 30d)
Utilisé comme pont depuis les scrapers pour récupérer les métriques de progression
"""

import sys
import json
import asyncio
import logging
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveAdsProgressionExtractor:
    """Extracteur pour les variations de Live Ads"""
    
    def __init__(self):
        self.timeout = 30000  # 30 secondes
    
    def parse_percent_text(self, txt):
        """Parse un pourcentage depuis une chaîne"""
        if not txt:
            return None
        try:
            # Extraire les chiffres et le signe
            cleaned = re.sub(r'[^\d.-]', '', str(txt))
            if not cleaned:
                return None
            return float(cleaned)
        except:
            return None
    
    def signed_by_class(self, raw, className):
        """Détermine le signe basé sur la classe CSS"""
        if raw is None:
            return None
        # Si la classe contient "bg-red-300", c'est négatif
        negative = "bg-red-300" in (className or "")
        return -abs(raw) if negative else abs(raw)
    
    def find_badge_after_label(self, root, label):
        """Trouve le badge qui suit un label exact"""
        try:
            # Chercher tous les éléments
            all_elements = root.query_selector_all("*")
            
            # Trouver le label exact
            label_node = None
            for element in all_elements:
                if element.text_content().strip() == label:
                    label_node = element
                    break
            
            if not label_node:
                return None
            
            # Chercher le frère suivant avec un %
            current = label_node
            while current:
                current = current.evaluate_handle("el => el.nextElementSibling")
                if current:
                    text = current.text_content()
                    if "%" in text:
                        return current
            
            # Fallback: chercher dans le parent
            parent = label_node.evaluate_handle("el => el.parentElement")
            if parent:
                children = parent.query_selector_all("*")
                for child in children:
                    text = child.text_content()
                    if "%" in text:
                        return child
            
            return None
        except:
            return None
    
    async def extract_live_ads_progression(self, shop_url):
        """
        Extrait les variations de Live Ads (7d et 30d) d'une boutique
        """
        logger.info(f"📊 Extraction variations Live Ads pour: {shop_url}")
        
        try:
            async with async_playwright() as p:
                # Lancer le navigateur
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Aller sur la page de la boutique
                await page.goto(shop_url, timeout=self.timeout)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Initialiser les résultats
                progression_data = {
                    "live_ads_7d": None,
                    "live_ads_30d": None,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Utiliser page.evaluate pour exécuter le JavaScript d'extraction
                try:
                    extraction_result = await page.evaluate("""
                        () => {
                            function parsePercentText(txt) {
                                if (!txt) return null;
                                const n = parseInt(String(txt).replace(/[^\\d-]/g, ""), 10);
                                return Number.isNaN(n) ? null : n;
                            }
                            
                            function signedByClass(raw, className) {
                                if (raw == null) return null;
                                const negative = className?.includes("bg-red-300");
                                return negative ? -Math.abs(raw) : Math.abs(raw);
                            }
                            
                            function findBadgeAfterLabel(root, label) {
                                const all = Array.from(root.querySelectorAll("*"));
                                const labelNode = all.find(n => n.childNodes.length === 1 && n.textContent.trim() === label);
                                if (!labelNode) return null;
                                
                                // 1) Essaye les frères directs à droite
                                for (let sib = labelNode.nextElementSibling; sib; sib = sib.nextElementSibling) {
                                    if (/%/.test(sib.textContent)) return sib;
                                }
                                // 2) Fallback: dans le même parent, l'élément avec un %
                                const parent = labelNode.parentElement || root;
                                const candidate = Array.from(parent.children).find(el => /%/.test(el.textContent));
                                return candidate || null;
                            }
                            
                            const badge7 = findBadgeAfterLabel(document, "7d");
                            const badge30 = findBadgeAfterLabel(document, "30d");
                            
                            const v7 = parsePercentText(badge7?.textContent);
                            const v30 = parsePercentText(badge30?.textContent);
                            
                            const live_ads_7d = signedByClass(v7, badge7?.className || "");
                            const live_ads_30d = signedByClass(v30, badge30?.className || "");
                            
                            return { live_ads_7d, live_ads_30d };
                        }
                    """)
                    
                    if extraction_result:
                        progression_data["live_ads_7d"] = extraction_result.get("live_ads_7d")
                        progression_data["live_ads_30d"] = extraction_result.get("live_ads_30d")
                        logger.info(f"✅ Variations Live Ads extraites: 7d={progression_data['live_ads_7d']}%, 30d={progression_data['live_ads_30d']}%")
                    else:
                        logger.warning("⚠️ Aucune donnée de progression Live Ads trouvée")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur extraction JavaScript: {e}")
                
                await browser.close()
                
                logger.info(f"✅ Données de progression extraites: {json.dumps(progression_data, indent=2)}")
                return progression_data
                
        except Exception as e:
            logger.error(f"❌ Erreur extraction progression Live Ads: {e}")
            return {
                "live_ads_7d": None,
                "live_ads_30d": None,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

async def main():
    """Fonction principale pour tester l'extracteur"""
    if len(sys.argv) < 2:
        print("Usage: python3 live_ads_progression_extractor.py <shop_url>")
        sys.exit(1)
    
    shop_url = sys.argv[1]
    extractor = LiveAdsProgressionExtractor()
    
    try:
        result = await extractor.extract_live_ads_progression(shop_url)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())