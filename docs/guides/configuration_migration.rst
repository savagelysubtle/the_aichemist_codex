Configuration Migration to pyproject.toml
=====================================

.. note::
   This document describes how we've migrated various configuration files into a consolidated ``pyproject.toml`` file to reduce configuration clutter and follow modern Python packaging practices.

Version: 1.0.0

Context
-------

The AIchemist Codex project has accumulated multiple configuration files in its root directory. This document outlines our approach to consolidating these configurations into a single ``pyproject.toml`` file, making the codebase cleaner and easier to navigate while following modern Python packaging best practices.

Requirements
-----------

* Centralize configuration in pyproject.toml where supported by tools
* Maintain compatibility with all development tools
* Document the migration process for future reference
* Explain which configurations remain separate and why
* Provide guidance for future configuration additions

Migrated Configuration Files
---------------------------

The following configuration files have been migrated to ``pyproject.toml``:

1. **CSpell Configuration**:

   * Original: ``cspell.config.yaml``
   * Target: ``[tool.cspell]`` section
   * Migration includes all spell checking settings and word lists

2. **Markdown Linting Rules**:

   * Original: ``.markdownlint.json``
   * Target: ``[tool.markdownlint]`` section
   * All linting rules maintained with identical settings

3. **Pre-commit Language Version**:

   * Original: ``.pre-commit-config.yaml`` (partial)
   * Target: ``[tool.pre-commit]`` section
   * Only migrated the ``default_language_version`` setting

Retained Configuration Files
---------------------------

Some configuration files were kept separate as they are better suited for their original format:

1. **Pre-commit Hook Configurations**:

   * File: ``.pre-commit-config.yaml``
   * Reason: The hook configurations are more compatible with pre-commit tools in YAML format
   * Note: Added a comment at the top to indicate partial migration

2. **GitHub Actions Workflows**:

   * Files: ``.github/workflows/*.yml``
   * Reason: These are specific to CI/CD and should remain as YAML files
   * Note: GitHub Actions specifically requires these files in their location

Migration Benefits
-----------------

The migration provides several key benefits:

* **Centralized Configuration**: Most project settings are now in a single file, making them easier to find and update.
* **Reduced Clutter**: Fewer files in the project root directory improves navigation.
* **Modern Packaging**: Following current Python best practices for package configuration.
* **Improved Tooling Support**: Many modern Python tools prioritize reading from ``pyproject.toml``.
* **Dependency Consistency**: Centralizing dependencies helps maintain consistency across development environments.

Using the Configuration
----------------------

Pre-commit
^^^^^^^^^^

Pre-commit is configured to use both ``pyproject.toml`` and ``.pre-commit-config.yaml``. The language version settings are in ``pyproject.toml``, while the hooks remain in the YAML file.

To run pre-commit:

.. code-block:: bash

   pre-commit run --all-files

Markdown Linting
^^^^^^^^^^^^^^^

Markdown linting rules have been migrated to ``pyproject.toml`` under the ``[tool.markdownlint]`` section. The linting will be enforced through pre-commit hooks.

Example configuration:

.. code-block:: toml

   [tool.markdownlint]
   default = true
   MD013   = false # Line length
   MD033   = false # Inline HTML
   MD036   = false # Emphasis used as header

Spell Checking (CSpell)
^^^^^^^^^^^^^^^^^^^^^^

Spell checking configuration has been migrated to ``pyproject.toml`` under the ``[tool.cspell]`` section.

Example configuration:

.. code-block:: toml

   [tool.cspell]
   version                = "0.2"
   ignore-paths           = []
   dictionary-definitions = []
   dictionaries           = []
   words                  = []
   ignore-words           = []
   imports                = []

Adding New Configuration
-----------------------

When adding new tools or configuration to the project:

1. **Prefer pyproject.toml**:

   * Add configuration to ``pyproject.toml`` if the tool supports it
   * Use the appropriate ``[tool.*]`` section for tool-specific configuration
   * Follow the TOML syntax for all entries

2. **Alternative Locations**:

   * If a tool doesn't support ``pyproject.toml``, consider these options in order:

     a. Place configuration in a subdirectory rather than the project root
     b. Use a configuration file following tool's conventions
     c. Document why the configuration couldn't be consolidated

3. **Documentation Updates**:

   * Document any new configuration files in this document
   * Explain why they couldn't be consolidated if applicable
   * Include examples of how to use the configuration

Troubleshooting
--------------

If you encounter issues with the migrated configuration:

1. **Syntax Validation**:

   * Validate the TOML syntax using the provided validation script:

     .. code-block:: python

        python validate_toml.py

   * Alternatively, use an online TOML validator

2. **Tool Configuration**:

   * Check that the tool is correctly looking for its configuration in ``pyproject.toml``
   * Some tools may need specific packages or plugins to read from ``pyproject.toml``
   * Verify the tool's documentation for ``pyproject.toml`` support

3. **Common Issues**:

   * Missing dependencies for tools that read configuration
   * Incorrect TOML syntax (e.g., indentation, quote styles)
   * Tool-specific formatting requirements not met
   * Outdated tool versions that don't support ``pyproject.toml``

Version History
--------------

+----------+------------+-------------+-------------------------+
| Version  | Date       | Author      | Changes                 |
+==========+============+=============+=========================+
| 1.0.0    | 2024-03-26 | AIchemist   | Initial documentation   |
+----------+------------+-------------+-------------------------+
