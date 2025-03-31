=============
Domain Layer
=============

The domain layer is the core of the clean architecture and contains business logic, rules, and domain models without any dependencies on external frameworks or technologies.

Overview
========

The domain layer is the heart of The Aichemist Codex, representing the essential business concepts and rules. It's independent of any specific technology or framework, meaning it can be tested in isolation and doesn't change when external technologies change.

Components
==========

Entities
-------

Domain entities are business objects with unique identity and lifecycle:

- **Document**: Represents a file with metadata and content
- **Tag**: Represents a tag for categorizing documents
- **Relationship**: Represents a connection between two documents
- **Version**: Represents a specific version of a document

Example entity:

.. code-block:: python

    class Document:
        def __init__(self, document_id: UUID, path: Path, metadata: Dict[str, Any]):
            self.id = document_id
            self.path = path
            self.metadata = metadata
            self.tags = []
            self.relationships = []
            self.versions = []

        def add_tag(self, tag: Tag) -> None:
            if tag not in self.tags:
                self.tags.append(tag)

        def create_version(self) -> Version:
            version = Version(self)
            self.versions.append(version)
            return version

Value Objects
-----------

Value objects are immutable objects defined by their attributes rather than identity:

- **FileType**: Represents the type of a file (e.g., PDF, Markdown)
- **MetadataValue**: Represents a specific metadata value with its type
- **TagType**: Categorizes tags by their purpose or origin
- **VersionMetadata**: Contains metadata specific to a version

Example value object:

.. code-block:: python

    @dataclass(frozen=True)
    class FileType:
        name: str
        extension: str
        mime_type: str

        def is_text_based(self) -> bool:
            text_based_types = ["text/plain", "text/markdown", "text/html"]
            return self.mime_type in text_based_types

Repository Interfaces
-------------------

Repository interfaces define contracts for data access without implementation details:

- **IDocumentRepository**: Interface for document persistence
- **ITagRepository**: Interface for tag persistence
- **IRelationshipRepository**: Interface for relationship persistence
- **IVersionRepository**: Interface for version history persistence

Example repository interface:

.. code-block:: python

    class IDocumentRepository(Protocol):
        def add(self, document: Document) -> None:
            ...

        def get_by_id(self, document_id: UUID) -> Optional[Document]:
            ...

        def get_by_path(self, path: Path) -> Optional[Document]:
            ...

        def update(self, document: Document) -> None:
            ...

        def delete(self, document_id: UUID) -> None:
            ...

        def list(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Document]:
            ...

Domain Services
-------------

Domain services implement business logic that doesn't naturally belong to entities:

- **RelationshipService**: Handles complex relationship detection and management
- **TaggingService**: Provides tagging recommendations and management
- **DocumentValidationService**: Validates documents against business rules
- **SearchDomainService**: Core search functionality independent of specific search engines

Example domain service:

.. code-block:: python

    class RelationshipService:
        def detect_relationships(self, document: Document, other_documents: List[Document]) -> List[Relationship]:
            """Detects potential relationships between documents based on domain rules."""
            relationships = []

            # Apply business rules for relationship detection
            for other_doc in other_documents:
                if self._documents_are_related(document, other_doc):
                    relationship = Relationship(
                        source_id=document.id,
                        target_id=other_doc.id,
                        relationship_type=self._determine_relationship_type(document, other_doc)
                    )
                    relationships.append(relationship)

            return relationships

        def _documents_are_related(self, doc1: Document, doc2: Document) -> bool:
            # Domain logic to determine if documents are related
            ...

        def _determine_relationship_type(self, doc1: Document, doc2: Document) -> RelationshipType:
            # Domain logic to determine relationship type
            ...

Domain Events
-----------

Domain events represent significant occurrences in the domain:

- **DocumentCreated**: A new document was created
- **TagAdded**: A tag was added to a document
- **RelationshipEstablished**: A relationship was created between documents
- **VersionCreated**: A new version was created

Example domain event:

.. code-block:: python

    @dataclass(frozen=True)
    class DocumentCreated:
        document_id: UUID
        path: Path
        timestamp: datetime

        def __post_init__(self):
            # Ensure the timestamp is set to now if not provided
            object.__setattr__(self, 'timestamp', self.timestamp or datetime.now())

Domain Exceptions
---------------

Domain exceptions represent errors specific to the domain:

- **InvalidDocumentException**: Document violates domain rules
- **DuplicateTagException**: Attempt to add a duplicate tag
- **InvalidRelationshipException**: Relationship violates domain rules
- **VersioningException**: Error in version management

Example domain exception:

.. code-block:: python

    class InvalidDocumentException(Exception):
        def __init__(self, document_id: UUID, reason: str):
            self.document_id = document_id
            self.reason = reason
            super().__init__(f"Document {document_id} is invalid: {reason}")

Design Patterns in the Domain Layer
==================================

The domain layer implements several design patterns:

- **Aggregate Pattern**: Document as the aggregate root with tags, relationships, and versions
- **Value Object Pattern**: Immutable objects like FileType and MetadataValue
- **Repository Pattern**: Clean interfaces for data access
- **Domain Service Pattern**: Complex business logic that doesn't belong to entities
- **Factory Pattern**: For creation of complex domain objects

Domain Layer Rules
================

1. No dependencies on external frameworks or libraries
2. No direct database access or I/O operations
3. Business rules and logic contained within this layer
4. All external interactions through repository interfaces
5. Domain models designed for business needs, not data storage
6. Use of rich domain models with behavior, not just data
