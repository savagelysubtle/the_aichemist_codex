Your First Search
==============

This tutorial will guide you through performing your first searches with The AIchemist Codex. You'll learn how to:

1. Perform basic text searches
2. Understand search results
3. Use search filters
4. Save and reuse searches

Prerequisites
------------

Before starting this tutorial, make sure you have:

- Installed The AIchemist Codex (:doc:`quick_start`)
- Created a project with some files added

Basic Search
-----------

Let's start with a simple text search:

.. code-block:: bash

   aichemist search "project management"

This performs a basic search using the default search provider (usually a combination of text and vector search).

The output will look something like this:

.. code-block:: text

   Search results for "project management":

   1. project_overview.pdf (Score: 0.92)
      "... effective project management requires clear communication and ..."

   2. team_guidelines.docx (Score: 0.78)
      "... follow standard project management methodologies for all initiatives ..."

   3. meeting_notes.txt (Score: 0.65)
      "... discussed project management tools and decided to use ..."

Understanding Search Results
--------------------------

Each search result includes:

- File name and path
- Relevance score (0-1, where 1 is the most relevant)
- A snippet of text showing the context of the match
- File type and size information

You can get more detailed results with the `--verbose` flag:

.. code-block:: bash

   aichemist search "project management" --verbose

Using Search Filters
------------------

Limit results by file type:

.. code-block:: bash

   aichemist search "project management" --file-types pdf,docx

Search in specific directories:

.. code-block:: bash

   aichemist search "project management" --directory ~/my_project/content/reports

Limit the number of results:

.. code-block:: bash

   aichemist search "project management" --limit 5

Combine filters:

.. code-block:: bash

   aichemist search "project management" --file-types pdf --directory ~/my_project/content/reports --limit 3

Choosing Search Providers
-----------------------

The AIchemist Codex supports different search methods through providers:

.. code-block:: bash

   # Vector (semantic) search
   aichemist search "innovative approaches" --provider vector

   # Text-based search
   aichemist search "exact phrase match" --provider text

   # Regular expression search
   aichemist search "data\\d+" --provider regex

Saving and Reusing Searches
-------------------------

Save a search for later use:

.. code-block:: bash

   aichemist search "project management" --file-types pdf --save-search "project_docs"

Run the saved search:

.. code-block:: bash

   aichemist search --load-search "project_docs"

List saved searches:

.. code-block:: bash

   aichemist search --list-searches

Next Steps
---------

Now that you've learned the basics of searching, you can:

- Explore more advanced semantic search in :doc:`../advanced_search/semantic_search`
- Learn about regex pattern matching in :doc:`../advanced_search/regex_techniques`
- Try combined search approaches in :doc:`../advanced_search/combined_search`

For more detailed information on all search options, see the :doc:`/user_guides/search_guide`.