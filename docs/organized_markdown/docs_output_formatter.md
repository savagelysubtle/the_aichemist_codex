Here's the updated content for modules/output_formatter.md:

```markdown
# Output Formatter Package Documentation

## Overview
The Output Formatter package provides multiple output formats for code analysis results, supporting JSON, Markdown, HTML, and CSV formats. It implements asynchronous I/O operations and consistent error handling across all formatters.

## Components

### 1. JSON Writer (json_writer.py)
- Handles structured JSON output
- Features:
  - Custom Path object serialization
  - Asynchronous file writing
  - Pretty printing with indentation
  - Error handling and logging
- Example usage:
  ```python
  await save_as_json_async(data, output_file)
  # or synchronous wrapper
  save_as_json(output_file, data)
  ```

### 2. Markdown Writer (markdown_writer.py)

- Generates readable Markdown documentation
- Features:
  - Folder-based organization
  - Function documentation
  - Emoji-enhanced formatting
  - Summary sections
- Content structure:

  ```markdown
  # 📖 Project Title
  ## 📂 Folder: `folder_name/`
  ### 📄 `file_name`
  #### Functions
  ##### 🔹 `function_name(args)`
  ```

### 3. HTML Writer (html_writer.py)

- Creates HTML reports
- Features:
  - Clean HTML structure
  - Function listings
  - File summaries
  - Argument documentation
- HTML structure:

  ```html
  <html>
    <head><title>Project Code Summary</title></head>
    <body>
      <h1>Project Title</h1>
      <h2>File Name</h2>
      <ul>
        <li><b>Function</b>: name (Line X)</li>
      </ul>
    </body>
  </html>
  ```

### 4. CSV Writer (csv_writer.py)

- Generates tabular data output
- Features:
  - Memory-efficient processing
  - Standard CSV format
  - Function metadata export
  - Consistent column structure
- CSV columns:
  - File
  - Type
  - Name
  - Arguments
  - Line Number

## Implementation Details

### Asynchronous I/O

- Uses AsyncFileIO for file operations
- Implements error handling
- Provides progress logging
- Ensures consistent file encoding

### Data Formatting

#### JSON Format

```json
{
    "file_path": {
        "functions": [
            {
                "name": "function_name",
                "args": ["arg1", "arg2"],
                "lineno": 10
            }
        ]
    }
}
```

#### Markdown Format

- Hierarchical structure
- Emoji-enhanced headings
- Function documentation
- File summaries

#### HTML Format

- Clean document structure
- Function listings
- File organization
- Argument documentation

#### CSV Format

- Tabular data structure
- Function metadata
- File information
- Line numbers

### Error Handling

- Comprehensive logging
- Operation status tracking
- Error recovery
- User feedback

## Integration Points

### Internal Dependencies

- Utils package for async I/O
- Config for settings
- Logger for error tracking

### External Dependencies

- aiofiles for async operations
- pathlib for path handling
- csv for CSV processing
- logging for error tracking

## Best Practices

### JSON Output

```python
# Async usage
await save_as_json_async(data, output_file)

# Sync usage
save_as_json(output_file, data)
```

### Markdown Output

```python
await save_as_markdown(
    output_file,
    data,
    gpt_summaries={},
    title="Project Code Summary"
)
```

### HTML Output

```python
await save_as_html(
    output_file,
    data,
    title="Project Code Summary"
)
```

### CSV Output

```python
await save_as_csv(output_file, data)
```

## Future Improvements

### Short-term

1. Additional output formats (PDF, DOCX)
2. Enhanced HTML styling
3. Template customization
4. Better error recovery
5. Progress reporting

### Long-term

1. Interactive HTML reports
2. Real-time preview generation
3. Custom format plugins
4. Streaming output support
5. Multi-format batch export

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the output formatting system effectively.
