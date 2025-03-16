Contributing
============

Thank you for your interest in contributing to The Aichemist Codex! This document provides guidelines and instructions for contributing to the project.

Getting Started
--------------

1. **Fork the repository**

   Create your own fork of the project on GitHub.

2. **Clone your fork**

   .. code-block:: bash

      git clone https://github.com/yourusername/the-aichemist-codex.git
      cd the-aichemist-codex

3. **Set up the development environment**

   .. code-block:: bash

      # Create and activate a virtual environment
      python -m venv .venv
      source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

      # Install dependencies
      pip install -e ".[dev]"

Development Workflow
------------------

1. **Create a new branch**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make your changes**

   * Write code that follows our coding standards
   * Add tests for your changes
   * Update documentation if necessary

3. **Run tests**

   .. code-block:: bash

      pytest

4. **Lint your code**

   .. code-block:: bash

      ruff check .
      ruff format .

5. **Commit your changes**

   .. code-block:: bash

      git add .
      git commit -m "Add descriptive commit message"

6. **Push to your fork**

   .. code-block:: bash

      git push origin feature/your-feature-name

7. **Create a pull request**

   Go to the GitHub page of your fork and create a pull request to the main repository.

Coding Standards
--------------

We follow PEP 8 coding style with some additional rules:

* Use 4 spaces for indentation (no tabs)
* Maximum line length of 88 characters
* Use type annotations for all function parameters and return values
* Use docstrings in Google style format
* Write descriptive variable names
* Keep functions small and focused

For detailed information, see our :doc:`code_style` guide.

Testing
------

All new features should include tests:

* Unit tests for individual functions and classes
* Integration tests for interactions between components
* Ensure all tests pass before submitting a pull request

Documentation
------------

Good documentation is crucial:

* Update existing docs or add new documentation for your changes
* Document all public APIs
* Include examples for non-trivial functionality
* Use clear and consistent language

To build documentation locally:

.. code-block:: bash

   cd docs
   make html

The HTML documentation will be in the ``_build/html`` directory.

Reporting Issues
--------------

If you find a bug or want to request a feature:

1. Check the GitHub issues to see if it's already reported
2. If not, create a new issue with:
   * A clear title
   * A detailed description
   * Steps to reproduce (for bugs)
   * Expected vs. actual behavior (for bugs)

Versioning
---------

We follow semantic versioning (MAJOR.MINOR.PATCH):

* MAJOR version for incompatible API changes
* MINOR version for new functionality in a backward-compatible manner
* PATCH version for backward-compatible bug fixes

License
------

By contributing to The Aichemist Codex, you agree that your contributions will be licensed under the project's MIT license.