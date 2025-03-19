"""
Search engine implementation.

This module provides the main search engine functionality for finding content
across different sources using various search providers.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

from ...core.exceptions import SearchError
from ...core.interfaces import SearchEngine, SearchProvider
from ...registry import Registry

logger = logging.getLogger(__name__)


class SearchEngineImpl(SearchEngine):
    """Implementation of the search engine interface."""

    def __init__(self):
        """Initialize the search engine."""
        self._registry = Registry.get_instance()
        self._providers: dict[str, SearchProvider] = {}
        self._default_providers: set[str] = set()
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the search engine.

        This method prepares the search engine for use by initializing
        internal data structures.
        """
        if self._initialized:
            return

        logger.info("Initializing search engine")
        self._initialized = True

    async def close(self) -> None:
        """
        Close the search engine and release resources.

        This method closes all search providers and cleans up resources.
        """
        logger.info("Closing search engine")

        # Close all providers
        for provider_id, provider in self._providers.items():
            try:
                await provider.close()
                logger.debug(f"Closed search provider: {provider_id}")
            except Exception as e:
                logger.error(f"Error closing search provider {provider_id}: {e}")

        self._providers.clear()
        self._default_providers.clear()
        self._initialized = False

    async def register_provider(
        self, provider_id: str, provider: SearchProvider, is_default: bool = False
    ) -> None:
        """
        Register a search provider with the search engine.

        Args:
            provider_id: Unique identifier for the provider
            provider: The search provider instance
            is_default: Whether this provider should be used by default

        Raises:
            SearchError: If a provider with the same ID is already registered
        """
        self._ensure_initialized()

        if provider_id in self._providers:
            raise SearchError(
                f"Search provider '{provider_id}' is already registered",
                provider_id=provider_id
            )

        # Initialize the provider
        await provider.initialize()

        # Register the provider
        self._providers[provider_id] = provider
        if is_default:
            self._default_providers.add(provider_id)

        logger.info(f"Registered search provider: {provider_id} (default: {is_default})")

    async def unregister_provider(self, provider_id: str) -> bool:
        """
        Unregister a search provider.

        Args:
            provider_id: Identifier of the provider to unregister

        Returns:
            True if the provider was unregistered, False if not found
        """
        self._ensure_initialized()

        if provider_id not in self._providers:
            logger.warning(f"Search provider not found: {provider_id}")
            return False

        # Get the provider
        provider = self._providers[provider_id]

        # Close the provider
        try:
            await provider.close()
        except Exception as e:
            logger.error(f"Error closing search provider {provider_id}: {e}")

        # Remove the provider
        del self._providers[provider_id]
        self._default_providers.discard(provider_id)

        logger.info(f"Unregistered search provider: {provider_id}")
        return True

    async def search(
        self, query: str, search_type: str = "text", options: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Search for content using a specific search type.

        Args:
            query: Search query string
            search_type: Type of search to perform (provider ID)
            options: Optional search parameters

        Returns:
            List of search results as dictionaries

        Raises:
            SearchError: If the search type is not supported or search fails
        """
        self._ensure_initialized()
        options = options or {}

        # Check if the search type is valid
        if search_type not in self._providers:
            raise SearchError(
                f"Unsupported search type: {search_type}",
                provider_id=search_type,
                query=query
            )

        # Get the provider
        provider = self._providers[search_type]

        try:
            # Perform the search
            results = await provider.search(query, options)
            return results
        except Exception as e:
            logger.error(f"Error during {search_type} search: {e}")
            raise SearchError(
                f"Search failed: {e}",
                provider_id=search_type,
                query=query,
                operation="search",
                details={"options": options}
            ) from e

    async def multi_search(
        self, query: str, search_types: list[str] = None, options: dict[str, Any] = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Search across multiple providers.

        Args:
            query: Search query string
            search_types: List of search types to use (provider IDs)
            options: Optional search parameters

        Returns:
            Dictionary mapping search types to results lists

        Raises:
            SearchError: If search fails
        """
        self._ensure_initialized()
        options = options or {}

        # If no search types are specified, use default providers
        if not search_types:
            search_types = list(self._default_providers)

        if not search_types:
            logger.warning("No search types specified and no default providers available")
            return {}

        results = {}
        errors = []

        # Perform search with each provider
        for search_type in search_types:
            try:
                # Check if the search type is valid
                if search_type not in self._providers:
                    logger.warning(f"Unsupported search type: {search_type}")
                    continue

                # Perform the search
                provider = self._providers[search_type]
                provider_results = await provider.search(query, options)
                results[search_type] = provider_results
            except Exception as e:
                logger.error(f"Error during {search_type} search: {e}")
                errors.append(f"{search_type}: {str(e)}")
                results[search_type] = []

        # If all providers failed, raise an error
        if errors and len(errors) == len(search_types):
            raise SearchError(
                "All search providers failed",
                query=query,
                operation="multi_search",
                details={"errors": errors}
            )

        return results

    async def index_file(self, file_path: str, file_type: str = None) -> None:
        """
        Index a file for searching.

        Args:
            file_path: Path to the file to index
            file_type: Optional file type hint

        Raises:
            SearchError: If indexing fails
        """
        self._ensure_initialized()

        # Index the file with all providers
        for provider_id, provider in self._providers.items():
            try:
                # Check if the provider supports indexing
                if hasattr(provider, "index_file"):
                    await provider.index_file(file_path, file_type)
                    logger.debug(f"Indexed file {file_path} with provider {provider_id}")
            except Exception as e:
                logger.error(f"Error indexing file {file_path} with provider {provider_id}: {e}")
                # Continue with other providers even if one fails

    async def remove_file_from_index(self, file_path: str) -> None:
        """
        Remove a file from the search index.

        Args:
            file_path: Path to the file to remove

        Raises:
            SearchError: If removal fails
        """
        self._ensure_initialized()

        # Remove the file from all providers
        for provider_id, provider in self._providers.items():
            try:
                # Check if the provider supports removing from index
                if hasattr(provider, "remove_file_from_index"):
                    await provider.remove_file_from_index(file_path)
                    logger.debug(f"Removed file {file_path} from provider {provider_id} index")
            except Exception as e:
                logger.error(f"Error removing file {file_path} from provider {provider_id} index: {e}")
                # Continue with other providers even if one fails

    async def get_available_search_types(self) -> list[str]:
        """
        Get a list of available search types (provider IDs).

        Returns:
            List of available search type identifiers
        """
        self._ensure_initialized()
        return list(self._providers.keys())

    async def get_search_options(self, search_type: str) -> dict[str, Any]:
        """
        Get supported options for a search type.

        Args:
            search_type: Type of search (provider ID)

        Returns:
            Dictionary of supported options

        Raises:
            SearchError: If the search type is not supported
        """
        self._ensure_initialized()

        # Check if the search type is valid
        if search_type not in self._providers:
            raise SearchError(
                f"Unsupported search type: {search_type}",
                provider_id=search_type
            )

        # Get the provider
        provider = self._providers[search_type]

        try:
            # Get supported options
            return await provider.get_supported_options()
        except Exception as e:
            logger.error(f"Error getting options for search type {search_type}: {e}")
            raise SearchError(
                f"Failed to get search options: {e}",
                provider_id=search_type,
                operation="get_options"
            ) from e

    async def reindex_all(self) -> None:
        """
        Rebuild the entire search index.

        This method triggers a complete reindexing for all providers.

        Raises:
            SearchError: If reindexing fails
        """
        self._ensure_initialized()

        errors = []

        # Reindex with all providers
        for provider_id, provider in self._providers.items():
            try:
                # Check if the provider supports reindexing
                if hasattr(provider, "reindex_all"):
                    await provider.reindex_all()
                    logger.info(f"Reindexed all content with provider {provider_id}")
            except Exception as e:
                error_msg = f"Error reindexing with provider {provider_id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # If all providers failed, raise an error
        if errors and len(errors) == len(self._providers):
            raise SearchError(
                "Reindexing failed for all providers",
                operation="reindex_all",
                details={"errors": errors}
            )

    def _ensure_initialized(self) -> None:
        """
        Ensure the search engine is initialized.

        Raises:
            SearchError: If the search engine is not initialized
        """
        if not self._initialized:
            raise SearchError("Search engine is not initialized")
