# Output Formatter Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The output_formatter module is responsible for formatting data in various output
formats. The key components include:

- **FormatterManager**: Main implementation that manages a collection of
  formatters
- **Formatters**:
  - **BaseFormatter**: Abstract base class for all formatters
  - **TextFormatter**: Formats data as plain text
  - **HtmlFormatter**: Formats data as HTML
  - **MarkdownFormatter**: Formats data as Markdown
  - **JsonFormatter**: Formats data as JSON
- Key functionalities:
  - Format conversion for various data types
  - Support for different output formats
  - Customizable formatting options
  - Formatter registration system

## Architectural Compliance

The output_formatter module demonstrates good alignment with the project's
architectural guidelines:

| Architectural Principle    | Status | Notes                                                                |
| -------------------------- | :----: | -------------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the domain layer                              |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection and service access            |
| **Interface-Based Design** |   ✅   | FormatterManager properly implements the OutputFormatter interface   |
| **Extensibility**          |   ✅   | Allows registration of custom formatters                             |
| **Separation of Concerns** |   ✅   | Clear separation between formatter manager and individual formatters |
| **Error Handling**         |   ✅   | Uses proper error handling throughout the module                     |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                    | Status | Issue                                                 |
| ----------------------- | :----: | ----------------------------------------------------- |
| **Style Customization** |   🔄   | Limited customization of styling parameters           |
| **Format Conversion**   |   ⚠️   | No direct conversion between output formats           |
| **Complex Data Types**  |   ⚠️   | Limited support for complex or nested data structures |
| **Pagination**          |   ❌   | No built-in pagination for large outputs              |
| **Image Support**       |   ❌   | Limited/no support for embedding images in formats    |
| **Schema Validation**   |   ❌   | No validation of data against expected schemas        |
| **Templating**          |   🔄   | Basic templating system could be enhanced             |

## Recommendations

### 1. Enhance Style Customization

- Implement comprehensive style configuration
- Support theme-based styling across formatters

```python
# domain/output_formatter/styles.py
class StyleManager:
    """Manager for output styles and themes."""

    def __init__(self):
        self._themes = {}
        self._register_default_themes()

    def _register_default_themes(self):
        """Register default themes."""
        self._themes = {
            "default": {
                "text": {
                    "heading_prefix": "== ",
                    "heading_suffix": " ==",
                    "bullet": "* ",
                    "indent": "  ",
                },
                "html": {
                    "font_family": "Arial, sans-serif",
                    "heading_color": "#333333",
                    "link_color": "#0066cc",
                    "background_color": "#ffffff",
                    "css_classes": {},
                },
                "markdown": {
                    "heading_style": "atx",  # atx (#) or setext (==)
                    "emphasis_style": "*",  # * or _
                    "strong_style": "**",  # ** or __
                    "link_style": "inline",  # inline or reference
                },
                "json": {
                    "indent": 2,
                    "sort_keys": True,
                    "ensure_ascii": False,
                },
            },
            "minimal": {
                "text": {
                    "heading_prefix": "",
                    "heading_suffix": ":",
                    "bullet": "- ",
                    "indent": " ",
                },
                "html": {
                    "font_family": "monospace",
                    "heading_color": "#000000",
                    "link_color": "#0000ee",
                    "background_color": "#ffffff",
                    "css_classes": {},
                },
                "markdown": {
                    "heading_style": "atx",
                    "emphasis_style": "_",
                    "strong_style": "__",
                    "link_style": "reference",
                },
                "json": {
                    "indent": 0,
                    "sort_keys": True,
                    "ensure_ascii": True,
                },
            },
        }

    def register_theme(self, name: str, theme: dict):
        """Register a custom theme."""
        if name in self._themes:
            raise ValueError(f"Theme already exists: {name}")

        self._themes[name] = theme

    def get_theme(self, name: str) -> dict:
        """Get a theme by name."""
        if name not in self._themes:
            raise ValueError(f"Unknown theme: {name}")

        return self._themes[name]

    def get_style(self, theme_name: str, format_type: str) -> dict:
        """Get style configuration for a specific format and theme."""
        theme = self.get_theme(theme_name)
        return theme.get(format_type, {})
```

### 2. Implement Format Conversion

- Add direct conversion between output formats
- Create a unified conversion interface

```python
# domain/output_formatter/converter.py
class FormatConverter:
    """Converter between different output formats."""

    def __init__(self, registry):
        self._registry = registry
        self._formatter_manager = registry.formatter_manager
        self._conversion_map = {
            # source_format -> target_format -> conversion_function
            "text": {
                "html": self._text_to_html,
                "markdown": self._text_to_markdown,
                "json": self._text_to_json,
            },
            "html": {
                "text": self._html_to_text,
                "markdown": self._html_to_markdown,
                "json": self._html_to_json,
            },
            "markdown": {
                "text": self._markdown_to_text,
                "html": self._markdown_to_html,
                "json": self._markdown_to_json,
            },
            "json": {
                "text": self._json_to_text,
                "html": self._json_to_html,
                "markdown": self._json_to_markdown,
            },
        }

    async def convert(self, content: str, source_format: str, target_format: str, options: dict = None) -> str:
        """
        Convert content from one format to another.

        Args:
            content: Content to convert
            source_format: Source format
            target_format: Target format
            options: Conversion options

        Returns:
            Converted content
        """
        if source_format == target_format:
            return content

        # Get conversion function
        source_map = self._conversion_map.get(source_format)
        if not source_map:
            raise ValueError(f"Unsupported source format: {source_format}")

        conversion_func = source_map.get(target_format)
        if not conversion_func:
            raise ValueError(f"Unsupported conversion: {source_format} -> {target_format}")

        # Apply conversion
        options = options or {}
        return await conversion_func(content, options)

    async def _text_to_html(self, content: str, options: dict) -> str:
        """Convert plain text to HTML."""
        # Replace newlines with <br> and spaces with &nbsp;
        import html
        escaped = html.escape(content)
        text_with_breaks = escaped.replace('\n', '<br>\n')

        # Wrap in a pre tag if monospace option is set
        if options.get('monospace', False):
            return f"<pre>{text_with_breaks}</pre>"

        # Otherwise replace spaces with &nbsp; only at start of lines
        text_with_spaces = text_with_breaks.replace('\n ', '\n&nbsp;')
        return f"<div>{text_with_spaces}</div>"

    async def _html_to_markdown(self, content: str, options: dict) -> str:
        """Convert HTML to Markdown."""
        try:
            import html2text
            converter = html2text.HTML2Text()
            converter.ignore_links = options.get('ignore_links', False)
            converter.ignore_images = options.get('ignore_images', False)
            converter.body_width = options.get('body_width', 0)
            return converter.handle(content)
        except ImportError:
            raise ImportError("html2text package is required for HTML to Markdown conversion")
```

### 3. Add Support for Complex Data Types

- Enhance formatters to handle complex data structures
- Add specialized formatters for different data types

```python
# domain/output_formatter/formatters/specialized/table_formatter.py
class TableFormatter:
    """Formatter for tabular data."""

    def format_table(self, data: list[dict], format_type: str, options: dict = None) -> str:
        """
        Format tabular data in the specified format.

        Args:
            data: List of dictionaries representing rows
            format_type: Output format type
            options: Formatting options

        Returns:
            Formatted table
        """
        options = options or {}
        formatter = self._get_formatter(format_type)
        if not formatter:
            raise ValueError(f"Unsupported format type: {format_type}")

        return formatter(data, options)

    def _get_formatter(self, format_type: str):
        """Get formatter function for the specified format type."""
        formatters = {
            "text": self._format_text_table,
            "html": self._format_html_table,
            "markdown": self._format_markdown_table,
            "json": self._format_json_table,
        }
        return formatters.get(format_type)

    def _format_text_table(self, data: list[dict], options: dict) -> str:
        """Format table as plain text."""
        if not data:
            return ""

        # Extract headers from first row
        headers = list(data[0].keys())

        # Calculate column widths
        col_widths = {header: len(header) for header in headers}
        for row in data:
            for header in headers:
                col_widths[header] = max(col_widths[header], len(str(row.get(header, ""))))

        # Format header row
        header_row = " | ".join(header.ljust(col_widths[header]) for header in headers)
        separator = "-+-".join("-" * col_widths[header] for header in headers)

        # Format data rows
        rows = []
        for row in data:
            formatted_row = " | ".join(
                str(row.get(header, "")).ljust(col_widths[header]) for header in headers
            )
            rows.append(formatted_row)

        # Combine all rows
        return "\n".join([header_row, separator] + rows)

# domain/output_formatter/formatters/specialized/tree_formatter.py
class TreeFormatter:
    """Formatter for hierarchical tree data."""

    def format_tree(self, data: dict, format_type: str, options: dict = None) -> str:
        """
        Format tree data in the specified format.

        Args:
            data: Hierarchical data with 'name' and 'children' keys
            format_type: Output format type
            options: Formatting options

        Returns:
            Formatted tree
        """
        options = options or {}
        formatter = self._get_formatter(format_type)
        if not formatter:
            raise ValueError(f"Unsupported format type: {format_type}")

        return formatter(data, options)
```

### 4. Implement Pagination

- Add support for paginating large outputs
- Create a unified pagination interface

```python
# domain/output_formatter/pagination.py
class Paginator:
    """Paginator for large output content."""

    def __init__(self, items_per_page: int = 10):
        self.items_per_page = items_per_page

    def paginate_items(self, items: list, page: int = 1) -> tuple[list, dict]:
        """
        Paginate a list of items.

        Args:
            items: List of items to paginate
            page: Page number (1-based)

        Returns:
            Tuple of (paginated_items, pagination_info)
        """
        if page < 1:
            page = 1

        total_items = len(items)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)

        if page > total_pages:
            page = total_pages

        start_idx = (page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)

        paginated_items = items[start_idx:end_idx]

        pagination_info = {
            "page": page,
            "items_per_page": self.items_per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_previous": page > 1,
            "has_next": page < total_pages,
            "previous_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
        }

        return paginated_items, pagination_info

    def format_pagination_controls(
        self, pagination_info: dict, format_type: str, options: dict = None
    ) -> str:
        """
        Format pagination controls in the specified format.

        Args:
            pagination_info: Pagination information
            format_type: Output format type
            options: Formatting options

        Returns:
            Formatted pagination controls
        """
        options = options or {}
        formatter = self._get_formatter(format_type)
        if not formatter:
            raise ValueError(f"Unsupported format type: {format_type}")

        return formatter(pagination_info, options)

    def _get_formatter(self, format_type: str):
        """Get formatter function for the specified format type."""
        formatters = {
            "text": self._format_text_pagination,
            "html": self._format_html_pagination,
            "markdown": self._format_markdown_pagination,
            "json": self._format_json_pagination,
        }
        return formatters.get(format_type)

    def _format_text_pagination(self, pagination_info: dict, options: dict) -> str:
        """Format pagination controls as plain text."""
        page = pagination_info["page"]
        total_pages = pagination_info["total_pages"]

        controls = [f"Page {page} of {total_pages}"]

        if pagination_info["has_previous"]:
            controls.append(f"Previous: {pagination_info['previous_page']}")

        if pagination_info["has_next"]:
            controls.append(f"Next: {pagination_info['next_page']}")

        return " | ".join(controls)
```

### 5. Add Image Support

- Implement image embedding in supported formats
- Create a unified image handling interface

```python
# domain/output_formatter/formatters/specialized/image_formatter.py
class ImageFormatter:
    """Formatter for image data."""

    def format_image(
        self, image_path: str, format_type: str, alt_text: str = "", options: dict = None
    ) -> str:
        """
        Format image in the specified output format.

        Args:
            image_path: Path to the image
            format_type: Output format type
            alt_text: Alternative text for the image
            options: Formatting options

        Returns:
            Formatted image reference or embed
        """
        options = options or {}
        formatter = self._get_formatter(format_type)
        if not formatter:
            raise ValueError(f"Unsupported format type: {format_type}")

        return formatter(image_path, alt_text, options)

    def _get_formatter(self, format_type: str):
        """Get formatter function for the specified format type."""
        formatters = {
            "text": self._format_text_image,
            "html": self._format_html_image,
            "markdown": self._format_markdown_image,
            "json": self._format_json_image,
        }
        return formatters.get(format_type)

    def _format_text_image(self, image_path: str, alt_text: str, options: dict) -> str:
        """Format image as plain text."""
        return f"[IMAGE: {alt_text or image_path}]"

    def _format_html_image(self, image_path: str, alt_text: str, options: dict) -> str:
        """Format image as HTML."""
        width = options.get("width", "")
        height = options.get("height", "")
        css_class = options.get("class", "")

        width_attr = f' width="{width}"' if width else ""
        height_attr = f' height="{height}"' if height else ""
        class_attr = f' class="{css_class}"' if css_class else ""

        return f'<img src="{image_path}" alt="{alt_text}"{width_attr}{height_attr}{class_attr}>'

    def _format_markdown_image(self, image_path: str, alt_text: str, options: dict) -> str:
        """Format image as Markdown."""
        return f"![{alt_text}]({image_path})"

    def _format_json_image(self, image_path: str, alt_text: str, options: dict) -> str:
        """Format image as JSON."""
        import json
        image_data = {
            "type": "image",
            "src": image_path,
            "alt": alt_text,
        }

        # Add additional attributes from options
        for key, value in options.items():
            if key not in image_data:
                image_data[key] = value

        return json.dumps(image_data)
```

### 6. Add Schema Validation

- Implement validation of data against expected schemas
- Support schema-based output formatting

```python
# domain/output_formatter/validation.py
class SchemaValidator:
    """Validator for data against schemas."""

    def __init__(self):
        self._schemas = {}

    def register_schema(self, schema_name: str, schema: dict):
        """Register a schema."""
        self._schemas[schema_name] = schema

    def get_schema(self, schema_name: str) -> dict:
        """Get a schema by name."""
        if schema_name not in self._schemas:
            raise ValueError(f"Unknown schema: {schema_name}")

        return self._schemas[schema_name]

    def validate(self, data: Any, schema_name: str) -> tuple[bool, list]:
        """
        Validate data against a schema.

        Args:
            data: Data to validate
            schema_name: Name of the schema to validate against

        Returns:
            Tuple of (is_valid, errors)
        """
        schema = self.get_schema(schema_name)

        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(data))
            return len(errors) == 0, errors
        except ImportError:
            raise ImportError("jsonschema package is required for schema validation")

class SchemaBasedFormatter:
    """Formatter for data based on schemas."""

    def __init__(self, registry):
        self._registry = registry
        self._validator = SchemaValidator()

    def register_schema(self, schema_name: str, schema: dict):
        """Register a schema."""
        self._validator.register_schema(schema_name, schema)

    async def format_data(
        self, data: Any, schema_name: str, format_type: str, options: dict = None
    ) -> str:
        """
        Format data based on a schema.

        Args:
            data: Data to format
            schema_name: Name of the schema to use
            format_type: Output format type
            options: Formatting options

        Returns:
            Formatted data
        """
        # Validate the data
        is_valid, errors = self._validator.validate(data, schema_name)
        if not is_valid:
            # Handle validation errors
            error_msg = "Data does not match the expected schema"
            error_details = [str(err) for err in errors]

            formatter = self._registry.formatter_manager.get_formatter(format_type)
            return formatter.format_error(error_msg, {"errors": error_details}, options)

        # Format the data based on the schema
        schema = self._validator.get_schema(schema_name)
        formatter = self._registry.formatter_manager.get_formatter(format_type)

        # Add schema information to options
        options = options or {}
        options["schema"] = schema

        return formatter.format_data(data, options)
```

### 7. Enhance Templating System

- Implement a more flexible templating system
- Support template inheritance and includes

```python
# domain/output_formatter/templating.py
class TemplateProvider:
    """Provider for formatting templates."""

    def __init__(self, registry):
        self._registry = registry
        self._templates = {}
        self._cache = {}

    def register_template(self, name: str, template: str, format_type: str):
        """Register a template."""
        if (name, format_type) in self._templates:
            raise ValueError(f"Template already exists: {name} ({format_type})")

        self._templates[(name, format_type)] = template
        # Clear cache for this template
        self._cache.pop((name, format_type), None)

    def get_template(self, name: str, format_type: str) -> str:
        """Get a template by name and format type."""
        key = (name, format_type)
        if key not in self._templates:
            raise ValueError(f"Unknown template: {name} ({format_type})")

        return self._templates[key]

    async def apply_template(
        self, data: Any, template_name: str, format_type: str, options: dict = None
    ) -> str:
        """
        Apply a template to data.

        Args:
            data: Data to format
            template_name: Name of the template to use
            format_type: Output format type
            options: Formatting options

        Returns:
            Formatted data
        """
        template = self.get_template(template_name, format_type)
        options = options or {}

        try:
            # Use Jinja2 for templating
            import jinja2

            # Check if we have a cached environment for this template
            key = (template_name, format_type)
            if key not in self._cache:
                env = jinja2.Environment(
                    autoescape=True,
                    trim_blocks=True,
                    lstrip_blocks=True
                )
                self._cache[key] = env.from_string(template)

            template_obj = self._cache[key]

            # Create context with data and options
            context = {
                "data": data,
                "options": options,
            }

            # Render the template
            return template_obj.render(**context)

        except ImportError:
            raise ImportError("jinja2 package is required for templating")
        except Exception as e:
            raise ValueError(f"Error applying template: {str(e)}")
```

## Implementation Plan

### Phase 1: Styling and Customization (2 weeks)

1. Implement style management system
2. Add theme support
3. Enhance existing formatters to use style system

### Phase 2: Complex Data Support (2 weeks)

1. Implement specialized formatters for complex data types
2. Add table and tree formatters
3. Enhance data structure handling

### Phase 3: Format Conversion and Validation (3 weeks)

1. Implement format converter
2. Add schema validation
3. Create schema-based formatter

### Phase 4: Advanced Features (3 weeks)

1. Add pagination support
2. Implement image handling
3. Enhance templating system

## Priority Matrix

| Improvement            | Impact | Effort | Priority |
| ---------------------- | :----: | :----: | :------: |
| Style Customization    |  High  | Medium |    1     |
| Complex Data Types     |  High  | Medium |    2     |
| Format Conversion      | Medium | Medium |    3     |
| Schema Validation      | Medium | Medium |    4     |
| Templating Enhancement | Medium |  High  |    5     |
| Pagination             |  Low   |  Low   |    6     |
| Image Support          |  Low   | Medium |    7     |
