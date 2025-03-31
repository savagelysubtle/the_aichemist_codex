# Using The AIchemist Codex Core Features

## Overview

After installing The AIchemist Codex from GitHub (see [[github-installation]]), you can use its core features for code analysis and management. This guide demonstrates practical usage based on the actual implementation.

## Core Features

### 1. Code Analysis Service

The heart of the analysis functionality is the `CodeAnalysisService`:

```python
from pathlib import Path
from the_aichemist_codex.infrastructure.analysis.code_analysis_service import CodeAnalysisService
from the_aichemist_codex.infrastructure.repositories.file_code_artifact_repository import FileCodeArtifactRepository

# Initialize the service
repository = FileCodeArtifactRepository(storage_dir=Path("artifacts"))
analysis_service = CodeAnalysisService(repository)

# Analyze a Python file
async def analyze_file():
    results = await analysis_service.analyze_file(
        file_path=Path("your_file.py"),
        depth=2  # 1: basic, 2: standard, 3: deep
    )

    # Results include:
    print(f"Basic metrics: {results['basic']}")  # Line count, size, etc.
    print(f"Complexity: {results['complexity']}")  # If depth >= 2
    print(f"Structure: {results['structure']}")   # If depth >= 2
```

### 2. Codebase Analysis

Analyze entire codebases or directories:

```python
async def analyze_project():
    results = await analysis_service.analyze_codebase(
        directory=Path("src"),
        depth=3,  # Deep analysis
        file_pattern="*.py"
    )

    # Access results
    print(f"Total files: {results['summary']['file_count']}")
    print(f"Total lines: {results['summary']['total_lines']}")

    if 'complexity' in results:
        print(f"Average complexity: {results['complexity']['average']}")
        print("Most complex files:")
        for file in results['complexity']['most_complex']:
            print(f"- {file['name']}: {file['complexity']}")
```

### 3. Knowledge Extraction

Extract knowledge from code files:

```python
async def extract_code_knowledge(artifact_id):
    knowledge = await analysis_service.extract_knowledge(
        artifact_id,
        max_items=10
    )

    for item in knowledge:
        print(f"Type: {item['type']}")
        print(f"Content: {item['content']}")
        print(f"Importance: {item['importance']}")
```

### 4. Code Structure Analysis

Get detailed code structure information:

```python
async def analyze_structure(artifact_id):
    structure = await analysis_service.get_structure(artifact_id)

    # Classes and methods
    for class_info in structure['classes']:
        print(f"Class: {class_info['name']}")
        print(f"Docstring: {class_info['docstring']}")
        for method in class_info['methods']:
            print(f"  Method: {method['name']}")

    # Functions
    for func in structure['functions']:
        print(f"Function: {func['name']}")
        print(f"Arguments: {func['args']}")
```

### 5. Code Relationships

Analyze dependencies and references:

```python
async def analyze_relationships(artifact_id):
    # Find dependencies
    deps = await analysis_service.find_dependencies(
        artifact_id,
        recursive=True
    )
    print("Dependencies:", [d.name for d in deps])

    # Find references
    refs = await analysis_service.find_references(
        artifact_id,
        recursive=True
    )
    print("References:", [r.name for r in refs])
```

### 6. Code Similarity Analysis

Find similar code artifacts:

```python
async def find_similar_code(artifact_id):
    similar = await analysis_service.find_similar_artifacts(
        artifact_id,
        min_similarity=0.7,
        limit=5
    )

    for artifact, similarity in similar:
        print(f"Similar file: {artifact.name}")
        print(f"Similarity score: {similarity:.2f}")
```

## Practical Examples

### 1. Project Quality Analysis

```python
async def analyze_project_quality(project_path: Path):
    """Analyze overall project quality."""
    results = await analysis_service.analyze_codebase(
        directory=project_path,
        depth=3,
        file_pattern="*.py"
    )

    # Quality metrics
    if 'complexity' in results:
        print("\nComplexity Analysis:")
        print(f"Average complexity: {results['complexity']['average']}")
        print("\nFiles needing attention:")
        for file in results['complexity']['most_complex']:
            if file['complexity'] > 15:  # High complexity threshold
                print(f"- {file['name']}: {file['complexity']}")

    # Knowledge extraction
    if 'knowledge' in results:
        print("\nKey Knowledge Points:")
        for item in results['knowledge']:
            if item['importance'] > 0.8:  # High importance threshold
                print(f"- {item['content']}")
```

### 2. Code Pattern Detection

```python
async def detect_patterns(project_path: Path):
    """Detect common patterns in codebase."""
    # Analyze all Python files
    results = await analysis_service.analyze_codebase(
        directory=project_path,
        depth=2,
        file_pattern="*.py"
    )

    # Find similar code structures
    patterns = {}
    for artifact_info in results['artifacts']:
        artifact_id = UUID(artifact_info['id'])
        similar = await analysis_service.find_similar_artifacts(
            artifact_id,
            min_similarity=0.8
        )
        if similar:
            patterns[artifact_info['name']] = similar

    # Report patterns
    for file_name, similar_files in patterns.items():
        print(f"\nPattern found in {file_name}:")
        for artifact, similarity in similar_files:
            print(f"- {artifact.name} (similarity: {similarity:.2f})")
```

### 3. Documentation Quality Check

```python
async def check_documentation(project_path: Path):
    """Check documentation quality."""
    results = await analysis_service.analyze_codebase(
        directory=project_path,
        depth=3,
        file_pattern="*.py"
    )

    # Extract and analyze documentation
    docs_issues = []
    for artifact_info in results['artifacts']:
        artifact_id = UUID(artifact_info['id'])
        knowledge = await analysis_service.extract_knowledge(artifact_id)

        # Check for missing or poor documentation
        has_docstrings = any(
            item['type'] == 'module_doc' or
            item['type'] == 'class' or
            item['type'] == 'function'
            for item in knowledge
        )

        if not has_docstrings:
            docs_issues.append(artifact_info['name'])

    # Report issues
    if docs_issues:
        print("\nFiles needing documentation:")
        for file in docs_issues:
            print(f"- {file}")
```

## Best Practices

1. **Async Usage**
   - Always use async/await with service methods
   - Handle async operations properly in your code
   - Consider using asyncio.gather for parallel operations

2. **Error Handling**
   - Handle RepositoryError for missing artifacts
   - Handle FileNotFoundError for missing files
   - Use try/except blocks around service calls

3. **Performance**
   - Use appropriate analysis depth for your needs
   - Consider caching results for large codebases
   - Process files in batches when possible

4. **Memory Management**
   - Clean up artifacts when no longer needed
   - Monitor storage directory size
   - Use context managers for resource cleanup

## Backlinks

- [[github-installation]]
- [[codebase-review]]
- [[systemPatterns]]
