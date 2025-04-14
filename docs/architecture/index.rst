============
Architecture
============

The Aichemist Codex follows a clean architecture approach, separating concerns into distinct layers:

* **Domain Layer**: Core business logic and entities
* **Application Layer**: Orchestrating domain objects to perform tasks
* **Infrastructure Layer**: Implementing interfaces defined in inner layers
* **Interfaces Layer**: Providing ways for users and external systems to interact with the application
* **Cross-Cutting Concerns**: Handling concerns that span multiple layers

.. toctree::
   :maxdepth: 1
   :caption: Overview

   overview
   directory_structure
   models

.. toctree::
   :maxdepth: 1
   :caption: Clean Architecture Layers

   domain_layer
   application_layer
   infrastructure_layer
   interfaces_layer
   cross_cutting_concerns

.. toctree::
   :maxdepth: 1
   :caption: Key Workflows

   tagging_workflow
   file_relationships

.. toctree::
   :maxdepth: 1
   :caption: Legacy Components

   analyzers
   authentication
   change_detector
   clustering
   detectors
   cli
   components
   dashboards
   detector
   directory_monitor
   directory_organizer
   embeddings
   encryption
   engines
   exporters
   extractors
   graph
   helpers
   indexers
   permissions
   plugins
   profilers
   project_reader
   query_parser
   recommendation
   secure_config
   settings
   snapshot
   transaction
   validation
   validators
