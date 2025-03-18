Text Provider
=============

Overview
--------

The Text Provider is a search provider that focuses on basic text-based searches within documents. It offers straightforward, keyword-based search functionality without the complexity of regular expressions or semantic understanding.

Implementation
-------------

The Text Provider extends the Base Provider and implements simple text search algorithms, including substring matching and token-based matching.

Key Features
-----------

* **Simple Keyword Matching**: Finds exact text matches within documents
* **Token-Based Searching**: Can break queries into tokens for more flexible matching
* **Case Sensitivity Options**: Supports both case-sensitive and case-insensitive searches
* **Whole Word Matching**: Optionally restricts matches to whole words only
* **Efficient for Small Datasets**: Optimized for quick searches in smaller document collections

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.search.providers.text_provider import TextSearchProvider

   # Initialize the text search provider
   text_provider = TextSearchProvider()

   # Perform a search for keywords
   results = text_provider.search(
       "important configuration",
       case_sensitive=False,
       whole_words_only=True,
       document_ids=["doc1", "doc2", "doc3"]
   )

   # Process the results
   for result in results:
       print(f"Found match in {result.document_id}: {result.content}")

.. automodule:: the_aichemist_codex.backend.domain.search.providers.text_provider
   :members:
   :undoc-members:
   :show-inheritance: