"""
Registry module for dependency management.

This module provides a global registry for managing dependencies,
helping to break circular import dependencies by providing a central
location for accessing service instances.
"""

import functools
import logging
from typing import Any, Optional, TypeVar, cast

from .core.interfaces import (
    AsyncIO,
    CacheProvider,
    ConfigProvider,
    ContentAnalyzer,
    DirectoryManager,
    FileReader,
    FileTree,
    FileValidator,
    FileWriter,
    IndexManager,
    MetadataManager,
    NotificationManager,
    ProjectPaths,
    RelationshipManager,
    SearchEngine,
    TaggingManager,
    AnalyticsManager,
    UserManager,
    FileManager,
    RollbackManager,
    OutputFormatter,
)

# Type variable for generic methods
T = TypeVar("T")


class Registry:
    """
    Singleton registry for managing dependencies.

    This class provides a central registry for accessing service instances,
    which helps break circular dependencies between modules.
    """

    # Singleton instance
    _instance: Optional["Registry"] = None

    @classmethod
    def get_instance(cls) -> "Registry":
        """
        Get the singleton instance of the Registry.

        Returns:
            The Registry instance
        """
        if cls._instance is None:
            cls._instance = Registry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry by clearing the singleton instance."""
        cls._instance = None

    def __init__(self):
        """Initialize the Registry instance."""
        if Registry._instance is not None:
            raise RuntimeError("Registry is a singleton. Use get_instance() instead.")

        # Dictionary to store service implementations
        self._services: dict[str, Any] = {}

        # Set to track which services are being constructed to detect circular dependencies
        self._constructing: set[str] = set()

        # Logger for the registry
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, service: Any) -> None:
        """
        Register a service in the registry.

        Args:
            name: The name of the service
            service: The service instance
        """
        self._services[name] = service
        self._logger.debug(f"Service registered: {name}")

    def get(self, name: str, default: Any | None = None) -> Any:
        """
        Get a service from the registry.

        Args:
            name: The name of the service
            default: Default value if service is not found

        Returns:
            The service instance or default if not found
        """
        return self._services.get(name, default)

    def get_typed(
        self, name: str, service_type: type[T], default: T | None = None
    ) -> T:
        """
        Get a service from the registry with type checking.

        Args:
            name: The name of the service
            service_type: The expected type of the service
            default: Default value if service is not found

        Returns:
            The service instance or default if not found

        Raises:
            TypeError: If the service is not of the expected type
        """
        service = self.get(name, default)
        if service is not None and not isinstance(service, service_type):
            raise TypeError(f"Service {name} is not of type {service_type.__name__}")
        return cast(T, service)

    def has(self, name: str) -> bool:
        """
        Check if a service exists in the registry.

        Args:
            name: The name of the service

        Returns:
            True if the service exists, False otherwise
        """
        return name in self._services

    def remove(self, name: str) -> None:
        """
        Remove a service from the registry.

        Args:
            name: The name of the service
        """
        if name in self._services:
            del self._services[name]
            self._logger.debug(f"Service removed: {name}")

    def _lazy_load(self, name: str, service_type: type[T], factory) -> T:
        """
        Lazily load a service, ensuring it's of the expected type.

        Args:
            name: The name of the service
            service_type: The expected type of the service
            factory: Factory function to create the service

        Returns:
            The service instance of the expected type
        """
        return cast(service_type, self.lazy_get(name, factory))

    def lazy_get(self, name: str, factory, *args, **kwargs) -> Any:
        """
        Get a service from the registry, creating it if it doesn't exist.

        Args:
            name: The name of the service
            factory: Factory function to create the service
            *args: Arguments to pass to the factory
            **kwargs: Keyword arguments to pass to the factory

        Returns:
            The service instance

        Raises:
            RuntimeError: If a circular dependency is detected
        """
        # Check if the service is already in the registry
        if name in self._services:
            return self._services[name]

        # Check for circular dependencies
        if name in self._constructing:
            raise RuntimeError(
                f"Circular dependency detected while creating service: {name}"
            )

        # Mark service as being constructed
        self._constructing.add(name)

        try:
            # Create the service
            service = factory(*args, **kwargs)

            # Register the service
            self.register(name, service)

            return service
        finally:
            # Mark service as no longer being constructed
            self._constructing.remove(name)

    # Convenience properties for commonly accessed services

    @property
    def project_paths(self):
        """Get the ProjectPaths implementation."""
        return self.get("project_paths")

    @property
    def config_provider(self):
        """Get the ConfigProvider implementation."""
        return self.get("config_provider")

    @property
    def file_validator(self):
        """Get the FileValidator implementation."""
        return self.get("file_validator")

    @property
    def async_io(self):
        """Get the AsyncIO implementation."""
        return self.get("async_io")

    @property
    def cache_manager(self):
        """Get the CacheManager implementation."""
        return self.get("cache_manager")

    @property
    def metadata_manager(self):
        """Get the MetadataManager implementation."""
        return self.get("metadata_manager")

    @property
    def search_engine(self) -> SearchEngine:
        """
        Get the SearchEngine instance.

        Returns:
            The SearchEngine instance
        """
        return self._lazy_load("search_engine", SearchEngine, self._create_search_engine)

    @property
    def index_manager(self) -> IndexManager:
        """
        Get the IndexManager instance.

        Returns:
            The IndexManager instance
        """
        return self._lazy_load("index_manager", IndexManager, self._create_index_manager)

    @property
    def file_reader(self) -> FileReader:
        """
        Get the FileReader instance.

        Returns:
            The FileReader instance
        """
        return self._lazy_load("file_reader", FileReader, self._create_file_reader)

    @property
    def file_writer(self) -> FileWriter:
        """
        Get the FileWriter instance.

        Returns:
            The FileWriter instance
        """
        return self._lazy_load("file_writer", FileWriter, self._create_file_writer)

    @property
    def tagging_manager(self) -> TaggingManager:
        """
        Get the TaggingManager instance.

        Returns:
            The TaggingManager instance
        """
        return self._lazy_load("tagging_manager", TaggingManager, self._create_tagging_manager)

    @property
    def relationship_manager(self) -> RelationshipManager:
        """
        Get the RelationshipManager instance.

        Returns:
            The RelationshipManager instance
        """
        return self._lazy_load("relationship_manager", RelationshipManager, self._create_relationship_manager)

    @property
    def analytics_manager(self) -> AnalyticsManager:
        """
        Get the AnalyticsManager instance.

        Returns:
            The AnalyticsManager instance
        """
        return self._lazy_load("analytics_manager", AnalyticsManager, self._create_analytics_manager)

    @property
    def notification_manager(self) -> NotificationManager:
        """
        Get the NotificationManager instance.

        Returns:
            The NotificationManager instance
        """
        return self._lazy_load("notification_manager", NotificationManager, self._create_notification_manager)

    @property
    def content_analyzer(self) -> ContentAnalyzer:
        """
        Get the ContentAnalyzer instance.

        Returns:
            The ContentAnalyzer instance
        """
        return self._lazy_load("content_analyzer", ContentAnalyzer, self._create_content_analyzer)

    @property
    def user_manager(self) -> UserManager:
        """
        Get the UserManager instance.

        Returns:
            The UserManager instance
        """
        return self._lazy_load("user_manager", UserManager, self._create_user_manager)

    @property
    def file_manager(self) -> FileManager:
        return self._lazy_load("file_manager", FileManager, self._create_file_manager)

    @property
    def rollback_manager(self) -> RollbackManager:
        return self._lazy_load("rollback_manager", RollbackManager, self._create_rollback_manager)

    @property
    def output_formatter(self) -> OutputFormatter:
        return self._lazy_load("output_formatter", OutputFormatter, self._create_output_formatter)

    def _create_file_reader(self) -> FileReader:
        """
        Create the FileReader instance.

        Returns:
            The FileReader instance
        """
        from .domain.file_reader.file_reader import FileReaderImpl

        return FileReaderImpl()

    def _create_file_writer(self) -> FileWriter:
        """
        Create the FileWriter instance.

        Returns:
            The FileWriter instance
        """
        from .domain.file_writer.file_writer import FileWriterImpl

        return FileWriterImpl()

    def _create_tagging_manager(self) -> TaggingManager:
        """
        Create a new TaggingManager instance.

        Returns:
            A new TaggingManager instance
        """
        from .domain.tagging.tagging_manager import TaggingManagerImpl
        return TaggingManagerImpl()

    def _create_relationship_manager(self) -> RelationshipManager:
        """
        Create a new RelationshipManager instance.

        Returns:
            A new RelationshipManager instance
        """
        from .domain.relationships.relationship_manager import RelationshipManagerImpl
        return RelationshipManagerImpl()

    def _create_analytics_manager(self) -> AnalyticsManager:
        """
        Create a new AnalyticsManager instance.

        Returns:
            A new AnalyticsManager instance
        """
        from .domain.analytics.analytics_manager import AnalyticsManagerImpl
        return AnalyticsManagerImpl()

    def _create_notification_manager(self) -> NotificationManager:
        """
        Create a new NotificationManager instance.

        Returns:
            A new NotificationManager instance
        """
        from .domain.notification.notification_manager import NotificationManagerImpl
        return NotificationManagerImpl(
            project_paths=self.project_paths,
            file_validator=self.file_validator,
        )

    def _create_content_analyzer(self) -> ContentAnalyzer:
        """
        Create the ContentAnalyzer instance.

        Returns:
            The ContentAnalyzer instance
        """
        from .domain.content_analyzer.analyzer_manager import ContentAnalyzerManager
        return ContentAnalyzerManager()

    def _create_user_manager(self) -> UserManager:
        """
        Create the UserManager instance.

        Returns:
            The UserManager instance
        """
        from .domain.user_management.user_manager import UserManagerImpl
        return UserManagerImpl(self.project_paths, self.file_validator)

    def _create_search_engine(self) -> SearchEngine:
        """
        Create the SearchEngine instance.

        Returns:
            The SearchEngine instance
        """
        from .domain.search.search_engine import SearchEngineImpl
        return SearchEngineImpl()

    def _create_index_manager(self) -> IndexManager:
        """
        Create the IndexManager instance.

        Returns:
            The IndexManager instance
        """
        from .domain.search.index_manager import IndexManagerImpl

        # Get the file manager and search engine from the registry
        file_manager = self.get("file_manager")
        search_engine = self.search_engine

        return IndexManagerImpl(search_engine, file_manager)

    def _create_directory_manager(self) -> DirectoryManager:
        # ... existing code ...

    def _create_file_manager(self) -> FileManager:
        from .domain.file_manager.file_manager import FileManagerImpl
        return FileManagerImpl()

    def _create_rollback_manager(self) -> RollbackManager:
        from .domain.rollback.rollback_manager import RollbackManagerImpl
        return RollbackManagerImpl()

    def _create_output_formatter(self) -> OutputFormatter:
        from .domain.output_


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
            return registry.lazy_get(service_name, factory, *args, **kwargs)

        return wrapper

    return decorator
