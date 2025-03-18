"""
Text formatter for plain text output.

This module provides functionality for formatting data as plain text.
"""

import logging
import textwrap
from typing import Any, Dict, List, Optional, Union

from .base_formatter import BaseFormatter

logger = logging.getLogger(__name__)


class TextFormatter(BaseFormatter):
    """
    Formatter for plain text output.

    This class formats data as plain text with various styling options.
    """

    @property
    def format_type(self) -> str:
        """Get the formatter type identifier."""
        return "text"

    @property
    def mime_type(self) -> str:
        """Get the MIME type for the formatted output."""
        return "text/plain"

    @property
    def file_extension(self) -> str:
        """Get the file extension for the formatted output."""
        return "txt"

    def format_data(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format data as plain text.

        Args:
            data: Data to format
            options: Optional formatting options
                - indent