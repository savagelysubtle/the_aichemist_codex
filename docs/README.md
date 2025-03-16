# The Aichemist Codex Documentation

This directory contains the Sphinx documentation for The Aichemist Codex
project.

## Documentation Structure

- `api/` - API reference documentation (auto-generated)
- `_static/` - Static files (CSS, JavaScript, images)
- `_templates/` - Custom Sphinx templates
- `images/` - Images used in the documentation
- `conf.py` - Sphinx configuration
- `index.rst` - Main documentation page
- `generate_api_docs.py` - Script to auto-generate API documentation
- `build_docs.py` - Script to build the complete documentation

## Building the Documentation

### Automated Build

The easiest way to build the documentation is to use the provided
`build_docs.py` script:

```bash
# Navigate to the docs directory
cd docs

# Build HTML documentation
python build_docs.py

# Build with clean option (removes previous build)
python build_docs.py --clean

# Build PDF documentation (requires LaTeX)
python build_docs.py --format pdf
```

### Manual Build

If you prefer to build the documentation manually:

1. Generate API documentation:

   ```bash
   python generate_api_docs.py
   ```

2. Build the Sphinx documentation:

   ```bash
   # Use make (Linux/macOS)
   make html

   # Or use the make.bat file (Windows)
   .\make.bat html
   ```

## Docstring Guidelines

To ensure proper documentation generation, follow these docstring guidelines:

### Google Style (Preferred)

```python
def example_function(param1, param2):
    """This is a function example.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The result of the operation.

    Raises:
        ValueError: If param1 is invalid.
    """
    pass
```

### Type Annotations

Use Python type annotations for better documentation:

```python
def example_function(param1: str, param2: int) -> bool:
    """This is a function example with type annotations."""
    pass
```

## Adding New Documentation

1. Create a new `.rst` file in the appropriate directory
2. Add the file to the appropriate toctree in one of the existing `.rst` files
3. Run the build_docs.py script to verify your changes

## Automatic Documentation Building

Documentation is automatically built and deployed on each push to the main
branch using GitHub Actions. The workflow file is located at
`.github/workflows/docs.yml`.

The latest documentation is available at:

- [GitHub Pages](https://your-username.github.io/the_aichemist_codex/) (if
  GitHub Pages is enabled)

## Dependencies

The documentation system requires the following dependencies:

- Sphinx
- sphinx-autodoc-typehints
- sphinx-copybutton
- furo (Sphinx theme)

These can be installed with:

```bash
pip install sphinx sphinx-autodoc-typehints sphinx-copybutton furo
```

Or by installing the development dependencies:

```bash
pip install -e ".[dev]"
```
