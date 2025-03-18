Importing Files
=============

This tutorial will guide you through adding and importing files into The AIchemist Codex. You'll learn how to:

1. Add individual files
2. Import entire directories
3. Set import options
4. Configure automatic processing

Prerequisites
------------

Before starting this tutorial, make sure you have:

- Installed The AIchemist Codex (:doc:`quick_start`)
- Created a project (:doc:`quick_start`)

Adding Individual Files
--------------------

To add a single file to your project:

.. code-block:: bash

   aichemist add /path/to/file.pdf

This imports the file into your content directory and processes it.

You can add multiple files at once:

.. code-block:: bash

   aichemist add /path/to/file1.pdf /path/to/file2.docx /path/to/file3.txt

Add files with custom metadata:

.. code-block:: bash

   aichemist add /path/to/file.pdf --metadata "author=John Doe,status=draft"

Importing Directories
------------------

Import an entire directory:

.. code-block:: bash

   aichemist add /path/to/directory

By default, this doesn't include subdirectories. To include them:

.. code-block:: bash

   aichemist add /path/to/directory --recursive

Filter files during import:

.. code-block:: bash

   # Import only PDF files
   aichemist add /path/to/directory --file-types pdf

   # Import multiple file types
   aichemist add /path/to/directory --file-types pdf,docx,txt

Import with custom naming:

.. code-block:: bash

   aichemist add /path/to/directory --name-pattern "imported_{filename}"

Import Options
-----------

Control how files are imported:

**Copy vs. Link mode**:

.. code-block:: bash

   # Copy files (default)
   aichemist add /path/to/files --mode copy

   # Link to original files
   aichemist add /path/to/files --mode link

**Duplicate handling**:

.. code-block:: bash

   # Skip existing files
   aichemist add /path/to/files --duplicates skip

   # Replace existing files
   aichemist add /path/to/files --duplicates replace

   # Keep both (rename new file)
   aichemist add /path/to/files --duplicates keep

Automatic Processing
-----------------

Control automatic processing during import:

.. code-block:: bash

   # Add without processing
   aichemist add /path/to/files --no-process

   # Add with specific processing steps
   aichemist add /path/to/files --process "metadata,text,index"

   # Add with automatic tagging
   aichemist add /path/to/files --auto-tag

Monitor import progress:

.. code-block:: bash

   aichemist add /path/to/large_directory --recursive --verbose

Batch Importing
------------

For large imports, use batch mode:

.. code-block:: bash

   aichemist batch-import /path/to/import_list.txt

Where `import_list.txt` contains a list of files/directories to import.

Schedule regular imports:

.. code-block:: bash

   aichemist add /path/to/directory --schedule daily

Import from Remote Sources
-----------------------

Import from URLs:

.. code-block:: bash

   aichemist add https://example.com/document.pdf

Import from cloud storage:

.. code-block:: bash

   aichemist add s3://my-bucket/documents/ --cloud-credentials /path/to/credentials.json

Next Steps
---------

Now that you know how to import files, you can:

- Learn how to search your content in :doc:`first_search`
- Organize your files efficiently with :doc:`../organization/project_structure`
- Add tags to classify your content with :doc:`basic_tagging`

For comprehensive reference information on all import options, see the :doc:`/user_guides/basic_usage`.