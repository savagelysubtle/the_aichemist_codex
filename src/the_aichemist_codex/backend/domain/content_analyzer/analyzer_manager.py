"""
Content Analyzer Manager for AIChemist Codex.

This module provides the implementation of the ContentAnalyzerManager,
which coordinates different content analyzers and delegates analysis tasks.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from the_aichemist_codex.backend.core.exceptions.exceptions import AnalysisError
from the_aichemist_codex.backend.core.interfaces.interfaces import (
    ContentAnalyzer,
    FileReader,
)

logger = logging.getLogger(__name__)


class ContentAnalyzerManager(ContentAnalyzer):
    """
    Manager for coordinating multiple content analyzers.

    This class manages a collection of specialized content analyzers
    and delegates analysis requests to the appropriate analyzer based
    on the file type or content.
    """

    def __init__(
        self, file_reader: FileReader, analyzers: list[ContentAnalyzer] | None = None
    ) -> None:
        """
        Initialize the ContentAnalyzerManager.

        Args:
            file_reader: File reader service for accessing file content
            analyzers: Optional list of ContentAnalyzer instances to manage
        """
        self._file_reader = file_reader
        self._analyzers: list[ContentAnalyzer] = analyzers or []
        self._default_analyzer: ContentAnalyzer | None = None
        self._initialized = False

        # Maps for efficient lookup
        self._extension_map: dict[str, ContentAnalyzer] = {}
        self._content_type_map: dict[str, ContentAnalyzer] = {}

    async def initialize(self) -> None:
        """
        Initialize the content analyzer manager and all managed analyzers.

        Raises:
            AnalysisError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Initialize each analyzer
            for analyzer in self._analyzers:
                await analyzer.initialize()

                # Register supported file types
                for ext in await analyzer.get_supported_file_types():
                    self._extension_map[ext.lower()] = analyzer

                # Register supported content types
                for content_type in await analyzer.get_supported_content_types():
                    self._content_type_map[content_type.lower()] = analyzer

            # Set default analyzer if available
            if self._analyzers:
                self._default_analyzer = self._analyzers[0]

            self._initialized = True
            logger.info("ContentAnalyzerManager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ContentAnalyzerManager: {e}")
            raise AnalysisError(
                f"Failed to initialize ContentAnalyzerManager: {e}"
            ) from e

    def _ensure_initialized(self) -> None:
        """
        Ensure the manager is initialized.

        Raises:
            AnalysisError: If the manager is not initialized
        """
        if not self._initialized:
            raise AnalysisError("ContentAnalyzerManager is not initialized")

    def add_analyzer(self, analyzer: ContentAnalyzer) -> None:
        """
        Add a new content analyzer to the manager.

        If the manager is already initialized, the new analyzer will
        be initialized and its supported types registered.

        Args:
            analyzer: ContentAnalyzer instance to add

        Raises:
            AnalysisError: If adding the analyzer fails
        """
        self._analyzers.append(analyzer)

        # Initialize and register if manager is already initialized
        if self._initialized:
            try:
                # Initialize the analyzer
                asyncio.run(analyzer.initialize())

                # Register supported file types
                for ext in asyncio.run(analyzer.get_supported_file_types()):
                    self._extension_map[ext.lower()] = analyzer

                # Register supported content types
                for content_type in asyncio.run(analyzer.get_supported_content_types()):
                    self._content_type_map[content_type.lower()] = analyzer

            except Exception as e:
                logger.error(f"Failed to add analyzer: {e}")
                raise AnalysisError(f"Failed to add analyzer: {e}") from e

    def remove_analyzer(self, analyzer: ContentAnalyzer) -> None:
        """
        Remove a content analyzer from the manager.

        Args:
            analyzer: ContentAnalyzer instance to remove
        """
        if analyzer in self._analyzers:
            self._analyzers.remove(analyzer)

            # Update mappings
            self._extension_map = {
                ext: ana
                for ext, ana in self._extension_map.items()
                if ana is not analyzer
            }

            self._content_type_map = {
                ct: ana
                for ct, ana in self._content_type_map.items()
                if ana is not analyzer
            }

            # Update default analyzer if needed
            if self._default_analyzer is analyzer:
                self._default_analyzer = self._analyzers[0] if self._analyzers else None

    def _find_analyzer_for_file(
        self, file_path: Path, content_type: str | None = None
    ) -> ContentAnalyzer:
        """
        Find an appropriate analyzer for the given file.

        Args:
            file_path: Path to the file to analyze
            content_type: Optional content type hint

        Returns:
            The most appropriate ContentAnalyzer

        Raises:
            AnalysisError: If no suitable analyzer is found
        """
        self._ensure_initialized()

        if not self._analyzers:
            raise AnalysisError("No content analyzers available")

        # Try to find analyzer by content type if provided
        if content_type and content_type.lower() in self._content_type_map:
            return self._content_type_map[content_type.lower()]

        # Try to find analyzer by file extension
        ext = file_path.suffix.lower().lstrip(".")
        if ext in self._extension_map:
            return self._extension_map[ext]

        # Use default analyzer if available
        if self._default_analyzer:
            return self._default_analyzer

        # No suitable analyzer found
        raise AnalysisError(
            f"No suitable analyzer found for file {file_path}",
            file_path=str(file_path),
            content_type=content_type,
        )

    def _find_analyzer_for_content(
        self, content_type: str | None = None
    ) -> ContentAnalyzer:
        """
        Find an appropriate analyzer for the given content type.

        Args:
            content_type: Optional content type hint

        Returns:
            The most appropriate ContentAnalyzer

        Raises:
            AnalysisError: If no suitable analyzer is found
        """
        self._ensure_initialized()

        if not self._analyzers:
            raise AnalysisError("No content analyzers available")

        # Try to find analyzer by content type if provided
        if content_type and content_type.lower() in self._content_type_map:
            return self._content_type_map[content_type.lower()]

        # Use default analyzer if available
        if self._default_analyzer:
            return self._default_analyzer

        # No suitable analyzer found
        raise AnalysisError(
            f"No suitable analyzer found for content type {content_type}",
            content_type=content_type,
        )

    async def analyze_file(
        self,
        file_path: Path,
        content_type: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a file and extract meaningful information.

        This implementation delegates to the appropriate analyzer based
        on the file type or provided content type.

        Args:
            file_path: Path to the file to analyze
            content_type: Optional hint about the file's content type
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If analysis fails or no suitable analyzer is found
        """
        analyzer = self._find_analyzer_for_file(file_path, content_type)
        return await analyzer.analyze_file(file_path, content_type, options)

    async def analyze_text(
        self,
        text: str,
        content_type: str | None = None,
        file_path: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze text content and extract meaningful information.

        This implementation delegates to the appropriate analyzer based
        on the provided content type.

        Args:
            text: The text content to analyze
            content_type: Optional hint about the content type
            file_path: Optional path to the source file (for context)
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            AnalysisError: If analysis fails or no suitable analyzer is found
        """
        analyzer = self._find_analyzer_for_content(content_type)
        return await analyzer.analyze_text(text, content_type, file_path, options)

    async def summarize(
        self, content: str | Path, max_length: int = 500, output_format: str = "text"
    ) -> str:
        """
        Generate a summary of file content.

        This implementation delegates to the appropriate analyzer based
        on the provided content.

        Args:
            content: Either a string of content or a path to a file
            max_length: Maximum length of the summary in characters
            output_format: Output format (e.g., "text", "html", "markdown")

        Returns:
            Generated summary as a string

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If summarization fails or no suitable analyzer is found
        """
        if isinstance(content, Path) or (
            isinstance(content, str) and Path(content).exists()
        ):
            file_path = Path(content) if isinstance(content, str) else content
            analyzer = self._find_analyzer_for_file(file_path)
        else:
            analyzer = self._find_analyzer_for_content()

        return await analyzer.summarize(content, max_length, output_format)

    async def extract_entities(
        self,
        content: str | Path,
        entity_types: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract named entities from content.

        This implementation delegates to the appropriate analyzer based
        on the provided content.

        Args:
            content: Either a string of content or a path to a file
            entity_types: Types of entities to extract (e.g., "person", "organization")
            min_confidence: Minimum confidence score for extracted entities

        Returns:
            Dictionary mapping entity types to lists of extracted entities

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If entity extraction fails or no suitable analyzer is found
        """
        if isinstance(content, Path) or (
            isinstance(content, str) and Path(content).exists()
        ):
            file_path = Path(content) if isinstance(content, str) else content
            analyzer = self._find_analyzer_for_file(file_path)
        else:
            analyzer = self._find_analyzer_for_content()

        return await analyzer.extract_entities(content, entity_types, min_confidence)

    async def extract_keywords(
        self, content: str | Path, max_keywords: int = 10, min_relevance: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Extract keywords or key phrases from content.

        This implementation delegates to the appropriate analyzer based
        on the provided content.

        Args:
            content: Either a string of content or a path to a file
            max_keywords: Maximum number of keywords to extract
            min_relevance: Minimum relevance score for keywords

        Returns:
            List of dictionaries containing keywords and their relevance scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If keyword extraction fails or no suitable analyzer is found
        """
        if isinstance(content, Path) or (
            isinstance(content, str) and Path(content).exists()
        ):
            file_path = Path(content) if isinstance(content, str) else content
            analyzer = self._find_analyzer_for_file(file_path)
        else:
            analyzer = self._find_analyzer_for_content()

        return await analyzer.extract_keywords(content, max_keywords, min_relevance)

    async def classify_content(
        self,
        content: str | Path,
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Classify content into categories.

        This implementation delegates to the appropriate analyzer based
        on the provided content.

        Args:
            content: Either a string of content or a path to a file
            taxonomy: Optional list of categories to use
            min_confidence: Minimum confidence score for classifications

        Returns:
            List of dictionaries containing categories and confidence scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If classification fails or no suitable analyzer is found
        """
        if isinstance(content, Path) or (
            isinstance(content, str) and Path(content).exists()
        ):
            file_path = Path(content) if isinstance(content, str) else content
            analyzer = self._find_analyzer_for_file(file_path)
        else:
            analyzer = self._find_analyzer_for_content()

        return await analyzer.classify_content(content, taxonomy, min_confidence)

    async def get_supported_file_types(self) -> list[str]:
        """
        Get a list of file types supported by all analyzers.

        Returns:
            List of supported file extensions
        """
        self._ensure_initialized()
        return sorted(list(self._extension_map.keys()))

    async def get_supported_content_types(self) -> list[str]:
        """
        Get a list of content types supported by all analyzers.

        Returns:
            List of supported content type identifiers
        """
        self._ensure_initialized()
        return sorted(list(self._content_type_map.keys()))
