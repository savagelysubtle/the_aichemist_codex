"""
Configuration-related error exceptions.

This module defines exceptions related to configuration operations.
"""

from typing import Any

from .base import AiChemistError


class ConfigError(AiChemistError):
    """
    Exception raised when there is an error with configuration.

    Attributes:
        message: Error message
        config_key: Configuration key that caused the error (if applicable)
        error_code: Error code (default: config_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        config_key: str = "",
        error_code: str = "config_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if config_key:
            details["config_key"] = config_key

        super().__init__(message, error_code, details)

        self.config_key = config_key


class ConfigValidationError(ConfigError):
    """
    Exception raised when configuration validation fails.

    Attributes:
        message: Error message
        config_key: Configuration key that failed validation
        error_code: Error code (default: config_validation_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        config_key: str = "",
        error_code: str = "config_validation_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            config_key: Configuration key that failed validation
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, config_key, error_code, details)


class ConfigFileError(ConfigError):
    """
    Exception raised when there is an error with a configuration file.

    Attributes:
        message: Error message
        file_path: Path to the configuration file
        error_code: Error code (default: config_file_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        error_code: str = "config_file_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            file_path: Path to the configuration file
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["file_path"] = file_path

        super().__init__(message, "", error_code, details)

        self.file_path = file_path
