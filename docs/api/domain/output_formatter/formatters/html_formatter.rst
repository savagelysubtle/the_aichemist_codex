HTML Formatter
=============

Overview
--------

The HTML Formatter converts data into HTML (HyperText Markup Language) format. It's designed for generating web-friendly output that can be displayed in browsers or embedded in web applications.

Implementation
-------------

The HTML Formatter extends the Base Formatter and implements specific logic to convert various data types into valid HTML markup, with support for styling and customization.

Key Features
-----------

* **Structured HTML Output**: Formats data as properly structured HTML
* **CSS Integration**: Supports custom CSS styling for formatted output
* **Template Support**: Uses customizable HTML templates
* **Table Formatting**: Automatically formats tabular data into HTML tables
* **Sanitization**: Properly escapes HTML special characters to prevent injection vulnerabilities
* **Responsive Design**: Generates responsive HTML that works across different device sizes

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter.formatters.html_formatter import HTMLFormatter

   # Initialize the HTML formatter with custom configuration
   html_formatter = HTMLFormatter(
       custom_css="path/to/styles.css",
       include_bootstrap=True,
       responsive=True
   )

   # Sample data to format
   data = {
       "title": "Search Results",
       "results": [
           {"name": "Document 1", "relevance": 0.95, "path": "/docs/doc1.pdf"},
           {"name": "Document 2", "relevance": 0.87, "path": "/docs/doc2.pdf"},
           {"name": "Document 3", "relevance": 0.72, "path": "/docs/doc3.pdf"}
       ]
   }

   # Format the data
   formatted_html = html_formatter.format(data)

   # Save to an HTML file
   with open("search_results.html", "w") as f:
       f.write(formatted_html)

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatters.html_formatter
   :members:
   :undoc-members:
   :show-inheritance: