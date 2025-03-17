===================
Directory Structure
===================

This document explains the directory structure of The Aichemist Codex, including:

1. Project directory layout
2. Source code organization
3. Data directory structure
4. Testing layout

Project Layout
=============

The Aichemist Codex follows a modern Python project structure:

.. code-block:: text

    the_aichemist_codex/              # Root project directory
    ├── src/                          # Source code package
    │   └── the_aichemist_codex/      # Main package
    │       ├── __init__.py           # Package initialization
    │       ├── __main__.py           # Entry point for direct execution
    │       └── backend/              # Backend modules
    │           ├── config/           # Configuration management
    │           ├── file_manager/     # File operations and organization
    │           ├── metadata/         # Metadata extraction and management
    │           ├── search/           # Search functionality
    │           ├── relationships/    # File relationship mapping
    │           ├── tagging/          # Auto-tagging capabilities
    │           └── utils/            # Utility functions
    ├── tests/                        # Test suite
    │   ├── unit/                     # Unit tests
    │   ├── integration/              # Integration tests
    │   └── conftest.py               # Test fixtures and configuration
    ├── docs/                         # Documentation
    │   ├── api/                      # API reference documentation
    │   ├── tutorials/                # Tutorials
    │   └── conf.py                   # Sphinx configuration
    ├── bin/                          # Executable scripts
    │   └── codex                     # CLI executable
    ├── .gitignore                    # Git ignore file
    ├── LICENSE                       # License file
    ├── MANIFEST.in                   # Package manifest
    ├── Makefile                      # Development tasks
    ├── pyproject.toml                # Project configuration
    └── README.md                     # Project overview

Import Paths
===========

When using or extending The Aichemist Codex, use the full package path for imports:

.. code-block:: python

    # Correct import pattern
    from the_aichemist_codex.backend.config import settings
    from the_aichemist_codex.backend.file_manager import FileManager

    # Incorrect - avoid these patterns
    from backend.src.config import settings         # Old path structure
    from ..config import settings                   # Relative import across package boundaries

Within a subpackage, you can use relative imports for closely related modules:

.. code-block:: python

    # For imports within the same subpackage, relative imports are acceptable
    from .file_mover import FileMover               # Same subpackage
    from ..utils.common import get_file_hash        # Parent package reference

For configuration and settings, use the recommended patterns to avoid circular imports:

.. code-block:: python

    # Preferred pattern for accessing data directory
    def get_data_dir():
        import os
        from pathlib import Path

        # Check environment variable first
        env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
        if env_data_dir:
            return Path(env_data_dir)

        # Then check config
        from the_aichemist_codex.backend.config.config_loader import get_config
        config = get_config()
        return Path(config.get("data_dir", "data"))

    # Example usage
    data_dir = get_data_dir()

Source Code Organization
=======================

The source code is organized in a logical structure inside the main package:

.. code-block:: text

    src/the_aichemist_codex/         # Main package
    ├── __init__.py                  # Package initialization
    ├── __main__.py                  # Direct execution entry point
    └── backend/                     # Backend modules
        ├── __init__.py              # Backend package initialization
        ├── cli.py                   # Command-line interface
        ├── main.py                  # Main application logic
        ├── config/                  # Configuration
        │   ├── __init__.py          # Package initialization
        │   ├── config_loader.py     # Configuration loading
        │   ├── logging_config.py    # Logging configuration
        │   └── settings.py          # Global settings
        ├── file_manager/            # File management
        ├── file_reader/             # File reading and parsing
        ├── search/                  # Search functionality
        ├── models/                  # Data models
        ├── tagging/                 # Tagging functionality
        ├── relationships/           # File relationships
        ├── metadata/                # Metadata extraction
        ├── ingest/                  # Content ingestion
        ├── rollback/                # Rollback and history
        └── utils/                   # Utility functions
            ├── __init__.py          # Package initialization
            ├── environment.py       # Environment detection
            └── validate_data_dir.py # Directory validation

Data Directory Structure
=======================

The application maintains a structured data directory for storing user data:

.. code-block:: text

    data_dir/                   # Base data directory
    ├── cache/                  # Cache files
    │   ├── embeddings/         # Embedding vectors
    │   └── thumbnails/         # File thumbnails
    ├── logs/                   # Application logs
    ├── versions/               # File version history
    ├── exports/                # Exported files
    ├── backup/                 # Backup files
    │   ├── rollback_temp/      # Temporary rollback files
    │   └── file_backups/       # File backups
    └── trash/                  # Deleted files

The data directory location can be configured through environment variables:

- ``AICHEMIST_DATA_DIR``: Directly sets the data directory
- ``AICHEMIST_ROOT_DIR``: Sets the project root, data dir will be ``<root>/data``

If not specified, the default locations are:

- Windows: ``%APPDATA%/AichemistCodex``
- macOS/Linux: ``~/.aichemist``

Testing Structure
===============

The testing structure is organized by test type:

.. code-block:: text

    tests/                         # Test root
    ├── conftest.py                # Shared test fixtures
    ├── unit/                      # Unit tests
    │   ├── config/                # Config tests
    │   ├── file_manager/          # File manager tests
    │   └── utils/                 # Utility tests
    ├── integration/               # Integration tests
    │   ├── cli/                   # CLI integration tests
    │   └── search/                # Search integration tests
    └── performance/               # Performance benchmarks

Documentation Structure
=====================

The documentation is organized into logical sections:

.. code-block:: text

    docs/                         # Documentation root
    ├── api/                      # API reference
    ├── tutorials/                # Detailed tutorials
    ├── _templates/               # Custom templates
    ├── _static/                  # Static assets
    ├── index.rst                 # Documentation index
    ├── installation.rst          # Installation guide
    ├── usage.rst                 # Usage guide
    ├── development.rst           # Development guide
    ├── environment.rst           # Environment documentation
    ├── configuration.rst         # Configuration documentation
    ├── data_management.rst       # Data management
    ├── cli_reference.rst         # CLI reference
    └── contributing.rst          # Contribution guide