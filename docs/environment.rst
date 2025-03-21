==========================
Environment Utilities
==========================

The environment utilities in The Aichemist Codex provide functions to detect how the application is running and access environment-specific information. These utilities are crucial for ensuring that the application behaves correctly in different execution contexts.

Overview
========

The environment utilities consist of several key functions in the ``the_aichemist_codex.backend.utils.environment`` module:

- :func:`is_development_mode`: Detects if the application is running in development mode
- :func:`get_import_mode`: Determines how the package was imported
- :func:`get_project_root`: Gets the project root directory in any execution context
- :func:`get_package_dir`: Gets the package installation directory

These utilities help the application adapt its behavior based on how it's being run, whether directly from source code or as an installed package.

Development Mode Detection
=========================

The primary function for detecting the execution environment is ``is_development_mode()``. This function uses several strategies to determine if the code is running from source:

.. code-block:: python

    def is_development_mode() -> bool:
        """
        Detect if running in development mode (not installed as package).

        This checks if we're running from source directories or as an installed package.

        Returns:
            bool: True if running from source, False if installed as package
        """
        # Check explicit environment variable first
        if os.environ.get("AICHEMIST_DEV_MODE"):
            return True

        # Check if running from source directory structure
        module_path = Path(__file__).resolve()
        src_parent = "src"

        # If we're in a src/the_aichemist_codex structure, we're in development mode
        return src_parent in module_path.parts

The detection works in two ways:

1. **Environment Variable Check**: If the ``AICHEMIST_DEV_MODE`` environment variable is set, the application is considered to be in development mode
2. **Path Structure Analysis**: The function examines the file path to check if it's running from a ``src/`` directory structure

Import Mode
==========

Beyond just detecting development mode, the ``get_import_mode()`` function provides more specific information about how the package was imported:

.. code-block:: python

    def get_import_mode() -> str:
        """
        Determine how the package was imported.

        Returns:
            str: "package" if installed and imported as a package,
                 "standalone" if running from source,
                 "editable" if installed in development/editable mode
        """
        if is_development_mode():
            return "standalone"

        # Check for editable install
        try:
            import importlib.metadata
            import sys
            from importlib.util import find_spec

            # More reliable way to detect editable installs
            spec = find_spec("the_aichemist_codex")
            if spec and spec.origin:
                origin_path = Path(spec.origin).resolve()
                if "site-packages" not in str(origin_path) and "src" in origin_path.parts:
                    return "editable"
        except (ImportError, ModuleNotFoundError):
            pass

        return "package"

This function distinguishes between three modes:

1. **standalone**: Running directly from source (not installed)
2. **editable**: Installed in development mode with ``pip install -e .``
3. **package**: Installed normally with ``pip install .`` or from PyPI

Directory Resolution
===================

The environment utilities also provide functions to reliably determine important directory paths regardless of how the application is running:

.. code-block:: python

    def get_project_root() -> Path:
        """
        Get the project root directory regardless of execution context.

        This function builds on top of determine_project_root() from settings
        but adds additional logic specific to package vs. standalone mode.

        Returns:
            Path: The project root directory
        """
        # Use the existing project root detection
        return determine_project_root()

    def get_package_dir() -> Path:
        """
        Get the package installation directory when running as an installed package.

        Returns:
            Path: The package installation directory
        """
        # If in development mode, return the src/the_aichemist_codex directory
        if is_development_mode():
            return Path(__file__).resolve().parents[2]

        # If installed, return the site-packages directory for the package
        import the_aichemist_codex
        return Path(the_aichemist_codex.__file__).resolve().parent

These functions ensure that the application can always find its resources, regardless of how it's being executed.

Using Environment Utilities
==========================

Here are some examples of how to use the environment utilities in your code:

Basic Usage
----------

.. code-block:: python

    from the_aichemist_codex.backend.utils.environment import is_development_mode

    if is_development_mode():
        # Do development-specific setup
        print("Running in development mode")
    else:
        # Do production-specific setup
        print("Running in production mode")

Getting Import Mode
-----------------

.. code-block:: python

    from the_aichemist_codex.backend.utils.environment import get_import_mode

    mode = get_import_mode()

    if mode == "standalone":
        print("Running from source directory")
    elif mode == "editable":
        print("Running from editable install")
    elif mode == "package":
        print("Running from installed package")

Finding Directories
-----------------

.. code-block:: python

    from the_aichemist_codex.backend.utils.environment import get_project_root, get_package_dir

    # Get the project root directory
    root_dir = get_project_root()
    print(f"Project root: {root_dir}")

    # Get the package directory
    package_dir = get_package_dir()
    print(f"Package directory: {package_dir}")

Environment Variables
===================

The environment utilities respect the following environment variables:

- ``AICHEMIST_DEV_MODE``: Force development mode detection (set to any value)
- ``AICHEMIST_ROOT_DIR``: Override the project root directory detection
- ``AICHEMIST_DATA_DIR``: Override the data directory location

Implementation Details
====================

The environment utilities use several strategies to determine the execution context:

1. **Environment Variables**: Checking for specific environment variables that control behavior
2. **Module Inspection**: Using Python's module system to detect how the code is imported
3. **Path Analysis**: Examining file paths to determine if running from source structure
4. **Import Introspection**: Using importlib to determine package installation status

These strategies ensure reliable detection of the execution context across different platforms and installation methods.