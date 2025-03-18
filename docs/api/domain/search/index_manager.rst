Index Manager
=============

The Index Manager is responsible for creating, maintaining, and querying search indices.

Overview
--------

The Index Manager:

* Creates and maintains search indices
* Manages index persistence and loading
* Provides index query capabilities
* Handles index updates and optimization

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.search.index_manager
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* **Multi-Index Support**: Manages multiple indices for different search strategies
* **Persistence**: Saves and loads indices to/from disk
* **Incremental Updates**: Supports incremental index updates
* **Index Maintenance**: Handles routine index maintenance and optimization
* **Async Operations**: Fully asynchronous index operations

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.search import IndexManager

   # Initialize the index manager
   index_manager = IndexManager(index_dir="/path/to/indices")

   # Create or update an index
   await index_manager.add_document(
       document_id="doc1",
       content="This is a sample document about machine learning.",
       metadata={"author": "John Doe", "created": "2023-01-01"}
   )

   # Commit changes to make them searchable
   await index_manager.commit()

   # Query the index
   results = await index_manager.search("machine learning", max_results=10)

   # Process results
   for result in results:
       print(f"Document: {result.document_id}, Score: {result.score}")
       print(f"Snippet: {result.snippet}")
       print("---")