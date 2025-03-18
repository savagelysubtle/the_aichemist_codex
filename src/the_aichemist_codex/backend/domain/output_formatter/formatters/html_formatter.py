"""
HTML formatter for output.

This module provides functionality for formatting data as HTML.
"""

import html
import logging
from typing import Any, Dict, List, Optional, Union

from .base_formatter import BaseFormatter

logger = logging.getLogger(__name__)


class HtmlFormatter(BaseFormatter):
    """
    Formatter for HTML output.

    This class formats data as HTML with appropriate markup.
    """

    @property
    def format_type(self) -> str:
        """Get the formatter type identifier."""
        return "html"

    @property
    def mime_type(self) -> str:
        """Get the MIME type for the formatted output."""
        return "text/html"

    @property
    def file_extension(self) -> str:
        """Get the file extension for the formatted output."""
        return "html"

    def format_data(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format data as HTML.

        Args:
            data: Data to format
            options: Optional formatting options
                - full_page: Whether to include HTML/head/body tags (default: False)
                - css: Custom CSS styles (default: None)
                - title: Page title for full page (default: "Data Output")

        Returns:
            Formatted HTML string
        """
        options = options or {}
        full_page = options.get("full_page", False)
        css = options.get("css", "")
        title = options.get("title", "Data Output")

        # Format the content based on its type
        if data is None:
            content = "<span class='null'>None</span>"
        elif isinstance(data, (int, float, bool)):
            content = f"<span class='literal'>{data}</span>"
        elif isinstance(data, str):
            # Check if this is already HTML
            if data.strip().startswith("<") and data.strip().endswith(">"):
                content = data
            else:
                # Escape and preserve newlines
                escaped = html.escape(data)
                content = f"<div class='text'>{escaped.replace('\n', '<br>')}</div>"
        elif isinstance(data, dict):
            content = self._format_dict(data, options)
        elif isinstance(data, list):
            content = self.format_list(data, options)
        else:
            # For other types, use string representation
            content = f"<span class='literal'>{html.escape(str(data))}</span>"

        # Wrap in a full HTML page if requested
        if full_page:
            default_css = """
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                .null { color: #999; font-style: italic; }
                .literal { color: #0000cc; font-family: monospace; }
                .key { font-weight: bold; color: #333; }
                .text { white-space: pre-wrap; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .error { color: #cc0000; font-weight: bold; }
                .error-details { margin-left: 20px; color: #666; }
                ul { margin-top: 5px; }
                li { margin-bottom: 5px; }
            """

            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <style>
        {default_css}
        {css}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""
        else:
            return content

    def format_list(
        self,
        items: List[Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a list of items as HTML.

        Args:
            items: List of items to format
            options: Optional formatting options
                - ordered: Whether to use ordered list (default: False)
                - class_name: CSS class for the list (default: None)

        Returns:
            Formatted HTML string
        """
        if not items:
            return "<div class='empty-list'>(Empty list)</div>"

        options = options or {}
        ordered = options.get("ordered", False)
        class_name = options.get("class_name", "")

        # Create a new options dict for nested items
        nested_options = options.copy()

        # Use ordered or unordered list based on options
        tag = "ol" if ordered else "ul"
        class_attr = f" class='{class_name}'" if class_name else ""

        list_items = []
        for item in items:
            # Format each item
            item_html = self.format_data(item, nested_options)
            list_items.append(f"<li>{item_html}</li>")

        return f"<{tag}{class_attr}>\n  " + "\n  ".join(list_items) + f"\n</{tag}>"

    def format_table(
        self,
        data: List[Dict[str, Any]],
        headers: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format tabular data as an HTML table.

        Args:
            data: List of dictionaries representing rows
            headers: Optional list of column headers (uses dict keys if None)
            options: Optional formatting options
                - class_name: CSS class for the table (default: "data-table")
                - caption: Table caption (default: None)
                - sortable: Whether to make the table sortable with JS (default: False)

        Returns:
            Formatted HTML string
        """
        if not data:
            return "<div class='empty-table'>(Empty table)</div>"

        options = options or {}
        class_name = options.get("class_name", "data-table")
        caption = options.get("caption", "")
        sortable = options.get("sortable", False)

        # Get headers from first row if not provided
        if not headers and data:
            headers = list(data[0].keys())

        if not headers:
            return "<div class='empty-table'>(Empty table - no headers)</div>"

        # Start building the HTML table
        html_parts = []

        # Add table tag with class
        html_parts.append(f"<table class='{class_name}'>")

        # Add caption if provided
        if caption:
            html_parts.append(f"  <caption>{html.escape(caption)}</caption>")

        # Add headers
        html_parts.append("  <thead>")
        html_parts.append("    <tr>")
        for header in headers:
            if sortable:
                html_parts.append(f"      <th data-sort='{html.escape(header)}'>{html.escape(header)}</th>")
            else:
                html_parts.append(f"      <th>{html.escape(header)}</th>")
        html_parts.append("    </tr>")
        html_parts.append("  </thead>")

        # Add body
        html_parts.append("  <tbody>")
        for row in data:
            html_parts.append("    <tr>")
            for header in headers:
                value = row.get(header, "")
                cell_content = self.format_data(value, {"full_page": False})
                html_parts.append(f"      <td>{cell_content}</td>")
            html_parts.append("    </tr>")
        html_parts.append("  </tbody>")

        # Close table
        html_parts.append("</table>")

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
            html_parts.append(js)

        return "\n".join(html_parts)

    def format_error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format an error message as HTML.

        Args:
            message: Error message
            details: Optional error details
            options: Optional formatting options
                - show_details: Whether to show error details (default: True)

        Returns:
            Formatted HTML string
        """
        options = options or {}
        show_details = options.get("show_details", True)

        html_parts = [f"<div class='error'>ERROR: {html.escape(message)}</div>"]

        if details and show_details:
            html_parts.append("<div class='error-details'>")
            html_parts.append("  <h3>Details:</h3>")
            html_parts.append("  <ul>")

            for key, value in details.items():
                html_parts.append(f"    <li><strong>{html.escape(key)}:</strong> {html.escape(str(value))}</li>")

            html_parts.append("  </ul>")
            html_parts.append("</div>")

        return "\n".join(html_parts)

    def _format_dict(
        self,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a dictionary as HTML.

        Args:
            data: Dictionary to format
            options: Formatting options

        Returns:
            Formatted HTML string
        """
        if not data:
            return "<div class='empty-dict'>(Empty dictionary)</div>"

        options = options or {}
        as_table = options.get("dict_as_table", True)

        # Create a new options dict for nested items
        nested_options = options.copy()
        nested_options["full_page"] = False

        if as_table:
            # Format as an HTML definition list
            html_parts = ["<dl class='dict'>"]

            for key, value in data.items():
                # Format the key and value
                html_parts.append(f"  <dt class='key'>{html.escape(str(key))}</dt>")
                html_parts.append(f"  <dd>{self.format_data(value, nested_options)}</dd>")

            html_parts.append("</dl>")
            return "\n".join(html_parts)
        else:
            # Format as a simple div with key-value pairs
            html_parts = ["<div class='dict'>"]

            for key, value in data.items():
                # Format each key-value pair
                value_html = self.format_data(value, nested_options)
                html_parts.append(f"  <div class='kv-pair'><span class='key'>{html.escape(str(key))}:</span> {value_html}</div>")

            html_parts.append("</div>")
            return "\n".join(html_parts)
