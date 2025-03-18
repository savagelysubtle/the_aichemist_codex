"""
Analytics Module.

This module provides functionality for tracking and analyzing application
usage, events, errors, and performance metrics.
"""

from .analytics_manager import AnalyticsManagerImpl
from .schema import AnalyticsSchema

__all__ = [
    "AnalyticsManagerImpl",
    "AnalyticsSchema",
]
