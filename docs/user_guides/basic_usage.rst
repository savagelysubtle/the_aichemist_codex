Basic Usage Guide
===============

This guide covers the basic usage of The AIchemist Codex to help you get started quickly.

Getting Started
--------------

After installing and configuring The AIchemist Codex, you can start using it through:

1. Command-line interface (CLI)
2. Python API
3. Web interface (if enabled)

Command-line Interface
--------------------

The basic command structure is:

.. code-block:: bash

   aichemist [command] [options]

Common Commands
~~~~~~~~~~~~~

1. **Initialize a project**:

   .. code-block:: bash

      aichemist init --project-dir /path/to/your/project

2. **Process files**:

   .. code-block:: bash

      aichemist process --input /path/to/files --output /path/to/output

3. **Search for content**:

   .. code-block:: bash

      aichemist search "your search query" --provider vector

4. **Manage tags**:

   .. code-block:: bash

      aichemist tag --add "important" --files /path/to/file.txt
      aichemist tag --suggest /path/to/file.txt

5. **View relationships**:

   .. code-block:: bash

      aichemist relationships --file /path/to/file.txt

Python API
---------

Using The AIchemist Codex in your Python scripts:

.. code-block:: python

   from aichemist_codex import AIchemist

   # Initialize
   ai = AIchemist(config_path="/path/to/config.yaml")

   # Process files
   ai.process_directory("/path/to/input", output_dir="/path/to/output")

   # Search
   results = ai.search("your search query", provider="vector")
   for result in results:
       print(f"Found in {result.document_id}: {result.content}")

   # Tagging
   ai.add_tag("/path/to/file.txt", "important")
   suggested_tags = ai.suggest_tags("/path/to/file.txt")

   # Relationships
   relationships = ai.get_relationships("/path/to/file.txt")
   for rel in relationships:
       print(f"Related to {rel.target_file} (Confidence: {rel.confidence})")

Web Interface
-----------

If you've enabled the web interface in your configuration, you can access it by:

1. Starting the web server:

   .. code-block:: bash

      aichemist web-server --port 8000

2. Open your browser and navigate to `http://localhost:8000`

3. Use the interface to:
   - Upload and process files
   - Search across your content
   - Manage tags and relationships
   - Visualize connections between files

Common Workflows
--------------

Project Initialization
~~~~~~~~~~~~~~~~~~~

1. Create a project directory
2. Initialize the AIchemist project
3. Configure project settings

.. code-block:: bash

   mkdir my_project
   cd my_project
   aichemist init
   aichemist config edit

Content Processing
~~~~~~~~~~~~~~~~

1. Add files to your project
2. Process the files to extract metadata and embeddings
3. Review the processing results

.. code-block:: bash

   cp /path/to/files/* ./content/
   aichemist process
   aichemist status

Search and Discovery
~~~~~~~~~~~~~~~~~

1. Search across your processed content
2. Review and refine search results
3. Explore relationships between files

.. code-block:: bash

   aichemist search "machine learning algorithms"
   aichemist relationships --file ./content/document.pdf

Next Steps
---------

After mastering the basics, explore these advanced topics:

- :doc:`project_organization` - Learn how to organize larger projects
- :doc:`search_guide` - Advanced search techniques
- :doc:`tagging_guide` - Comprehensive tagging strategies
- :doc:`api_usage` - Integrate with other applications