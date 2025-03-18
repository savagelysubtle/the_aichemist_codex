Regex Provider
==============

Overview
--------

The Regex Provider is a search provider that uses regular expressions to find matching content within documents. It's particularly useful for pattern-based searches where you need precise control over what constitutes a match.

Implementation
-------------

The Regex Provider extends the Base Provider and implements search functionality using Python's built-in regular expression engine.

Key Features
-----------

* **Pattern Matching**: Searches content using regex patterns
* **Case Sensitivity Options**: Supports case-sensitive and case-insensitive searches
* **Multiline Support**: Can search across multiple lines in a document
* **Match Highlighting**: Provides context around matches for better readability
* **Performance Optimization**: Uses compiled regex patterns for efficient searching

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.search.providers.regex_provider import RegexSearchProvider

   # Initialize the regex search provider
   regex_provider = RegexSearchProvider()

   # Perform a search using a regex pattern
   results = regex_provider.search(
       "function\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s*\\(",  # Find function definitions
       case_sensitive=True,
       document_ids=["doc1", "doc2"]
   )

   # Process the results
   for result in results:
       print(f"Found match in {result.document_id}: {result.content}")

.. automodule:: the_aichemist_codex.backend.domain.search.providers.regex_provider
   :members:
   :undoc-members:
   :show-inheritance: