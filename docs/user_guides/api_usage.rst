API Usage
=========

This guide explains how to use The AIchemist Codex programmatically through its Python API.

Getting Started
-------------

Import and Initialize
~~~~~~~~~~~~~~~~~

To use the AIchemist Codex in your Python scripts or applications:

.. code-block:: python

   from aichemist_codex import AIchemist

   # Initialize with default configuration
   ai = AIchemist()

   # Initialize with custom configuration file
   ai = AIchemist(config_path="/path/to/config.yaml")

   # Initialize with configuration profile
   ai = AIchemist(profile="development")

   # Initialize with specific project directory
   ai = AIchemist(project_dir="/path/to/project")

Core API Functionality
--------------------

Project Management
~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a new project
   ai.create_project("/path/to/new_project")

   # Create a project with template
   ai.create_project("/path/to/new_project", template="research")

   # List available templates
   templates = ai.list_templates()

   # Get project info
   project_info = ai.get_project_info()

   # Switch to a different project
   ai.set_project("/path/to/another_project")

   # List configured projects
   projects = ai.list_projects()

File Operations
~~~~~~~~~~~~

.. code-block:: python

   # Add a file to the system
   ai.add_file("/path/to/file.txt")

   # Add with metadata
   ai.add_file("/path/to/file.txt", metadata={"author": "John Doe", "status": "draft"})

   # Add multiple files
   ai.add_files(["/path/to/file1.txt", "/path/to/file2.pdf"])

   # Add directory recursively
   ai.add_directory("/path/to/documents", recursive=True)

   # Update a file
   ai.update_file("/path/to/modified_file.txt")

   # Remove a file
   ai.remove_file("/path/to/file.txt")

Search API
~~~~~~~~

.. code-block:: python

   # Basic search
   results = ai.search("quantum computing")

   # Specify search provider
   results = ai.search("quantum computing", provider="vector")

   # Limit results
   results = ai.search("quantum computing", limit=5)

   # Filter by file type
   results = ai.search("quantum computing", file_types=["pdf", "docx"])

   # Search in specific directory
   results = ai.search("quantum computing", directory="/path/to/documents")

   # Search with metadata
   results = ai.search("quantum computing", metadata={"author": "John Doe"})

   # Advanced metadata query
   results = ai.search("quantum computing",
                       metadata_query="created_date > '2023-01-01' AND status = 'published'")

   # Process search results
   for result in results:
       print(f"File: {result.file_path}")
       print(f"Score: {result.score}")
       print(f"Snippet: {result.snippet}")
       print(f"Metadata: {result.metadata}")

Tagging API
~~~~~~~~~

.. code-block:: python

   # Add tags to a file
   ai.add_tags("/path/to/file.txt", ["ai", "research", "draft"])

   # Remove tags
   ai.remove_tags("/path/to/file.txt", ["draft"])

   # Get tags for a file
   tags = ai.get_tags("/path/to/file.txt")

   # Find files with specific tags
   files = ai.find_by_tags(["ai", "research"])

   # Get tag suggestions
   suggestions = ai.suggest_tags("/path/to/file.txt")

   # Apply suggested tags
   ai.apply_suggested_tags("/path/to/file.txt", min_confidence=0.7)

   # Create tag hierarchy
   ai.create_tag_relation("machine_learning", "ai", relation_type="child_of")

   # Get child tags
   children = ai.get_child_tags("ai")

Metadata API
~~~~~~~~~~

.. code-block:: python

   # Get all metadata
   metadata = ai.get_metadata("/path/to/file.txt")

   # Get specific metadata field
   author = ai.get_metadata_field("/path/to/file.txt", "author")

   # Set a single field
   ai.set_metadata_field("/path/to/file.txt", "status", "published")

   # Set multiple fields
   ai.set_metadata({
       "author": "John Doe",
       "status": "published",
       "version": "1.2"
   }, "/path/to/file.txt")

   # Remove a field
   ai.remove_metadata_field("/path/to/file.txt", "draft_version")

   # Extract metadata automatically
   extracted = ai.extract_metadata("/path/to/file.pdf")

   # Create metadata template
   ai.create_metadata_template("document", ["author", "title", "status", "department"])

   # Apply template
   ai.apply_metadata_template("document", "/path/to/file.txt")

Content Analysis API
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate summary
   summary = ai.generate_summary("/path/to/file.txt")

   # Extract keywords
   keywords = ai.extract_keywords("/path/to/file.txt")

   # Identify entities
   entities = ai.extract_entities("/path/to/file.txt")

   # Generate topics
   topics = ai.extract_topics("/path/to/file.txt")

   # Sentiment analysis
   sentiment = ai.analyze_sentiment("/path/to/file.txt")

   # Batch analysis
   analysis = ai.analyze_content("/path/to/file.txt",
                                 analyzers=["summary", "keywords", "entities"])

Relationship API
~~~~~~~~~~~~~

.. code-block:: python

   # Find related files
   related = ai.find_related_files("/path/to/file.txt")

   # Add manual relationship
   ai.add_relationship("/path/to/file1.txt", "/path/to/file2.txt",
                      relationship_type="references", strength=0.8)

   # Get relationships
   relationships = ai.get_relationships("/path/to/file.txt")

   # Remove relationship
   ai.remove_relationship("/path/to/file1.txt", "/path/to/file2.txt")

   # Find by relationship type
   files = ai.find_by_relationship("/path/to/file.txt", relationship_type="references")

   # Get relationship graph
   graph = ai.get_relationship_graph("/path/to/file.txt", depth=2)

Content Processing API
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Index content
   ai.index_directory("/path/to/directory")

   # Process file
   ai.process_file("/path/to/file.txt")

   # Reindex all content
   ai.reindex()

   # Get index status
   status = ai.get_index_status()

   # Check if file is indexed
   is_indexed = ai.is_indexed("/path/to/file.txt")

Output Formatting API
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate formatted output
   output = ai.format_output(["/path/to/file1.txt", "/path/to/file2.txt"],
                            format="markdown")

   # Use template
   output = ai.format_with_template(["/path/to/file.txt"], template="report")

   # Export to file
   ai.export_formatted(["/path/to/file.txt"], format="html",
                       output_path="report.html")

   # List available templates
   templates = ai.list_output_templates()

System Management API
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Export system data
   ai.export_data("/path/to/export")

   # Import data
   ai.import_data("/path/to/import.zip")

   # Backup system
   ai.backup("/path/to/backup")

   # Restore from backup
   ai.restore("/path/to/backup.zip")

   # Get system stats
   stats = ai.get_system_stats()

   # Clear cache
   ai.clear_cache()

Advanced API Usage
----------------

Working with Multiple Files
~~~~~~~~~~~~~~~~~~~~~~~

Process and analyze multiple files efficiently:

.. code-block:: python

   # Process files in bulk
   files = ["/path/to/file1.txt", "/path/to/file2.pdf", "/path/to/file3.docx"]

   # Add files in batch
   ai.add_files(files)

   # Extract metadata in batch
   metadata_results = ai.extract_metadata_batch(files)

   # Generate summaries in batch
   summaries = ai.generate_summaries(files)

   # Apply tags in batch
   ai.add_tags_batch(files, ["processed", "batch"])

Asynchronous Operations
~~~~~~~~~~~~~~~~~~~~

For long-running operations, use the async API:

.. code-block:: python

   import asyncio

   # Initialize async client
   ai_async = AIchemist(async_mode=True)

   async def process_large_directory():
       # Start async indexing
       task_id = await ai_async.index_directory_async("/path/to/large_directory")

       # Check status periodically
       while True:
           status = await ai_async.get_task_status(task_id)
           print(f"Progress: {status.progress}%")
           if status.completed:
               break
           await asyncio.sleep(1)

       # Get results
       results = await ai_async.get_task_results(task_id)
       return results

   # Run async function
   results = asyncio.run(process_large_directory())

Custom Callbacks
~~~~~~~~~~~~~

Register callbacks for various events:

.. code-block:: python

   # Define callback functions
   def on_file_indexed(file_path, status):
       print(f"Indexed: {file_path}, Status: {status}")

   def on_error(error, context):
       print(f"Error: {error} in context {context}")

   # Register callbacks
   ai.register_callback("file_indexed", on_file_indexed)
   ai.register_callback("error", on_error)

   # Use with context
   with ai.callbacks_enabled():
       ai.index_directory("/path/to/documents")

Extension API
~~~~~~~~~~

Create custom extensions and plugins:

.. code-block:: python

   from aichemist_codex.extensions import Extension

   # Create custom extension
   class MyCustomExtension(Extension):
       def __init__(self, config=None):
           super().__init__(name="my_extension", config=config)

       def initialize(self):
           # Setup extension
           pass

       def process_file(self, file_path):
           # Custom processing logic
           return {"custom_data": "some value"}

   # Register extension
   ai.register_extension(MyCustomExtension())

   # Use extension
   result = ai.extensions.my_extension.process_file("/path/to/file.txt")

Advanced Configuration via API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure the system programmatically:

.. code-block:: python

   # Get current config
   config = ai.get_config()

   # Update config sections
   ai.update_config("search", {"default_provider": "vector", "result_limit": 20})

   # Update nested config
   ai.update_config("providers.vector", {"model": "all-MiniLM-L6-v2", "dimensions": 384})

   # Save config changes
   ai.save_config()

   # Create a new profile
   ai.create_config_profile("custom_profile", {"search.result_limit": 50})

   # Switch profile
   ai.set_profile("custom_profile")

Integration Examples
-----------------

Web Application Integration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import Flask, request, jsonify
   from aichemist_codex import AIchemist

   app = Flask(__name__)
   ai = AIchemist(project_dir="/path/to/project")

   @app.route("/search", methods=["POST"])
   def search():
       query = request.json.get("query")
       provider = request.json.get("provider", "vector")
       limit = request.json.get("limit", 10)

       results = ai.search(query, provider=provider, limit=limit)

       return jsonify({
           "results": [
               {
                   "file": r.file_path,
                   "score": r.score,
                   "snippet": r.snippet
               }
               for r in results
           ]
       })

   @app.route("/tags/<path:file_path>", methods=["GET"])
   def get_tags(file_path):
       tags = ai.get_tags(file_path)
       return jsonify({"tags": tags})

   if __name__ == "__main__":
       app.run(debug=True)

Script Automation Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aichemist_codex import AIchemist
   import os
   import argparse

   def process_new_documents(directory, output_format="markdown"):
       ai = AIchemist()

       # Get all files in directory
       files = [os.path.join(directory, f) for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))]

       # Process each file
       for file_path in files:
           print(f"Processing {file_path}")

           # Add file to system
           ai.add_file(file_path)

           # Extract metadata
           metadata = ai.extract_metadata(file_path)
           print(f"Extracted metadata: {len(metadata)} fields")

           # Suggest and apply tags
           tags = ai.suggest_tags(file_path)
           ai.apply_suggested_tags(file_path, min_confidence=0.7)
           print(f"Applied tags: {ai.get_tags(file_path)}")

           # Generate summary
           summary = ai.generate_summary(file_path)
           print(f"Generated summary of {len(summary)} characters")

       # Generate report
       output = ai.format_output(files, format=output_format)
       output_path = os.path.join(directory, "report." + output_format)

       with open(output_path, "w") as f:
           f.write(output)

       print(f"Report generated at {output_path}")

   if __name__ == "__main__":
       parser = argparse.ArgumentParser(description="Process new documents")
       parser.add_argument("directory", help="Directory with documents to process")
       parser.add_argument("--format", default="markdown",
                           choices=["markdown", "html", "text"],
                           help="Output format")

       args = parser.parse_args()
       process_new_documents(args.directory, args.format)

Error Handling
-----------

.. code-block:: python

   from aichemist_codex import AIchemist
   from aichemist_codex.exceptions import AIchemistError, FileNotFoundError, IndexError

   ai = AIchemist()

   try:
       # Attempt operation
       ai.process_file("/path/to/file.txt")

   except FileNotFoundError as e:
       print(f"File not found: {e}")
       # Handle missing file

   except IndexError as e:
       print(f"Index error: {e}")
       # Handle index related issues

   except AIchemistError as e:
       print(f"General error: {e}")
       # Handle any other AIchemist errors

   except Exception as e:
       print(f"Unexpected error: {e}")
       # Handle unexpected errors

Best Practices
------------

1. **Initialize Once**: Create a single AIchemist instance and reuse it throughout your application
2. **Batch Operations**: Use batch methods when processing multiple files for better performance
3. **Error Handling**: Always implement proper error handling for robust applications
4. **Resource Management**: Close the AIchemist instance when done to free resources
5. **Configuration**: Use configuration profiles for different environments
6. **Async for Long Operations**: Use async methods for long-running operations
7. **Logging**: Configure logging to track operation progress and issues
8. **Extension Isolation**: Create isolated extensions for custom functionality

Performance Tips
~~~~~~~~~~~~~

.. code-block:: python

   # Configure for performance
   ai = AIchemist(
       config={
           "performance": {
               "cache_size": 512,  # MB
               "batch_size": 100,
               "parallel_processing": True,
               "max_workers": 4
           }
       }
   )

   # Use batch operations
   ai.add_files(files, batch_size=50)

   # Process in parallel
   ai.process_directory("/path/to/documents", parallel=True, max_workers=4)

   # Use the context manager for automatic cleanup
   with AIchemist() as ai:
       ai.index_directory("/path/to/documents")
       # Resources automatically released at the end of the block