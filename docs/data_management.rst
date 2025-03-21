Data Management
==============

The Aichemist Codex uses a standardized data directory structure to organize its files, metadata, and cache. This guide explains how data is stored, accessed, and managed.

Data Directory Structure
----------------------

The Aichemist Codex uses a structured data directory for all its operations. By default, this directory is created in the following location:

- **Windows**: ``%APPDATA%\AichemistCodex``
- **macOS/Linux**: ``~/.aichemist``

This location can be overridden with the ``AICHEMIST_DATA_DIR`` environment variable.

Standard Subdirectories
^^^^^^^^^^^^^^^^^^^^^

The data directory contains these standard subdirectories:

.. code-block:: text

    data/
    ├── cache/        # Cached data for improved performance
    ├── logs/         # Log files for troubleshooting
    ├── versions/     # File version history
    ├── exports/      # Exported data and reports
    ├── backup/       # Automatic backups
    └── trash/        # Files moved to trash

Each subdirectory serves a specific purpose:

- **cache**: Temporary files for performance optimization, including search indices, embedding vectors, and metadata caches
- **logs**: Application logs organized by date and component
- **versions**: Version history of files being tracked
- **exports**: Generated reports, visualizations, and data exports
- **backup**: Automatic backups created before potentially destructive operations
- **trash**: Files removed from the system but not permanently deleted

Environment Variables
-------------------

The following environment variables control data directory behavior:

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Variable
     - Description
     - Example
   * - ``AICHEMIST_DATA_DIR``
     - Sets the base data directory location
     - ``/data/aichemist``
   * - ``AICHEMIST_CACHE_DIR``
     - Override only the cache directory
     - ``/tmp/aichemist_cache``
   * - ``AICHEMIST_LOG_DIR``
     - Override only the logs directory
     - ``/var/log/aichemist``
   * - ``AICHEMIST_LOG_LEVEL``
     - Set the logging verbosity
     - ``DEBUG``
   * - ``AICHEMIST_DEV_MODE``
     - Force development mode
     - ``1``

These environment variables can be set in your shell or in a ``.env`` file in the project directory.

The DirectoryManager
------------------

Behind the scenes, The Aichemist Codex uses a ``DirectoryManager`` class to handle all directory operations. This ensures consistent access and validation across the application.

.. code-block:: python

    from the_aichemist_codex.backend.file_manager.directory_manager import DirectoryManager

    # Get the standard directory manager
    from the_aichemist_codex.backend.config.settings import directory_manager

    # Access standard directories
    cache_dir = directory_manager.get_dir("cache")
    logs_dir = directory_manager.get_dir("logs")

    # Get a file path in the base directory
    config_path = directory_manager.get_file_path("settings.json")

Managing Data Directories
-----------------------

The CLI provides several commands for managing data directories:

Validating the Directory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To check if your data directory is valid:

.. code-block:: bash

    codex data validate

This will report any issues with the directory structure. To automatically fix issues:

.. code-block:: bash

    codex data validate --fix

Repairing the Directory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To repair the directory structure (creates missing directories and sets correct permissions):

.. code-block:: bash

    codex data repair

By default, this creates a backup before making changes. To skip the backup:

.. code-block:: bash

    codex data repair --backup=false

Viewing Data Directory Information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To see information about your data directory:

.. code-block:: bash

    codex data info

For detailed information, including disk usage and file counts:

.. code-block:: bash

    codex data info --verbose

Development vs. Installed Mode
----------------------------

The Aichemist Codex can detect whether it's running in development mode or as an installed package, and adjust its behavior accordingly.

In development mode:
- Environment variables have higher priority
- More detailed logging is enabled by default
- The source code directories are used for resources

In installed mode:
- Standard locations are used by default
- Logging is less verbose
- Package-installed resources are used

This detection is automatic, but you can force development mode by setting the ``AICHEMIST_DEV_MODE`` environment variable.

Data Directory in API Usage
-------------------------

When using The Aichemist Codex as a library, you can customize the data directory:

.. code-block:: python

    from pathlib import Path
    from the_aichemist_codex.backend.file_manager.directory_manager import DirectoryManager

    # Create a custom directory manager
    custom_data_dir = Path("/path/to/custom/data")
    dir_manager = DirectoryManager(custom_data_dir)

    # Use it with other components
    from the_aichemist_codex.backend.tagging import TagManager
    tag_manager = TagManager(data_dir=dir_manager.get_dir("tags"))

Configuration Files
-----------------

The Aichemist Codex uses several configuration files stored in the data directory:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - File
     - Purpose
   * - ``.codexconfig``
     - Main configuration file (TOML format)
   * - ``secure_config.enc``
     - Encrypted configuration for sensitive settings
   * - ``sorting_rules.yaml``
     - File organization rules
   * - ``tagging_rules.json``
     - Rules for automatic tagging

The ``.env.template`` File
^^^^^^^^^^^^^^^^^^^^^^^^

The repository includes a ``.env.template`` file that shows all available environment variables with example values. Copy this to ``.env`` in your project directory to set local environment variables.