Metadata Guide
=============

This guide explains how to work with metadata in The AIchemist Codex to enhance file organization and searchability.

Understanding Metadata
--------------------

Metadata in The AIchemist Codex refers to structured information about your files. It includes:

* **File Properties**: Size, creation date, modification date, etc.
* **Content Metadata**: Author, title, keywords, etc.
* **Extracted Information**: Topics, entities, summaries, etc.
* **User-Added Metadata**: Custom fields and values
* **Relationships**: Connections to other files

Metadata is stored separately from the files themselves, allowing for rich data without modifying the original files.

Viewing Metadata
--------------

To view metadata for a file:

.. code-block:: bash

   # View all metadata for a file
   aichemist metadata show --file /path/to/file.txt

   # View specific metadata fields
   aichemist metadata show --file /path/to/file.txt --fields "author,title,created_date"

   # Export metadata to JSON
   aichemist metadata export --file /path/to/file.txt --output metadata.json

Using Python:

.. code-block:: python

   from aichemist_codex import AIchemist

   ai = AIchemist()

   # Get all metadata
   metadata = ai.get_metadata("/path/to/file.txt")

   # Get specific fields
   author = ai.get_metadata_field("/path/to/file.txt", "author")

   # Print all metadata
   for key, value in metadata.items():
       print(f"{key}: {value}")

Adding and Editing Metadata
-------------------------

Manual Metadata Management
~~~~~~~~~~~~~~~~~~~~~~~

Add or update metadata through the command line:

.. code-block:: bash

   # Add or update a single metadata field
   aichemist metadata set --file /path/to/file.txt --field "author" --value "John Doe"

   # Add or update multiple fields at once
   aichemist metadata set --file /path/to/file.txt --fields "author=John Doe,status=draft,priority=high"

   # Add metadata to multiple files
   aichemist metadata set --files "/path/to/file1.txt,/path/to/file2.pdf" --field "department" --value "Finance"

Using Python:

.. code-block:: python

   # Set a single field
   ai.set_metadata_field("/path/to/file.txt", "author", "John Doe")

   # Set multiple fields
   ai.set_metadata({
       "author": "John Doe",
       "status": "draft",
       "priority": "high"
   }, "/path/to/file.txt")

Removing Metadata
~~~~~~~~~~~~~~

Remove metadata fields:

.. code-block:: bash

   # Remove a single field
   aichemist metadata remove --file /path/to/file.txt --field "temp_status"

   # Remove multiple fields
   aichemist metadata remove --file /path/to/file.txt --fields "temp_status,draft_version"

Using Python:

.. code-block:: python

   # Remove a single field
   ai.remove_metadata_field("/path/to/file.txt", "temp_status")

   # Remove multiple fields
   ai.remove_metadata_fields("/path/to/file.txt", ["temp_status", "draft_version"])

Automatic Metadata Extraction
--------------------------

The AIchemist Codex can automatically extract metadata from files:

.. code-block:: bash

   # Extract metadata from a file
   aichemist metadata extract --file /path/to/file.pdf

   # Extract specific metadata types
   aichemist metadata extract --file /path/to/file.pdf --extractors "text,authors,topics"

   # Batch extract from multiple files
   aichemist metadata extract --directory /path/to/documents --recursive

Using Python:

.. code-block:: python

   # Extract all metadata
   extracted = ai.extract_metadata("/path/to/file.pdf")

   # Extract specific types
   authors = ai.extract_metadata("/path/to/file.pdf", extractors=["authors"])

   # Batch extract
   results = ai.extract_metadata_batch(["/path/to/file1.pdf", "/path/to/file2.docx"])

Available Metadata Extractors
~~~~~~~~~~~~~~~~~~~~~~~~~~

The AIchemist Codex includes several metadata extractors:

* **Basic**: File properties (size, dates, MIME type)
* **Text**: Text extraction and statistics
* **Authors**: Author information
* **Topics**: Topic identification using ML
* **Entities**: Named entity recognition
* **Language**: Language detection
* **Sentiment**: Sentiment analysis
* **Keywords**: Automatic keyword extraction
* **Images**: Image detection and analysis
* **Structure**: Document structure analysis
* **References**: Citation and reference extraction
* **Custom**: User-defined extractors

Metadata Templates
---------------

Define metadata templates for consistent application:

.. code-block:: bash

   # Create a metadata template
   aichemist metadata-template create --name "document" --fields "author,title,status,department,version"

   # Apply a template to a file
   aichemist metadata-template apply --template "document" --file /path/to/file.txt

   # Apply with default values
   aichemist metadata-template apply --template "document" --file /path/to/file.txt --defaults "status=draft,version=1.0"

Using Python:

.. code-block:: python

   # Create a template
   ai.create_metadata_template("document", ["author", "title", "status", "department", "version"])

   # Apply a template
   ai.apply_metadata_template("document", "/path/to/file.txt")

   # Apply with defaults
   ai.apply_metadata_template("document", "/path/to/file.txt", defaults={"status": "draft", "version": "1.0"})

Searching with Metadata
---------------------

Use metadata in searches:

.. code-block:: bash

   # Search for files with specific metadata
   aichemist search --metadata "author=John Doe"

   # Combine metadata and content search
   aichemist search "machine learning" --metadata "status=published,department=Research"

   # Search with metadata ranges
   aichemist search --metadata "created_date>2023-01-01,priority<3"

Using Python:

.. code-block:: python

   # Search with metadata
   results = ai.search(metadata={"author": "John Doe"})

   # Combined search
   results = ai.search("machine learning", metadata={"status": "published"})

   # Advanced metadata queries
   results = ai.search(metadata_query="created_date > '2023-01-01' AND (department = 'Research' OR department = 'Development')")

Metadata Best Practices
---------------------

1. **Be Consistent**: Use consistent naming and values for metadata fields
2. **Use Templates**: Define templates for common file types
3. **Don't Overuse**: Focus on useful metadata that adds value
4. **Combine with Tags**: Use metadata for structured data, tags for categories
5. **Regularly Update**: Keep metadata current as files change
6. **Use Automation**: Leverage automatic extraction where possible

Advanced Metadata Features
-----------------------

Metadata Validation
~~~~~~~~~~~~~~~~

Define validation rules for metadata fields:

.. code-block:: bash

   # Define a validation rule
   aichemist metadata-rule create --field "priority" --type "enum" --values "low,medium,high"
   aichemist metadata-rule create --field "version" --type "regex" --pattern "^\\d+\\.\\d+\\.\\d+$"

   # Validate metadata
   aichemist metadata validate --file /path/to/file.txt

   # Validate and fix issues
   aichemist metadata validate --file /path/to/file.txt --fix

Metadata Statistics
~~~~~~~~~~~~~~~

Analyze metadata across your files:

.. code-block:: bash

   # Get metadata statistics
   aichemist metadata stats

   # Get statistics for specific fields
   aichemist metadata stats --fields "author,department,status"

   # Export statistics to CSV
   aichemist metadata stats --output stats.csv

Bulk Metadata Operations
~~~~~~~~~~~~~~~~~~~~

Perform operations on multiple files:

.. code-block:: bash

   # Copy metadata from one file to another
   aichemist metadata copy --source /path/to/source.txt --target /path/to/target.txt

   # Batch update metadata
   aichemist metadata batch-update --directory /path/to/documents --field "status" --value "archived"

   # Find and replace in metadata
   aichemist metadata replace --field "department" --find "Marketing" --replace "Digital Marketing"