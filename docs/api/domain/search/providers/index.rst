Search Providers
===============

The Search Providers module contains various search provider implementations for different search strategies.

.. toctree::
   :maxdepth: 2

   base_provider
   regex_provider
   text_provider
   vector_provider

Base Provider
------------

The BaseProvider class defines the interface that all search providers must implement.

.. automodule:: the_aichemist_codex.backend.domain.search.providers.base_provider
   :members:
   :undoc-members:
   :show-inheritance:

Regex Provider
------------

The RegexProvider implements search functionality using regular expressions.

.. automodule:: the_aichemist_codex.backend.domain.search.providers.regex_provider
   :members:
   :undoc-members:
   :show-inheritance:

Text Provider
------------

The TextProvider implements text-based search functionality.

.. automodule:: the_aichemist_codex.backend.domain.search.providers.text_provider
   :members:
   :undoc-members:
   :show-inheritance:

Vector Provider
-------------

The VectorProvider implements semantic search using vector embeddings.

.. automodule:: the_aichemist_codex.backend.domain.search.providers.vector_provider
   :members:
   :undoc-members:
   :show-inheritance: