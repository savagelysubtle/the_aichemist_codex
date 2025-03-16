Installation
============

This guide covers the different ways to install The Aichemist Codex.

System Requirements
-----------------

* **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+, Fedora 34+)
* **Python**: Version 3.10 or higher
* **Disk Space**: At least 100MB for the base installation, plus space for your files
* **RAM**: 4GB minimum, 8GB recommended

Installation Methods
------------------

Using pip (Recommended)
~~~~~~~~~~~~~~~~~~~~~~

The simplest way to install The Aichemist Codex is using pip:

.. code-block:: bash

   pip install the-aichemist-codex

For development installations:

.. code-block:: bash

   git clone https://github.com/yourusername/the_aichemist_codex.git
   cd the_aichemist_codex
   pip install -e .

Using Poetry
~~~~~~~~~~~

If you prefer using Poetry for dependency management:

.. code-block:: bash

   # For using as a dependency in your project
   poetry add the-aichemist-codex

   # For development
   git clone https://github.com/yourusername/the_aichemist_codex.git
   cd the_aichemist_codex
   poetry install

From Source
~~~~~~~~~~

To install from source:

.. code-block:: bash

   git clone https://github.com/yourusername/the_aichemist_codex.git
   cd the_aichemist_codex
   python setup.py install

Docker Installation
~~~~~~~~~~~~~~~~~

We also provide a Docker image for containerized usage:

.. code-block:: bash

   docker pull aichemist/codex:latest
   docker run -v /path/to/your/files:/data aichemist/codex

Verify Installation
-----------------

To verify that The Aichemist Codex was installed correctly:

.. code-block:: bash

   aichemist --version

This should display the version number and basic information about your installation.

Dependencies
----------

The Aichemist Codex depends on several Python packages, which will be automatically installed:

* **aiofiles**: For asynchronous file operations
* **numpy** and **pandas**: For data processing
* **rapidfuzz**: For fuzzy search capabilities
* **whoosh**: For full-text indexing
* **pyyaml**: For configuration file parsing
* **faiss-cpu**: For vector similarity search
* **sentence-transformers**: For semantic text processing
* **cryptography**: For secure configuration storage

Troubleshooting
-------------

Common installation issues and their solutions:

Missing Dependencies
~~~~~~~~~~~~~~~~~~

If you encounter errors about missing dependencies, try installing with the extras option:

.. code-block:: bash

   pip install the-aichemist-codex[all]

This will install all optional dependencies.

Installation Fails on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, you might need to install the Microsoft Visual C++ Build Tools first:

1. Download and install the `Microsoft Visual C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_
2. During installation, select "C++ build tools" and ensure the latest Windows SDK is selected
3. Try installing The Aichemist Codex again

Next Steps
---------

After installation, see the :doc:`getting_started` guide to begin using The Aichemist Codex.
