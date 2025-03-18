"""
Bootstrap module for initializing the application.

This module provides functions for initializing the application,
registering service implementations, and setting up the dependency
injection framework.
"""

import asyncio
import logging
from pathlib import Path

from .infrastructure.config.config_provider import ConfigProviderImpl
from .infrastructure.file.file_validator import FileValidatorImpl
from .infrastructure.io.async_io_impl import AsyncIOImpl
from .infrastructure.paths.project_paths import ProjectPathsImpl
from .registry import Registry
from .services.cache.cache_manager import CacheManager
from .services.file.directory_manager import DirectoryManager
from .services.metadata.metadata_manager import MetadataManager

logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """
    Bootstrap class for initializing the application.

    This class provides methods for initializing the application components
    and setting up the dependency injection framework.
    """

    @staticmethod
    async def initialize_async(
        project_root: Path | None = None,
        config_file: str | None = None,
        enable_logging: bool = True,
    ) -> Registry:
        """
        Initialize the application by registering service implementations.

        Args:
            project_root: Optional custom project root directory
            config_file: Optional custom configuration file path
            enable_logging: Whether to enable logging

        Returns:
            The initialized Registry instance
        """
        if enable_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        # Reset the registry in case it was previously initialized
        Registry.reset()

        # Get registry instance
        registry = Registry.get_instance()

        # Initialize core services

        # 1. Project Paths - required by other services
        logger.info("Initializing ProjectPaths...")
        project_paths = ProjectPathsImpl(project_root)
        registry.register("project_paths", project_paths)

        # 2. Config Provider - requires ProjectPaths
        logger.info("Initializing ConfigProvider...")
        config_provider = ConfigProviderImpl()
        if config_file:
            config_provider.load_config_file(config_file)
        registry.register("config_provider", config_provider)

        # 3. File Validator - requires ProjectPaths and ConfigProvider
        logger.info("Initializing FileValidator...")
        file_validator = FileValidatorImpl()
        registry.register("file_validator", file_validator)

        # 4. Async IO - requires FileValidator
        logger.info("Initializing AsyncIO...")
        async_io = AsyncIOImpl()
        registry.register("async_io", async_io)

        # 5. Directory Manager - requires ProjectPaths and FileValidator
        logger.info("Initializing DirectoryManager...")
        directory_manager = DirectoryManager()
        registry.register("directory_manager", directory_manager)

        # 6. Cache Manager - requires ProjectPaths and FileValidator
        logger.info("Initializing CacheManager...")
        cache_manager = CacheManager()
        registry.register("cache_manager", cache_manager)

        # 7. Metadata Manager - requires AsyncIO, FileValidator, and CacheManager
        logger.info("Initializing MetadataManager...")
        metadata_manager = MetadataManager()
        registry.register("metadata_manager", metadata_manager)

        # 8. Search Engine - obtained from registry through lazy loading
        # Will be initialized later with proper async initialization

        # 9. Tagging Manager - requires ProjectPaths and FileValidator
        logger.info("Initializing TaggingManager...")
        tagging_manager = registry.tagging_manager
        await tagging_manager.initialize()

        # 10. Relationship Manager - requires ProjectPaths, FileValidator, and FileReader
        logger.info("Initializing RelationshipManager...")
        relationship_manager = registry.relationship_manager
        await relationship_manager.initialize()

        # 11. Analytics Manager - requires ProjectPaths and ConfigProvider
        logger.info("Initializing AnalyticsManager...")
        analytics_manager = registry.analytics_manager
        await analytics_manager.initialize()

        # 12. Notification Manager - requires ProjectPaths and FileValidator
        logger.info("Initializing NotificationManager...")
        notification_manager = registry.notification_manager
        await notification_manager.initialize()

        # 13. Content Analyzer - requires FileReader
        logger.info("Initializing ContentAnalyzer...")
        content_analyzer = registry.content_analyzer
        await content_analyzer.initialize()

        # 14. User Manager - requires ProjectPaths and FileValidator
        logger.info("Initializing UserManager...")
        user_manager = registry.user_manager
        await user_manager.initialize()

        # 15. Search Engine - requires initialization
        logger.info("Initializing SearchEngine...")
        search_engine = registry.search_engine
        await search_engine.initialize()

        # Register default search providers
        logger.info("Registering search providers...")
        from .domain.search.providers.regex_provider import RegexSearchProvider
        from .domain.search.providers.text_provider import TextSearchProvider
        from .domain.search.providers.vector_provider import VectorSearchProvider

        await search_engine.register_provider(
            "text", TextSearchProvider(), is_default=True
        )
        await search_engine.register_provider(
            "regex", RegexSearchProvider(), is_default=True
        )

        # Set up vector search provider with cache directory
        cache_dir = project_paths.get_cache_dir() / "vector_search"
        vector_provider = VectorSearchProvider(cache_dir=str(cache_dir))
        await search_engine.register_provider(
            "vector", vector_provider, is_default=True
        )

        # 16. Index Manager - requires SearchEngine and FileManager
        logger.info("Initializing IndexManager...")
        index_manager = registry.index_manager
        await index_manager.initialize()

        # Initialize FileManager
        logger.info("Initializing FileManager...")
        file_manager = registry.file_manager
        await file_manager.initialize()

        # Initialize RollbackManager
        logger.info("Initializing RollbackManager...")
        rollback_manager = registry.rollback_manager
        await rollback_manager.initialize()

        # Initialize OutputFormatter
        logger.info("Initializing OutputFormatter...")
        output_formatter = registry.output_formatter
        await output_formatter.initialize()

        logger.info("Application initialization complete.")
        return registry

    @staticmethod
    def initialize(
        project_root: Path | None = None,
        config_file: str | None = None,
        enable_logging: bool = True,
    ) -> Registry:
        """
        Initialize the application synchronously (wrapper around async initialization).

        This method runs the async initialization in an event loop.

        Args:
            project_root: Optional custom project root directory
            config_file: Optional custom configuration file path
            enable_logging: Whether to enable logging

        Returns:
            The initialized Registry instance
        """
        return asyncio.run(
            ApplicationBootstrap.initialize_async(
                project_root=project_root,
                config_file=config_file,
                enable_logging=enable_logging,
            )
        )


def initialize_application(
    project_root: Path | None = None,
    config_file: str | None = None,
    enable_logging: bool = True,
) -> Registry:
    """
    Initialize the application.

    This is a convenience function that delegates to ApplicationBootstrap.

    Args:
        project_root: Optional custom project root directory
        config_file: Optional custom configuration file path
        enable_logging: Whether to enable logging

    Returns:
        The initialized Registry instance
    """
    return ApplicationBootstrap.initialize(
        project_root=project_root,
        config_file=config_file,
        enable_logging=enable_logging,
    )


async def initialize_application_async(
    project_root: Path | None = None,
    config_file: str | None = None,
    enable_logging: bool = True,
) -> Registry:
    """
    Initialize the application asynchronously.

    This is a convenience function that delegates to ApplicationBootstrap.

    Args:
        project_root: Optional custom project root directory
        config_file: Optional custom configuration file path
        enable_logging: Whether to enable logging

    Returns:
        The initialized Registry instance
    """
    return await ApplicationBootstrap.initialize_async(
        project_root=project_root,
        config_file=config_file,
        enable_logging=enable_logging,
    )


# Initialize and register metadata extractors
def _initialize_metadata_extractors():
    """Initialize metadata extractors and register them with the metadata manager."""
    logger.info("Initializing metadata extractors")
    registry = Registry.get_instance()
    metadata_manager = registry
