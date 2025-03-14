# File Relationship Mapping

## Overview

The File Relationship Mapping feature helps users discover, visualize, and leverage relationships between files in their system. By automatically detecting various types of connections between files, it enables more intelligent navigation, organization, and understanding of file structures.

## Features

### 1. Relationship Detection

The system detects multiple types of relationships between files:

- **Reference Relationships**: Files that explicitly reference each other
  - Import/include statements in code files
  - Links or mentions of other files in documents
  - References in comments or metadata

- **Content Relationships**: Files with similar or related content
  - Similar text content or topics
  - Shared keywords or concepts
  - Similar code patterns or structures

- **Structural Relationships**: Files related by their location or naming
  - Parent-child directory relationships
  - Files with related naming patterns (e.g., file.py and file_test.py)
  - Files belonging to the same project structure

- **Temporal Relationships**: Files related by time
  - Files created or modified together
  - Files with related version history
  - Files typically accessed together

- **Derived Relationships**: Files derived from others
  - Generated files and their sources
  - Compiled files and source code
  - Converted formats (e.g., Markdown to PDF)

### 2. Relationship Graph

The system builds a graph-based representation of file relationships that enables:

- **Path Finding**: Discover how files are connected through intermediaries
- **Centrality Analysis**: Identify the most important or central files
- **Clustering**: Find groups of closely related files
- **Visualization**: Generate visual representations of file relationships

### 3. Intelligent Navigation

Use relationship data to navigate your files more effectively:

- **Find Related Files**: Quickly locate files related to the one you're working on
- **Discover Dependencies**: Understand which files depend on others
- **Identify File Clusters**: Find groups of files that work together

### 4. Graph Export

Export relationship graphs for visualization or analysis:

- **JSON Format**: Compatible with common visualization libraries
- **GraphViz DOT Format**: For detailed graph visualization
- **Customizable Output**: Filter by relationship type, strength, and more

## Usage

### Command Line Interface

#### Detecting Relationships

```bash
# Detect relationships for specific files
python -m backend.cli relationships detect path/to/file1.py path/to/file2.py

# Detect relationships for all files in a directory
python -m backend.cli relationships detect path/to/directory/*.py

# Specify detection strategies
python -m backend.cli relationships detect path/to/file.py --strategies IMPORT_ANALYSIS DIRECTORY_STRUCTURE
```

#### Finding Related Files

```bash
# Find all files related to a specific file
python -m backend.cli relationships find-related path/to/file.py

# Filter by relationship type
python -m backend.cli relationships find-related path/to/file.py --types IMPORTS REFERENCES

# Filter by minimum strength
python -m backend.cli relationships find-related path/to/file.py --min-strength 0.7

# Save results to a file
python -m backend.cli relationships find-related path/to/file.py --output results.json
```

#### Finding Paths Between Files

```bash
# Find paths connecting two files
python -m backend.cli relationships find-paths source.py target.py

# Limit path length
python -m backend.cli relationships find-paths source.py target.py --max-length 3

# Save results to a file
python -m backend.cli relationships find-paths source.py target.py --output paths.json
```

#### Exporting Visualizations

```bash
# Export relationship graph as JSON
python -m backend.cli relationships export graph.json

# Export as GraphViz DOT format
python -m backend.cli relationships export graph.dot --format dot

# Filter relationships by type
python -m backend.cli relationships export graph.json --types IMPORTS REFERENCES

# Limit the number of nodes
python -m backend.cli relationships export graph.json --max-nodes 50
```

#### Finding Central Files

```bash
# Find the most central files in your codebase
python -m backend.cli relationships find-central

# Specify the number of results
python -m backend.cli relationships find-central --top-n 20

# Filter by relationship type
python -m backend.cli relationships find-central --types IMPORTS REFERENCES

# Save results to a file
python -m backend.cli relationships find-central --output central_files.json
```

## Technical Details

### Architecture

The relationship mapping system consists of four main components:

1. **Relationship Detector**: Analyzes files to detect relationships using various strategies
2. **Relationship Store**: Persists relationships in a SQLite database
3. **Relationship Graph**: Provides graph operations on the relationship data
4. **CLI Interface**: Allows users to interact with the relationship system

### Detection Strategies

Different detection strategies are implemented to identify various relationship types:

- **Import Analysis**: Detects import statements in code files
- **Directory Structure Analysis**: Identifies relationships based on file location
- **Content Similarity**: Compares file contents for similarity
- **Modification History**: Analyzes files modified together
- **Naming Pattern Analysis**: Finds relationships based on naming conventions

### Database Schema

Relationships are stored in a SQLite database with the following schema:

```sql
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    strength REAL NOT NULL,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### Relationship Types

The system defines the following relationship types:

- `IMPORTS`: File imports or includes another file
- `REFERENCES`: File references another file
- `LINKS_TO`: File contains a link to another file
- `SIMILAR_CONTENT`: Files have similar textual content
- `SHARED_KEYWORDS`: Files share significant keywords
- `PARENT_CHILD`: Directory contains file relationship
- `SIBLING`: Files in same directory
- `MODIFIED_TOGETHER`: Files frequently modified in same commit
- `CREATED_TOGETHER`: Files created at similar times
- `COMPILED_FROM`: File is compiled/generated from another file
- `EXTRACTED_FROM`: File was extracted from another file
- `CUSTOM`: User-defined relationship

## Integration with Other Features

The File Relationship Mapping feature integrates with other features in The Aichemist Codex:

- **Tags System**: Relationships can be used to suggest tags for files
- **Search**: Relationships enhance search relevance and results
- **Metadata Extraction**: File metadata informs relationship detection
- **File Processing**: Relationship detection is integrated into file processing pipelines

## Performance Considerations

- **Incremental Updates**: Only analyze changed files when possible
- **Relationship Caching**: Cache relationship data for quicker access
- **Configurable Depth**: Control how deep relationship graphs are built
- **Strength Filtering**: Filter low-confidence relationships to reduce noise

## Future Enhancements

- **Web-based Visualization**: Interactive exploration of file relationships
- **Relationship Prediction**: Suggest potential relationships based on patterns
- **User-defined Relationships**: Allow users to manually create relationships
- **External Reference Detection**: Detect references to external libraries
- **Workspace Analysis**: Analyze entire workspaces for relationship patterns