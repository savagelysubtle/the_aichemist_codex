"""
Search-related error exceptions.

This module defines exceptions related to search operations.
"""

from typing import Any

from .base import AiChemistError


class SearchError(AiChemistError):
    """
    Exception raised when there is an error with search operations.

    Attributes:
        message: Error message
        query: Search query that caused the error (if applicable)
        error_code: Error code (default: search_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        query: str = "",
        error_code: str = "search_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            query: Search query that caused the error (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        if query:
            details["query"] = query

        super().__init__(message, error_code, details)

        self.query = query


class SearchSyntaxError(SearchError):
    """
    Exception raised when there is a syntax error in a search query.

    Attributes:
        message: Error message
        query: Search query with the syntax error
        error_code: Error code (default: search_syntax_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        query: str = "",
        error_code: str = "search_syntax_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            query: Search query with the syntax error
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message, query, error_code, details)


class SearchIndexError(SearchError):
    """
    Exception raised when there is an error with the search index.

    Attributes:
        message: Error message
        index_name: Name of the index (if applicable)
        error_code: Error code (default: search_index_error)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        index_name: str = "",
        error_code: str = "search_index_error",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            index_name: Name of the index (if applicable)
            error_code: Error code
            details: Additional error details
        """
        if details is None:
            details = {}

        details["index_name"] = index_name

        super().__init__(message, "", error_code, details)

        self.index_name = index_name
