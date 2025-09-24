#!/usr/bin/env python3
"""
Status Manager for Noxtools scraper
- Classify scraping status based on metrics completeness
- Determine completed/partial/failed status
- Handle status logic for Alpha (logging) and Beta (database)
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StatusManagerConfig:
    """Configuration for status manager."""
    # Required metrics for "completed" status
    required_metrics: list[str] = None
    
    # Critical metrics that cause "failed" if missing
    critical_metrics: list[str] = None
    
    def __post_init__(self):
        if self.required_metrics is None:
            self.required_metrics = [
                'visits', 'entrancesSearchOrganic', 'entrancesSearchPaid',
                'purchasesPerVisit', 'avgVisitDuration', 'bouncesPerVisit', 'cpc',
                'branded_traffic'
            ]
        
        if self.critical_metrics is None:
            self.critical_metrics = [
                'visits'  # visits is critical - if missing, likely failed
            ]

class StatusManager:
    """Handles scraping status classification and management."""
    
    def __init__(self, config: Optional[StatusManagerConfig] = None):
        self.config = config or StatusManagerConfig()
    
    def classify_scraping_status(self, metrics: Dict[str, Any]) -> Literal['completed', 'partial', 'failed']:
        """
        Classify scraping status based on metrics completeness.
        
        Args:
            metrics: Dictionary of scraped metrics
            
        Returns:
            Status: 'completed', 'partial', or 'failed'
        """
        try:
            if not metrics:
                logger.warning("No metrics provided for status classification")
                return 'failed'
            
            # Count valid metrics
            valid_metrics = 0
            total_metrics = len(self.config.required_metrics)
            missing_metrics = []
            critical_missing = []
            
            for metric in self.config.required_metrics:
                value = metrics.get(metric)
                if self._is_valid_metric_value(value):
                    valid_metrics += 1
                else:
                    missing_metrics.append(metric)
                    if metric in self.config.critical_metrics:
                        critical_missing.append(metric)
            
            # Determine status based on completeness
            if critical_missing:
                # Critical metrics missing = failed
                logger.warning(f"Critical metrics missing: {critical_missing}")
                return 'failed'
            
            elif valid_metrics == total_metrics:
                # All metrics present = completed
                logger.info(f"All {total_metrics} metrics successfully scraped")
                return 'completed'
            
            elif valid_metrics > 0:
                # Some metrics present = partial
                logger.info(f"Partial scraping: {valid_metrics}/{total_metrics} metrics ({missing_metrics} missing)")
                return 'partial'
            
            else:
                # No valid metrics = failed
                logger.warning("No valid metrics found")
                return 'failed'
                
        except Exception as e:
            logger.error(f"Error classifying scraping status: {e}")
            return 'failed'
    
    def _is_valid_metric_value(self, value: Any) -> bool:
        """
        Check if a metric value is valid (not None, not empty, not error).
        
        Args:
            value: Metric value to validate
            
        Returns:
            True if value is valid, False otherwise
        """
        if value is None:
            return False
        
        if isinstance(value, str):
            # Check for empty strings or error indicators
            if not value.strip():
                return False
            if value.lower() in ['error', 'failed', 'timeout', 'not found', 'n/a', 'na']:
                return False
        
        if isinstance(value, (int, float)):
            # Check for invalid numeric values
            if value < 0:  # Negative values might be invalid for most metrics
                return False
        
        return True
    
    def get_status_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive status summary for debugging.
        
        Args:
            metrics: Dictionary of scraped metrics
            
        Returns:
            Dictionary with status details
        """
        try:
            status = self.classify_scraping_status(metrics)
            
            # Count metrics by validity
            valid_count = 0
            invalid_count = 0
            missing_count = 0
            
            metric_details = {}
            
            for metric in self.config.required_metrics:
                value = metrics.get(metric)
                is_valid = self._is_valid_metric_value(value)
                
                metric_details[metric] = {
                    'value': value,
                    'valid': is_valid,
                    'critical': metric in self.config.critical_metrics
                }
                
                if is_valid:
                    valid_count += 1
                elif value is None:
                    missing_count += 1
                else:
                    invalid_count += 1
            
            return {
                'status': status,
                'summary': {
                    'total_metrics': len(self.config.required_metrics),
                    'valid_metrics': valid_count,
                    'invalid_metrics': invalid_count,
                    'missing_metrics': missing_count,
                    'completion_rate': (valid_count / len(self.config.required_metrics)) * 100
                },
                'metric_details': metric_details,
                'config': {
                    'required_metrics': self.config.required_metrics,
                    'critical_metrics': self.config.critical_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating status summary: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def log_status_result(self, shop_id: int, shop_url: str, metrics: Dict[str, Any], 
                         status: Optional[str] = None) -> None:
        """
        Log status result in a formatted way.
        
        Args:
            shop_id: Shop ID
            shop_url: Shop URL
            metrics: Scraped metrics
            status: Pre-computed status (optional)
        """
        try:
            if status is None:
                status = self.classify_scraping_status(metrics)
            
            summary = self.get_status_summary(metrics)
            
            logger.info(f"📊 STATUS RESULT - Shop {shop_id}")
            logger.info(f"   URL: {shop_url}")
            logger.info(f"   Status: {status.upper()}")
            logger.info(f"   Completion: {summary['summary']['completion_rate']:.1f}% ({summary['summary']['valid_metrics']}/{summary['summary']['total_metrics']})")
            
            if status == 'partial':
                missing = [m for m, details in summary['metric_details'].items() if not details['valid']]
                logger.info(f"   Missing metrics: {missing}")
            
            elif status == 'failed':
                critical_missing = [m for m, details in summary['metric_details'].items() 
                                  if not details['valid'] and details['critical']]
                if critical_missing:
                    logger.warning(f"   Critical metrics missing: {critical_missing}")
            
        except Exception as e:
            logger.error(f"Error logging status result: {e}")
    
    def get_status_manager_info(self) -> Dict[str, Any]:
        """
        Get comprehensive status manager information for debugging.
        
        Returns:
            Dictionary with status manager configuration
        """
        return {
            'required_metrics': self.config.required_metrics,
            'critical_metrics': self.config.critical_metrics,
            'total_required': len(self.config.required_metrics),
            'total_critical': len(self.config.critical_metrics),
            'status_logic': {
                'completed': 'All required metrics present and valid',
                'partial': 'Some metrics present, none critical missing',
                'failed': 'Critical metrics missing or no valid metrics'
            }
        }

# Convenience functions
def classify_status(metrics: Dict[str, Any]) -> Literal['completed', 'partial', 'failed']:
    """Quick function to classify scraping status."""
    manager = StatusManager()
    return manager.classify_scraping_status(metrics)

def get_status_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to get status summary."""
    manager = StatusManager()
    return manager.get_status_summary(metrics)
