#!/usr/bin/env python3
"""
Module API organic.Summary pour le scraper de production
Basé sur le test qui fonctionnait parfaitement
"""

import asyncio
import logging
from datetime import datetime, timezone
from api_client import APIClient
from credentials_manager import CredentialsManager
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class OrganicSummaryAPI:
    """API organic.Summary qui fonctionne avec le scraper de production"""
    
    def __init__(self, page):
        """Initialisation avec la page Playwright du scraper"""
        self.page = page
        self.credentials_manager = CredentialsManager()
        self.api_client = APIClient(self.credentials_manager)
    
    def calculate_target_date(self) -> str:
        """
        Calcule la date cible : mois en cours - 2 mois, 15 du mois
        Exemple: septembre 2025 -> juillet 2025 -> 20250715
        """
        now = datetime.now(timezone.utc)
        # Mois en cours - 2 mois
        target_month = now.month - 2
        target_year = now.year
        
        # Gérer le cas où on passe en année précédente
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # Format: YYYYMMDD avec le 15 du mois
        target_date = f"{target_year:04d}{target_month:02d}15"
        
        logger.info(f"📅 Date calculée: {target_date} (mois en cours - 2 mois, 15 du mois)")
        return target_date
    
    async def get_organic_traffic(self, domain: str) -> Optional[str]:
        """
        Récupère l'organic traffic via l'API organic.Summary
        Utilise exactement la même logique que le test qui fonctionnait
        """
        try:
            logger.info(f"🎯 API organic.Summary pour {domain}")
            
            # Utiliser la session existante du scraper de production
            logger.info("🔄 Utilisation de la session existante du scraper de production")
            
            target_date = self.calculate_target_date()
            
            # Appel API identique au test qui fonctionnait
            result = await self.page.evaluate("""
                async (data) => {
                    try {
                        const response = await fetch('/dpa/rpc', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                "id": Math.floor(Math.random() * 10000),
                                "jsonrpc": "2.0",
                                "method": "organic.Summary",
                                "params": {
                                    "request_id": crypto.randomUUID(),
                                    "report": "domain.overview",
                                    "args": {
                                        "searchItem": data.domain,
                                        "searchType": "domain", 
                                        "database": "us",
                                        "dateType": "monthly",
                                        "date": data.target_date,
                                        "dateFormat": "date"
                                    },
                                    "userId": data.credentials.userId,
                                    "apiKey": data.credentials.apiKey
                                }
                            })
                        });
                        
                        const responseText = await response.text();
                        
                        if (!response.ok) {
                            return {
                                error: `HTTP ${response.status}: ${responseText}`,
                                status: response.status
                            };
                        }
                        
                        return JSON.parse(responseText);
                        
                    } catch (error) {
                        return {
                            error: error.message,
                            type: 'fetch_error'
                        };
                    }
                }
            """, {
                'domain': domain,
                'target_date': target_date,
                'credentials': self.credentials
            })
            
            if result.get('error'):
                logger.error(f"❌ Erreur API organic.Summary: {result['error']}")
                return None
            
            if result.get('result') and len(result['result']) > 0:
                # Chercher l'entrée USA
                us_entry = None
                for entry in result['result']:
                    if entry.get('database') == 'us':
                        us_entry = entry
                        break
                
                if not us_entry:
                    us_entry = result['result'][0]
                
                organic = us_entry.get('organicTraffic') or us_entry.get('organic_traffic') or 0
                
                # Formater le nombre
                if organic >= 1000000:
                    formatted = f"{organic/1000000:.1f}M"
                elif organic >= 1000:
                    formatted = f"{organic/1000:.1f}K"
                else:
                    formatted = str(organic)
                
                logger.info(f"✅ API organic.Summary: {formatted}")
                return formatted
            
            logger.warning("⚠️ Aucune donnée organic trouvée via API")
            return None
            
        except Exception as error:
            logger.error(f"❌ Erreur API organic.Summary: {error}")
            return None
    
    async def verify_credentials(self) -> bool:
        """
        Vérifie que les credentials sont toujours valides
        """
        try:
            logger.info("🔍 Vérification des credentials...")
            
            # Test avec google.com
            result = await self.get_organic_traffic('google.com')
            
            if result:
                logger.info("✅ Credentials valides")
                return True
            else:
                logger.warning("⚠️ Credentials potentiellement expirés")
                return False
                
        except Exception as error:
            logger.error(f"❌ Erreur vérification credentials: {error}")
            return False
