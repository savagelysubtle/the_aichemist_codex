"""Base classes for metadata extraction.

This module provides the foundation for all metadata extractors, including
the base class and registry for dynamic extractor discovery and selection.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

# First-party absolute imports for Registry
from the_aichemist_codex.backend.registry import Registry

# Only import types during type checking
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BaseMetadataExtractor(ABC):
    """Base class for all metadata extractors."""

    def __init__(self) -> None:
        """Initialize the metadata extractor."""
        self._registry = Registry.get_instance()

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Any:  # Type: FileMetadata
        """Extract metadata from the given file.

        Args:
            file_path: Path to the file to extract metadata from

        Returns:
            FileMetadata: The extracted metadata
        """
        pass
