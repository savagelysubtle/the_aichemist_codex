# File Manager Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The file_manager module is responsible for handling file operations such as
moving, copying, detecting changes, versioning, and monitoring directories for
changes. The key components include:

- **FileManagerImpl**: Main implementation of the FileManager interface
- **ChangeDetector**: Utility for comparing files and detecting differences
- **DirectoryMonitor**: Service for watching directory changes in real-time
- Key functionalities:
  - File operations (move, copy)
  - File versioning and restoration
  - Change detection between versions
  - Directory monitoring for changes

## Architectural Compliance

The file_manager module demonstrates good alignment with the project's
architectural guidelines in several areas:

| Architectural Principle    | Status | Notes                                                                            |
| -------------------------- | :----: | -------------------------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Proper separation between core interface and domain implementation               |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection and service access                        |
| **Interface-Based Design** |   ✅   | FileManagerImpl properly implements the FileManager interface                    |
| **Import Strategy**        |   ✅   | Uses absolute imports for core interfaces and relative imports for local modules |
| **Asynchronous Design**    | ✅/⚠️  | Most methods use async/await, but some in DirectoryMonitor are inconsistent      |
| **Error Handling**         |   ✅   | Uses specific FileManagerError with context                                      |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                               | Status | Issue                                                                |
| ---------------------------------- | :----: | -------------------------------------------------------------------- |
| **External Dependency Management** |   ⚠️   | Watchdog library is directly imported without abstraction layer      |
| **Async Consistency**              |   ⚠️   | Some monitoring methods don't fully leverage async patterns          |
| **Configuration**                  |   🔄   | Limited configuration options for monitors and change detection      |
| **Testing Support**                |   ❌   | No mock filesystem for testing file operations safely                |
| **Extensibility**                  |   🔄   | Limited support for custom file operations or monitoring strategies  |
| **Performance**                    |   ⚠️   | Monitor implementation could be optimized for large directories      |
| **Transactional Operations**       |   ❌   | File operations are not transactional and lack rollback capabilities |

## Recommendations

### 1. Abstract External Dependencies

- Create an adapter layer for file system monitoring to abstract the Watchdog
  dependency
- Implement alternative monitoring strategies when Watchdog is not available

```python
# infrastructure/file_system/monitor_adapter.py
class FileSystemMonitorAdapter:
    """Adapter for file system monitoring implementations."""

    @classmethod
    def create_monitor(cls, config_provider):
        """Factory method to create appropriate monitor implementation."""
        try:
            # Try to use Watchdog if available
            return WatchdogMonitorAdapter()
        except ImportError:
            # Fall back to polling implementation
            return PollingMonitorAdapter()

class WatchdogMonitorAdapter:
    """Watchdog-based implementation of file system monitoring."""

    def __init__(self):
        from watchdog.observers import Observer
        self._observer = Observer()

    # Implementation methods

class PollingMonitorAdapter:
    """Polling-based implementation of file system monitoring."""

    def __init__(self):
        self._polling_interval = 1.0  # seconds
        self._running = False

    # Implementation methods using polling approach
```

### 2. Implement Async Monitoring Correctly

- Refactor DirectoryMonitor to use proper async patterns
- Use asyncio.Event for control flow instead of sleep loops

```python
# domain/file_manager/directory_monitor.py
class AsyncDirectoryMonitor:
    """Asynchronous directory monitoring service."""

    def __init__(self, directory: Path, callback, monitor_adapter):
        self._directory = directory
        self._callback = callback
        self._monitor_adapter = monitor_adapter
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start monitoring the directory."""
        # Register with monitor adapter
        await self._monitor_adapter.register(self._directory, self._handle_event)

    async def stop(self):
        """Stop monitoring the directory."""
        self._stop_event.set()
        await self._monitor_adapter.unregister(self._directory)

    async def _handle_event(self, event):
        """Handle file system events asynchronously."""
        # Process the event
        if callable(self._callback):
            await self._callback(event)
```

### 3. Add Transactional File Operations

- Implement a transaction system for file operations
- Support rollback of failed operations

```python
# domain/file_manager/transaction.py
class FileTransaction:
    """Transaction for file operations with rollback capability."""

    def __init__(self, registry):
        self._registry = registry
        self._operations = []
        self._rollback_ops = []

    async def add_operation(self, operation, *args, rollback=None):
        """Add an operation to the transaction."""
        self._operations.append((operation, args))
        if rollback:
            self._rollback_ops.append(rollback)

    async def commit(self):
        """Commit all operations in the transaction."""
        results = []
        for i, (operation, args) in enumerate(self._operations):
            try:
                result = await operation(*args)
                results.append(result)
            except Exception as e:
                # Operation failed, rollback previous operations
                await self.rollback(i)
                raise e
        return results

    async def rollback(self, up_to=None):
        """Rollback operations in reverse order."""
        for rollback_op in reversed(self._rollback_ops[:up_to]):
            try:
                await rollback_op()
            except Exception as e:
                # Log the error but continue rolling back
                logger.error(f"Error during rollback: {e}")
```

### 4. Add File System Abstraction Layer

- Create an abstraction layer for file system operations
- Enable easier testing with mock file systems

```python
# infrastructure/file_system/file_system.py
class FileSystem:
    """Abstraction for file system operations."""

    @abstractmethod
    async def move(self, source: Path, destination: Path) -> None:
        """Move a file from source to destination."""
        pass

    @abstractmethod
    async def copy(self, source: Path, destination: Path) -> None:
        """Copy a file from source to destination."""
        pass

    @abstractmethod
    async def delete(self, path: Path) -> None:
        """Delete a file or directory."""
        pass

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        pass

# Real implementation
class RealFileSystem(FileSystem):
    """Real file system implementation."""

    async def move(self, source: Path, destination: Path) -> None:
        """Move a file from source to destination."""
        shutil.move(str(source), str(destination))

    # Other method implementations

# Mock implementation for testing
class MockFileSystem(FileSystem):
    """Mock file system for testing."""

    def __init__(self):
        self._files = {}

    async def move(self, source: Path, destination: Path) -> None:
        """Move a file from source to destination."""
        if str(source) not in self._files:
            raise FileNotFoundError(f"Source not found: {source}")
        self._files[str(destination)] = self._files.pop(str(source))

    # Other method implementations
```

### 5. Implement Progressive Monitoring

- Add support for progressive monitoring with change batching
- Handle large directories more efficiently

```python
# domain/file_manager/progressive_monitor.py
class ProgressiveDirectoryMonitor:
    """Monitor that processes changes in batches for efficiency."""

    def __init__(self, directory: Path, batch_size: int = 100, batch_interval: float = 0.5):
        self._directory = directory
        self._batch_size = batch_size
        self._batch_interval = batch_interval
        self._pending_events = []
        self._batch_timer = None

    async def start(self, callback):
        """Start monitoring with batched event processing."""
        # Set up the monitor

        # Set up batch timer
        self._batch_timer = asyncio.create_task(self._process_batches(callback))

    async def _process_batches(self, callback):
        """Process events in batches."""
        while True:
            await asyncio.sleep(self._batch_interval)

            # Get current batch of events
            current_batch = []
            while self._pending_events and len(current_batch) < self._batch_size:
                current_batch.append(self._pending_events.pop(0))

            if current_batch:
                # Process the batch
                await callback(current_batch)
```

### 6. Add Configurable Change Detection

- Make change detection strategies configurable
- Support different algorithms for different file types

```python
# domain/file_manager/change_detector.py
class ConfigurableChangeDetector:
    """Change detector with configurable strategies."""

    def __init__(self, config_provider):
        self._config_provider = config_provider
        self._strategies = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default change detection strategies."""
        self._strategies = {
            "text": TextChangeStrategy(),
            "binary": BinaryChangeStrategy(),
            "image": ImageChangeStrategy(),
            "default": DefaultChangeStrategy()
        }

    async def detect_changes(self, current, reference, file_type=None):
        """Detect changes using the appropriate strategy."""
        # Determine file type if not provided
        if not file_type and isinstance(current, Path):
            file_type = self._determine_file_type(current)

        # Get the appropriate strategy
        strategy = self._strategies.get(file_type, self._strategies["default"])

        # Apply the strategy
        return await strategy.detect_changes(current, reference)

class ChangeStrategy:
    """Base class for change detection strategies."""

    @abstractmethod
    async def detect_changes(self, current, reference):
        """Detect changes between current and reference."""
        pass
```

### 7. Add Support for Distributed File Operations

- Add support for distributed file operations across multiple nodes
- Implement conflict resolution strategies

```python
# domain/file_manager/distributed_operations.py
class DistributedFileManager:
    """Extension for distributed file operations."""

    def __init__(self, file_manager, node_manager):
        self._file_manager = file_manager
        self._node_manager = node_manager

    async def distributed_copy(self, source_path, destination_path, node_id=None):
        """Copy a file to a specific node or all nodes."""
        if node_id:
            # Copy to specific node
            return await self._node_manager.execute_operation(
                node_id, "copy_file", [source_path, destination_path]
            )
        else:
            # Copy to all nodes
            return await self._node_manager.broadcast_operation(
                "copy_file", [source_path, destination_path]
            )

    # Other distributed operations

    async def resolve_conflicts(self, file_path, strategy="newest"):
        """Resolve conflicts across nodes."""
        # Get file info from all nodes
        file_info = await self._node_manager.gather_file_info(file_path)

        # Apply resolution strategy
        if strategy == "newest":
            newest = max(file_info, key=lambda x: x["modified_time"])
            # Use the newest file as the authoritative version
            # and distribute it to all nodes
            return await self.distributed_copy(newest["node_id"], file_path)
```

## Implementation Plan

### Phase 1: Core Improvements (2 weeks)

1. Create file system abstraction layer
2. Refactor DirectoryMonitor for proper async pattern usage
3. Implement abstract monitoring adapter

### Phase 2: Reliability & Transactions (3 weeks)

1. Develop transactional file operations system
2. Add rollback capabilities
3. Implement configurable change detection

### Phase 3: Performance & Scalability (2 weeks)

1. Develop progressive monitoring for large directories
2. Optimize change detection for large files
3. Implement batched operations

### Phase 4: Advanced Features (3 weeks)

1. Add distributed file operations support
2. Implement conflict resolution strategies
3. Add extensibility points for custom operations

## Priority Matrix

| Improvement                    | Impact | Effort | Priority |
| ------------------------------ | :----: | :----: | :------: |
| File System Abstraction        |  High  | Medium |    1     |
| Transactional Operations       |  High  |  High  |    2     |
| Async Monitoring Improvements  | Medium |  Low   |    3     |
| External Dependency Management | Medium |  Low   |    4     |
| Configurable Change Detection  | Medium | Medium |    5     |
| Progressive Monitoring         |  High  | Medium |    6     |
| Distributed Operations         |  High  |  High  |    7     |
