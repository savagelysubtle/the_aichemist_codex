Regex Search Techniques
====================

This tutorial explores the powerful regular expression search capabilities in The AIchemist Codex. You'll learn how to use pattern matching to find precise content that other search methods might miss.

Understanding Regex Search
-----------------------

Regular expressions (regex) are patterns that describe sets of strings. Benefits of regex search include:

- Finding content that matches specific patterns (emails, URLs, dates, etc.)
- Creating complex search queries with precise syntax requirements
- Capturing sections of text that follow particular formats
- Excluding matches that don't meet specific criteria

When to Use Regex Search
---------------------

Regex search is ideal for:

- Finding all instances of structured data (emails, phone numbers, etc.)
- Locating code patterns or function definitions
- Searching for specific document formats or reference numbers
- Finding text with specific formatting or structure

Basic Regex Patterns
-----------------

To perform a basic regex search:

.. code-block:: bash

   aichemist search "error\\d+" --provider regex

This will find all occurrences of the word "error" followed by one or more digits.

Common regex patterns:

.. code-block:: bash

   # Find email addresses
   aichemist search "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}" --provider regex

   # Find URLs
   aichemist search "https?://[\\w\\d.-]+\\.[a-zA-Z]{2,}[\\w\\d\\/.?=&-]*" --provider regex

   # Find dates (MM/DD/YYYY format)
   aichemist search "\\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\\d|3[01])/\\d{4}\\b" --provider regex

Advanced Regex Search
------------------

Use regex search with capture groups:

.. code-block:: bash

   aichemist search "function ([a-zA-Z_][a-zA-Z0-9_]*)" --provider regex --capture-groups

This searches for function names and captures them separately in the results.

Case sensitivity options:

.. code-block:: bash

   # Case-sensitive search
   aichemist search "Error" --provider regex --case-sensitive

   # Case-insensitive search
   aichemist search "error" --provider regex --case-insensitive

Multiline search:

.. code-block:: bash

   aichemist search "^import.*\\n.*matplotlib" --provider regex --multiline

This finds import statements followed by a line that includes "matplotlib".

Context Control
------------

Get more context around matches:

.. code-block:: bash

   aichemist search "critical\\s+error" --provider regex --context-lines 5

This shows 5 lines before and after each match.

Specify context direction:

.. code-block:: bash

   # Show only lines before the match
   aichemist search "exception" --provider regex --context-before 3

   # Show only lines after the match
   aichemist search "exception" --provider regex --context-after 3

Combining with Other Search Types
-----------------------------

For more comprehensive results, combine regex with other search types:

.. code-block:: bash

   aichemist search "error" --provider regex,text

This performs both regex and text search, then combines the results.

Use regex to filter semantic search results:

.. code-block:: bash

   aichemist search "database connectivity" --provider vector --post-filter "error\\d+"

This performs a semantic search for "database connectivity" and then filters for results that contain "error" followed by digits.

Regex Search in Python
-------------------

Use regex search in your code:

.. code-block:: python

   from aichemist_codex import AIchemist
   import re

   ai = AIchemist()

   # Basic regex search
   results = ai.search("error\\d+", provider="regex")

   # Advanced regex search with custom pattern
   pattern = re.compile(r"class\s+([A-Z][a-zA-Z0-9_]*)")
   results = ai.search_with_pattern(pattern)

   # Process results
   for result in results:
       print(f"{result.filename}:{result.line_number} - {result.match}")
       print(f"Context: {result.context}")
       print("-" * 50)

Regex Performance Tips
-------------------

Optimize your regex searches:

1. **Be specific** - Narrow down the search scope with file filters
2. **Avoid greedy patterns** - Use `+?` and `*?` instead of `+` and `*` when possible
3. **Use anchors** - `^` and `$` can help focus searches at the beginning or end of lines
4. **Limit backtracking** - Avoid nested repetition operators
5. **Pre-filter** - Use a text search before applying complex regex patterns

Next Steps
---------

Now that you've mastered regex search, explore:

- :doc:`semantic_search` - Learn about searching by meaning and concepts
- :doc:`combined_search` - Combine multiple search methods for better results
- :doc:`search_customization` - Customize search behavior for your specific needs

For comprehensive reference information on all search capabilities, see the :doc:`/user_guides/search_guide`.