Formatter Manager
================

The Formatter Manager is responsible for managing and coordinating the different output formatters.

Overview
--------

The Formatter Manager:

* Registers and manages formatter implementations
* Routes formatting requests to the appropriate formatter
* Provides a unified formatting interface
* Supports dynamic formatter selection

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatter_manager
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* **Multiple Format Support**: Manages formatters for different output formats (text, JSON, HTML, Markdown)
* **Dynamic Registration**: Supports dynamic registration of new formatters
* **Format Selection**: Automatically selects appropriate formatter based on format type
* **Default Formatting**: Provides sensible defaults for common use cases
* **Extensibility**: Easy to extend with new formatter implementations

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter import FormatterManager
   from the_aichemist_codex.backend.domain.search import SearchResult

   # Initialize the formatter manager
   formatter = FormatterManager()

   # Create some search results
   results = [
       SearchResult(document_id="doc1", score=0.95, snippet="Sample text about machine learning"),
       SearchResult(document_id="doc2", score=0.85, snippet="Another document about AI")
   ]

   # Format as JSON
   json_output = formatter.format(results, format_type="json", pretty=True)

   # Format as HTML
   html_output = formatter.format(results, format_type="html", include_css=True)

   # Format as Markdown
   markdown_output = formatter.format(results, format_type="markdown")