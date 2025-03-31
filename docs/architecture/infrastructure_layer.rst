===================
Infrastructure Layer
===================

The infrastructure layer provides implementations for interfaces defined in the domain and application layers, encapsulating all interactions with external systems, frameworks, and technologies.

Overview
========

The infrastructure layer is the outermost layer of the core application, implementing the interfaces defined in the domain and application layers. It contains concrete implementations for persistence, messaging, file handling, networking, and all other technical concerns. This layer is where the system interacts with the outside world, such as databases, file systems, external services, and other infrastructure components.

Components
==========

Repository Implementations
-------------------------

Concrete implementations of repository interfaces defined in the domain layer:

- **SqliteDocumentRepository**: Implements IDocumentRepository using SQLite
- **SqliteTagRepository**: Implements ITagRepository using SQLite
- **SqliteRelationshipRepository**: Implements IRelationshipRepository using SQLite
- **FileSystemVersionRepository**: Implements IVersionRepository using the file system

Example repository implementation:

.. code-block:: python

    class SqliteDocumentRepository(IDocumentRepository):
        def __init__(self, db_connection: Connection):
            self.db_connection = db_connection

        def add(self, document: Document) -> None:
            cursor = self.db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO documents (id, path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(document.id),
                    str(document.path),
                    document.created_at.isoformat(),
                    document.updated_at.isoformat()
                )
            )

            # Store metadata as JSON
            for key, value in document.metadata.items():
                cursor.execute(
                    """
                    INSERT INTO document_metadata (document_id, key, value)
                    VALUES (?, ?, ?)
                    """,
                    (str(document.id), key, json.dumps(value))
                )

            self.db_connection.commit()

        def get_by_id(self, document_id: UUID) -> Optional[Document]:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT id, path, created_at, updated_at FROM documents WHERE id = ?",
                (str(document_id),)
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Load document from database
            document = Document(
                document_id=UUID(row[0]),
                path=Path(row[1]),
                metadata={}
            )

            # Set timestamps
            document.created_at = datetime.fromisoformat(row[2])
            document.updated_at = datetime.fromisoformat(row[3])

            # Load metadata
            cursor.execute(
                "SELECT key, value FROM document_metadata WHERE document_id = ?",
                (str(document_id),)
            )

            for key, value in cursor.fetchall():
                document.metadata[key] = json.loads(value)

            return document

Persistence Adapters
------------------

Database and storage adapters:

- **SqliteDatabase**: SQLite database adapter
- **FileSystemStorage**: File system storage adapter
- **InMemoryCache**: In-memory caching adapter
- **DatabaseMigrator**: Handles database schema migrations

Example persistence adapter:

.. code-block:: python

    class SqliteDatabase:
        def __init__(self, db_path: Path):
            self.db_path = db_path
            self.connection = None

        def connect(self) -> Connection:
            if self.connection is None:
                self.connection = sqlite3.connect(
                    self.db_path,
                    detect_types=sqlite3.PARSE_DECLTYPES
                )
                self.connection.row_factory = sqlite3.Row

            return self.connection

        def close(self) -> None:
            if self.connection:
                self.connection.close()
                self.connection = None

        def execute_script(self, script: str) -> None:
            connection = self.connect()
            connection.executescript(script)
            connection.commit()

Messaging
--------

Message handling components:

- **EventBus**: Implementation of the event bus for domain events
- **MessagePublisher**: Publishes messages to external systems
- **MessageConsumer**: Consumes messages from external systems
- **MessageSerializer**: Serializes/deserializes messages

Example messaging component:

.. code-block:: python

    class InMemoryEventBus(IEventBus):
        def __init__(self):
            self.handlers = defaultdict(list)

        def register(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
            """Register an event handler for a specific event type."""
            self.handlers[event_type].append(handler)

        def publish(self, event: Any) -> None:
            """Publish an event to all registered handlers."""
            event_type = type(event)
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    handler(event)

Search
-----

Search implementations:

- **SqliteSearchProvider**: Basic search using SQLite
- **LuceneSearchProvider**: Full-text search using Lucene
- **EmbeddingSearchProvider**: Semantic search using embeddings

Example search implementation:

.. code-block:: python

    class SqliteSearchProvider(ISearchProvider):
        def __init__(self, db_connection: Connection):
            self.db_connection = db_connection

        def search(self, query: str, limit: int = 100) -> List[SearchResult]:
            cursor = self.db_connection.cursor()
            cursor.execute(
                """
                SELECT id, path, snippet(documents_fts, 0, '<b>', '</b>', '...', 10) as snippet
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit)
            )

            results = []
            for row in cursor.fetchall():
                results.append(SearchResult(
                    document_id=UUID(row[0]),
                    path=Path(row[1]),
                    snippet=row[2],
                    score=1.0  # Not provided by SQLite FTS
                ))

            return results

Configuration
-----------

Configuration handling:

- **ConfigLoader**: Loads configuration from various sources
- **EnvironmentConfig**: Handles environment-specific configuration
- **FeatureFlags**: Manages feature flags and toggles
- **ConfigValidator**: Validates configuration values

Example configuration component:

.. code-block:: python

    class ConfigLoader:
        def __init__(self):
            self.config = {}
            self.config_sources = []

        def add_source(self, source: IConfigSource) -> None:
            """Add a configuration source."""
            self.config_sources.append(source)

        def load(self) -> Dict[str, Any]:
            """Load configuration from all sources."""
            self.config = {}

            # Load from sources in order (later sources override earlier ones)
            for source in self.config_sources:
                self.config.update(source.load())

            return self.config

        def get(self, key: str, default: Any = None) -> Any:
            """Get a configuration value."""
            return self.config.get(key, default)

Logging and Telemetry
-------------------

Logging and monitoring implementations:

- **LoggingProvider**: Handles application logging
- **MetricsCollector**: Collects application metrics
- **TracingProvider**: Implements distributed tracing
- **HealthChecker**: Monitors application health

Example logging component:

.. code-block:: python

    class LoggingProvider:
        def __init__(self, config: Dict[str, Any]):
            self.logger = logging.getLogger("aichemist")
            self.configure(config)

        def configure(self, config: Dict[str, Any]) -> None:
            """Configure the logger based on configuration."""
            log_level = getattr(logging, config.get("log_level", "INFO"))
            log_format = config.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            log_file = config.get("log_file")

            # Configure root logger
            logging.basicConfig(
                level=log_level,
                format=log_format,
                filename=log_file
            )

            # Add console handler if needed
            if config.get("log_to_console", True):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(log_format))
                self.logger.addHandler(console_handler)

        def get_logger(self, name: str) -> logging.Logger:
            """Get a logger with the specified name."""
            return logging.getLogger(f"aichemist.{name}")

Security
-------

Security-related components:

- **AuthenticationProvider**: Handles user authentication
- **AuthorizationService**: Manages access control
- **EncryptionService**: Provides encryption capabilities
- **SecretManager**: Manages sensitive information

Example security component:

.. code-block:: python

    class AuthenticationProvider:
        def __init__(self, user_repository: IUserRepository):
            self.user_repository = user_repository

        def authenticate(self, username: str, password: str) -> Optional[User]:
            """Authenticate a user with username and password."""
            user = self.user_repository.get_by_username(username)
            if not user:
                return None

            # Check password
            if not self.verify_password(password, user.password_hash):
                return None

            return user

        def verify_password(self, password: str, password_hash: str) -> bool:
            """Verify a password against a hash."""
            # Use secure password verification
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )

External Services
---------------

Integrations with external services:

- **EmailService**: Sends email notifications
- **WebhookService**: Handles webhook integrations
- **AiService**: Integrates with AI services
- **StorageService**: Integrates with cloud storage services

Example external service integration:

.. code-block:: python

    class EmailService:
        def __init__(self, config: Dict[str, Any]):
            self.smtp_host = config.get("smtp_host", "localhost")
            self.smtp_port = config.get("smtp_port", 25)
            self.smtp_user = config.get("smtp_user")
            self.smtp_password = config.get("smtp_password")
            self.from_address = config.get("email_from", "noreply@example.com")

        def send_email(self, to: str, subject: str, body: str, is_html: bool = False) -> None:
            """Send an email to the specified recipient."""
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = to
            msg["Subject"] = subject

            # Add body
            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)

Design Patterns in the Infrastructure Layer
=========================================

The infrastructure layer implements several design patterns:

- **Adapter Pattern**: Adapt domain interfaces to external technologies
- **Repository Pattern**: Concrete implementations of repository interfaces
- **Proxy Pattern**: Provide controlled access to resources
- **Decorator Pattern**: Add functionality to components transparently
- **Factory Pattern**: Create and configure infrastructure components
- **Bridge Pattern**: Separate abstractions from implementations

Infrastructure Layer Rules
========================

1. Implements interfaces defined in domain and application layers
2. Contains all technical details and external dependencies
3. Handles all I/O operations (database, file system, network)
4. Creates and manages connections to external resources
5. Translates between domain models and persistence models
6. Handles infrastructure-specific error handling and recovery
