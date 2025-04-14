.. aichemist_codex documentation master file, created by
   sphinx-quickstart on Fri Feb 28 12:14:10 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to The Aichemist Codex
===================================================

.. image:: /images/logo.png
   :width: 200px
   :alt: The Aichemist Codex Logo
   :align: center

*Intelligent File Management and Knowledge Extraction System*

The Aichemist Codex is an advanced file management and knowledge extraction system
designed to transform how you interact with your files and documents. It leverages
AI and machine learning to provide intelligent file organization, content analysis,
and relationship mapping.

Key Features
-----------

- **Intelligent File Organization**: Automatically organize and sort files based on content
- **Advanced Content Search**: Find files using semantic, fuzzy, or regex search
- **Relationship Mapping**: Discover connections between files in your collection
- **Auto-Tagging**: Automatically generate and apply tags based on file content
- **Dual-Mode Operation**: Run as a package or standalone application
- **Python API**: Use the functionality in your own Python applications

.. note::
   The Aichemist Codex supports both Python 3.10+ and can be run as a standalone application
   or integrated into your own projects. See the :doc:`guides/installation` guide for details.

.. note::
   Detailed component-specific documentation can be found in the ``organized_markdown/``
   directory, which contains markdown files for individual modules and components.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   README

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

   api/domain
   api/domain/entities
   api/domain/value_objects
   api/domain/repositories
   api/domain/services
   api/domain/events
   api/domain/exceptions

   api/application
   api/application/use_cases
   api/application/commands
   api/application/queries
   api/application/dto
   api/application/mappers
   api/application/services
   api/application/validators

   api/infrastructure
   api/infrastructure/persistence
   api/infrastructure/messaging
   api/infrastructure/search
   api/infrastructure/config
   api/infrastructure/security
   api/infrastructure/ai
   api/infrastructure/utils

   api/interfaces
   api/interfaces/api
   api/interfaces/cli
   api/interfaces/events
   api/interfaces/stream
   api/interfaces/presenters

   api/cross_cutting
   api/cross_cutting/caching
   api/cross_cutting/error_handling
   api/cross_cutting/security
   api/cross_cutting/telemetry
   api/cross_cutting/validation
   api/cross_cutting/workflows

   api/backend

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/index
   architecture/overview
   architecture/domain_layer
   architecture/application_layer
   architecture/infrastructure_layer
   architecture/interfaces_layer
   architecture/cross_cutting_concerns
   architecture/directory_structure
   architecture/models
   architecture/tagging_workflow
   architecture/file_relationships

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/index
   roadmap/index
   changelog

Indices and tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
