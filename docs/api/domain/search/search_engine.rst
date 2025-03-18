Search Engine
=============

The Search Engine is responsible for orchestrating search operations across different search providers.

Overview
--------

The Search Engine:

* Manages multiple search providers
* Routes search queries to the appropriate provider
* Combines and ranks search results
* Provides a unified search interface

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.search.search_engine
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* **Multi-Modal Search**: Supports different search modalities (text, regex, vector)
* **Provider Management**: Dynamically registers and manages search providers
* **Result Ranking**: Combines and ranks results from different providers
* **Caching**: Caches search results for improved performance
* **Async Operations**: Fully asynchronous search operations

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.search import SearchEngine

   # Initialize the search engine
   search_engine = SearchEngine()

   # Perform a search
   results = await search_engine.search("machine learning",
                                       max_results=10,
                                       search_type="combined")

   # Process results
   for result in results:
       print(f"Document: {result.document_id}, Score: {result.score}")
       print(f"Snippet: {result.snippet}")
       print("---")