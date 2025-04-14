API Development
==============

This guide provides information on extending and customizing the Python API for The AIchemist Codex.

Overview
--------

The AIchemist Codex provides a comprehensive Python API that allows developers to integrate its functionality into their own applications. The API follows the clean architecture principles and is organized into layers.

Architecture
-----------

The API follows the clean architecture principles of the main application:

* **Domain Layer**: Core business entities, value objects, and business rules
* **Application Layer**: Use cases, services, and application-specific logic
* **Infrastructure Layer**: Implementation details, external services, and data access
* **Interfaces Layer**: API endpoints, controllers, and presenters

API Structure
------------

The main API entry points are organized by functionality:

* **File Management**: APIs for file operations, organization, and metadata
* **Search**: APIs for semantic, fuzzy, and regex search
* **Tagging**: APIs for automatic and manual tagging
* **Relationships**: APIs for managing file relationships
* **Configuration**: APIs for system configuration

Extending the API
----------------

To extend the API with new functionality:

1. Identify the appropriate layer for your extension
2. Implement the required interfaces and classes
3. Register your extension with the appropriate registry
4. Update the API documentation

Example: Adding a New File Analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from the_aichemist_codex.domain.interfaces import FileAnalyzer
    from the_aichemist_codex.domain.entities import FileMetadata

    class CustomFileAnalyzer(FileAnalyzer):
        """Custom file analyzer that extracts specific metadata."""

        def analyze(self, file_path):
            """Analyze a file and extract metadata.

            Args:
                file_path: Path to the file to analyze

            Returns:
                FileMetadata: Extracted metadata
            """
            # Implementation here
            metadata = FileMetadata(
                file_path=file_path,
                custom_field="Custom value"
            )
            return metadata

    # Register the analyzer
    from the_aichemist_codex.infrastructure.registry import analyzer_registry
    analyzer_registry.register("custom", CustomFileAnalyzer())

Testing API Extensions
---------------------

API extensions should be thoroughly tested:

.. code-block:: python

    import pytest
    from the_aichemist_codex.domain.entities import FileMetadata
    from custom_extension import CustomFileAnalyzer

    def test_custom_analyzer():
        analyzer = CustomFileAnalyzer()
        metadata = analyzer.analyze("path/to/test/file")

        assert isinstance(metadata, FileMetadata)
        assert metadata.file_path == "path/to/test/file"
        assert metadata.custom_field == "Custom value"

API Documentation
----------------

When extending the API, update the documentation:

1. Add docstrings to all classes and methods
2. Update the API reference documentation
3. Add examples and tutorials for the new functionality

Best Practices
-------------

1. **Interface Segregation**: Create focused interfaces with specific responsibilities
2. **Dependency Inversion**: Depend on abstractions, not concrete implementations
3. **Single Responsibility**: Each class should have a single responsibility
4. **Open/Closed**: Extensions should be open for extension but closed for modification
5. **Error Handling**: Use appropriate error handling and exceptions

Advanced Topics
--------------

Dependency Injection
~~~~~~~~~~~~~~~~~~~

Use dependency injection to manage dependencies:

.. code-block:: python

    class FileService:
        def __init__(self, file_repository, file_analyzer):
            self.file_repository = file_repository
            self.file_analyzer = file_analyzer

        def process_file(self, file_path):
            metadata = self.file_analyzer.analyze(file_path)
            self.file_repository.save_metadata(file_path, metadata)
            return metadata

Event-Driven Architecture
~~~~~~~~~~~~~~~~~~~~~~~~

Use events for loose coupling between components:

.. code-block:: python

    from the_aichemist_codex.domain.events import FileProcessedEvent
    from the_aichemist_codex.infrastructure.event_bus import event_bus

    class FileProcessor:
        def process_file(self, file_path):
            # Process the file
            result = self._do_processing(file_path)

            # Publish an event
            event = FileProcessedEvent(file_path=file_path, result=result)
            event_bus.publish(event)

            return result

    # Event subscriber
    @event_bus.subscribe(FileProcessedEvent)
    def handle_file_processed(event):
        print(f"File processed: {event.file_path}")
        # Additional processing here

API Versioning
~~~~~~~~~~~~~

Implement API versioning to maintain backward compatibility:

.. code-block:: python

    class APIv1:
        def process_file(self, file_path):
            # v1 implementation
            pass

    class APIv2:
        def process_file(self, file_path, options=None):
            # v2 implementation with additional options
            if options is None:
                options = {}
            # Enhanced processing
            pass

    # Factory function to get the appropriate API version
    def get_api(version="v2"):
        if version == "v1":
            return APIv1()
        elif version == "v2":
            return APIv2()
        else:
            raise ValueError(f"Unsupported API version: {version}")
