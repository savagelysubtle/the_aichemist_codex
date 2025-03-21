"""
File Manager error exceptions.

This module defines exceptions related to file management operations.
"""

from typing import Any

from .base import AiChemistError


class FileManagerError(AiChemistError):
    """
    Exception raised when there is an error with file management operations.

    Attributes:
        message: Error message
        file_path: Path of the file that caused the error (if applicable)
        operation: Name of the operation that failed (e.g., "move_file", "copy_file")
        error_code: Error code (default: file_manager_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        operation: str = "",
        error_code: str = "file_manager_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path of the file that caused the error (if applicable)
            operation: Name of the operation that failed
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation

        super().__init__(message, error_code, details)

        self.file_path = file_path
        self.operation = operation
