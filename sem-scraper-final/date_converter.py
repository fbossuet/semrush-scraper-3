#!/usr/bin/env python3
"""
Système centralisé de conversion des formats de dates vers ISO 8601 UTC
Gère tous les formats reçus des APIs externes et sources de données
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Dict, Any
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

class DateConverter:
    """
    Convertisseur centralisé pour tous les formats de dates vers ISO 8601 UTC
    """
    
    # Formats de dates détectés dans les APIs
    SUPPORTED_FORMATS = [
        # ISO 8601 formats
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2025-08-05T19:40:56.053Z
        "%Y-%m-%dT%H:%M:%S.%f",       # 2025-08-05T19:40:56.053
        "%Y-%m-%dT%H:%M:%SZ",         # 2025-08-05T19:40:56Z
        "%Y-%m-%dT%H:%M:%S",          # 2025-08-05T19:40:56
        
        # Formats avec espaces
        "%Y-%m-%d %H:%M:%S.%f",       # 2025-08-05 20:47:15.852714
        "%Y-%m-%d %H:%M:%S",          # 2025-08-05 20:47:15
        
        # Formats courts
        "%Y-%m-%d",                   # 2025-08-05
        "%Y/%m/%d",                   # 2025/08/05
        "%d/%m/%Y",                   # 05/08/2025
        "%m/%d/%Y",                   # 08/05/2025
        
        # Formats avec timezone
        "%Y-%m-%dT%H:%M:%S%z",        # 2025-08-05T19:40:56+02:00
        "%Y-%m-%d %H:%M:%S %z",       # 2025-08-05 20:47:15 +02:00
        
        # Formats JavaScript/Unix
        "%Y-%m-%dT%H:%M:%S.%fZ",      # Timestamp JavaScript
    ]
    
    # Patterns pour détecter les formats spécifiques
    PATTERNS = {
        'iso_with_z': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$',
        'iso_without_z': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$',
        'space_format': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?$',
        'date_only': r'^\d{4}-\d{2}-\d{2}$',
        'unix_timestamp': r'^\d{10}(\.\d+)?$',
        'javascript_timestamp': r'^\d{13}$',
    }
    
    @classmethod
    def convert_to_iso8601_utc(cls, date_input: Union[str, int, float, datetime, None]) -> Optional[str]:
        """
        Convertit n'importe quel format de date vers ISO 8601 UTC
        
        Args:
            date_input: Date à convertir (str, int, float, datetime, None)
            
        Returns:
            str: Date au format ISO 8601 UTC ou None si conversion impossible
        """
        if date_input is None:
            return None
            
        # Si c'est déjà un datetime
        if isinstance(date_input, datetime):
            return cls._datetime_to_iso8601_utc(date_input)
        
        # Si c'est un timestamp numérique
        if isinstance(date_input, (int, float)):
            return cls._timestamp_to_iso8601_utc(date_input)
        
        # Si c'est une chaîne
        if isinstance(date_input, str):
            return cls._string_to_iso8601_utc(date_input)
        
        # Fallback: essayer de convertir en string
        try:
            return cls._string_to_iso8601_utc(str(date_input))
        except Exception as e:
            logger.warning(f"⚠️ Impossible de convertir la date: {date_input} - {e}")
            return None
    
    @classmethod
    def _datetime_to_iso8601_utc(cls, dt: datetime) -> str:
        """Convertit un datetime vers ISO 8601 UTC"""
        if dt.tzinfo is None:
            # Si pas de timezone, assumer UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convertir vers UTC
            dt = dt.astimezone(timezone.utc)
        
        return dt.isoformat()
    
    @classmethod
    def _timestamp_to_iso8601_utc(cls, timestamp: Union[int, float]) -> str:
        """Convertit un timestamp vers ISO 8601 UTC"""
        # Gérer les timestamps JavaScript (millisecondes) et Unix (secondes)
        if timestamp > 1e12:  # Timestamp JavaScript (millisecondes)
            timestamp = timestamp / 1000
        
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.isoformat()
    
    @classmethod
    def _string_to_iso8601_utc(cls, date_str: str) -> Optional[str]:
        """Convertit une chaîne de date vers ISO 8601 UTC"""
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        
        # Détecter le format et convertir
        detected_format = cls._detect_format(date_str)
        
        if detected_format:
            return cls._convert_detected_format(date_str, detected_format)
        
        # Fallback: utiliser dateutil
        return cls._convert_with_dateutil(date_str)
    
    @classmethod
    def _detect_format(cls, date_str: str) -> Optional[str]:
        """Détecte le format de la date"""
        for pattern_name, pattern in cls.PATTERNS.items():
            if re.match(pattern, date_str):
                return pattern_name
        return None
    
    @classmethod
    def _convert_detected_format(cls, date_str: str, format_type: str) -> Optional[str]:
        """Convertit selon le format détecté"""
        try:
            if format_type == 'iso_with_z':
                # 2025-08-05T19:40:56.053Z
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return cls._datetime_to_iso8601_utc(dt)
            
            elif format_type == 'iso_without_z':
                # 2025-08-05T19:40:56.053
                dt = datetime.fromisoformat(date_str)
                return cls._datetime_to_iso8601_utc(dt)
            
            elif format_type == 'space_format':
                # 2025-08-05 20:47:15.852714
                if '.' in date_str:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return cls._datetime_to_iso8601_utc(dt)
            
            elif format_type == 'date_only':
                # 2025-08-05
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return cls._datetime_to_iso8601_utc(dt)
            
            elif format_type == 'unix_timestamp':
                # 1691234567
                timestamp = float(date_str)
                return cls._timestamp_to_iso8601_utc(timestamp)
            
            elif format_type == 'javascript_timestamp':
                # 1691234567890
                timestamp = float(date_str) / 1000
                return cls._timestamp_to_iso8601_utc(timestamp)
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur conversion format {format_type}: {date_str} - {e}")
        
        return None
    
    @classmethod
    def _convert_with_dateutil(cls, date_str: str) -> Optional[str]:
        """Convertit avec dateutil comme fallback"""
        try:
            dt = dateutil_parser.parse(date_str)
            return cls._datetime_to_iso8601_utc(dt)
        except Exception as e:
            logger.warning(f"⚠️ Erreur dateutil pour: {date_str} - {e}")
            return None
    
    @classmethod
    def convert_dict_dates(cls, data: Dict[str, Any], date_fields: list) -> Dict[str, Any]:
        """
        Convertit toutes les dates d'un dictionnaire
        
        Args:
            data: Dictionnaire contenant les données
            date_fields: Liste des champs contenant des dates
            
        Returns:
            Dict: Dictionnaire avec les dates converties
        """
        result = data.copy()
        
        for field in date_fields:
            if field in result and result[field] is not None:
                converted = cls.convert_to_iso8601_utc(result[field])
                if converted:
                    result[field] = converted
                else:
                    logger.warning(f"⚠️ Impossible de convertir le champ {field}: {result[field]}")
                    result[field] = None
        
        return result
    
    @classmethod
    def validate_iso8601_utc(cls, date_str: str) -> bool:
        """
        Valide qu'une chaîne est au format ISO 8601 UTC
        
        Args:
            date_str: Chaîne à valider
            
        Returns:
            bool: True si valide, False sinon
        """
        if not date_str:
            return False
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt).total_seconds() == 0
        except:
            return False

# Fonctions utilitaires pour compatibilité
def parse_date_robust(date_string: Union[str, None]) -> Optional[datetime]:
    """
    Fonction de compatibilité avec l'ancien code
    Retourne un datetime au lieu d'une chaîne ISO 8601
    """
    if not date_string:
        return None
    
    iso_string = DateConverter.convert_to_iso8601_utc(date_string)
    if iso_string:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    return None

def convert_api_response_dates(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les dates d'une réponse API vers ISO 8601 UTC
    
    Args:
        response_data: Données de réponse API
        
    Returns:
        Dict: Données avec dates converties
    """
    # Champs de dates communs dans les APIs
    date_fields = [
        'timestamp', 'created_at', 'updated_at', 'scraped_at', 'creation_date',
        'last_update', 'date', 'time', 'start_date', 'end_date', 'year_founded'
    ]
    
    return DateConverter.convert_dict_dates(response_data, date_fields)

# Tests unitaires
if __name__ == "__main__":
    # Tests des conversions
    test_cases = [
        "2025-08-05T19:40:56.053Z",
        "2025-08-05T19:40:56.053",
        "2025-08-05 20:47:15.852714",
        "2025-08-05T19:40:56",
        "2025-08-05 20:47:15",
        "2025-08-05",
        "1691234567",  # Unix timestamp
        "1691234567890",  # JavaScript timestamp
        datetime.now(),
        datetime.now(timezone.utc),
        None,
        "",
        "invalid_date"
    ]
    
    print("🧪 TESTS DE CONVERSION DES DATES")
    print("=" * 50)
    
    for test_input in test_cases:
        result = DateConverter.convert_to_iso8601_utc(test_input)
        print(f"Input: {test_input}")
        print(f"Output: {result}")
        print(f"Valid: {DateConverter.validate_iso8601_utc(result) if result else 'N/A'}")
        print("-" * 30)
