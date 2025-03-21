Advanced Semantic Search Techniques
===============================

This tutorial explores the advanced semantic search capabilities in The Aichemist Codex, explaining how to leverage AI-powered search to find conceptually related content beyond simple keyword matching.

Understanding Semantic Search
--------------------------

Unlike traditional keyword search, semantic search understands the meaning and context of both your query and your documents. Benefits include:

- Finding conceptually related content even when exact keywords aren't present
- Understanding synonyms, related concepts, and contextual meaning
- Identifying documents with similar themes regardless of specific terminology
- Ranking results based on conceptual relevance, not just keyword frequency

Basic Semantic Search
------------------

To perform a simple semantic search:

.. code-block:: bash

   codex search --method semantic "machine learning applications in healthcare"

This will return documents related to machine learning in healthcare contexts, even if they don't contain these exact terms.

Search Modifiers
-------------

Refine your semantic searches with modifiers:

**Similarity threshold**:

.. code-block:: bash

   codex search --method semantic --threshold 0.75 "quantum computing algorithms"

Only results with a similarity score above 0.75 will be returned (default is 0.6).

**Result count limit**:

.. code-block:: bash

   codex search --method semantic --limit 20 "climate change mitigation strategies"

Returns up to 20 results (default is 10).

**Including file details**:

.. code-block:: bash

   codex search --method semantic --detailed "neural networks"

Shows detailed metadata for each result, including creation date, file size, and tags.

Multi-Stage Search Pipelines
-------------------------

Combine multiple search methods for powerful hybrid searches:

**Keyword pre-filtering + semantic ranking**:

.. code-block:: bash

   codex search --method hybrid --keyword-filter "python" --semantic-query "asynchronous programming patterns"

This first finds all documents containing "python", then semantically ranks them by relevance to "asynchronous programming patterns".

**Tag filtering + semantic search**:

.. code-block:: bash

   codex search --method semantic --tags "research,academic" "gene editing ethics"

Only searches within files tagged as both "research" and "academic".

**Date-range + semantic search**:

.. code-block:: bash

   codex search --method semantic --created-after 2023-01-01 --created-before 2023-12-31 "blockchain applications"

Searches only files created in 2023.

Contextual Search
--------------

Provide more context for better results:

**Context-enhanced queries**:

.. code-block:: bash

   codex search --method semantic --context "I'm researching for a graduate-level computer science paper" "graph algorithms for social network analysis"

The additional context helps the search engine understand the academic nature of your query.

**File-based context**:

.. code-block:: bash

   codex search --method semantic --context-file reference_paper.pdf "similar methodologies"

Uses the content of reference_paper.pdf to establish context for finding similar methodologies.

Visualizing Search Results
-----------------------

**Relationship visualization**:

.. code-block:: bash

   codex search --method semantic --visualize "renewable energy storage" --output graph.png

Generates a network graph showing relationships between results.

**Embedding space visualization**:

.. code-block:: bash

   codex search --method semantic --visualize-embeddings "artificial intelligence" --output embeddings.png

Creates a 2D visualization of how documents are clustered in the embedding space.

Advanced Query Techniques
----------------------

**Weighted concept search**:

.. code-block:: bash

   codex search --method semantic "natural language processing:0.8, sentiment analysis:0.4, transformer models:0.6"

Searches for documents related to these concepts with the specified weights.

**Negative semantic search**:

.. code-block:: bash

   codex search --method semantic "quantum computing -classical algorithms"

Finds documents about quantum computing while avoiding those focused on classical algorithms.

**Concept blending**:

.. code-block:: bash

   codex search --method semantic --blend "solar energy + water purification"

Finds documents at the intersection of these two concepts.

Custom Search Models
-----------------

The Aichemist Codex supports different embedding models for different types of content:

.. code-block:: bash

   # For scientific/technical content
   codex search --method semantic --model technical "crystalline structures"

   # For legal/formal documents
   codex search --method semantic --model legal "contractual obligations"

   # For creative/literary content
   codex search --method semantic --model creative "character development techniques"

Working with Search Profiles
-------------------------

Create and save search profiles for frequently used search patterns:

.. code-block:: bash

   # Create a search profile
   codex profile --create research_profile --method semantic --tags "research" --detailed

   # Use a search profile
   codex search --profile research_profile "quantum entanglement"

   # List available profiles
   codex profile --list

   # Export a profile to share
   codex profile --export research_profile > research_profile.json

Python API for Semantic Search
---------------------------

For programmatic access to semantic search:

.. code-block:: python

   import asyncio
   from the_aichemist_codex.backend.search import SemanticSearchEngine
   from the_aichemist_codex.backend.models import SearchResult

   async def semantic_search_example():
       # Initialize the search engine
       search_engine = SemanticSearchEngine()
       await search_engine.initialize()

       # Basic semantic search
       results = await search_engine.search(
           query="machine learning explainability",
           method="semantic",
           limit=5
       )

       print(f"Found {len(results)} results:")
       for result in results:
           print(f"- {result.file_path}: {result.similarity_score:.2f}")

       # Advanced multi-stage search
       advanced_results = await search_engine.search(
           query="reinforcement learning",
           method="hybrid",
           pre_filter={
               "tags": ["ai", "research"],
               "date_range": {
                   "start": "2022-01-01",
                   "end": "2023-12-31"
               }
           },
           threshold=0.7
       )

       # Analyze results
       summary = await search_engine.analyze_results(advanced_results)
       print(f"\nSearch Result Analysis:")
       print(f"Main concepts: {', '.join(summary['concepts'])}")
       print(f"Suggested related queries: {', '.join(summary['suggested_queries'])}")

   # Run the async function
   asyncio.run(semantic_search_example())

Fine-Tuning Semantic Search
------------------------

**Adjust tokenization settings**:

.. code-block:: bash

   codex config --set search.semantic.tokenizer "scientific"

Options include "general", "scientific", "legal", and "creative".

**Adjust chunking strategy**:

.. code-block:: bash

   codex config --set search.semantic.chunk_size 512
   codex config --set search.semantic.chunk_overlap 50

Controls how documents are split for embedding.

**Cache management**:

.. code-block:: bash

   # Clear embedding cache to force recomputation
   codex cache --clear embeddings

   # View embedding statistics
   codex cache --stats embeddings

Troubleshooting Search Issues
--------------------------

**Search quality issues**:

If results don't match expectations:

.. code-block:: bash

   # Get detailed explanation of why results matched
   codex search --method semantic --explain "distributed systems"

   # Try a different model
   codex search --method semantic --model alternative "distributed systems"

**Performance issues**:

If search is slow:

.. code-block:: bash

   # Check index status
   codex status --index

   # Rebuild index (takes time but improves performance)
   codex rebuild --index semantic

Real-World Use Cases
-----------------

**Research literature review**:

.. code-block:: bash

   # First gather all potentially relevant papers
   codex search --method semantic --tags "paper,research" --limit 50 "quantum error correction"

   # Then find methodologies across these papers
   codex search --within-results --method semantic "experimental methodology"

   # Export citations for these papers
   codex export --format bibliography --output quantum_citations.bib

**Knowledge base management**:

.. code-block:: bash

   # Find gaps in documentation
   codex analyze --gaps "authentication processes"

   # Find outdated information
   codex search --method semantic --created-before 2022-01-01 "security best practices"

   # Find contradictory information
   codex analyze --contradictions "project timeline"

By mastering these advanced semantic search techniques, you can efficiently discover and organize information across large document collections, finding connections and insights that would be impossible with traditional search methods.