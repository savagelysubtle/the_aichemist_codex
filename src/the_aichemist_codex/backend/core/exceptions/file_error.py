"""
File-related error exceptions.

This module defines exceptions related to file operations.
"""

from typing import Any

from .base import AiChemistError


class FileError(AiChemistError):
    """
    Exception raised when there is an error with file operations.

    Attributes:
        message: Error message
        file_path: Path of the file that caused the error
        error_code: Error code (default: file_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "file_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file that caused the error
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["file_path"] = file_path

        super().__init__(message, error_code, details)

        self.file_path = file_path


class DirectoryError(FileError):
    """
    Exception raised when there is an error with directory operations.

    Attributes:
        message: Error message
        file_path: Path of the directory that caused the error
        error_code: Error code (default: directory_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "directory_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the directory that caused the error
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, file_path, error_code, details)


class UnsafePathError(FileError):
    """
    Exception raised when a file path is deemed unsafe.

    Attributes:
        message: Error message
        file_path: The unsafe file path
        error_code: Error code (default: unsafe_path_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "unsafe_path_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: The unsafe file path
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, file_path, error_code, details)
