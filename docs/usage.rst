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

   codex init [path]

This creates a new codex at the specified path, setting up necessary directories and configuration.

Add Files to Codex
^^^^^^^^^^^^^^^^

.. code-block:: bash

   codex add [files_or_directories]

This command adds files or entire directories to the codex, processing and indexing them for search and organization.

Search for Content
^^^^^^^^^^^^^^^

.. code-block:: bash

   codex search "search query"

This performs a search across all indexed files.

Advanced Search Options
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Fuzzy search
   codex search --fuzzy "aproximate term"

   # Semantic search
   codex search --semantic "conceptually similar content"

   # Regex search
   codex search --regex "pattern.*search"

   # Search by file type
   codex search --type=python "function definition"

   # Search by tag
   codex search --tag=documentation

File Organization
~~~~~~~~~~~~~~~

Organize Files Based on Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   codex organize [directory]

This applies the sorting rules defined in your configuration to organize files.

Find Duplicate Files
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   codex dupes [directory]

This identifies duplicate files and provides options for handling them.

Tag Management
~~~~~~~~~~~~

Auto-Tag Files
^^^^^^^^^^^^

.. code-block:: bash

   codex tag --auto [files_or_directories]

This automatically generates and applies tags based on file content.

Get Tag Suggestions
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   codex tag --suggest [files]

This generates tag suggestions without applying them, allowing you to review and select appropriate tags. The system uses multiple strategies:

* Content-based suggestions based on file content and metadata
* Collaborative filtering suggestions based on similar files
* Machine learning-based classification suggestions

Manual Tag Operations
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Add tags
   codex tag --add "tag1,tag2" [files]

   # Remove tags
   codex tag --remove "tag1" [files]

   # List tags
   codex tag --list [files]

Working with Tags in Python
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from backend.src.tagging import TagManager, TagSuggester
   from pathlib import Path
   import asyncio

   async def manage_tags():
       # Initialize tag manager (with database path)
       db_path = Path(".aichemist/tags.db")
       tag_manager = TagManager(db_path)
       await tag_manager.initialize()

       # Create or retrieve a tag
       tag_id = await tag_manager.create_tag("important", "Important documents")

       # Add tag to a file
       file_path = Path("document.pdf")
       await tag_manager.add_file_tag(file_path, tag_id=tag_id)

       # Get tags for a file
       tags = await tag_manager.get_file_tags(file_path)
       print(f"Tags for {file_path}:")
       for tag in tags:
           print(f"- {tag['name']}")

       # Get tag suggestions for a file
       suggestions = await tag_manager.get_tag_suggestions(file_path)
       print(f"Suggested tags:")
       for suggestion in suggestions:
           print(f"- {suggestion['name']} (Score: {suggestion['score']})")

       # Using the TagSuggester for more advanced suggestions
       from backend.src.file_reader import FileReader
       file_reader = FileReader()
       suggester = TagSuggester(tag_manager)

       # Get file metadata
       metadata = await file_reader.process_file(file_path)

       # Get comprehensive suggestions
       advanced_suggestions = await suggester.suggest_tags(metadata)
       print("Advanced tag suggestions:")
       for tag, confidence in advanced_suggestions:
           print(f"- {tag} ({confidence:.2f})")

   asyncio.run(manage_tags())

Relationship Mapping
------------------

Generate Relationship Map
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   codex relationships [files_or_directories]

This analyzes files and generates a map of relationships between them.

Find Related Files
^^^^^^^^^^^^^^^

.. code-block:: bash

   codex related [file]

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
   from backend.src.tagging import TagManager, TagSuggester
   from pathlib import Path
   import asyncio

   async def main():
       # Initialize components
       reader = FileReader()
       metadata_mgr = MetadataManager()
       search = SearchEngine()
       tag_manager = TagManager(Path(".aichemist/tags.db"))
       await tag_manager.initialize()
       suggester = TagSuggester(tag_manager)

       # Process a file
       file_path = Path("document.pdf")
       metadata = await reader.process_file(file_path)

       # Store metadata
       await metadata_mgr.add(metadata)

       # Get tag suggestions
       tag_suggestions = await suggester.suggest_tags(metadata)
       print(f"Suggested tags for {file_path}:")
       for tag, confidence in tag_suggestions:
           print(f"- {tag} ({confidence:.2f})")

       # Apply high-confidence tags automatically
       high_confidence_tags = [(tag, conf) for tag, conf in tag_suggestions if conf > 0.8]
       if high_confidence_tags:
           await tag_manager.add_file_tags(file_path, high_confidence_tags)
           print(f"Applied {len(high_confidence_tags)} high-confidence tags")

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
