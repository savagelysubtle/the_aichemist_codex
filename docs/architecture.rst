==========================
The AIchemist Codex Architecture
==========================

This document describes the architecture of The AIchemist Codex project.

Overview
--------

The AIchemist Codex follows a **domain-driven design** with a **layered architecture** approach. The application uses the **Registry pattern** to prevent circular dependencies and facilitate dependency injection.

.. image:: /images/architecture_diagram.png
   :width: 800px
   :alt: The AIchemist Codex Architecture Diagram
   :align: center

Layered Architecture
-------------------

The codebase is organized into the following layers:

1. **Core Layer**: Contains interfaces, models, constants, and exceptions
2. **Infrastructure Layer**: Provides base implementations and utilities
3. **Domain Layer**: Contains business logic and implementations
4. **Service Layer**: Composes domain components into services
5. **Application Layer**: Entry points for the application (CLI, API)

Core Layer
^^^^^^^^^^

The core layer defines the contracts, models, and exceptions used across the application. This layer should not depend on any other layer.

Key components:

- ``interfaces.py``: Contains interfaces for all primary services
- ``models.py``: Contains data models and value objects
- ``constants.py``: Contains application constants
- ``exceptions.py``: Contains application-specific exceptions

Infrastructure Layer
^^^^^^^^^^^^^^^^^^^^

The infrastructure layer provides foundational implementations and utilities:

- ``io/``: I/O operations and file system access
- ``paths/``: Path resolution and validation
- ``config/``: Configuration management
- ``persistence/``: Data storage mechanisms
- ``security/``: Security utilities
- ``file/``: Low-level file operations

Domain Layer
^^^^^^^^^^^

The domain layer contains the business logic implementations organized by domain:

- ``file_reader/``: Reading files of various formats
- ``file_writer/``: Writing files of various formats
- ``file_manager/``: High-level file operations
- ``search/``: Search functionality
- ``tagging/``: Auto-tagging and tag management
- ``metadata/``: Metadata extraction
- ``relationships/``: File relationship mapping
- ``notification/``: Notification system
- ``project_reader/``: Project directory reading
- ``ingest/``: Data ingestion
- ``output_formatter/``: Output formatting
- ``rollback/``: Rollback functionality

Service Layer
^^^^^^^^^^^

Services compose domain components to provide higher-level functionality:

- ``processing_service``: Coordinates file processing
- ``analysis_service``: Coordinates analysis operations
- ``organization_service``: Coordinates organization operations

Application Layer
^^^^^^^^^^^^^^

Entry points to the application:

- ``cli/``: Command-line interface
- ``api/``: HTTP API and web interfaces
- ``__main__.py``: Direct module execution entry point

Import Strategy
---------------

The AIchemist Codex follows specific import strategies to maintain clean architecture and prevent circular dependencies:

1. **Core Layer Imports**: Use absolute imports for core components:

   .. code-block:: python

       # Importing core constants
       from the_aichemist_codex.backend.core.constants.constants import MAX_FILE_SIZE_MB

       # Importing core interfaces
       from the_aichemist_codex.backend.core.interfaces import FileReader

   This approach ensures core components are always accessible regardless of where the code is executed from.

2. **Related Module Imports**: For closely related modules within the same package, relative imports may be used:

   .. code-block:: python

       # Importing from a sibling module
       from .file_validation import validate_path

       # Importing from a parent package
       from ..utils.formatters import format_size

   Relative imports should be used sparingly and only for modules unlikely to be reorganized.

3. **Service Dependencies**: Use the Registry pattern for service dependencies to prevent circular imports:

   .. code-block:: python

       # Get registry instance
       from the_aichemist_codex.registry import Registry
       registry = Registry.get_instance()

       # Access services through registry
       file_reader = registry.file_reader
       file_writer = registry.file_writer

   The Registry pattern is especially important for domain and service layer components that might have complex dependency relationships.

4. **Development Setup**: During development, install the package in editable mode:

   .. code-block:: bash

       pip install -e .

   This ensures absolute imports work correctly while allowing changes to be immediately reflected.

Registry Pattern
---------------

The AIchemist Codex uses the Registry pattern to manage dependencies and prevent circular imports:

.. code-block:: python

    # Get the registry instance
    registry = Registry.get_instance()

    # Get a service from the registry
    file_reader = registry.file_reader

    # Use the service
    content = file_reader.read_text("path/to/file.txt")

This pattern allows:

1. **Lazy loading**: Components are only created when needed
2. **Dependency injection**: Dependencies are provided rather than created
3. **Circular dependency avoidance**: Components interact through the registry
4. **Testability**: Components can be easily mocked for testing

Bootstrap Process
----------------

The application is initialized via the bootstrap process:

1. Registry is initialized
2. Base services are registered
3. Configuration is loaded
4. Core components are initialized
5. Application is ready to process commands

Example Flow
-----------

A typical workflow through the architecture looks like this:

1. User invokes a command through CLI or API
2. Application layer receives the command
3. Service layer coordinates the required operations
4. Domain layer implements the business logic
5. Infrastructure layer handles low-level operations
6. Results flow back up through the layers
7. Output is formatted and returned to the user

Development Guidelines
---------------------

When developing for The AIchemist Codex:

1. **Respect layer boundaries**: Higher layers can use lower layers, but not vice versa
2. **Implement against interfaces**: All implementations should fulfill a core interface
3. **Use the registry**: Access components through the registry, not direct imports
4. **Follow domain separation**: Keep components in their appropriate domain directories
5. **Avoid circular imports**: Structure code to prevent circular dependencies
6. **Use absolute imports for core components**: Make dependencies explicit and reliable
7. **Use the Registry pattern for service dependencies**: Prevent circular imports between services