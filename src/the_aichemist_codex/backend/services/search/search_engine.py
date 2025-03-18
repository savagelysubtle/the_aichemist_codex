"""
Implementation of the search engine service.

This module provides functionality for searching through files using
various search algorithms, leveraging the registry pattern to avoid
circular dependencies.
"""

import os
import re
from pathlib import Path

from ...core.constants import SEARCH_SCORE_THRESHOLD, SNIPPET_LENGTH
from ...core.exceptions import SearchError
from ...core.interfaces import SearchEngine as SearchEngineInterface
from ...core.models import SearchResult
from ...core.utils import extract_text_snippet
from ...registry import Registry


class SearchEngine(SearchEngineInterface):
    """
    Search engine for finding content in files.

    This class provides functionality for searching through files using
    various search algorithms, leveraging the registry pattern to avoid
    circular dependencies.
    """

    def __init__(self):
        """Initialize the SearchEngine instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator
        self._async_io = self._registry.async_io
        self._cache = self._registry.cache_manager
        self._metadata_manager = self._registry.metadata_manager

        # Extensions supported for full-text search
        self._searchable_extensions: set[str] = {
            # Text files
            "txt",
            "md",
            "rst",
            "log",
            # Code files
            "py",
            "js",
            "html",
            "css",
            "json",
            "xml",
            "yaml",
            "yml",
            "ini",
            "toml",
            # Document files (plain text only)
            "csv",
            "tsv",
        }

        # Cache directory for search indexes
        self._search_dir = self._paths.get_cache_dir() / "search"
        os.makedirs(self._search_dir, exist_ok=True)

    async def simple_search(
        self,
        query: str,
        directories: list[str] = None,
        file_extensions: list[str] = None,
        max_results: int = 10,
        case_sensitive: bool = False,
    ) -> list[SearchResult]:
        """
        Perform a simple text search across files.

        Args:
            query: The search query
            directories: List of directories to search in (defaults to project root)
            file_extensions: List of file extensions to search (defaults to all searchable)
            max_results: Maximum number of results to return
            case_sensitive: Whether the search should be case sensitive

        Returns:
            List of search results

        Raises:
            SearchError: If there is an error during search
        """
        try:
            # Validate query
            if not query or len(query.strip()) == 0:
                raise SearchError("Search query cannot be empty")

            # Validate and normalize directories
            search_dirs = []
            if directories:
                for dir_path in directories:
                    # Ensure the directory path is safe
                    self._validator.ensure_path_safe(dir_path)
                    path_obj = self._paths.resolve_path(dir_path)

                    if not path_obj.exists() or not path_obj.is_dir():
                        raise SearchError(f"Directory does not exist: {dir_path}")

                    search_dirs.append(path_obj)
            else:
                # Default to project root
                search_dirs.append(self._paths.get_project_root())

            # Normalize file extensions
            search_extensions = set()
            if file_extensions:
                for ext in file_extensions:
                    # Remove leading dot if present
                    ext = ext.lower().lstrip(".")
                    if ext in self._searchable_extensions:
                        search_extensions.add(ext)
            else:
                search_extensions = self._searchable_extensions

            # Prepare search query
            if not case_sensitive:
                query = query.lower()

            # Start search
            results = []

            for directory in search_dirs:
                # Get all files recursively
                files = await self._get_all_files(directory, search_extensions)

                for file_path in files:
                    if len(results) >= max_results:
                        break

                    # Skip files that are too large (will be handled by indexed search)
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > 1024 * 1024:  # Skip files larger than 1MB
                            continue
                    except Exception:
                        continue

                    # Read file content
                    try:
                        content = await self._async_io.read_file(str(file_path))

                        # Search in content
                        if not case_sensitive:
                            content_to_search = content.lower()
                        else:
                            content_to_search = content

                        if query in content_to_search:
                            # Calculate score based on frequency and position
                            score = self._calculate_score(content_to_search, query)

                            if score >= SEARCH_SCORE_THRESHOLD:
                                # Get snippet
                                snippet = extract_text_snippet(
                                    content, query, SNIPPET_LENGTH
                                )

                                # Get title (first try metadata, then fallback to filename)
                                title = None
                                try:
                                    metadata = (
                                        await self._metadata_manager.get_metadata(
                                            str(file_path)
                                        )
                                    )
                                    title = metadata.title
                                except Exception:
                                    pass

                                if not title:
                                    title = file_path.name

                                # Add to results
                                results.append(
                                    SearchResult(
                                        file_path=str(file_path),
                                        score=score,
                                        title=title,
                                        snippet=snippet,
                                        metadata={
                                            "matches": content_to_search.count(query)
                                        },
                                    )
                                )
                    except Exception:
                        # Skip files that can't be read
                        continue

            # Sort results by score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:max_results]

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Error during search: {str(e)}", query)

    async def regex_search(
        self,
        pattern: str,
        directories: list[str] = None,
        file_extensions: list[str] = None,
        max_results: int = 10,
        case_sensitive: bool = False,
    ) -> list[SearchResult]:
        """
        Perform a regex search across files.

        Args:
            pattern: The regex pattern to search for
            directories: List of directories to search in (defaults to project root)
            file_extensions: List of file extensions to search (defaults to all searchable)
            max_results: Maximum number of results to return
            case_sensitive: Whether the search should be case sensitive

        Returns:
            List of search results

        Raises:
            SearchError: If there is an error during search
        """
        try:
            # Validate pattern
            if not pattern or len(pattern.strip()) == 0:
                raise SearchError("Search pattern cannot be empty")

            # Compile regex
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except Exception as e:
                raise SearchError(f"Invalid regex pattern: {str(e)}", pattern)

            # Validate and normalize directories
            search_dirs = []
            if directories:
                for dir_path in directories:
                    # Ensure the directory path is safe
                    self._validator.ensure_path_safe(dir_path)
                    path_obj = self._paths.resolve_path(dir_path)

                    if not path_obj.exists() or not path_obj.is_dir():
                        raise SearchError(f"Directory does not exist: {dir_path}")

                    search_dirs.append(path_obj)
            else:
                # Default to project root
                search_dirs.append(self._paths.get_project_root())

            # Normalize file extensions
            search_extensions = set()
            if file_extensions:
                for ext in file_extensions:
                    # Remove leading dot if present
                    ext = ext.lower().lstrip(".")
                    if ext in self._searchable_extensions:
                        search_extensions.add(ext)
            else:
                search_extensions = self._searchable_extensions

            # Start search
            results = []

            for directory in search_dirs:
                # Get all files recursively
                files = await self._get_all_files(directory, search_extensions)

                for file_path in files:
                    if len(results) >= max_results:
                        break

                    # Skip files that are too large
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > 1024 * 1024:  # Skip files larger than 1MB
                            continue
                    except Exception:
                        continue

                    # Read file content
                    try:
                        content = await self._async_io.read_file(str(file_path))

                        # Search with regex
                        matches = list(regex.finditer(content))

                        if matches:
                            # Calculate score based on number of matches
                            score = min(1.0, len(matches) / 10.0)  # Max score of 1.0

                            if score >= SEARCH_SCORE_THRESHOLD:
                                # Get snippet from first match
                                match_pos = matches[0].start()
                                match_text = matches[0].group(0)
                                snippet_start = max(0, match_pos - SNIPPET_LENGTH // 2)
                                snippet_end = min(
                                    len(content),
                                    match_pos + len(match_text) + SNIPPET_LENGTH // 2,
                                )
                                snippet = content[snippet_start:snippet_end]

                                # Add ellipsis if needed
                                if snippet_start > 0:
                                    snippet = "..." + snippet
                                if snippet_end < len(content):
                                    snippet = snippet + "..."

                                # Get title (first try metadata, then fallback to filename)
                                title = None
                                try:
                                    metadata = (
                                        await self._metadata_manager.get_metadata(
                                            str(file_path)
                                        )
                                    )
                                    title = metadata.title
                                except Exception:
                                    pass

                                if not title:
                                    title = file_path.name

                                # Add to results
                                results.append(
                                    SearchResult(
                                        file_path=str(file_path),
                                        score=score,
                                        title=title,
                                        snippet=snippet,
                                        metadata={"matches": len(matches)},
                                    )
                                )
                    except Exception:
                        # Skip files that can't be read
                        continue

            # Sort results by score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:max_results]

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Error during regex search: {str(e)}", pattern)

    async def metadata_search(
        self, query: str, file_extensions: list[str] = None, max_results: int = 10
    ) -> list[SearchResult]:
        """
        Search for files by metadata.

        Args:
            query: The search query
            file_extensions: List of file extensions to search
            max_results: Maximum number of results to return

        Returns:
            List of search results

        Raises:
            SearchError: If there is an error during search
        """
        try:
            # Search in metadata
            metadata_results = await self._metadata_manager.search_metadata(
                query=query, file_extensions=file_extensions, limit=max_results
            )

            # Convert to search results
            results = []
            for metadata in metadata_results:
                # Create a snippet from description or first few lines of the file
                snippet = None
                if metadata.description:
                    snippet = metadata.description
                else:
                    try:
                        content = await self._async_io.read_file(metadata.path)
                        snippet = "\n".join(content.split("\n")[:3])
                    except Exception:
                        pass

                results.append(
                    SearchResult(
                        file_path=metadata.path,
                        score=0.9,  # High score for metadata matches
                        title=metadata.title or metadata.filename,
                        snippet=snippet,
                        metadata={
                            "size": metadata.size,
                            "type": metadata.content_type,
                            "modified": metadata.modified_time.isoformat(),
                        },
                    )
                )

            return results

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Error during metadata search: {str(e)}", query)

    async def combined_search(
        self,
        query: str,
        directories: list[str] = None,
        file_extensions: list[str] = None,
        max_results: int = 20,
        case_sensitive: bool = False,
    ) -> list[SearchResult]:
        """
        Perform a combined search using multiple search methods.

        Args:
            query: The search query
            directories: List of directories to search in
            file_extensions: List of file extensions to search
            max_results: Maximum number of results to return
            case_sensitive: Whether the search should be case sensitive

        Returns:
            List of search results

        Raises:
            SearchError: If there is an error during search
        """
        # Get results from different search methods
        metadata_results = await self.metadata_search(
            query=query, file_extensions=file_extensions, max_results=max_results // 2
        )

        content_results = await self.simple_search(
            query=query,
            directories=directories,
            file_extensions=file_extensions,
            max_results=max_results,
            case_sensitive=case_sensitive,
        )

        # Combine results, removing duplicates
        combined_results = []
        seen_paths = set()

        # Add metadata results first (they usually have higher quality)
        for result in metadata_results:
            combined_results.append(result)
            seen_paths.add(result.file_path)

        # Add content results, skipping duplicates
        for result in content_results:
            if result.file_path not in seen_paths:
                combined_results.append(result)
                seen_paths.add(result.file_path)

        # Sort by score and limit to max_results
        combined_results.sort(key=lambda x: x.score, reverse=True)
        return combined_results[:max_results]

    async def _get_all_files(self, directory: Path, extensions: set[str]) -> list[Path]:
        """
        Get all files recursively from a directory with specific extensions.

        Args:
            directory: The directory to search in
            extensions: Set of file extensions to include

        Returns:
            List of file paths
        """
        files = []

        for item in directory.glob("**/*"):
            if item.is_file():
                # Check if the file has a valid extension
                ext = item.suffix.lower().lstrip(".")
                if ext in extensions:
                    files.append(item)

        return files

    def _calculate_score(self, content: str, query: str) -> float:
        """
        Calculate a search score based on content and query.

        Args:
            content: The content to search in
            query: The search query

        Returns:
            Search score between 0.0 and 1.0
        """
        # Basic scoring based on number of occurrences
        occurrences = content.count(query)
        if occurrences == 0:
            return 0.0

        # Higher score for more occurrences, but with diminishing returns
        frequency_score = min(0.6, occurrences / 20.0)

        # Higher score for matches that occur earlier in the content
        position = content.find(query)
        position_score = 0.4 * (1.0 - min(1.0, position / 1000.0))

        return frequency_score + position_score
