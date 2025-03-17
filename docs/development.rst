==================================
The Aichemist Codex Development Guide
==================================

This guide explains how to work with The Aichemist Codex in both development and
installed modes.

Running Modes
============

The Aichemist Codex supports multiple execution modes:

1. **Development Mode**: Running directly from source code
2. **Installed Mode**: Running as an installed package
3. **Editable Mode**: Installed with ``pip install -e .`` for development

Setting Up Development Environment
================================

.. code-block:: bash

    # Clone the repository
    git clone <repository-url>
    cd the_aichemist_codex

    # Create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

    # Install in development mode with all dependencies
    pip install -e ".[dev]"

Running in Different Modes
=========================

Direct Execution (Development Mode)
----------------------------------

The easiest way to run the application in development mode is to use the ``run.py`` script:

.. code-block:: bash

    # Run the application using the run.py script
    python run.py

    # Run with specific command
    python run.py tree data/

You can also run the module directly:

.. code-block:: bash

    # Run the module directly
    python -m the_aichemist_codex

    # Run the CLI directly
    python -m the_aichemist_codex.backend.cli

    # Run with specific command
    python -m the_aichemist_codex.backend.cli tree

Installed Package Mode
--------------------

After installing with ``pip install .`` or from PyPI:

.. code-block:: bash

    # Use the entry point
    codex

    # Run a specific command
    codex tree

Environment Variables
===================

The following environment variables control the application's behavior:

- ``AICHEMIST_ROOT_DIR``: Override project root directory detection
- ``AICHEMIST_DATA_DIR``: Override base data directory
- ``AICHEMIST_CACHE_DIR``: Override cache directory
- ``AICHEMIST_LOG_DIR``: Override logs directory
- ``AICHEMIST_LOG_LEVEL``: Set logging level
- ``AICHEMIST_DEV_MODE``: Force development mode (set to any value)

Directory Structure
=================

- ``src/the_aichemist_codex/``: Main package source code
    - ``backend/``: Backend modules for file operations and processing
        - ``config/``: Configuration and settings
        - ``file_manager/``: File management and operations
        - ``utils/``: Utility functions and helpers
    - ``cli/``: Command-line interface implementation
- ``tests/``: Test suite
- ``docs/``: Documentation
- ``bin/``: Executable scripts

Development Tools
===============

- **Testing**: ``pytest``
- **Linting**: ``ruff check``
- **Formatting**: ``ruff format``
- **Type Checking**: ``mypy``

Common Development Tasks
=====================

.. code-block:: bash

    # Run tests
    pytest

    # Run linters and type checking
    ruff check .
    mypy .

    # Format code
    ruff format .

Data Directory Management
======================

The application provides commands to manage the data directory structure:

.. code-block:: bash

    # Validate the data directory structure
    python run.py data validate

    # Automatically fix issues in the data directory
    python run.py data validate --fix

    # Repair the data directory (creates backup by default)
    python run.py data repair

    # Show information about the data directory
    python run.py data info

    # Show detailed information
    python run.py data info --verbose

Detecting Execution Mode
=====================

The application automatically detects whether it's running in development or installed mode.
You can add runtime checks in your code using the environment utilities:

.. code-block:: python

    from the_aichemist_codex.backend.utils.environment import is_development_mode, get_import_mode

    # Check if running in development mode
    if is_development_mode():
        print("Running in development mode")

    # Get more specific import mode
    mode = get_import_mode()  # Returns "standalone", "editable", or "package"
    print(f"Import mode: {mode}")