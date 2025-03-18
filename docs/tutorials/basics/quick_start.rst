Quick Start Tutorial
==================

This tutorial will guide you through setting up and using The AIchemist Codex for the first time. In just 15 minutes, you'll learn how to:

1. Install the software
2. Create your first project
3. Add and process files
4. Perform basic searches
5. Generate automatic tags

Installation
-----------

First, let's install The AIchemist Codex:

.. code-block:: bash

   pip install aichemist-codex

Verify the installation:

.. code-block:: bash

   aichemist --version

Setting Up Your First Project
---------------------------

Initialize a new project in your chosen directory:

.. code-block:: bash

   aichemist init ~/my_project

This creates the necessary directory structure and configuration files. Review the created structure:

.. code-block:: bash

   ls -la ~/my_project

You should see:
- `.aichemist/` directory with configuration files
- `content/` directory for your files
- `output/` directory for generated content

Adding and Processing Files
--------------------------

Let's add some files to your project:

.. code-block:: bash

   aichemist add ~/Documents/*.pdf

This will:
- Import the files to your project
- Extract metadata from the files
- Index the content for searching
- Process the files for relationships

Check the status of your project:

.. code-block:: bash

   aichemist status

This shows a summary of your project, including file counts and processing status.

Basic Searching
-------------

Now that you have files in your project, let's try searching:

.. code-block:: bash

   aichemist search "important concept"

Try a more advanced semantic search:

.. code-block:: bash

   aichemist search "machine learning applications" --provider vector

This finds conceptually related content, even if the exact terms aren't present.

Auto-Tagging Files
----------------

Generate tag suggestions for your files:

.. code-block:: bash

   aichemist tag suggest --file ~/my_project/content/document.pdf

Apply tags automatically:

.. code-block:: bash

   aichemist tag suggest --file ~/my_project/content/document.pdf --apply

View the applied tags:

.. code-block:: bash

   aichemist tag list --file ~/my_project/content/document.pdf

Next Steps
---------

Congratulations! You've completed the quick start tutorial. Now you can:

- Learn more about advanced search in :doc:`../advanced_search/semantic_search`
- Explore tagging strategies in :doc:`../organization/tagging_workflow`
- Organize your files effectively with :doc:`../organization/project_structure`
- Use the Python API with :doc:`../development/api_integration`

For comprehensive reference information, see the :doc:`/user_guides/index`.