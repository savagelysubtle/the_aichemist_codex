"""Base classes for metadata extraction.

This module provides the foundation for all metadata extractors, including
the base class and registry for dynamic extractor discovery and selection.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from backend.file_reader.file_metadata import FileMetadata
from backend.utils.async_io import AsyncFileIO
from backend.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class BaseMetadataExtractor(ABC):
    """Base class for all metadata extractors.

    Metadata extractors analyze file content to extract meaningful information
    such as keywords, topics, entities, and other content-based metadata.
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize the metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        self.cache_manager = cache_manager

    @abstractmethod
    async def extract(
        self,
        file_path: Union[str, Path],
        content: Optional[str] = None,
        mime_type: Optional[str] = None,
        metadata: Optional[FileMetadata] = None,
    ) -> Dict[str, Any]:
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
    def supported_mime_types(self) -> List[str]:
        """List of MIME types supported by this extractor."""
        pass

    async def _get_content(
        self, file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> str:
        """Read the content of a file.

        Args:
            file_path: Path to the file
            encoding: Text encoding to use

        Returns:
            The file content as a string
        """
        try:
            return await AsyncFileIO.read(file_path, encoding=encoding)
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            return await AsyncFileIO.read(file_path, encoding="latin-1")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""


class MetadataExtractorRegistry:
    """Registry for metadata extractors.

    This class keeps track of all available extractors and helps select
    the appropriate extractor for a given file.
    """

    _extractors: Dict[str, Type[BaseMetadataExtractor]] = {}
    _mime_type_map: Dict[str, Type[BaseMetadataExtractor]] = {}

    @classmethod
    def register(
        cls, extractor_class: Type[BaseMetadataExtractor]
    ) -> Type[BaseMetadataExtractor]:
        """Register a metadata extractor.

        This method can be used as a decorator to register extractor classes.

        Args:
            extractor_class: The extractor class to register

        Returns:
            The registered extractor class
        """
        cls._extractors[extractor_class.__name__] = extractor_class

        # Map MIME types to this extractor
        for mime_type in extractor_class.supported_mime_types:
            cls._mime_type_map[mime_type] = extractor_class

        return extractor_class

    @classmethod
    def get_extractor_for_mime_type(
        cls, mime_type: str
    ) -> Optional[Type[BaseMetadataExtractor]]:
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
    def get_all_extractors(cls) -> List[Type[BaseMetadataExtractor]]:
        """Get all registered extractors.

        Returns:
            A list of all registered extractor classes
        """
        return list(cls._extractors.values())
