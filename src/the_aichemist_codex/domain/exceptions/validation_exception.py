"""Validation exception for domain entities."""


class ValidationException(Exception):
    """Exception raised when domain entity validation fails.

    This exception is used when a domain entity fails validation due to
    missing or invalid attributes.

    Attributes:
        errors: A dictionary mapping field names to error messages
        message: A custom error message
    """

    def __init__(
        self, message: str = "Validation error", errors: dict[str, str] | None = None
    ) -> None:
        """Initialize a ValidationException.

        Args:
            message: The error message
            errors: A dictionary mapping field names to error messages
        """
        self.errors = errors or {}
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string containing the error message and any field errors
        """
        if not self.errors:
            return self.message

        error_details = ", ".join(
            f"{field}: {error}" for field, error in self.errors.items()
        )
        return f"{self.message}: {error_details}"

    def add_error(self, field: str, error: str) -> None:
        """Add a field error to the exception.

        Args:
            field: The name of the field with the error
            error: The error message
        """
        self.errors[field] = error
