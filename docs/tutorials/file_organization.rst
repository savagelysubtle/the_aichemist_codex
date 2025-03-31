File Organization Tutorial
========================

This tutorial explores the automated file organization capabilities of The Aichemist Codex, showing you how to create, customize, and apply organization rules to efficiently structure your document collections.

Understanding File Organization
----------------------------

The Aichemist Codex provides a powerful system for organizing files based on various attributes:

- Content analysis (topics, entities, document type)
- Metadata (creation date, author, title)
- Tags (manually assigned or auto-generated)
- File properties (type, size, extension)

Organization can be performed through:

- Physical reorganization (files are moved to new locations)
- Symbolic/hard links (files remain in place but are accessible from organized locations)
- Virtual organization (files are accessible through a virtual filesystem interface)

Basic Organization
---------------

To organize files with default settings:

.. code-block:: bash

   # Preview organization (no changes made)
   codex organize ~/my_documents --dry-run

   # Apply organization
   codex organize ~/my_documents --confirm

By default, this organizes files into directories based on their type:

- Documents/ (PDFs, DOCs, etc.)
- Images/ (PNGs, JPGs, etc.)
- Audio/ (MP3s, WAVs, etc.)
- Video/ (MP4s, MOVs, etc.)
- Code/ (source code files)
- Archives/ (ZIPs, RARs, etc.)
- Other/ (miscellaneous files)

Organization Methods
-----------------

The Aichemist Codex supports multiple organization methods:

**Type-based organization**:

.. code-block:: bash

   codex organize ~/my_documents --method type

**Date-based organization**:

.. code-block:: bash

   codex organize ~/my_documents --method date

Creates a year/month structure (e.g., 2023/05/).

**Tag-based organization**:

.. code-block:: bash

   codex organize ~/my_documents --method tags

Creates directories based on applied tags.

**Content-based organization**:

.. code-block:: bash

   codex organize ~/my_documents --method content

Uses semantic analysis to group similar content together.

**Custom rule-based organization**:

.. code-block:: bash

   codex organize ~/my_documents --method rules --rules-file my_rules.yaml

Uses custom defined rules (explained below).

Organization Rules
---------------

Custom organization rules are defined in YAML files. Here's an example:

.. code-block:: yaml

   version: 1.0

   # Global settings
   settings:
     organization_method: hierarchical  # hierarchical, flat, or hybrid
     treat_duplicates: move_to_duplicates  # skip, move_to_duplicates, or rename
     handle_conflicts: ask  # ask, rename, or skip
     create_missing_dirs: true

   # Rule definitions
   rules:
     # Project documentation rule
     - name: Project Documentation
       conditions:
         - type: content_match
           pattern: "project plan|technical spec|requirements"
         - type: tag
           value: "documentation"
       target: "Projects/Documentation/{extracted.project_name|Unknown Project}"

     # Research papers rule
     - name: Research Papers
       conditions:
         - type: extension
           value: [pdf, doc, docx]
         - type: content_match
           pattern: "abstract|methodology|conclusion"
       target: "Research/{extracted.year|Unknown Year}/{extracted.topic|Uncategorized}"

     # Source code rule
     - name: Source Code
       conditions:
         - type: extension
           value: [py, js, java, cpp, c, rb]
       target: "Code/{extension}/{extracted.project_name|Misc}"

     # Personal documents rule
     - name: Personal Documents
       conditions:
         - type: tag
           value: "personal"
       target: "Personal/{file.created_year}/{file.created_month}"

   # Metadata extraction definitions
   extractors:
     - name: project_name
       method: regex
       pattern: "Project Name: ([\\w\\s\\-]+)"
       fallback: "content_analysis"

     - name: year
       method: metadata
       field: "creation_year"
       fallback: "current_year"

     - name: topic
       method: semantic
       model: "topic_classifier"
       options:
         categories: ["AI", "Biology", "Chemistry", "Physics", "Economics"]

To apply these rules:

.. code-block:: bash

   codex organize ~/my_documents --rules-file my_rules.yaml

Rule Components
------------

Rules consist of:

1. **Conditions**: Criteria for matching files
2. **Target**: Template for the destination path
3. **Options**: Additional processing instructions

**Condition types**:

- `extension`: File extension(s)
- `content_match`: Text patterns in the content
- `tag`: Applied tags
- `metadata`: File metadata values
- `size`: File size ranges
- `created`: Creation date ranges
- `modified`: Modification date ranges
- `semantic`: Semantic content matching

**Target path templates**:

The target path can include:

- Static text: `"Research/Papers/"`
- File attributes: `"{file.name}"`, `"{file.extension}"`
- Extracted metadata: `"{extracted.project_name}"`
- Date components: `"{file.created_year}"`, `"{file.created_month}"`
- Conditional paths: `"{tag.category|Uncategorized}"`

Making Backups Before Organizing
-----------------------------

Before applying organization rules to important files:

.. code-block:: bash

   # Create a backup
   codex backup ~/my_documents --output ~/documents_backup.zip

   # Verify backup
   codex backup --verify ~/documents_backup.zip

   # Organize with confidence
   codex organize ~/my_documents --rules-file my_rules.yaml

Incremental Organization
---------------------

You can organize incrementally:

.. code-block:: bash

   # Organize only new files
   codex organize ~/my_documents --incremental

   # Organize files modified in the last week
   codex organize ~/my_documents --modified-since 7d

Virtual Organization
-----------------

Instead of physically moving files, you can create a virtual organized view:

.. code-block:: bash

   # Create a virtual organization
   codex organize ~/my_documents --virtual --output ~/organized_view

This creates symbolic links in an organized structure while leaving original files in place.

Organization Reports
----------------

Generate reports on organization results:

.. code-block:: bash

   # Generate a detailed report
   codex organize ~/my_documents --report organization_report.html

   # Generate statistics only
   codex organize ~/my_documents --stats-only > organization_stats.json

Tag-Based Organization
------------------

Tags are particularly useful for organization:

.. code-block:: bash

   # Organize by primary tag
   codex organize ~/my_documents --by-primary-tag

   # Organize using tag hierarchy
   codex organize ~/my_documents --by-tag-hierarchy

   # Use tag categories as directory levels
   codex organize ~/my_documents --by-tag-categories

Content-Based Organization
----------------------

For automatic content-based organization:

.. code-block:: bash

   # Organize by detected topic
   codex organize ~/my_documents --by-topic

   # Organize by content similarity
   codex organize ~/my_documents --by-clusters --num-clusters 10

   # Organize by document type
   codex organize ~/my_documents --by-document-type

Using Python API for Organization
------------------------------

For programmatic organization:

.. code-block:: python

   import asyncio
   from pathlib import Path
   from the_aichemist_codex.backend.organization import FileOrganizer
   from the_aichemist_codex.backend.rules import OrganizationRuleSet

   async def organize_documents():
       # Initialize the organizer
       organizer = FileOrganizer()

       # Load custom rules
       rules = OrganizationRuleSet.from_file("my_rules.yaml")

       # Set up organization parameters
       source_dir = Path("~/my_documents").expanduser()

       # Preview organization (returns a plan but doesn't execute)
       plan = await organizer.plan_organization(
           source_dir=source_dir,
           rules=rules,
           incremental=True
       )

       # Print the organization plan
       print(f"Organization plan contains {len(plan.moves)} operations")
       for move in plan.moves[:5]:  # Show first 5 moves
           print(f"- {move.source} → {move.destination}")

       # Execute the plan with confirmation
       if input("Apply organization? (y/n): ").lower() == 'y':
           result = await organizer.execute_plan(plan)
           print(f"Organized {result.success_count} files")
           if result.errors:
               print(f"Encountered {len(result.errors)} errors")
               for error in result.errors:
                   print(f"- {error}")

   # Run the async function
   asyncio.run(organize_documents())

Advanced Organization Features
---------------------------

**Deduplication during organization**:

.. code-block:: bash

   codex organize ~/my_documents --deduplicate

**Content-aware filename generation**:

.. code-block:: bash

   codex organize ~/my_documents --rename-by-content

**Handle multi-document files (like PDFs)**:

.. code-block:: bash

   codex organize ~/my_documents --split-documents

**Custom preprocessing**:

.. code-block:: bash

   codex organize ~/my_documents --preprocess my_script.py

Where `my_script.py` is a custom preprocessing script.

Integration with Other Codex Features
----------------------------------

Organization works well with other Codex features:

.. code-block:: bash

   # First analyze and tag content
   codex tag --auto ~/my_documents

   # Then organize based on tags
   codex organize ~/my_documents --by-tags

   # Search within organized structure
   codex search --method semantic "quantum computing" --in ~/organized_docs

Maintaining Organization Over Time
-------------------------------

To maintain organization as you add new files:

.. code-block:: bash

   # Set up a watch folder
   codex watch --folder ~/Downloads --organize-using my_rules.yaml

This monitors the folder and automatically organizes new files.

You can also set up scheduled organization:

.. code-block:: bash

   codex schedule --task organize --rules my_rules.yaml --frequency daily

Conclusion
--------

With The Aichemist Codex's organization capabilities, you can maintain a clean, structured document repository that adapts to your specific needs. Experiment with different organization strategies and rules to find the system that works best for your workflow.

Remember that organization settings can be saved as profiles, allowing you to quickly apply your preferred organization strategy to different directories:

.. code-block:: bash

   # Save current organization settings as a profile
   codex organize --save-profile research_organization

   # Apply the profile later
   codex organize ~/new_documents --profile research_organization
