Basic Tagging Tutorial
==================

This tutorial will guide you through the basics of tagging files in The AIchemist Codex. You'll learn how to:

1. Add manual tags to files
2. Use auto-tagging features
3. Search by tags
4. Organize your tag structure

Prerequisites
------------

Before starting this tutorial, make sure you have:

- Installed The AIchemist Codex (:doc:`quick_start`)
- Created a project with some files added

Manual Tagging
------------

Add tags to a file manually:

.. code-block:: bash

   aichemist tag add --file /path/to/file.pdf --tags "research,ai,draft"

This adds three tags to the specified file.

Remove tags from a file:

.. code-block:: bash

   aichemist tag remove --file /path/to/file.pdf --tags "draft"

List all tags for a file:

.. code-block:: bash

   aichemist tag list --file /path/to/file.pdf

Auto-Tagging
----------

The AIchemist Codex can suggest tags based on file content:

.. code-block:: bash

   aichemist tag suggest --file /path/to/file.pdf

This shows suggested tags without applying them. The output includes confidence scores.

Apply suggested tags:

.. code-block:: bash

   aichemist tag suggest --file /path/to/file.pdf --apply

Only tags with confidence above the default threshold will be applied.

Set a custom confidence threshold:

.. code-block:: bash

   aichemist tag suggest --file /path/to/file.pdf --apply --threshold 0.7

Searching by Tags
--------------

Find all files with specific tags:

.. code-block:: bash

   aichemist tag find --tags "research,ai"

This finds files that have both the "research" and "ai" tags.

Use tag-based search with other search criteria:

.. code-block:: bash

   aichemist search "machine learning" --tags "research,published"

Organizing Your Tags
-----------------

List all tags in your project:

.. code-block:: bash

   aichemist tag list-all

Create tag hierarchies (parent-child relationships):

.. code-block:: bash

   aichemist tag relate --parent "ai" --child "machine-learning"
   aichemist tag relate --parent "ai" --child "neural-networks"

Find all files with a parent tag (includes children):

.. code-block:: bash

   aichemist tag find --tags "ai" --include-children

Next Steps
---------

Now that you've learned the basics of tagging, you can:

- Develop more advanced tagging strategies in :doc:`../organization/tagging_workflow`
- Learn how to use tags with metadata in :doc:`../organization/metadata_management`
- Explore automatic tag suggestion tuning in the :doc:`/user_guides/tagging_guide`

For comprehensive reference information on all tagging capabilities, see the :doc:`/user_guides/tagging_guide`.