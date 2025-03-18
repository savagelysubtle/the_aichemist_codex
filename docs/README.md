# The AIchemist Codex - Documentation

This directory contains the documentation for The AIchemist Codex project.

## Documentation Structure

The documentation is organized as follows:

- `api/` - API reference documentation
  - `domain/` - Domain-driven modules documentation (current implementation)
  - Legacy module documentation (marked with "Legacy" in titles)
- `tutorials/` - Step-by-step guides for common tasks
- `usage/` - General usage documentation
- `development/` - Development guides and contributing information

## Building the Documentation

To build the documentation:

1. Activate your virtual environment:

   ```
   .\.venv\Scripts\Activate.ps1  # On Windows with PowerShell
   source .venv/bin/activate     # On Linux/macOS
   ```

2. Install the project with development dependencies:

   ```
   # If using pip
   pip install -e ".[dev]"

   # If using uv (recommended)
   uv pip install -e ".[dev]"
   ```

3. Navigate to the docs directory and build:

   ```
   cd docs
   make html
   ```

4. The built documentation will be available in `_build/html/index.html`

## Documentation Generation

The API documentation is automatically generated using the
`generate_api_docs.py` script based on the project's module structure. This
script:

1. Scans the project's backend directory
2. Creates RST files for each module
3. Updates the API index

## Legacy Documentation

Some documentation pages are marked as "Legacy" and point to the new
domain-driven structure. This is to help users transitioning from previous
versions of the codebase.

## Customizing the Documentation

To add custom documentation pages:

1. Create a new `.rst` file in the appropriate directory
2. Add your content using reStructuredText format
3. Include the page in the appropriate toctree in `index.rst` or other index
   files

## Theme and Configuration

The documentation uses the Furo theme and is configured in `conf.py`. Additional
extensions used include:

- `sphinx.ext.autodoc` - For automatic API documentation
- `sphinx.ext.autosectionlabel` - For automatic section labels
- `sphinx.ext.napoleon` - For Google-style docstrings
- `sphinx_copybutton` - For copy buttons on code blocks
