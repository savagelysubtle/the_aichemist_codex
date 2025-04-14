======================
Cross-Cutting Concerns
======================

The cross-cutting concerns layer contains functionality that spans multiple layers of the clean architecture, providing services that are used throughout the application.

Overview
========

Cross-cutting concerns are aspects of a system that affect multiple components and cannot be cleanly decomposed from the rest of the system. In The Aichemist Codex, these concerns are isolated in a dedicated layer to prevent them from being scattered throughout the codebase, which would lead to code duplication and maintenance challenges.

Components
==========

Caching
-------

Caching mechanisms to improve performance:

- **CacheProvider**: Interface for cache implementations
- **MemoryCache**: In-memory caching implementation
- **FileSystemCache**: File-based caching implementation
- **DistributedCache**: Distributed caching implementation

Example caching component:

.. code-block:: python

    class MemoryCache(ICacheProvider):
        def __init__(self, expiration_seconds: int = 300):
            self.cache = {}
            self.expiration_seconds = expiration_seconds
            self.timestamps = {}

        def get(self, key: str) -> Optional[Any]:
            """Get a value from the cache."""
            if key not in self.cache:
                return None

            # Check if the entry has expired
            timestamp = self.timestamps.get(key, 0)
            if time.time() - timestamp > self.expiration_seconds:
                self.delete(key)
                return None

            return self.cache[key]

        def set(self, key: str, value: Any, expiration_seconds: Optional[int] = None) -> None:
            """Set a value in the cache."""
            self.cache[key] = value
            self.timestamps[key] = time.time()

        def delete(self, key: str) -> None:
            """Delete a value from the cache."""
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]

        def clear(self) -> None:
            """Clear all values from the cache."""
            self.cache.clear()
            self.timestamps.clear()

Error Handling
-------------

Centralized error handling infrastructure:

- **ErrorHandler**: Central error handling service
- **ExceptionMapper**: Maps exceptions to appropriate responses
- **ErrorLogger**: Logs errors with appropriate context
- **ErrorNotifier**: Sends notifications for critical errors

Example error handling component:

.. code-block:: python

    class ErrorHandler:
        def __init__(self, logger: Logger, notifier: Optional[IErrorNotifier] = None):
            self.logger = logger
            self.notifier = notifier
            self.exception_mappers = {}

        def register_mapper(self, exception_type: Type[Exception], mapper: Callable[[Exception], Any]) -> None:
            """Register an exception mapper for a specific exception type."""
            self.exception_mappers[exception_type] = mapper

        def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
            """Handle an exception using the appropriate mapper."""
            context = context or {}

            # Log the exception
            self.logger.error(
                f"Error occurred: {str(exception)}",
                exc_info=exception,
                extra=context
            )

            # Notify if critical
            if self.notifier and self._is_critical(exception):
                self.notifier.notify(exception, context)

            # Find the appropriate mapper
            for exc_type, mapper in self.exception_mappers.items():
                if isinstance(exception, exc_type):
                    return mapper(exception)

            # Default handling if no mapper found
            return self._default_handler(exception)

        def _is_critical(self, exception: Exception) -> bool:
            """Determine if an exception is critical."""
            critical_types = (
                SystemError,
                MemoryError,
                ConnectionError,
                DatabaseError
            )
            return isinstance(exception, critical_types)

        def _default_handler(self, exception: Exception) -> Any:
            """Default exception handler."""
            # Re-raise by default
            raise exception

Security
-------

Security mechanisms:

- **AuthenticationService**: Handles user authentication
- **AuthorizationService**: Manages access control
- **EncryptionService**: Provides encryption capabilities
- **SecureConfigProvider**: Manages secure configuration values

Example security component:

.. code-block:: python

    class EncryptionService:
        def __init__(self, key_provider: IKeyProvider):
            self.key_provider = key_provider
            self.fernet = None
            self._initialize()

        def _initialize(self) -> None:
            """Initialize the encryption service."""
            key = self.key_provider.get_key()
            self.fernet = Fernet(key)

        def encrypt(self, data: Union[str, bytes]) -> bytes:
            """Encrypt data."""
            if isinstance(data, str):
                data = data.encode('utf-8')

            return self.fernet.encrypt(data)

        def decrypt(self, data: bytes) -> bytes:
            """Decrypt data."""
            return self.fernet.decrypt(data)

        def encrypt_file(self, input_path: Path, output_path: Path) -> None:
            """Encrypt a file."""
            with open(input_path, 'rb') as f:
                data = f.read()

            encrypted_data = self.encrypt(data)

            with open(output_path, 'wb') as f:
                f.write(encrypted_data)

        def decrypt_file(self, input_path: Path, output_path: Path) -> None:
            """Decrypt a file."""
            with open(input_path, 'rb') as f:
                data = f.read()

            decrypted_data = self.decrypt(data)

            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

Telemetry
--------

Telemetry infrastructure:

- **LoggingService**: Centralized logging
- **MetricsCollector**: Collects application metrics
- **TracingProvider**: Implements distributed tracing
- **HealthMonitor**: Monitors application health

Example telemetry component:

.. code-block:: python

    class MetricsCollector:
        def __init__(self, metrics_provider: IMetricsProvider):
            self.provider = metrics_provider
            self.counters = {}
            self.gauges = {}
            self.histograms = {}

        def counter(self, name: str, description: str) -> Counter:
            """Get or create a counter metric."""
            if name not in self.counters:
                self.counters[name] = self.provider.create_counter(name, description)

            return self.counters[name]

        def gauge(self, name: str, description: str) -> Gauge:
            """Get or create a gauge metric."""
            if name not in self.gauges:
                self.gauges[name] = self.provider.create_gauge(name, description)

            return self.gauges[name]

        def histogram(self, name: str, description: str, buckets: Optional[List[float]] = None) -> Histogram:
            """Get or create a histogram metric."""
            if name not in self.histograms:
                self.histograms[name] = self.provider.create_histogram(name, description, buckets)

            return self.histograms[name]

        def record_operation_duration(self, operation_name: str, duration_seconds: float) -> None:
            """Record the duration of an operation."""
            histogram = self.histogram(
                f"{operation_name}_duration_seconds",
                f"Duration of {operation_name} operation in seconds"
            )
            histogram.observe(duration_seconds)

        def increment_operation_count(self, operation_name: str, labels: Optional[Dict[str, str]] = None) -> None:
            """Increment the count of an operation."""
            counter = self.counter(
                f"{operation_name}_total",
                f"Total number of {operation_name} operations"
            )
            counter.inc(labels or {})

Validation
---------

Validation mechanisms:

- **ValidationService**: Centralized validation service
- **Validator**: Base class for validators
- **ValidationRule**: Interface for validation rules
- **ValidationResult**: Represents validation results

Example validation component:

.. code-block:: python

    class ValidationService:
        def __init__(self):
            self.validators = {}

        def register_validator(self, object_type: Type, validator: IValidator) -> None:
            """Register a validator for a specific object type."""
            self.validators[object_type] = validator

        def validate(self, obj: Any) -> ValidationResult:
            """Validate an object using the appropriate validator."""
            object_type = type(obj)

            # Find the appropriate validator
            validator = self._find_validator(object_type)
            if not validator:
                return ValidationResult(is_valid=True, errors=[])

            # Validate the object
            return validator.validate(obj)

        def _find_validator(self, object_type: Type) -> Optional[IValidator]:
            """Find a validator for the given object type."""
            # Check for exact match
            if object_type in self.validators:
                return self.validators[object_type]

            # Check for parent classes
            for cls in object_type.__mro__[1:]:
                if cls in self.validators:
                    return self.validators[cls]

            return None

Workflows
--------

Workflow orchestration:

- **WorkflowEngine**: Orchestrates complex workflows
- **WorkflowStep**: Represents a step in a workflow
- **WorkflowContext**: Contains workflow state
- **WorkflowResult**: Represents workflow results

Example workflow component:

.. code-block:: python

    class WorkflowEngine:
        def __init__(self, logger: Logger):
            self.logger = logger
            self.workflows = {}

        def register_workflow(self, name: str, steps: List[IWorkflowStep]) -> None:
            """Register a workflow with the given name and steps."""
            self.workflows[name] = steps

        async def execute_workflow(self, name: str, context: Dict[str, Any]) -> WorkflowResult:
            """Execute a workflow with the given name and context."""
            if name not in self.workflows:
                raise ValueError(f"Workflow '{name}' not found")

            steps = self.workflows[name]
            workflow_context = WorkflowContext(context)

            try:
                for step in steps:
                    self.logger.info(f"Executing workflow step: {step.__class__.__name__}")
                    await step.execute(workflow_context)

                    if workflow_context.should_stop:
                        self.logger.info(f"Workflow '{name}' stopped early at step: {step.__class__.__name__}")
                        break

                return WorkflowResult(
                    success=True,
                    context=workflow_context.data,
                    error=None
                )

            except Exception as e:
                self.logger.error(f"Error executing workflow '{name}': {str(e)}", exc_info=e)
                return WorkflowResult(
                    success=False,
                    context=workflow_context.data,
                    error=str(e)
                )

Design Patterns in the Cross-Cutting Concerns Layer
=================================================

The cross-cutting concerns layer implements several design patterns:

- **Decorator Pattern**: Add functionality to components transparently
- **Strategy Pattern**: Flexible algorithms for different concerns
- **Chain of Responsibility**: Process requests through a chain of handlers
- **Observer Pattern**: Notify components about events
- **Singleton Pattern**: Ensure a single instance of a service
- **Proxy Pattern**: Control access to resources

Cross-Cutting Concerns Layer Rules
================================

1. Provides services that span multiple layers
2. Implements concerns that would otherwise be duplicated
3. Maintains separation of concerns
4. Follows the dependency rule (depends only on inner layers)
5. Uses dependency injection for flexibility
6. Provides clear interfaces for other layers to use
