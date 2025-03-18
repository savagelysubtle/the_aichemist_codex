"""
Base formatter interface for the output formatter system.

This module defines the base class for all formatters, providing a common
interface for formatting data in different ways.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseFormatter(ABC):
    """
    Base class for all formatters.

    This abstract class defines the interface that all formatters must implement
    for converting data to specific output formats.
    """

    @property
    @abstractmethod
    def format_type(self) -> str:
        """Get the formatter type identifier."""
        pass

    @property
    @abstractmethod
    def mime_type(self) -> str:
        """Get the MIME type for the formatted output."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for the formatted output."""
        pass

    @abstractmethod
    def format_data(self, data: Any, options: dict[str, Any] | None = None) -> str:
        """
        Format data according to the formatter's output type.

        Args:
            data: Data to format
            options: Optional formatting options

        Returns:
            Formatted string
        """
        pass

    @abstractmethod
    def format_list(
        self, items: list[Any], options: dict[str, Any] | None = None
    ) -> str:
        """
        Format a list of items.

        Args:
            items: List of items to format
            options: Optional formatting options

        Returns:
            Formatted string
        """
        pass

    @abstractmethod
    def format_table(
        self,
        data: list[dict[str, Any]],
        headers: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format tabular data.

        Args:
            data: List of dictionaries representing rows
            headers: Optional list of column headers
            options: Optional formatting options

        Returns:
            Formatted string
        """
        pass

    @abstractmethod
    def format_error(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format an error message.

        Args:
            message: Error message
            details: Optional error details
            options: Optional formatting options

        Returns:
            Formatted string
        """
        pass
