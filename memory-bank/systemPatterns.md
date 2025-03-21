# The AIChemist Codex - System Patterns

## System Architecture

The AIChemist Codex follows a layered domain-driven design architecture enhanced
with modern async processing patterns:

```
┌──────────────────────────────────────────────────────────────┐
│                        Application Layer                      │
│                   (CLI, Future GUI, API)                      │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                        Service Layer                          │
│           (Application services, orchestration)               │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                        Domain Layer                           │
│         (Business logic, domain services, entities)           │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                      │
│          (Implementations of core interfaces)                 │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                         Core Layer                            │
│          (Interfaces, exceptions, constants, models)          │
└──────────────────────────────────────────────────────────────┘
```

## Key Technical Decisions

### 1. Enhanced Registry Pattern

The Registry pattern is enhanced with contextual service resolution and
lifecycle management:

```python
# Modern Registry implementation
class Registry:
    _instance = None

    @classmethod
    def get_instance(cls) -> 'Registry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._services = {}
        self._factories = {}
        self._contexts = {}
        self._scopes = {}

    # Service registration with scope
    def register(self, key: str, implementation, scope: str = "singleton"):
        self._services[key] = implementation
        self._scopes[key] = scope

    # Context-aware service resolution
    def resolve(self, key: str, context: str = None):
        # Respect service lifecycle (singleton, transient, scoped)
        scope = self._scopes.get(key, "singleton")

        if scope == "singleton":
            return self._services.get(key)
        elif scope == "transient":
            return self._factories.get(key)()
        else:  # scoped
            context_key = f"{context}:{key}"
            if context_key not in self._contexts:
                self._contexts[context_key] = self._factories.get(key)()
            return self._contexts[context_key]

    # Lazy-loaded property for common services
    @property
    def file_reader(self) -> 'FileReader':
        return self.resolve('file_reader')
```

### 2. Async-First Processing Pattern

File operations utilize memory-mapped I/O with asyncio for high performance:

```python
# Async file processing with mmap
async def process_file(file_path: str, chunk_size: int = 10_000_000):
    # Create queues for the producer-consumer pattern
    input_queue = asyncio.Queue(maxsize=10)
    output_queue = asyncio.Queue(maxsize=10)

    # Start producer, processor, and consumer tasks
    reader_task = asyncio.create_task(
        read_file_chunks(file_path, input_queue, chunk_size)
    )
    processor_task = asyncio.create_task(
        process_chunks(input_queue, output_queue)
    )
    writer_task = asyncio.create_task(
        write_processed_chunks(output_file, output_queue)
    )

    # Wait for all tasks to complete
    await asyncio.gather(reader_task, processor_task, writer_task)

async def read_file_chunks(file_path: str, queue: asyncio.Queue, chunk_size: int):
    with open(file_path, "rb") as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            for position in range(0, len(mm), chunk_size):
                # Read a chunk and put it in the queue
                chunk = mm[position:position + chunk_size]
                await queue.put(chunk)

    # Signal end of file
    await queue.put(None)
```

### 3. Vector-Based Search Pattern

The search engine uses embeddings and vector databases for semantic search:

```python
# Vector-based search implementation
class VectorSearchEngine:
    def __init__(self, vector_db, embedding_model):
        self.vector_db = vector_db
        self.embedding_model = embedding_model

    async def index_document(self, document_id: str, content: str):
        # Generate embedding vector
        embedding = await self.embedding_model.embed(content)

        # Store in vector database
        await self.vector_db.upsert(document_id, embedding)

    async def search(self, query: str, limit: int = 10):
        # Generate query embedding
        query_embedding = await self.embedding_model.embed(query)

        # Find similar documents
        results = await self.vector_db.search(
            query_embedding,
            limit=limit
        )

        return results

    async def hybrid_search(self, query: str, limit: int = 10):
        # Combine keyword search with vector search
        keyword_results = await self.keyword_search(query, limit=limit)
        vector_results = await self.search(query, limit=limit)

        # Merge and rank results
        return self._merge_results(keyword_results, vector_results)
```

## Design Patterns in Use

### 1. Factory Pattern

Factory methods create implementations of interfaces:

```python
def create_file_reader() -> FileReaderInterface:
    return FileReaderImpl()

def create_search_engine() -> SearchEngineInterface:
    # Initialize vector database
    vector_db = create_vector_db()

    # Initialize embedding model
    embedding_model = create_embedding_model()

    return VectorSearchEngineImpl(vector_db, embedding_model)
```

### 2. Strategy Pattern

Different strategies for file operations, search, and metadata extraction:

```python
# Different search strategies
class FullTextSearchStrategy(SearchStrategy):
    def search(self, query: str, files: List[Path]) -> List[SearchResult]:
        # Implementation...

class SemanticSearchStrategy(SearchStrategy):
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    async def search(self, query: str, files: List[Path]) -> List[SearchResult]:
        # Generate query embedding
        query_embedding = await self.embedding_model.embed(query)

        # Find similar documents
        # Implementation...
```

### 3. Observer Pattern

For event notification and handling:

```python
# Event system for file changes
class FileChangeNotifier:
    def __init__(self):
        self._observers = []

    def add_observer(self, observer: FileChangeObserver):
        self._observers.append(observer)

    def notify_file_changed(self, file_path: Path):
        for observer in self._observers:
            observer.on_file_changed(file_path)
```

### 4. Adapter Pattern

For backward compatibility and external system integration:

```python
# Adapter for legacy code compatibility
class LegacyFileReaderAdapter(FileReaderInterface):
    def __init__(self, legacy_reader):
        self._legacy_reader = legacy_reader

    def read_text(self, path: str) -> str:
        return self._legacy_reader.read_file_contents(path)
```

### 5. Producer-Consumer Pattern

For efficient async processing of large files:

```python
async def producer(queue: asyncio.Queue, file_path: str):
    # Read chunks from file and put them in the queue
    # ...

async def consumer(queue: asyncio.Queue, output_path: str):
    # Process chunks from the queue and write to output
    # ...

async def processor(input_queue: asyncio.Queue, output_queue: asyncio.Queue):
    # Process chunks from input queue and put results in output queue
    while True:
        chunk = await input_queue.get()
        if chunk is None:
            await output_queue.put(None)
            break

        processed_chunk = process_chunk(chunk)
        await output_queue.put(processed_chunk)
        input_queue.task_done()
```

## Component Relationships

### File Management System

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  FileManager    │──────│  PathValidator  │      │ TransactionLog  │
└────────┬────────┘      └─────────────────┘      └────────┬────────┘
         │                                                  │
         ▼                                                  ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   FileReader    │──────│   FileWriter    │──────│  RollbackSystem │
└────────┬────────┘      └────────┬────────┘      └─────────────────┘
         │                        │
         └────────────────┬───────┘
                          │
                          ▼
                   ┌─────────────────┐
                   │ DuplicateDetector│
                   └─────────────────┘
```

### Enhanced Content Analysis System

```
┌─────────────────┐      ┌─────────────────┐
│ MetadataManager │──────│   MimeDetector  │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  ContentParser  │──────│  TaggingSystem  │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └────────────────┬───────┘
                          │
                          ▼
                   ┌─────────────────┐
                   │RelationshipMapper│
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  KnowledgeGraph │
                   └─────────────────┘
```

### Vector-Based Search System

```
┌─────────────────┐
│  SearchEngine   │
└────────┬────────┘
         │
         ├─────────────────────┬───────────────────┐
         │                     │                   │
         ▼                     ▼                   ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│FullTextSearcher │   │SemanticSearcher │   │ HybridSearcher  │
└─────────────────┘   └────────┬────────┘   └─────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  VectorDatabase │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ EmbeddingModel  │
                      └─────────────────┘
```

## Error Handling Pattern

The project uses a structured error handling approach with specific exception
types:

```python
# Base exception for all project errors
class AiChemistError(Exception):
    """Base exception for all project errors."""

# Specific exception types
class FileError(AiChemistError):
    """Error related to file operations."""

class DirectoryError(AiChemistError):
    """Error related to directory operations."""

class UnsafePathError(AiChemistError):
    """Error for unsafe file paths."""
```

## Module Structure Pattern

Each module follows a consistent structure:

```
domain/file_reader/
├── __init__.py           # Exports main classes
├── file_reader.py        # Main implementation
├── strategies/           # Specific strategies
│   ├── __init__.py
│   ├── text_reader.py
│   └── binary_reader.py
└── exceptions.py         # Module-specific exceptions
```

## Plugin Architecture Pattern

The system supports extensibility through a plugin architecture:

```python
# Plugin registry
class PluginRegistry:
    def __init__(self):
        self.plugins = {}

    def register_plugin(self, plugin_type: str, plugin):
        if plugin_type not in self.plugins:
            self.plugins[plugin_type] = []
        self.plugins[plugin_type].append(plugin)

    def get_plugins(self, plugin_type: str):
        return self.plugins.get(plugin_type, [])

# Plugin interface
class Plugin(Protocol):
    def initialize(self):
        ...

    def name(self) -> str:
        ...

    def version(self) -> str:
        ...
```

# System Patterns

This document outlines the core architectural patterns and design decisions in
the AIChemist Codex system.

## Architecture Overview

The AIChemist Codex follows a layered architecture with clean separation of
concerns:

- **Core Layer**: Contains interfaces, models, and abstractions
- **Domain Layer**: Implements business logic and core functionality
- **Infrastructure Layer**: Provides external integrations and I/O operations
- **Presentation Layer**: Handles UI concerns (CLI and potential future
  interfaces)

## Key Patterns

### Registry Pattern

The system uses a centralized Registry for dependency management:

- **Singleton Instance**: One registry instance is maintained throughout the
  application
- **Service Lifecycles**: Services can be registered as singleton, transient, or
  scoped
- **Lazy Initialization**: Services are only created when needed
- **Forward Declarations**: Interfaces are forward-declared to break circular
  dependencies
- **Property Accessors**: Common services are exposed through properties for
  cleaner syntax

```python
# Example Registry usage
registry = Registry.get_instance()
search_engine = registry.search_engine
```

### Async-First Architecture

The system is designed with asynchronous operations as the primary pattern:

- **Python Asyncio**: Leverages the asyncio library for async operations
- **Async Interfaces**: Core interfaces define async methods
- **Sync Wrappers**: Where needed, sync wrappers are provided for backward
  compatibility
- **Task Management**: Long-running operations are managed as asyncio tasks

### Producer-Consumer Pattern

For processing large files efficiently, we implement a producer-consumer
pattern:

- **Memory-Mapped I/O**: Uses memory mapping for efficient file reading
- **Async Queues**: Utilizes asyncio.Queue for chunk coordination
- **Worker Pools**: Supports configurable number of worker tasks
- **Processing Modes**: Supports sequential, parallel, and streaming modes

```python
# Example AsyncFileProcessor implementation
async def process_file(
    self,
    input_file: str,
    output_file: str,
    processor: ChunkProcessor | AsyncChunkProcessor,
    chunk_size: int | None = None,
    mode: ProcessingMode = ProcessingMode.PARALLEL,
    num_workers: int | None = None,
    result_collector: ResultCollector | None = None,
) -> Any:
    # ... implementation
```

### Strategy Pattern for Relationship Detection

Relationship detection is implemented using the strategy pattern:

- **Detection Strategies**: Different strategies for various relationship types
- **Strategy Interface**: Common interface for all detection strategies
- **Composable Detection**: Multiple strategies can be composed for
  comprehensive detection
- **Extensibility**: New strategies can be added without modifying existing code

```python
# Basic structure of the strategy pattern
class DetectionStrategy(ABC):
    @abstractmethod
    async def detect_relationships(self, file_path: Path) -> List[Relationship]:
        pass

class RelationshipDetector:
    def __init__(self):
        self._strategies = [
            VectorSimilarityStrategy(),
            ReferenceDetectionStrategy(),
            # More strategies can be added
        ]

    async def detect_relationships(self, file_path: Path) -> List[Relationship]:
        # Aggregates results from all strategies
```

### Vector-Based Similarity

For detecting semantic similarities between files:

- **Vector Embeddings**: Uses vector representations of file content
- **Similarity Threshold**: Configurable threshold for relationship creation
- **Efficient Lookups**: Uses vector databases for fast similarity searches
- **Contextual Understanding**: Captures semantic relationships beyond exact
  pattern matches

### Exception Hierarchy

A comprehensive exception hierarchy for consistent error handling:

- **Base Exception**: `AiChemistError` serves as the base for all exceptions
- **Specialized Exceptions**: Domain-specific exceptions inherit from the base
- **Context Preservation**: Exceptions maintain context for better error
  reporting
- **Consistent API**: All exceptions have a common structure and behavior

```python
# Exception hierarchy structure
class AiChemistError(Exception):
    def __init__(self, message: str, error_code: str = "general_error", details: dict = None):
        # ... implementation

class FileError(AiChemistError):
    def __init__(self, message: str, file_path: str, error_code: str = "file_error", details: dict = None):
        # ... implementation
```

## Data Flow

1. **File Intake**: Files are read using the AsyncFileProcessor for efficient
   I/O
2. **Content Analysis**: File content is analyzed for metadata extraction
3. **Vector Generation**: Text content is converted to vector embeddings
4. **Relationship Detection**: Relationships between files are detected and
   stored
5. **Search Indexing**: Content and relationships are indexed for search
6. **Query Processing**: User queries are processed against the indexes
7. **Result Presentation**: Results are formatted and presented to the user

## Extensibility Points

The system is designed with several extension points:

- **Detection Strategies**: New relationship detection strategies can be added
- **Processor Functions**: Custom chunk processing functions can be supplied
- **Output Formatters**: Custom output formatting can be implemented
- **Storage Providers**: Different storage backends can be integrated
- **Vector Backends**: Various vector database systems can be used
