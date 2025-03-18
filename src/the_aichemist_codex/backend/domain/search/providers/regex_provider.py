"""
Regex search provider implementation.

This module provides regex-based search capabilities for more advanced
pattern matching in content.
"""

import logging
import re
from re import Match, Pattern
from typing import Any

from the_aichemist_codex.backend.core.exceptions import SearchError
from the_aichemist_codex.backend.core.models import FileMetadata, SearchResult
from the_aichemist_codex.backend.domain.search.providers.base_provider import (
    BaseSearchProvider,
)

logger = logging.getLogger(__name__)


class RegexSearchProvider(BaseSearchProvider):
    """Implements a regex-based search provider."""

    def __init__(self, flags: int = 0):
        """
        Initialize the regex search provider.

        Args:
            flags: Regex compilation flags (re.IGNORECASE, re.MULTILINE, etc.)
        """
        self._flags = flags
        self._content_cache = {}  # Simple in-memory cache of content for searching
        self._compiled_patterns = {}  # Cache for compiled regex patterns
        super().__init__()

    async def _initialize_provider(self) -> None:
        """Initialize the regex search provider."""
        # Nothing special to initialize for regex search
        pass

    async def _close_provider(self) -> None:
        """Close the regex search provider."""
        # Clear caches
        self._content_cache.clear()
        self._compiled_patterns.clear()

    async def _perform_search(
        self, query: str, options: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Perform regex search.

        Args:
            query: The regex pattern to search for
            options: Search options including:
                - flags: Override default regex flags
                - content_types: List of content types to search in
                - max_results: Maximum number of results to return
                - include_content: Whether to include the matched content in results
                - content_preview_length: Length of content preview to include
                - match_whole_word: Whether to match whole words only
                - match_case: Whether to match case
                - match_multiline: Whether to use multiline mode

        Returns:
            List of search results as dictionaries
        """
        try:
            # Process regex options
            pattern, regex_flags = self._prepare_regex(query, options)

            # Get search options
            content_types = options.get("content_types", [])
            max_results = options.get("max_results", 100)
            include_content = options.get("include_content", False)
            preview_length = options.get("content_preview_length", 100)

            # Get content to search through
            content_items = await self._get_searchable_content(content_types)

            # Perform search
            results = []
            for item in content_items:
                item_id = item.get("id")
                item_content = item.get("content", "")
                item_metadata = item.get("metadata", {})

                # Find all matches
                matches = list(pattern.finditer(item_content))

                if matches:
                    # Create search result for each match
                    for i, match in enumerate(matches):
                        result = self._create_search_result(
                            item_id,
                            item_metadata,
                            match,
                            item_content,
                            i,
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

        except re.error as e:
            error_msg = f"Invalid regex pattern: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e
        except Exception as e:
            error_msg = f"Error in regex search: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    def _get_provider_options(self) -> dict[str, Any]:
        """
        Get the options supported by the regex search provider.

        Returns:
            Dictionary of supported options
        """
        return {
            "flags": {
                "type": "integer",
                "description": "Regex compilation flags",
                "default": self._flags,
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
            "match_whole_word": {
                "type": "boolean",
                "description": "Whether to match whole words only",
                "default": False,
            },
            "match_case": {
                "type": "boolean",
                "description": "Whether to match case",
                "default": True,
            },
            "match_multiline": {
                "type": "boolean",
                "description": "Whether to use multiline mode",
                "default": False,
            },
        }

    def _get_provider_type(self) -> str:
        """
        Get the provider type identifier.

        Returns:
            String identifier for this provider type
        """
        return "regex"

    def _prepare_regex(
        self, pattern: str, options: dict[str, Any]
    ) -> tuple[Pattern, int]:
        """
        Prepare regex pattern with appropriate flags.

        Args:
            pattern: The regex pattern string
            options: Search options

        Returns:
            Tuple of (compiled pattern, flags used)

        Raises:
            re.error: If the pattern is invalid
        """
        # Get regex flags
        flags = options.get("flags", self._flags)

        # Apply option-specific flags
        if not options.get("match_case", True):
            flags |= re.IGNORECASE

        if options.get("match_multiline", False):
            flags |= re.MULTILINE

        # Modify pattern if whole word matching is required
        if options.get("match_whole_word", False):
            pattern = r"\b" + pattern + r"\b"

        # Check if pattern is already compiled
        cache_key = f"{pattern}:{flags}"
        if cache_key in self._compiled_patterns:
            return self._compiled_patterns[cache_key], flags

        # Compile pattern
        compiled_pattern = re.compile(pattern, flags)

        # Cache for reuse
        self._compiled_patterns[cache_key] = compiled_pattern

        return compiled_pattern, flags

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
                    "id": "code1",
                    "content": 'def hello_world():\n    print("Hello, world!")\n    return True',
                    "metadata": {
                        "title": "Hello World Function",
                        "type": "code",
                        "path": "/src/hello.py",
                        "created": "2023-01-01T12:00:00Z",
                    },
                },
                {
                    "id": "code2",
                    "content": "class User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email",
                    "metadata": {
                        "title": "User Class",
                        "type": "code",
                        "path": "/src/models.py",
                        "created": "2023-01-02T12:00:00Z",
                    },
                },
                {
                    "id": "doc1",
                    "content": "Email: support@example.com\nPhone: 123-456-7890",
                    "metadata": {
                        "title": "Contact Information",
                        "type": "document",
                        "path": "/docs/contact.txt",
                        "created": "2023-01-03T12:00:00Z",
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

    def _create_search_result(
        self,
        item_id: str,
        metadata: dict[str, Any],
        match: Match,
        content: str,
        match_index: int,
        include_content: bool,
        preview_length: int,
    ) -> dict[str, Any]:
        """
        Create a search result dictionary from a regex match.

        Args:
            item_id: ID of the matched item
            metadata: Item metadata
            match: The regex match object
            content: The full content that was searched
            match_index: Index of this match in the sequence of matches
            include_content: Whether to include full content
            preview_length: Length of content preview to include

        Returns:
            Search result dictionary
        """
        # Get match information
        match_start = match.start()
        match_end = match.end()
        matched_text = match.group(0)

        # Extract context around the match
        start = max(0, match_start - preview_length // 2)
        end = min(len(content), match_end + preview_length // 2)
        context = content[start:end]

        # Collect any named groups
        named_groups = {}
        if match.groupdict():
            named_groups = match.groupdict()

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
            id=f"{item_id}_{match_index}",
            score=1.0,  # Regex matches don't have a relevance score
            file=file_meta,
            match_position=match_start,
            match_context=context,
            matched_terms=[matched_text],
            match_groups=named_groups,  # Store any named capture groups
        )

        # Convert to dictionary
        result_dict = result.to_dict()

        # Add regex-specific fields
        result_dict.update(
            {
                "match_length": match_end - match_start,
                "match_text": matched_text,
                "named_groups": named_groups,
            }
        )

        # Optionally include the full content
        if include_content:
            result_dict["content"] = (
                content[:preview_length] + "..."
                if len(content) > preview_length
                else content
            )

        return result_dict

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

        logger.debug(f"Added content with ID {content_id} to regex search index")

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
            logger.debug(
                f"Removed content with ID {content_id} from regex search index"
            )
        else:
            logger.debug(
                f"Content with ID {content_id} not found in regex search index"
            )

        return removed

    async def clear_index(self) -> None:
        """Clear all content from the search index."""
        self._ensure_initialized()
        self._content_cache.clear()
        self._compiled_patterns.clear()
        logger.debug("Cleared regex search index")
