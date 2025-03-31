"""Repository exceptions for the AIchemist Codex domain."""

from typing import Any


class RepositoryError(Exception):
    """Exception raised when a repository operation fails.

    This exception is used to indicate errors related to repository operations,
    such as failures to save, retrieve, or delete entities.

    Attributes:
        entity_type: The type of entity involved in the operation
        operation: The operation that failed (e.g., 'save', 'get', 'delete')
        details: Additional details about the error
        entity_id: The ID of the entity involved, if applicable
        cause: The underlying exception that caused this error, if any
    """

    def __init__(
        self,
        message: str = "Repository operation failed",
        entity_type: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
        entity_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize a RepositoryError.

        Args:
            message: The error message
            entity_type: The type of entity involved in the operation
            operation: The operation that failed
            details: Additional details about the error
            entity_id: The ID of the entity involved, if applicable
            cause: The underlying exception that caused this error, if any
        """
        self.entity_type = entity_type
        self.operation = operation
        self.details = details or {}
        self.entity_id = entity_id
        self.cause = cause
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string containing the error message and any additional details
        """
        components = [self.message]

        if self.entity_type:
            components.append(f"Entity type: {self.entity_type}")

        if self.operation:
            components.append(f"Operation: {self.operation}")

        if self.entity_id:
            components.append(f"Entity ID: {self.entity_id}")

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            components.append(f"Details: {details_str}")

        if self.cause:
            components.append(f"Cause: {str(self.cause)}")

        return " | ".join(components)
