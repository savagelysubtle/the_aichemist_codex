import logging
import os
from typing import Any

from ...core.exceptions import MetadataExtractionError
from ...registry import Registry
from .extractor import Extractor

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manager for metadata extraction from various file types."""

    def __init__(self, registry: Registry):
        """Initialize the metadata manager with a registry.

        Args:
            registry: The registry for accessing dependencies
        """
        self._registry = registry
        self._extractors: list[Extractor] = []
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the metadata manager.

        This method should be called before using the manager.
        It registers all available extractors.
        """
        if self._initialized:
            return

        logger.info("Initializing metadata manager")

        # The extractors will be registered externally through register_extractor
        self._initialized = True
        logger.info("Metadata manager initialized successfully")

    def register_extractor(self, extractor: Extractor) -> None:
        """Register an extractor with the metadata manager.

        Args:
            extractor: The extractor to register
        """
        if not self._initialized:
            self.initialize()

        self._extractors.append(extractor)
        logger.debug(f"Registered extractor: {extractor.__class__.__name__}")

    def get_supported_extensions(self) -> set[str]:
        """Get all file extensions supported by registered extractors.

        Returns:
            Set of supported file extensions
        """
        if not self._initialized:
            self.initialize()

        extensions = set()
        for extractor in self._extractors:
            extensions.update(extractor.supported_extensions)
        return extensions

    def get_supported_mime_types(self) -> set[str]:
        """Get all MIME types supported by registered extractors.

        Returns:
            Set of supported MIME types
        """
        if not self._initialized:
            self.initialize()

        mime_types = set()
        for extractor in self._extractors:
            mime_types.update(extractor.supported_mime_types)
        return mime_types

    def get_extractor_for_file(
        self, file_path: str, mime_type: str | None = None
    ) -> Extractor | None:
        """Get the appropriate extractor for the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file

        Returns:
            An extractor that can handle the file, or None if no suitable extractor is found
        """
        if not self._initialized:
            self.initialize()

        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None

        for extractor in self._extractors:
            if extractor.can_handle(file_path, mime_type):
                return extractor

        return None

    def extract_metadata(
        self, file_path: str, mime_type: str | None = None
    ) -> dict[str, Any]:
        """Extract metadata from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file

        Returns:
            Dictionary containing the extracted metadata

        Raises:
            MetadataExtractionError: If metadata extraction fails
        """
        if not self._initialized:
            self.initialize()

        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            return extractor.extract_metadata(file_path)
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e

    def extract_content(self, file_path: str, mime_type: str | None = None) -> str:
        """Extract textual content from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file

        Returns:
            Extracted textual content

        Raises:
            MetadataExtractionError: If content extraction fails
        """
        if not self._initialized:
            self.initialize()

        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            return extractor.extract_content(file_path)
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract content from {file_path}: {str(e)}"
            ) from e

    def generate_preview(
        self, file_path: str, max_size: int = 1000, mime_type: str | None = None
    ) -> str:
        """Generate a textual preview of the file content.

        Args:
            file_path: Path to the file
            max_size: Maximum size of the preview in characters
            mime_type: Optional MIME type of the file

        Returns:
            A textual preview of the file content

        Raises:
            MetadataExtractionError: If preview generation fails
        """
        if not self._initialized:
            self.initialize()

        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            return extractor.generate_preview(file_path, max_size)
        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to generate preview for {file_path}: {str(e)}"
            ) from e
