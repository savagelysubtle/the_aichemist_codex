Base Provider
=============

Overview
--------

The Base Provider serves as the foundation for all search providers in The AIchemist Codex. It defines the common interface and functionality that all search providers must implement.

Implementation
-------------

The Base Provider is implemented as an abstract base class, providing a standardized way to search content regardless of the underlying search method.

Key Features
-----------

* **Standardized Interface**: Provides a consistent API for all search providers
* **Abstract Methods**: Defines required methods that all providers must implement
* **Configuration Management**: Handles common configuration options for search providers
* **Result Formatting**: Provides standard result formatting capabilities

Usage Example
------------

While you cannot instantiate the Base Provider directly (as it's an abstract class), all concrete providers follow this pattern:

.. code-block:: python

   from the_aichemist_codex.backend.domain.search.providers.base_provider import BaseSearchProvider

   class CustomSearchProvider(BaseSearchProvider):
       def __init__(self, config=None):
           super().__init__(config)
           # Custom initialization code

       def search(self, query, **kwargs):
           # Implement search logic
           return search_results

.. automodule:: the_aichemist_codex.backend.domain.search.providers.base_provider
   :members:
   :undoc-members:
   :show-inheritance: