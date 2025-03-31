Quick Start Tutorial
==================

This tutorial will guide you through setting up and using The Aichemist Codex for the first time.

Installation
-----------

1. Install the package using pip:

   .. code-block:: bash

      pip install the-aichemist-codex

2. Verify the installation:

   .. code-block:: bash

      codex --version

Setting Up Your First Codex
--------------------------

1. Initialize a new codex in your chosen directory:

   .. code-block:: bash

      codex init ~/my_codex

   This creates the necessary directory structure and configuration files.

2. Review the created structure:

   .. code-block:: bash

      ls -la ~/my_codex

   You should see the `.codexconfig` file and data directory.

Adding and Processing Files
--------------------------

1. Add some files to your codex:

   .. code-block:: bash

      codex add ~/Documents/*.pdf

   This will:
   - Copy or link the files to your codex
   - Extract metadata from the files
   - Index the content for searching
   - Analyze the files for potential relationships

2. Check the status of your codex:

   .. code-block:: bash

      codex status

   This shows a summary of your codex, including file counts and processing status.

Searching for Content
-------------------

Now that you have files in your codex, let's try searching:

1. Basic text search:

   .. code-block:: bash

      codex search "important concept"

   This performs a full-text search across all indexed files.

2. Try a fuzzy search:

   .. code-block:: bash

      codex search --method fuzzy "approximte term"

   This finds matches even with spelling variations or typos.

3. Semantic search:

   .. code-block:: bash

      codex search --method semantic "machine learning applications"

   This finds conceptually related content, even if the exact terms aren't used.

Auto-Tagging Files
----------------

1. Generate tag suggestions for your files:

   .. code-block:: bash

      codex tag --suggest ~/my_codex/*.pdf

   This analyzes the content and suggests appropriate tags.

2. Apply tags automatically:

   .. code-block:: bash

      codex tag --auto ~/my_codex/*.pdf

   This generates and applies tags based on file content.

3. View tags for a specific file:

   .. code-block:: bash

      codex tag --list ~/my_codex/document.pdf

Organizing Files
--------------

1. Run a dry-run organization to see what would happen:

   .. code-block:: bash

      codex organize ~/my_codex

   By default, this runs in dry-run mode, showing what would change.

2. Actually perform the organization:

   .. code-block:: bash

      codex organize ~/my_codex --confirm

   This applies the sorting rules to organize your files.

Finding Relationships
-------------------

1. Generate a relationship map for your files:

   .. code-block:: bash

      codex relationships map ~/my_codex

   This analyzes relationships between files based on content similarity, references, and other factors.

2. Find files related to a specific file:

   .. code-block:: bash

      codex relationships related ~/my_codex/document.pdf

   This shows files that are related to the specified file.

Using the Python API
------------------

The Aichemist Codex can also be used as a Python library:

.. code-block:: python

   import asyncio
   from pathlib import Path
   from the_aichemist_codex.backend.file_reader import FileReader
   from the_aichemist_codex.backend.search import SearchEngine
   from the_aichemist_codex.backend.tagging import TagManager

   async def main():
       # Initialize components
       file_reader = FileReader()
       search_engine = SearchEngine()

       # Process a file
       file_path = Path("document.pdf")
       metadata = await file_reader.process_file(file_path)
       print(f"Processed {file_path}")
       print(f"Title: {metadata.title}")
       print(f"MIME type: {metadata.mime_type}")

       # Search for content
       results = await search_engine.search("important concept")
       print("\nSearch results:")
       for result in results:
           print(f"- {result.path} (Score: {result.score})")

   # Run the async function
   asyncio.run(main())

Next Steps
---------

Now that you have a basic understanding of The Aichemist Codex, you can:

- Configure advanced settings in your `.codexconfig` file
- Set up custom tagging rules
- Define your own file organization patterns
- Explore the Python API for integration with your applications

Check out these resources to learn more:

- :doc:`../configuration` - Detailed configuration options
- :doc:`../data_management` - Managing your data directories
- :doc:`../cli_reference` - Complete command-line reference
- :doc:`tagging_workflow` - Advanced tagging tutorial
