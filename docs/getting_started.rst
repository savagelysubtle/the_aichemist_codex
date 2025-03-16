Getting Started
===============

Welcome to The Aichemist Codex! This guide will help you get up and running quickly.

What is The Aichemist Codex?
---------------------------

The Aichemist Codex is an advanced file management and knowledge extraction system that helps you:

* Organize your files intelligently based on content
* Extract and analyze metadata from various file types
* Discover relationships between files
* Search for content using advanced techniques
* Auto-tag files based on their content

Prerequisites
------------

Before you begin, make sure you have:

* Python 3.10 or higher
* pip or Poetry for dependency management
* At least 100MB of free disk space

Quick Start
----------

1. **Installation**

   .. code-block:: bash

      # Using pip
      pip install the-aichemist-codex

      # Using Poetry
      poetry add the-aichemist-codex

2. **Initialize a new codex**

   .. code-block:: bash

      aichemist init /path/to/your/codex

3. **Add files to your codex**

   .. code-block:: bash

      aichemist add /path/to/your/files

4. **Search for content**

   .. code-block:: bash

      aichemist search "your search query"

Example Usage
-----------

.. code-block:: python

   from backend.src.file_reader import FileReader
   from backend.src.search import SearchEngine
   from pathlib import Path

   # Initialize components
   reader = FileReader()
   search = SearchEngine()

   # Process a file
   metadata = await reader.process_file(Path("document.pdf"))
   print(f"Detected MIME type: {metadata.mime_type}")

   # Search for content
   results = await search.search("machine learning")
   for result in results:
       print(f"Found in: {result.path}")

Next Steps
---------

* Check out the :doc:`usage` guide for more detailed information
* Learn about :doc:`configuration` options
* Explore the :doc:`api/file_reader` module documentation