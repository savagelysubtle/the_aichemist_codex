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

4. **Get tag suggestions**

   .. code-block:: bash

      aichemist tag --suggest /path/to/your/files

5. **Apply tags to files**

   .. code-block:: bash

      aichemist tag --auto /path/to/your/files

6. **Search for content**

   .. code-block:: bash

      aichemist search "your search query"

Example Usage
-----------

.. code-block:: python

   import asyncio
   from backend.src.file_reader import FileReader
   from backend.src.search import SearchEngine
   from backend.src.tagging import TagManager, TagSuggester
   from pathlib import Path

   async def main():
       # Initialize components
       reader = FileReader()
       search = SearchEngine()
       tag_manager = TagManager(Path(".aichemist/tags.db"))
       await tag_manager.initialize()
       suggester = TagSuggester(tag_manager)

       # Process a file
       file_path = Path("document.pdf")
       metadata = await reader.process_file(file_path)
       print(f"Detected MIME type: {metadata.mime_type}")

       # Get tag suggestions
       suggestions = await suggester.suggest_tags(metadata)
       print("Suggested tags:")
       for tag, confidence in suggestions:
           print(f"- {tag} ({confidence:.2f})")

       # Apply tags automatically
       await tag_manager.add_file_tags(file_path, suggestions[:5])  # Add top 5 tags

       # Search for content
       results = await search.search("machine learning")
       for result in results:
           print(f"Found in: {result.path}")

   # Run the async function
   asyncio.run(main())

Next Steps
---------

* Check out the :doc:`usage` guide for more detailed information
* Learn about :doc:`configuration` options
* Explore the :doc:`api/file_reader` module documentation
* See the :doc:`api/tagging` documentation for advanced tagging features