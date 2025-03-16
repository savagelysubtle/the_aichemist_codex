Usage Guide
===========

This guide covers the main features and usage patterns of The Aichemist Codex.

Command Line Interface
--------------------

The Aichemist Codex provides a comprehensive command-line interface for all its functionality.

Basic Commands
~~~~~~~~~~~~~

Initialize a New Codex
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist init [path]

This creates a new codex at the specified path, setting up necessary directories and configuration.

Add Files to Codex
^^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist add [files_or_directories]

This command adds files or entire directories to the codex, processing and indexing them for search and organization.

Search for Content
^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist search "search query"

This performs a search across all indexed files.

Advanced Search Options
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Fuzzy search
   aichemist search --fuzzy "aproximate term"

   # Semantic search
   aichemist search --semantic "conceptually similar content"

   # Regex search
   aichemist search --regex "pattern.*search"

   # Search by file type
   aichemist search --type=python "function definition"

   # Search by tag
   aichemist search --tag=documentation

File Organization
~~~~~~~~~~~~~~~

Organize Files Based on Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist organize [directory]

This applies the sorting rules defined in your configuration to organize files.

Find Duplicate Files
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist dupes [directory]

This identifies duplicate files and provides options for handling them.

Tag Management
~~~~~~~~~~~~

Auto-Tag Files
^^^^^^^^^^^^

.. code-block:: bash

   aichemist tag --auto [files_or_directories]

This automatically generates and applies tags based on file content.

Manual Tag Operations
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Add tags
   aichemist tag --add "tag1,tag2" [files]

   # Remove tags
   aichemist tag --remove "tag1" [files]

   # List tags
   aichemist tag --list [files]

Relationship Mapping
------------------

Generate Relationship Map
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist relationships [files_or_directories]

This analyzes files and generates a map of relationships between them.

Find Related Files
^^^^^^^^^^^^^^^

.. code-block:: bash

   aichemist related [file]

This shows files related to the specified file.

Python API
---------

The Aichemist Codex can also be used as a Python library in your applications.

Basic Example
~~~~~~~~~~~

.. code-block:: python

   from backend.src.file_reader import FileReader
   from backend.src.metadata import MetadataManager
   from backend.src.search import SearchEngine
   from pathlib import Path
   import asyncio

   async def main():
       # Initialize components
       reader = FileReader()
       metadata_mgr = MetadataManager()
       search = SearchEngine()

       # Process a file
       file_path = Path("document.pdf")
       metadata = await reader.process_file(file_path)

       # Store metadata
       await metadata_mgr.add(metadata)

       # Search for content
       results = await search.search("important concept")

       # Print results
       for result in results:
           print(f"Found in: {result.path} (Score: {result.score})")

   # Run the async function
   asyncio.run(main())

Working with File Relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from backend.src.relationships import RelationshipDetector, RelationshipGraph
   from pathlib import Path
   import asyncio

   async def analyze_relationships():
       # Initialize detector
       detector = RelationshipDetector()

       # Detect relationships
       file_path = Path("main.py")
       relationships = await detector.detect_relationships(file_path)

       # Build relationship graph
       graph = RelationshipGraph()
       for rel in relationships:
           graph.add_relationship(rel)

       # Find central files
       central_files = graph.get_central_nodes(top_n=5)
       print("Most connected files:")
       for file, score in central_files:
           print(f"- {file}: {score}")

   asyncio.run(analyze_relationships())

Configuration
-----------

The Aichemist Codex can be configured via configuration files or environment variables.
See the :doc:`configuration` guide for detailed information.

Advanced Features
---------------

For more advanced usage and features, check out the specific module documentation in the API Reference section.