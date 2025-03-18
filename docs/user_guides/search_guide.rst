Search Guide
===========

This guide explains how to use the powerful search capabilities of The AIchemist Codex.

Search Types
-----------

The AIchemist Codex supports multiple search types to help you find content effectively:

1. **Vector Search (Semantic)**: Find content based on meaning, not just keywords
2. **Text Search**: Simple keyword-based search
3. **Regex Search**: Advanced pattern matching using regular expressions
4. **Combined Search**: Uses multiple search providers and ranks results

Choosing the Right Search Type
----------------------------

* **Vector Search**: Best for concept-based searches where you're looking for similar ideas rather than exact text matches
* **Text Search**: Best for simple keyword searches with exact matches
* **Regex Search**: Best for pattern matching (e.g., finding all email addresses or function definitions)
* **Combined Search**: Best for general-purpose search when you want comprehensive results

Using Search from the Command Line
--------------------------------

Basic search using the default provider:

.. code-block:: bash

   aichemist search "machine learning algorithms"

Specify a search provider:

.. code-block:: bash

   aichemist search "function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(" --provider regex
   aichemist search "neural networks" --provider vector
   aichemist search "configuration file" --provider text

Limit search results:

.. code-block:: bash

   aichemist search "deep learning" --max-results 5

Filter by file type:

.. code-block:: bash

   aichemist search "API reference" --file-types .py,.md,.rst

Search within specific directories:

.. code-block:: bash

   aichemist search "database connection" --directories ./src,./docs

Using Search in Python
--------------------

Basic search:

.. code-block:: python

   from aichemist_codex import AIchemist

   ai = AIchemist()
   results = ai.search("machine learning algorithms")

   for result in results:
       print(f"Document: {result.document_id}")
       print(f"Score: {result.score}")
       print(f"Content: {result.content}")
       print("---")

Advanced search with specific provider:

.. code-block:: python

   # Vector (semantic) search
   vector_results = ai.search(
       "improving database performance",
       provider="vector",
       similarity_threshold=0.75,
       max_results=10
   )

   # Regex search
   regex_results = ai.search(
       r"class\s+[A-Z][a-zA-Z0-9]*\s*\(.*\):",  # Find class definitions
       provider="regex",
       case_sensitive=True
   )

   # Text search
   text_results = ai.search(
       "configuration settings",
       provider="text",
       whole_words_only=True,
       case_sensitive=False
   )

Advanced Search Features
----------------------

Fine-tuning Vector Search
~~~~~~~~~~~~~~~~~~~~~~~~

Vector search performance depends on the embedding model and similarity settings:

.. code-block:: python

   # Configure vector search settings
   ai.configure_search(
       provider="vector",
       embedding_model="sentence-transformers/all-mpnet-base-v2",
       similarity_metric="cosine",
       similarity_threshold=0.7
   )

   # Perform search with new settings
   results = ai.search("machine learning models", provider="vector")

Using Regular Expressions
~~~~~~~~~~~~~~~~~~~~~~~

Regular expressions allow powerful pattern matching:

.. code-block:: bash

   # Find all function definitions
   aichemist search "def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(" --provider regex

   # Find all email addresses
   aichemist search "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" --provider regex

   # Find all TODO comments
   aichemist search "TODO:.*$" --provider regex

Search Result Formatting
---------------------

Control the output format of search results:

.. code-block:: bash

   # Get results in JSON format
   aichemist search "configuration" --format json

   # Get results in Markdown format
   aichemist search "API documentation" --format markdown

   # Save results to a file
   aichemist search "database" --format html --output search_results.html

Search Best Practices
------------------

1. **Start General, Then Refine**: Begin with broader searches, then narrow down with more specific terms
2. **Use Vector Search for Concepts**: When looking for ideas or concepts rather than exact text
3. **Combine with Tags**: Use tags to narrow down search scope
4. **Use Filters**: Limit by file type, directory, or metadata to get more relevant results
5. **Explore Relationships**: Use search results as starting points to explore related files

Troubleshooting Search Issues
--------------------------

Common issues and solutions:

1. **No Results Found**:
   - Try different search terms
   - Check if files have been properly indexed
   - Try a different search provider
   - Lower the similarity threshold for vector search

2. **Too Many Results**:
   - Use more specific search terms
   - Add filters (file types, directories)
   - Increase the similarity threshold for vector search
   - Use combined search with higher ranking thresholds

3. **Poor Quality Results**:
   - Check if the right search provider is being used
   - For vector search, try a different embedding model
   - Ensure content has been properly processed and indexed

4. **Slow Searches**:
   - Check if search indices are up to date
   - Consider optimizing your configuration
   - For large repositories, implement more specific filters