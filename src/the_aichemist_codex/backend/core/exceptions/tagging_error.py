"""
Tagging-related error exceptions.

This module defines exceptions related to tagging operations.
"""

from typing import Any

from .base import AiChemistError


class TaggingError(AiChemistError):
    """
    Exception raised when there is an error with tagging operations.

    Attributes:
        message: Error message
        file_path: Path of the file associated with the tag operation (if applicable)
        error_code: Error code (default: tagging_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "tagging_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file associated with the tag operation (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if file_path:
            details["file_path"] = file_path

        super().__init__(message, error_code, details)

        self.file_path = file_path


class TagValidationError(TaggingError):
    """
    Exception raised when tag validation fails.

    Attributes:
        message: Error message
        tag: Tag that failed validation
        file_path: Path of the file associated with the tag (if applicable)
        error_code: Error code (default: tag_validation_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        tag: str = "",
        file_path: str = "",
        error_code: str = "tag_validation_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            tag: Tag that failed validation
            file_path: Path of the file associated with the tag (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["tag"] = tag

        super().__init__(message, file_path, error_code, details)

        self.tag = tag


class TagNotFoundError(TaggingError):
    """
    Exception raised when a tag is not found.

    Attributes:
        message: Error message
        tag: Tag that was not found
        file_path: Path of the file associated with the tag operation (if applicable)
        error_code: Error code (default: tag_not_found_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        tag: str = "",
        file_path: str = "",
        error_code: str = "tag_not_found_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            tag: Tag that was not found
            file_path: Path of the file associated with the tag operation (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["tag"] = tag

        super().__init__(message, file_path, error_code, details)

        self.tag = tag
