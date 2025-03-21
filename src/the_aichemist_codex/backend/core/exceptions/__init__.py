"""
Exceptions for the AIChemist Codex application.

This module defines all the exceptions used in the application.
"""

# Import base exceptions
from .authentication_error import AuthenticationError, AuthorizationError
from .base import AiChemistError
from .config_error import ConfigError

# Import specific exceptions
from .file_error import DirectoryError, FileError, UnsafePathError
from .file_manager_error import FileManagerError
from .metadata_error import MetadataError
from .processing_error import (
    AsyncProcessingError,
    ChunkProcessingError,
    ProcessingError,
)
from .relationship_error import RelationshipError
from .search_error import SearchError
from .tagging_error import TaggingError

# Export all exceptions
__all__ = [
    "AiChemistError",
    "FileError",
    "DirectoryError",
    "UnsafePathError",
    "ConfigError",
    "ProcessingError",
    "AsyncProcessingError",
    "ChunkProcessingError",
    "SearchError",
    "MetadataError",
    "RelationshipError",
    "TaggingError",
    "AuthenticationError",
    "AuthorizationError",
    "FileManagerError",
]
