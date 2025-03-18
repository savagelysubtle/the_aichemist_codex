Ingest Manager
=============

The Ingest Manager is responsible for coordinating the ingestion of content from various sources.

Overview
--------

The Ingest Manager:

* Coordinates the ingestion process
* Manages ingestion sources
* Routes content through appropriate processors
* Tracks ingestion status and history

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.ingest.ingest_manager
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* **Multi-Source Support**: Ingests content from multiple sources
* **Processor Pipeline**: Routes content through appropriate processors
* **Batch Processing**: Handles batch ingestion for improved performance
* **Error Handling**: Robust error handling and recovery mechanisms
* **Event Emission**: Emits events for ingestion status and progress

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.ingest import IngestManager
   from pathlib import Path

   # Initialize the ingest manager
   ingest_manager = IngestManager()

   # Ingest a single file
   result = await ingest_manager.ingest_file(
       file_path=Path("/path/to/document.pdf"),
       metadata={"source": "user_upload", "author": "John Doe"},
       process_content=True
   )

   # Ingest a directory
   results = await ingest_manager.ingest_directory(
       directory_path=Path("/path/to/documents/"),
       recursive=True,
       file_types=[".pdf", ".txt", ".docx"],
       metadata={"source": "user_upload"},
       process_content=True
   )

   # Process ingestion results
   for result in results:
       if result.success:
           print(f"Successfully ingested: {result.file_path}")
           print(f"Generated ID: {result.document_id}")
       else:
           print(f"Failed to ingest: {result.file_path}")
           print(f"Error: {result.error_message}")