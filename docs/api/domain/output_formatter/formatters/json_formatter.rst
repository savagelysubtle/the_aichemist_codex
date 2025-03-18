JSON Formatter
=============

Overview
--------

The JSON Formatter converts data into JSON (JavaScript Object Notation) format. It's particularly useful for generating machine-readable outputs that can be easily consumed by other systems or applications.

Implementation
-------------

The JSON Formatter extends the Base Formatter and implements specific logic to convert various data types into valid JSON format, with support for customization options.

Key Features
-----------

* **Standard JSON Output**: Formats data following the JSON specification
* **Pretty Printing**: Configurable indentation for human-readable JSON
* **Circular Reference Handling**: Safely handles circular references in data structures
* **Custom Serialization**: Supports custom serialization for complex objects
* **Encoding Options**: Configurable character encoding and special character handling

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter.formatters.json_formatter import JSONFormatter

   # Initialize the JSON formatter with custom configuration
   json_formatter = JSONFormatter(
       indent=4,
       sort_keys=True,
       ensure_ascii=False
   )

   # Sample data to format
   data = {
       "project": "The AIchemist Codex",
       "version": "1.0.0",
       "features": ["search", "tagging", "relationships"],
       "settings": {
           "debug": False,
           "max_results": 100
       }
   }

   # Format the data
   formatted_json = json_formatter.format(data)

   # Use the formatted JSON
   print(formatted_json)

   # Or save to a file
   with open("output.json", "w") as f:
       f.write(formatted_json)

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatters.json_formatter
   :members:
   :undoc-members:
   :show-inheritance: