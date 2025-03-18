"""
Search engine implementation.

This module provides a unified interface for searching across various providers
and data sources within the AIChemist Codex.
"""

import logging
from typing import Any

from the_aichemist_codex.backend.core.exceptions import SearchError
from the_aichemist_codex.backend.core.interfaces import SearchEngine, SearchProvider

logger = logging.getLogger(__name__)


class SearchEngineImpl(SearchEngine):
    """Implementation of the search engine."""

    def __init__(self):
        """Initialize the search engine."""
        self._providers = {}  # type: Dict[str, SearchProvider]
        self._default_providers = set()  # type: Set[str]
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the search engine and its providers.

        Raises:
            SearchError: If initialization fails
        """
        if self._initialized:
            logger.debug("Search engine already initialized")
            return

        try:
            logger.info("Initializing search engine")

            # Initialize all registered providers
            for provider_id, provider in self._providers.items():
                try:
                    await provider.initialize()
                    logger.info(f"Initialized search provider: {provider_id}")
                except Exception as e:
                    logger.error(f"Failed to initialize provider {provider_id}: {e}")
                    # We continue even if some providers fail to initialize

            self._initialized = True
            logger.info("Search engine initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize search engine: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def close(self) -> None:
        """
        Close the search engine and its providers.

        Raises:
            SearchError: If closing fails
        """
        if not self._initialized:
            logger.debug("Search engine not initialized")
            return

        try:
            logger.info("Closing search engine")

            # Close all registered providers
            for provider_id, provider in self._providers.items():
                try:
                    await provider.close()
                    logger.info(f"Closed search provider: {provider_id}")
                except Exception as e:
                    logger.error(f"Failed to close provider {provider_id}: {e}")
                    # We continue even if some providers fail to close

            self._initialized = False
            logger.info("Search engine closed successfully")
        except Exception as e:
            error_msg = f"Failed to close search engine: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def register_provider(
        self, provider_id: str, provider: SearchProvider, is_default: bool = False
    ) -> None:
        """
        Register a search provider with the engine.

        Args:
            provider_id: Unique identifier for the provider
            provider: The search provider instance
            is_default: Whether this provider should be used by default

        Raises:
            SearchError: If registration fails
        """
        try:
            if provider_id in self._providers:
                logger.warning(f"Replacing existing provider with ID '{provider_id}'")

            logger.info(f"Registering search provider: {provider_id}")
            self._providers[provider_id] = provider

            if is_default:
                self._default_providers.add(provider_id)
                logger.info(f"Added {provider_id} as a default search provider")

            # Initialize the provider if the engine is already initialized
            if self._initialized:
                await provider.initialize()

        except Exception as e:
            error_msg = f"Failed to register provider {provider_id}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def unregister_provider(self, provider_id: str) -> bool:
        """
        Unregister a search provider from the engine.

        Args:
            provider_id: Identifier of the provider to remove

        Returns:
            True if the provider was removed, False if not found

        Raises:
            SearchError: If unregistration fails
        """
        try:
            if provider_id not in self._providers:
                logger.warning(f"No provider found with ID '{provider_id}'")
                return False

            logger.info(f"Unregistering search provider: {provider_id}")

            # Close the provider if the engine is initialized
            if self._initialized:
                try:
                    await self._providers[provider_id].close()
                except Exception as e:
                    logger.warning(f"Error closing provider {provider_id}: {e}")

            # Remove from providers dictionary
            del self._providers[provider_id]

            # Remove from default providers if present
            if provider_id in self._default_providers:
                self._default_providers.remove(provider_id)

            logger.info(f"Unregistered search provider: {provider_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to unregister provider {provider_id}: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_provider(self, provider_id: str) -> SearchProvider | None:
        """
        Get a search provider by its ID.

        Args:
            provider_id: Identifier of the provider to retrieve

        Returns:
            The search provider or None if not found
        """
        return self._providers.get(provider_id)

    async def list_providers(self) -> list[dict[str, Any]]:
        """
        List all registered search providers.

        Returns:
            List of provider details (id, type, is_default)
        """
        result = []

        for provider_id, provider in self._providers.items():
            try:
                provider_type = await provider.get_provider_type()
                result.append(
                    {
                        "id": provider_id,
                        "type": provider_type,
                        "is_default": provider_id in self._default_providers,
                    }
                )
            except Exception as e:
                logger.warning(f"Error getting provider details for {provider_id}: {e}")
                result.append(
                    {
                        "id": provider_id,
                        "type": "unknown",
                        "is_default": provider_id in self._default_providers,
                        "error": str(e),
                    }
                )

        return result

    async def search(
        self,
        query: str,
        provider_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform a search using the specified provider or default providers.

        Args:
            query: The search query
            provider_id: ID of the provider to use, or None to use defaults
            options: Provider-specific search options

        Returns:
            List of search results

        Raises:
            SearchError: If the search fails or no providers are available
        """
        self._ensure_initialized()

        if not query:
            logger.warning("Empty search query provided")
            return []

        options = options or {}

        try:
            # Determine which providers to use
            providers_to_use = {}

            if provider_id:
                # Use the specified provider
                if provider_id not in self._providers:
                    raise SearchError(f"No provider found with ID '{provider_id}'")
                providers_to_use[provider_id] = self._providers[provider_id]
            else:
                # Use default providers
                if not self._default_providers:
                    raise SearchError("No default search providers configured")

                for default_id in self._default_providers:
                    providers_to_use[default_id] = self._providers[default_id]

            if not providers_to_use:
                raise SearchError("No search providers available")

            # Perform search with each provider
            results = []
            errors = []

            for pid, provider in providers_to_use.items():
                try:
                    logger.debug(f"Searching with provider {pid}")
                    provider_results = await provider.search(query, options)

                    # Add provider ID to each result
                    for result in provider_results:
                        result["provider_id"] = pid

                    results.extend(provider_results)
                    logger.debug(
                        f"Provider {pid} returned {len(provider_results)} results"
                    )
                except Exception as e:
                    error_msg = f"Error searching with provider {pid}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Sort results by score (if available)
            if results:
                results.sort(key=lambda r: r.get("score", 0), reverse=True)

            # If all providers failed, raise an error
            if errors and not results:
                raise SearchError(f"All search providers failed: {'; '.join(errors)}")

            return results

        except SearchError:
            # Re-raise SearchError as is
            raise
        except Exception as e:
            error_msg = f"Error performing search: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def get_search_options(
        self, provider_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get the search options supported by a provider or all providers.

        Args:
            provider_id: ID of the provider to get options for, or None for all

        Returns:
            Dictionary of provider options

        Raises:
            SearchError: If the operation fails or provider not found
        """
        self._ensure_initialized()

        try:
            result = {}

            if provider_id:
                # Get options for the specified provider
                if provider_id not in self._providers:
                    raise SearchError(f"No provider found with ID '{provider_id}'")

                provider = self._providers[provider_id]
                result[provider_id] = await provider.get_supported_options()
            else:
                # Get options for all providers
                for pid, provider in self._providers.items():
                    try:
                        result[pid] = await provider.get_supported_options()
                    except Exception as e:
                        logger.error(f"Error getting options for provider {pid}: {e}")
                        result[pid] = {"error": str(e)}

            return result

        except SearchError:
            # Re-raise SearchError as is
            raise
        except Exception as e:
            error_msg = f"Error getting search options: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    def _ensure_initialized(self) -> None:
        """
        Ensure the search engine is initialized.

        Raises:
            SearchError: If the engine is not initialized
        """
        if not self._initialized:
            raise SearchError("Search engine not initialized")
