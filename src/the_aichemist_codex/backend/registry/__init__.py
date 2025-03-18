"""
Registry module for the_aichemist_codex.

This module provides a central registry for accessing service instances,
preventing circular dependencies through the use of lazy initialization
and dependency injection.
"""

from typing import Optional, Type

from ..core.interfaces import (
    AsyncIO,
    CacheProvider,
    ConfigProvider,
    DirectoryManager,
    FileReader,
    FileTree,
    FileValidator,
    MetadataManager,
    ProjectPaths,
    ProjectReader,
    SearchEngine,
)


class Registry:
    """
    Central registry for singleton service instances.

    This class uses the Singleton pattern to provide global access to service
    instances while preventing circular dependencies through lazy initialization.
    """

    _instance = None

    @classmethod
    def get_instance(cls) -> "Registry":
        """Get the singleton instance of the Registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the Registry with None for all service instances."""
        if Registry._instance is not None:
            raise RuntimeError(
                "Registry is a singleton. Use Registry.get_instance() instead."
            )

        # Initialize all service instances to None for lazy loading
        self._project_paths: ProjectPaths | None = None
        self._file_validator: FileValidator | None = None
        self._config_provider: ConfigProvider | None = None
        self._async_io: AsyncIO | None = None
        self._cache_provider: CacheProvider | None = None
        self._directory_manager: DirectoryManager | None = None
        self._file_tree: FileTree | None = None
        self._file_reader: FileReader | None = None
        self._metadata_manager: MetadataManager | None = None
        self._search_engine: SearchEngine | None = None
        self._project_reader: ProjectReader | None = None

    def register_implementation(self, interface_type: type, implementation_instance):
        """Register an implementation for an interface."""
        if interface_type == ProjectPaths:
            self._project_paths = implementation_instance
        elif interface_type == FileValidator:
            self._file_validator = implementation_instance
        elif interface_type == ConfigProvider:
            self._config_provider = implementation_instance
        elif interface_type == AsyncIO:
            self._async_io = implementation_instance
        elif interface_type == CacheProvider:
            self._cache_provider = implementation_instance
        elif interface_type == DirectoryManager:
            self._directory_manager = implementation_instance
        elif interface_type == FileTree:
            self._file_tree = implementation_instance
        elif interface_type == FileReader:
            self._file_reader = implementation_instance
        elif interface_type == MetadataManager:
            self._metadata_manager = implementation_instance
        elif interface_type == SearchEngine:
            self._search_engine = implementation_instance
        elif interface_type == ProjectReader:
            self._project_reader = implementation_instance
        else:
            raise ValueError(f"Unknown interface type: {interface_type}")

    # Properties for accessing service instances

    @property
    def project_paths(self) -> ProjectPaths:
        """Get the project paths service."""
        if self._project_paths is None:
            # Import here to avoid circular imports
            from ..infrastructure.config.paths import ProjectPathsImpl

            self._project_paths = ProjectPathsImpl()
        return self._project_paths

    @property
    def file_validator(self) -> FileValidator:
        """Get the file validator service."""
        if self._file_validator is None:
            # Import here to avoid circular imports
            from ..infrastructure.security.file_validator import FileValidatorImpl

            self._file_validator = FileValidatorImpl()
        return self._file_validator

    @property
    def config_provider(self) -> ConfigProvider:
        """Get the configuration provider service."""
        if self._config_provider is None:
            # Import here to avoid circular imports
            from ..infrastructure.config.config_provider import ConfigProviderImpl

            self._config_provider = ConfigProviderImpl()
        return self._config_provider

    @property
    def async_io(self) -> AsyncIO:
        """Get the asynchronous I/O service."""
        if self._async_io is None:
            # Import here to avoid circular imports
            from ..infrastructure.io.async_io_impl import AsyncIOImpl

            self._async_io = AsyncIOImpl()
        return self._async_io

    @property
    def cache_provider(self) -> CacheProvider:
        """Get the cache provider service."""
        if self._cache_provider is None:
            # Import here to avoid circular imports
            from ..services.cache.cache_manager import CacheManager

            self._cache_provider = CacheManager()
        return self._cache_provider

    @property
    def directory_manager(self) -> DirectoryManager:
        """Get the directory manager service."""
        if self._directory_manager is None:
            # Import here to avoid circular imports
            from ..services.file_mgmt.directory_manager import DirectoryManagerImpl

            self._directory_manager = DirectoryManagerImpl()
        return self._directory_manager

    @property
    def file_tree(self) -> FileTree:
        """Get the file tree service."""
        if self._file_tree is None:
            # Import here to avoid circular imports
            from ..services.file_mgmt.file_tree import FileTreeImpl

            self._file_tree = FileTreeImpl()
        return self._file_tree

    @property
    def file_reader(self) -> FileReader:
        """Get the file reader service."""
        if self._file_reader is None:
            # Import here to avoid circular imports
            from ..domain.file_reader.file_reader import FileReaderImpl

            self._file_reader = FileReaderImpl()
        return self._file_reader

    @property
    def metadata_manager(self) -> MetadataManager:
        """Get the metadata manager service."""
        if self._metadata_manager is None:
            # Import here to avoid circular imports
            from ..services.metadata.manager import MetadataManagerImpl

            self._metadata_manager = MetadataManagerImpl()
        return self._metadata_manager

    @property
    def search_engine(self) -> SearchEngine:
        """Get the search engine service."""
        if self._search_engine is None:
            # Import here to avoid circular imports
            from ..services.search.search_engine import SearchEngineImpl

            self._search_engine = SearchEngineImpl()
        return self._search_engine

    @property
    def project_reader(self) -> ProjectReader:
        """Get the project reader service."""
        if self._project_reader is None:
            # Import here to avoid circular imports
            from ..domain.project_reader.project_reader import ProjectReaderImpl

            self._project_reader = ProjectReaderImpl()
        return self._project_reader
