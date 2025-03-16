"""Search provider implementations for different search types."""

from typing import List, Protocol, runtime_checkable


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol defining the interface for search providers."""

    async def search(self, query: str, **kwargs) -> list[str]:
        """
        Perform a search using this provider.

        Args:
            query: The search query
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching file paths
        """
        ...
