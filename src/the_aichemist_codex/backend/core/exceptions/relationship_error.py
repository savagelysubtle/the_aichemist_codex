"""
Relationship-related error exceptions.

This module defines exceptions related to relationship operations.
"""

from typing import Any

from .base import AiChemistError


class RelationshipError(AiChemistError):
    """
    Exception raised when there is an error with relationship operations.

    Attributes:
        message: Error message
        relationship_id: ID of the relationship (if applicable)
        error_code: Error code (default: relationship_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        relationship_id: str = "",
        error_code: str = "relationship_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            relationship_id: ID of the relationship (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if relationship_id:
            details["relationship_id"] = relationship_id

        super().__init__(message, error_code, details)

        self.relationship_id = relationship_id


class RelationshipNotFoundError(RelationshipError):
    """
    Exception raised when a relationship is not found.

    Attributes:
        message: Error message
        relationship_id: ID of the relationship that was not found
        error_code: Error code (default: relationship_not_found_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        relationship_id: str = "",
        error_code: str = "relationship_not_found_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            relationship_id: ID of the relationship that was not found
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, relationship_id, error_code, details)


class RelationshipValidationError(RelationshipError):
    """
    Exception raised when relationship validation fails.

    Attributes:
        message: Error message
        relationship_id: ID of the relationship that failed validation (if applicable)
        error_code: Error code (default: relationship_validation_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        relationship_id: str = "",
        error_code: str = "relationship_validation_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            relationship_id: ID of the relationship that failed validation (if applicable)
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, relationship_id, error_code, details)
