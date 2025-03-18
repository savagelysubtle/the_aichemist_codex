"""
Text search provider implementation.

This module provides a basic text search capability using simple string matching
techniques for searching through content.
"""

import logging
from typing import Any

from the_aichemist_codex.backend.core.models import FileMetadata, SearchResult
from the_aichemist_codex.backend.domain.search.providers.base_provider import (
    BaseSearchProvider,
)

logger = logging.getLogger(__name__)


class TextSearchProvider(BaseSearchProvider):
    """Implements a simple text search provider."""

    def __init__(self, case_sensitive: bool = False):
        """
        Initialize the text search provider.

        Args:
            case_sensitive: Whether to perform case-sensitive search
        """
        self._case_sensitive = case_sensitive
        self._content_cache = {}  # Simple in-memory cache of content for searching
        super().__init__()

    async def _initialize_provider(self) -> None:
        """Initialize the text search provider."""
        # Nothing special to initialize for basic text search
        pass

    async def _close_provider(self) -> None:
        """Close the text search provider."""
        # Clear any cached content
        self._content_cache.clear()

    async def _perform_search(
        self, query: str, options: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Perform text search.

        Args:
            query: The text to search for
            options: Search options including:
                - case_sensitive: Override default case sensitivity
                - content_types: List of content types to search in
                - max_results: Maximum number of results to return
                - include_content: Whether to include the matched content in results
                - content_preview_length: Length of content preview to include

        Returns:
            List of search results as dictionaries
        """
        # Get search options
        case_sensitive = options.get("case_sensitive", self._case_sensitive)
        content_types = options.get("content_types", [])
        max_results = options.get("max_results", 100)
        include_content = options.get("include_content", False)
        preview_length = options.get("content_preview_length", 100)

        # Get content to search through (in a real implementation, this would
        # likely query a database or file system)
        content_items = await self._get_searchable_content(content_types)

        # Prepare query
        search_query = query if case_sensitive else query.lower()

        # Perform search
        results = []
        for item in content_items:
            item_id = item.get("id")
            item_content = item.get("content", "")
            item_metadata = item.get("metadata", {})

            # Prepare content for matching
            match_content = item_content if case_sensitive else item_content.lower()

            # Find all matches
            matches = self._find_matches(match_content, search_query)

            if matches:
                # Create search result for each match
                for match_position, context in matches:
                    result = self._create_search_result(
                        item_id,
                        item_metadata,
                        match_position,
                        context,
                        include_content,
                        preview_length,
                    )
                    results.append(result)

                    # Respect max results limit
                    if len(results) >= max_results:
                        logger.debug(f"Reached max results limit ({max_results})")
                        break

            # Respect max results limit
            if len(results) >= max_results:
                break

        return results

    def _get_provider_options(self) -> dict[str, Any]:
        """
        Get the options supported by the text search provider.

        Returns:
            Dictionary of supported options
        """
        return {
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether to perform case-sensitive search",
                "default": self._case_sensitive,
            },
            "content_types": {
                "type": "array",
                "description": "List of content types to search in",
                "default": [],
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 100,
            },
            "include_content": {
                "type": "boolean",
                "description": "Whether to include the matched content in results",
                "default": False,
            },
            "content_preview_length": {
                "type": "integer",
                "description": "Length of content preview to include",
                "default": 100,
            },
        }

    def _get_provider_type(self) -> str:
        """
        Get the provider type identifier.

        Returns:
            String identifier for this provider type
        """
        return "text"

    async def _get_searchable_content(
        self, content_types: list[str]
    ) -> list[dict[str, Any]]:
        """
        Get content that can be searched through.

        In a real implementation, this would query a database or file system.
        For this example, we return mock data.

        Args:
            content_types: List of content types to filter by

        Returns:
            List of content items with their metadata
        """
        # In a real implementation, this would fetch content from a database or files
        # For now, we'll return some mock data if the cache is empty
        if not self._content_cache:
            # Mock some content for demonstration purposes
            self._content_cache = [
                {
                    "id": "doc1",
                    "content": "This is a sample document about AI and machine learning.",
                    "metadata": {
                        "title": "AI Introduction",
                        "type": "document",
                        "path": "/docs/ai-intro.txt",
                        "created": "2023-01-01T12:00:00Z",
                    },
                },
                {
                    "id": "doc2",
                    "content": "Python is a versatile programming language used in data science.",
                    "metadata": {
                        "title": "Python Overview",
                        "type": "document",
                        "path": "/docs/python.txt",
                        "created": "2023-01-02T12:00:00Z",
                    },
                },
            ]

        # Filter by content types if specified
        if content_types:
            return [
                item
                for item in self._content_cache
                if item.get("metadata", {}).get("type") in content_types
            ]

        return self._content_cache

    def _find_matches(self, content: str, query: str) -> list[tuple[int, str]]:
        """
        Find all matches of the query in the content.

        Args:
            content: The content to search in
            query: The search query

        Returns:
            List of tuples (position, context) for each match
        """
        matches = []
        position = 0

        while True:
            position = content.find(query, position)
            if position == -1:
                break

            # Extract context around the match
            start = max(0, position - 50)
            end = min(len(content), position + len(query) + 50)
            context = content[start:end]

            matches.append((position, context))
            position += len(query)

        return matches

    def _create_search_result(
        self,
        item_id: str,
        metadata: dict[str, Any],
        match_position: int,
        context: str,
        include_content: bool,
        preview_length: int,
    ) -> dict[str, Any]:
        """
        Create a search result dictionary.

        Args:
            item_id: ID of the matched item
            metadata: Item metadata
            match_position: Position of the match in the content
            context: Context around the match
            include_content: Whether to include full content
            preview_length: Length of content preview

        Returns:
            Search result dictionary
        """
        # Create a file metadata object from the metadata dictionary
        file_meta = FileMetadata(
            id=metadata.get("id", item_id),
            name=metadata.get("title", ""),
            path=metadata.get("path", ""),
            size=metadata.get("size", 0),
            created_time=metadata.get("created", ""),
            modified_time=metadata.get("modified", ""),
            content_type=metadata.get("type", ""),
            metadata=metadata,
        )

        # Create the search result
        result = SearchResult(
            id=f"{item_id}_{match_position}",
            score=1.0,  # Simple matching has no relevance score
            file=file_meta,
            match_position=match_position,
            match_context=context,
            matched_terms=[],  # Not tracking specific terms in simple text search
        )

        # Convert to dictionary for the API
        return result.to_dict()

    async def add_content(
        self, content_id: str, content: str, metadata: dict[str, Any]
    ) -> None:
        """
        Add content to the search index.

        Args:
            content_id: Unique identifier for the content
            content: The content text
            metadata: Content metadata
        """
        self._ensure_initialized()

        # Add to in-memory cache
        self._content_cache.append(
            {"id": content_id, "content": content, "metadata": metadata}
        )

        logger.debug(f"Added content with ID {content_id} to text search index")

    async def remove_content(self, content_id: str) -> bool:
        """
        Remove content from the search index.

        Args:
            content_id: Unique identifier for the content to remove

        Returns:
            True if content was removed, False if not found
        """
        self._ensure_initialized()

        initial_length = len(self._content_cache)
        self._content_cache = [
            item for item in self._content_cache if item.get("id") != content_id
        ]

        removed = len(self._content_cache) < initial_length
        if removed:
            logger.debug(f"Removed content with ID {content_id} from text search index")
        else:
            logger.debug(f"Content with ID {content_id} not found in text search index")

        return removed

    async def clear_index(self) -> None:
        """Clear all content from the search index."""
        self._ensure_initialized()
        self._content_cache.clear()
        logger.debug("Cleared text search index")
