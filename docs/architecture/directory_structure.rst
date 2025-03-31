===================
Directory Structure
===================

This document explains the directory structure of The Aichemist Codex, including:

1. Project directory layout
2. Source code organization
3. Data directory structure
4. Testing layout

Project Layout
=============

The Aichemist Codex follows a modern Python project structure with clean architecture principles:

.. code-block:: text

    the_aichemist_codex/              # Root project directory
    ├── .cursor/                      # Cursor editor configuration
    │   └── rules/                    # Cursor AI assistant rules
    ├── .github/                      # GitHub configuration
    ├── .uv_cache/                    # UV package manager cache
    ├── .venv/                        # Virtual environment (not in repo)
    ├── bin/                          # Scripts and binaries
    ├── config/                       # Configuration files
    ├── data/                         # Data files
    ├── deployment/                   # Deployment configurations
    ├── dist/                         # Distribution packages
    ├── docs/                         # Documentation
    │   ├── api/                      # API reference documentation
    │   ├── architecture/             # Architecture documentation
    │   ├── diagrams/                 # Architecture and flow diagrams
    │   ├── guides/                   # User and developer guides
    │   ├── tutorials/                # Tutorials and examples
    │   ├── roadmap/                  # Project roadmap
    │   ├── images/                   # Documentation images
    │   └── _build/                   # Generated documentation
    ├── memory-bank/                  # Project memory bank
    ├── Notes/                        # Development notes
    ├── scripts/                      # Utility scripts
    ├── src/                          # Source code package
    │   └── the_aichemist_codex/      # Main package
    │       ├── ai/                   # AI integration layer
    │       ├── application/          # Application layer
    │       ├── backend/              # Legacy code (to be migrated)
    │       ├── cross_cutting/        # Cross-cutting concerns
    │       ├── domain/               # Domain layer
    │       ├── infrastructure/       # Infrastructure layer
    │       ├── interfaces/           # Interface adapters
    │       ├── plugins/              # Plugin architecture
    │       └── utils/                # Utility modules
    ├── tests/                        # Test suite
    │   ├── unit/                     # Unit tests
    │   ├── integration/              # Integration tests
    │   └── performance/              # Performance tests
    ├── tmp/                          # Temporary files
    ├── .coverage                     # Coverage configuration
    ├── .gitattributes                # Git attributes
    ├── .gitignore                    # Git ignore file
    ├── .markdownlint.json            # Markdown linting rules
    ├── .pre-commit-config.yaml       # Pre-commit hooks
    ├── .python-version               # Python version specifier
    ├── cspell.config.yaml            # Spell checking configuration
    ├── Makefile                      # Development tasks
    ├── pyproject.toml                # Project configuration
    └── uv.lock                       # Dependency lock file

Import Paths
===========

When using or extending The Aichemist Codex, use the full package path for imports:

.. code-block:: python

    # Correct import pattern for domain layer
    from the_aichemist_codex.domain.entities import Document
    from the_aichemist_codex.domain.repositories.interfaces import IDocumentRepository

    # Correct import pattern for application layer
    from the_aichemist_codex.application.commands import CreateDocumentCommand
    from the_aichemist_codex.application.handlers.command_handlers import CreateDocumentHandler

    # Correct import pattern for infrastructure layer
    from the_aichemist_codex.infrastructure.persistence.repositories import DocumentRepository

    # Legacy code imports (will be migrated over time)
    from the_aichemist_codex.backend.core.file_manager import FileManager

    # Incorrect - avoid these patterns
    from domain.entities import Document                # Incomplete import
    from ..repositories import DocumentRepository       # Relative import across package boundaries

Within a subpackage, you can use relative imports for closely related modules:

.. code-block:: python

    # For imports within the same subpackage, relative imports are acceptable
    from .document import Document                        # Same subpackage
    from ..repositories.interfaces import IDocumentRepository  # Parent package reference

For configuration and settings, use the recommended patterns to avoid circular imports:

.. code-block:: python

    # Preferred pattern for accessing data directory
    def get_data_dir():
        import os
        from pathlib import Path

        # Check environment variable first
        env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
        if env_data_dir:
            return Path(env_data_dir)

        # Then check config
        from the_aichemist_codex.infrastructure.config.config_loader import get_config
        config = get_config()
        return Path(config.get("data_dir", "data"))

    # Example usage
    data_dir = get_data_dir()

Source Code Organization
=======================

The source code is organized according to clean architecture principles with domain-driven design:

.. code-block:: text

    src/the_aichemist_codex/         # Main package
    ├── domain/                      # Domain layer
    │   ├── entities/                # Business entities
    │   ├── events/                  # Domain events
    │   ├── exceptions/              # Domain-specific exceptions
    │   ├── models/                  # Domain models
    │   ├── repositories/            # Repository interfaces
    │   │   └── interfaces/          # Interface definitions
    │   ├── services/                # Domain services
    │   │   └── interfaces/          # Service interfaces
    │   └── value_objects/           # Immutable value objects
    │
    ├── application/                 # Application layer
    │   ├── commands/                # Command objects
    │   ├── dto/                     # Data Transfer Objects
    │   ├── exceptions/              # Application-specific exceptions
    │   ├── handlers/                # Command & query handlers
    │   │   ├── command_handlers/    # Command handlers
    │   │   ├── event_handlers/      # Event handlers
    │   │   └── query_handlers/      # Query handlers
    │   ├── mappers/                 # Object mappers
    │   ├── queries/                 # Query objects
    │   ├── services/                # Application services
    │   ├── use_cases/               # Application use cases
    │   └── validators/              # Validators for commands and queries
    │
    ├── infrastructure/              # Infrastructure layer
    │   ├── authentication/          # Authentication infrastructure
    │   ├── cache/                   # Cache implementations
    │   ├── config/                  # Configuration handling
    │   ├── logging/                 # Logging infrastructure
    │   ├── messaging/               # Message handling
    │   │   ├── consumers/           # Message consumers
    │   │   └── publishers/          # Message publishers
    │   ├── persistence/             # Data storage implementations
    │   │   ├── migrations/          # Database migrations
    │   │   └── repositories/        # Repository implementations
    │   ├── search/                  # Search implementations
    │   ├── storage/                 # File storage
    │   ├── telemetry/               # Telemetry infrastructure
    │   └── utils/                   # Infrastructure utilities
    │
    ├── interfaces/                  # Interface adapters
    │   ├── api/                     # API interfaces
    │   │   ├── graphql/             # GraphQL API
    │   │   └── rest/                # REST API
    │   ├── cli/                     # Command-line interfaces
    │   ├── events/                  # Event interfaces
    │   └── stream/                  # Streaming interfaces
    │
    ├── cross_cutting/               # Cross-cutting concerns
    │   ├── caching/                 # Caching mechanisms
    │   ├── error_handling/          # Error handling infrastructure
    │   ├── security/                # Security mechanisms
    │   ├── telemetry/               # Telemetry infrastructure
    │   │   ├── logging/             # Logging components
    │   │   ├── metrics/             # Metrics collection
    │   │   └── tracing/             # Distributed tracing
    │   ├── validation/              # Validation mechanisms
    │   └── workflows/               # Workflow orchestration
    │
    ├── plugins/                     # Plugin architecture
    │   ├── core/                    # Core plugin infrastructure
    │   └── extensions/              # Extension points
    │
    ├── utils/                       # Utility modules
    │   ├── constants/               # Constant definitions
    │   ├── decorators/              # Decorator functions
    │   └── helpers/                 # Helper functions
    │
    ├── ai/                          # AI integration layer
    │   ├── classifiers/             # Classification models
    │   ├── embeddings/              # Vector embeddings
    │   ├── models/                  # AI models
    │   └── transformers/            # Data transformation for AI
    │
    └── backend/                     # Legacy code (to be migrated)
        ├── core/                    # Core functionality
        │   ├── common/              # Common utilities
        │   ├── file_manager/        # File management
        │   ├── file_reader/         # File reading
        │   └── ...                  # Other legacy modules
        └── infrastructure/          # Legacy infrastructure
            ├── config/              # Configuration
            ├── notification/        # Notification system
            └── utils/               # Utilities

Data Directory Structure
=======================

The application maintains a structured data directory for storing user data:

.. code-block:: text

    data_dir/                   # Base data directory
    ├── cache/                  # Cache files
    │   ├── embeddings/         # Embedding vectors
    │   └── thumbnails/         # File thumbnails
    ├── logs/                   # Application logs
    ├── versions/               # File version history
    ├── exports/                # Exported files
    ├── backup/                 # Backup files
    │   ├── rollback_temp/      # Temporary rollback files
    │   └── file_backups/       # File backups
    └── trash/                  # Deleted files

The data directory location can be configured through environment variables:

- ``AICHEMIST_DATA_DIR``: Directly sets the data directory
- ``AICHEMIST_ROOT_DIR``: Sets the project root, data dir will be ``<root>/data``

If not specified, the default locations are:

- Windows: ``%APPDATA%/AichemistCodex``
- macOS/Linux: ``~/.aichemist``

Testing Structure
===============

The testing structure is organized to mirror the clean architecture layers:

.. code-block:: text

    tests/                         # Test root
    ├── conftest.py                # Shared test fixtures
    ├── unit/                      # Unit tests
    │   ├── domain/                # Domain layer tests
    │   │   ├── entities/          # Entity tests
    │   │   ├── repositories/      # Repository interface tests
    │   │   └── services/          # Domain service tests
    │   ├── application/           # Application layer tests
    │   │   ├── commands/          # Command tests
    │   │   ├── handlers/          # Handler tests
    │   │   └── services/          # Application service tests
    │   ├── infrastructure/        # Infrastructure tests
    │   │   ├── persistence/       # Persistence tests
    │   │   └── messaging/         # Messaging tests
    │   └── interfaces/            # Interface tests
    │       ├── api/               # API tests
    │       └── cli/               # CLI tests
    ├── integration/               # Integration tests
    │   ├── application/           # Application integration tests
    │   ├── infrastructure/        # Infrastructure integration tests
    │   └── interfaces/            # Interface integration tests
    └── performance/               # Performance benchmarks
        ├── search/                # Search performance tests
        └── storage/               # Storage performance tests

Documentation Structure
=====================

The documentation is organized into logical sections aligned with the clean architecture:

.. code-block:: text

    docs/                         # Documentation root
    ├── api/                      # API reference
    ├── architecture/             # Architecture documentation
    │   ├── overview.rst          # Architecture overview
    │   ├── domain_layer.rst      # Domain layer documentation
    │   ├── application_layer.rst # Application layer documentation
    │   ├── infrastructure_layer.rst # Infrastructure layer documentation
    │   ├── interfaces_layer.rst  # Interfaces layer documentation
    │   └── diagrams/             # Architecture diagrams
    ├── tutorials/                # Detailed tutorials
    ├── _templates/               # Custom templates
    ├── _static/                  # Static assets
    ├── index.rst                 # Documentation index
    ├── installation.rst          # Installation guide
    ├── usage.rst                 # Usage guide
    ├── development.rst           # Development guide
    ├── environment.rst           # Environment documentation
    ├── configuration.rst         # Configuration documentation
    ├── data_management.rst       # Data management
    ├── cli_reference.rst         # CLI reference
    └── contributing.rst          # Contribution guide
