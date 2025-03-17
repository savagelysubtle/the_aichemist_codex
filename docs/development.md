# The Aichemist Codex - Development Guide

This guide explains how to work with The Aichemist Codex in both development and
installed modes.

## Running Modes

The Aichemist Codex supports multiple execution modes:

1. **Development Mode**: Running directly from source code
2. **Installed Mode**: Running as an installed package
3. **Editable Mode**: Installed with `pip install -e .` for development

## Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd the_aichemist_codex

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

## Running in Different Modes

### Direct Execution (Development Mode)

```bash
# Run the module directly
python -m the_aichemist_codex

# Run the CLI directly
python -m the_aichemist_codex.backend.cli

# Run with specific command
python -m the_aichemist_codex.backend.cli tree
```

### Installed Package Mode

After installing with `pip install .` or from PyPI:

```bash
# Use the entry point
codex

# Run a specific command
codex tree
```

## Environment Variables

The following environment variables control the application's behavior:

- `AICHEMIST_ROOT_DIR`: Override project root directory detection
- `AICHEMIST_DATA_DIR`: Override base data directory
- `AICHEMIST_CACHE_DIR`: Override cache directory
- `AICHEMIST_LOG_DIR`: Override logs directory
- `AICHEMIST_LOG_LEVEL`: Set logging level
- `AICHEMIST_DEV_MODE`: Force development mode (set to any value)

## Directory Structure

- `src/the_aichemist_codex/`: Main package source code
  - `backend/`: Backend modules for file operations and processing
    - `config/`: Configuration and settings
    - `file_manager/`: File management and operations
    - `utils/`: Utility functions and helpers
  - `cli/`: Command-line interface implementation
- `tests/`: Test suite
- `docs/`: Documentation
- `bin/`: Executable scripts

## Development Tools

- **Testing**: `pytest`
- **Linting**: `ruff check`
- **Formatting**: `ruff format`
- **Type Checking**: `mypy`

## Common Development Tasks

```bash
# Run tests
pytest

# Run linters and type checking
ruff check .
mypy .

# Format code
ruff format .
```

````

### 4. Create a Setup Scripts Directory

```python:src/the_aichemist_codex/bin/codex
#!/usr/bin/env python3
"""Executable wrapper for the Aichemist Codex CLI."""

from the_aichemist_codex.backend.cli import main

if __name__ == "__main__":
    main()
````

### 5. Update pyproject.toml Script Section

This would be a suggestion to update the scripts section of your pyproject.toml:

```toml
[project.scripts]
codex = "the_aichemist_codex.backend.cli:main"
```

## Next Steps

Would you like me to proceed with implementing these components? I'll start with
creating the `environment.py` utility, which is the foundation for the dual-mode
detection.
