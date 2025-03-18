Semantic Search Tutorial
=====================

This tutorial explores the powerful semantic search capabilities in The AIchemist Codex. You'll learn how to use AI-powered search to find conceptually related content beyond simple keyword matching.

Understanding Semantic Search
--------------------------

Unlike traditional keyword search, semantic search understands the meaning and context of both your query and your documents. Benefits include:

- Finding conceptually related content even when exact keywords aren't present
- Understanding synonyms, related concepts, and contextual meaning
- Identifying documents with similar themes regardless of specific terminology
- Ranking results based on conceptual relevance, not just keyword frequency

When to Use Semantic Search
------------------------

Semantic search is ideal for:

- Research and discovery when you don't know exact terms
- Finding conceptually similar documents
- Uncovering hidden relationships between topics
- Exploring a topic space without exact keyword knowledge

Basic Semantic Search
------------------

To perform a semantic search:

.. code-block:: bash

   aichemist search "machine learning applications in healthcare" --provider vector

This will return documents related to machine learning in healthcare contexts, even if they don't contain these exact terms.

Semantic Search Options
--------------------

Refine your semantic searches with these options:

**Similarity threshold**:

.. code-block:: bash

   aichemist search "quantum computing algorithms" --provider vector --threshold 0.75

Only results with a similarity score above 0.75 will be returned (default is usually 0.6).

**Result count limit**:

.. code-block:: bash

   aichemist search "climate change mitigation strategies" --provider vector --limit 20

Returns up to 20 results (default is 10).

**Including context snippets**:

.. code-block:: bash

   aichemist search "renewable energy" --provider vector --context-length 150

Returns context snippets of 150 characters around each match (default is 100).

Using Multiple Embedding Models
----------------------------

The AIchemist Codex may support multiple embedding models for semantic search. To use a specific model:

.. code-block:: bash

   aichemist search "artificial intelligence ethics" --provider vector --model "all-mpnet-base-v2"

Available models may include:
- all-MiniLM-L6-v2 (faster, less accurate)
- all-mpnet-base-v2 (slower, more accurate)
- custom-domain-model (domain-specific)

Combining Semantic Search with Other Search Types
---------------------------------------------

For more comprehensive results, you can combine semantic search with other search types:

.. code-block:: bash

   aichemist search "neural network architecture" --combined

This performs both semantic and text search, then combines and ranks the results.

Fine-tuning with Metadata Filters
------------------------------

Narrow your semantic search with metadata:

.. code-block:: bash

   aichemist search "machine learning" --provider vector --metadata "document_type=research,date>2022-01-01"

This restricts the semantic search to research documents created after January 1, 2022.

Semantic Search in Python
----------------------

Use semantic search in your code:

.. code-block:: python

   from aichemist_codex import AIchemist

   ai = AIchemist()

   # Basic semantic search
   results = ai.search("quantum computing", provider="vector")

   # Advanced semantic search
   results = ai.search(
       "machine learning applications",
       provider="vector",
       threshold=0.75,
       limit=20,
       metadata={"document_type": "paper"}
   )

   # Process results
   for result in results:
       print(f"{result.filename} (Score: {result.score})")
       print(f"Snippet: {result.snippet}")
       print("-" * 50)

Troubleshooting Semantic Search
----------------------------

If you're not getting the expected results:

1. **Try different query phrasing**
   * Use different synonyms or phrasings
   * Be more specific in your query
   * Use longer, more descriptive queries

2. **Adjust similarity threshold**
   * Lower for more results (may be less relevant)
   * Higher for fewer, more relevant results

3. **Check embedding model**
   * Different models have different strengths
   * Domain-specific models may perform better for specialized topics

4. **Ensure content is properly indexed**
   * Run `aichemist index status` to check index status
   * Re-index with `aichemist reindex` if needed

Next Steps
---------

Now that you've mastered semantic search, explore:

- :doc:`regex_techniques` - Learn powerful pattern matching with regular expressions
- :doc:`combined_search` - Combine multiple search methods for better results
- :doc:`search_customization` - Customize search behavior for your specific needs

For comprehensive reference information on all search capabilities, see the :doc:`/user_guides/search_guide`.