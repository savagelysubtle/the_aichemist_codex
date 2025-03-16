# Database Metadata Extraction

## Overview

The database metadata extraction module provides comprehensive capabilities for
extracting rich metadata from various database file formats. This module is part
of The Aichemist Codex's Expanded Format Support, enabling intelligent analysis
and organization of database files.

The extractor can process various database formats (SQLite, MySQL dumps,
PostgreSQL dumps) and extracts a wide range of metadata including schema
information, table counts, column details, and other database-specific metadata.
This enables powerful searching, organization, and analysis of database content.

## Features

- **Format Detection**: Automatically identify and process various database file
  formats
- **Schema Analysis**: Extract table definitions, views, indexes, and
  relationships
- **Statistical Information**: Table counts, row counts, and other database
  metrics
- **SQL Dump Analysis**: Parse SQL dump files to extract database structure
- **Table and Column Inspection**: Detailed metadata about tables and their
  columns
- **Index Information**: Extract index definitions and coverage statistics
- **Database Size and Complexity Metrics**: Understand database scope and scale

## Usage

### Basic Usage

```python
from backend.src.metadata import DatabaseMetadataExtractor

# Create an instance of the extractor
extractor = DatabaseMetadataExtractor()

# Extract metadata from a database file
metadata = await extractor.extract("/path/to/database.sqlite")

# Use the extracted metadata
if "schema" in metadata:
    table_count = metadata["schema"]["table_count"]
    total_rows = metadata["statistics"]["total_rows"]
    print(f"Database contains {table_count} tables with {total_rows} total rows")
```

### With Cache Manager

For performance optimization, you can provide a cache manager:

```python
from backend.src.metadata import DatabaseMetadataExtractor
from backend.src.utils.cache_manager import CacheManager

# Create a cache manager
cache_manager = CacheManager()

# Create an instance of the extractor with cache support
extractor = DatabaseMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (this will use/update the cache)
metadata = await extractor.extract("/path/to/database.sqlite")
```

## Extracted Metadata

The extractor returns a dictionary with the following structure:

```python
{
    "metadata_type": "database",
    "format": {
        "type": "sqlite",           # Database type (sqlite, mysql_dump, etc.)
        "file_size": 51200,         # Size in bytes
        "sqlite_version": "3.36.0", # For SQLite databases
        "detected_type": "mysql",   # For SQL dumps, detected format
        "database_name": "test_db", # If available
        "default_charset": "utf8mb4" # For SQL dumps
    },
    "schema": {
        "table_count": 12,          # Number of tables
        "view_count": 3,            # Number of views
        "total_objects": 15,        # Total schema objects
        "tables": [                 # Detailed table information
            {
                "name": "users",
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "primary_key": True,
                        "not_null": True
                    },
                    {
                        "name": "username",
                        "type": "TEXT",
                        "primary_key": False,
                        "not_null": True
                    },
                    # More columns...
                ],
                "row_count": 1250,
                "index_count": 2,
                "indexes": [
                    {
                        "name": "idx_username",
                        "columns": ["username"],
                        "unique": True
                    },
                    # More indexes...
                ]
            },
            # More tables...
        ],
        "views": [                  # View information
            {
                "name": "active_users",
                "definition": "CREATE VIEW active_users AS SELECT..."
            },
            # More views...
        ],
        "schemas": ["public", "auth"],  # For PostgreSQL dumps
        "extensions": ["postgis", "hstore"]  # For PostgreSQL dumps
    },
    "statistics": {
        "total_rows": 15000,            # Approximate total row count
        "total_indexes": 25,            # Total number of indexes
        "avg_rows_per_table": 1250,     # Average rows per table
        "bytes_per_row": 142.5,         # Average bytes per row
        "insert_statements": 500,       # For SQL dumps only
        "alter_statements": 10,         # For SQL dumps only
        "total_statements": 550         # For SQL dumps only
    },
    "summary": "SQLite database with 12 tables, 3 views, and approximately 15000 total rows"
}
```

> **Note**: Not all fields will be present for all database files. The content
> depends on what metadata is available in the original file and the specific
> format.

## Supported Database Formats

The extractor supports the following database formats:

- SQLite database files (.db, .sqlite, .sqlite3)
- SQL dump files (.sql)
- MySQL dump files (.mysql, .sql)
- PostgreSQL dump files (.pgsql, .sql)

## Error Handling

The extractor implements robust error handling to ensure it doesn't fail when
processing problematic database files:

- Missing files are reported as warnings
- Unsupported file types are gracefully skipped
- Corrupted database files are handled safely
- SQL parsing errors are caught and logged
- Errors are logged with appropriate severity levels

## Performance Considerations

- **Caching**: Use the cache manager for repeated access to the same files
- **Selective Processing**: For large databases, only metadata is extracted, not
  content
- **SQL Dump Parsing**: Uses pattern matching instead of full SQL parsing for
  performance
- **Connection Management**: Database connections are properly opened and closed
  to prevent resource leaks
- **Read-Only Access**: Databases are opened in read-only mode to prevent
  accidental modification

## Implementation Details

### SQLite Processing

SQLite database files are processed using SQLite's standard library, which
provides a safe and efficient way to inspect database structure without
executing arbitrary SQL. The extractor:

1. Opens the database in read-only mode
2. Extracts schema information (tables, views, columns, indexes)
3. Collects statistics (row counts, index counts)
4. Analyzes relationships between tables (foreign keys)
5. Calculates file size metrics

### SQL Dump Processing

SQL dump files are processed using regular expression pattern matching to
extract schema information:

1. Identifies CREATE TABLE, CREATE VIEW, and other DDL statements
2. Counts INSERT statements to estimate data volume
3. Detects database type from specific syntax patterns
4. Extracts column definitions and constraints
5. Analyzes format-specific features (e.g., MySQL charset)

### Format Detection

The extractor uses multiple methods to identify database types:

1. MIME type detection
2. File extension matching
3. Content pattern analysis for SQL dumps
4. Format-specific indicators (e.g., "ENGINE=InnoDB" for MySQL)

### Safety Features

The extractor includes several safety mechanisms:

- Type checking and validation
- Defensive attribute access
- Exception handling with appropriate logging
- Cache key generation based on modification time
- Read-only access to database files
- Proper resource cleanup

## Integration with Other Components

The database metadata extractor integrates with several other components in The
Aichemist Codex:

- **File Manager**: Provides supplementary information for database file
  operations
- **Search**: Enables searching by database properties and table names
- **Auto-Tagging**: Supplies metadata for automatic categorization of database
  files
- **Relationships**: Can establish connections between related database files
- **File Similarity**: Contributes data points for database similarity
  algorithms

## Configuration

The database metadata extractor has no specific configuration options beyond the
cache manager. It automatically adapts to the available information in each
database file.

## Next Steps and Future Enhancements

Planned improvements for the database metadata extraction include:

- Enhanced SQL parsing capabilities
- Table relationship visualization
- Query extraction and analysis from SQL dumps
- Database performance metric extraction
- Schema change detection between versions
- Data profiling capabilities for columns
- Integration with database documentation tools
- More comprehensive database type detection
- Support for additional database formats (MongoDB, Redis dumps)
