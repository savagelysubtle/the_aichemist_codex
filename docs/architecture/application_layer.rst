=================
Application Layer
=================

The application layer orchestrates domain objects to fulfill user requirements and implements application-specific business rules.

Overview
========

The application layer sits between the domain layer and external interfaces. It coordinates the interactions between domain objects and implements use cases that represent the system's behavior from the user's perspective. This layer depends only on the domain layer and is independent of external frameworks and infrastructure concerns.

Components
==========

Use Cases
--------

Use cases represent specific actions that users can perform with the system:

- **CreateDocument**: Create a new document in the system
- **SearchDocuments**: Search for documents using various criteria
- **TagDocument**: Add tags to a document
- **ManageVersions**: Create and manage document versions
- **AnalyzeRelationships**: Analyze relationships between documents

Example use case:

.. code-block:: python

    class CreateDocumentUseCase:
        def __init__(
            self,
            document_repository: IDocumentRepository,
            event_publisher: IEventPublisher
        ):
            self.document_repository = document_repository
            self.event_publisher = event_publisher

        def execute(self, command: CreateDocumentCommand) -> UUID:
            """Create a new document based on the provided command."""
            # Create domain entity
            document = Document(
                document_id=uuid4(),
                path=command.path,
                metadata=command.metadata
            )

            # Use repository to persist
            self.document_repository.add(document)

            # Publish domain event
            self.event_publisher.publish(DocumentCreated(
                document_id=document.id,
                path=document.path,
                timestamp=datetime.now()
            ))

            return document.id

Commands and Queries
------------------

Following the Command Query Responsibility Segregation (CQRS) pattern:

Commands:
- **CreateDocumentCommand**: Command to create a document
- **UpdateMetadataCommand**: Command to update document metadata
- **AddTagCommand**: Command to add a tag to a document
- **CreateVersionCommand**: Command to create a new version

Queries:
- **GetDocumentByIdQuery**: Query to retrieve a document by ID
- **SearchDocumentsByTagQuery**: Query to search documents by tag
- **GetDocumentHistoryQuery**: Query to retrieve document version history
- **FindRelatedDocumentsQuery**: Query to find documents related to a given document

Example command:

.. code-block:: python

    @dataclass
    class CreateDocumentCommand:
        path: Path
        content_type: str
        metadata: Dict[str, Any]
        tags: List[str] = field(default_factory=list)

Example query:

.. code-block:: python

    @dataclass
    class SearchDocumentsByTagQuery:
        tag_names: List[str]
        match_all: bool = False
        limit: int = 100
        offset: int = 0

Handlers
-------

Handlers process commands and queries:

Command Handlers:
- **CreateDocumentHandler**: Handles document creation
- **UpdateMetadataHandler**: Handles metadata updates
- **AddTagHandler**: Handles adding tags to documents

Query Handlers:
- **GetDocumentByIdHandler**: Retrieves documents by ID
- **SearchDocumentsByTagHandler**: Searches documents by tags
- **GetDocumentHistoryHandler**: Retrieves document history

Example handler:

.. code-block:: python

    class CreateDocumentHandler:
        def __init__(self, document_repository: IDocumentRepository, event_bus: IEventBus):
            self.document_repository = document_repository
            self.event_bus = event_bus

        def handle(self, command: CreateDocumentCommand) -> UUID:
            document = Document(
                document_id=uuid4(),
                path=command.path,
                metadata={
                    "content_type": command.content_type,
                    **command.metadata
                }
            )

            # Add tags if provided
            for tag_name in command.tags:
                document.add_tag(Tag(name=tag_name))

            # Save document
            self.document_repository.add(document)

            # Publish event
            self.event_bus.publish(DocumentCreated(
                document_id=document.id,
                path=document.path,
                timestamp=datetime.now()
            ))

            return document.id

DTOs (Data Transfer Objects)
--------------------------

DTOs facilitate data transfer between the application layer and interfaces:

- **DocumentDto**: Represents a document for external consumption
- **TagDto**: Represents a tag for external consumption
- **RelationshipDto**: Represents a relationship for external consumption
- **SearchResultDto**: Represents search results

Example DTO:

.. code-block:: python

    @dataclass
    class DocumentDto:
        id: str
        path: str
        content_type: str
        metadata: Dict[str, Any]
        tags: List[str]
        created_at: datetime
        updated_at: datetime
        version_count: int

Mappers
------

Mappers transform between domain entities and DTOs:

- **DocumentMapper**: Maps between Document entities and DocumentDtos
- **TagMapper**: Maps between Tag entities and TagDtos
- **RelationshipMapper**: Maps between Relationship entities and RelationshipDtos

Example mapper:

.. code-block:: python

    class DocumentMapper:
        @staticmethod
        def to_dto(document: Document) -> DocumentDto:
            return DocumentDto(
                id=str(document.id),
                path=str(document.path),
                content_type=document.metadata.get("content_type", "unknown"),
                metadata=document.metadata,
                tags=[tag.name for tag in document.tags],
                created_at=document.created_at,
                updated_at=document.updated_at,
                version_count=len(document.versions)
            )

        @staticmethod
        def to_entity(dto: DocumentDto) -> Document:
            # Create document entity from DTO
            document = Document(
                document_id=UUID(dto.id) if isinstance(dto.id, str) else dto.id,
                path=Path(dto.path) if isinstance(dto.path, str) else dto.path,
                metadata=dto.metadata
            )

            # Add tags
            for tag_name in dto.tags:
                document.add_tag(Tag(name=tag_name))

            return document

Application Services
------------------

Application services coordinate complex operations that may involve multiple domain entities:

- **DocumentService**: Manages document operations
- **SearchService**: Coordinates search operations
- **TaggingService**: Manages the tagging process
- **RelationshipService**: Coordinates relationship operations

Example application service:

.. code-block:: python

    class DocumentService:
        def __init__(
            self,
            document_repository: IDocumentRepository,
            tag_repository: ITagRepository,
            event_bus: IEventBus
        ):
            self.document_repository = document_repository
            self.tag_repository = tag_repository
            self.event_bus = event_bus

        def create_document(self, command: CreateDocumentCommand) -> UUID:
            """Create a new document with the given details."""
            # Implementation using repositories and domain objects

        def update_document(self, command: UpdateDocumentCommand) -> None:
            """Update an existing document."""
            # Implementation using repositories and domain objects

        def tag_document(self, command: TagDocumentCommand) -> None:
            """Add tags to a document."""
            # Implementation using repositories and domain objects

        def get_document(self, query: GetDocumentQuery) -> Optional[DocumentDto]:
            """Get a document by its ID."""
            # Implementation using repositories and domain objects

Event Handlers
------------

Event handlers respond to domain events:

- **DocumentCreatedHandler**: Responds to document creation events
- **TagAddedHandler**: Responds to tag addition events
- **RelationshipEstablishedHandler**: Responds to relationship creation events

Example event handler:

.. code-block:: python

    class DocumentCreatedHandler:
        def __init__(self, search_index_service: ISearchIndexService):
            self.search_index_service = search_index_service

        def handle(self, event: DocumentCreated) -> None:
            """Handle document created event by indexing the document."""
            self.search_index_service.index_document(event.document_id)

Validators
---------

Validators ensure that commands and queries are valid before processing:

- **CreateDocumentValidator**: Validates document creation commands
- **UpdateMetadataValidator**: Validates metadata update commands
- **SearchQueryValidator**: Validates search queries

Example validator:

.. code-block:: python

    class CreateDocumentValidator:
        def validate(self, command: CreateDocumentCommand) -> List[str]:
            errors = []

            if not command.path:
                errors.append("Path is required")

            if not command.path.exists():
                errors.append(f"Path {command.path} does not exist")

            if not command.content_type:
                errors.append("Content type is required")

            return errors

Design Patterns in the Application Layer
======================================

The application layer implements several design patterns:

- **Command Pattern**: Encapsulate requests as objects
- **CQRS Pattern**: Separate commands (write) from queries (read)
- **Mediator Pattern**: Coordinate interaction between domain objects
- **Facade Pattern**: Provide a simplified interface to complex subsystems
- **DTO Pattern**: Transfer data between layers
- **Validator Pattern**: Validate input before processing

Application Layer Rules
=====================

1. Depends only on the domain layer
2. Contains use cases that orchestrate domain objects
3. Transforms between external DTOs and domain objects
4. Implements application-specific business rules
5. Manages transaction boundaries and unit of work
6. Publishes and handles domain events
