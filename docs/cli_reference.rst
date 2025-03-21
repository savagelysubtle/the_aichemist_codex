CLI Reference
=============

This page provides a comprehensive reference for The Aichemist Codex command-line interface.

Command Structure
---------------

All commands follow this general structure:

.. code-block:: bash

   codex [command] [subcommand] [options] [arguments]

Global Options
------------

These options can be used with any command:

.. code-block:: text

   --help, -h       Show help message for a command
   --version, -v    Show version information
   --verbose        Enable verbose output
   --quiet          Suppress non-error output
   --config FILE    Specify a custom configuration file
   --log-level LVL  Set log level (debug, info, warning, error, critical)

Core Commands
-----------

``init``
~~~~~~~

Initialize a new codex at the specified path, creating the necessary directory structure and configuration.

.. code-block:: bash

   codex init [PATH]

Options:
  ``--template TEMPLATE``  Use a specific configuration template (default: standard)
  ``--force``              Override existing codex without confirmation

Examples:

.. code-block:: bash

   # Initialize in the current directory
   codex init .

   # Initialize in a specific directory with a custom template
   codex init ~/documents/research --template research

``add``
~~~~~~

Add files or directories to the codex, processing and indexing them.

.. code-block:: bash

   codex add [FILES_OR_DIRS...]

Options:
  ``--recursive, -r``      Process directories recursively
  ``--exclude PATTERN``    Exclude files matching the pattern
  ``--tag TAG``            Apply tags to all added files
  ``--no-index``           Add files without indexing them

Examples:

.. code-block:: bash

   # Add a specific file
   codex add document.pdf

   # Add multiple directories recursively
   codex add --recursive ~/documents ~/research

   # Add with tags
   codex add report.docx --tag report,important

``search``
~~~~~~~~

Search for content across all indexed files.

.. code-block:: bash

   codex search [OPTIONS] QUERY

Options:
  ``--method METHOD``      Search method (fulltext, fuzzy, semantic, regex)
  ``--case-sensitive``     Enable case-sensitive search
  ``--whole-word``         Match whole words only
  ``--tag TAG``            Limit search to files with specific tags
  ``--type TYPE``          Limit search to specific file types
  ``--limit N``            Limit results to N entries
  ``--format FORMAT``      Output format (text, json, csv)

Examples:

.. code-block:: bash

   # Basic fulltext search
   codex search "machine learning"

   # Fuzzy search
   codex search --method fuzzy "approximte term"

   # Semantic search limited to tagged files
   codex search --method semantic --tag research "neural networks"

   # Regex search with case sensitivity
   codex search --method regex --case-sensitive "Pattern[0-9]+"

Data Management Commands
---------------------

``data validate``
~~~~~~~~~~~~~~

Validate the data directory structure.

.. code-block:: bash

   codex data validate [OPTIONS]

Options:
  ``--fix``    Automatically fix validation issues

Examples:

.. code-block:: bash

   # Check the data directory
   codex data validate

   # Check and fix issues
   codex data validate --fix

``data repair``
~~~~~~~~~~~~

Repair the data directory structure by creating missing directories and fixing permissions.

.. code-block:: bash

   codex data repair [OPTIONS]

Options:
  ``--backup``    Create backup before repair (default: True)

Examples:

.. code-block:: bash

   # Repair with automatic backup
   codex data repair

   # Repair without backup
   codex data repair --backup=false

``data info``
~~~~~~~~~~

Show information about the data directory.

.. code-block:: bash

   codex data info [OPTIONS]

Options:
  ``--verbose, -v``    Show detailed information

Examples:

.. code-block:: bash

   # Show basic info
   codex data info

   # Show detailed info
   codex data info --verbose

Tagging Commands
--------------

``tag``
~~~~~

Manage tags for files.

Subcommands:
  ``--auto``          Automatically generate and apply tags
  ``--suggest``       Generate tag suggestions without applying
  ``--add TAGS``      Add specific tags to files
  ``--remove TAGS``   Remove tags from files
  ``--list``          List all tags for files

Examples:

.. code-block:: bash

   # Auto-tag files
   codex tag --auto ~/documents/*.pdf

   # Get tag suggestions
   codex tag --suggest report.docx

   # Add specific tags
   codex tag --add "important,research" document.pdf

   # Remove tags
   codex tag --remove "draft" *.docx

   # List tags for a file
   codex tag --list report.pdf

File Organization Commands
-----------------------

``organize``
~~~~~~~~~

Organize files according to defined rules.

.. code-block:: bash

   codex organize [DIRECTORY]

Options:
  ``--config FILE``     Use a specific rules configuration file
  ``--dry-run``         Show what would be done without making changes
  ``--confirm``         Actually perform the operations (override dry-run)
  ``--backup``          Create backups of files before moving (default: True)

Examples:

.. code-block:: bash

   # Dry run of organization
   codex organize ~/downloads

   # Actual organization
   codex organize ~/downloads --confirm

   # Use custom rules
   codex organize ~/documents --config rules.yaml --confirm

``dupes``
~~~~~~~

Find duplicate files.

.. code-block:: bash

   codex duplicates [DIRECTORY]

Options:
  ``--output FILE``     Output file to save results
  ``--method METHOD``   Method to use (hash, name, content)

Examples:

.. code-block:: bash

   # Find duplicates using hash method
   codex duplicates ~/documents

   # Find duplicates using content comparison and save results
   codex duplicates ~/downloads --method content --output dupes.json

Advanced Commands
--------------

``relationships``
~~~~~~~~~~~~~~

Analyze and manage file relationships.

Subcommands:
  ``map``        Generate a relationship map
  ``related``    Find files related to the specified file
  ``visualize``  Create a visual graph of relationships

Examples:

.. code-block:: bash

   # Generate relationship map
   codex relationships map ~/project

   # Find related files
   codex relationships related document.py

   # Create visualization
   codex relationships visualize ~/project --output graph.png

``notebooks``
~~~~~~~~~~

Convert Jupyter notebooks to other formats.

.. code-block:: bash

   codex notebooks [DIRECTORY]

Options:
  ``--output-format FORMAT``    Output format (py, md, html)
  ``--recursive``               Process subdirectories recursively

Examples:

.. code-block:: bash

   # Convert notebooks to Python files
   codex notebooks ~/notebooks

   # Convert notebooks to Markdown recursively
   codex notebooks ~/research --output-format md --recursive