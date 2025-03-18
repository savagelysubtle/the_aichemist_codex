"""
Index manager implementation.

This module provides functionality to manage search indexes, add or remove content
from search indexes, and maintain the search infrastructure.
"""

import logging
import os
from typing import Any

from the_aichemist_codex.backend.core.exceptions import SearchError
from the_aichemist_codex.backend.core.interfaces import (
    FileManager,
    IndexManager,
    SearchEngine,
    SearchProvider,
)

logger = logging.getLogger(__name__)


class IndexManagerImpl(IndexManager):
    """Implementation of the index manager."""

    def __init__(
        self, search_engine: SearchEngine, file_manager: FileManager | None = None
    ):
        """
        Initialize the index manager.

        Args:
            search_engine: The search engine instance
            file_manager: Optional file manager for scanning files
        """
        self._search_engine = search_engine
        self._file_manager = file_manager
        self._initialized = False
        self._indexable_types = set(
            [
                ".txt",
                ".md",
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".csv",
                ".log",
                ".yml",
                ".yaml",
                ".toml",
                ".ini",
                ".cfg",
                ".java",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".ts",
                ".rst",
                ".adoc",
            ]
        )

    async def initialize(self) -> None:
        """
        Initialize the index manager.

        Raises:
            SearchError: If initialization fails
        """
        if self._initialized:
            logger.debug("Index manager already initialized")
            return

        try:
            logger.info("Initializing index manager")
            self._initialized = True
            logger.info("Index manager initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize index manager: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def close(self) -> None:
        """
        Close the index manager.

        Raises:
            SearchError: If closing fails
        """
        if not self._initialized:
            logger.debug("Index manager not initialized")
            return

        try:
            logger.info("Closing index manager")
            self._initialized = False
            logger.info("Index manager closed successfully")
        except Exception as e:
            error_msg = f"Failed to close index manager: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def index_file(
        self, file_path: str, provider_ids: list[str] | None = None
    ) -> dict[str, bool]:
        """
        Index a single file with the specified providers.

        Args:
            file_path: Path to the file to index
            provider_ids: IDs of providers to use, or None for all

        Returns:
            Dictionary mapping provider IDs to success status

        Raises:
            SearchError: If indexing fails
        """
        self._ensure_initialized()

        try:
            # Check if file exists and is readable
            if not os.path.isfile(file_path):
                raise SearchError(f"File not found: {file_path}")

            if not os.access(file_path, os.R_OK):
                raise SearchError(f"File not readable: {file_path}")

            # Get file metadata and content
            file_id = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()

            # Skip unsupported file types
            if file_extension not in self._indexable_types:
                logger.warning(f"Skipping unsupported file type: {file_extension}")
                return {}

            # Read file content
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Create metadata
            metadata = {
                "path": file_path,
                "title": os.path.basename(file_path),
                "type": file_extension.lstrip("."),
                "size": os.path.getsize(file_path),
                "created": os.path.getctime(file_path),
                "modified": os.path.getmtime(file_path),
            }

            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for indexing")
                return {}

            # Index the file with each provider
            results = {}

            for provider_id, provider in available_providers.items():
                try:
                    # Check if the provider supports this content type
                    provider_options = await provider.get_supported_options()
                    supported_types = provider_options.get("content_types", {}).get(
                        "default", []
                    )

                    if supported_types and metadata["type"] not in supported_types:
                        logger.warning(
                            f"Provider {provider_id} does not support content type {metadata['type']}"
                        )
                        results[provider_id] = False
                        continue

                    # Add the file to the provider's index
                    await self._add_to_index(provider, file_id, content, metadata)
                    results[provider_id] = True
                    logger.info(f"Indexed file {file_path} with provider {provider_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to index file {file_path} with provider {provider_id}: {e}"
                    )
                    results[provider_id] = False

            return results

        except Exception as e:
            error_msg = f"Failed to index file {file_path}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def index_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        provider_ids: list[str] | None = None,
        file_types: list[str] | None = None,
    ) -> dict[str, dict[str, int]]:
        """
        Index all files in a directory.

        Args:
            directory_path: Path to the directory to index
            recursive: Whether to index subdirectories
            provider_ids: IDs of providers to use, or None for all
            file_types: File extensions to index, or None for all indexable types

        Returns:
            Dictionary mapping provider IDs to statistics (indexed, failed)

        Raises:
            SearchError: If indexing fails
        """
        self._ensure_initialized()

        try:
            # Check if directory exists
            if not os.path.isdir(directory_path):
                raise SearchError(f"Directory not found: {directory_path}")

            logger.info(f"Indexing directory: {directory_path}")

            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for indexing")
                return {}

            # Process file types
            indexable_types = None
            if file_types:
                # Convert to normalized set (with leading dots)
                indexable_types = set(
                    [ext if ext.startswith(".") else f".{ext}" for ext in file_types]
                )
                logger.info(f"Filtering to file types: {indexable_types}")
            else:
                # Use default indexable types
                indexable_types = self._indexable_types

            # Initialize results
            results = {
                provider_id: {"indexed": 0, "failed": 0}
                for provider_id in available_providers
            }

            # Walk directory
            for root, dirs, files in os.walk(directory_path):
                # Process each file
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_extension = os.path.splitext(filename)[1].lower()

                    # Skip if not an indexable type
                    if file_extension not in indexable_types:
                        continue

                    try:
                        # Index the file
                        file_results = await self.index_file(
                            file_path, list(available_providers.keys())
                        )

                        # Update statistics
                        for provider_id, success in file_results.items():
                            if success:
                                results[provider_id]["indexed"] += 1
                            else:
                                results[provider_id]["failed"] += 1
                    except Exception as e:
                        logger.error(f"Failed to index file {file_path}: {e}")
                        # Update failure statistics for all providers
                        for provider_id in available_providers:
                            results[provider_id]["failed"] += 1

                # Stop if not recursive
                if not recursive:
                    break

            logger.info(f"Completed indexing directory {directory_path}")
            return results

        except Exception as e:
            error_msg = f"Failed to index directory {directory_path}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def remove_from_index(
        self, file_path: str, provider_ids: list[str] | None = None
    ) -> dict[str, bool]:
        """
        Remove a file from the index.

        Args:
            file_path: Path to the file to remove
            provider_ids: IDs of providers to use, or None for all

        Returns:
            Dictionary mapping provider IDs to success status

        Raises:
            SearchError: If removal fails
        """
        self._ensure_initialized()

        try:
            # Generate file ID
            file_id = os.path.basename(file_path)

            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for removing from index")
                return {}

            # Remove the file from each provider's index
            results = {}

            for provider_id, provider in available_providers.items():
                try:
                    # Check if the provider has a remove_content method
                    if hasattr(provider, "remove_content") and callable(
                        provider.remove_content
                    ):
                        # Call the method directly
                        removed = await provider.remove_content(file_id)
                        results[provider_id] = removed
                        logger.info(
                            f"Removed file {file_path} from provider {provider_id}"
                        )
                    else:
                        logger.warning(
                            f"Provider {provider_id} does not support removing content"
                        )
                        results[provider_id] = False
                except Exception as e:
                    logger.error(
                        f"Failed to remove file {file_path} from provider {provider_id}: {e}"
                    )
                    results[provider_id] = False

            return results

        except Exception as e:
            error_msg = f"Failed to remove file {file_path} from index: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def clear_index(
        self, provider_ids: list[str] | None = None
    ) -> dict[str, bool]:
        """
        Clear the entire index for the specified providers.

        Args:
            provider_ids: IDs of providers to clear, or None for all

        Returns:
            Dictionary mapping provider IDs to success status

        Raises:
            SearchError: If clearing fails
        """
        self._ensure_initialized()

        try:
            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for clearing index")
                return {}

            # Clear the index for each provider
            results = {}

            for provider_id, provider in available_providers.items():
                try:
                    # Check if the provider has a clear_index method
                    if hasattr(provider, "clear_index") and callable(
                        provider.clear_index
                    ):
                        # Call the method directly
                        await provider.clear_index()
                        results[provider_id] = True
                        logger.info(f"Cleared index for provider {provider_id}")
                    else:
                        logger.warning(
                            f"Provider {provider_id} does not support clearing index"
                        )
                        results[provider_id] = False
                except Exception as e:
                    logger.error(
                        f"Failed to clear index for provider {provider_id}: {e}"
                    )
                    results[provider_id] = False

            return results

        except Exception as e:
            error_msg = f"Failed to clear index: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_index_stats(
        self, provider_ids: list[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Get statistics about the index.

        Args:
            provider_ids: IDs of providers to get statistics for, or None for all

        Returns:
            Dictionary mapping provider IDs to index statistics

        Raises:
            SearchError: If getting statistics fails
        """
        self._ensure_initialized()

        try:
            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for getting index statistics")
                return {}

            # Get statistics for each provider
            results = {}

            for provider_id, provider in available_providers.items():
                try:
                    # Check if the provider has a get_index_stats method
                    if hasattr(provider, "get_index_stats") and callable(
                        provider.get_index_stats
                    ):
                        # Call the method directly
                        stats = await provider.get_index_stats()
                        results[provider_id] = stats
                        logger.debug(f"Got index statistics for provider {provider_id}")
                    else:
                        # Provider doesn't support statistics, return basic info
                        results[provider_id] = {
                            "provider_type": await provider.get_provider_type(),
                            "supported": False,
                        }
                        logger.warning(
                            f"Provider {provider_id} does not support index statistics"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to get index statistics for provider {provider_id}: {e}"
                    )
                    results[provider_id] = {"error": str(e)}

            return results

        except Exception as e:
            error_msg = f"Failed to get index statistics: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def add_indexable_type(self, file_extension: str) -> None:
        """
        Add a file type to the list of indexable types.

        Args:
            file_extension: File extension to add (with or without leading dot)

        Raises:
            SearchError: If the operation fails
        """
        self._ensure_initialized()

        try:
            # Normalize extension (ensure it has a leading dot)
            if not file_extension.startswith("."):
                file_extension = f".{file_extension}"

            # Add to set of indexable types
            self._indexable_types.add(file_extension.lower())

            logger.info(f"Added {file_extension} to indexable file types")

        except Exception as e:
            error_msg = f"Failed to add indexable type {file_extension}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def remove_indexable_type(self, file_extension: str) -> bool:
        """
        Remove a file type from the list of indexable types.

        Args:
            file_extension: File extension to remove (with or without leading dot)

        Returns:
            True if the type was removed, False if it wasn't in the list

        Raises:
            SearchError: If the operation fails
        """
        self._ensure_initialized()

        try:
            # Normalize extension (ensure it has a leading dot)
            if not file_extension.startswith("."):
                file_extension = f".{file_extension}"

            file_extension = file_extension.lower()

            # Remove from set of indexable types
            if file_extension in self._indexable_types:
                self._indexable_types.remove(file_extension)
                logger.info(f"Removed {file_extension} from indexable file types")
                return True
            else:
                logger.warning(f"File type {file_extension} not in indexable types")
                return False

        except Exception as e:
            error_msg = f"Failed to remove indexable type {file_extension}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_indexable_types(self) -> list[str]:
        """
        Get the list of indexable file types.

        Returns:
            List of file extensions that are considered indexable

        Raises:
            SearchError: If the operation fails
        """
        self._ensure_initialized()

        try:
            # Return sorted list of indexable types
            return sorted(list(self._indexable_types))

        except Exception as e:
            error_msg = f"Failed to get indexable types: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def reindex_all(
        self, provider_ids: list[str] | None = None
    ) -> dict[str, dict[str, int]]:
        """
        Reindex all content for all providers or specified providers.

        Args:
            provider_ids: IDs of providers to reindex, or None for all

        Returns:
            Dictionary mapping provider IDs to statistics (indexed, failed)

        Raises:
            SearchError: If reindexing fails
        """
        self._ensure_initialized()

        try:
            # Get providers to use
            available_providers = await self._get_providers(provider_ids)

            if not available_providers:
                logger.warning("No providers available for reindexing")
                return {}

            # Clear existing indexes
            await self.clear_index(list(available_providers.keys()))

            # Reindex content if file manager is available
            if self._file_manager:
                # Get root directories from file manager
                root_dirs = await self._file_manager.get_root_directories()

                # Initialize results
                results = {
                    provider_id: {"indexed": 0, "failed": 0}
                    for provider_id in available_providers
                }

                # Index each root directory
                for directory in root_dirs:
                    try:
                        dir_path = directory.path
                        dir_results = await self.index_directory(
                            dir_path,
                            recursive=True,
                            provider_ids=list(available_providers.keys()),
                        )

                        # Accumulate results
                        for provider_id, stats in dir_results.items():
                            results[provider_id]["indexed"] += stats["indexed"]
                            results[provider_id]["failed"] += stats["failed"]

                    except Exception as e:
                        logger.error(
                            f"Failed to reindex directory {directory.path}: {e}"
                        )
                        # Update failure statistics
                        for provider_id in available_providers:
                            results[provider_id]["failed"] += 1

                return results
            else:
                logger.warning("File manager not available for reindexing")
                return {
                    provider_id: {"indexed": 0, "failed": 0}
                    for provider_id in available_providers
                }

        except Exception as e:
            error_msg = f"Failed to reindex all content: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def _get_providers(
        self, provider_ids: list[str] | None = None
    ) -> dict[str, SearchProvider]:
        """
        Get the providers to use based on the provided IDs.

        Args:
            provider_ids: IDs of providers to use, or None for all

        Returns:
            Dictionary mapping provider IDs to provider instances
        """
        # Get all available providers
        all_providers = {}
        provider_list = await self._search_engine.list_providers()

        for provider_info in provider_list:
            provider_id = provider_info["id"]
            provider = await self._search_engine.get_provider(provider_id)
            if provider:
                all_providers[provider_id] = provider

        # If no IDs specified, use all providers
        if not provider_ids:
            return all_providers

        # Filter providers by ID
        filtered_providers = {}
        for provider_id in provider_ids:
            if provider_id in all_providers:
                filtered_providers[provider_id] = all_providers[provider_id]
            else:
                logger.warning(f"Provider {provider_id} not found")

        return filtered_providers

    async def _add_to_index(
        self,
        provider: SearchProvider,
        file_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """
        Add content to a provider's index.

        Args:
            provider: The search provider
            file_id: Unique ID for the file
            content: Content to index
            metadata: File metadata

        Raises:
            Exception: If adding to index fails
        """
        # Check if the provider supports adding content
        if hasattr(provider, "add_content") and callable(provider.add_content):
            # Call the method directly
            await provider.add_content(file_id, content, metadata)
        else:
            raise SearchError("Provider does not support adding content to index")

    def _ensure_initialized(self) -> None:
        """
        Ensure the index manager is initialized.

        Raises:
            SearchError: If the manager is not initialized
        """
        if not self._initialized:
            raise SearchError("Index manager not initialized")
