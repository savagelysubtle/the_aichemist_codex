# Documentation for The Aichemist Codex

This directory contains the complete documentation for The Aichemist Codex
project.

## Documentation Structure

- **User Documentation**

  - `getting_started.rst` - Quick start guide for new users
  - `installation.rst` - Installation instructions
  - `usage.rst` - How to use the application
  - `cli_reference.rst` - Command-line interface reference
  - `configuration.rst` - Configuration options

- **Developer Documentation**

  - `development.rst` - General development guide
  - `api/` - API documentation (auto-generated)
  - `code_style.rst` - Coding style guidelines
  - `code_maintenance.md` - Code maintenance procedures
  - `code_review.md` - Code review guidelines
  - `contributing.rst` - How to contribute to the project

- **Project Information**

  - `roadmap.rst` - Future development plans
  - `roadmap/` - Detailed roadmap documents
  - `changelog.rst` - Version history and changes
  - `project_summary.md` - Project overview and summary

- **Technical Documentation**
  - `architecture.rst` - System architecture
  - `data_management.rst` - Data handling and storage
  - `directory_structure.rst` - Project structure explanation
  - `environment.rst` - Environment setup and requirements

## Building the Documentation

To build the documentation:

```bash
# Navigate to the docs directory
cd docs

# Build HTML documentation
make html

# The built documentation will be in _build/html/
```

## Documentation Tooling

- Documentation is built using [Sphinx](https://www.sphinx-doc.org/)
- API documentation is auto-generated from code docstrings
- Both reStructuredText (.rst) and Markdown (.md) formats are supported

## Contributing to Documentation

When contributing to documentation:

1. Follow the existing style and formatting
2. Update the table of contents where necessary
3. Run spell-check before submitting changes
4. Test any code examples to ensure they work
5. Build the documentation locally to preview changes

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
