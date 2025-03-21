"""
Base implementation of the ContentAnalyzer interface.

This module provides a base implementation for content analysis functionality,
with common utilities and helper methods for specific analyzer implementations.
"""

import logging
import mimetypes
from abc import abstractmethod
from pathlib import Path
from typing import Any

from the_aichemist_codex.backend.core.exceptions.exceptions import (
    AnalysisError,
    FileError,
)
from the_aichemist_codex.backend.core.interfaces.interfaces import (
    ContentAnalyzer,
    FileReader,
)

logger = logging.getLogger(__name__)


class BaseContentAnalyzer(ContentAnalyzer):
    """
    Base implementation of the ContentAnalyzer interface.

    This class provides common functionality for content analyzers,
    including file type detection and basic content loading.
    """

    def __init__(self, file_reader: FileReader) -> None:
        """
        Initialize the base content analyzer.

        Args:
            file_reader: File reader service for accessing file content
        """
        self._file_reader = file_reader
        self._initialized = False
        self._mime_type_map: dict[str, str] = {}
        self._supported_extensions: set[str] = set()
        self._supported_content_types: set[str] = set()

    async def initialize(self) -> None:
        """
        Initialize the content analyzer.

        This base implementation registers supported file types and content types.

        Raises:
            AnalysisError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Register default MIME types if not already registered
            if not mimetypes.inited:
                mimetypes.init()

            # Register supported extensions and content types
            await self._register_supported_types()

            self._initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content analyzer: {e}")
            raise AnalysisError(f"Failed to initialize content analyzer: {e}") from e

    @abstractmethod
    async def _register_supported_types(self) -> None:
        """
        Register supported file types and content types.

        This method should be implemented by subclasses to register
        the file types and content types they support.
        """
        pass

    def _ensure_initialized(self) -> None:
        """
        Ensure the analyzer is initialized.

        Raises:
            AnalysisError: If the analyzer is not initialized
        """
        if not self._initialized:
            raise AnalysisError("Content analyzer is not initialized")

    async def _load_content(self, content: str | Path) -> str:
        """
        Load content from a string or file path.

        Args:
            content: String content or path to a file

        Returns:
            Content as a string

        Raises:
            FileError: If the file cannot be read
        """
        if isinstance(content, Path) or (
            isinstance(content, str) and Path(content).exists()
        ):
            # Content is a file path
            file_path = Path(content) if isinstance(content, str) else content
            return await self._file_reader.read_text(str(file_path))
        elif isinstance(content, str):
            # Content is already a string
            return content
        else:
            raise FileError(f"Invalid content type: {type(content)}")

    def _detect_content_type(self, file_path: Path) -> str:
        """
        Detect the content type of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Detected content type string
        """
        ext = file_path.suffix.lower().lstrip(".")

        # Check if we have a mapping for this extension
        if ext in self._mime_type_map:
            return self._mime_type_map[ext]

        # Fall back to mimetypes module
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    async def analyze_file(
        self,
        file_path: Path,
        content_type: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a file and extract meaningful information.

        Args:
            file_path: Path to the file to analyze
            content_type: Optional hint about the file's content type
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If analysis fails
        """
        self._ensure_initialized()

        # Detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(file_path)

        try:
            # Load the file content
            content = await self._file_reader.read_text(str(file_path))

            # Analyze the content
            result = await self.analyze_text(
                text=content,
                content_type=content_type,
                file_path=file_path,
                options=options,
            )

            # Add file metadata to the result
            result.update(
                {
                    "file_path": str(file_path),
                    "content_type": content_type,
                    "file_name": file_path.name,
                    "extension": file_path.suffix.lower().lstrip("."),
                }
            )

            return result
        except FileError:
            # Re-raise FileError as is
            raise
        except AnalysisError:
            # Re-raise AnalysisError as is
            raise
        except Exception as e:
            # Wrap other exceptions in AnalysisError
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise AnalysisError(
                f"Error analyzing file: {e}",
                file_path=str(file_path),
                analyzer_type=self.__class__.__name__,
                content_type=content_type,
            ) from e

    async def analyze_text(
        self,
        text: str,
        content_type: str | None = None,
        file_path: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze text content and extract meaningful information.

        This base implementation raises NotImplementedError and should
        be overridden by concrete analyzer implementations.

        Args:
            text: The text content to analyze
            content_type: Optional hint about the content type
            file_path: Optional path to the source file (for context)
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            NotImplementedError: This base method is not implemented
        """
        raise NotImplementedError("analyze_text must be implemented by subclass")

    async def summarize(
        self, content: str | Path, max_length: int = 500, output_format: str = "text"
    ) -> str:
        """
        Generate a summary of file content.

        This base implementation raises NotImplementedError and should
        be overridden by concrete analyzer implementations.

        Args:
            content: Either a string of content or a path to a file
            max_length: Maximum length of the summary in characters
            output_format: Output format (e.g., "text", "html", "markdown")

        Returns:
            Generated summary as a string

        Raises:
            NotImplementedError: This base method is not implemented
        """
        raise NotImplementedError("summarize must be implemented by subclass")

    async def extract_entities(
        self,
        content: str | Path,
        entity_types: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract named entities from content.

        This base implementation raises NotImplementedError and should
        be overridden by concrete analyzer implementations.

        Args:
            content: Either a string of content or a path to a file
            entity_types: Types of entities to extract (e.g., "person", "organization")
            min_confidence: Minimum confidence score for extracted entities

        Returns:
            Dictionary mapping entity types to lists of extracted entities

        Raises:
            NotImplementedError: This base method is not implemented
        """
        raise NotImplementedError("extract_entities must be implemented by subclass")

    async def extract_keywords(
        self, content: str | Path, max_keywords: int = 10, min_relevance: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Extract keywords or key phrases from content.

        This base implementation raises NotImplementedError and should
        be overridden by concrete analyzer implementations.

        Args:
            content: Either a string of content or a path to a file
            max_keywords: Maximum number of keywords to extract
            min_relevance: Minimum relevance score for keywords

        Returns:
            List of dictionaries containing keywords and their relevance scores

        Raises:
            NotImplementedError: This base method is not implemented
        """
        raise NotImplementedError("extract_keywords must be implemented by subclass")

    async def classify_content(
        self,
        content: str | Path,
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Classify content into categories.

        This base implementation raises NotImplementedError and should
        be overridden by concrete analyzer implementations.

        Args:
            content: Either a string of content or a path to a file
            taxonomy: Optional list of categories to use
            min_confidence: Minimum confidence score for classifications

        Returns:
            List of dictionaries containing categories and confidence scores

        Raises:
            NotImplementedError: This base method is not implemented
        """
        raise NotImplementedError("classify_content must be implemented by subclass")

    async def get_supported_file_types(self) -> list[str]:
        """
        Get a list of file types supported by this analyzer.

        Returns:
            List of supported file extensions
        """
        self._ensure_initialized()
        return sorted(list(self._supported_extensions))

    async def get_supported_content_types(self) -> list[str]:
        """
        Get a list of content types supported by this analyzer.

        Returns:
            List of supported content type identifiers
        """
        self._ensure_initialized()
        return sorted(list(self._supported_content_types))
