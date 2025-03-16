Code Style Guide
==============

This document defines the coding standards and best practices for The Aichemist Codex project. Following these guidelines ensures consistency across the codebase and makes collaboration easier.

Python Version
------------

The Aichemist Codex requires Python 3.10 or higher. This allows us to use modern Python features like:

* Pattern matching
* Improved type annotations including `|` for union types
* Improved error messages
* Better performance

Formatting and Linting
--------------------

We use the following tools for code quality:

* **Ruff**: For code linting and automatic formatting
* **mypy**: For static type checking
* **black**: As a code style reference (via Ruff)

Code Style Rules
--------------

General Guidelines
~~~~~~~~~~~~~~~~

* Maximum line length: 88 characters
* Use 4 spaces for indentation (no tabs)
* Use clear variable and function names
* Keep functions small and focused on a single responsibility
* Avoid deeply nested code (try to limit to 3-4 levels of nesting)
* Follow the principle of least surprise in API design
* Prefer clarity over cleverness

Imports
~~~~~~

Organize imports in this order, with a blank line between each group:

1. Standard library imports
2. Third-party library imports
3. Local application imports

Example:

.. code-block:: python

   import os
   import sys
   from pathlib import Path
   from typing import List, Dict, Optional, Any

   import numpy as np
   import pandas as pd
   from pydantic import BaseModel

   from backend.src.utils import logger
   from backend.src.config import settings

Naming Conventions
~~~~~~~~~~~~~~~~

* **Classes**: Use PascalCase (e.g., `FileManager`, `TagHierarchy`)
* **Functions, methods, variables**: Use snake_case (e.g., `process_file`, `tag_count`)
* **Constants**: Use UPPER_CASE (e.g., `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`)
* **Private members**: Prefix with a single underscore (e.g., `_internal_method`)
* **Very private members**: Prefix with double underscore (e.g., `__mangle_this`)
* **Type variables**: Use PascalCase, preferably with a single letter (e.g., `T`, `U`, `V`)

Type Annotations
~~~~~~~~~~~~~~

Use type annotations for all function parameters and return values:

.. code-block:: python

   def process_file(
       file_path: Path,
       options: Dict[str, Any] = None,
       timeout: Optional[float] = 30.0
   ) -> Dict[str, Any]:
       """Process a file and return metadata."""
       options = options or {}
       # function body
       return metadata

For Python 3.10+, use the new union syntax with `|`:

.. code-block:: python

   def get_tag(tag_id: int | None = None, tag_name: str | None = None) -> dict[str, Any] | None:
       """Get a tag by ID or name."""
       # function body

Docstrings
~~~~~~~~~

Use Google style docstrings:

.. code-block:: python

   def function_with_types_in_docstring(param1, param2):
       """Example function with docstring.

       This function does something useful.

       Args:
           param1: The first parameter.
           param2: The second parameter.

       Returns:
           The return value.

       Raises:
           ValueError: If param1 is not valid.
       """

Error Handling
~~~~~~~~~~~~

* Be explicit about exceptions that can be raised
* Use specific exception types, not just `Exception`
* Add context to exceptions when re-raising
* Document exceptions in docstrings

Example:

.. code-block:: python

   try:
       data = process_data(raw_data)
   except ValueError as e:
       raise ValueError(f"Failed to process {filename}: {e}") from e

Classes
~~~~~~

* Use dataclasses or Pydantic models where appropriate
* Implement special methods as needed (e.g., `__str__`, `__repr__`)
* Follow the SOLID principles
* Use composition over inheritance
* Document class responsibilities and assumptions

Testing
------

* Tests should be placed in the `tests/` directory, mirroring the structure of the code being tested
* Test file names should start with `test_`
* Use pytest for testing
* Aim for high test coverage, especially for core functionality
* Use fixtures and parametrization for cleaner tests

Example:

.. code-block:: python

   import pytest
   from pathlib import Path

   @pytest.fixture
   def sample_file():
       file_path = Path("tests/data/sample.txt")
       with open(file_path, 'w') as f:
           f.write("Sample content")
       yield file_path
       file_path.unlink()

   def test_process_file(sample_file):
       result = process_file(sample_file)
       assert result["mime_type"] == "text/plain"
       assert result["size"] > 0

Performance Considerations
------------------------

* Profile code for performance bottlenecks
* Use appropriate data structures for the task
* Consider memory usage for large datasets
* Use asynchronous programming where it makes sense
* Document performance characteristics for user-facing APIs

Documentation
-----------

* Document public APIs comprehensively
* Include examples for non-trivial functionality
* Keep documentation in sync with code changes
* Use clear and concise language
* Include both "how" and "why" in documentation

Conclusion
---------

This code style guide aims to create a consistent and maintainable codebase. When in doubt, prioritize readability and simplicity. Consistent code is easier to read, understand, and maintain.