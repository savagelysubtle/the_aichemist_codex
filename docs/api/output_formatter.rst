Output Formatter (Legacy)
======================

.. note::
   This is a legacy documentation page. Please refer to the updated :doc:`domain/output_formatter`
   documentation for the current implementation.

The Output Formatter module provides functionality for formatting data into different output formats.

Current Implementation
--------------------

The Output Formatter system has been migrated to the new domain-driven architecture. Please see:

* :doc:`domain/output_formatter` - Current output formatter module documentation
* :doc:`domain/output_formatter/formatters/index` - Available formatter implementations

.. raw:: html

   <meta http-equiv="refresh" content="0; url=domain/output_formatter.html">

.. automodule:: backend.src.output_formatter
   :members:
   :undoc-members:
   :show-inheritance:

Formatter
--------

The base Formatter class defines the interface for all output formatters.

.. automodule:: backend.src.output_formatter.formatter
   :members:
   :undoc-members:
   :show-inheritance:

Text Formatter
------------

The TextFormatter presents results in plain text format.

.. automodule:: backend.src.output_formatter.text
   :members:
   :undoc-members:
   :show-inheritance:

JSON Formatter
-----------

The JSONFormatter outputs results in JSON format for machine-readable output.

.. automodule:: backend.src.output_formatter.json
   :members:
   :undoc-members:
   :show-inheritance:

HTML Formatter
-----------

The HTMLFormatter creates HTML representations of results.

.. automodule:: backend.src.output_formatter.html
   :members:
   :undoc-members:
   :show-inheritance:

Markdown Formatter
---------------

The MarkdownFormatter outputs results in Markdown format.

.. automodule:: backend.src.output_formatter.markdown
   :members:
   :undoc-members:
   :show-inheritance:

CSV Formatter
----------

The CSVFormatter outputs tabular data in CSV format.

.. automodule:: backend.src.output_formatter.csv
   :members:
   :undoc-members:
   :show-inheritance:

Terminal Formatter
---------------

The TerminalFormatter creates rich, colorful terminal output.

.. automodule:: backend.src.output_formatter.terminal
   :members:
   :undoc-members:
   :show-inheritance:
