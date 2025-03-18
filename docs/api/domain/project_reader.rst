Project Reader Module
=====================

The Project Reader Module provides functionality for reading and analyzing project structures. It offers capabilities for analyzing codebases, generating project summaries, and converting notebooks to scripts.

Core Components
--------------

- **Project Analysis**: Code analysis for extracting information about project structure and functions
- **Project Summarization**: Generation of project summaries in markdown or JSON format
- **Notebook Conversion**: Conversion of Jupyter notebooks to Python scripts
- **Token Estimation**: Functionality to estimate token counts for text processing

Implementation Details
--------------------

The Project Reader module uses asynchronous I/O operations for efficient file processing and implements the core ProjectReader interface defined in the system. It handles Python code parsing, Jupyter notebook conversion, and generation of structured project summaries.

.. automodule:: the_aichemist_codex.backend.domain.project_reader
   :members:
   :undoc-members:
   :show-inheritance:
   :imported-members:

Project Reader Implementation
----------------------------

The ProjectReaderImpl class is the primary implementation of the ProjectReader interface, providing methods for analyzing project structure, summarizing projects, and converting notebooks to Python code.

.. automodule:: the_aichemist_codex.backend.domain.project_reader.project_reader
   :members:
   :undoc-members:
   :show-inheritance:

Project Reader Models
-------------------

Data models and helper classes used by the project reader system, including Version and Tag classes.

.. automodule:: the_aichemist_codex.backend.domain.project_reader.models
   :members:
   :undoc-members:
   :show-inheritance:
