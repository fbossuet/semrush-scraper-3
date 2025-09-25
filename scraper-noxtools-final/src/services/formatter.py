#!/usr/bin/env python3
"""
Data formatting pipeline for Noxtools scraper
- Normalize compact numbers (K/M suffixes)
- Convert percentages (remove %)
- Convert durations to seconds (integers)
- Convert dates to timestamps
- Apply formatting to all metrics
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, date
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

def normalize_compact_number(value: str) -> Optional[int]:
    """
    Normalize compact numbers with K/M suffixes.
    
    Examples:
        "33.3K" -> 333000
        "1.5M" -> 1500000
        "123" -> 123
        "45.6" -> 45 (truncated to int)
    
    Args:
        value: String value to normalize
        
    Returns:
        Integer value or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    # Clean the value (remove spaces, commas, dots as separators)
    cleaned = value.strip().replace(',', '').replace(' ', '')
    
    # Handle K/M suffixes
    if cleaned.upper().endswith('K'):
        try:
            number_part = cleaned[:-1]
            return int(float(number_part) * 1000)
        except (ValueError, IndexError):
            logger.warning(f"Invalid K format: {value}")
            return None
    
    elif cleaned.upper().endswith('M'):
        try:
            number_part = cleaned[:-1]
            return int(float(number_part) * 1000000)
        except (ValueError, IndexError):
            logger.warning(f"Invalid M format: {value}")
            return None
    
    # Handle regular numbers
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        logger.warning(f"Invalid number format: {value}")
        return None

def normalize_percentage(value: str) -> Optional[float]:
    """
    Normalize percentage values by removing % sign.
    
    Examples:
        "45.6%" -> 45.6
        "100%" -> 100.0
        "0.5%" -> 0.5
    
    Args:
        value: String value with optional % sign
        
    Returns:
        Float value or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    # Remove % sign and clean
    cleaned = value.strip().replace('%', '').replace(',', '').replace(' ', '')
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        logger.warning(f"Invalid percentage format: {value}")
        return None

def normalize_duration_to_seconds(value: str) -> Optional[int]:
    """
    Convert duration strings to seconds (integers).
    
    Examples:
        "2m 30s" -> 150
        "1h 15m" -> 4500
        "45s" -> 45
        "1:30" -> 90 (mm:ss format)
    
    Args:
        value: Duration string
        
    Returns:
        Seconds as integer or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    cleaned = value.strip().lower()
    total_seconds = 0
    
    try:
        # Handle mm:ss format
        if ':' in cleaned and cleaned.count(':') == 1:
            parts = cleaned.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        
        # Handle h/m/s format
        # Extract hours
        hour_match = re.search(r'(\d+)h', cleaned)
        if hour_match:
            total_seconds += int(hour_match.group(1)) * 3600
        
        # Extract minutes
        min_match = re.search(r'(\d+)m', cleaned)
        if min_match:
            total_seconds += int(min_match.group(1)) * 60
        
        # Extract seconds
        sec_match = re.search(r'(\d+)s', cleaned)
        if sec_match:
            total_seconds += int(sec_match.group(1))
        
        # If no time units found, try to parse as plain number (assume seconds)
        if total_seconds == 0:
            # Remove any non-numeric characters except decimal point
            numeric_only = re.sub(r'[^\d.]', '', cleaned)
            if numeric_only:
                return int(float(numeric_only))
        
        return total_seconds if total_seconds > 0 else None
        
    except (ValueError, AttributeError):
        logger.warning(f"Invalid duration format: {value}")
        return None

def to_timestamp_iso(value: Union[str, date, datetime]) -> Optional[str]:
    """
    Convert date/datetime to ISO 8601 UTC timestamp for logging/metadata.
    
    Args:
        value: Date, datetime, or string to convert
        
    Returns:
        ISO 8601 UTC string or None if invalid
    """
    if not value:
        return None
    
    try:
        if isinstance(value, datetime):
            return value.utcnow().isoformat() + 'Z'
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
            return dt.utcnow().isoformat() + 'Z'
        elif isinstance(value, str):
            # Try to parse common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.utcnow().isoformat() + 'Z'
                except ValueError:
                    continue
            logger.warning(f"Unrecognized date format: {value}")
            return None
        else:
            logger.warning(f"Unsupported date type: {type(value)}")
            return None
    except Exception as e:
        logger.error(f"Error converting to timestamp: {e}")
        return None

def to_sqlite_date(value: Union[str, date, datetime]) -> Optional[str]:
    """
    Convert date/datetime to SQLite DATE format (YYYY-MM-DD).
    
    Args:
        value: Date, datetime, or string to convert
        
    Returns:
        SQLite DATE string (YYYY-MM-DD) or None if invalid
    """
    if not value:
        return None
    
    try:
        if isinstance(value, datetime):
            return value.date().isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, str):
            # Try to parse common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            logger.warning(f"Unrecognized date format: {value}")
            return None
        else:
            logger.warning(f"Unsupported date type: {type(value)}")
            return None
    except Exception as e:
        logger.error(f"Error converting to SQLite date: {e}")
        return None

# Mapping from Noxtools metrics to analytics table fields
NOXTOOLS_TO_ANALYTICS_MAP = {
    'visits': 'visits',
    'entrancesSearchOrganic': 'organic_traffic', 
    'entrancesSearchPaid': 'paid_search_traffic',
    'purchasesPerVisit': 'conversion_rate',
    'avgVisitDuration': 'avg_visit_duration',
    'bouncesPerVisit': 'bounce_rate',
    'cpc': 'cpc',
    'branded_traffic': 'branded_traffic'  # New metric from tasks
}

def format_metrics(raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply formatting pipeline to all metrics.
    
    Args:
        raw_metrics: Raw metrics dictionary from scraping
        
    Returns:
        Formatted metrics dictionary ready for database
    """
    formatted = {}
    
    for noxtools_key, value in raw_metrics.items():
        if value is None or value == '':
            formatted[noxtools_key] = None
            continue
        
        # Map to analytics field name
        analytics_key = NOXTOOLS_TO_ANALYTICS_MAP.get(noxtools_key, noxtools_key)
        
        # Apply appropriate formatting based on metric type
        if noxtools_key in ['visits', 'entrancesSearchOrganic', 'entrancesSearchPaid', 'branded_traffic']:
            # Traffic metrics: normalize compact numbers
            formatted[analytics_key] = normalize_compact_number(str(value))
            
        elif noxtools_key in ['purchasesPerVisit', 'bouncesPerVisit']:
            # Percentage metrics: remove % sign
            formatted[analytics_key] = normalize_percentage(str(value))
            
        elif noxtools_key == 'avgVisitDuration':
            # Duration metric: convert to seconds
            formatted[analytics_key] = normalize_duration_to_seconds(str(value))
            
        elif noxtools_key == 'cpc':
            # CPC: keep as float (no special formatting needed)
            try:
                formatted[analytics_key] = float(str(value).replace(',', '').replace(' ', ''))
            except (ValueError, TypeError):
                formatted[analytics_key] = None
                
        else:
            # Default: keep as string
            formatted[analytics_key] = str(value)
    
    # Add metadata
    formatted['scraped_at'] = to_timestamp_iso(datetime.utcnow())  # ISO 8601 for logging
    formatted['updated_at'] = to_sqlite_date(datetime.utcnow())    # SQLite DATE format
    formatted['scraper_source'] = 'noxtools'
    
    logger.info(f"Formatted metrics: {len(formatted)} fields processed")
    return formatted

def get_formatter_info() -> Dict[str, Any]:
    """
    Get comprehensive formatter information for debugging.
    
    Returns:
        Dictionary with formatter configuration and mappings
    """
    return {
        'metrics_mapping': NOXTOOLS_TO_ANALYTICS_MAP,
        'supported_formats': {
            'compact_numbers': ['K', 'M', 'plain numbers'],
            'percentages': ['with % sign'],
            'durations': ['mm:ss', 'h/m/s format', 'plain seconds'],
            'dates': ['ISO 8601', 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS']
        },
        'output_types': {
            'traffic_metrics': 'integer',
            'percentage_metrics': 'float', 
            'duration_metrics': 'integer (seconds)',
            'cpc_metrics': 'float',
            'timestamps': 'ISO 8601 UTC string'
        }
    }

Data formatting pipeline for Noxtools scraper
- Normalize compact numbers (K/M suffixes)
- Convert percentages (remove %)
- Convert durations to seconds (integers)
- Convert dates to timestamps
- Apply formatting to all metrics
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, date
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

def normalize_compact_number(value: str) -> Optional[int]:
    """
    Normalize compact numbers with K/M suffixes.
    
    Examples:
        "33.3K" -> 333000
        "1.5M" -> 1500000
        "123" -> 123
        "45.6" -> 45 (truncated to int)
    
    Args:
        value: String value to normalize
        
    Returns:
        Integer value or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    # Clean the value (remove spaces, commas, dots as separators)
    cleaned = value.strip().replace(',', '').replace(' ', '')
    
    # Handle K/M suffixes
    if cleaned.upper().endswith('K'):
        try:
            number_part = cleaned[:-1]
            return int(float(number_part) * 1000)
        except (ValueError, IndexError):
            logger.warning(f"Invalid K format: {value}")
            return None
    
    elif cleaned.upper().endswith('M'):
        try:
            number_part = cleaned[:-1]
            return int(float(number_part) * 1000000)
        except (ValueError, IndexError):
            logger.warning(f"Invalid M format: {value}")
            return None
    
    # Handle regular numbers
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        logger.warning(f"Invalid number format: {value}")
        return None

def normalize_percentage(value: str) -> Optional[float]:
    """
    Normalize percentage values by removing % sign.
    
    Examples:
        "45.6%" -> 45.6
        "100%" -> 100.0
        "0.5%" -> 0.5
    
    Args:
        value: String value with optional % sign
        
    Returns:
        Float value or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    # Remove % sign and clean
    cleaned = value.strip().replace('%', '').replace(',', '').replace(' ', '')
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        logger.warning(f"Invalid percentage format: {value}")
        return None

def normalize_duration_to_seconds(value: str) -> Optional[int]:
    """
    Convert duration strings to seconds (integers).
    
    Examples:
        "2m 30s" -> 150
        "1h 15m" -> 4500
        "45s" -> 45
        "1:30" -> 90 (mm:ss format)
    
    Args:
        value: Duration string
        
    Returns:
        Seconds as integer or None if invalid
    """
    if not value or not isinstance(value, str):
        return None
    
    cleaned = value.strip().lower()
    total_seconds = 0
    
    try:
        # Handle mm:ss format
        if ':' in cleaned and cleaned.count(':') == 1:
            parts = cleaned.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        
        # Handle h/m/s format
        # Extract hours
        hour_match = re.search(r'(\d+)h', cleaned)
        if hour_match:
            total_seconds += int(hour_match.group(1)) * 3600
        
        # Extract minutes
        min_match = re.search(r'(\d+)m', cleaned)
        if min_match:
            total_seconds += int(min_match.group(1)) * 60
        
        # Extract seconds
        sec_match = re.search(r'(\d+)s', cleaned)
        if sec_match:
            total_seconds += int(sec_match.group(1))
        
        # If no time units found, try to parse as plain number (assume seconds)
        if total_seconds == 0:
            # Remove any non-numeric characters except decimal point
            numeric_only = re.sub(r'[^\d.]', '', cleaned)
            if numeric_only:
                return int(float(numeric_only))
        
        return total_seconds if total_seconds > 0 else None
        
    except (ValueError, AttributeError):
        logger.warning(f"Invalid duration format: {value}")
        return None

def to_timestamp_iso(value: Union[str, date, datetime]) -> Optional[str]:
    """
    Convert date/datetime to ISO 8601 UTC timestamp for logging/metadata.
    
    Args:
        value: Date, datetime, or string to convert
        
    Returns:
        ISO 8601 UTC string or None if invalid
    """
    if not value:
        return None
    
    try:
        if isinstance(value, datetime):
            return value.utcnow().isoformat() + 'Z'
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
            return dt.utcnow().isoformat() + 'Z'
        elif isinstance(value, str):
            # Try to parse common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.utcnow().isoformat() + 'Z'
                except ValueError:
                    continue
            logger.warning(f"Unrecognized date format: {value}")
            return None
        else:
            logger.warning(f"Unsupported date type: {type(value)}")
            return None
    except Exception as e:
        logger.error(f"Error converting to timestamp: {e}")
        return None

def to_sqlite_date(value: Union[str, date, datetime]) -> Optional[str]:
    """
    Convert date/datetime to SQLite DATE format (YYYY-MM-DD).
    
    Args:
        value: Date, datetime, or string to convert
        
    Returns:
        SQLite DATE string (YYYY-MM-DD) or None if invalid
    """
    if not value:
        return None
    
    try:
        if isinstance(value, datetime):
            return value.date().isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, str):
            # Try to parse common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            logger.warning(f"Unrecognized date format: {value}")
            return None
        else:
            logger.warning(f"Unsupported date type: {type(value)}")
            return None
    except Exception as e:
        logger.error(f"Error converting to SQLite date: {e}")
        return None

# Mapping from Noxtools metrics to analytics table fields
NOXTOOLS_TO_ANALYTICS_MAP = {
    'visits': 'visits',
    'entrancesSearchOrganic': 'organic_traffic', 
    'entrancesSearchPaid': 'paid_search_traffic',
    'purchasesPerVisit': 'conversion_rate',
    'avgVisitDuration': 'avg_visit_duration',
    'bouncesPerVisit': 'bounce_rate',
    'cpc': 'cpc',
    'branded_traffic': 'branded_traffic'  # New metric from tasks
}

def format_metrics(raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply formatting pipeline to all metrics.
    
    Args:
        raw_metrics: Raw metrics dictionary from scraping
        
    Returns:
        Formatted metrics dictionary ready for database
    """
    formatted = {}
    
    for noxtools_key, value in raw_metrics.items():
        if value is None or value == '':
            formatted[noxtools_key] = None
            continue
        
        # Map to analytics field name
        analytics_key = NOXTOOLS_TO_ANALYTICS_MAP.get(noxtools_key, noxtools_key)
        
        # Apply appropriate formatting based on metric type
        if noxtools_key in ['visits', 'entrancesSearchOrganic', 'entrancesSearchPaid', 'branded_traffic']:
            # Traffic metrics: normalize compact numbers
            formatted[analytics_key] = normalize_compact_number(str(value))
            
        elif noxtools_key in ['purchasesPerVisit', 'bouncesPerVisit']:
            # Percentage metrics: remove % sign
            formatted[analytics_key] = normalize_percentage(str(value))
            
        elif noxtools_key == 'avgVisitDuration':
            # Duration metric: convert to seconds
            formatted[analytics_key] = normalize_duration_to_seconds(str(value))
            
        elif noxtools_key == 'cpc':
            # CPC: keep as float (no special formatting needed)
            try:
                formatted[analytics_key] = float(str(value).replace(',', '').replace(' ', ''))
            except (ValueError, TypeError):
                formatted[analytics_key] = None
                
        else:
            # Default: keep as string
            formatted[analytics_key] = str(value)
    
    # Add metadata
    formatted['scraped_at'] = to_timestamp_iso(datetime.utcnow())  # ISO 8601 for logging
    formatted['updated_at'] = to_sqlite_date(datetime.utcnow())    # SQLite DATE format
    formatted['scraper_source'] = 'noxtools'
    
    logger.info(f"Formatted metrics: {len(formatted)} fields processed")
    return formatted

def get_formatter_info() -> Dict[str, Any]:
    """
    Get comprehensive formatter information for debugging.
    
    Returns:
        Dictionary with formatter configuration and mappings
    """
    return {
        'metrics_mapping': NOXTOOLS_TO_ANALYTICS_MAP,
        'supported_formats': {
            'compact_numbers': ['K', 'M', 'plain numbers'],
            'percentages': ['with % sign'],
            'durations': ['mm:ss', 'h/m/s format', 'plain seconds'],
            'dates': ['ISO 8601', 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS']
        },
        'output_types': {
            'traffic_metrics': 'integer',
            'percentage_metrics': 'float', 
            'duration_metrics': 'integer (seconds)',
            'cpc_metrics': 'float',
            'timestamps': 'ISO 8601 UTC string'
        }
    }
