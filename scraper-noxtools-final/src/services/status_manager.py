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
    required_metrics: list = None
    # Critical metrics that must be present (if any missing = failed)
    critical_metrics: list = None
    # Minimum threshold for partial status
    partial_threshold: float = 0.5
    
    def __post_init__(self):
        if self.required_metrics is None:
            # SUPPRIMÉ: 'visits' de la liste - Métrique monthly visits supprimée selon spec007
            self.required_metrics = [
                'organic_search_traffic', 'paid_search_traffic',
                'bounce_rate', 'avg_visit_duration', 'conversion_rate'
            ]
        if self.critical_metrics is None:
            # SUPPRIMÉ: 'visits' de la liste critique - Métrique monthly visits supprimée selon spec007
            self.critical_metrics = ['organic_search_traffic']

class StatusManager:
    """Manages scraping status classification and logic."""
    
    def __init__(self, config: Optional[StatusManagerConfig] = None):
        self.config = config or StatusManagerConfig()
        
    def classify_scraping_status(self, metrics: Dict[str, Any]) -> Literal['completed', 'partial', 'failed']:
        """Classify scraping status based on metrics completeness.
        
        Args:
            metrics: Dictionary of extracted metrics
            
        Returns:
            Status classification: 'completed', 'partial', or 'failed'
        """
        if not metrics or not isinstance(metrics, dict):
            logger.warning("⚠️ No metrics provided for status classification")
            return 'failed'
        
        # Check for critical metrics first
        critical_missing = []
        for metric in self.config.critical_metrics:
            if metric not in metrics or not self._is_valid_metric(metrics[metric]):
                critical_missing.append(metric)
        
        if critical_missing:
            logger.warning(f"⚠️ Critical metrics missing: {critical_missing}")
            return 'failed'
        
        # Count valid required metrics
        valid_metrics = 0
        total_required = len(self.config.required_metrics)
        
        for metric in self.config.required_metrics:
            if metric in metrics and self._is_valid_metric(metrics[metric]):
                valid_metrics += 1
        
        # Determine status based on completeness
        completeness_ratio = valid_metrics / total_required if total_required > 0 else 0
        
        if completeness_ratio >= 1.0:
            logger.info(f"✅ Status: completed ({valid_metrics}/{total_required} metrics)")
            return 'completed'
        elif completeness_ratio >= self.config.partial_threshold:
            logger.info(f"⚠️ Status: partial ({valid_metrics}/{total_required} metrics)")
            return 'partial'
        else:
            logger.warning(f"❌ Status: failed ({valid_metrics}/{total_required} metrics)")
            return 'failed'
    
    def _is_valid_metric(self, value: Any) -> bool:
        """Check if a metric value is valid (not None, not empty, not error)."""
        if value is None:
            return False
        
        if isinstance(value, str):
            # Check for error indicators
            error_indicators = ['error', 'failed', 'timeout', 'not found', 'n/a', 'na']
            if value.lower() in error_indicators:
                return False
            # Check for empty or whitespace-only strings
            if not value.strip():
                return False
        
        if isinstance(value, (int, float)):
            # Check for negative values (might indicate errors)
            if value < 0:
                return False
        
        return True
    
    def get_status_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed status summary with metrics analysis.
        
        Args:
            metrics: Dictionary of extracted metrics
            
        Returns:
            Detailed status summary
        """
        status = self.classify_scraping_status(metrics)
        
        # Analyze metrics completeness
        valid_metrics = []
        missing_metrics = []
        invalid_metrics = []
        
        for metric in self.config.required_metrics:
            if metric in metrics:
                if self._is_valid_metric(metrics[metric]):
                    valid_metrics.append(metric)
                else:
                    invalid_metrics.append(metric)
            else:
                missing_metrics.append(metric)
        
        return {
            'status': status,
            'completeness_ratio': len(valid_metrics) / len(self.config.required_metrics),
            'valid_metrics': valid_metrics,
            'missing_metrics': missing_metrics,
            'invalid_metrics': invalid_metrics,
            'total_metrics': len(metrics) if metrics else 0,
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
