# Project Reader Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The project_reader module is responsible for analyzing and summarizing code
projects. The key components include:

- **ProjectReaderImpl**: Main implementation of the ProjectReader interface
- **TokenAnalyzer**: Tool for analyzing token counts in code (for LLM context
  estimation)
- **NotebookConverter**: Utility for converting Jupyter notebooks to Python
  scripts
- Key functionalities:
  - Project structure analysis
  - Code summarization
  - Notebook conversion
  - Token estimation

## Architectural Compliance

The project_reader module demonstrates good alignment with the project's
architectural guidelines:

| Architectural Principle    | Status | Notes                                                             |
| -------------------------- | :----: | ----------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the domain layer                           |
| **Interface-Based Design** |   ✅   | ProjectReaderImpl properly implements the ProjectReader interface |
| **Asynchronous Design**    |   ✅   | Methods consistently use async/await patterns                     |
| **Error Handling**         |   ✅   | Uses specific ProjectReaderError with context                     |
| **Separation of Concerns** |   ✅   | Clear separation between readers, converters, and analyzers       |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                         | Status | Issue                                                                   |
| ---------------------------- | :----: | ----------------------------------------------------------------------- |
| **Dependency Injection**     |   ⚠️   | Takes FileSystemService in constructor but doesn't use Registry pattern |
| **Language Support**         |   🔄   | Limited language parsing capabilities beyond Python                     |
| **AST Analysis**             |   ⚠️   | Basic AST analysis could be expanded                                    |
| **Performance**              |   ⚠️   | Could be optimized for large projects                                   |
| **Caching**                  |   ❌   | No caching mechanism for parsed results                                 |
| **Project Filtering**        |   🔄   | Limited control over which files to include/exclude                     |
| **Documentation Generation** |   ⚠️   | Lacks comprehensive documentation generation capabilities               |

## Recommendations

### 1. Implement Registry Pattern

- Refactor to use Registry pattern for dependencies
- Improve testability and consistency with other modules

```python
# domain/project_reader/project_reader.py
class ProjectReaderImpl(ProjectReader):
    """Implementation of the ProjectReader interface."""

    def __init__(self):
        """Initialize the ProjectReader."""
        self._registry = Registry.get_instance()
        self._file_system_service = self._registry.file_system_service
        self._file_reader = self._registry.file_reader
        self._token_analyzer = TokenAnalyzer()
        self._notebook_converter = NotebookConverter(self._file_system_service)
        self._config_provider = self._registry.config_provider
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the project reader."""
        if self._initialized:
            return

        try:
            # Load configuration
            self._max_file_size = self._config_provider.get_config(
                "project_reader.max_file_size_mb", 10
            ) * 1024 * 1024

            self._initialized = True
            logger.info("ProjectReader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ProjectReader: {e}")
            raise ProjectReaderError(f"Failed to initialize: {e}")
```

### 2. Enhance Language Support

- Add support for more programming languages
- Implement language-specific parsers

```python
# domain/project_reader/language/language_parser.py
class LanguageParser:
    """Base class for language-specific parsers."""

    @abstractmethod
    async def parse_file(self, file_path: Path) -> dict:
        """Parse a file and extract information."""
        pass

    @abstractmethod
    async def extract_symbols(self, content: str) -> list:
        """Extract symbols from content."""
        pass

    @abstractmethod
    async def extract_dependencies(self, content: str) -> list:
        """Extract dependencies from content."""
        pass

# Concrete implementations
class PythonParser(LanguageParser):
    # Implementation for Python

class JavascriptParser(LanguageParser):
    # Implementation for JavaScript

class JavaParser(LanguageParser):
    # Implementation for Java

class RustParser(LanguageParser):
    # Implementation for Rust

# Language parser registry
class LanguageParserRegistry:
    """Registry for language parsers."""

    def __init__(self):
        self._parsers = {}
        self._register_default_parsers()

    def _register_default_parsers(self):
        """Register default language parsers."""
        self._parsers = {
            ".py": PythonParser(),
            ".js": JavascriptParser(),
            ".ts": JavascriptParser(),  # TypeScript uses JavaScript parser
            ".java": JavaParser(),
            ".rs": RustParser(),
        }

    def register_parser(self, extension: str, parser: LanguageParser):
        """Register a parser for a file extension."""
        self._parsers[extension] = parser

    def get_parser(self, file_path: Path) -> LanguageParser:
        """Get parser for a file."""
        ext = file_path.suffix.lower()
        return self._parsers.get(ext)
```

### 3. Implement Advanced AST Analysis

- Add comprehensive AST analysis for better code understanding
- Extract rich metadata from code structure

```python
# domain/project_reader/ast/ast_analyzer.py
class ASTAnalyzer:
    """Analyzer for Abstract Syntax Trees."""

    def __init__(self):
        self._analyzers = {}
        self._register_default_analyzers()

    def _register_default_analyzers(self):
        """Register default AST analyzers."""
        self._analyzers = {
            "python": PythonASTAnalyzer(),
            "javascript": JavascriptASTAnalyzer(),
            "java": JavaASTAnalyzer(),
        }

    async def analyze_ast(self, ast_node, language: str) -> dict:
        """
        Analyze an AST node and extract information.

        Args:
            ast_node: The AST node to analyze
            language: Programming language

        Returns:
            Dictionary of analysis results
        """
        analyzer = self._analyzers.get(language.lower())
        if not analyzer:
            return {"error": f"No analyzer available for language: {language}"}

        return await analyzer.analyze(ast_node)

class PythonASTAnalyzer:
    """AST analyzer for Python code."""

    async def analyze(self, ast_node) -> dict:
        """Analyze Python AST node."""
        result = {
            "imports": [],
            "classes": [],
            "functions": [],
            "constants": [],
            "docstrings": [],
            "complexity": {}
        }

        # Visit all nodes and extract information
        visitor = PythonASTVisitor()
        visitor.visit(ast_node)

        # Extract information
        result["imports"] = visitor.imports
        result["classes"] = visitor.classes
        result["functions"] = visitor.functions
        result["constants"] = visitor.constants
        result["docstrings"] = visitor.docstrings
        result["complexity"] = self._calculate_complexity(ast_node)

        return result

    def _calculate_complexity(self, ast_node) -> dict:
        """Calculate complexity metrics for Python code."""
        # Calculate cyclomatic complexity, cognitive complexity, etc.
        # Return metrics
        return {
            "cyclomatic": self._calculate_cyclomatic_complexity(ast_node),
            "cognitive": self._calculate_cognitive_complexity(ast_node),
            "maintainability_index": self._calculate_maintainability_index(ast_node),
        }
```

### 4. Add Result Caching

- Implement caching for parsed results
- Optimize performance for large projects

```python
# domain/project_reader/cache.py
class ProjectReaderCache:
    """Cache for project reader results."""

    def __init__(self, cache_dir: Path, max_age_hours: int = 24):
        self._cache_dir = cache_dir
        self._max_age_seconds = max_age_hours * 3600
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, project_path: Path, file_path: Path = None) -> str:
        """Generate cache key."""
        if file_path:
            # For file-level cache
            rel_path = file_path.relative_to(project_path)
            file_hash = hashlib.md5(str(rel_path).encode()).hexdigest()
            return f"file_{file_hash}"
        else:
            # For project-level cache
            project_hash = hashlib.md5(str(project_path).encode()).hexdigest()
            return f"project_{project_hash}"

    async def get(self, project_path: Path, file_path: Path = None):
        """Get cached result if available and not stale."""
        cache_key = self._get_cache_key(project_path, file_path)
        cache_file = self._cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if cache is stale
        file_modified = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if (datetime.now() - file_modified).total_seconds() > self._max_age_seconds:
            return None

        # Read cache
        try:
            async with aiofiles.open(cache_file, "r") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None

    async def put(self, project_path: Path, result, file_path: Path = None):
        """Cache a result."""
        cache_key = self._get_cache_key(project_path, file_path)
        cache_file = self._cache_dir / f"{cache_key}.json"

        try:
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(json.dumps(result, indent=2))
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")
```

### 5. Implement Advanced Project Filtering

- Add configurable project filtering
- Support common ignore patterns and custom rules

```python
# domain/project_reader/filter.py
class ProjectFilter:
    """Filter for project files."""

    def __init__(self, config_provider=None):
        self._config_provider = config_provider
        self._default_ignores = [
            "**/.git/**",
            "**/.svn/**",
            "**/.hg/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.so",
            "**/*.a",
            "**/*.dll",
            "**/*.lib",
            "**/*.dylib",
            "**/venv/**",
            "**/.env/**",
            "**/.venv/**",
        ]
        self._custom_ignores = []
        self._include_patterns = []

    async def initialize(self):
        """Initialize with configuration."""
        if self._config_provider:
            # Load custom ignores from config
            self._custom_ignores = self._config_provider.get_config(
                "project_reader.ignore_patterns", []
            )

            # Load include patterns from config
            self._include_patterns = self._config_provider.get_config(
                "project_reader.include_patterns", []
            )

    def add_ignore_pattern(self, pattern: str):
        """Add a pattern to ignore."""
        self._custom_ignores.append(pattern)

    def add_include_pattern(self, pattern: str):
        """Add a pattern to include."""
        self._include_patterns.append(pattern)

    async def should_include(self, file_path: Path, project_root: Path) -> bool:
        """
        Determine if a file should be included.

        Args:
            file_path: Path to the file
            project_root: Project root directory

        Returns:
            True if the file should be included, False otherwise
        """
        # Get relative path for pattern matching
        rel_path = file_path.relative_to(project_root)
        path_str = str(rel_path)

        # Check if file is explicitly included
        if self._include_patterns:
            for pattern in self._include_patterns:
                if fnmatch.fnmatch(path_str, pattern):
                    return True
            # If include patterns are specified and none match, exclude the file
            return False

        # Check against ignore patterns
        all_ignores = self._default_ignores + self._custom_ignores
        for pattern in all_ignores:
            if fnmatch.fnmatch(path_str, pattern):
                return False

        return True
```

### 6. Add Documentation Generation

- Implement automatic documentation generation
- Support multiple documentation formats

```python
# domain/project_reader/documentation/generator.py
class DocumentationGenerator:
    """Generator for project documentation."""

    def __init__(self, registry):
        self._registry = registry
        self._generators = {}
        self._register_default_generators()

    def _register_default_generators(self):
        """Register default documentation generators."""
        self._generators = {
            "markdown": MarkdownDocGenerator(),
            "rst": ReStructuredTextDocGenerator(),
            "html": HTMLDocGenerator(),
            "json": JSONDocGenerator(),
        }

    def register_generator(self, format_name: str, generator):
        """Register a documentation generator."""
        self._generators[format_name] = generator

    async def generate_documentation(
        self,
        project_path: Path,
        output_path: Path,
        format: str = "markdown",
        options: dict = None
    ) -> Path:
        """
        Generate documentation for a project.

        Args:
            project_path: Path to the project root
            output_path: Path to output documentation
            format: Documentation format (markdown, rst, html, json)
            options: Generation options

        Returns:
            Path to the generated documentation
        """
        generator = self._generators.get(format.lower())
        if not generator:
            raise ValueError(f"Unsupported documentation format: {format}")

        # Get project reader
        project_reader = self._registry.project_reader

        # Read project structure
        project_info = await project_reader.summarize_project(project_path)

        # Generate documentation
        return await generator.generate(project_info, output_path, options or {})
```

### 7. Optimize for Large Projects

- Implement chunked processing for large projects
- Add parallel file processing

```python
# domain/project_reader/parallel_reader.py
class ParallelProjectReader:
    """Parallel reader for large projects."""

    def __init__(self, registry, max_workers: int = 4):
        self._registry = registry
        self._max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)

    async def read_project(self, project_path: Path, filter=None) -> dict:
        """
        Read a project in parallel.

        Args:
            project_path: Path to the project
            filter: Optional ProjectFilter instance

        Returns:
            Project information dictionary
        """
        # Get all files in the project
        files = await self._get_project_files(project_path, filter)

        # Process files in parallel
        file_results = await self._process_files_parallel(files, project_path)

        # Combine results
        return self._combine_results(file_results, project_path)

    async def _get_project_files(self, project_path: Path, filter=None) -> list:
        """Get list of files in project."""
        files = []

        # Walk directory
        for root, _, filenames in os.walk(project_path):
            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename

                # Apply filter if provided
                if filter and not await filter.should_include(file_path, project_path):
                    continue

                files.append(file_path)

        return files

    async def _process_files_parallel(self, files: list, project_path: Path) -> list:
        """Process files in parallel."""
        tasks = []
        for file_path in files:
            task = self._process_file(file_path, project_path)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_file(self, file_path: Path, project_path: Path) -> dict:
        """Process a single file with concurrency control."""
        async with self._semaphore:
            try:
                file_reader = self._registry.project_reader
                return await file_reader.read_file(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                return {"path": str(file_path), "error": str(e)}

    def _combine_results(self, file_results: list, project_path: Path) -> dict:
        """Combine individual file results into project summary."""
        # Process results and build project structure
        summary = {
            "project_path": str(project_path),
            "files": [],
            "structure": {},
            "languages": {},
            "summary": {},
            "modules": [],
        }

        # Filter out errors
        valid_results = [r for r in file_results if not isinstance(r, Exception) and "error" not in r]

        # Count files by language
        for result in valid_results:
            lang = result.get("language", "unknown")
            if lang not in summary["languages"]:
                summary["languages"][lang] = 0
            summary["languages"][lang] += 1

            # Add to files list
            summary["files"].append({
                "path": result.get("path"),
                "language": lang,
                "symbols": len(result.get("symbols", [])),
                "size": result.get("size", 0),
            })

            # Build module information
            if "module" in result:
                summary["modules"].append(result["module"])

        # Build project structure
        summary["structure"] = self._build_directory_structure(valid_results, project_path)

        # Generate overall summary
        summary["summary"] = {
            "total_files": len(summary["files"]),
            "total_modules": len(summary["modules"]),
            "languages": summary["languages"],
            "estimated_tokens": sum(r.get("tokens", 0) for r in valid_results),
        }

        return summary
```

## Implementation Plan

### Phase 1: Core Improvements (2 weeks)

1. Implement Registry pattern for dependency injection
2. Add advanced project filtering
3. Improve AST analysis for Python

### Phase 2: Performance Optimization (2 weeks)

1. Implement result caching
2. Add parallel processing for large projects
3. Optimize token counting

### Phase 3: Language Support (3 weeks)

1. Create language parser registry
2. Implement parsers for additional languages
3. Add comprehensive symbol extraction

### Phase 4: Documentation Generation (2 weeks)

1. Implement documentation generators
2. Add support for multiple output formats
3. Create templates for documentation

## Priority Matrix

| Improvement                | Impact | Effort | Priority |
| -------------------------- | :----: | :----: | :------: |
| Registry Pattern           |  High  |  Low   |    1     |
| Result Caching             |  High  | Medium |    2     |
| Advanced Project Filtering | Medium |  Low   |    3     |
| Parallel Processing        |  High  | Medium |    4     |
| Enhanced AST Analysis      | Medium |  High  |    5     |
| Language Support           | Medium |  High  |    6     |
| Documentation Generation   |  Low   |  High  |    7     |
