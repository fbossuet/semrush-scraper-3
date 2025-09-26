#!/usr/bin/env python3
"""
Service d'enregistrement des métriques en base de données
- Intégration avec le scraper Noxtools
- Conversion des métriques au format BDD
- Gestion des erreurs et logs
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseSaver:
    """Service pour sauvegarder les métriques en base de données."""
    
    def __init__(self, db_path: str = "../trendtrack-scraper-final/data/trendtrack.db"):
        self.db_path = db_path
    
    def save_metrics(self, shop_id: int, metrics: Dict[str, Any]) -> bool:
        """
        Sauvegarde les métriques d'une boutique en base de données.
        
        Args:
            shop_id: ID de la boutique
            metrics: Dictionnaire des métriques extraites
            
        Returns:
            True si sauvegarde réussie, False sinon
        """
        try:
            # Connexion à la base de données
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Préparer les données pour l'insertion
                data = self._prepare_metrics_data(metrics)
                
                # Insérer les métriques
                cursor.execute('''
                    INSERT INTO analytics (
                        shop_id, visits, organic_traffic, paid_search_traffic,
                        bounce_rate, avg_visit_duration, conversion_rate, cpc,
                        updated_at, scraping_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    shop_id,
                    data['visits'],
                    data['organic_traffic'],
                    data['paid_search_traffic'],
                    data['bounce_rate'],
                    data['avg_visit_duration'],
                    data['conversion_rate'],
                    data['cpc'],
                    datetime.now().isoformat(),
                    'completed'
                ))
                
                conn.commit()
                logger.info(f"✅ Métriques sauvegardées pour shop_id: {shop_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde métriques pour shop_id {shop_id}: {e}")
            return False
    
    def _prepare_metrics_data(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare les données métriques pour l'insertion en BDD.
        
        Args:
            metrics: Métriques brutes du scraper
            
        Returns:
            Dictionnaire des données formatées pour la BDD
        """
        data = {
            'visits': None,
            'organic_traffic': None,
            'paid_search_traffic': None,
            'bounce_rate': None,
            'avg_visit_duration': None,
            'conversion_rate': None,
            'cpc': None
        }
        
        # Visites
        if 'visits' in metrics:
            visits = metrics['visits']
            if isinstance(visits, int):
                data['visits'] = visits
            elif isinstance(visits, str) and visits.isdigit():
                data['visits'] = int(visits)
        
        # Trafic organique
        if 'organic_search_traffic' in metrics:
            org_traffic = metrics['organic_search_traffic']
            if isinstance(org_traffic, str):
                # Convertir "161.2K" en 161200
                org_str = org_traffic.replace('K', '').replace('.', '')
                if org_str.isdigit():
                    data['organic_traffic'] = int(org_str) * 1000
            elif isinstance(org_traffic, int):
                data['organic_traffic'] = org_traffic
        
        # Trafic payant
        if 'paid_search_traffic' in metrics:
            paid_traffic = metrics['paid_search_traffic']
            if isinstance(paid_traffic, str):
                # Convertir "122.2K" en 122200
                paid_str = paid_traffic.replace('K', '').replace('.', '')
                if paid_str.isdigit():
                    data['paid_search_traffic'] = int(paid_str) * 1000
            elif isinstance(paid_traffic, int):
                data['paid_search_traffic'] = paid_traffic
        
        # Taux de rebond
        if 'bounce_rate' in metrics:
            bounce = metrics['bounce_rate']
            if isinstance(bounce, str):
                bounce_str = bounce.replace('%', '')
                try:
                    data['bounce_rate'] = float(bounce_str)
                except ValueError:
                    pass
            elif isinstance(bounce, (int, float)):
                data['bounce_rate'] = float(bounce)
        
        # Durée moyenne de visite
        if 'avg_visit_duration' in metrics:
            data['avg_visit_duration'] = str(metrics['avg_visit_duration'])
        
        # Taux de conversion
        if 'purchase_conversion' in metrics:
            data['conversion_rate'] = str(metrics['purchase_conversion'])
        
        # CPC
        if 'cpc' in metrics:
            cpc = metrics['cpc']
            if isinstance(cpc, (int, float)):
                data['cpc'] = float(cpc)
            elif isinstance(cpc, str):
                cpc_str = cpc.replace('$', '').replace('€', '')
                try:
                    data['cpc'] = float(cpc_str)
                except ValueError:
                    pass
        
        logger.debug(f"📊 Données préparées: {data}")
        return data
    
    def get_shop_by_domain(self, domain: str) -> Optional[int]:
        """
        Récupère l'ID d'une boutique par son domaine.
        
        Args:
            domain: Domaine de la boutique
            
        Returns:
            ID de la boutique ou None si non trouvée
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Rechercher par shop_url contenant le domaine
                cursor.execute('''
                    SELECT id FROM shops 
                    WHERE shop_url LIKE ? 
                    LIMIT 1
                ''', (f'%{domain}%',))
                
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur recherche boutique {domain}: {e}")
            return None
    
    def get_analytics_count(self) -> int:
        """Retourne le nombre total d'enregistrements analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM analytics")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Erreur comptage analytics: {e}")
            return 0
    
    def get_recent_analytics(self, limit: int = 5) -> list:
        """Retourne les dernières métriques sauvegardées."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.shop_id, s.shop_name, a.visits, a.organic_traffic, a.cpc, a.updated_at
                    FROM analytics a
                    JOIN shops s ON a.shop_id = s.id
                    ORDER BY a.updated_at DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Erreur récupération analytics: {e}")
            return []

# Fonction de convenance
def save_metrics_to_db(domain: str, metrics: Dict[str, Any], db_path: str = "../trendtrack-scraper-final/data/trendtrack.db") -> bool:
    """
    Fonction de convenance pour sauvegarder les métriques d'un domaine.
    
    Args:
        domain: Domaine de la boutique
        metrics: Métriques à sauvegarder
        db_path: Chemin vers la base de données
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    saver = DatabaseSaver(db_path)
    
    # Trouver l'ID de la boutique
    shop_id = saver.get_shop_by_domain(domain)
    if not shop_id:
        logger.warning(f"⚠️ Boutique non trouvée pour le domaine: {domain}")
        return False
    
    # Sauvegarder les métriques
    return saver.save_metrics(shop_id, metrics)
