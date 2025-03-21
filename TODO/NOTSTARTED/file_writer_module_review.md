# File Writer Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The file_writer module is responsible for writing data to files in different
formats. The key components include:

- **FileWriterImpl**: Main implementation of the FileWriter interface
- Key functionalities:
  - Writing text and binary data to files
  - Serializing and writing JSON and YAML data
  - Appending text to existing files
  - Path safety validation through FileValidator

## Architectural Compliance

The file_writer module demonstrates good alignment with the project's
architectural guidelines:

| Architectural Principle    | Status | Notes                                                                            |
| -------------------------- | :----: | -------------------------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the domain layer                                          |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection and service access                        |
| **Interface-Based Design** |   ✅   | FileWriterImpl properly implements the FileWriter interface                      |
| **Import Strategy**        |   ✅   | Uses absolute imports for core interfaces and relative imports for local modules |
| **Asynchronous Design**    |   ✅   | Methods consistently use async/await patterns                                    |
| **Error Handling**         |   ✅   | Uses specialized FileError with context                                          |
| **Path Safety**            |   ✅   | Implements path validation using FileValidator                                   |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                    | Status | Issue                                               |
| ----------------------- | :----: | --------------------------------------------------- |
| **Format Extension**    |   🔄   | Limited support for specialized file formats        |
| **Atomic Operations**   |   ❌   | No support for atomic file operations               |
| **Transaction Support** |   ❌   | Lacks transactional writing capabilities            |
| **Compression**         |   ❌   | No built-in support for compressed formats          |
| **Write Verification**  |   ⚠️   | Missing verification after write operations         |
| **Progress Reporting**  |   ❌   | No mechanism for reporting progress on large writes |
| **Template Support**    |   ⚠️   | No support for template-based file generation       |

## Recommendations

### 1. Implement Extensible Format System

- Create a plugin system for format handlers
- Allow registration of custom format writers

```python
# domain/file_writer/format_handlers.py
class FormatHandler:
    """Base class for file format handlers."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Get format name."""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Get supported file extensions."""
        pass

    @abstractmethod
    async def serialize(self, data: Any, options: dict = None) -> str:
        """Serialize data to string."""
        pass

    @abstractmethod
    async def write(self, file_path: str, data: Any, options: dict = None) -> None:
        """Write data to file."""
        pass

# Concrete handlers
class XmlFormatHandler(FormatHandler):
    """Handler for XML format."""

    @property
    def format_name(self) -> str:
        return "xml"

    @property
    def file_extensions(self) -> list[str]:
        return [".xml"]

    async def serialize(self, data: Any, options: dict = None) -> str:
        """Serialize data to XML."""
        options = options or {}
        try:
            import dicttoxml
            xml_data = dicttoxml.dicttoxml(
                data,
                custom_root=options.get("root", "root"),
                attr_type=options.get("attr_type", False)
            )
            return xml_data.decode('utf-8')
        except ImportError:
            raise ImportError("dicttoxml package is required for XML serialization")

    async def write(self, file_path: str, data: Any, options: dict = None) -> None:
        """Write data as XML to file."""
        xml_content = await self.serialize(data, options)
        file_writer = Registry.get_instance().file_writer
        await file_writer.write_text(file_path, xml_content)

# In FileWriterImpl
def register_format_handler(self, handler: FormatHandler) -> None:
    """Register a format handler."""
    self._format_handlers[handler.format_name] = handler
    for ext in handler.file_extensions:
        self._extension_handlers[ext] = handler.format_name

async def write_format(self, file_path: str, data: Any, format_name: str = None, options: dict = None) -> None:
    """
    Write data using a specific format handler.

    Args:
        file_path: Path to file
        data: Data to write
        format_name: Name of format to use, or None to detect from extension
        options: Format-specific options
    """
    if not format_name:
        # Detect format from file extension
        ext = os.path.splitext(file_path)[1].lower()
        format_name = self._extension_handlers.get(ext)
        if not format_name:
            raise FileError(f"Unsupported file extension: {ext}", file_path)

    # Get handler for the format
    handler = self._format_handlers.get(format_name)
    if not handler:
        raise FileError(f"Unsupported format: {format_name}", file_path)

    # Use handler to write data
    await handler.write(file_path, data, options)
```

### 2. Add Atomic File Operations

- Implement atomic write operations for data safety
- Use temporary files and atomic rename

```python
# domain/file_writer/atomic.py
class AtomicFileWriter:
    """Writer for atomic file operations."""

    def __init__(self, registry):
        self._registry = registry
        self._validator = registry.file_validator
        self._paths = registry.project_paths

    async def write_atomic(self, file_path: str, content: str | bytes, is_binary: bool = False) -> None:
        """
        Write content to a file atomically.

        Args:
            file_path: Path to the file
            content: Content to write
            is_binary: Whether content is binary

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(file_path)
        path_str = str(path_obj)

        # Create temporary file in the same directory
        import tempfile
        import os
        import shutil

        directory = os.path.dirname(path_str)
        if directory:
            os.makedirs(directory, exist_ok=True)

        try:
            # Create a temporary file
            fd, temp_path = tempfile.mkstemp(dir=directory)

            try:
                # Write content to temporary file
                with os.fdopen(fd, 'wb' if is_binary else 'w') as f:
                    if is_binary:
                        f.write(content)
                    else:
                        f.write(content)

                # Make sure content is flushed to disk
                os.fsync(fd)

                # Atomic replace (this is atomic on most platforms)
                if os.name == 'nt':  # Windows
                    # Windows needs special handling
                    if os.path.exists(path_str):
                        os.replace(temp_path, path_str)
                    else:
                        os.rename(temp_path, path_str)
                else:
                    # Unix-like systems
                    os.rename(temp_path, path_str)

            except Exception as e:
                # Clean up temporary file in case of error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise FileError(f"Failed to write file atomically: {str(e)}", file_path)

        except Exception as e:
            raise FileError(f"Failed to create temporary file: {str(e)}", file_path)

# In FileWriterImpl
async def write_text_atomic(self, file_path: str, content: str) -> None:
    """
    Write text to a file atomically.

    Args:
        file_path: Path to the file
        content: Text content to write
    """
    atomic_writer = AtomicFileWriter(self._registry)
    await atomic_writer.write_atomic(file_path, content, is_binary=False)

async def write_binary_atomic(self, file_path: str, content: bytes) -> None:
    """
    Write binary data to a file atomically.

    Args:
        file_path: Path to the file
        content: Binary content to write
    """
    atomic_writer = AtomicFileWriter(self._registry)
    await atomic_writer.write_atomic(file_path, content, is_binary=True)
```

### 3. Implement Transaction Support

- Add transaction-like operations for multiple file writes
- Support rollback and commitment

```python
# domain/file_writer/transaction.py
class FileTransaction:
    """Transaction for multiple file operations."""

    def __init__(self, registry):
        self._registry = registry
        self._validator = registry.file_validator
        self._file_writer = registry.file_writer
        self._operations = []
        self._executed = []
        self._committed = False
        self._rolledback = False

    async def write_text(self, file_path: str, content: str) -> None:
        """Add a text write operation to the transaction."""
        self._operations.append(("write_text", file_path, content))

    async def write_binary(self, file_path: str, content: bytes) -> None:
        """Add a binary write operation to the transaction."""
        self._operations.append(("write_binary", file_path, content))

    async def write_json(self, file_path: str, data: Any) -> None:
        """Add a JSON write operation to the transaction."""
        self._operations.append(("write_json", file_path, data))

    async def write_yaml(self, file_path: str, data: Any) -> None:
        """Add a YAML write operation to the transaction."""
        self._operations.append(("write_yaml", file_path, data))

    async def delete_file(self, file_path: str) -> None:
        """Add a file deletion operation to the transaction."""
        self._operations.append(("delete", file_path))

    async def commit(self) -> None:
        """
        Commit all operations in the transaction.

        This executes all operations and marks the transaction as committed.
        If any operation fails, all completed operations are rolled back.
        """
        if self._committed or self._rolledback:
            raise ValueError("Transaction already committed or rolled back")

        try:
            # Execute all operations
            for op in self._operations:
                op_type = op[0]
                file_path = op[1]

                if op_type == "write_text":
                    await self._file_writer.write_text(file_path, op[2])
                elif op_type == "write_binary":
                    await self._file_writer.write_binary(file_path, op[2])
                elif op_type == "write_json":
                    await self._file_writer.write_json(file_path, op[2])
                elif op_type == "write_yaml":
                    await self._file_writer.write_yaml(file_path, op[2])
                elif op_type == "delete":
                    await self._registry.file_system_service.delete_file(file_path)

                self._executed.append(op)

            self._committed = True

        except Exception as e:
            # Roll back completed operations
            await self.rollback()
            raise FileError(f"Transaction failed: {str(e)}")

    async def rollback(self) -> None:
        """
        Roll back all executed operations.

        This attempts to restore the file system to its state before the transaction.
        """
        if self._committed:
            raise ValueError("Cannot roll back committed transaction")

        if self._rolledback:
            return  # Already rolled back

        # Try to roll back each executed operation
        for op in reversed(self._executed):
            op_type = op[0]
            file_path = op[1]

            try:
                if op_type == "delete":
                    # If we deleted a file, we might not be able to restore it
                    pass
                else:
                    # For write operations, check if file existed before
                    backup_path = f"{file_path}.bak"
                    if self._registry.file_system_service.file_exists(backup_path):
                        # Restore from backup
                        await self._registry.file_system_service.copy_file(backup_path, file_path)
                        await self._registry.file_system_service.delete_file(backup_path)
                    else:
                        # File didn't exist before, delete it
                        await self._registry.file_system_service.delete_file(file_path)
            except Exception:
                # Just log errors during rollback, don't raise
                import logging
                logging.getLogger(__name__).error(
                    f"Error rolling back operation {op_type} for {file_path}"
                )

        self._rolledback = True
```

### 4. Add Compression Support

- Implement support for writing compressed files
- Support multiple compression formats

```python
# domain/file_writer/compression.py
class CompressionHandler:
    """Handler for file compression."""

    def __init__(self, registry):
        self._registry = registry
        self._compressors = {
            "gzip": self._compress_gzip,
            "zip": self._compress_zip,
            "bz2": self._compress_bz2,
            "lzma": self._compress_lzma,
        }

    async def write_compressed(
        self, file_path: str, content: bytes, format: str = "gzip", level: int = 9
    ) -> None:
        """
        Write compressed content to a file.

        Args:
            file_path: Path to the file
            content: Content to compress and write
            format: Compression format (gzip, zip, bz2, lzma)
            level: Compression level (1-9, where 9 is highest)

        Raises:
            FileError: If compression or writing fails
            ValueError: If format is not supported
        """
        compressor = self._compressors.get(format.lower())
        if not compressor:
            raise ValueError(f"Unsupported compression format: {format}")

        try:
            # Compress the content
            compressed_data = await compressor(content, level)

            # Write the compressed data
            await self._registry.file_writer.write_binary(file_path, compressed_data)

        except Exception as e:
            raise FileError(f"Failed to write compressed file: {str(e)}", file_path)

    async def _compress_gzip(self, content: bytes, level: int) -> bytes:
        """Compress data using gzip."""
        import gzip
        return gzip.compress(content, level)

    async def _compress_zip(self, content: bytes, level: int) -> bytes:
        """Compress data using zip."""
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, 'w',
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=level
        ) as zip_file:
            zip_file.writestr("content", content)

        return zip_buffer.getvalue()

    async def _compress_bz2(self, content: bytes, level: int) -> bytes:
        """Compress data using bz2."""
        import bz2
        return bz2.compress(content, level)

    async def _compress_lzma(self, content: bytes, level: int) -> bytes:
        """Compress data using lzma."""
        import lzma
        return lzma.compress(content, preset=level)
```

### 5. Implement Write Verification

- Add verification steps after write operations
- Ensure data integrity

```python
# domain/file_writer/verification.py
class WriteVerifier:
    """Verifier for write operations."""

    def __init__(self, registry):
        self._registry = registry
        self._file_reader = registry.file_reader

    async def verify_text_write(self, file_path: str, expected_content: str) -> bool:
        """
        Verify a text write operation.

        Args:
            file_path: Path to the file
            expected_content: Expected content

        Returns:
            True if verification passed, False otherwise
        """
        try:
            # Read the file
            actual_content = await self._file_reader.read_text(file_path)

            # Compare content
            return actual_content == expected_content

        except Exception:
            return False

    async def verify_binary_write(self, file_path: str, expected_content: bytes) -> bool:
        """
        Verify a binary write operation.

        Args:
            file_path: Path to the file
            expected_content: Expected content

        Returns:
            True if verification passed, False otherwise
        """
        try:
            # Read the file
            actual_content = await self._file_reader.read_binary(file_path)

            # Compare content
            return actual_content == expected_content

        except Exception:
            return False

    async def verify_json_write(self, file_path: str, expected_data: Any) -> bool:
        """
        Verify a JSON write operation.

        Args:
            file_path: Path to the file
            expected_data: Expected data

        Returns:
            True if verification passed, False otherwise
        """
        try:
            # Read the file
            actual_data = await self._file_reader.read_json(file_path)

            # Compare data (convert to strings for comparison)
            import json
            expected_json = json.dumps(expected_data, sort_keys=True)
            actual_json = json.dumps(actual_data, sort_keys=True)

            return expected_json == actual_json

        except Exception:
            return False

# In FileWriterImpl
async def write_text_verified(self, file_path: str, content: str) -> bool:
    """
    Write text to a file and verify the write.

    Args:
        file_path: Path to the file
        content: Text content to write

    Returns:
        True if write and verification succeeded
    """
    await self.write_text(file_path, content)
    verifier = WriteVerifier(self._registry)
    return await verifier.verify_text_write(file_path, content)
```

### 6. Add Progress Reporting for Large Writes

- Implement progress reporting for large file writes
- Support cancellation of write operations

```python
# domain/file_writer/progress.py
class WriteProgressReporter:
    """Reporter for write operation progress."""

    def __init__(self, callback=None):
        self.callback = callback
        self.total_bytes = 0
        self.written_bytes = 0
        self.start_time = None
        self.last_update_time = None
        self.cancelled = False

    def reset(self, total_bytes: int):
        """Reset the progress reporter for a new operation."""
        self.total_bytes = total_bytes
        self.written_bytes = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.cancelled = False

    def update(self, bytes_written: int) -> bool:
        """
        Update progress and check if operation is cancelled.

        Args:
            bytes_written: Number of bytes written in this update

        Returns:
            False if operation was cancelled, True otherwise
        """
        if self.cancelled:
            return False

        self.written_bytes += bytes_written
        current_time = time.time()

        # Report progress at most every 100ms
        if self.callback and (current_time - self.last_update_time) >= 0.1:
            progress = {
                "total_bytes": self.total_bytes,
                "written_bytes": self.written_bytes,
                "percentage": (self.written_bytes / max(1, self.total_bytes)) * 100,
                "elapsed_seconds": current_time - self.start_time,
                "bytes_per_second": self.written_bytes / max(0.001, current_time - self.start_time),
            }

            try:
                result = self.callback(progress)
                # If callback returns False, cancel the operation
                if result is False:
                    self.cancelled = True
                    return False
            except Exception:
                # Ignore callback errors
                pass

            self.last_update_time = current_time

        return True

    def complete(self):
        """Mark the operation as complete."""
        if self.callback:
            progress = {
                "total_bytes": self.total_bytes,
                "written_bytes": self.written_bytes,
                "percentage": 100,
                "elapsed_seconds": time.time() - self.start_time,
                "bytes_per_second": self.written_bytes / max(0.001, time.time() - self.start_time),
                "completed": True
            }

            try:
                self.callback(progress)
            except Exception:
                # Ignore callback errors
                pass

# In FileWriterImpl
async def write_binary_with_progress(
    self, file_path: str, content: bytes, progress_callback=None
) -> bool:
    """
    Write binary data with progress reporting.

    Args:
        file_path: Path to the file
        content: Binary content to write
        progress_callback: Optional callback for progress reporting

    Returns:
        True if write completed, False if cancelled
    """
    # Validate path safety
    self._validator.ensure_path_safe(file_path)

    # Create progress reporter
    reporter = WriteProgressReporter(progress_callback)
    reporter.reset(len(content))

    # Ensure the directory exists
    path_obj = self._paths.resolve_path(file_path)
    directory = os.path.dirname(str(path_obj))
    if directory:
        os.makedirs(directory, exist_ok=True)

    try:
        # Write in chunks to allow progress reporting
        chunk_size = 65536  # 64KB chunks
        with open(path_obj, "wb") as f:
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                f.write(chunk)

                # Update progress and check for cancellation
                if not reporter.update(len(chunk)):
                    return False  # Operation was cancelled

        # Mark as complete
        reporter.complete()
        return True

    except Exception as e:
        raise FileError(f"Failed to write binary file: {str(e)}", file_path)
```

### 7. Add Template Support

- Implement template-based file generation
- Support multiple template engines

```python
# domain/file_writer/templates.py
class TemplateEngine:
    """Base class for template engines."""

    @abstractmethod
    async def render(self, template: str, context: dict) -> str:
        """
        Render a template with context.

        Args:
            template: Template string
            context: Context data for rendering

        Returns:
            Rendered string
        """
        pass

class JinjaTemplateEngine(TemplateEngine):
    """Template engine using Jinja2."""

    def __init__(self):
        try:
            import jinja2
            self._jinja_env = jinja2.Environment(
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
        except ImportError:
            raise ImportError("jinja2 package is required for Jinja templates")

    async def render(self, template: str, context: dict) -> str:
        """Render template using Jinja2."""
        template_obj = self._jinja_env.from_string(template)
        return template_obj.render(**context)

class TemplateManager:
    """Manager for template-based file generation."""

    def __init__(self, registry):
        self._registry = registry
        self._file_writer = registry.file_writer
        self._engines = {
            "jinja": JinjaTemplateEngine(),
            "simple": SimpleTemplateEngine(),
        }

    def register_engine(self, name: str, engine: TemplateEngine) -> None:
        """Register a template engine."""
        self._engines[name] = engine

    async def render_template(
        self, template: str, context: dict, engine_name: str = "jinja"
    ) -> str:
        """
        Render a template with context.

        Args:
            template: Template string
            context: Context data for rendering
            engine_name: Name of template engine to use

        Returns:
            Rendered string
        """
        engine = self._engines.get(engine_name)
        if not engine:
            raise ValueError(f"Unknown template engine: {engine_name}")

        return await engine.render(template, context)

    async def write_template(
        self, file_path: str, template: str, context: dict, engine_name: str = "jinja"
    ) -> None:
        """
        Render a template and write to a file.

        Args:
            file_path: Path to output file
            template: Template string
            context: Context data for rendering
            engine_name: Name of template engine to use
        """
        # Render the template
        rendered = await self.render_template(template, context, engine_name)

        # Write the rendered content
        await self._file_writer.write_text(file_path, rendered)

    async def write_template_file(
        self, template_file: str, output_file: str, context: dict, engine_name: str = "jinja"
    ) -> None:
        """
        Render a template file and write to an output file.

        Args:
            template_file: Path to template file
            output_file: Path to output file
            context: Context data for rendering
            engine_name: Name of template engine to use
        """
        # Read the template file
        file_reader = self._registry.file_reader
        template = await file_reader.read_text(template_file)

        # Render and write
        await self.write_template(output_file, template, context, engine_name)
```

## Implementation Plan

### Phase 1: Core Enhancements (2 weeks)

1. Implement extensible format system
2. Add atomic file operations
3. Implement write verification

### Phase 2: Advanced Features (3 weeks)

1. Add transaction support
2. Implement compression support
3. Add progress reporting for large writes

### Phase 3: Template System (2 weeks)

1. Design and implement template engine abstraction
2. Add Jinja2 template support
3. Create template manager

### Phase 4: Integration & Testing (1 week)

1. Integrate with other modules
2. Add comprehensive tests
3. Document new capabilities

## Priority Matrix

| Improvement              | Impact | Effort | Priority |
| ------------------------ | :----: | :----: | :------: |
| Atomic Operations        |  High  |  Low   |    1     |
| Write Verification       |  High  |  Low   |    2     |
| Transaction Support      |  High  | Medium |    3     |
| Extensible Format System | Medium | Medium |    4     |
| Compression Support      | Medium | Medium |    5     |
| Progress Reporting       |  Low   |  Low   |    6     |
| Template Support         | Medium |  High  |    7     |
