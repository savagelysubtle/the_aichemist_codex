"""
Core interfaces for the application.

This module defines the interfaces that various components of the application
must implement. These interfaces help to break circular dependencies by
allowing components to depend on abstractions rather than concrete implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Import shared models for types that don't create circular imports

if TYPE_CHECKING:
    # Forward references for types that might create circular dependencies
    pass


class ProjectPaths(ABC):
    """
    Interface for project path management.

    This interface defines methods for accessing project directories
    and resolving paths within the project.
    """

    @abstractmethod
    def get_project_root(self) -> Path:
        """
        Get the project root directory.

        Returns:
            Path to the project root directory
        """
        pass

    @abstractmethod
    def get_app_data_dir(self) -> Path:
        """
        Get the application data directory.

        Returns:
            Path to the application data directory
        """
        pass

    @abstractmethod
    def get_config_dir(self) -> Path:
        """
        Get the configuration directory.

        Returns:
            Path to the configuration directory
        """
        pass

    @abstractmethod
    def get_cache_dir(self) -> Path:
        """
        Get the cache directory.

        Returns:
            Path to the cache directory
        """
        pass

    @abstractmethod
    def get_data_dir(self) -> Path:
        """
        Get the data directory.

        Returns:
            Path to the data directory
        """
        pass

    @abstractmethod
    def get_logs_dir(self) -> Path:
        """
        Get the logs directory.

        Returns:
            Path to the logs directory
        """
        pass

    @abstractmethod
    def get_temp_dir(self) -> Path:
        """
        Get the temporary directory.

        Returns:
            Path to the temporary directory
        """
        pass

    @abstractmethod
    def get_default_config_file(self) -> Path:
        """
        Get the default configuration file path.

        Returns:
            Path to the default configuration file
        """
        pass

    @abstractmethod
    def resolve_path(self, path: str, relative_to: Path | None = None) -> Path:
        """
        Resolve a path relative to a base directory.

        Args:
            path: The path to resolve
            relative_to: The base directory to resolve from (defaults to project root)

        Returns:
            The resolved path
        """
        pass

    @abstractmethod
    def get_relative_path(self, path: str, base_path: Path | None = None) -> str:
        """
        Get a path relative to a base path.

        Args:
            path: The path to get relative
            base_path: The base path (defaults to project root)

        Returns:
            The relative path as a string
        """
        pass


class ConfigProvider(ABC):
    """
    Interface for configuration management.

    This interface defines methods for accessing and modifying
    configuration values.
    """

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if the key doesn't exist

        Returns:
            The configuration value or default if not found
        """
        pass

    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        pass

    @abstractmethod
    def load_config_file(self, file_path: str) -> None:
        """
        Load configuration from a file.

        Args:
            file_path: Path to the configuration file
        """
        pass

    @abstractmethod
    def save_config(self) -> None:
        """Save the current configuration to the default configuration file."""
        pass


class FileValidator(ABC):
    """
    Interface for file validation.

    This interface defines methods for validating file paths
    and ensuring they are safe to access.
    """

    @abstractmethod
    def is_path_safe(self, path: str) -> bool:
        """
        Check if a file path is safe to access.

        Args:
            path: The file path to validate

        Returns:
            True if the path is safe, False otherwise
        """
        pass

    @abstractmethod
    def ensure_path_safe(self, path: str) -> str:
        """
        Ensure a file path is safe to access.

        Args:
            path: The file path to validate

        Returns:
            The validated path

        Raises:
            UnsafePathError: If the path is not safe
        """
        pass

    @abstractmethod
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to make it safe for use in a file system.

        Args:
            filename: The filename to sanitize

        Returns:
            A sanitized filename
        """
        pass


class AsyncIO(ABC):
    """
    Interface for asynchronous file I/O operations.

    This interface defines methods for reading and writing files
    asynchronously.
    """

    @abstractmethod
    async def read_file(self, file_path: str) -> str:
        """
        Read a file asynchronously.

        Args:
            file_path: Path to the file

        Returns:
            The file contents as a string

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def write_file(self, file_path: str, content: str) -> None:
        """
        Write to a file asynchronously.

        Args:
            file_path: Path to the file
            content: Content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists asynchronously.

        Args:
            file_path: Path to the file

        Returns:
            True if the file exists, False otherwise

        Raises:
            UnsafePathError: If the path is unsafe
        """
        pass


class CacheProvider(ABC):
    """
    Interface for cache management.

    This interface defines methods for caching values and
    retrieving them later.
    """

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.

        Args:
            key: The cache key
            default: Default value if the key doesn't exist or is expired

        Returns:
            The cached value or default if not found or expired
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        pass

    @abstractmethod
    async def get_with_refresh(
        self, key: str, refresh_func, ttl: int | None = None
    ) -> Any:
        """
        Get a value from the cache, refreshing it if needed.

        Args:
            key: The cache key
            refresh_func: Function to call to refresh the value
            ttl: Time-to-live in seconds

        Returns:
            The cached or refreshed value
        """
        pass


class DirectoryManager(ABC):
    """
    Interface for directory management.

    This interface defines methods for managing directories
    and performing operations on them.
    """

    @abstractmethod
    async def ensure_directory_exists(self, directory_path: str) -> Path:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            Path object for the directory

        Raises:
            DirectoryError: If the directory cannot be created
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def list_directory(self, directory_path: str) -> list[str]:
        """
        List the contents of a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of filenames in the directory

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def get_subdirectories(self, directory_path: str) -> list[str]:
        """
        Get a list of subdirectories in a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of subdirectory names

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def remove_directory(
        self, directory_path: str, recursive: bool = False
    ) -> bool:
        """
        Remove a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to remove recursively

        Returns:
            True if successful, False otherwise

        Raises:
            DirectoryError: If the directory cannot be removed
            UnsafePathError: If the path is unsafe
        """
        pass


class MetadataManager(ABC):
    """
    Interface for metadata management.

    This interface defines methods for extracting and managing
    metadata from different file types.
    """

    @abstractmethod
    async def get_metadata(self, file_path: str) -> Any:  # -> "FileMetadata"
        """
        Get metadata for a file, either from cache or by extracting it.

        Args:
            file_path: Path to the file

        Returns:
            The file metadata

        Raises:
            MetadataError: If there is an error extracting the metadata
        """
        pass

    @abstractmethod
    async def update_metadata(
        self, file_path: str, updates: dict[str, Any]
    ) -> Any:  # -> "FileMetadata"
        """
        Update metadata for a file.

        Args:
            file_path: Path to the file
            updates: Dictionary of metadata fields to update

        Returns:
            The updated metadata

        Raises:
            MetadataError: If there is an error updating the metadata
        """
        pass

    @abstractmethod
    async def search_metadata(
        self, query: str, file_extensions: list[str] = None, limit: int = 10
    ) -> list[Any]:  # -> List["FileMetadata"]
        """
        Search for files by metadata.

        Args:
            query: Search query
            file_extensions: Filter by file extensions
            limit: Maximum number of results

        Returns:
            List of matching file metadata
        """
        pass


class SearchEngine(ABC):
    """
    Interface for the search engine.

    The search engine orchestrates multiple search providers and index managers
    to deliver comprehensive search capabilities.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the search engine.

        This method sets up any necessary resources and initializes
        all registered search providers and index managers.

        Raises:
            SearchError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the search engine and free resources.

        Raises:
            SearchError: If closing fails
        """
        pass

    @abstractmethod
    async def search(
        self, query: str, search_type: str = "text", options: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Perform a search using the specified search type.

        Args:
            query: The search query
            search_type: Type of search (text, regex, vector, etc.)
            options: Additional search options

        Returns:
            List of search results

        Raises:
            SearchError: If search fails or search_type is unsupported
        """
        pass

    @abstractmethod
    async def multi_search(
        self, query: str, search_types: list[str], options: dict[str, Any] = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Perform multiple searches with the same query.

        Args:
            query: The search query
            search_types: List of search types to use
            options: Additional search options

        Returns:
            Dictionary mapping search types to their results

        Raises:
            SearchError: If search fails or any search_type is unsupported
        """
        pass

    @abstractmethod
    async def index_file(self, file_path: str, file_type: str = None) -> None:
        """
        Index a file for searching.

        Args:
            file_path: Path to the file
            file_type: Type of file for specialized indexing (optional)

        Raises:
            SearchError: If indexing fails
        """
        pass

    @abstractmethod
    async def remove_file_from_index(self, file_path: str) -> None:
        """
        Remove a file from the search index.

        Args:
            file_path: Path to the file

        Raises:
            SearchError: If removal fails
        """
        pass

    @abstractmethod
    async def get_available_search_types(self) -> list[str]:
        """
        Get the available search types.

        Returns:
            List of supported search type identifiers

        Raises:
            SearchError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_search_options(self, search_type: str) -> dict[str, Any]:
        """
        Get the options available for a specific search type.

        Args:
            search_type: Type of search

        Returns:
            Dictionary of supported options

        Raises:
            SearchError: If search_type is unsupported
        """
        pass

    @abstractmethod
    async def reindex_all(self) -> None:
        """
        Rebuild all search indexes.

        This is an expensive operation that should be used
        sparingly, typically after major system changes.

        Raises:
            SearchError: If reindexing fails
        """
        pass


class FileTree(ABC):
    """
    Interface for file tree operations.

    This interface defines methods for working with the
    file tree structure.
    """

    @abstractmethod
    async def get_tree(self, root_dir: str, max_depth: int = None) -> dict:
        """
        Get a file tree structure starting from a root directory.

        Args:
            root_dir: The root directory
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary representing the file tree

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def find_files(
        self, root_dir: str, pattern: str, max_depth: int = None
    ) -> list[str]:
        """
        Find files matching a pattern in a directory tree.

        Args:
            root_dir: The root directory
            pattern: Glob pattern to match files
            max_depth: Maximum depth to traverse

        Returns:
            List of matching file paths

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass


class FileReader(ABC):
    """
    Interface for file reading operations.

    This interface defines methods for reading and parsing
    files of different formats.
    """

    @abstractmethod
    async def read_text(self, file_path: str) -> str:
        """
        Read a text file.

        Args:
            file_path: Path to the file

        Returns:
            The file contents as a string

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def read_binary(self, file_path: str) -> bytes:
        """
        Read a binary file.

        Args:
            file_path: Path to the file

        Returns:
            The file contents as bytes

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def read_json(self, file_path: str) -> Any:
        """
        Read and parse a JSON file.

        Args:
            file_path: Path to the file

        Returns:
            The parsed JSON data

        Raises:
            FileError: If the file cannot be read or parsed
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def read_yaml(self, file_path: str) -> Any:
        """
        Read and parse a YAML file.

        Args:
            file_path: Path to the file

        Returns:
            The parsed YAML data

        Raises:
            FileError: If the file cannot be read or parsed
            UnsafePathError: If the path is unsafe
        """
        pass


class FileWriter(ABC):
    """
    Interface for file writing operations.

    This interface defines methods for writing data to files
    in different formats.
    """

    @abstractmethod
    async def write_text(self, file_path: str, content: str) -> None:
        """
        Write text to a file.

        Args:
            file_path: Path to the file
            content: Text content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def write_binary(self, file_path: str, content: bytes) -> None:
        """
        Write binary data to a file.

        Args:
            file_path: Path to the file
            content: Binary content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def write_json(self, file_path: str, data: Any) -> None:
        """
        Write data as JSON to a file.

        Args:
            file_path: Path to the file
            data: Data to serialize as JSON

        Raises:
            FileError: If the data cannot be serialized or the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def write_yaml(self, file_path: str, data: Any) -> None:
        """
        Write data as YAML to a file.

        Args:
            file_path: Path to the file
            data: Data to serialize as YAML

        Raises:
            FileError: If the data cannot be serialized or the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass

    @abstractmethod
    async def append_text(self, file_path: str, content: str) -> None:
        """
        Append text to a file.

        Args:
            file_path: Path to the file
            content: Text content to append

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        pass


class TaggingManager(ABC):
    """
    Interface for managing file tagging operations.

    This interface defines methods for creating, retrieving, updating, and
    deleting tags and their associations with files. It also provides
    methods for querying files by tags and retrieving tag statistics.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the tag manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the tag manager."""
        pass

    @abstractmethod
    async def create_tag(self, name: str, description: str = "") -> int:
        """
        Create a new tag.

        Args:
            name: Name of the tag (must be unique)
            description: Optional description of the tag

        Returns:
            The ID of the newly created tag

        Raises:
            TagError: If tag creation fails or a tag with the same name already exists
        """
        pass

    @abstractmethod
    async def get_tag(self, tag_id: int) -> dict[str, Any] | None:
        """
        Get tag information by ID.

        Args:
            tag_id: ID of the tag to retrieve

        Returns:
            Tag information as a dictionary, or None if not found
        """
        pass

    @abstractmethod
    async def get_tag_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get tag information by name.

        Args:
            name: Name of the tag to retrieve

        Returns:
            Tag information as a dictionary, or None if not found
        """
        pass

    @abstractmethod
    async def update_tag(
        self, tag_id: int, name: str | None = None, description: str | None = None
    ) -> bool:
        """
        Update an existing tag.

        Args:
            tag_id: ID of the tag to update
            name: New name for the tag (optional)
            description: New description for the tag (optional)

        Returns:
            True if the tag was updated, False otherwise

        Raises:
            TagError: If the tag does not exist or the update fails
        """
        pass

    @abstractmethod
    async def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: ID of the tag to delete

        Returns:
            True if the tag was deleted, False otherwise

        Raises:
            TagError: If the tag does not exist or the deletion fails
        """
        pass

    @abstractmethod
    async def get_all_tags(self) -> list[dict[str, Any]]:
        """
        Get all tags.

        Returns:
            A list of dictionaries containing tag information
        """
        pass

    @abstractmethod
    async def add_file_tag(
        self,
        file_path: Path,
        tag_id: int | None = None,
        tag_name: str | None = None,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> bool:
        """
        Add a tag to a file.

        Args:
            file_path: Path to the file
            tag_id: ID of the tag to add (either tag_id or tag_name must be provided)
            tag_name: Name of the tag to add (either tag_id or tag_name must be provided)
            source: Source of the tag (e.g., "manual", "auto", "suggested")
            confidence: Confidence score for the tag (0.0 to 1.0)

        Returns:
            True if the tag was added, False otherwise

        Raises:
            TagError: If neither tag_id nor tag_name is provided, or if the tag does not exist
            FileError: If the file does not exist
        """
        pass

    @abstractmethod
    async def add_file_tags(
        self, file_path: Path, tags: list[tuple[str, float]], source: str = "auto"
    ) -> int:
        """
        Add multiple tags to a file.

        Args:
            file_path: Path to the file
            tags: List of (tag_name, confidence) tuples
            source: Source of the tags (e.g., "manual", "auto", "suggested")

        Returns:
            Number of tags added

        Raises:
            FileError: If the file does not exist
        """
        pass

    @abstractmethod
    async def remove_file_tag(self, file_path: Path, tag_id: int) -> bool:
        """
        Remove a tag from a file.

        Args:
            file_path: Path to the file
            tag_id: ID of the tag to remove

        Returns:
            True if the tag was removed, False otherwise

        Raises:
            TagError: If the tag does not exist
            FileError: If the file does not exist
        """
        pass

    @abstractmethod
    async def get_file_tags(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get all tags for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of dictionaries containing tag information
        """
        pass

    @abstractmethod
    async def get_files_by_tag(
        self, tag_id: int | None = None, tag_name: str | None = None
    ) -> list[str]:
        """
        Get all files with a specific tag.

        Args:
            tag_id: ID of the tag (either tag_id or tag_name must be provided)
            tag_name: Name of the tag (either tag_id or tag_name must be provided)

        Returns:
            List of file paths

        Raises:
            TagError: If neither tag_id nor tag_name is provided, or if the tag does not exist
        """
        pass

    @abstractmethod
    async def get_files_by_tags(
        self, tag_ids: list[int], require_all: bool = False
    ) -> list[str]:
        """
        Get all files with specific tags.

        Args:
            tag_ids: List of tag IDs
            require_all: If True, files must have all tags; if False, files must have any of the tags

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    async def get_tag_counts(self) -> list[dict[str, Any]]:
        """
        Get the number of files for each tag.

        Returns:
            List of dictionaries containing tag information and file counts
        """
        pass

    @abstractmethod
    async def get_tag_suggestions(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get tag suggestions for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of dictionaries containing suggested tag information and confidence scores
        """
        pass


class RelationshipManager(ABC):
    """
    Interface for managing file relationships.

    This interface defines methods for creating, retrieving, updating, and
    deleting relationships between files. It also provides methods for
    querying relationships and analyzing file connections.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the relationship manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the relationship manager."""
        pass

    @abstractmethod
    async def add_relationship(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: str,
        strength: float = 1.0,
        metadata: dict[str, Any] = None,
    ) -> str:
        """
        Add a relationship between two files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship (see RelationshipType enum)
            strength: Strength of the relationship (0.0 to 1.0)
            metadata: Additional metadata for the relationship

        Returns:
            The ID of the newly created relationship

        Raises:
            RelationshipError: If relationship creation fails
            FileError: If either file does not exist
        """
        pass

    @abstractmethod
    async def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        """
        Get relationship information by ID.

        Args:
            relationship_id: ID of the relationship to retrieve

        Returns:
            Relationship information as a dictionary, or None if not found
        """
        pass

    @abstractmethod
    async def update_relationship(
        self,
        relationship_id: str,
        rel_type: str = None,
        strength: float = None,
        metadata: dict[str, Any] = None,
    ) -> bool:
        """
        Update an existing relationship.

        Args:
            relationship_id: ID of the relationship to update
            rel_type: New type for the relationship (optional)
            strength: New strength for the relationship (optional)
            metadata: New metadata for the relationship (optional)

        Returns:
            True if the relationship was updated, False otherwise

        Raises:
            RelationshipError: If the relationship does not exist or the update fails
        """
        pass

    @abstractmethod
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: ID of the relationship to delete

        Returns:
            True if the relationship was deleted, False otherwise

        Raises:
            RelationshipError: If the relationship does not exist or the deletion fails
        """
        pass

    @abstractmethod
    async def get_relationships_for_file(
        self, file_path: Path, as_source: bool = True, as_target: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get all relationships for a file.

        Args:
            file_path: Path to the file
            as_source: Include relationships where the file is the source
            as_target: Include relationships where the file is the target

        Returns:
            List of dictionaries containing relationship information
        """
        pass

    @abstractmethod
    async def find_related_files(
        self, file_path: Path, rel_types: list[str] = None, min_strength: float = 0.0
    ) -> list[dict[str, Any]]:
        """
        Find files related to the given file.

        Args:
            file_path: Path to the file
            rel_types: Types of relationships to include (optional)
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of dictionaries containing related file information and relationship details
        """
        pass

    @abstractmethod
    async def detect_relationships(
        self, file_path: Path, strategies: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        Detect relationships for a file using various detection strategies.

        Args:
            file_path: Path to the file
            strategies: List of detection strategy names (optional)

        Returns:
            List of detected relationships

        Raises:
            FileError: If the file does not exist
        """
        pass

    @abstractmethod
    async def get_relationship_graph(
        self, root_file: Path = None, max_depth: int = 2, min_strength: float = 0.0
    ) -> dict[str, Any]:
        """
        Get a graph representation of file relationships.

        Args:
            root_file: Starting file for the graph (optional)
            max_depth: Maximum depth of relationships to traverse
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            Dictionary representing the relationship graph
        """
        pass


class AnalyticsManager(ABC):
    """
    Interface for analytics and usage statistics.

    This interface defines methods for tracking, storing, and analyzing
    usage patterns and statistics within the application.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the analytics manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the analytics manager."""
        pass

    @abstractmethod
    async def track_event(
        self, event_type: str, metadata: dict[str, Any] = None
    ) -> str:
        """
        Track an application event.

        Args:
            event_type: Type of event (e.g., "file_opened", "search_performed")
            metadata: Additional metadata about the event

        Returns:
            The ID of the tracked event

        Raises:
            Exception: If tracking fails
        """
        pass

    @abstractmethod
    async def track_error(
        self, error_type: str, message: str, metadata: dict[str, Any] = None
    ) -> str:
        """
        Track an application error.

        Args:
            error_type: Type of error
            message: Error message
            metadata: Additional metadata about the error

        Returns:
            The ID of the tracked error

        Raises:
            Exception: If tracking fails
        """
        pass

    @abstractmethod
    async def get_usage_statistics(
        self, start_time: datetime = None, end_time: datetime = None
    ) -> dict[str, Any]:
        """
        Get usage statistics for a time period.

        Args:
            start_time: Start of the time period (None for all time)
            end_time: End of the time period (None for current time)

        Returns:
            Dictionary with usage statistics
        """
        pass

    @abstractmethod
    async def get_event_timeline(
        self, event_types: list[str] = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get a timeline of events.

        Args:
            event_types: Types of events to include (None for all)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        pass

    @abstractmethod
    async def get_frequent_errors(
        self, days: int = 7, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get most frequent errors in the given time period.

        Args:
            days: Number of days to look back
            limit: Maximum number of errors to return

        Returns:
            List of error dictionaries with count and frequency
        """
        pass

    @abstractmethod
    async def get_feature_usage(self) -> dict[str, Any]:
        """
        Get statistics about feature usage.

        Returns:
            Dictionary with feature usage statistics
        """
        pass

    @abstractmethod
    async def get_performance_metrics(
        self, metric_types: list[str] = None
    ) -> dict[str, Any]:
        """
        Get performance metrics for different operations.

        Args:
            metric_types: Types of metrics to include (None for all)

        Returns:
            Dictionary with performance metrics
        """
        pass

    @abstractmethod
    async def clear_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clear analytics data older than the specified number of days.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of records deleted
        """
        pass


class NotificationManager(ABC):
    """
    Interface for notification management.

    This interface defines methods for sending notifications to
    subscribers and managing notification delivery status.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the notification manager.

        Creates the necessary database tables and prepares the manager for use.

        Raises:
            NotificationError: If initialization fails
        """
        pass

    @abstractmethod
    async def add_subscriber(
        self, name: str | None = None, channels: list[Any] | None = None
    ) -> Any:
        """
        Register a new notification subscriber.

        Args:
            name: Optional name for the subscriber
            channels: Optional list of notification channels

        Returns:
            A new Subscriber instance

        Raises:
            NotificationError: If registration fails
        """
        pass

    @abstractmethod
    async def remove_subscriber(self, subscriber_id: str) -> None:
        """
        Remove a notification subscriber.

        Args:
            subscriber_id: ID of the subscriber to remove

        Raises:
            NotificationError: If removal fails
        """
        pass

    @abstractmethod
    async def get_subscriber(self, subscriber_id: str) -> Any:
        """
        Get a subscriber by ID.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            The subscriber details

        Raises:
            NotificationError: If subscriber not found or retrieval fails
        """
        pass

    @abstractmethod
    async def list_subscribers(self) -> list[Any]:
        """
        List all notification subscribers.

        Returns:
            List of all subscribers

        Raises:
            NotificationError: If retrieval fails
        """
        pass

    @abstractmethod
    async def update_subscriber(
        self,
        subscriber_id: str,
        name: str | None = None,
        channels: list[Any] | None = None,
        enabled: bool | None = None,
    ) -> Any:
        """
        Update subscriber details.

        Args:
            subscriber_id: ID of the subscriber to update
            name: New name (or None to not change)
            channels: New list of channels (or None to not change)
            enabled: New enabled status (or None to not change)

        Returns:
            Updated subscriber

        Raises:
            NotificationError: If update fails
        """
        pass

    @abstractmethod
    async def send_notification(
        self,
        message: str,
        level: Any = None,
        metadata: dict[str, Any] | None = None,
        sender_id: str | None = None,
        subscriber_ids: list[str] | None = None,
    ) -> Any:
        """
        Send a notification to subscribers.

        Args:
            message: Notification message
            level: Notification severity level
            metadata: Additional data to include
            sender_id: ID of the sender (component/module)
            subscriber_ids: Optional list of specific subscribers to notify
                            (if None, will send to all subscribers)

        Returns:
            The created notification

        Raises:
            NotificationError: If sending fails
        """
        pass

    @abstractmethod
    async def get_notification(self, notification_id: str) -> Any:
        """
        Retrieve a notification by ID.

        Args:
            notification_id: ID of the notification

        Returns:
            The notification

        Raises:
            NotificationError: If notification not found or retrieval fails
        """
        pass

    @abstractmethod
    async def get_notifications(
        self,
        subscriber_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Any]:
        """
        Get notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            List of notifications

        Raises:
            NotificationError: If retrieval fails
        """
        pass

    @abstractmethod
    async def mark_notification_read(
        self, notification_id: str, subscriber_id: str
    ) -> None:
        """
        Mark a notification as read for a specific subscriber.

        Args:
            notification_id: ID of the notification
            subscriber_id: ID of the subscriber

        Raises:
            NotificationError: If update fails
        """
        pass

    @abstractmethod
    async def mark_all_read(self, subscriber_id: str) -> int:
        """
        Mark all notifications as read for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of notifications marked as read

        Raises:
            NotificationError: If update fails
        """
        pass

    @abstractmethod
    async def delete_notification(self, notification_id: str) -> None:
        """
        Delete a notification from the system.

        Args:
            notification_id: ID of the notification to delete

        Raises:
            NotificationError: If deletion fails
        """
        pass

    @abstractmethod
    async def delete_all_for_subscriber(self, subscriber_id: str) -> int:
        """
        Delete all notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of notifications deleted

        Raises:
            NotificationError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_unread_count(self, subscriber_id: str) -> int:
        """
        Get the count of unread notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of unread notifications

        Raises:
            NotificationError: If retrieval fails
        """
        pass


class ContentAnalyzer(ABC):
    """
    Interface for analyzing file content.

    This interface defines methods for analyzing and extracting meaningful
    information from various types of file content.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the content analyzer.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def analyze_file(
        self,
        file_path: Path,
        content_type: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a file and extract meaningful information.

        Args:
            file_path: Path to the file to analyze
            content_type: Optional hint about the file's content type
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If analysis fails
        """
        pass

    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        content_type: str | None = None,
        file_path: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze text content and extract meaningful information.

        Args:
            text: The text content to analyze
            content_type: Optional hint about the content type
            file_path: Optional path to the source file (for context)
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            AnalysisError: If analysis fails
        """
        pass

    @abstractmethod
    async def summarize(
        self, content: str | Path, max_length: int = 500, format: str = "text"
    ) -> str:
        """
        Generate a summary of file content.

        Args:
            content: Either a string of content or a path to a file
            max_length: Maximum length of the summary in characters
            format: Output format (e.g., "text", "html", "markdown")

        Returns:
            Generated summary as a string

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If summarization fails
        """
        pass

    @abstractmethod
    async def extract_entities(
        self,
        content: str | Path,
        entity_types: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract named entities from content.

        Args:
            content: Either a string of content or a path to a file
            entity_types: Types of entities to extract (e.g., "person", "organization")
            min_confidence: Minimum confidence score for extracted entities

        Returns:
            Dictionary mapping entity types to lists of extracted entities

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If entity extraction fails
        """
        pass

    @abstractmethod
    async def extract_keywords(
        self, content: str | Path, max_keywords: int = 10, min_relevance: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Extract keywords or key phrases from content.

        Args:
            content: Either a string of content or a path to a file
            max_keywords: Maximum number of keywords to extract
            min_relevance: Minimum relevance score for keywords

        Returns:
            List of dictionaries containing keywords and their relevance scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If keyword extraction fails
        """
        pass

    @abstractmethod
    async def classify_content(
        self,
        content: str | Path,
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Classify content into categories.

        Args:
            content: Either a string of content or a path to a file
            taxonomy: Optional list of categories to use
            min_confidence: Minimum confidence score for classifications

        Returns:
            List of dictionaries containing categories and confidence scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If classification fails
        """
        pass

    @abstractmethod
    async def get_supported_file_types(self) -> list[str]:
        """
        Get a list of file types supported by this analyzer.

        Returns:
            List of supported file extensions or MIME types
        """
        pass

    @abstractmethod
    async def get_supported_content_types(self) -> list[str]:
        """
        Get a list of content types supported by this analyzer.

        Returns:
            List of supported content type identifiers
        """
        pass


class UserManager(ABC):
    """
    Interface for user management operations.

    This interface defines methods for managing users, including
    authentication, authorization, profile management, and preferences.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the user manager.

        This method should be called once during application startup
        to set up the user manager (e.g., connect to database, load
        data, initialize caches).

        Raises:
            UserError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the user manager and free resources.

        This method should be called during application shutdown.

        Raises:
            UserError: If closing fails
        """
        pass

    @abstractmethod
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "user",
    ) -> dict[str, Any]:
        """
        Create a new user.

        Args:
            username: Unique username for the user
            email: Email address for the user
            password: Password for the user (will be securely hashed)
            full_name: Full name of the user (optional)
            role: Role for the user (default: "user")

        Returns:
            Dictionary containing user information

        Raises:
            UserError: If user creation fails
            ValidationError: If input validation fails
        """
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """
        Get user information by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Get user information by username.

        Args:
            username: Username to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Get user information by email.

        Args:
            email: Email address to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def update_user(
        self, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update user information.

        Args:
            user_id: User ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated user information

        Raises:
            UserError: If update fails
            ValidationError: If input validation fails
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User ID to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            UserError: If deletion fails
        """
        pass

    @abstractmethod
    async def authenticate(
        self, username_or_email: str, password: str
    ) -> dict[str, Any] | None:
        """
        Authenticate a user with username/email and password.

        Args:
            username_or_email: Username or email address
            password: Password to verify

        Returns:
            Dictionary containing user information if authentication succeeds,
            None otherwise

        Raises:
            UserError: If authentication fails for a reason other than
                       invalid credentials
        """
        pass

    @abstractmethod
    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password change was successful, False otherwise

        Raises:
            UserError: If password change fails
            ValidationError: If password validation fails
        """
        pass

    @abstractmethod
    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User ID
            new_password: New password to set

        Returns:
            True if password reset was successful, False otherwise

        Raises:
            UserError: If password reset fails
            ValidationError: If password validation fails
        """
        pass

    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """
        Get user preferences.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing user preferences

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def update_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: Dictionary of preference updates

        Returns:
            Updated preferences dictionary

        Raises:
            UserError: If update fails
        """
        pass

    @abstractmethod
    async def check_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User ID to check
            permission: Permission to check for
            resource_id: Optional resource ID to check permission against

        Returns:
            True if the user has the permission, False otherwise

        Raises:
            UserError: If permission check fails
        """
        pass

    @abstractmethod
    async def grant_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Grant a permission to a user.

        Args:
            user_id: User ID to grant permission to
            permission: Permission to grant
            resource_id: Optional resource ID to grant permission on

        Returns:
            True if permission was granted, False otherwise

        Raises:
            UserError: If granting permission fails
        """
        pass

    @abstractmethod
    async def revoke_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Revoke a permission from a user.

        Args:
            user_id: User ID to revoke permission from
            permission: Permission to revoke
            resource_id: Optional resource ID to revoke permission from

        Returns:
            True if permission was revoked, False otherwise

        Raises:
            UserError: If revoking permission fails
        """
        pass

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all permissions for a user.

        Args:
            user_id: User ID to get permissions for

        Returns:
            List of permission dictionaries

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def list_users(
        self,
        query: str | None = None,
        role: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List users, optionally filtered.

        Args:
            query: Optional search query to filter results
            role: Optional role to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of user dictionaries

        Raises:
            UserError: If retrieval fails
        """
        pass

    @abstractmethod
    async def count_users(
        self, query: str | None = None, role: str | None = None
    ) -> int:
        """
        Count users, optionally filtered.

        Args:
            query: Optional search query to filter results
            role: Optional role to filter by

        Returns:
            Number of matching users

        Raises:
            UserError: If counting fails
        """
        pass


class SearchProvider(ABC):
    """
    Interface for search providers that implement specific search mechanisms.

    Search providers handle different types of searches like:
    - Text/keyword search
    - Regular expression search
    - Vector/semantic search
    - Metadata-based search

    Each provider has its own specialized algorithm and index structure.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the search provider.

        This method sets up any necessary resources for the provider to function.

        Raises:
            SearchError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the search provider and free resources.

        Raises:
            SearchError: If closing fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_supported_options(self) -> dict[str, Any]:
        """
        Get the options supported by this provider.

        Returns:
            Dictionary of supported options, their types, and descriptions
        """
        pass

    @abstractmethod
    async def get_provider_type(self) -> str:
        """
        Get the type of this search provider.

        Returns:
            String identifier for this provider type
        """
        pass


class IndexManager(ABC):
    """
    Interface for managing search indexes.

    The index manager handles:
    - Creating and maintaining search indexes
    - Adding, updating, and removing documents from indexes
    - Optimizing indexes for performance
    - Providing statistics about indexes
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the index manager.

        This method sets up any necessary resources and ensures
        indexes are in a consistent state.

        Raises:
            SearchError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the index manager and free resources.

        Raises:
            SearchError: If closing fails
        """
        pass

    @abstractmethod
    async def add_document(
        self, doc_id: str, content: str, metadata: dict[str, Any] = None
    ) -> None:
        """
        Add a document to the index.

        Args:
            doc_id: Unique document identifier
            content: Document content to be indexed
            metadata: Document metadata for specialized searches

        Raises:
            SearchError: If indexing fails
        """
        pass

    @abstractmethod
    async def update_document(
        self, doc_id: str, content: str = None, metadata: dict[str, Any] = None
    ) -> None:
        """
        Update an existing document in the index.

        Args:
            doc_id: Document identifier
            content: New document content (None to keep existing)
            metadata: New document metadata (None to keep existing)

        Raises:
            SearchError: If document doesn't exist or update fails
        """
        pass

    @abstractmethod
    async def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the index.

        Args:
            doc_id: Document identifier

        Raises:
            SearchError: If document doesn't exist or removal fails
        """
        pass

    @abstractmethod
    async def optimize_index(self) -> None:
        """
        Optimize the index for better performance.

        Raises:
            SearchError: If optimization fails
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the index.

        Returns:
            Dictionary with statistics like document count, index size, etc.

        Raises:
            SearchError: If retrieving stats fails
        """
        pass

    @abstractmethod
    async def clear_index(self) -> None:
        """
        Clear all documents from the index.

        Raises:
            SearchError: If clearing fails
        """
        pass


class ProjectReader(ABC):
    """
    Interface for project structure analysis and code reading.

    This interface defines methods for reading, analyzing, and summarizing
    code projects, extracting information about structure, functions,
    and other code elements.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the project reader.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the project reader."""
        pass

    @abstractmethod
    async def summarize_project(
        self,
        directory: Path,
        output_markdown: Path | None = None,
        output_json: Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate a summary of the project in the specified directory.

        Args:
            directory: Path to the project directory
            output_markdown: Optional path to save markdown summary
            output_json: Optional path to save JSON summary

        Returns:
            Dictionary containing project summary data

        Raises:
            ProjectReaderError: If summarization fails
            FileError: If the directory does not exist or is not readable
        """
        pass

    @abstractmethod
    async def convert_notebook(self, notebook_path: Path) -> str:
        """
        Convert a Jupyter notebook to a Python script.

        Args:
            notebook_path: Path to the notebook file

        Returns:
            String containing the Python script

        Raises:
            ProjectReaderError: If conversion fails
            FileError: If the notebook file does not exist or is not readable
        """
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.

        Args:
            text: The text to analyze

        Returns:
            Estimated token count
        """
        pass
