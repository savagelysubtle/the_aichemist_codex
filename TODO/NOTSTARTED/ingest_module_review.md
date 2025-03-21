# Ingest Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The ingest module is responsible for content acquisition from various sources
and processing through specialized pipelines. The key components include:

- **IngestManagerImpl**: Main implementation of the IngestManager interface
- **Sources**: Base and specialized content sources (FilesystemIngestSource,
  WebIngestSource)
- **Processors**: Content processors for different content types (Text,
  Markdown, Code)
- **Models**: Data models for ingest jobs, content, and processing status
- Key functionalities:
  - Content acquisition from multiple sources
  - Content processing through specialized pipelines
  - Job tracking and status management
  - Source and processor registration

## Architectural Compliance

The ingest module demonstrates good alignment with the project's architectural
guidelines:

| Architectural Principle    | Status | Notes                                                                            |
| -------------------------- | :----: | -------------------------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the domain layer                                          |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection and service access                        |
| **Interface-Based Design** |   ✅   | IngestManagerImpl properly implements the IngestManager interface                |
| **Import Strategy**        |   ✅   | Uses absolute imports for core interfaces and relative imports for local modules |
| **Asynchronous Design**    |   ✅   | Methods consistently use async/await patterns                                    |
| **Extension Points**       |   ✅   | Good design for extensibility with source and processor registration             |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                      | Status | Issue                                                        |
| ------------------------- | :----: | ------------------------------------------------------------ |
| **Error Handling**        |   ⚠️   | Inconsistent error handling across sources and processors    |
| **Progress Reporting**    |   🔄   | Limited mechanism for reporting ingestion progress           |
| **Parallel Processing**   |   ⚠️   | Sequential processing of content items could be parallelized |
| **Source Authentication** |   ❌   | Limited authentication mechanisms for remote sources         |
| **Resumable Operations**  |   ❌   | No support for resuming failed ingest operations             |
| **Content Validation**    |   ⚠️   | Basic content validation could be enhanced                   |
| **Job Management**        |   🔄   | Job lifecycle management could be improved                   |

## Recommendations

### 1. Implement Consistent Error Handling

- Create specialized error types for ingest operations
- Add context-rich error information for debugging

```python
# core/exceptions.py
class IngestError(AiChemistError):
    """Base class for ingest-related errors."""
    pass

class SourceAccessError(IngestError):
    """Error raised when a source cannot be accessed."""
    def __init__(self, message: str, source_id: str, details: dict = None):
        self.source_id = source_id
        self.details = details or {}
        super().__init__(f"Source access error: {message}")

class ProcessingError(IngestError):
    """Error raised when content processing fails."""
    def __init__(self, message: str, content_id: str, processor_id: str, details: dict = None):
        self.content_id = content_id
        self.processor_id = processor_id
        self.details = details or {}
        super().__init__(f"Processing error: {message}")
```

### 2. Add Progress Reporting System

- Create a unified progress reporting system
- Support real-time progress updates and status reporting

```python
# domain/ingest/progress.py
class ProgressReporter:
    """Progress reporting system for ingest operations."""

    def __init__(self, job_id: str, total_items: int, callback=None):
        self._job_id = job_id
        self._total_items = total_items
        self._processed_items = 0
        self._started_at = datetime.now()
        self._last_update = None
        self._status = "initializing"
        self._callback = callback
        self._phases = {}

    async def start_phase(self, phase_name: str, items: int):
        """Start a new processing phase."""
        self._phases[phase_name] = {
            "total": items,
            "processed": 0,
            "started_at": datetime.now(),
            "status": "in_progress"
        }
        self._status = f"processing_{phase_name}"
        await self._report_progress()

    async def update_phase(self, phase_name: str, processed: int, status: str = None):
        """Update progress for a phase."""
        if phase_name in self._phases:
            self._phases[phase_name]["processed"] = processed
            if status:
                self._phases[phase_name]["status"] = status
            self._last_update = datetime.now()
            await self._report_progress()

    async def complete_phase(self, phase_name: str):
        """Mark a phase as complete."""
        if phase_name in self._phases:
            self._phases[phase_name]["status"] = "completed"
            self._phases[phase_name]["completed_at"] = datetime.now()
            await self._report_progress()

    async def item_processed(self, item_id: str):
        """Record a processed item."""
        self._processed_items += 1
        self._last_update = datetime.now()
        await self._report_progress()

    async def _report_progress(self):
        """Report current progress."""
        progress = {
            "job_id": self._job_id,
            "total_items": self._total_items,
            "processed_items": self._processed_items,
            "progress_percentage": (self._processed_items / max(1, self._total_items)) * 100,
            "started_at": self._started_at,
            "last_update": self._last_update,
            "status": self._status,
            "phases": self._phases,
            "estimated_time_remaining": self._estimate_remaining_time()
        }

        # Notify callback if provided
        if self._callback and callable(self._callback):
            await self._callback(progress)

        return progress

    def _estimate_remaining_time(self):
        """Estimate remaining time based on progress."""
        if self._processed_items == 0:
            return None

        elapsed = (datetime.now() - self._started_at).total_seconds()
        items_per_second = self._processed_items / elapsed

        if items_per_second == 0:
            return None

        remaining_items = self._total_items - self._processed_items
        return remaining_items / items_per_second
```

### 3. Implement Parallel Processing

- Add support for parallel content processing
- Control concurrency based on resource availability

```python
# domain/ingest/parallel_processor.py
class ParallelProcessor:
    """Processor for parallel content processing."""

    def __init__(self, registry, max_workers: int = 4):
        self._registry = registry
        self._max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)

    async def process_batch(self, items: list, processor_id: str, progress_reporter=None):
        """
        Process a batch of items in parallel.

        Args:
            items: List of content items to process
            processor_id: ID of the processor to use
            progress_reporter: Optional progress reporter

        Returns:
            List of processing results
        """
        tasks = []
        for item in items:
            task = self._process_item(item, processor_id, progress_reporter)
            tasks.append(task)

        # Process all items in parallel with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing item {items[i].id}: {result}")
            else:
                processed_results.append(result)

        return processed_results

    async def _process_item(self, item, processor_id, progress_reporter):
        """Process a single item with concurrency control."""
        async with self._semaphore:
            # Get the processor
            processor = self._registry.get_processor(processor_id)
            if not processor:
                raise ProcessingError(
                    f"Processor not found: {processor_id}",
                    content_id=item.id,
                    processor_id=processor_id
                )

            # Process the item
            result = await processor.process(item)

            # Update progress if reporter provided
            if progress_reporter:
                await progress_reporter.item_processed(item.id)

            return result
```

### 4. Add Source Authentication Framework

- Create a framework for source authentication
- Support multiple authentication methods

```python
# domain/ingest/auth/auth_provider.py
class AuthProvider:
    """Provider for authentication credentials."""

    def __init__(self, registry):
        self._registry = registry
        self._auth_handlers = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default authentication handlers."""
        self._auth_handlers = {
            "basic": BasicAuthHandler(),
            "oauth": OAuthHandler(),
            "token": TokenAuthHandler(),
            "api_key": ApiKeyHandler(),
        }

    def register_handler(self, auth_type: str, handler):
        """Register a new authentication handler."""
        self._auth_handlers[auth_type] = handler

    async def get_credentials(self, source_id: str, auth_config: dict):
        """
        Get authentication credentials for a source.

        Args:
            source_id: ID of the source
            auth_config: Authentication configuration

        Returns:
            Authentication credentials for the source
        """
        auth_type = auth_config.get("type")
        if not auth_type or auth_type not in self._auth_handlers:
            raise ValueError(f"Unsupported authentication type: {auth_type}")

        handler = self._auth_handlers[auth_type]
        return await handler.get_credentials(source_id, auth_config)

class AuthHandler:
    """Base class for authentication handlers."""

    @abstractmethod
    async def get_credentials(self, source_id: str, auth_config: dict):
        """Get authentication credentials."""
        pass

class BasicAuthHandler(AuthHandler):
    """Handler for basic authentication."""

    async def get_credentials(self, source_id: str, auth_config: dict):
        """Get basic auth credentials."""
        username = auth_config.get("username")
        password = auth_config.get("password")

        # If password is a reference to secure storage, resolve it
        if password and password.startswith("secret:"):
            secret_name = password[7:]
            password = await self._get_secret(secret_name)

        return {
            "type": "basic",
            "username": username,
            "password": password
        }
```

### 5. Implement Resumable Operations

- Add support for checkpoint-based resumable operations
- Enable restart from last successful checkpoint

```python
# domain/ingest/checkpoint.py
class CheckpointManager:
    """Manager for operation checkpoints."""

    def __init__(self, data_dir: Path):
        self._checkpoint_dir = data_dir / "checkpoints"
        self._ensure_dir_exists()

    def _ensure_dir_exists(self):
        """Ensure the checkpoint directory exists."""
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    async def save_checkpoint(self, job_id: str, checkpoint_data: dict):
        """
        Save a checkpoint for a job.

        Args:
            job_id: ID of the job
            checkpoint_data: Checkpoint data to save
        """
        checkpoint_file = self._checkpoint_dir / f"{job_id}.json"

        # Add timestamp to checkpoint
        checkpoint_data["timestamp"] = datetime.now().isoformat()

        # Write checkpoint to file
        async with aiofiles.open(checkpoint_file, "w") as f:
            await f.write(json.dumps(checkpoint_data, indent=2))

    async def load_checkpoint(self, job_id: str):
        """
        Load the latest checkpoint for a job.

        Args:
            job_id: ID of the job

        Returns:
            Checkpoint data or None if no checkpoint exists
        """
        checkpoint_file = self._checkpoint_dir / f"{job_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            async with aiofiles.open(checkpoint_file, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading checkpoint for job {job_id}: {e}")
            return None

    async def clear_checkpoint(self, job_id: str):
        """
        Clear the checkpoint for a job.

        Args:
            job_id: ID of the job
        """
        checkpoint_file = self._checkpoint_dir / f"{job_id}.json"

        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
            except IOError as e:
                logger.error(f"Error clearing checkpoint for job {job_id}: {e}")
```

### 6. Enhance Content Validation

- Add comprehensive content validation framework
- Support schema-based validation and custom validators

```python
# domain/ingest/validation.py
class ContentValidator:
    """Validator for ingested content."""

    def __init__(self, registry):
        self._registry = registry
        self._validators = {}
        self._register_default_validators()

    def _register_default_validators(self):
        """Register default content validators."""
        self._validators = {
            ContentType.TEXT: TextContentValidator(),
            ContentType.JSON: JsonContentValidator(),
            ContentType.XML: XmlContentValidator(),
            ContentType.CSV: CsvContentValidator(),
        }

    def register_validator(self, content_type: ContentType, validator):
        """Register a validator for a content type."""
        self._validators[content_type] = validator

    async def validate(self, content: IngestContent, validation_options: dict = None):
        """
        Validate content.

        Args:
            content: Content to validate
            validation_options: Optional validation options

        Returns:
            Validation result with any errors or warnings
        """
        # Get appropriate validator
        validator = self._validators.get(content.content_type)
        if not validator:
            return ValidationResult(
                is_valid=False,
                errors=[f"No validator available for content type: {content.content_type}"]
            )

        # Perform validation
        return await validator.validate(content, validation_options or {})

class ValidationResult:
    """Result of content validation."""

    def __init__(self, is_valid: bool, errors=None, warnings=None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
```

### 7. Improve Job Management

- Enhance job lifecycle management
- Add support for job prioritization and scheduling

```python
# domain/ingest/job_manager.py
class JobManager:
    """Manager for ingest job lifecycle."""

    def __init__(self, registry):
        self._registry = registry
        self._jobs = {}
        self._job_queue = asyncio.PriorityQueue()
        self._running_jobs = set()
        self._max_concurrent_jobs = 3
        self._worker_task = None

    async def initialize(self):
        """Initialize the job manager."""
        # Start the worker task
        self._worker_task = asyncio.create_task(self._process_jobs())

    async def close(self):
        """Close the job manager."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def submit_job(self, job: IngestJob, priority: int = 0):
        """
        Submit a job for processing.

        Args:
            job: Job to submit
            priority: Priority (lower value means higher priority)
        """
        # Store job
        self._jobs[job.id] = job

        # Add to queue with priority
        await self._job_queue.put((priority, job.id))

        return job.id

    async def get_job_status(self, job_id: str):
        """
        Get the status of a job.

        Args:
            job_id: ID of the job

        Returns:
            Job status information
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        return {
            "id": job.id,
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "progress": job.progress,
            "source_id": job.source_id,
            "is_running": job_id in self._running_jobs
        }

    async def _process_jobs(self):
        """Process jobs from the queue."""
        while True:
            # Check if we can run more jobs
            if len(self._running_jobs) >= self._max_concurrent_jobs:
                await asyncio.sleep(1)
                continue

            try:
                # Get next job from queue
                priority, job_id = await self._job_queue.get()

                # Skip if job is no longer valid
                if job_id not in self._jobs:
                    self._job_queue.task_done()
                    continue

                # Run the job
                self._running_jobs.add(job_id)
                job = self._jobs[job_id]
                job.status = IngestStatus.PROCESSING

                # Start job processing
                asyncio.create_task(self._run_job(job))

                self._job_queue.task_done()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error processing job queue: {e}")
                await asyncio.sleep(1)

    async def _run_job(self, job: IngestJob):
        """Run a specific job."""
        try:
            # Get ingest manager
            ingest_manager = self._registry.ingest_manager

            # Run the job
            await ingest_manager.run_job(job)

            # Update job status
            job.status = IngestStatus.COMPLETED
            job.updated_at = datetime.now()

        except Exception as e:
            logger.error(f"Error running job {job.id}: {e}")
            job.status = IngestStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now()

        finally:
            # Remove from running jobs
            self._running_jobs.remove(job.id)
```

## Implementation Plan

### Phase 1: Error Handling & Validation (2 weeks)

1. Implement consistent error handling framework
2. Add content validation system
3. Enhance existing error handling

### Phase 2: Progress & Parallelism (2 weeks)

1. Implement progress reporting system
2. Add parallel processing capabilities
3. Optimize resource usage

### Phase 3: Authentication & Security (3 weeks)

1. Develop source authentication framework
2. Implement credential management
3. Add secure storage for sensitive information

### Phase 4: Job Management & Resumability (3 weeks)

1. Enhance job lifecycle management
2. Implement checkpoint-based resumability
3. Add job scheduling and prioritization

## Priority Matrix

| Improvement              | Impact | Effort | Priority |
| ------------------------ | :----: | :----: | :------: |
| Error Handling           |  High  |  Low   |    1     |
| Parallel Processing      |  High  | Medium |    2     |
| Progress Reporting       | Medium |  Low   |    3     |
| Content Validation       | Medium | Medium |    4     |
| Job Management           |  High  |  High  |    5     |
| Resumable Operations     | Medium |  High  |    6     |
| Authentication Framework | Medium |  High  |    7     |
