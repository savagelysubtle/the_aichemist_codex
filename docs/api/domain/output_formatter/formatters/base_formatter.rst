Base Formatter
=============

Overview
--------

The Base Formatter serves as the foundation for all output formatters in The AIchemist Codex. It defines the common interface and functionality that all formatters must implement to ensure consistent output generation.

Implementation
-------------

The Base Formatter is implemented as an abstract base class that establishes the contract for formatting data in various output formats.

Key Features
-----------

* **Standardized Interface**: Provides a consistent API for all formatters
* **Abstract Methods**: Defines required methods that all formatters must implement
* **Configuration Management**: Handles common configuration options for formatters
* **Data Validation**: Provides basic validation of input data before formatting

Usage Example
------------

While you cannot instantiate the Base Formatter directly (as it's an abstract class), all concrete formatters follow this pattern:

.. code-block:: python

   from the_aichemist_codex.backend.domain.output_formatter.formatters.base_formatter import BaseFormatter

   class CustomFormatter(BaseFormatter):
       def __init__(self, config=None):
           super().__init__(config)
           # Custom initialization code

       def format(self, data):
           # Implement formatting logic
           return formatted_output

.. automodule:: the_aichemist_codex.backend.domain.output_formatter.formatters.base_formatter
   :members:
   :undoc-members:
   :show-inheritance: