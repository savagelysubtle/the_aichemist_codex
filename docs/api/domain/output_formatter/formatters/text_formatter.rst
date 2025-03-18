Text Formatter
=============

Overview
--------

The Text Formatter is responsible for converting data into plain text format. It provides a simple and readable output format suitable for console display or text files.

Implementation
-------------

The Text Formatter extends the Base Formatter and implements specific logic to convert various data types into well-formatted plain text.

Key Features
-----------

* **Simple Text Output**: Formats data as human-readable plain text
* **Custom Templates**: Supports customizable text templates
* **Indentation Control**: Configurable indentation levels for hierarchical data
* **Line Width Control**: Handles text wrapping to ensure output fits within specified line widths
* **Special Character Handling**: Properly escapes and handles special characters

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter.formatters.text_formatter import TextFormatter

   # Initialize the text formatter with custom configuration
   text_formatter = TextFormatter(
       indent_size=2,
       max_line_width=80,
       include_metadata=True
   )

   # Sample data to format
   data = {
       "title": "Project Report",
       "items": [
           {"name": "Task 1", "status": "Completed"},
           {"name": "Task 2", "status": "In Progress"}
       ]
   }

   # Format the data
   formatted_text = text_formatter.format(data)

   # Print or save the formatted text
   print(formatted_text)

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatters.text_formatter
   :members:
   :undoc-members:
   :show-inheritance: