"""
Base ingest source implementation.

This module defines the base class for all ingest sources, providing
common functionality and a standard interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Iterator

from ..models import IngestContent, IngestSource

logger = logging.getLogger(__name__)


class Base