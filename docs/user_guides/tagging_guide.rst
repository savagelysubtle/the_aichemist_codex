Tagging Guide
============

This guide explains the powerful tagging system in The AIchemist Codex and how to use it effectively.

Overview of Tagging
-----------------

Tagging allows you to categorize and organize your files based on content, purpose, or any other classification system. The AIchemist Codex provides:

* **Manual Tagging**: Manually assign tags to files
* **Auto-Tagging**: AI-powered automatic tag suggestions
* **Tag Hierarchies**: Organize tags in parent-child relationships
* **Tag Schemas**: Define structured tag systems for consistent organization

Working with Tags
---------------

Manual Tagging
~~~~~~~~~~~~

Add tags using the command line:

.. code-block:: bash

   # Add a single tag to a file
   aichemist tag --add "important" --file /path/to/file.txt

   # Add multiple tags to a file
   aichemist tag --add "python,documentation,example" --file /path/to/file.txt

   # Add tags to multiple files
   aichemist tag --add "report" --files /path/to/file1.txt,/path/to/file2.pdf

Remove tags:

.. code-block:: bash

   # Remove a tag from a file
   aichemist tag --remove "draft" --file /path/to/file.txt

List tags for a file:

.. code-block:: bash

   aichemist tag --list --file /path/to/file.txt

Auto-Tagging
~~~~~~~~~~

Let the AI suggest tags based on content:

.. code-block:: bash

   # Get tag suggestions for a file
   aichemist tag --suggest --file /path/to/file.txt

   # Apply suggested tags automatically
   aichemist tag --auto-tag --file /path/to/file.txt

   # Get suggestions with confidence scores
   aichemist tag --suggest --with-scores --file /path/to/file.txt

   # Auto-tag with minimum confidence threshold
   aichemist tag --auto-tag --min-confidence 0.75 --file /path/to/file.txt

Tag Hierarchies
~~~~~~~~~~~~~

Create hierarchical tag structures:

.. code-block:: bash

   # Create a parent-child relationship
   aichemist tag --create-hierarchy "programming/python"
   aichemist tag --create-hierarchy "programming/javascript"

   # Add a file to a hierarchical tag
   aichemist tag --add "programming/python" --file /path/to/script.py

   # List all subtags
   aichemist tag --list-subtags "programming"

   # Find files with any subtag
   aichemist tag --find --tag "programming" --include-subtags

Tag Schemas
~~~~~~~~~

Define structured tag schemas for consistent organization:

.. code-block:: bash

   # Define a tag schema
   aichemist tag-schema --create "document_type" --values "report,memo,presentation,code,data"
   aichemist tag-schema --create "status" --values "draft,review,approved,published"

   # Apply schema tags
   aichemist tag --add "document_type:report" --file /path/to/report.pdf
   aichemist tag --add "status:draft" --file /path/to/report.pdf

   # List files with specific schema tags
   aichemist find --tags "document_type:report,status:draft"

Using Tags in Python
------------------

Basic tagging operations:

.. code-block:: python

   from aichemist_codex import AIchemist

   ai = AIchemist()

   # Add tags
   ai.add_tags("/path/to/file.txt", ["important", "documentation"])

   # Get tags for a file
   tags = ai.get_tags("/path/to/file.txt")
   print(f"Tags: {', '.join(tags)}")

   # Remove tags
   ai.remove_tags("/path/to/file.txt", ["draft"])

   # Get suggestions
   suggested_tags = ai.suggest_tags("/path/to/file.txt")
   for tag, confidence in suggested_tags.items():
       print(f"Suggested tag: {tag} (confidence: {confidence:.2f})")

   # Auto-tag
   applied_tags = ai.auto_tag("/path/to/file.txt", min_confidence=0.7)
   print(f"Applied tags: {', '.join(applied_tags)}")

   # Find files with tags
   files = ai.find_by_tags(["documentation", "python"])
   for file in files:
       print(f"Found: {file}")

Tagging Best Practices
--------------------

1. **Be Consistent**: Use a consistent tagging scheme across your files
2. **Use Hierarchies**: Organize related tags into hierarchies
3. **Combine Manual and Auto-Tagging**: Use AI suggestions but review them for accuracy
4. **Don't Over-Tag**: Too many tags can become unmanageable
5. **Use Tag Schemas**: Define schemas for different aspects (type, status, topic)
6. **Review Periodically**: Audit and refine your tagging system regularly

Advanced Tagging Features
-----------------------

Custom Tag Classifiers
~~~~~~~~~~~~~~~~~~~

Train custom tag classifiers for domain-specific tagging:

.. code-block:: python

   # Train a custom tag classifier
   ai.train_tag_classifier(
       tag="financial_report",
       positive_examples=["/path/to/financial1.pdf", "/path/to/financial2.pdf"],
       negative_examples=["/path/to/other1.pdf", "/path/to/other2.pdf"]
   )

   # Use the custom classifier
   is_financial = ai.classify_tag("financial_report", "/path/to/unknown.pdf")
   print(f"Is financial report: {is_financial}")

Tag Analysis
~~~~~~~~~~

Analyze your tagging patterns:

.. code-block:: bash

   # Get tag statistics
   aichemist tag-stats

   # Visualize tag relationships
   aichemist tag-visualize --output tag_graph.html

   # Find similar tags (potential duplicates)
   aichemist tag-similar

   # Get tag recommendations for a directory
   aichemist tag-recommend --directory /path/to/directory

Tag-Based Workflows
----------------

Using tags to build automated workflows:

.. code-block:: bash

   # Process all files with a specific tag
   aichemist process --tags "needs_processing"

   # Apply transformations to tagged files
   aichemist transform --tags "document,needs_conversion" --convert-to pdf

   # Build collections based on tags
   aichemist collection --create "research_papers" --tags "research,paper,published"

   # Generate reports based on tags
   aichemist report --tags "financial,quarterly" --output quarterly_report.pdf