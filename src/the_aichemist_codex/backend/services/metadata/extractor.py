"""Base classes for metadata extraction.

This module provides the foundation for all metadata extractors, including
the base class and registry for dynamic extractor discovery and selection.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ...core.models import FileMetadata
from ...registry import Registry

logger = logging.getLogger(__name__)


class BaseMetadataExtractor(ABC):
    """Base class for all metadata extractors."""

    def __init__(self):