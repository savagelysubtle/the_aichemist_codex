"""
Regex search provider implementation.

This module provides a search provider that uses regular expressions
for more powerful pattern matching.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ....core.exceptions import SearchError
from ....registry import Registry
from ...search.utils.result_ranking import rank_results
from .base_provider import BaseSearchProvider

logger = logging.getLogger(__name__)


class RegexSearchProvider(BaseSearchProvider):
    """
    Regular expression based search provider.

    This provider performs searches using regular expressions for
    more powerful pattern matching capabilities.
    """

    def __init__(self):
        """Initialize the regex search provider."""
        super().__init__()
        self._registry = Registry.get_instance()
        self._file_cache: dict[str, str] = {}
        self._max_results = 100
        self._max_cache_size = 50  # Maximum number of files to cache

    async def _initialize_provider(self) -> None:
        """Initialize the regex search provider."""
        # Load config if needed
        config = self._registry.config_provider
        self._max_results = config.get_config("search.regex.max_results", 100)
        self._max_cache_size = config.get_config("search.regex.max_cache_size", 50)

    async def _close_provider(self) -> None:
        """Close the regex search provider."""
        # Clear the cache
        self._file_cache.clear()

    async def search(
        self, query: str, options: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Search for regex patterns in files.

        Args:
            query: Regex pattern to search for
            options: Optional search parameters
                - case_sensitive: Whether to perform case-sensitive search (default: False)
                - max_results: Maximum number of results to return (default: 100)
                - paths: List of paths to search in (default: all indexed paths)
                - file_extensions: List of file extensions to search (default: all text files)
                - multiline: Whether to enable multiline matching (default: False)
                - dot_all: Whether dot matches newlines (default: False)

        Returns:
            List of search results, each containing file path, snippet, score, and match info
        """
        self._ensure_initialized()
        options = options or {}

        # Get search options
        case_sensitive = options.get("case_sensitive", False)
        max_results = options.get("max_results", self._max_results)
        paths = options.get("paths", [])
        file_extensions = options.get("file_extensions", [])
        multiline = options.get("multiline", False)
        dot_all = options.get("dot_all", False)

        # Convert paths to list if it's a single string
        if isinstance(paths, str):
            paths = [paths]

        # Prepare the search pattern
        if multiline:
            pattern = r'(?s).*'
        else:
            pattern = re.escape(query)

        flags = 0 if case_sensitive else re.IGNORECASE
        if multiline:
            flags |= re.DOTALL
        if dot_all:
            flags |= re.MULTILINE

        try:
            # Find files to search
            files_to_search = await self._find_files_to_search(paths, file_extensions)

            # Perform the search
            results = []
            for file_path in files_to_search:
                try:
                    # Get file content
                    content = await self._get_file_content(file_path)

                    # Search for matches
                    matches = list(re.finditer(pattern, content, flags))

                    if matches:
                        # Create a result for each match
                        for match in matches[:10]:  # Limit to 10 matches per file
                            # Extract snippet context
                            snippet = self._extract_snippet(content, match.start(), match.end())

                            # Calculate score (simple count-based score for now)
                            score = 1.0 / (len(results) + 1)  # Higher score for first results

                            results.append({
                                "file_path": str(file_path),
                                "snippet": snippet,
                                "score": score,
                                "match_position": match.start(),
                                "match_length": match.end() - match.start()
                            })
                except Exception as e:
                    logger.warning(f"Error searching file {file_path}: {e}")

            # Rank and limit results
            ranked_results = rank_results(results)
            return ranked_results[:max_results]

        except Exception as e:
            logger.error(f"Error in regex search: {e}")
            raise SearchError(
                f"Regex search failed: {e}",
                provider_id=self.get_provider_type(),
                query=query,
                operation="search",
                details={"options": options}
            ) from e

    async def get_supported_options(self) -> dict[str, Any]:
        """
        Get supported options for this search provider.

        Returns:
            Dictionary of supported options and their descriptions
        """
        return {
            "case_sensitive": {
                "type": "boolean",
                "default": False,
                "description": "Whether to perform case-sensitive search"
            },
            "max_results": {
                "type": "integer",
                "default": self._max_results,
                "description": "Maximum number of results to return"
            },
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "List of paths to search in (empty for all)"
            },
            "file_extensions": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "List of file extensions to search (empty for all text files)"
            },
            "multiline": {
                "type": "boolean",
                "default": False,
                "description": "Whether to enable multiline matching"
            },
            "dot_all": {
                "type": "boolean",
                "default": False,
                "description": "Whether dot matches newlines"
            }
        }

    async def get_provider_type(self) -> str:
        """
        Get the type identifier for this search provider.

        Returns:
            Provider type string
        """
        return "regex"

    async def index_file(self, file_path: str, file_type: str = None) -> None:
        """
        Index a file for searching.

        For the regex provider, this simply adds the file to the cache
        if it's a text file.

        Args:
            file_path: Path to the file to index
            file_type: Optional file type hint
        """
        self._ensure_initialized()

        try:
            # Check if the file is a text file
            if not self._is_text_file(file_path):
                return

            # Add to cache if needed
            if len(self._file_cache) < self._max_cache_size:
                await self._get_file_content(file_path)
        except Exception as e:
            logger.warning(f"Error indexing file {file_path}: {e}")

    async def remove_file_from_index(self, file_path: str) -> None:
        """
        Remove a file from the index.

        For the regex provider, this removes the file from the cache.

        Args:
            file_path: Path to the file to remove
        """
        self._ensure_initialized()

        # Remove from cache if present
        if file_path in self._file_cache:
            del self._file_cache[file_path]

    async def _find_files_to_search(
        self, paths: list[str], file_extensions: list[str]
    ) -> list[str]:
        """
        Find files to search based on paths and extensions.

        Args:
            paths: List of paths to search in
            file_extensions: List of file extensions to search

        Returns:
            List of file paths to search
        """
        # Get file manager to find files
        file_manager = self._registry.file_manager

        files_to_search = []

        # If no paths specified, use default search paths
        if not paths:
            # Get project paths
            project_paths = self._registry.project_paths
            paths = [str(project_paths.get_project_root())]

        # Find all files in the specified paths
        for path in paths:
            try:
                # Different behavior based on whether path is file or directory
                path_obj = Path(path)
                if path_obj.is_file():
                    # Single file
                    if self._matches_extensions(path, file_extensions):
                        files_to_search.append(path)
                else:
                    # Directory - walk and find files
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if self._matches_extensions(file_path, file_extensions):
                                files_to_search.append(file_path)
            except Exception as e:
                logger.warning(f"Error finding files in {path}: {e}")

        # Filter to include only text files
        return [file for file in files_to_search if self._is_text_file(file)]

    def _matches_extensions(self, file_path: str, extensions: list[str]) -> bool:
        """
        Check if a file matches the specified extensions.

        Args:
            file_path: Path to the file
            extensions: List of extensions to match (without dot)

        Returns:
            True if the file matches, False otherwise
        """
        # If no extensions specified, match all
        if not extensions:
            return True

        # Get file extension (without dot)
        _, ext = os.path.splitext(file_path)
        ext = ext[1:] if ext.startswith(".") else ext

        # Check if extension matches
        return ext.lower() in [e.lower() for e in extensions]

    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is likely a text file, False otherwise
        """
        # Common text file extensions
        text_extensions = {
            "txt", "md", "markdown", "rst", "py", "js", "ts", "html", "htm", "css",
            "json", "xml", "yaml", "yml", "ini", "toml", "c", "cpp", "h", "hpp",
            "java", "cs", "go", "rs", "sh", "bat", "ps1", "log", "csv", "tsv"
        }

        # Get file extension (without dot)
        _, ext = os.path.splitext(file_path)
        ext = ext[1:] if ext.startswith(".") else ext

        return ext.lower() in text_extensions

    async def _get_file_content(self, file_path: str) -> str:
        """
        Get the content of a file, using cache if available.

        Args:
            file_path: Path to the file

        Returns:
            File content as string
        """
        # Check cache first
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        # Read file content
        file_reader = self._registry.file_reader
        try:
            content = await file_reader.read_text(file_path)

            # Update cache
            if len(self._file_cache) >= self._max_cache_size:
                # Remove a random entry if cache is full
                self._file_cache.pop(next(iter(self._file_cache)))

            self._file_cache[file_path] = content
            return content
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return ""

    def _extract_snippet(self, content: str, match_start: int, match_end: int, context_size: int = 50) -> str:
        """
        Extract a snippet of text around a match.

        Args:
            content: The full content string
            match_start: Start position of the match
            match_end: End position of the match
            context_size: Number of characters to include before and after match

        Returns:
            Snippet of text with context around the match
        """
        # Calculate snippet range
        start = max(0, match_start - context_size)
        end = min(len(content), match_end + context_size)

        # Extract the snippet
        snippet = content[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
