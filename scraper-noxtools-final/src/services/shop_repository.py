#!/usr/bin/env python3
"""
Shop Repository for Noxtools scraper
- Retrieve shops to scrape from database
- Filter by scraping_status (NULL = not scraped yet)
- Handle batch processing with anti-detection delays
"""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from core.anti_detection import compute_delay_seconds, TokenBucket

logger = logging.getLogger(__name__)

@dataclass
class Shop:
    """Shop data model."""
    id: int
    shop_url: str
    name: Optional[str] = None
    status: Optional[str] = None

@dataclass
class ShopRepositoryConfig:
    """Configuration for shop repository."""
    # Database path
    db_path: str = "trendtrack-scraper-final/data/trendtrack.db"
    
    # Batch processing
    batch_size: int = 5
    inter_batch_delay_ms: int = 2000  # 2 seconds between batches
    
    # Anti-detection delays
    base_delay_ms: int = 1000
    jitter_ms: int = 500
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    burst_size: int = 10

class ShopRepository:
    """Handles shop data retrieval from database."""
    
    def __init__(self, config: Optional[ShopRepositoryConfig] = None):
        self.config = config or ShopRepositoryConfig()
        self.rate_limiter = TokenBucket(
            capacity=self.config.burst_size,
            refill_rate_per_min=self.config.rate_limit_per_minute
        )
    
    def get_shops_to_scrape(self, limit: Optional[int] = None, offset: int = 0) -> List[Shop]:
        """
        Retrieve shops that need to be scraped (scraping_status is NULL).
        
        Args:
            limit: Maximum number of shops to retrieve (default: batch_size)
            offset: Number of shops to skip
            
        Returns:
            List of Shop objects ready for scraping
        """
        try:
            if limit is None:
                limit = self.config.batch_size
            
            # Ensure database path exists
            db_path = Path(self.config.db_path)
            if not db_path.exists():
                logger.error(f"Database not found: {db_path}")
                return []
            
            # Connect to database
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Query shops that haven't been scraped yet
                query = """
                SELECT s.id, s.shop_url, s.name, a.scraping_status
                FROM shops s
                LEFT JOIN analytics a ON s.id = a.shop_id
                WHERE a.scraping_status IS NULL
                ORDER BY s.id
                LIMIT ? OFFSET ?
                """
                
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                
                shops = []
                for row in rows:
                    shop = Shop(
                        id=row['id'],
                        shop_url=row['shop_url'],
                        name=row['name'],
                        status=row['scraping_status']
                    )
                    shops.append(shop)
                
                logger.info(f"Retrieved {len(shops)} shops to scrape (limit={limit}, offset={offset})")
                return shops
                
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving shops: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving shops: {e}")
            return []
    
    def get_total_shops_to_scrape(self) -> int:
        """
        Get total count of shops that need to be scraped.
        
        Returns:
            Total number of shops with NULL scraping_status
        """
        try:
            db_path = Path(self.config.db_path)
            if not db_path.exists():
                logger.error(f"Database not found: {db_path}")
                return 0
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT COUNT(*)
                FROM shops s
                LEFT JOIN analytics a ON s.id = a.shop_id
                WHERE a.scraping_status IS NULL
                """
                
                cursor.execute(query)
                count = cursor.fetchone()[0]
                
                logger.debug(f"Total shops to scrape: {count}")
                return count
                
        except sqlite3.Error as e:
            logger.error(f"Database error counting shops: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error counting shops: {e}")
            return 0
    
    async def get_shops_batch_with_delay(self, batch_number: int = 0) -> List[Shop]:
        """
        Get a batch of shops with anti-detection delay.
        
        Args:
            batch_number: Batch number for offset calculation
            
        Returns:
            List of Shop objects for current batch
        """
        try:
            # Calculate offset for this batch
            offset = batch_number * self.config.batch_size
            
            # Get shops for this batch
            shops = self.get_shops_to_scrape(limit=self.config.batch_size, offset=offset)
            
            if shops:
                logger.info(f"Batch {batch_number + 1}: {len(shops)} shops ready for scraping")
                
                # Apply rate limiting
                await self.rate_limiter.acquire()
                
                # Apply anti-detection delay
                import asyncio
                delay = compute_delay_seconds(
                    base_ms=self.config.base_delay_ms,
                    jitter_ms=self.config.jitter_ms
                )
                await asyncio.sleep(delay)
                logger.debug(f"Applied anti-detection delay: {delay:.2f}s")
                
            return shops
            
        except Exception as e:
            logger.error(f"Error getting batch {batch_number}: {e}")
            return []
    
    def get_shop_by_id(self, shop_id: int) -> Optional[Shop]:
        """
        Get a specific shop by ID.
        
        Args:
            shop_id: Shop ID to retrieve
            
        Returns:
            Shop object or None if not found
        """
        try:
            db_path = Path(self.config.db_path)
            if not db_path.exists():
                logger.error(f"Database not found: {db_path}")
                return None
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                SELECT s.id, s.shop_url, s.name, a.scraping_status
                FROM shops s
                LEFT JOIN analytics a ON s.id = a.shop_id
                WHERE s.id = ?
                """
                
                cursor.execute(query, (shop_id,))
                row = cursor.fetchone()
                
                if row:
                    shop = Shop(
                        id=row['id'],
                        shop_url=row['shop_url'],
                        name=row['name'],
                        status=row['scraping_status']
                    )
                    logger.debug(f"Retrieved shop {shop_id}: {shop.shop_url}")
                    return shop
                else:
                    logger.warning(f"Shop {shop_id} not found")
                    return None
                    
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving shop {shop_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving shop {shop_id}: {e}")
            return None
    
    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get comprehensive repository information for debugging.
        
        Returns:
            Dictionary with repository configuration and statistics
        """
        try:
            total_shops = self.get_total_shops_to_scrape()
            
            return {
                'database_path': self.config.db_path,
                'database_exists': Path(self.config.db_path).exists(),
                'batch_size': self.config.batch_size,
                'inter_batch_delay_ms': self.config.inter_batch_delay_ms,
                'anti_detection': {
                    'base_delay_ms': self.config.base_delay_ms,
                    'jitter_ms': self.config.jitter_ms
                },
                'rate_limiting': {
                    'per_minute': self.config.rate_limit_per_minute,
                    'burst_size': self.config.burst_size
                },
                'statistics': {
                    'total_shops_to_scrape': total_shops,
                    'estimated_batches': (total_shops + self.config.batch_size - 1) // self.config.batch_size
                }
            }
            
        except Exception as e:
            logger.error(f"Repository info error: {e}")
            return {'error': str(e)}

# Convenience functions
def get_shops_to_scrape(db_path: str = "trendtrack-scraper-final/data/trendtrack.db", 
                       limit: int = 5) -> List[Shop]:
    """Quick function to get shops to scrape."""
    config = ShopRepositoryConfig(db_path=db_path, batch_size=limit)
    repository = ShopRepository(config)
    return repository.get_shops_to_scrape()

def get_total_shops_count(db_path: str = "trendtrack-scraper-final/data/trendtrack.db") -> int:
    """Quick function to get total shops count."""
    config = ShopRepositoryConfig(db_path=db_path)
    repository = ShopRepository(config)
    return repository.get_total_shops_to_scrape()
