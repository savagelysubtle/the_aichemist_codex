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

   from the_aichemist_codex.backend.utils import logger
   from the_aichemist_codex.backend.config import settings

Naming Conventions
~~~~~~~~~~~~~~~~

* **Classes**: Use PascalCase (e.g., `FileManager`, `