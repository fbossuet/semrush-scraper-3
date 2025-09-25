#!/usr/bin/env python3
"""
URL parameters utilities for Noxtools scraper
- Centralized date calculation (current date - 2 months, day 15)
- URL building for market overview with dynamic parameters
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional, Union
from urllib.parse import urlencode, urlparse, parse_qs

logger = logging.getLogger(__name__)

def compute_reference_date(today_utc: Optional[Union[datetime, date]] = None) -> date:
    """
    Compute reference date: current date - 2 months, day fixed to 15.
    
    Handles January/February edge cases (goes to previous year).
    
    Args:
        today_utc: Current UTC datetime (defaults to datetime.utcnow())
        
    Returns:
        Reference date with day=15, 2 months before today
        
    Examples:
        2025-01-24 -> 2024-11-15
        2025-02-10 -> 2024-12-15
        2025-09-24 -> 2025-07-15
    """
    if today_utc is None:
        today_utc = datetime.utcnow().date()
    elif isinstance(today_utc, datetime):
        today_utc = today_utc.date()
    
    current_year = today_utc.year
    current_month = today_utc.month
    
    # Calculate target month (current - 2)
    target_month = current_month - 2
    target_year = current_year
    
    # Handle year rollover for January/February
    if target_month <= 0:
        target_month += 12
        target_year -= 1
    
    reference_date = date(target_year, target_month, 15)
    
    logger.info(f"Computed reference date: {today_utc} -> {reference_date}")
    return reference_date

def build_date_range(ref_date: Optional[date] = None) -> str:
    """
    Build date range string in YYYY-MM-15 format.
    
    Args:
        ref_date: Reference date (defaults to computed reference date)
        
    Returns:
        Date range string (e.g., "2025-07-15")
    """
    if ref_date is None:
        ref_date = compute_reference_date()
    
    date_range = ref_date.strftime("%Y-%m-15")
    logger.info(f"Built date range: {date_range}")
    return date_range

def build_market_overview_url(base_url: str, fid: str, date_range: str, 
                            country: str = "us", search_type: str = "domain") -> str:
    """
    Build complete market overview URL with all parameters.
    
    Args:
        base_url: Base URL (e.g., "https://semrush3.semrush.pw/analytics/traffic/market-overview/")
        fid: FID parameter from search results
        date_range: Date range string (e.g., "2025-07-15")
        country: Country code (default: "us")
        search_type: Search type (default: "domain")
        
    Returns:
        Complete URL with all parameters
    """
    params = {
        'searchType': search_type,
        'fid': fid,
        'dateRange': date_range,
        'country': country
    }
    
    # Ensure base URL ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Build complete URL
    complete_url = base_url + '?' + urlencode(params)
    
    logger.info(f"Built market overview URL: {complete_url}")
    return complete_url

def extract_fid_from_url(url: str) -> Optional[str]:
    """
    Extract FID parameter from a market overview URL.
    
    Args:
        url: Market overview URL
        
    Returns:
        FID value or None if not found
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        fid = query_params.get('fid', [None])[0]
        
        if fid:
            logger.info(f"Extracted FID from URL: {fid}")
        else:
            logger.warning(f"No FID found in URL: {url}")
            
        return fid
    except Exception as e:
        logger.error(f"Error extracting FID from URL {url}: {e}")
        return None

def get_url_params_info() -> dict:
    """
    Get comprehensive URL parameters information for debugging.
    
    Returns:
        Dictionary with computed parameters
    """
    ref_date = compute_reference_date()
    date_range = build_date_range(ref_date)
    
    return {
        'reference_date': ref_date.isoformat(),
        'date_range': date_range,
        'default_country': 'us',
        'default_search_type': 'domain',
        'computed_at': datetime.utcnow().isoformat()
    }

URL parameters utilities for Noxtools scraper
- Centralized date calculation (current date - 2 months, day 15)
- URL building for market overview with dynamic parameters
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional, Union
from urllib.parse import urlencode, urlparse, parse_qs

logger = logging.getLogger(__name__)

def compute_reference_date(today_utc: Optional[Union[datetime, date]] = None) -> date:
    """
    Compute reference date: current date - 2 months, day fixed to 15.
    
    Handles January/February edge cases (goes to previous year).
    
    Args:
        today_utc: Current UTC datetime (defaults to datetime.utcnow())
        
    Returns:
        Reference date with day=15, 2 months before today
        
    Examples:
        2025-01-24 -> 2024-11-15
        2025-02-10 -> 2024-12-15
        2025-09-24 -> 2025-07-15
    """
    if today_utc is None:
        today_utc = datetime.utcnow().date()
    elif isinstance(today_utc, datetime):
        today_utc = today_utc.date()
    
    current_year = today_utc.year
    current_month = today_utc.month
    
    # Calculate target month (current - 2)
    target_month = current_month - 2
    target_year = current_year
    
    # Handle year rollover for January/February
    if target_month <= 0:
        target_month += 12
        target_year -= 1
    
    reference_date = date(target_year, target_month, 15)
    
    logger.info(f"Computed reference date: {today_utc} -> {reference_date}")
    return reference_date

def build_date_range(ref_date: Optional[date] = None) -> str:
    """
    Build date range string in YYYY-MM-15 format.
    
    Args:
        ref_date: Reference date (defaults to computed reference date)
        
    Returns:
        Date range string (e.g., "2025-07-15")
    """
    if ref_date is None:
        ref_date = compute_reference_date()
    
    date_range = ref_date.strftime("%Y-%m-15")
    logger.info(f"Built date range: {date_range}")
    return date_range

def build_market_overview_url(base_url: str, fid: str, date_range: str, 
                            country: str = "us", search_type: str = "domain") -> str:
    """
    Build complete market overview URL with all parameters.
    
    Args:
        base_url: Base URL (e.g., "https://semrush3.semrush.pw/analytics/traffic/market-overview/")
        fid: FID parameter from search results
        date_range: Date range string (e.g., "2025-07-15")
        country: Country code (default: "us")
        search_type: Search type (default: "domain")
        
    Returns:
        Complete URL with all parameters
    """
    params = {
        'searchType': search_type,
        'fid': fid,
        'dateRange': date_range,
        'country': country
    }
    
    # Ensure base URL ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Build complete URL
    complete_url = base_url + '?' + urlencode(params)
    
    logger.info(f"Built market overview URL: {complete_url}")
    return complete_url

def extract_fid_from_url(url: str) -> Optional[str]:
    """
    Extract FID parameter from a market overview URL.
    
    Args:
        url: Market overview URL
        
    Returns:
        FID value or None if not found
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        fid = query_params.get('fid', [None])[0]
        
        if fid:
            logger.info(f"Extracted FID from URL: {fid}")
        else:
            logger.warning(f"No FID found in URL: {url}")
            
        return fid
    except Exception as e:
        logger.error(f"Error extracting FID from URL {url}: {e}")
        return None

def get_url_params_info() -> dict:
    """
    Get comprehensive URL parameters information for debugging.
    
    Returns:
        Dictionary with computed parameters
    """
    ref_date = compute_reference_date()
    date_range = build_date_range(ref_date)
    
    return {
        'reference_date': ref_date.isoformat(),
        'date_range': date_range,
        'default_country': 'us',
        'default_search_type': 'domain',
        'computed_at': datetime.utcnow().isoformat()
    }
