"""
Core exception classes for the application.

This module defines the exception classes used throughout the application.
These exceptions provide a consistent way of handling errors and
propagating them to the appropriate error handlers.
"""

from pathlib import Path
from typing import Any


class AiChemistError(Exception):
    """Base exception class for all application exceptions."""

    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            details: Additional details about the error (optional)
        """
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigError(AiChemistError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, config_key: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            config_key: The configuration key that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.config_key = config_key
        super().__init__(message, details)


class FileError(AiChemistError):
    """Exception raised for file-related errors."""

    def __init__(self, message: str, file_path: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            file_path: The path of the file that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.file_path = file_path
        super().__init__(message, details)


class DirectoryError(AiChemistError):
    """Exception raised for directory-related errors."""

    def __init__(self, message: str, directory_path: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            directory_path: The path of the directory that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.directory_path = directory_path
        super().__init__(message, details)


class UnsafePathError(FileError):
    """Exception raised when a path is deemed unsafe to access."""

    def __init__(self, message: str, path: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            path: The unsafe path (optional)
            details: Additional details about the error (optional)
        """
        super().__init__(message, path, details)


class CacheError(AiChemistError):
    """Exception raised for cache-related errors."""

    def __init__(self, message: str, cache_key: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            cache_key: The cache key that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.cache_key = cache_key
        super().__init__(message, details)


class MetadataError(AiChemistError):
    """Exception raised for metadata-related errors."""

    def __init__(self, message: str, file_path: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            file_path: The path of the file that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.file_path = file_path
        super().__init__(message, details)


class SearchError(AiChemistError):
    """Exception raised for search-related errors."""

    def __init__(
        self,
        message: str,
        provider_id: str | None = None,
        query: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize a SearchError.

        Args:
            message: Error message
            provider_id: ID of the search provider involved in the error
            query: Search query that caused the error
            operation: Operation that failed
            details: Additional error details
        """
        self.provider_id = provider_id
        self.query = query
        self.operation = operation
        self.details = details or {}
        super().__init__(message)


class ValidationError(AiChemistError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            field: The field that failed validation (optional)
            details: Additional details about the error (optional)
        """
        self.field = field
        super().__init__(message, details)


class TimeoutError(AiChemistError):
    """Exception raised when an operation times out."""

    def __init__(
        self,
        message: str,
        operation: str = None,
        timeout: float = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            operation: The operation that timed out (optional)
            timeout: The timeout value in seconds (optional)
            details: Additional details about the error (optional)
        """
        self.operation = operation
        self.timeout = timeout
        super().__init__(message, details)


class NetworkError(AiChemistError):
    """Exception raised for network-related errors."""

    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            url: The URL that caused the error (optional)
            status_code: The HTTP status code (optional)
            details: Additional details about the error (optional)
        """
        self.url = url
        self.status_code = status_code
        super().__init__(message, details)


class AuthenticationError(AiChemistError):
    """Exception raised for authentication errors."""

    def __init__(self, message: str, user: str = None, details: str = None):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            user: The user that failed authentication (optional)
            details: Additional details about the error (optional)
        """
        self.user = user
        super().__init__(message, details)


class AuthorizationError(AiChemistError):
    """Exception raised for authorization errors."""

    def __init__(
        self, message: str, user: str = None, resource: str = None, details: str = None
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            user: The user that failed authorization (optional)
            resource: The resource that was being accessed (optional)
            details: Additional details about the error (optional)
        """
        self.user = user
        self.resource = resource
        super().__init__(message, details)


class NotificationError(AiChemistError):
    """Exception raised for notification-related errors."""

    def __init__(
        self,
        message: str,
        notification_id: str = None,
        subscriber_id: str = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            notification_id: The ID of the notification (optional)
            subscriber_id: The ID of the subscriber (optional)
            details: Additional details about the error (optional)
        """
        self.notification_id = notification_id
        self.subscriber_id = subscriber_id
        super().__init__(message, details)


class TagError(AiChemistError):
    """Exception raised for tag-related errors."""

    def __init__(
        self,
        message: str,
        tag_name: str = None,
        tag_id: int = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            tag_name: The name of the tag that caused the error (optional)
            tag_id: The ID of the tag that caused the error (optional)
            details: Additional details about the error (optional)
        """
        self.tag_name = tag_name
        self.tag_id = tag_id
        super().__init__(message, details)


class RelationshipError(AiChemistError):
    """Exception raised for relationship-related errors."""

    def __init__(
        self,
        message: str,
        relationship_id: str = None,
        source_path: str = None,
        target_path: str = None,
        rel_type: str = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            relationship_id: The ID of the relationship that caused the error (optional)
            source_path: The source path of the relationship (optional)
            target_path: The target path of the relationship (optional)
            rel_type: The type of the relationship (optional)
            details: Additional details about the error (optional)
        """
        self.relationship_id = relationship_id
        self.source_path = source_path
        self.target_path = target_path
        self.rel_type = rel_type
        super().__init__(message, details)


class AnalysisError(AiChemistError):
    """Exception raised for content analysis errors."""

    def __init__(
        self,
        message: str,
        file_path: str = None,
        analyzer_type: str = None,
        content_type: str = None,
        details: str = None,
    ):
        """
        Initialize the exception.

        Args:
            message: A descriptive error message
            file_path: The path of the file that caused the error (optional)
            analyzer_type: The type of analyzer that encountered the error (optional)
            content_type: The content type being analyzed (optional)
            details: Additional details about the error (optional)
        """
        self.file_path = file_path
        self.analyzer_type = analyzer_type
        self.content_type = content_type
        super().__init__(message, details)


class UserError(AiChemistError):
    """Exception raised for user management related errors."""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        username: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize a UserError.

        Args:
            message: Error message
            user_id: ID of the user involved in the error
            username: Username of the user involved in the error
            operation: Operation that failed
            details: Additional error details
        """
        self.user_id = user_id
        self.username = username
        self.operation = operation
        self.details = details or {}
        super().__init__(message)


class ProjectReaderError(AiChemistError):
    """
    Base exception for errors related to project reading and analysis.

    This exception is raised when there are issues with reading,
    analyzing, or summarizing project files and code.
    """

    def __init__(
        self,
        message: str,
        file_path: str | Path | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize a ProjectReaderError.

        Args:
            message: Error message
            file_path: Path to the file that caused the error (optional)
            details: Additional error details (optional)
        """
        super().__init__(message, details)
        self.file_path = str(file_path) if file_path else None
