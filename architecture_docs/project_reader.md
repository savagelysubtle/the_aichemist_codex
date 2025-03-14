Here's the updated content for modules/project_reader.md:

```markdown
# Project Reader Package Documentation

## Overview
The Project Reader package provides comprehensive code analysis and project summarization capabilities. It includes Python code analysis, Jupyter notebook processing, token counting, and tag handling functionality, with support for multiple output formats.

## Components

### 1. Code Summary (code_summary.py)
- Core code analysis functionality
- Features:
  - AST-based Python code analysis
  - Function and class detection
  - Docstring extraction
  - Asynchronous file processing
  - Multi-format output support
- Example usage:
  ```python
  summary = summarize_project(
      directory=Path("project_dir"),
      output_markdown=Path("summary.md"),
      output_json=Path("summary.json")
  )
  ```

### 2. Notebook Converter (notebooks.py)

- Jupyter notebook processing
- Features:
  - Notebook to Python script conversion
  - Code cell extraction
  - Asynchronous processing
  - Error handling
- Example usage:

  ```python
  converter = NotebookConverter()
  script = await converter.to_script_async(notebook_path)
  # or synchronous version
  script = converter.to_script(notebook_path)
  ```

### 3. Token Analyzer (token_counter.py)

- Token estimation functionality
- Features:
  - Uses tiktoken for accurate counting
  - cl100k_base encoding support
  - Simple API
- Example usage:

  ```python
  analyzer = TokenAnalyzer()
  token_count = analyzer.estimate(text)
  ```

### 4. Tag Handler (tags.py)

- Tag management system
- Features:
  - Tag object representation
  - Tag string parsing
  - Simple tag creation
- Example usage:

  ```python
  tag = parse_tag("feature")
  print(tag)  # Tag(feature)
  ```

## Implementation Details

### Code Analysis Process

1. Directory Scanning
   - Recursive Python file discovery
   - Ignore pattern application
   - Safe file handling

2. AST Processing
   - Function detection
   - Docstring extraction
   - Metadata collection
   - Error handling

3. Notebook Handling
   - JSON parsing
   - Code cell extraction
   - Source concatenation
   - Error recovery

### Function Metadata

```python
{
    "name": "function_name",
    "args": ["arg1", "arg2"],
    "decorators": ["decorator1"],
    "return_type": "return_type",
    "lineno": 10,
    "docstring": "Function documentation"
}
```

### Output Formats

- JSON summary
- Markdown documentation
- Folder-based organization
- Function documentation

## Integration Points

### Internal Dependencies

- Utils package for async I/O
- Output Formatter for export
- Safety checks for file handling

### External Dependencies

- ast for code parsing
- tiktoken for token counting
- json for notebook parsing
- asyncio for async operations

## Best Practices

### Code Analysis

```python
# Analyze project
summary = summarize_project(
    directory=project_path,
    output_markdown=md_path,
    output_json=json_path
)

# Process single file
metadata = await process_file(file_path)
```

### Notebook Processing

```python
# Async conversion
script = await NotebookConverter.to_script_async(notebook_path)

# Sync conversion
script = NotebookConverter.to_script(notebook_path)
```

### Error Handling

```python
try:
    summary = await summarize_code(directory)
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    # Implement recovery strategy
```

## Future Improvements

### Short-term

1. Additional language support
2. Enhanced notebook analysis
3. Better error recovery
4. Extended metadata extraction
5. Improved tag system

### Long-term

1. Language-agnostic analysis
2. Real-time code analysis
3. Advanced code metrics
4. Integration with IDEs
5. Machine learning-based insights

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the project reading system effectively.
