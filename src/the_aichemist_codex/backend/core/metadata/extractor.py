"""Base classes for metadata extraction.

This module provides the foundation for all metadata extractors, including
the base class and registry for dynamic extractor discovery and selection.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.utils.io.async_io import AsyncFileIO
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class BaseMetadataExtractor(ABC):
    """Base class for all metadata extractors.

    Metadata extractors analyze file content to extract meaningful information
    such as keywords, topics, entities, and other content-based metadata.
    """

    def __init__(self, cache_manager: CacheManager | None = None):
        """Initialize the metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        self.cache_manager = cache_manager

    @abstractmethod
    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """Extract metadata from a file.

        This method must be implemented by all concrete extractor classes.

        Args:
            file_path: Path to the file
            content: Optional pre-loaded file content
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            A dictionary containing extracted metadata
        """
        pass

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """List of MIME types supported by this extractor.

        Returns:
            list[str]: A list of MIME type strings that this extractor can handle
        """
        pass

    async def _get_content(self, file_path: str | Path) -> str:
        """Read the content of a file.

        Args:
            file_path: Path to the file

        Returns:
            The file content as a string
        """
        try:
            # Convert to Path and ensure correct method signature
            path = Path(file_path)
            return await AsyncFileIO.read_text(path)
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            # Note: We can't specify encoding in AsyncFileIO.read, so this fallback may not work
            logger.warning(
                f"UnicodeDecodeError when reading {file_path}, using default encoding"
            )
            path = Path(file_path)
            return await AsyncFileIO.read_text(path)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""


class MetadataExtractorRegistry:
    """Registry for metadata extractors.

    This class keeps track of all available extractors and helps select
    the appropriate extractor for a given file.
    """

    _extractors: dict[str, type[BaseMetadataExtractor]] = {}
    _mime_type_map: dict[str, type[BaseMetadataExtractor]] = {}

    @classmethod
    def register(
        cls, extractor_class: type[BaseMetadataExtractor]
    ) -> type[BaseMetadataExtractor]:
        """Register a metadata extractor.

        This method can be used as a decorator to register extractor classes.

        Args:
            extractor_class: The extractor class to register

        Returns:
            The registered extractor class
        """
        cls._extractors[extractor_class.__name__] = extractor_class

        # Map MIME types to this extractor
        # We need to create an instance to access instance properties
        try:
            # Create a temporary instance to access the property
            temp_instance = extractor_class(None)  # Pass None as cache_manager
            # Get the supported mime types from the instance
            mime_types = temp_instance.supported_mime_types

            # Make sure we have a valid list
            if not isinstance(mime_types, list):
                logger.warning(
                    f"supported_mime_types from {extractor_class.__name__} is not a list: {mime_types}"
                )
                mime_types = list(mime_types) if hasattr(mime_types, "__iter__") else []

            # Register the extractor for each supported MIME type
            for mime_type in mime_types:
                cls._mime_type_map[mime_type] = extractor_class

        except Exception as e:
            logger.error(
                f"Error registering MIME types for {extractor_class.__name__}: {e}"
            )

        return extractor_class

    @classmethod
    def get_extractor_for_mime_type(
        cls, mime_type: str
    ) -> type[BaseMetadataExtractor] | None:
        """Get the appropriate extractor for a MIME type.

        Args:
            mime_type: The MIME type to find an extractor for

        Returns:
            An extractor class that supports the given MIME type, or None if not found
        """
        # Try exact match first
        if mime_type in cls._mime_type_map:
            return cls._mime_type_map[mime_type]

        # Try matching main type (e.g., "text/*")
        main_type = mime_type.split("/")[0] + "/*"
        if main_type in cls._mime_type_map:
            return cls._mime_type_map[main_type]

        return None

    @classmethod
    def get_all_extractors(cls) -> list[type[BaseMetadataExtractor]]:
        """Get all registered extractors.

        Returns:
            A list of all registered extractor classes
        """
        return list(cls._extractors.values())
