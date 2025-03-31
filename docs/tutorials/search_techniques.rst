Search Techniques Tutorial
=======================

This tutorial covers the various search methods available in The Aichemist Codex, helping you master different techniques for finding information in your document collection.

Search Methods Overview
--------------------

The Aichemist Codex offers multiple search methods, each with its own strengths:

1. **Basic Filename Search**: Quick search based on filenames
2. **Full-text Search**: Traditional keyword-based content search
3. **Fuzzy Search**: Approximate matching that handles typos and variations
4. **Regex Search**: Pattern-based search using regular expressions
5. **Semantic Search**: AI-powered search based on meaning rather than exact words
6. **Hybrid Search**: Combinations of different search methods

Let's explore each of these methods in detail.

Basic Filename Search
------------------

The simplest search looks for files by name:

.. code-block:: bash

   codex search --filename "report"

This searches for files with "report" in their filename.

**Wildcard Patterns**:

.. code-block:: bash

   codex search --filename "*.pdf"
   codex search --filename "report_2023*"

Full-text Search
-------------

Search for specific words or phrases in document content:

.. code-block:: bash

   codex search --fulltext "machine learning"

Full-text search options:

.. code-block:: bash

   # Case-sensitive search
   codex search --fulltext "Python" --case-sensitive

   # Whole word search
   codex search --fulltext "test" --whole-word

   # Proximity search (words within 5 words of each other)
   codex search --fulltext "neural network" --proximity 5

Fuzzy Search
----------

Find results that approximately match your query:

.. code-block:: bash

   codex search --fuzzy "machne learnin"

This will match "machine learning" despite the typos.

**Adjusting Fuzzy Matching**:

.. code-block:: bash

   # Adjust the similarity threshold (0-100)
   codex search --fuzzy "statistic" --similarity 70

Regex Search
----------

Search using regular expression patterns:

.. code-block:: bash

   # Find email addresses
   codex search --regex "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"

   # Find dates in format MM/DD/YYYY
   codex search --regex "\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/[0-9]{4}\b"

Advanced Search Filters
--------------------

Refine any search with additional filters:

**File Type Filters**:

.. code-block:: bash

   codex search --fulltext "budget" --type pdf,xlsx

**Date Range Filters**:

.. code-block:: bash

   # Files created in the last 30 days
   codex search --fulltext "project" --created-since 30d

   # Files modified between specific dates
   codex search --fulltext "report" --modified-between 2023-01-01 2023-06-30

**Size Filters**:

.. code-block:: bash

   # Files larger than 1MB
   codex search --fulltext "video" --larger-than 1MB

   # Files smaller than 100KB
   codex search --fulltext "config" --smaller-than 100KB

**Tag Filters**:

.. code-block:: bash

   # Search only in files with specific tags
   codex search --fulltext "algorithm" --tags research,important

Combined Search Methods
--------------------

Combine multiple search methods for powerful queries:

.. code-block:: bash

   # Fuzzy filename + fulltext search
   codex search --filename "~reprt" --fulltext "quarterly"

   # Semantic search with date filter
   codex search --semantic "data visualization techniques" --created-since 90d

   # Regex + tag filter
   codex search --regex "\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b" --tags contacts

Search Fields
-----------

Target specific fields in your metadata:

.. code-block:: bash

   # Search in titles
   codex search --field title "proposal"

   # Search in authors
   codex search --field author "Smith"

   # Search in custom metadata
   codex search --field metadata.project "Alpha"

Advanced Output Options
--------------------

Control how search results are displayed:

.. code-block:: bash

   # Show detailed results
   codex search --fulltext "budget" --detailed

   # Format as JSON
   codex search --fulltext "budget" --format json

   # Limit results
   codex search --fulltext "budget" --limit 5

   # Sort by modification date
   codex search --fulltext "budget" --sort-by modified

Saving and Reusing Searches
------------------------

Save frequent searches for later use:

.. code-block:: bash

   # Save a search
   codex search --semantic "machine learning" --tags research --save ml_research

   # Run a saved search
   codex search --saved ml_research

   # List saved searches
   codex search --list-saved

Search Programmatically
--------------------

Access search capabilities from Python:

.. code-block:: python

   import asyncio
   from the_aichemist_codex.backend.search import SearchEngine

   async def search_example():
       # Initialize the search engine
       search_engine = SearchEngine()
       await search_engine.initialize()

       # Basic search
       results = await search_engine.search(
           query="machine learning",
           method="fulltext",
           filters={
               "tags": ["research"],
               "created_after": "2023-01-01"
           },
           limit=10
       )

       # Print results
       print(f"Found {len(results)} results:")
       for result in results:
           print(f"- {result.path} (Score: {result.score:.2f})")

       # Advanced multi-method search
       advanced_results = await search_engine.multi_search(
           queries=[
               {"text": "neural networks", "method": "semantic", "weight": 0.7},
               {"text": "python", "method": "fulltext", "weight": 0.3}
           ],
           combine="weighted_average"
       )

   # Run the async function
   asyncio.run(search_example())

Search Performance Tips
--------------------

Optimize your searches for better performance:

1. **Use Specific Search Methods**: Choose the appropriate search method for your needs
2. **Add Filters**: Narrow down the search space with type, date, or tag filters
3. **Index Management**: Keep your search indices up to date with `codex index --rebuild`
4. **Batch Searches**: For multiple searches, use batch mode: `codex search --batch queries.json`

Troubleshooting Searches
---------------------

When searches don't return expected results:

1. **Check Spelling**: Fulltext search is exact; use fuzzy search for approximate matching
2. **Verify Indexing**: Ensure files are properly indexed with `codex status --index`
3. **Try Alternative Methods**: If fulltext fails, try semantic search and vice versa
4. **Examine Filters**: Make sure filters aren't too restrictive
5. **Debug Mode**: Use `codex search --debug` to see detailed search process information

Conclusion
--------

By mastering the different search techniques in The Aichemist Codex, you can efficiently find information across your document collection, combining the precision of traditional search with the intelligence of semantic search and the flexibility of regular expressions.
