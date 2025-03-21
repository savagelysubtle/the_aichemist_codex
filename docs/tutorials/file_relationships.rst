File Relationships Tutorial
==========================

This tutorial explains how to discover, visualize, and leverage relationships between files in The Aichemist Codex.

Understanding File Relationships
-----------------------------

The Aichemist Codex can automatically detect and track relationships between files based on various factors:

- Content similarity
- References between documents
- Shared metadata
- Temporal relationships (files created or modified together)
- Semantic connections between topics

These relationships help you understand how your documents connect to each other, revealing insights and patterns that might not be immediately obvious.

Discovering Relationships
----------------------

**Basic Relationship Detection**

To find files related to a specific document:

.. code-block:: bash

   codex relationships find document.pdf

This will show a list of files related to document.pdf, ranked by relationship strength.

**Setting Relationship Thresholds**

You can adjust the sensitivity of relationship detection:

.. code-block:: bash

   codex relationships find --threshold 0.7 document.pdf

Higher thresholds (closer to 1.0) show only the strongest relationships, while lower thresholds reveal more distant connections.

**Filtering Relationship Types**

Focus on specific types of relationships:

.. code-block:: bash

   codex relationships find --type content document.pdf
   codex relationships find --type reference document.pdf
   codex relationships find --type temporal document.pdf

Visualizing Relationships
----------------------

**Creating Relationship Graphs**

Generate visual graphs of file relationships:

.. code-block:: bash

   codex relationships visualize document.pdf --output graph.png

This creates a network visualization with the specified document at the center.

**Exploring Broader Networks**

Visualize relationships across multiple files:

.. code-block:: bash

   codex relationships visualize-group *.pdf --output research_network.png

**Interactive Exploration**

Launch an interactive relationship explorer:

.. code-block:: bash

   codex relationships explore ~/my_documents

Working with Relationships Programmatically
----------------------------------------

For programmatic access to relationship data:

.. code-block:: python

   import asyncio
   from the_aichemist_codex.backend.relationships import RelationshipManager

   async def explore_relationships():
       # Initialize the relationship manager
       rel_manager = RelationshipManager()
       await rel_manager.initialize()

       # Find related files
       file_path = "~/Documents/research_paper.pdf"
       related_files = await rel_manager.find_related(file_path, threshold=0.6)

       print(f"Files related to {file_path}:")
       for related_file, score in related_files:
           print(f"- {related_file}: {score:.2f}")

       # Get relationship data for visualization
       graph_data = await rel_manager.get_relationship_graph(file_path, depth=2)

       # Export relationship data
       await rel_manager.export_relationships("relationships.json")

   # Run the async function
   asyncio.run(explore_relationships())

Leveraging Relationships for Research
----------------------------------

Relationships can enhance your research workflow:

**Discovering Missing Links**

Find potentially relevant documents you might have missed:

.. code-block:: bash

   codex relationships gaps document.pdf

This identifies documents that should be related based on content but don't have explicit references.

**Building Literature Review Chains**

Create chains of related documents for literature reviews:

.. code-block:: bash

   codex relationships chain --start paper1.pdf --end paper2.pdf

This finds the shortest path of related documents connecting two papers.

**Clustering Related Documents**

Group documents into clusters based on their relationships:

.. code-block:: bash

   codex relationships cluster ~/research --method community

Advanced Relationship Features
---------------------------

**Custom Relationship Rules**

Define custom rules for detecting relationships in a `relationship_rules.yaml` file:

.. code-block:: yaml

   rules:
     - name: "Citation relationships"
       detector: "citations"
       strength: 0.8
       bidirectional: false

     - name: "Author relationships"
       detector: "metadata"
       field: "author"
       strength: 0.5
       bidirectional: true

Apply these rules with:

.. code-block:: bash

   codex relationships detect --rules relationship_rules.yaml *.pdf

**Relationship Analytics**

Generate analytics about your document relationships:

.. code-block:: bash

   codex relationships analyze ~/research

This produces statistics like centrality measures, identifying key documents in your collection.

Conclusion
--------

By mastering file relationships in The Aichemist Codex, you can:

- Discover connections between documents you might otherwise miss
- Visualize your document collections as networks of knowledge
- Identify key documents and potential gaps in your research
- Build more comprehensive understanding of your information

These capabilities are particularly valuable for research, knowledge management, and large document collections where manual tracking of relationships would be impractical.