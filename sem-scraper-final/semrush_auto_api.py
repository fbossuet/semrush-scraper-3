#!/usr/bin/env python3
"""
🔐 API SEMRUSH USA AVEC CREDENTIALS AUTO - Version Python
Conversion du code JavaScript en Python pour le scraper SEM
"""

import asyncio
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SemrushUSAAutoAPI:
    """API Semrush avec récupération automatique des credentials"""
    
    def __init__(self):
        self.credentials = None
        self.is_authenticated = False
        self.page = None  # Page Playwright pour les appels API
    
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
    
    async def get_credentials(self) -> Dict[str, Any]:
        """Récupère les credentials depuis la page web"""
        try:
            logger.info('🔍 Récupération des credentials...')
            
            # Récupérer depuis localStorage, sessionStorage, cookies, etc.
            credentials_data = await self.page.evaluate("""
                () => {
                    const credentials = {};
                    
                    // Chercher dans localStorage
                    const authToken = localStorage.getItem('auth_token') || localStorage.getItem('semrush_token');
                    const userId = localStorage.getItem('user_id') || localStorage.getItem('semrush_user_id');
                    
                    // Chercher dans sessionStorage
                    const sessionAuth = sessionStorage.getItem('auth_token') || sessionStorage.getItem('semrush_credentials');
                    
                    // Chercher dans les cookies
                    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
                        const [key, value] = cookie.trim().split('=');
                        acc[key] = value;
                        return acc;
                    }, {});
                    
                    // Essayer window global
                    const windowAuth = window.user_credentials || window.semrushAuth || window.authData;
                    
                    return {
                        localStorage: {
                            authToken: authToken,
                            userId: userId
                        },
                        sessionStorage: {
                            auth: sessionAuth
                        },
                        cookies: Object.keys(cookies).filter(k => k.includes('auth')),
                        window: !!windowAuth,
                        timestamp: new Date().toISOString()
                    };
                }
            """)
            
            logger.info(f'📊 Credentials trouvés: {credentials_data}')
            
            # Utiliser les credentials trouvés ou fallback
            self.credentials = {
                'apiKey': credentials_data.get('localStorage', {}).get('authToken') or 
                         credentials_data.get('sessionStorage', {}).get('auth') or 
                         "943cfac719badc2ca14126e08b8fe44f",
                'userId': int(credentials_data.get('localStorage', {}).get('userId') or 26931056),
                'lastUpdate': credentials_data.get('timestamp', int(datetime.now(timezone.utc).timestamp() * 1000))
            }
            
            return self.credentials
            
        except Exception as error:
            logger.error(f'❌ Erreur récupération credentials: {error}')
            # Fallback sur credentials par défaut
            self.credentials = {
                'apiKey': "943cfac719badc2ca14126e08b8fe44f",
                'userId': 26931056,
                'lastUpdate': int(datetime.now(timezone.utc).timestamp() * 1000)
            }
            return self.credentials
    
    async def verify_connection(self) -> bool:
        """Vérifie la connexion avec l'API"""
        try:
            logger.info('🔍 Vérification de la connexion...')
            
            target_date = self.calculate_target_date()
            
            test_response = await self.page.evaluate("""
                async (data) => {
                    const response = await fetch('/dpa/rpc', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "organic.Summary",
                            "params": {
                                "request_id": crypto.randomUUID(),
                                "report": "domain.overview", 
                                "args": {
                                    "searchItem": "google.com",
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
                    
                    return await response.json();
                }
            """, {
                'target_date': target_date,
                'credentials': self.credentials
            })
            
            if test_response.get('error'):
                logger.error(f'❌ Connexion échouée: {test_response["error"]}')
                self.is_authenticated = False
                return False
            else:
                logger.info('✅ Connexion OK !')
                self.is_authenticated = True
                return True
                
        except Exception as error:
            logger.error(f'❌ Erreur vérification: {error}')
            self.is_authenticated = False
            return False
    
    async def refresh_credentials(self) -> bool:
        """Rafraîchit les credentials"""
        logger.info('🔄 Refresh des credentials...')
        
        # Re-scanner tous les endroits possibles
        await self.get_credentials()
        
        # Re-vérifier
        await self.verify_connection()
        
        if self.is_authenticated:
            logger.info('✅ Credentials refreshés avec succès !')
        else:
            logger.info('⚠️ Refresh partiel - utilisation des fallbacks')
        
        return self.is_authenticated
    
    async def initialize(self, page) -> bool:
        """Initialisation complète de l'API"""
        logger.info('🚀 Initialisation de l\'API Semrush...')
        logger.info('=' * 50)
        
        self.page = page
        
        # 1. Récupérer credentials
        await self.get_credentials()
        logger.info(f'📋 Credentials: userId={self.credentials["userId"]}, apiKey={self.credentials["apiKey"][:8]}...')
        
        # 2. Vérifier connexion
        await self.verify_connection()
        
        # 3. Status final
        if self.is_authenticated:
            logger.info('🎉 API prête à l\'emploi !')
        else:
            logger.info('⚠️ API en mode déconnecté (fallback)')
            await self.refresh_credentials()
        
        return self.is_authenticated
    
    async def get_usa_traffic(self, domain: str) -> Optional[Dict[str, Any]]:
        """Récupère le traffic USA pour un domaine"""
        # Auto-refresh si nécessaire
        if not self.is_authenticated or not self.credentials:
            logger.info('🔄 Auto-refresh...')
            await self.initialize(self.page)
        
        try:
            logger.info(f'🎯 ANALYSE USA: {domain.upper()}')
            logger.info('=' * 50)
            
            target_date = self.calculate_target_date()
            
            response = await self.page.evaluate("""
                async (data) => {
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
                    
                    return await response.json();
                }
            """, {
                'domain': domain,
                'target_date': target_date,
                'credentials': self.credentials
            })
            
            if response.get('result') and len(response['result']) > 0:
                us_entry = None
                for entry in response['result']:
                    if entry.get('database') == 'us':
                        us_entry = entry
                        break
                
                if not us_entry:
                    us_entry = response['result'][0]
                
                organic = us_entry.get('organic_traffic') or us_entry.get('organic') or 0
                paid = us_entry.get('traffic') or us_entry.get('paid') or 0
                total = organic + paid
                
                result = {
                    'domain': domain,
                    'database': 'us',
                    'organic': {
                        'traffic': organic,
                        'formatted': self.format_number(organic)
                    },
                    'paid': {
                        'traffic': paid,
                        'formatted': self.format_number(paid)
                    },
                    'total': {
                        'traffic': total,
                        'formatted': self.format_number(total)
                    },
                    'credentials': {
                        'valid': self.is_authenticated,
                        'lastUpdate': self.credentials['lastUpdate']
                    }
                }
                
                logger.info('🇺🇸 RÉSULTATS USA:')
                logger.info(f'📊 {domain}:')
                logger.info(f'  🌱 Organique: {result["organic"]["formatted"]}')
                logger.info(f'  💰 Payant: {result["paid"]["formatted"]}')
                logger.info(f'  🎯 TOTAL: {result["total"]["formatted"]}')
                
                return result
            
            logger.info('❌ Aucune donnée trouvée')
            return None
            
        except Exception as error:
            logger.error(f'❌ Erreur API: {error}')
            
            # Auto-retry avec refresh
            logger.info('🔄 Tentative de refresh et retry...')
            await self.refresh_credentials()
            
            return None
    
    def format_number(self, num: int) -> str:
        """Formate un nombre pour l'affichage"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)

# Instance globale
semrush_auto_api = SemrushUSAAutoAPI()
