Tagging Workflow Tutorial
=====================

This tutorial explains how to use The Aichemist Codex's powerful tagging system to organize and classify your files.

Understanding Tags
----------------

Tags in The Aichemist Codex are more than just simple labels. They're structured metadata that can include:

- **Name**: The primary tag identifier (e.g., "research")
- **Description**: Optional detailed description of the tag's purpose
- **Category**: Optional grouping of related tags (e.g., "project", "status", "topic")
- **Parent Tags**: Optional hierarchical relationship with other tags
- **Color**: Optional visual indicator for the tag

Tags are stored in a database and can be applied to any file in your codex.

Creating Tags Manually
--------------------

Let's start by creating some tags manually:

.. code-block:: bash

   # Create a simple tag
   codex tag --create "research" --description "Research materials and references"

   # Create a tag with a category
   codex tag --create "in-progress" --category "status" --description "Work in progress"

   # Create a hierarchical tag
   codex tag --create "python" --parent "programming" --description "Python programming language"

You can list all available tags with:

.. code-block:: bash

   codex tag --list-all

This will show all tags, their descriptions, categories, and hierarchical relationships.

Applying Tags Manually
--------------------

To apply tags to files manually:

.. code-block:: bash

   # Apply a single tag
   codex tag --add "research" document.pdf

   # Apply multiple tags
   codex tag --add "research,python,in-progress" scripts/*.py

   # Apply tags to multiple files
   codex tag --add "important" doc1.pdf doc2.pdf doc3.pdf

You can view tags applied to a file with:

.. code-block:: bash

   codex tag --list document.pdf

And remove tags with:

.. code-block:: bash

   codex tag --remove "in-progress" document.pdf

Automatic Tag Suggestions
-----------------------

The Aichemist Codex can analyze your files and suggest appropriate tags using multiple methods:

1. **Content-based analysis**: Examines the file content to identify key topics and concepts
2. **Metadata extraction**: Uses file metadata like titles, authors, and creation dates
3. **Collaborative filtering**: Suggests tags based on similar files in your codex
4. **Machine learning classification**: Uses pre-trained models to categorize content

To get tag suggestions for a file:

.. code-block:: bash

   codex tag --suggest document.pdf

This will display a list of suggested tags with confidence scores. You can then choose which tags to apply.

To see what factors contributed to each suggestion:

.. code-block:: bash

   codex tag --suggest --explain document.pdf

Automatic Tagging
---------------

For fully automated tagging:

.. code-block:: bash

   codex tag --auto document.pdf

By default, this applies suggestions with a confidence score above 0.7. You can adjust this threshold:

.. code-block:: bash

   codex tag --auto --threshold 0.5 document.pdf

You can also specify which suggestion methods to use:

.. code-block:: bash

   codex tag --auto --methods content,metadata document.pdf

Creating a Tagging Workflow
-------------------------

Here's a recommended workflow for efficient tagging:

1. **Set up tag categories and hierarchies**:

   Create a consistent set of tag categories and top-level tags:

   .. code-block:: bash

      # Create categories
      codex tag --create "project" --category "category"
      codex tag --create "status" --category "category"
      codex tag --create "topic" --category "category"

      # Create top-level tags
      codex tag --create "research-project" --category "project"
      codex tag --create "personal" --category "project"
      codex tag --create "draft" --category "status"
      codex tag --create "final" --category "status"

2. **Process new files in batches**:

   When you get new files, add them to your codex and tag them in one go:

   .. code-block:: bash

      # Add files to codex
      codex add ~/Downloads/*.pdf

      # Generate tag suggestions
      codex tag --suggest --batch ~/Downloads/*.pdf > tag_suggestions.json

      # Review suggestions (opens in default editor)
      codex tag --review tag_suggestions.json

      # Apply approved suggestions
      codex tag --apply tag_suggestions.json

3. **Refine tags over time**:

   Periodically review and refine your tagging:

   .. code-block:: bash

      # Find files without tags
      codex search --untagged

      # Find files with specific tags
      codex search --tag "research-project" --tag "draft"

      # Update tags as files progress
      codex tag --remove "draft" --add "final" completed_report.pdf

Using Tag Hierarchies
-------------------

Tag hierarchies help organize related tags:

.. code-block:: bash

   # Create a parent tag
   codex tag --create "programming" --description "Programming languages and tools"

   # Create child tags
   codex tag --create "python" --parent "programming"
   codex tag --create "javascript" --parent "programming"
   codex tag --create "golang" --parent "programming"

When you search for files with the parent tag, it includes all files with child tags:

.. code-block:: bash

   # Find all programming-related files
   codex search --tag "programming"

You can view the tag hierarchy with:

.. code-block:: bash

   codex tag --hierarchy

Using Tags in Python
------------------

For programmatic access to the tagging system:

.. code-block:: python

   import asyncio
   from pathlib import Path
   from the_aichemist_codex.backend.tagging import TagManager, TagSuggester

   async def tag_management_example():
       # Initialize tag manager
       tag_manager = TagManager()
       await tag_manager.initialize()

       # Create a tag
       tag_id = await tag_manager.create_tag(
           name="project-x",
           description="Project X research materials",
           category="project"
       )

       # Apply tag to file
       file_path = Path("research_data.pdf")
       await tag_manager.add_file_tag(file_path, tag_id)

       # Get tags for a file
       tags = await tag_manager.get_file_tags(file_path)
       print(f"Tags for {file_path}:")
       for tag in tags:
           print(f"- {tag.name}: {tag.description}")

       # Use the suggester
       suggester = TagSuggester(tag_manager)
       suggestions = await suggester.suggest_tags_for_file(file_path)

       print("\nTag suggestions:")
       for tag, confidence in suggestions:
           print(f"- {tag.name}: {confidence:.2f}")

   # Run the async function
   asyncio.run(tag_management_example())

Custom Tagging Rules
------------------

You can define custom rules for automatic tagging in a `tagging_rules.json` file:

.. code-block:: json

   {
     "rules": [
       {
         "name": "Python files",
         "conditions": [
           {"type": "extension", "value": ".py"}
         ],
         "tags": ["python", "code"]
       },
       {
         "name": "Research documents",
         "conditions": [
           {"type": "content", "value": "research", "min_occurrences": 3},
           {"type": "content", "value": "methodology"}
         ],
         "tags": ["research"]
       }
     ]
   }

Apply these rules with:

.. code-block:: bash

   codex tag --rules tagging_rules.json *.py *.pdf

Advanced Tag Features
-------------------

**Tag-based organization**:

.. code-block:: bash

   # Organize files based on tags
   codex organize --by-tags ~/my_codex

This creates directories based on tag categories and moves files accordingly.

**Tag statistics**:

.. code-block:: bash

   # View tag usage statistics
   codex tag --stats

**Export and import tags**:

.. code-block:: bash

   # Export all tag definitions
   codex tag --export tags.json

   # Import tag definitions
   codex tag --import tags.json

**Tag cleanup**:

.. code-block:: bash

   # Find unused tags
   codex tag --unused

   # Remove unused tags
   codex tag --cleanup

By mastering these tagging techniques, you can create a powerful organization system for your files, making it easy to find, group, and manage related content.
