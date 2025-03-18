Ingest Models
============

The Ingest Models module defines data structures used throughout the ingestion process.

Overview
--------

The Ingest Models include:

* Data structures for ingestion requests and responses
* Status tracking models
* Configuration models for ingestion sources and processors
* Result models for processed content

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.ingest.models
   :members:
   :undoc-members:
   :show-inheritance:

Key Models
---------

* **IngestRequest**: Represents a request to ingest content
* **IngestResult**: Represents the result of an ingestion operation
* **IngestSource**: Represents a source of content for ingestion
* **IngestProcessor**: Represents a processor for specific content types
* **IngestStatus**: Tracks the status of an ingestion operation

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.ingest.models import (
       IngestRequest,
       IngestOptions,
       ContentType,
       ProcessingPriority
   )
   from pathlib import Path

   # Create an ingest request
   request = IngestRequest(
       source_path=Path("/path/to/document.pdf"),
       content_type=ContentType.PDF,
       options=IngestOptions(
           extract_text=True,
           extract_metadata=True,
           extract_images=False,
           priority=ProcessingPriority.NORMAL
       ),
       metadata={
           "author": "John Doe",
           "source": "user_upload",
           "tags": ["report", "financial"]
       }
   )

   # The request can then be passed to the IngestManager for processing