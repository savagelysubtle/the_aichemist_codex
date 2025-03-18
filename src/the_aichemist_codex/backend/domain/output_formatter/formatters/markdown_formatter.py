"""
Markdown formatter for output.

This module provides functionality for formatting data as Markdown text.
"""

import logging
from typing import Any

from .base_formatter import BaseFormatter

logger = logging.getLogger(__name__)


class MarkdownFormatter(BaseFormatter):
    """
    Formatter for Markdown output.

    This class formats data as Markdown text with standard Markdown formatting.
    """

    @property
    def format_type(self) -> str:
        """Get the formatter type identifier."""
        return "markdown"

    @property
    def mime_type(self) -> str:
        """Get the MIME type for the formatted output."""
        return "text/markdown"

    @property
    def file_extension(self) -> str:
        """Get the file extension for the formatted output."""
        return "md"

    def format_data(self, data: Any, options: dict[str, Any] | None = None) -> str:
        """
        Format data as Markdown.

        Args:
            data: Data to format
            options: Optional formatting options
                - heading_level: Base heading level (default: 1)
                - code_lang: Language for code blocks (default: None)
                - wrap: Whether to wrap text (default: True)
                - width: Maximum line width (default: 80)

        Returns:
            Formatted string
        """
        options = options or {}
        heading_level = options.get("heading_level", 1)
        code_lang = options.get("code_lang", "")
        wrap = options.get("wrap", True)
        width = options.get("width", 80)

        # Handle different data types
        if data is None:
            return "`None`"

        if isinstance(data, (int, float, bool)):
            return f"`{data}`"
        elif isinstance(data, str):
            # Check if this is likely multi-line text
            if "\n" in data or len(data) > width:
                # Use a code block for multi-line text
                return f"```\n{data}\n```"
            else:
                return data
        elif isinstance(data, dict):
            return self._format_dict(data, options)
        elif isinstance(data, list):
            return self.format_list(data, options)
        else:
            # For other types, use string representation in code block
            return f"`{str(data)}`"

    def format_list(
        self, items: list[Any], options: dict[str, Any] | None = None
    ) -> str:
        """
        Format a list of items as Markdown.

        Args:
            items: List of items to format
            options: Optional formatting options
                - bullet: Bullet style (default: "- ")
                - numbered: Whether to use numbered list (default: False)

        Returns:
            Formatted string
        """
        if not items:
            return "Empty list"

        options = options or {}
        bullet = options.get("bullet", "- ")
        numbered = options.get("numbered", False)

        # Create a new options dict for nested items
        nested_options = options.copy()

        lines = []
        for i, item in enumerate(items):
            if numbered:
                prefix = f"{i + 1}. "
            else:
                prefix = bullet

            # Format the item
            item_text = self.format_data(item, nested_options)

            # For multi-line items, ensure proper Markdown list formatting
            item_lines = item_text.splitlines()
            if len(item_lines) > 1:
                # First line has the bullet
                lines.append(f"{prefix}{item_lines[0]}")
                # Subsequent lines need proper indentation to be part of the same list item
                for line in item_lines[1:]:
                    # In Markdown, indenting by at least 4 spaces makes it part of the previous list item
                    lines.append(f"    {line}")
            else:
                lines.append(f"{prefix}{item_text}")

        return "\n".join(lines)

    def format_table(
        self,
        data: list[dict[str, Any]],
        headers: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format tabular data as a Markdown table.

        Args:
            data: List of dictionaries representing rows
            headers: Optional list of column headers (uses dict keys if None)
            options: Optional formatting options
                - alignment: Column alignment, list of "left", "center", "right" (default: all "left")

        Returns:
            Formatted string
        """
        if not data:
            return "*Empty table*"

        options = options or {}

        # Get headers from first row if not provided
        if not headers and data:
            headers = list(data[0].keys())

        if not headers:
            return "*Empty table (no headers)*"

        # Set up column alignment
        alignments = options.get("alignment", ["left"] * len(headers))
        if len(alignments) < len(headers):
            alignments.extend(["left"] * (len(headers) - len(alignments)))

        # Convert data values to strings and calculate max width for each column
        str_data = []
        col_widths = [len(h) for h in headers]

        for row in data:
            str_row = {}
            for i, header in enumerate(headers):
                if header in row:
                    str_val = str(row[header])
                    str_row[header] = str_val
                    col_widths[i] = max(col_widths[i], len(str_val))
                else:
                    str_row[header] = ""
            str_data.append(str_row)

        # Build the table
        table_lines = []

        # Add header row
        header_line = "| "
        for i, header in enumerate(headers):
            header_line += header.ljust(col_widths[i]) + " | "
        table_lines.append(header_line)

        # Add separator row with alignment markers
        separator_line = "| "
        for i, width in enumerate(col_widths):
            if alignments[i] == "center":
                separator_line += ":" + "-" * (width - 2) + ":" + " | "
            elif alignments[i] == "right":
                separator_line += "-" * (width - 1) + ":" + " | "
            else:  # left align (default)
                separator_line += ":" + "-" * (width - 1) + " | "
        table_lines.append(separator_line)

        # Add data rows
        for row in str_data:
            data_line = "| "
            for i, header in enumerate(headers):
                val = row.get(header, "")
                if alignments[i] == "center":
                    data_line += val.center(col_widths[i]) + " | "
                elif alignments[i] == "right":
                    data_line += val.rjust(col_widths[i]) + " | "
                else:  # left align
                    data_line += val.ljust(col_widths[i]) + " | "
            table_lines.append(data_line)

        return "\n".join(table_lines)

    def format_error(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format an error message as Markdown.

        Args:
            message: Error message
            details: Optional error details
            options: Optional formatting options
                - show_details: Whether to show error details (default: True)

        Returns:
            Formatted string
        """
        options = options or {}
        show_details = options.get("show_details", True)

        lines = [f"**ERROR:** {message}"]

        if details and show_details:
            lines.append("")
            lines.append("**Details:**")

            # Format details as a Markdown list
            for key, value in details.items():
                lines.append(f"- **{key}:** {value}")

        return "\n".join(lines)

    def _format_dict(
        self, data: dict[str, Any], options: dict[str, Any] | None = None
    ) -> str:
        """
        Format a dictionary as Markdown.

        Args:
            data: Dictionary to format
            options: Formatting options

        Returns:
            Formatted string
        """
        if not data:
            return "*Empty dictionary*"

        options = options or {}
        as_list = options.get("dict_as_list", True)

        # Create a new options dict for nested items
        nested_options = options.copy()

        if as_list:
            lines = []
            for key, value in data.items():
                # Format the value
                value_text = self.format_data(value, nested_options)

                # For multi-line values, format appropriately
                value_lines = value_text.splitlines()
                if len(value_lines) > 1:
                    lines.append(f"- **{key}:**")
                    for line in value_lines:
                        lines.append(f"  {line}")
                else:
                    lines.append(f"- **{key}:** {value_text}")

            return "\n".join(lines)
        else:
            # Format as a code block
            lines = []
            for key, value in data.items():
                value_str = str(value).replace("\n", " ")
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                lines.append(f"{key}: {value_str}")

            return "```\n" + "\n".join(lines) + "\n```"
