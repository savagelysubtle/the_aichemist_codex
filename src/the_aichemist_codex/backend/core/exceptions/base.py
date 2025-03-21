"""
Base exceptions for the AIChemist Codex application.

This module defines the base exception class for all application exceptions.
"""

from typing import Any


class AiChemistError(Exception):
    """
    Base exception class for all AIChemist Codex application errors.

    Attributes:
        message: Error message
        error_code: Error code for identifying the error type
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: str = "general_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            error_code: Error code for identifying the error type
            details: Additional error details
        """
        super().__init__(message)

        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        """
        Get the string representation of the error.

        Returns:
            String representation of the error
        """
        if self.details:
            return f"{self.message} (code: {self.error_code}, details: {self.details})"
        return f"{self.message} (code: {self.error_code})"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the error to a dictionary representation.

        Returns:
            Dictionary representation of the error
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }
