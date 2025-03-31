=================
Interfaces Layer
=================

The interfaces layer provides the mechanisms for external systems and users to interact with the application, adapting between external protocols and the internal application structure.

Overview
========

The interfaces layer is the outermost layer of the clean architecture, responsible for handling all communication between the outside world and the application core. It transforms incoming requests into application layer commands and queries, and transforms the results back into appropriate response formats. This layer contains API controllers, CLI commands, event handlers, and other interface adapters.

Components
==========

API Interfaces
-------------

Components that handle HTTP/REST API requests:

- **ApiController**: Base controller with shared functionality
- **DocumentsController**: Handles document-related API requests
- **TagsController**: Handles tag-related API requests
- **SearchController**: Handles search-related API requests
- **VersionsController**: Handles version-related API requests

Example API controller:

.. code-block:: python

    class DocumentsController:
        def __init__(
            self,
            command_bus: ICommandBus,
            query_bus: IQueryBus,
            logger: Logger
        ):
            self.command_bus = command_bus
            self.query_bus = query_bus
            self.logger = logger

        async def get_document(self, document_id: str) -> Response:
            """Get a document by its ID."""
            try:
                query = GetDocumentByIdQuery(document_id=UUID(document_id))
                result = await self.query_bus.execute(query)

                if not result:
                    return Response(status_code=404, content={"error": "Document not found"})

                return Response(status_code=200, content=asdict(result))

            except Exception as e:
                self.logger.error(f"Error getting document {document_id}: {str(e)}")
                return Response(status_code=500, content={"error": "Internal server error"})

        async def create_document(self, request: Request) -> Response:
            """Create a new document."""
            try:
                data = await request.json()

                command = CreateDocumentCommand(
                    path=Path(data["path"]),
                    content_type=data["content_type"],
                    metadata=data.get("metadata", {}),
                    tags=data.get("tags", [])
                )

                document_id = await self.command_bus.execute(command)

                return Response(
                    status_code=201,
                    content={"id": str(document_id)},
                    headers={"Location": f"/api/documents/{document_id}"}
                )

            except KeyError as e:
                return Response(
                    status_code=400,
                    content={"error": f"Missing required field: {str(e)}"}
                )

            except Exception as e:
                self.logger.error(f"Error creating document: {str(e)}")
                return Response(status_code=500, content={"error": "Internal server error"})

CLI Interfaces
------------

Command-line interface components:

- **CliCommand**: Base class for CLI commands
- **DocumentCommands**: Document-related CLI commands
- **TagCommands**: Tag-related CLI commands
- **SearchCommands**: Search-related CLI commands
- **AdminCommands**: Administrative CLI commands

Example CLI command:

.. code-block:: python

    class DocumentCommands:
        def __init__(
            self,
            command_bus: ICommandBus,
            query_bus: IQueryBus
        ):
            self.command_bus = command_bus
            self.query_bus = query_bus

        def add_document(self, path: str, content_type: str, tags: List[str]) -> None:
            """Add a document to the system."""
            try:
                command = CreateDocumentCommand(
                    path=Path(path),
                    content_type=content_type,
                    metadata={},
                    tags=tags
                )

                document_id = self.command_bus.execute(command)
                click.echo(f"Document created with ID: {document_id}")

            except Exception as e:
                click.echo(f"Error creating document: {str(e)}", err=True)
                sys.exit(1)

        def list_documents(self, tag: Optional[str] = None, limit: int = 10) -> None:
            """List documents in the system."""
            try:
                query = ListDocumentsQuery(tag=tag, limit=limit)
                results = self.query_bus.execute(query)

                if not results:
                    click.echo("No documents found.")
                    return

                for doc in results:
                    click.echo(f"{doc.id}: {doc.path} [{doc.content_type}]")

            except Exception as e:
                click.echo(f"Error listing documents: {str(e)}", err=True)
                sys.exit(1)

Event Interfaces
--------------

Components that handle external events:

- **EventHandler**: Base class for event handlers
- **ExternalFileChangedHandler**: Handles file change events from the file system
- **WebhookHandler**: Handles incoming webhook events
- **ScheduledTaskHandler**: Handles scheduled task events

Example event handler:

.. code-block:: python

    class ExternalFileChangedHandler:
        def __init__(
            self,
            command_bus: ICommandBus,
            logger: Logger
        ):
            self.command_bus = command_bus
            self.logger = logger

        async def handle(self, event: ExternalFileChanged) -> None:
            """Handle external file changed event."""
            try:
                # Determine the event type
                if event.change_type == "created":
                    command = CreateDocumentCommand(
                        path=event.file_path,
                        content_type=self._determine_content_type(event.file_path),
                        metadata={"source": "file_watcher"}
                    )
                    await self.command_bus.execute(command)

                elif event.change_type == "modified":
                    command = UpdateDocumentCommand(
                        path=event.file_path,
                        create_version=True
                    )
                    await self.command_bus.execute(command)

                elif event.change_type == "deleted":
                    command = DeleteDocumentCommand(
                        path=event.file_path
                    )
                    await self.command_bus.execute(command)

            except Exception as e:
                self.logger.error(f"Error handling file change event: {str(e)}")

        def _determine_content_type(self, path: Path) -> str:
            """Determine content type from file extension."""
            suffix = path.suffix.lower()
            content_types = {
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".json": "application/json",
                ".html": "text/html",
                ".xml": "application/xml"
            }
            return content_types.get(suffix, "application/octet-stream")

Presenters
---------

Components that handle formatting responses for presentation:

- **JsonPresenter**: Formats responses as JSON
- **CliPresenter**: Formats responses for CLI output
- **HtmlPresenter**: Formats responses as HTML
- **CsvPresenter**: Formats responses as CSV

Example presenter:

.. code-block:: python

    class JsonPresenter:
        def present_document(self, document: DocumentDto) -> Dict[str, Any]:
            """Present a document as JSON."""
            return {
                "id": str(document.id),
                "path": str(document.path),
                "content_type": document.content_type,
                "metadata": document.metadata,
                "tags": document.tags,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "version_count": document.version_count
            }

        def present_documents(self, documents: List[DocumentDto]) -> Dict[str, Any]:
            """Present a list of documents as JSON."""
            return {
                "count": len(documents),
                "documents": [self.present_document(doc) for doc in documents]
            }

        def present_error(self, error: str, status_code: int = 400) -> Dict[str, Any]:
            """Present an error as JSON."""
            return {
                "error": error,
                "status_code": status_code
            }

GraphQL Interface
--------------

GraphQL API components:

- **GraphQLSchema**: Defines the GraphQL schema
- **GraphQLResolvers**: Implements resolvers for GraphQL queries and mutations
- **GraphQLTypes**: Defines GraphQL types

Example GraphQL resolver:

.. code-block:: python

    class DocumentResolvers:
        def __init__(
            self,
            query_bus: IQueryBus,
            command_bus: ICommandBus
        ):
            self.query_bus = query_bus
            self.command_bus = command_bus

        async def get_document(self, info, document_id: str) -> Dict[str, Any]:
            """Resolver for getting a document by ID."""
            query = GetDocumentByIdQuery(document_id=UUID(document_id))
            result = await self.query_bus.execute(query)

            if not result:
                raise GraphQLError("Document not found")

            return self._document_to_dict(result)

        async def search_documents(self, info, query: str, limit: int = 10) -> List[Dict[str, Any]]:
            """Resolver for searching documents."""
            search_query = SearchDocumentsQuery(query=query, limit=limit)
            results = await self.query_bus.execute(search_query)

            return [self._document_to_dict(doc) for doc in results]

        def _document_to_dict(self, document: DocumentDto) -> Dict[str, Any]:
            """Convert a document DTO to a dictionary."""
            return {
                "id": str(document.id),
                "path": str(document.path),
                "content_type": document.content_type,
                "metadata": document.metadata,
                "tags": document.tags,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "version_count": document.version_count
            }

Stream Processors
--------------

Components that handle streaming data:

- **StreamProcessor**: Base class for stream processors
- **FileStreamProcessor**: Processes file streams
- **MessageStreamProcessor**: Processes message streams
- **EventStreamProcessor**: Processes event streams

Example stream processor:

.. code-block:: python

    class FileStreamProcessor:
        def __init__(
            self,
            command_bus: ICommandBus,
            logger: Logger
        ):
            self.command_bus = command_bus
            self.logger = logger

        async def process(self, file_stream: AsyncIterator[bytes], metadata: Dict[str, Any]) -> None:
            """Process a file stream."""
            try:
                # Create a temporary file
                temp_file = NamedTemporaryFile(delete=False)
                temp_path = Path(temp_file.name)

                # Write the stream to the temporary file
                async with aiofiles.open(temp_path, "wb") as f:
                    async for chunk in file_stream:
                        await f.write(chunk)

                # Create a document from the temporary file
                command = CreateDocumentCommand(
                    path=temp_path,
                    content_type=metadata.get("content_type", "application/octet-stream"),
                    metadata={
                        "original_filename": metadata.get("filename", "unknown"),
                        "source": "stream",
                        **metadata
                    }
                )

                document_id = await self.command_bus.execute(command)
                self.logger.info(f"Created document {document_id} from stream")

            except Exception as e:
                self.logger.error(f"Error processing file stream: {str(e)}")
                raise
            finally:
                # Clean up the temporary file
                if "temp_path" in locals():
                    temp_path.unlink(missing_ok=True)

Design Patterns in the Interfaces Layer
=====================================

The interfaces layer implements several design patterns:

- **MVC Pattern**: Separate models, views, and controllers
- **Adapter Pattern**: Adapt application logic to external interfaces
- **Decorator Pattern**: Add functionality to interfaces transparently
- **Facade Pattern**: Provide simplified interfaces to complex subsystems
- **Strategy Pattern**: Flexible algorithms for request handling
- **Observer Pattern**: Notify components about events

Interfaces Layer Rules
====================

1. Transforms external requests into application layer commands and queries
2. Handles protocol-specific details (HTTP, CLI, GraphQL, etc.)
3. Contains no business logic
4. Maps DTOs to appropriate response formats
5. Manages interface-specific error handling
6. Provides consistent, well-documented APIs
