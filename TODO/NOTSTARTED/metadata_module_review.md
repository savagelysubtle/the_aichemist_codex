# Metadata Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The metadata module is responsible for extracting metadata and content from
various file types. The key components include:

- **MetadataManager**: Central manager that coordinates metadata extraction from
  different file types
- **Extractor**: Abstract base class defining the interface for all metadata
  extractors
- **Specialized Extractors**:
  - TextExtractor: For text files
  - PdfExtractor: For PDF documents
  - ImageExtractor: For image files
  - AudioExtractor: For audio files
  - VideoExtractor: For video files
  - CodeExtractor: For source code files
  - DocumentExtractor: For office documents

Key functionalities:

- Metadata extraction from various file types
- Content extraction for indexing and search
- Preview generation for displaying file snippets
- Support for multiple file formats through specialized extractors
- MIME type and extension-based file handling

## Architectural Compliance

The metadata module demonstrates good alignment with the project's architectural
guidelines:

| Architectural Principle    | Status | Notes                                                      |
| -------------------------- | :----: | ---------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the domain layer                    |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection                     |
| **Interface-Based Design** |   ✅   | Uses abstract base class for all extractors                |
| **Extensibility**          |   ✅   | Easily extensible with new extractors via registration     |
| **Separation of Concerns** |   ✅   | Clear separation between manager and individual extractors |
| **Error Handling**         |   ✅   | Specialized exception types for metadata operations        |
| **Logging**                |   ✅   | Consistent logging throughout the module                   |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                            | Status | Issue                                                  |
| ------------------------------- | :----: | ------------------------------------------------------ |
| **Async Support**               |   ❌   | No async methods for potentially blocking I/O          |
| **Caching**                     |   ❌   | No caching mechanism for extracted metadata            |
| **Performance Optimization**    |   ⚠️   | Some extractors may be inefficient with large files    |
| **Dependency Management**       |   ⚠️   | External library dependencies not explicitly managed   |
| **Metadata Enrichment**         |   ❌   | No post-processing or enrichment of extracted metadata |
| **Extract Configuration**       |   ⚠️   | Limited configuration options for extraction behavior  |
| **Structured Content Handling** |   ⚠️   | Limited handling of structured content extraction      |

## Recommendations

### 1. Implement Async Support

- Refactor core operations to use async/await patterns
- Enable parallel metadata extraction

```python
# domain/metadata/extractor.py
class Extractor(ABC):
    # ... existing code ...

    @abstractmethod
    async def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from the given file asynchronously."""
        pass

    @abstractmethod
    async def extract_content(self, file_path: str) -> str:
        """Extract textual content from the given file asynchronously."""
        pass

    @abstractmethod
    async def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a textual preview of the file content asynchronously."""
        pass

# domain/metadata/metadata_manager.py
class MetadataManager:
    # ... existing code ...

    async def extract_metadata(
        self, file_path: str, mime_type: str | None = None
    ) -> dict[str, Any]:
        """Extract metadata from the given file asynchronously."""
        if not self._initialized:
            self.initialize()

        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            return await extractor.extract_metadata(file_path)
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e
```

### 2. Add Metadata Caching

- Implement caching for extracted metadata to improve performance
- Use file modification time for cache invalidation

```python
# domain/metadata/cache.py
class MetadataCache:
    """Cache for extracted metadata."""

    def __init__(self, max_size: int = 1000):
        """Initialize the metadata cache.

        Args:
            max_size: Maximum number of entries in the cache
        """
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._max_size = max_size

    async def get(self, file_path: str) -> dict[str, Any] | None:
        """Get metadata from the cache if it exists and is valid.

        Args:
            file_path: Path to the file

        Returns:
            Cached metadata, or None if not in cache or invalid
        """
        if file_path not in self._cache:
            return None

        # Get cached timestamp and metadata
        cached_mtime, metadata = self._cache[file_path]

        # Check if file has been modified
        try:
            current_mtime = os.path.getmtime(file_path)
            if current_mtime > cached_mtime:
                # File has been modified, invalidate cache
                del self._cache[file_path]
                return None
            return metadata
        except OSError:
            # File might not exist anymore
            del self._cache[file_path]
            return None

    async def put(self, file_path: str, metadata: dict[str, Any]) -> None:
        """Store metadata in the cache.

        Args:
            file_path: Path to the file
            metadata: Extracted metadata
        """
        try:
            # Get file modification time
            mtime = os.path.getmtime(file_path)

            # If cache is full, remove oldest entry
            if len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            # Store in cache
            self._cache[file_path] = (mtime, metadata)
        except OSError:
            # Ignore if file doesn't exist
            pass

# In MetadataManager
class MetadataManager:
    def __init__(self, registry: Registry):
        # ... existing initialization ...
        self._cache = MetadataCache()

    async def extract_metadata(
        self, file_path: str, mime_type: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Extract metadata from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file
            use_cache: Whether to use cached metadata if available

        Returns:
            Dictionary containing the extracted metadata
        """
        if not self._initialized:
            self.initialize()

        # Try to get from cache if caching is enabled
        if use_cache:
            cached_metadata = await self._cache.get(file_path)
            if cached_metadata is not None:
                return cached_metadata

        # Extract metadata using the appropriate extractor
        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            metadata = await extractor.extract_metadata(file_path)

            # Store in cache if caching is enabled
            if use_cache:
                await self._cache.put(file_path, metadata)

            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e
```

### 3. Implement Dependency Management

- Create an explicit dependency management system for external libraries
- Handle missing dependencies gracefully

```python
# domain/metadata/dependencies.py
class DependencyManager:
    """Manager for external dependencies used by extractors."""

    def __init__(self):
        self._dependencies: dict[str, bool] = {}
        self._optional_dependencies: set[str] = set()

    def register_dependency(self, name: str, optional: bool = False) -> None:
        """Register a dependency.

        Args:
            name: Name of the dependency package
            optional: Whether the dependency is optional
        """
        if optional:
            self._optional_dependencies.add(name)
        self._check_dependency(name)

    def _check_dependency(self, name: str) -> None:
        """Check if a dependency is installed.

        Args:
            name: Name of the dependency package
        """
        try:
            __import__(name)
            self._dependencies[name] = True
        except ImportError:
            self._dependencies[name] = False
            if name not in self._optional_dependencies:
                logger.warning(f"Required dependency '{name}' is not installed")
            else:
                logger.info(f"Optional dependency '{name}' is not installed")

    def is_available(self, name: str) -> bool:
        """Check if a dependency is available.

        Args:
            name: Name of the dependency package

        Returns:
            True if the dependency is available, False otherwise
        """
        if name not in self._dependencies:
            self._check_dependency(name)
        return self._dependencies[name]

    def get_missing_dependencies(self) -> list[str]:
        """Get a list of missing dependencies.

        Returns:
            List of names of missing dependencies
        """
        return [name for name, available in self._dependencies.items()
                if not available and name not in self._optional_dependencies]

# In each extractor that uses external dependencies:
class PdfExtractor(Extractor):
    def __init__(self, dependency_manager: DependencyManager):
        super().__init__()
        self._dependency_manager = dependency_manager
        self._dependency_manager.register_dependency("pypdf", optional=False)
        self._dependency_manager.register_dependency("pdf2image", optional=True)

        # Set supported formats
        self._supported_extensions = {".pdf"}
        self._supported_mime_types = {"application/pdf"}

    async def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from PDF files."""
        if not self._dependency_manager.is_available("pypdf"):
            raise ImportError("The 'pypdf' package is required for PDF extraction")

        # Extract PDF metadata using pypdf
        # ...
```

### 4. Add Metadata Enrichment Pipeline

- Implement a pipeline for post-processing extracted metadata
- Add support for custom enrichers

```python
# domain/metadata/enrichers.py
class MetadataEnricher(ABC):
    """Base class for metadata enrichers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the enricher."""
        pass

    @abstractmethod
    async def enrich(self, metadata: dict[str, Any], file_path: str) -> dict[str, Any]:
        """Enrich the metadata.

        Args:
            metadata: Original metadata
            file_path: Path to the file

        Returns:
            Enriched metadata
        """
        pass

class GeolocationEnricher(MetadataEnricher):
    """Enricher for adding geolocation data to metadata."""

    @property
    def name(self) -> str:
        return "geolocation"

    async def enrich(self, metadata: dict[str, Any], file_path: str) -> dict[str, Any]:
        """Add geolocation data to metadata if GPS coordinates exist."""
        # Check if metadata contains GPS coordinates
        if "gps_latitude" in metadata and "gps_longitude" in metadata:
            try:
                # Get location data from coordinates
                lat = metadata["gps_latitude"]
                lon = metadata["gps_longitude"]

                # Use a geocoding service to get location information
                # This is just a placeholder for the actual implementation
                location_data = await self._get_location_data(lat, lon)

                # Add location data to metadata
                metadata["location"] = location_data
            except Exception as e:
                logger.warning(f"Failed to enrich geolocation data: {str(e)}")

        return metadata

    async def _get_location_data(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Get location data from coordinates."""
        # Implement with appropriate geocoding service
        pass

# In MetadataManager
class MetadataManager:
    def __init__(self, registry: Registry):
        # ... existing initialization ...
        self._enrichers: dict[str, MetadataEnricher] = {}

    def register_enricher(self, enricher: MetadataEnricher) -> None:
        """Register a metadata enricher.

        Args:
            enricher: The enricher to register
        """
        if not self._initialized:
            self.initialize()

        self._enrichers[enricher.name] = enricher
        logger.debug(f"Registered metadata enricher: {enricher.name}")

    async def extract_metadata_enriched(
        self, file_path: str, mime_type: str | None = None,
        enrichers: list[str] | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Extract and enrich metadata from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file
            enrichers: Names of enrichers to apply, or None for all
            use_cache: Whether to use cached metadata if available

        Returns:
            Dictionary containing the extracted and enriched metadata
        """
        # Extract base metadata
        metadata = await self.extract_metadata(file_path, mime_type, use_cache)

        # Apply enrichers
        if enrichers is None:
            # Use all registered enrichers
            enricher_list = list(self._enrichers.values())
        else:
            # Use specified enrichers
            enricher_list = [
                self._enrichers[name] for name in enrichers
                if name in self._enrichers
            ]

        # Apply each enricher in sequence
        for enricher in enricher_list:
            try:
                metadata = await enricher.enrich(metadata, file_path)
            except Exception as e:
                logger.warning(
                    f"Enricher {enricher.name} failed for {file_path}: {str(e)}"
                )

        return metadata
```

### 5. Improve Extraction Configuration

- Add configuration options for customizing extraction behavior
- Support different extraction profiles

```python
# domain/metadata/config.py
class ExtractionConfig:
    """Configuration for metadata extraction."""

    def __init__(self, **kwargs):
        """Initialize the extraction configuration.

        Args:
            **kwargs: Configuration options
        """
        # Default configuration
        self.max_text_size: int = kwargs.get("max_text_size", 10 * 1024 * 1024)  # 10 MB
        self.extract_content: bool = kwargs.get("extract_content", True)
        self.extract_metadata: bool = kwargs.get("extract_metadata", True)
        self.thumbnail_size: tuple[int, int] = kwargs.get("thumbnail_size", (200, 200))
        self.content_extract_strategy: str = kwargs.get("content_extract_strategy", "full")
        self.metadata_extract_depth: str = kwargs.get("metadata_extract_depth", "standard")

        # Custom options (for specific extractors)
        self.custom: dict[str, Any] = kwargs.get("custom", {})

    @classmethod
    def minimal(cls) -> "ExtractionConfig":
        """Create a minimal extraction configuration."""
        return cls(
            extract_content=False,
            extract_metadata=True,
            metadata_extract_depth="minimal"
        )

    @classmethod
    def full(cls) -> "ExtractionConfig":
        """Create a full extraction configuration."""
        return cls(
            extract_content=True,
            extract_metadata=True,
            metadata_extract_depth="full",
            content_extract_strategy="full"
        )

    @classmethod
    def content_only(cls) -> "ExtractionConfig":
        """Create a content-only extraction configuration."""
        return cls(
            extract_content=True,
            extract_metadata=False,
            content_extract_strategy="full"
        )

    def with_custom_option(self, extractor_name: str, option: str, value: Any) -> "ExtractionConfig":
        """Add a custom option for a specific extractor.

        Args:
            extractor_name: Name of the extractor
            option: Option name
            value: Option value

        Returns:
            Modified configuration
        """
        if extractor_name not in self.custom:
            self.custom[extractor_name] = {}
        self.custom[extractor_name][option] = value
        return self

# In Extractor class
class Extractor(ABC):
    # ... existing code ...

    @abstractmethod
    async def extract_metadata(self, file_path: str, config: ExtractionConfig = None) -> dict[str, Any]:
        """Extract metadata from the given file."""
        pass

    @abstractmethod
    async def extract_content(self, file_path: str, config: ExtractionConfig = None) -> str:
        """Extract textual content from the given file."""
        pass

    @abstractmethod
    async def generate_preview(self, file_path: str, config: ExtractionConfig = None) -> str:
        """Generate a textual preview of the file content."""
        pass

# In MetadataManager
class MetadataManager:
    # ... existing code ...

    async def extract_metadata(
        self, file_path: str, mime_type: str | None = None,
        config: ExtractionConfig = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Extract metadata from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file
            config: Extraction configuration
            use_cache: Whether to use cached metadata if available

        Returns:
            Dictionary containing the extracted metadata
        """
        if not self._initialized:
            self.initialize()

        # Use default config if none provided
        config = config or ExtractionConfig()

        # Try to get from cache if caching is enabled
        if use_cache:
            cached_metadata = await self._cache.get(file_path)
            if cached_metadata is not None:
                return cached_metadata

        # Extract metadata using the appropriate extractor
        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            metadata = await extractor.extract_metadata(file_path, config)

            # Store in cache if caching is enabled
            if use_cache:
                await self._cache.put(file_path, metadata)

            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e
```

### 6. Enhance Structured Content Extraction

- Add support for structured content extraction
- Support for sectioning and organization of extracted content

```python
# domain/metadata/structured.py
from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class ContentSection:
    """Represents a section of extracted content."""

    title: str
    content: str
    level: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    subsections: list["ContentSection"] = field(default_factory=list)

@dataclass
class StructuredContent:
    """Represents structured content extracted from a file."""

    sections: list[ContentSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: ContentSection) -> None:
        """Add a section to the structured content."""
        self.sections.append(section)

    def to_text(self) -> str:
        """Convert structured content to plain text."""
        result = []

        for section in self.sections:
            self._append_section_text(result, section, 0)

        return "\n".join(result)

    def _append_section_text(self, result: list[str], section: ContentSection, indent: int) -> None:
        """Append section text to result list."""
        # Add section title with appropriate indentation
        if section.title:
            result.append(f"{'  ' * indent}{'#' * section.level} {section.title}")

        # Add section content
        if section.content:
            # Indent each line of content
            content_lines = section.content.split("\n")
            result.extend([f"{'  ' * indent}{line}" for line in content_lines])

        # Add subsections
        for subsection in section.subsections:
            self._append_section_text(result, subsection, indent + 1)

# In extractors that support structured content
class DocumentExtractor(Extractor):
    # ... existing code ...

    async def extract_structured_content(self, file_path: str, config: ExtractionConfig = None) -> StructuredContent:
        """Extract structured content from a document.

        Args:
            file_path: Path to the document
            config: Extraction configuration

        Returns:
            Structured content extracted from the document
        """
        config = config or ExtractionConfig()

        # Create structured content object
        structured_content = StructuredContent()

        try:
            # Import necessary libraries
            import docx

            # Open the document
            doc = docx.Document(file_path)

            # Extract content by sections (using headings)
            current_section = None
            section_stack = []

            for paragraph in doc.paragraphs:
                # Check if paragraph is a heading
                if paragraph.style.name.startswith('Heading'):
                    # Get heading level
                    try:
                        level = int(paragraph.style.name.replace('Heading ', ''))
                    except ValueError:
                        level = 1

                    # Create a new section
                    new_section = ContentSection(
                        title=paragraph.text.strip(),
                        content="",
                        level=level
                    )

                    # Adjust section stack based on heading level
                    while section_stack and section_stack[-1].level >= level:
                        section_stack.pop()

                    # Add to parent section or directly to structured content
                    if section_stack:
                        section_stack[-1].subsections.append(new_section)
                    else:
                        structured_content.add_section(new_section)

                    # Update current section
                    current_section = new_section
                    section_stack.append(current_section)
                elif current_section is not None:
                    # Add content to current section
                    if current_section.content:
                        current_section.content += f"\n{paragraph.text}"
                    else:
                        current_section.content = paragraph.text
                else:
                    # Create a default section for content before any heading
                    current_section = ContentSection(
                        title="",
                        content=paragraph.text,
                        level=0
                    )
                    structured_content.add_section(current_section)
                    section_stack.append(current_section)

            return structured_content

        except Exception as e:
            logger.error(f"Error extracting structured content from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract structured content from {file_path}: {str(e)}"
            ) from e

# In MetadataManager
class MetadataManager:
    # ... existing code ...

    async def extract_structured_content(
        self, file_path: str, mime_type: str | None = None,
        config: ExtractionConfig = None
    ) -> StructuredContent:
        """Extract structured content from the given file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file
            config: Extraction configuration

        Returns:
            Structured content extracted from the file

        Raises:
            MetadataExtractionError: If content extraction fails
            NotImplementedError: If structured extraction is not supported
        """
        if not self._initialized:
            self.initialize()

        extractor = self.get_extractor_for_file(file_path, mime_type)
        if not extractor:
            raise MetadataExtractionError(
                f"No suitable extractor found for file: {file_path}"
            )

        try:
            # Check if extractor supports structured content extraction
            if hasattr(extractor, 'extract_structured_content'):
                return await extractor.extract_structured_content(file_path, config)
            else:
                # Fallback: create basic structured content from plain text
                content = await extractor.extract_content(file_path, config)
                structured = StructuredContent()
                structured.add_section(ContentSection(
                    title="Content",
                    content=content,
                    level=1
                ))
                return structured

        except Exception as e:
            logger.error(f"Error extracting structured content from {file_path}: {str(e)}")
            raise MetadataExtractionError(
                f"Failed to extract structured content from {file_path}: {str(e)}"
            ) from e
```

## Implementation Plan

### Phase 1: Core Enhancements (3 weeks)

1. Implement async support throughout the module
2. Add metadata caching system
3. Create explicit dependency management

### Phase 2: Advanced Features (4 weeks)

1. Implement metadata enrichment pipeline
2. Add extraction configuration system
3. Enhance error handling and logging

### Phase 3: Structured Content (3 weeks)

1. Design structured content data model
2. Implement structured extraction in document extractor
3. Add support for PDF and other formats

### Phase 4: Testing and Integration (2 weeks)

1. Add comprehensive test suite
2. Integrate with other modules
3. Create documentation and examples

## Priority Matrix

| Improvement              | Impact | Effort | Priority |
| ------------------------ | :----: | :----: | :------: |
| Async Support            |  High  | Medium |    1     |
| Metadata Caching         |  High  |  Low   |    2     |
| Dependency Management    | Medium |  Low   |    3     |
| Extraction Configuration | Medium | Medium |    4     |
| Metadata Enrichment      | Medium |  High  |    5     |
| Structured Content       |  High  |  High  |    6     |
