Domain Modules
=============

This section contains documentation for all the domain modules in the new domain-driven architecture of The AIchemist Codex.

.. toctree::
   :maxdepth: 2
   :caption: Domain Modules:

   core/index
   project_reader/index
   ingest/index
   search/index
   output_formatter/index
   relationships/index
   tagging/index
   metadata/index
   notification/index
   rollback/index

Core Concepts
------------

The domain-driven architecture of The AIchemist Codex is organized around distinct business domains, each encapsulating a specific area of functionality. Each domain consists of:

1. **Domain Models**: Data structures representing concepts in the domain
2. **Domain Services**: Business logic and operations specific to the domain
3. **Domain Interfaces**: Contracts that define how other domains interact with this domain
4. **Domain Events**: Events that can be raised by the domain and handled by subscribers

Architecture Benefits
-------------------

The domain-driven architecture provides several benefits:

* **Modularity**: Each domain is a self-contained module that can be developed and tested independently
* **Maintainability**: Changes to one domain have minimal impact on other domains
* **Scalability**: Individual domains can be scaled independently based on demand
* **Testability**: Clear domain boundaries make it easier to write focused tests

For more information about the architecture and design principles, see the :doc:`../architecture` documentation.