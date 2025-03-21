"""
Authentication-related error exceptions.

This module defines exceptions related to authentication and authorization.
"""

from typing import Any

from .base import AiChemistError


class AuthenticationError(AiChemistError):
    """
    Exception raised when there is an error with authentication.

    Attributes:
        message: Error message
        user_id: ID of the user being authenticated (if available)
        error_code: Error code (default: authentication_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        user_id: str = "",
        error_code: str = "authentication_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            user_id: ID of the user being authenticated (if available)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["user_id"] = user_id

        super().__init__(message, error_code, details)

        self.user_id = user_id


class AuthorizationError(AuthenticationError):
    """
    Exception raised when there is an error with authorization.

    Attributes:
        message: Error message
        user_id: ID of the user being authorized (if available)
        resource: Resource the user is trying to access
        error_code: Error code (default: authorization_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        user_id: str = "",
        resource: str = "",
        error_code: str = "authorization_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            user_id: ID of the user being authorized (if available)
            resource: Resource the user is trying to access
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["resource"] = resource

        super().__init__(message, user_id, error_code, details)

        self.resource = resource
