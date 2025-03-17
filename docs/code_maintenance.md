# Code Maintenance Guide

## Circular Import Resolution

The codebase previously had a number of circular import issues that have been
resolved. This document outlines the changes made and provides guidance for
maintaining the code structure to prevent future issues.

### Changes Made

1. **Package Structure Restructuring**

   - Changed the import paths from `backend.src.*` to
     `the_aichemist_codex.backend.*`
   - Reorganized the code into a proper package structure with proper namespaces

2. **Circular Import Resolution**

   - Resolved circular dependency between `config`, `settings`, and various
     other modules
   - Modified the following files to avoid circular imports:
     - `config_loader.py`: Now uses default values instead of importing from
       `settings.py`
     - `safety.py`: Now uses the `config` object directly
     - `change_history_manager.py`: Uses dynamic function to get data directory
     - `rollback_manager.py`: Uses function to determine the data directory path
     - `file_mover.py`: Uses a function to get data directory instead of
       importing from settings
     - Other file managers: Modified to follow the same pattern

3. **Directory Management Pattern**
   - Created `get_data_dir()` functions in modules that need access to the data
     directory
   - This avoids the need to import from `settings.py` which created circular
     dependencies

### Best Practices

1. **Import Guidelines**

   - Always use the full package path for imports:
     `from the_aichemist_codex.backend.module import Component`
   - Avoid cyclic dependencies by careful module design
   - When possible, use dependency injection rather than direct imports

2. **Dynamic Config Access**

   - When a module needs access to configuration values:
     - Option 1: Pass required config values as parameters
     - Option 2: Import the config object directly, not through settings
     - Option 3: Create a function to retrieve needed values dynamically

3. **Handling Directory Paths**

   - Use the `get_data_dir()` pattern to dynamically resolve directory paths
   - Example:

   ```python
   def get_data_dir():
       """Get the data directory path.

       This function avoids circular imports by dynamically
       retrieving the data directory path.
       """
       import os
       from pathlib import Path

       # Check for environment variable first
       env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
       if env_data_dir:
           return Path(env_data_dir)

       # Otherwise, use relative path from the current file
       from the_aichemist_codex.backend.config.config_loader import get_config
       config = get_config()
       return Path(config.get("data_dir", "data"))
   ```

4. **Using DirectoryManager**

   - The `DirectoryManager` class requires named parameters:

   ```python
   # Correct usage
   await directory_manager.ensure_directory(directory=path)

   # Incorrect usage
   await DirectoryManager.ensure_directory(path)  # Missing 'directory=' and using static call
   ```

### Common Pitfalls

1. **Static Method vs Instance Method Confusion**

   - Always check if a method is static or instance before calling it
   - Example: `DirectoryManager.ensure_directory()` is an instance method, not
     static

2. **Implicit Dependencies**

   - Avoid relying on globals or module-level imports for configuration
   - Use explicit dependencies where possible

3. **Test Import Paths**
   - When writing tests, use the same import paths as the main code
   - Use the full package path:
     `from the_aichemist_codex.backend.module import Component`

## Maintenance Tasks

When adding new features or modules, keep these guidelines in mind:

1. **Module Organization**

   - Place new modules in the appropriate directory based on their function
   - Follow the package structure outlined in the README

2. **Configuration Management**

   - Add new configuration options to `config_loader.py` with defaults
   - Access configuration through the `config` object, not through `settings.py`

3. **Testing**

   - Update test import paths to match the new structure
   - Ensure tests use the correct namespaces and package paths

4. **Documentation**
   - Update documentation to reflect new import paths and module organization
   - Document any complex dependency relationships

By following these guidelines, we can maintain a clean, circular-import-free
codebase that is easier to understand and extend.
