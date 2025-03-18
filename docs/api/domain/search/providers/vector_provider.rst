Vector Provider
===============

Overview
--------

The Vector Provider is an advanced search provider that performs semantic searches using vector embeddings. Instead of matching exact text or patterns, it finds documents that are semantically similar to the query, enabling more intuitive and human-like search capabilities.

Implementation
-------------

The Vector Provider extends the Base Provider and utilizes embedding models to convert text into vector representations. It then performs similarity calculations to find the most relevant matches.

Key Features
-----------

* **Semantic Understanding**: Finds conceptually related content, not just exact matches
* **Embedding Models**: Uses state-of-the-art embedding models for text representation
* **Similarity Metrics**: Supports multiple similarity measures (cosine, dot product, etc.)
* **Multilingual Support**: Works across different languages when using appropriate embedding models
* **Configurable Thresholds**: Adjustable similarity thresholds for controlling match precision
* **Vector Caching**: Optimizes performance by caching document embeddings

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.search.providers.vector_provider import VectorSearchProvider

   # Initialize the vector search provider
   vector_provider = VectorSearchProvider(
       embedding_model="sentence-transformers/all-mpnet-base-v2"
   )

   # Perform a semantic search
   results = vector_provider.search(
       "How to optimize database performance",
       similarity_threshold=0.75,
       max_results=5
   )

   # Process the results
   for result in results:
       print(f"Match in {result.document_id} with similarity {result.score}: {result.content}")

.. automodule:: the_aichemist_codex.backend.domain.search.providers.vector_provider
   :members:
   :undoc-members:
   :show-inheritance: