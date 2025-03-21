"""
Metadata-related error exceptions.

This module defines exceptions related to metadata operations.
"""

from typing import Any

from .base import AiChemistError


class MetadataError(AiChemistError):
    """
    Exception raised when there is an error with metadata operations.

    Attributes:
        message: Error message
        file_path: Path of the file associated with the metadata (if applicable)
        error_code: Error code (default: metadata_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "metadata_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file associated with the metadata (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if file_path:
            details["file_path"] = file_path

        super().__init__(message, error_code, details)

        self.file_path = file_path


class MetadataExtractionError(MetadataError):
    """
    Exception raised when metadata extraction fails.

    Attributes:
        message: Error message
        file_path: Path of the file that failed metadata extraction
        error_code: Error code (default: metadata_extraction_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "metadata_extraction_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file that failed metadata extraction
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, file_path, error_code, details)


class MetadataStorageError(MetadataError):
    """
    Exception raised when there is an error storing metadata.

    Attributes:
        message: Error message
        file_path: Path of the file associated with the metadata
        error_code: Error code (default: metadata_storage_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "metadata_storage_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file associated with the metadata
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, file_path, error_code, details)
