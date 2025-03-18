Markdown Formatter
=================

Overview
--------

The Markdown Formatter converts data into Markdown format, a lightweight markup language with plain text formatting syntax. It's ideal for generating documentation, README files, or content for platforms that support Markdown rendering.

Implementation
-------------

The Markdown Formatter extends the Base Formatter and implements specific logic to convert various data types into well-structured Markdown syntax.

Key Features
-----------

* **Standard Markdown Syntax**: Follows CommonMark or GitHub Flavored Markdown specifications
* **Rich Text Elements**: Supports headings, lists, tables, code blocks, and other Markdown elements
* **Link Generation**: Automatically formats URLs and references as Markdown links
* **Image Support**: Converts image data to proper Markdown image syntax
* **Table of Contents**: Optionally generates a table of contents for structured documents
* **Code Highlighting**: Supports syntax highlighting in code blocks

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter.formatters.markdown_formatter import MarkdownFormatter

   # Initialize the Markdown formatter with custom configuration
   md_formatter = MarkdownFormatter(
       flavor="github",
       include_toc=True,
       code_highlighting=True
   )

   # Sample data to format
   data = {
       "title": "Project Documentation",
       "sections": [
           {
               "heading": "Installation",
               "content": "Run `pip install aichemist-codex` to install the package.",
               "code": "pip install aichemist-codex"
           },
           {
               "heading": "Usage",
               "content": "Import and initialize the library as shown below.",
               "code": "from aichemist_codex import AIchemist\n\nai = AIchemist()"
           }
       ]
   }

   # Format the data
   formatted_markdown = md_formatter.format(data)

   # Save to a Markdown file
   with open("README.md", "w") as f:
       f.write(formatted_markdown)

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatters.markdown_formatter
   :members:
   :undoc-members:
   :show-inheritance: