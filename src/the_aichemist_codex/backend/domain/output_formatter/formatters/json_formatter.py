"""
JSON formatter for output.

This module provides functionality for formatting data as JSON.
"""

import json
import logging
from typing import Any

from .base_formatter import BaseFormatter

logger = logging.getLogger(__name__)


class JsonFormatter(BaseFormatter):
    """
    Formatter for JSON output.

    This class formats data as JSON with optional pretty-printing and customization.
    """

    @property
    def format_type(self) -> str:
        """Get the formatter type identifier."""
        return "json"

    @property
    def mime_type(self) -> str:
        """Get the MIME type for the formatted output."""
        return "application/json"

    @property
    def file_extension(self) -> str:
        """Get the file extension for the formatted output."""
        return "json"

    def format_data(self, data: Any, options: dict[str, Any] | None = None) -> str:
        """
        Format data as JSON.

        Args:
            data: Data to format
            options: Optional formatting options
                - pretty_print: Whether to pretty-print the JSON (default: False)
                - indent: Indentation level for pretty-printing (default: 4)

        Returns:
            Formatted JSON string
        """
        options = options or {}
        pretty_print = options.get("pretty_print", False)
        indent = options.get("indent", 4)

        return json.dumps(data, indent=indent) if pretty_print else json.dumps(data)

    def format_list(
        self, items: list[Any], options: dict[str, Any] | None = None
    ) -> str:
        """
        Format a list of items as JSON.

        Args:
            items: List of items to format
            options: Optional formatting options
                - ordered: Whether to use ordered list (default: False)
                - class_name: CSS class for the list (default: None)

        Returns:
            Formatted JSON string
        """
        if not items:
            return "[]"

        options = options or {}
        ordered = options.get("ordered", False)
        class_name = options.get("class_name", "")

        # Create a new options dict for nested items
        nested_options = options.copy()

        # Use ordered or unordered list based on options
        tag = "ordered_list" if ordered else "list"
        class_attr = f" class='{class_name}'" if class_name else ""

        list_items = []
        for item in items:
            # Format each item
            item_json = self.format_data(item, nested_options)
            list_items.append(f"{item_json}")

        return f"{{{tag}{class_attr}: [{', '.join(list_items)}]}}"

    def format_table(
        self,
        data: list[dict[str, Any]],
        headers: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format tabular data as JSON.

        Args:
            data: List of dictionaries representing rows
            headers: Optional list of column headers (uses dict keys if None)
            options: Optional formatting options
                - class_name: CSS class for the table (default: "data-table")
                - caption: Table caption (default: None)
                - sortable: Whether to make the table sortable with JS (default: False)

        Returns:
            Formatted JSON string
        """
        if not data:
            return "[]"

        options = options or {}
        class_name = options.get("class_name", "data-table")
        caption = options.get("caption", "")
        sortable = options.get("sortable", False)

        # Get headers from first row if not provided
        if not headers and data:
            headers = list(data[0].keys())

        if not headers:
            return "[]"

        # Start building the JSON array
        json_parts = []

        # Add table caption if provided
        if caption:
            json_parts.append(f'"caption": "{caption}"')

        # Add table headers
        json_parts.append(
            f'"headers": [{", ".join([f"{header}" for header in headers])}]'
            if sortable
            else f'"headers": {headers}'
        )

        # Add table rows
        json_parts.append('"rows": [')
        for row in data:
            json_parts.append("  [")
            for header in headers:
                value = row.get(header, "")
                json_parts.append(f"{self.format_data(value, {'full_page': False})}")
                json_parts.append(",")
            json_parts[-1] = json_parts[-1][:-1] + "]"
            json_parts.append(",")
        json_parts[-1] = json_parts[-1][:-1] + "]"

        # Close JSON array
        json_parts.append("]")

        # Add JavaScript for sortable tables if requested
        if sortable:
            js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('table.data-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = header.dataset.sort;
                const rows = Array.from(table.querySelectorAll('tbody tr'));

                // Sort the rows
                rows.sort((a, b) => {
                    const aValue = a.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent;
                    const bValue = b.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent;

                    // Check if values are numbers
                    const aNum = parseFloat(aValue);
                    const bNum = parseFloat(bValue);

                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return aNum - bNum;
                    }

                    return aValue.localeCompare(bValue);
                });

                // Remove existing rows
                table.querySelector('tbody').innerHTML = '';

                // Add sorted rows
                rows.forEach(row => {
                    table.querySelector('tbody').appendChild(row);
                });
            });
        });
    });
});
</script>
"""
            json_parts.append(js)

        return f"{{{', '.join(json_parts)}}}"

    def format_error(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Format an error message as JSON.

        Args:
            message: Error message
            details: Optional error details
            options: Optional formatting options
                - show_details: Whether to show error details (default: True)

        Returns:
            Formatted JSON string
        """
        options = options or {}
        show_details = options.get("show_details", True)

        json_parts = [f'"error": "{message}"']

        if details and show_details:
            json_parts.append('"details": {')
            json_parts.append('  "h3": "Details:",')
            json_parts.append('  "ul": [')

            for key, value in details.items():
                json_parts.append(f'    "li": "<strong>{key}:</strong> {str(value)}"')

            json_parts.append("  ]")
            json_parts.append("}")

        json_parts.append("}")

        return f"{{{', '.join(json_parts)}}}"

    def _format_dict(
        self, data: dict[str, Any], options: dict[str, Any] | None = None
    ) -> str:
        """
        Format a dictionary as JSON.

        Args:
            data: Dictionary to format
            options: Formatting options

        Returns:
            Formatted JSON string
        """
        if not data:
            return "{}"

        options = options or {}
        as_table = options.get("dict_as_table", True)

        # Create a new options dict for nested items
        nested_options = options.copy()
        nested_options["full_page"] = False

        if as_table:
            # Format as an JSON definition list
            json_parts = ["{"]

            for key, value in data.items():
                # Format the key and value
                json_parts.append(f'"{key}": {self.format_data(value, nested_options)}')
                json_parts.append(",")

            json_parts[-1] = json_parts[-1][:-1] + "}"
            return "\n".join(json_parts)
        else:
            # Format as a simple JSON object with key-value pairs
            json_parts = ["{"]

            for key, value in data.items():
                # Format each key-value pair
                value_json = self.format_data(value, nested_options)
                json_parts.append(f'"{key}": {value_json}')
                json_parts.append(",")

            json_parts[-1] = json_parts[-1][:-1] + "}"
            return "\n".join(json_parts)
