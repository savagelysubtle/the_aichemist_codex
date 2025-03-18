import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Extractor(ABC):
    """Base class for all metadata extractors."""

    def __init__(self):
        self._supported_extensions: set[str] = set()
        self._supported_mime_types: set[str] = set()

    @property
    def supported_extensions(self) -> set[str]:
        """Get the file extensions supported by this extractor."""
        return self._supported_extensions

    @property
    def supported_mime_types(self) -> set[str]:
        """Get the MIME types supported by this extractor."""
        return self._supported_mime_types

    def can_handle(self, file_path: str, mime_type: str | None = None) -> bool:
        """Check if this extractor can handle the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file

        Returns:
            True if this extractor can handle the file, False otherwise
        """
        if not os.path.exists(file_path):
            return False

        # Check by extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() in self._supported_extensions:
            return True

        # Check by MIME type if provided
        if mime_type and mime_type in self._supported_mime_types:
            return True

        return False

    @abstractmethod
    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from the given file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing the extracted metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        pass

    @abstractmethod
    def extract_content(self, file_path: str) -> str:
        """Extract textual content from the given file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted textual content

        Raises:
            ExtractorError: If content extraction fails
        """
        pass

    @abstractmethod
    def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a textual preview of the file content.

        Args:
            file_path: Path to the file
            max_size: Maximum size of the preview in characters

        Returns:
            A textual preview of the file content

        Raises:
            ExtractorError: If preview generation fails
        """
        pass
