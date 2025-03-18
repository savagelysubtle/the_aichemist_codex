Ingest (Legacy)
==============

.. note::
   This is a legacy documentation page. Please refer to the updated :doc:`domain/ingest`
   documentation for the current implementation.

The Ingest module provides functionality for importing files and data from various sources.

Current Implementation
--------------------

The Ingest system has been migrated to the new domain-driven architecture. Please see:

* :doc:`domain/ingest` - Current ingest module documentation
* :doc:`domain/ingest/processors/index` - Ingest processors for different file types

.. raw:: html

   <meta http-equiv="refresh" content="0; url=domain/ingest.html">

.. automodule:: backend.src.ingest
   :members:
   :undoc-members:
   :show-inheritance:

Ingest Manager
------------

The IngestManager coordinates the ingestion of files from different sources.

.. automodule:: backend.src.ingest.manager
   :members:
   :undoc-members:
   :show-inheritance:

File System Ingestor
-----------------

The FileSystemIngestor imports files from local file systems.

.. automodule:: backend.src.ingest.file_system
   :members:
   :undoc-members:
   :show-inheritance:

Cloud Storage Ingestor
-------------------

The CloudStorageIngestor imports files from cloud storage services.

.. automodule:: backend.src.ingest.cloud_storage
   :members:
   :undoc-members:
   :show-inheritance:

Database Ingestor
--------------

The DatabaseIngestor imports structured data from databases.

.. automodule:: backend.src.ingest.database
   :members:
   :undoc-members:
   :show-inheritance:

Web Ingestor
----------

The WebIngestor imports content from web sources and APIs.

.. automodule:: backend.src.ingest.web
   :members:
   :undoc-members:
   :show-inheritance:

Email Ingestor
-----------

The EmailIngestor imports files and content from email systems.

.. automodule:: backend.src.ingest.email
   :members:
   :undoc-members:
   :show-inheritance:

Ingest Processors
--------------

The ingest processors perform transformations and validations on ingested data.

.. automodule:: backend.src.ingest.processors
   :members:
   :undoc-members:
   :show-inheritance:
