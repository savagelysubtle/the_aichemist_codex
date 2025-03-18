Tagging (Legacy)
==============

.. note::
   This is a legacy documentation page. Please refer to the updated :doc:`domain/tagging`
   documentation for the current implementation.

The Tagging module provides functionality for organizing and categorizing files using tags.

Current Implementation
--------------------

The Tagging system has been migrated to the new domain-driven architecture. Please see:

* :doc:`domain/tagging` - Current tagging module documentation

.. raw:: html

   <meta http-equiv="refresh" content="0; url=domain/tagging.html">

.. automodule:: backend.src.tagging
   :members:
   :undoc-members:
   :show-inheritance:

TagManager
----------

The TagManager is responsible for creating, retrieving, updating, and deleting tags and their associations with files.

.. automodule:: backend.src.tagging.manager
   :members:
   :undoc-members:
   :show-inheritance:

TagSuggester
------------

The TagSuggester provides automated tag suggestions based on file content, metadata, and similarity to previously tagged files.

.. automodule:: backend.src.tagging.suggester
   :members:
   :undoc-members:
   :show-inheritance:

TagClassifier
------------

The TagClassifier uses machine learning to classify files and suggest tags based on their content.

.. automodule:: backend.src.tagging.classifier
   :members:
   :undoc-members:
   :show-inheritance:

Tag Hierarchy
-------------

The TagHierarchy manages hierarchical relationships between tags.

.. automodule:: backend.src.tagging.hierarchy
   :members:
   :undoc-members:
   :show-inheritance:

Tag Schema
----------

The TagSchema manages the database schema for tag storage.

.. automodule:: backend.src.tagging.schema
   :members:
   :undoc-members:
   :show-inheritance:
