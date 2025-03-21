"""
Registry module for dependency management.

This module provides a centralized registry that manages all dependencies in the application.
It helps to break circular import dependencies and provides a clean way to access services.
"""

import functools
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, Protocol, TypeVar

from .core.interfaces import (
    AsyncIO,
    CacheProvider,
    DirectoryManager,
    FileValidator,
    MetadataExtractor,
    ProjectPaths,
    RelationshipManager,
    SearchEngine,
    SettingsManager,
    StorageProvider,
    VectorStore,
)


# Define placeholder protocols for interfaces that might not be imported directly
class OutputFormatter(Protocol):
    """Protocol for OutputFormatter interface."""

    async def format_output(self, content: Any, format_type: str) -> str: ...
    async def initialize(self) -> None: ...


class RollbackManager(Protocol):
    """Protocol for RollbackManager interface."""

    async def initialize(self) -> None: ...
    async def create_snapshot(self, operation_id: str, file_path: str) -> str: ...


# Type variable for generic methods
T = TypeVar("T")


class ServiceLifecycle(Enum):
    """Defines the lifecycle of a service in the registry."""

    SINGLETON = auto()  # Single instance for the entire application
    TRANSIENT = auto()  # New instance created each time the service is resolved
    SCOPED = auto()  # Single instance per context (e.g., request)


class Registry:
    """
    Centralized registry for managing application dependencies.

    This class provides a singleton instance that manages all dependencies
    in the application, helping to break circular import dependencies and
    providing a clean way to access services.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the registry with empty service dictionaries."""
        if Registry._instance is not None:
            raise RuntimeError(
                "Use Registry.get_instance() to get the registry instance"
            )

        # Dictionary to store service factories
        self._factories: dict[str, Callable[[], Any]] = {}

        # Dictionary to store singleton instances
        self._instances: dict[str, Any] = {}

        # Dictionary to store service lifecycle information
        self._lifecycles: dict[str, str] = {}

        # Default lifecycle
        self._default_lifecycle = "transient"

    def register(
        self, name: str, factory: Callable[[], T], lifecycle: str = "transient"
    ) -> None:
        """
        Register a service factory with the registry.

        Args:
            name: The name of the service
            factory: The factory function that creates the service
            lifecycle: The lifecycle of the service (transient, singleton, or scoped)
        """
        self._factories[name] = factory
        self._lifecycles[name] = lifecycle

    def resolve(self, name: str, context: str | None = None) -> Any:
        """
        Resolve a service from the registry.

        Args:
            name: The name of the service
            context: Optional context for resolving the service

        Returns:
            The resolved service instance

        Raises:
            KeyError: If the service is not registered
        """
        if name not in self._factories:
            raise KeyError(f"Service '{name}' is not registered")

        lifecycle = self._lifecycles.get(name, self._default_lifecycle)

        # For singleton services, return the cached instance if available
        if lifecycle == "singleton":
            if name not in self._instances:
                self._instances[name] = self._factories[name]()
            return self._instances[name]

        # For transient services, create a new instance each time
        return self._factories[name]()

    # Properties for common services to provide a cleaner API
    @property
    def settings(self) -> SettingsManager:
        """Get the settings manager."""
        return self.resolve("settings")

    @property
    def project_paths(self) -> ProjectPaths:
        """Get the project paths service."""
        return self.resolve("project_paths")

    @property
    def file_validator(self) -> FileValidator:
        """Get the file validator service."""
        return self.resolve("file_validator")

    @property
    def async_io(self) -> AsyncIO:
        """Get the async I/O service."""
        return self.resolve("async_io")

    @property
    def storage_provider(self) -> StorageProvider:
        """Get the storage provider service."""
        return self.resolve("storage_provider")

    @property
    def cache_provider(self) -> CacheProvider:
        """Get the cache provider service."""
        return self.resolve("cache_provider")

    @property
    def directory_manager(self) -> DirectoryManager:
        """Get the directory manager service."""
        return self.resolve("directory_manager")

    @property
    def search_engine(self) -> SearchEngine:
        """Get the search engine service."""
        return self.resolve("search_engine")

    @property
    def vector_store(self) -> VectorStore:
        """Get the vector store service."""
        return self.resolve("vector_store")

    @property
    def metadata_extractor(self) -> MetadataExtractor:
        """Get the metadata extractor service."""
        return self.resolve("metadata_extractor")

    @property
    def relationship_manager(self) -> RelationshipManager:
        """Get the relationship manager service."""
        return self.resolve("relationship_manager")


# Helper function for registering service factories
def register_service(
    name: str, lifecycle: str = "transient"
) -> Callable[[Callable[[], T]], Callable[[], T]]:
    """
    Decorator for registering service factories with the registry.

    Args:
        name: The name of the service
        lifecycle: The lifecycle of the service (transient, singleton, or scoped)

    Returns:
        A decorator that registers the factory function
    """

    def decorator(factory: Callable[[], T]) -> Callable[[], T]:
        Registry.get_instance().register(name, factory, lifecycle)
        return factory

    return decorator


# Decorator for lazy initialization of services
def lazy_service(service_name: str):
    """
    Decorator for lazy initialization of services.

    Args:
        service_name: The name of the service

    Returns:
        A decorator that initializes a service lazily
    """

    def decorator(factory):
        @functools.wraps(factory)
        def wrapper(*args, **kwargs):
            registry = Registry.get_instance()
            try:
                # Try to resolve the service
                return registry.resolve(service_name, context=None)
            except KeyError:
                # If service is not registered, create it using the factory
                service = factory(*args, **kwargs)
                registry.register(service_name, lambda: service)
                return service

        return wrapper

    return decorator
