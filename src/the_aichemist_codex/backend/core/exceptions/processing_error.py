"""
Processing error exceptions.

This module defines exceptions related to file processing operations.
"""

from typing import Any

from .base import AiChemistError


class ProcessingError(AiChemistError):
    """
    Exception raised when there is an error during file processing.

    Attributes:
        message: Error message
        error_code: Error code (default: processing_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: str = "processing_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, error_code, details)


class AsyncProcessingError(ProcessingError):
    """
    Exception raised when there is an error during asynchronous file processing.

    Attributes:
        message: Error message
        error_code: Error code (default: async_processing_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: str = "async_processing_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, error_code, details)


class ChunkProcessingError(ProcessingError):
    """
    Exception raised when there is an error processing a specific chunk.

    Attributes:
        message: Error message
        chunk_index: Index of the chunk where the error occurred
        error_code: Error code (default: chunk_processing_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        chunk_index: int,
        error_code: str = "chunk_processing_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            chunk_index: Index of the chunk where the error occurred
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["chunk_index"] = chunk_index

        super().__init__(message, error_code, details)
