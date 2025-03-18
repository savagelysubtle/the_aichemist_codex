Ingest Processors
===============

The Ingest Processors module provides specialized processors for handling different types of content during ingestion.

.. toctree::
   :maxdepth: 2

   code_processor

Code Processor
-------------

The CodeProcessor specializes in processing source code files during ingestion.

.. automodule:: the_aichemist_codex.backend.domain.ingest.processors.code_processor
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.ingest.processors import CodeProcessor
   from pathlib import Path

   # Initialize the code processor
   processor = CodeProcessor()

   # Process a Python file
   file_path = Path("/path/to/source.py")
   result = await processor.process(file_path)

   # Access processed data
   print(f"Language detected: {result.language}")
   print(f"Number of functions: {len(result.functions)}")
   print(f"Number of classes: {len(result.classes)}")

   # Extract code structure
   for function in result.functions:
       print(f"Function: {function.name}")
       print(f"  Parameters: {', '.join(function.parameters)}")
       print(f"  Documentation: {function.docstring}")

   for cls in result.classes:
       print(f"Class: {cls.name}")
       print(f"  Methods: {', '.join(m.name for m in cls.methods)}")
       print(f"  Properties: {', '.join(cls.properties)}")