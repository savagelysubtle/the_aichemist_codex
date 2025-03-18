"""
Base search provider implementation.

This module provides a base implementation for search providers,
with common utilities and helper methods for specific providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from the_aichemist_codex.backend.core.exceptions import SearchError
from the_aichemist_codex.backend.core.interfaces import SearchProvider

logger = logging.getLogger(__name__)


class BaseSearchProvider(SearchProvider, ABC):
    """
    Base implementation of the SearchProvider interface.

    This class provides common functionality for search providers,
    including initialization and cleanup.
    """

    def __init__(self):
        """Initialize the base search provider."""
        self._initialized = False
        self._provider_type = self._get_provider_type()

    async def initialize(self) -> None:
        """
        Initialize the search provider.

        This method prepares the provider for use by initializing
        internal data structures.
        """
        if self._initialized:
            logger.debug(f"{self._provider_type} provider already initialized")
            return

        try:
            logger.info(f"Initializing {self._provider_type} search provider")
            await self._initialize_provider()
            self._initialized = True
            logger.info(
                f"{self._provider_type} search provider initialized successfully"
            )
        except Exception as e:
            error_msg = (
                f"Failed to initialize {self._provider_type} search provider: {e}"
            )
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def close(self) -> None:
        """
        Close the search provider and release resources.

        This method cleans up resources used by the provider.
        """
        if not self._initialized:
            logger.debug(f"{self._provider_type} provider not initialized")
            return

        try:
            logger.info(f"Closing {self._provider_type} search provider")
            await self._close_provider()
            self._initialized = False
            logger.info(f"{self._provider_type} search provider closed successfully")
        except Exception as e:
            error_msg = f"Failed to close {self._provider_type} search provider: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def search(
        self, query: str, options: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Perform a search using this provider.

        Args:
            query: The search query
            options: Optional provider-specific parameters

        Returns:
            List of search results

        Raises:
            SearchError: If search fails
        """
        if not self._initialized:
            raise SearchError(f"{self._provider_type} provider not initialized")

        if not query:
            logger.warning("Empty search query provided")
            return []

        try:
            logger.debug(f"Performing {self._provider_type} search with query: {query}")
            results = await self._perform_search(query, options or {})
            logger.debug(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            error_msg = f"Error in {self._provider_type} search: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_supported_options(self) -> dict[str, Any]:
        """
        Get the options supported by this provider.

        Returns:
            Dictionary of supported options, their types, and descriptions
        """
        if not self._initialized:
            raise SearchError(f"{self._provider_type} provider not initialized")

        try:
            return self._get_provider_options()
        except Exception as e:
            error_msg = (
                f"Error getting supported options for {self._provider_type}: {e}"
            )
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_provider_type(self) -> str:
        """
        Get the type of this search provider.

        Returns:
            String identifier for this provider type
        """
        return self._provider_type

    def _ensure_initialized(self) -> None:
        """
        Ensure the provider is initialized.

        Raises:
            SearchError: If the provider is not initialized
        """
        if not self._initialized:
            raise SearchError(f"{self._provider_type} provider not initialized")

    @abstractmethod
    async def _initialize_provider(self) -> None:
        """
        Initialize provider-specific resources.

        This method should be implemented by subclasses to perform
        provider-specific initialization.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def _close_provider(self) -> None:
        """
        Close provider-specific resources.

        This method should be implemented by subclasses to perform
        provider-specific cleanup.

        Raises:
            Exception: If closing fails
        """
        pass

    @abstractmethod
    async def _perform_search(
        self, query: str, options: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Perform provider-specific search.

        This method should be implemented by subclasses to perform
        the actual search operation.

        Args:
            query: The search query
            options: Provider-specific parameters

        Returns:
            List of search results

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    def _get_provider_options(self) -> dict[str, Any]:
        """
        Get provider-specific options.

        This method should be implemented by subclasses to return
        provider-specific options.

        Returns:
            Dictionary of supported options
        """
        pass

    @abstractmethod
    def _get_provider_type(self) -> str:
        """
        Get the provider type identifier.

        This method should be implemented by subclasses to return
        a unique identifier for the provider type.

        Returns:
            String identifier for this provider type
        """
        pass
