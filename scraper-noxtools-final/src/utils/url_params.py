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
    logger.info(f"📅 [DEBUG] Starting reference date computation...")
    logger.info(f"📅 [DEBUG] Input today_utc: {today_utc}")
    
    if today_utc is None:
        today_utc = datetime.utcnow().date()
        logger.info(f"📅 [DEBUG] Using current UTC date: {today_utc}")
    elif isinstance(today_utc, datetime):
        today_utc = today_utc.date()
        logger.info(f"📅 [DEBUG] Converted datetime to date: {today_utc}")
    
    current_year = today_utc.year
    current_month = today_utc.month
    logger.info(f"📅 [DEBUG] Current year: {current_year}")
    logger.info(f"📅 [DEBUG] Current month: {current_month}")
    
    # Calculate target month (current - 2)
    target_month = current_month - 2
    target_year = current_year
    logger.info(f"📅 [DEBUG] Initial target month: {target_month}")
    logger.info(f"📅 [DEBUG] Initial target year: {target_year}")
    
    # Handle year rollover for January/February
    if target_month <= 0:
        target_month += 12
        target_year -= 1
        logger.info(f"📅 [DEBUG] Year rollover handled - new target month: {target_month}")
        logger.info(f"📅 [DEBUG] Year rollover handled - new target year: {target_year}")
    
    reference_date = date(target_year, target_month, 15)
    logger.info(f"📅 [DEBUG] Computed reference date: {today_utc} -> {reference_date}")
    logger.info(f"✅ [DEBUG] Reference date computation successful")
    return reference_date

def build_date_range(ref_date: Optional[date] = None) -> str:
    """
    Build date range string in YYYY-MM-15 format.
    
    Args:
        ref_date: Reference date (defaults to computed reference date)
        
    Returns:
        Date range string (e.g., "2025-07-15")
    """
    logger.info(f"📅 [DEBUG] Starting date range building...")
    logger.info(f"📅 [DEBUG] Input ref_date: {ref_date}")
    
    if ref_date is None:
        logger.info(f"📅 [DEBUG] No ref_date provided, computing reference date...")
        ref_date = compute_reference_date()
        logger.info(f"📅 [DEBUG] Computed reference date: {ref_date}")
    
    logger.info(f"📅 [DEBUG] Using reference date: {ref_date}")
    logger.info(f"📅 [DEBUG] Formatting date to YYYY-MM-15...")
    date_range = ref_date.strftime("%Y-%m-15")
    logger.info(f"📅 [DEBUG] Built date range: {date_range}")
    logger.info(f"✅ [DEBUG] Date range building successful")
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
    logger.info(f"🔗 [DEBUG] Starting market overview URL building...")
    logger.info(f"🔗 [DEBUG] Base URL: {base_url}")
    logger.info(f"🔗 [DEBUG] FID: {fid}")
    logger.info(f"🔗 [DEBUG] Date range: {date_range}")
    logger.info(f"🔗 [DEBUG] Country: {country}")
    logger.info(f"🔗 [DEBUG] Search type: {search_type}")
    
    params = {
        'searchType': search_type,
        'fid': fid,
        'dateRange': date_range,
        'country': country
    }
    logger.info(f"🔗 [DEBUG] URL parameters: {params}")
    
    # Ensure base URL ends with /
    if not base_url.endswith('/'):
        base_url += '/'
        logger.info(f"🔗 [DEBUG] Added trailing slash to base URL: {base_url}")
    
    # Build complete URL
    logger.info(f"🔗 [DEBUG] Encoding parameters...")
    encoded_params = urlencode(params)
    logger.info(f"🔗 [DEBUG] Encoded parameters: {encoded_params}")
    
    complete_url = base_url + '?' + encoded_params
    logger.info(f"🔗 [DEBUG] Built complete URL: {complete_url}")
    logger.info(f"✅ [DEBUG] Market overview URL building successful")
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
        logger.info(f"🔍 [DEBUG] Starting FID extraction from URL...")
        logger.info(f"🔍 [DEBUG] Input URL: {url}")
        
        logger.info(f"🔍 [DEBUG] Parsing URL...")
        parsed = urlparse(url)
        logger.info(f"🔍 [DEBUG] Parsed URL scheme: {parsed.scheme}")
        logger.info(f"🔍 [DEBUG] Parsed URL netloc: {parsed.netloc}")
        logger.info(f"🔍 [DEBUG] Parsed URL path: {parsed.path}")
        logger.info(f"🔍 [DEBUG] Parsed URL query: {parsed.query}")
        
        logger.info(f"🔍 [DEBUG] Parsing query parameters...")
        query_params = parse_qs(parsed.query)
        logger.info(f"🔍 [DEBUG] Query parameters: {query_params}")
        
        logger.info(f"🔍 [DEBUG] Looking for FID parameter...")
        fid = query_params.get('fid', [None])[0]
        logger.info(f"🔍 [DEBUG] Extracted FID: {fid}")
        
        if fid:
            logger.info(f"✅ [DEBUG] Extracted FID from URL: {fid}")
        else:
            logger.warning(f"⚠️ [DEBUG] No FID found in URL: {url}")
            
        return fid
    except Exception as e:
        logger.error(f"❌ [DEBUG] Error extracting FID from URL {url}: {e}")
        logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
        logger.error(f"❌ [DEBUG] Exception args: {e.args}")
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

def build_overview_url(base_url: str, shop_url: str, date_range: str, 
                      country: str = "us", search_type: str = "domain") -> str:
    """
    Build complete overview URL with all parameters for CPC extraction.
    
    Args:
        base_url: Base URL (e.g., "https://semrush2.semrush.pw/analytics/overview/")
        shop_url: Shop URL to analyze (e.g., "cakesbody.com")
        date_range: Date range string (e.g., "2025-07-15")
        country: Country code (default: "us")
        search_type: Search type (default: "domain")
        
    Returns:
        Complete URL with all parameters
    """
    # Convert date range from YYYY-MM-15 to YYYYMM format
    if '-' in date_range:
        date_parts = date_range.split('-')
        date_formatted = f"{date_parts[0]}{date_parts[1].zfill(2)}"
    else:
        date_formatted = date_range
    
    params = {
        'searchType': search_type,
        'q': shop_url,
        'db': country,
        'date': date_formatted
    }
    
    # Ensure base URL ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Build complete URL
    complete_url = base_url + '?' + urlencode(params)
    logger.info(f"🔗 [DEBUG] Built complete overview URL: {complete_url}")
    logger.info(f"✅ [DEBUG] Overview URL building successful")
    return complete_url

