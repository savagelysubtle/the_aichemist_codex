Installation Guide
=================

This guide provides detailed instructions for installing The AIchemist Codex.

System Requirements
------------------

* Python 3.10 or higher
* 4GB RAM minimum (8GB+ recommended)
* 2GB of available disk space
* Operating System: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+, CentOS 8+)

Installation Methods
------------------

There are multiple ways to install The AIchemist Codex:

Via pip (Recommended)
~~~~~~~~~~~~~~~~~~~

The easiest way to install is using pip:

.. code-block:: bash

   pip install aichemist-codex

For development versions:

.. code-block:: bash

   pip install git+https://github.com/the-aichemist/aichemist-codex.git

From Source
~~~~~~~~~~

To install from source:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/the-aichemist/aichemist-codex.git
      cd aichemist-codex

2. Create and activate a virtual environment (optional but recommended):

   .. code-block:: bash

      python -m venv .venv
      # On Windows
      .\.venv\Scripts\activate
      # On macOS/Linux
      source .venv/bin/activate

3. Install dependencies and the package:

   .. code-block:: bash

      pip install -e .

Using Docker
~~~~~~~~~~

For containerized deployment:

1. Pull the Docker image:

   .. code-block:: bash

      docker pull theaichemist/aichemist-codex:latest

2. Run the container:

   .. code-block:: bash

      docker run -p 8000:8000 -v /your/data:/app/data theaichemist/aichemist-codex:latest

Verifying Installation
---------------------

To verify the installation was successful:

.. code-block:: bash

   aichemist --version

This should display the current version of The AIchemist Codex.

Next Steps
---------

After installation:

1. Review the :doc:`configuration` guide to configure your installation
2. Follow the :doc:`basic_usage` guide to get started with your first project

Troubleshooting
--------------

Common Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~

1. **Missing Dependencies**: Ensure you have required system libraries installed
2. **Python Version**: Verify you're using Python 3.10+
3. **Permission Issues**: Try using `sudo` (Linux/macOS) or run as administrator (Windows)

For more help, visit the project's GitHub Issues page or contact support.