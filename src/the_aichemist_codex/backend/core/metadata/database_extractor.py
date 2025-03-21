"""
Database metadata extraction for The Aichemist Codex.

This module provides functionality to extract metadata from database files,
including schema information, table counts, column details, and other
database-specific metadata.
"""

# Standard library imports
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

# Third-party imports will be added via pip during implementation
# For now we'll implement with standard library for SQLite
# Later we can add sqlite-utils if needed
# Local application imports
from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager
from the_aichemist_codex.backend.utils.io.mime_type_detector import MimeTypeDetector

# Initialize logger with proper name
logger = logging.getLogger(__name__)


class DatabaseMetadataExtractor(BaseMetadataExtractor):
    """
    Metadata extractor for database files.

    This extractor can process various database formats (SQLite, MySQL dumps,
    PostgreSQL dumps) and extract rich metadata including:
    - Database type and version
    - Schema information (tables, views, indexes)
    - Table statistics (row counts, column counts)
    - Size metrics and performance indicators
    - SQL statement analysis for dump files
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = [
        "application/x-sqlite3",
        "application/vnd.sqlite3",
        "text/x-sql",
        "application/sql",
        "application/x-sql",
    ]

    # File extensions to format mappings
    FORMAT_MAP = {
        ".db": "sqlite",
        ".sqlite": "sqlite",
        ".sqlite3": "sqlite",
        ".sql": "sql_dump",
        ".mysql": "mysql_dump",
        ".pgsql": "postgresql_dump",
    }

    @property
    def supported_mime_types(self) -> list[str]:
        """Get the list of MIME types this extractor supports.

        Returns:
            List of supported MIME types
        """
        return self.SUPPORTED_MIME_TYPES

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        """Initialize the database metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()

    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """Extract metadata from a database file.

        Args:
            file_path: Path to the database file
            content: File content (used for SQL dumps)
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted database metadata
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Database file not found: {path}")
            return {}

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

        # Check if this is a supported database type
        if mime_type not in self.supported_mime_types:
            # Try checking extension as fallback
            ext = path.suffix.lower()
            if ext not in self.FORMAT_MAP:
                logger.debug(f"Unsupported database type: {mime_type} for file: {path}")
                return {}

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"db_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached database metadata for {path}")
                return cached_data

        # Process the database file
        try:
            result = await self._process_database(path, content)

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error extracting database metadata from {path}: {str(e)}")
            return {}

    async def _process_database(
        self, path: Path, content: str | None
    ) -> dict[str, Any]:
        """Process a database file to extract metadata.

        Args:
            path: Path to the database file
            content: File content (used for SQL dumps)

        Returns:
            Dictionary containing extracted database metadata
        """
        result = {
            "metadata_type": "database",
            "format": {},
            "schema": {},
            "statistics": {},
        }

        # Determine database type from extension
        ext = path.suffix.lower()
        db_type = self.FORMAT_MAP.get(ext, "unknown")
        result["format"]["type"] = db_type

        # Process based on database type
        if db_type == "sqlite":
            self._process_sqlite(path, result)
        elif "dump" in db_type:
            self._process_sql_dump(path, content, db_type, result)

        return result

    def _process_sqlite(self, path: Path, result: dict[str, Any]) -> None:
        """Process SQLite database file and extract metadata.

        Args:
            path: Path to the SQLite database file
            result: Dictionary to update with extracted metadata
        """
        try:
            # Record basic file information
            result["format"]["file_size"] = path.stat().st_size

            # Connect to the database in read-only mode
            uri = f"file:{str(path)}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get SQLite version
            cursor.execute("SELECT sqlite_version()")
            result["format"]["sqlite_version"] = cursor.fetchone()[0]

            # Get list of tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Get list of views
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            )
            views = [row[0] for row in cursor.fetchall()]

            # Store basic schema information
            result["schema"]["tables"] = []
            result["schema"]["table_count"] = len(tables)
            result["schema"]["view_count"] = len(views)
            result["schema"]["total_objects"] = len(tables) + len(views)

            # Extract detailed table information
            total_rows = 0
            total_indexes = 0

            for table_name in tables:
                table_info = {
                    "name": table_name,
                    "columns": [],
                    "indexes": [],
                }

                # Get table columns
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns = cursor.fetchall()

                for column in columns:
                    table_info["columns"].append(
                        {
                            "name": column["name"],
                            "type": column["type"],
                            "primary_key": bool(column["pk"]),
                            "not_null": bool(column["notnull"]),
                        }
                    )

                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                    row_count = cursor.fetchone()[0]
                    table_info["row_count"] = row_count
                    total_rows += row_count
                except sqlite3.Error:
                    # Table might be corrupt or virtual
                    table_info["row_count"] = 0

                # Get indexes
                cursor.execute(f"PRAGMA index_list('{table_name}')")
                indexes = cursor.fetchall()
                table_info["index_count"] = len(indexes)
                total_indexes += len(indexes)

                for idx in indexes:
                    # Get columns in the index
                    cursor.execute(f"PRAGMA index_info('{idx['name']}')")
                    index_columns = [row["name"] for row in cursor.fetchall()]

                    table_info["indexes"].append(
                        {
                            "name": idx["name"],
                            "columns": index_columns,
                            "unique": bool(idx["unique"]),
                        }
                    )

                result["schema"]["tables"].append(table_info)

            # Extract view information
            result["schema"]["views"] = []
            for view_name in views:
                # Get view definition
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE type='view' AND name=?",
                    (view_name,),
                )
                view_def = cursor.fetchone()[0]

                result["schema"]["views"].append(
                    {
                        "name": view_name,
                        "definition": view_def,
                    }
                )

            # Add statistics
            result["statistics"]["total_rows"] = total_rows
            result["statistics"]["total_indexes"] = total_indexes
            result["statistics"]["avg_rows_per_table"] = (
                total_rows / len(tables) if tables else 0
            )

            # Database file size analysis
            bytes_per_row = (
                result["format"]["file_size"] / total_rows if total_rows > 0 else 0
            )
            result["statistics"]["bytes_per_row"] = round(bytes_per_row, 2)

            # Add user-friendly summary
            result["summary"] = (
                f"SQLite database with {len(tables)} tables, "
                f"{len(views)} views, and approximately {total_rows} total rows"
            )

            # Close connection
            conn.close()

        except Exception as e:
            logger.debug(f"Error processing SQLite database {path}: {str(e)}")
            # Add info about the error to the result
            result["error"] = f"Error processing SQLite database: {str(e)}"

    def _process_sql_dump(
        self, path: Path, content: str | None, db_type: str, result: dict[str, Any]
    ) -> None:
        """Process SQL dump file and extract metadata.

        Args:
            path: Path to the SQL dump file
            content: File content if already loaded
            db_type: Type of SQL dump (mysql_dump, postgresql_dump, etc.)
            result: Dictionary to update with extracted metadata
        """
        try:
            # Load content if not provided
            if content is None:
                with open(path, encoding="utf-8", errors="replace") as f:
                    content = f.read()

            # Record basic information
            result["format"]["file_size"] = path.stat().st_size
            result["format"]["dump_type"] = db_type

            # Extract information based on SQL statements
            if db_type == "mysql_dump":
                self._analyze_mysql_dump(content, result)
            elif db_type == "postgresql_dump":
                self._analyze_postgresql_dump(content, result)
            else:
                self._analyze_generic_sql(content, result)

        except Exception as e:
            logger.debug(f"Error processing SQL dump {path}: {str(e)}")
            # Add info about the error to the result
            result["error"] = f"Error processing SQL dump: {str(e)}"

    def _analyze_generic_sql(self, content: str, result: dict[str, Any]) -> None:
        """Analyze generic SQL content to extract metadata.

        Args:
            content: SQL content to analyze
            result: Dictionary to update with extracted metadata
        """
        # Extract CREATE TABLE statements
        create_table_pattern = re.compile(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\`\[\"\']?(\w+)[\`\[\"\']?",
            re.IGNORECASE,
        )
        tables = create_table_pattern.findall(content)

        # Extract CREATE VIEW statements
        create_view_pattern = re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+[\`\[\"\']?(\w+)[\`\[\"\']?",
            re.IGNORECASE,
        )
        views = create_view_pattern.findall(content)

        # Extract INSERT statements
        insert_pattern = re.compile(r"INSERT\s+INTO", re.IGNORECASE)
        inserts = len(insert_pattern.findall(content))

        # Extract ALTER TABLE statements
        alter_pattern = re.compile(r"ALTER\s+TABLE", re.IGNORECASE)
        alters = len(alter_pattern.findall(content))

        # Try to detect database type from content
        db_type = "generic_sql"
        if "ENGINE=InnoDB" in content or "ENGINE=MyISAM" in content:
            db_type = "mysql"
        elif "PostgreSQL database dump" in content or "SET search_path =" in content:
            db_type = "postgresql"
        elif "BEGIN TRANSACTION;" in content and "COMMIT;" in content:
            db_type = "sqlite"

        # Record findings
        result["format"]["detected_type"] = db_type
        result["schema"]["table_count"] = len(tables)
        result["schema"]["view_count"] = len(views)
        result["schema"]["tables"] = tables
        result["schema"]["views"] = views

        result["statistics"]["insert_statements"] = inserts
        result["statistics"]["alter_statements"] = alters
        result["statistics"]["total_statements"] = (
            len(tables) + len(views) + inserts + alters
        )

        # Add user-friendly summary
        result["summary"] = (
            f"SQL dump with {len(tables)} table definitions, "
            f"{len(views)} view definitions, and {inserts} insert statements"
        )

    def _analyze_mysql_dump(self, content: str, result: dict[str, Any]) -> None:
        """Analyze MySQL dump content to extract metadata.

        Args:
            content: MySQL dump content to analyze
            result: Dictionary to update with extracted metadata
        """
        # First run generic SQL analysis
        self._analyze_generic_sql(content, result)

        # Extract MySQL-specific information

        # Try to extract MySQL version
        version_pattern = re.compile(r"-- Server version\s+(\d+\.\d+\.\d+)")
        version_match = version_pattern.search(content)
        if version_match:
            result["format"]["mysql_version"] = version_match.group(1)

        # Look for database name
        db_name_pattern = re.compile(r"-- Current Database: `([^`]+)`")
        db_name_match = db_name_pattern.search(content)
        if db_name_match:
            result["format"]["database_name"] = db_name_match.group(1)

        # Extract character set and collation
        charset_pattern = re.compile(r"DEFAULT CHARSET=(\w+)")
        charset_matches = charset_pattern.findall(content)
        if charset_matches:
            # Use the most common charset
            from collections import Counter

            charset_counts = Counter(charset_matches)
            result["format"]["default_charset"] = charset_counts.most_common(1)[0][0]

        # Update the detected type
        result["format"]["detected_type"] = "mysql"

        # Update summary
        if "database_name" in result["format"]:
            result["summary"] = (
                f"MySQL dump of database '{result['format']['database_name']}' "
                f"with {result['schema']['table_count']} tables, "
                f"{result['schema']['view_count']} views, and "
                f"{result['statistics']['insert_statements']} insert statements"
            )
        else:
            result["summary"] = (
                f"MySQL dump with {result['schema']['table_count']} tables, "
                f"{result['schema']['view_count']} views, and "
                f"{result['statistics']['insert_statements']} insert statements"
            )

    def _analyze_postgresql_dump(self, content: str, result: dict[str, Any]) -> None:
        """Analyze PostgreSQL dump content to extract metadata.

        Args:
            content: PostgreSQL dump content to analyze
            result: Dictionary to update with extracted metadata
        """
        # First run generic SQL analysis
        self._analyze_generic_sql(content, result)

        # Extract PostgreSQL-specific information

        # Try to extract PostgreSQL version
        version_pattern = re.compile(
            r"-- PostgreSQL database dump\s*\n--\s*\n-- PostgreSQL version (\d+\.\d+)"
        )
        version_match = version_pattern.search(content)
        if version_match:
            result["format"]["postgresql_version"] = version_match.group(1)

        # Look for database name
        db_name_pattern = re.compile(r"-- Name: ([^;]+);")
        db_name_match = db_name_pattern.search(content)
        if db_name_match:
            result["format"]["database_name"] = db_name_match.group(1).strip()

        # Extract schemas
        schema_pattern = re.compile(r"CREATE SCHEMA (?:IF NOT EXISTS )?([^\s;]+)")
        schemas = schema_pattern.findall(content)
        result["schema"]["schemas"] = schemas
        result["schema"]["schema_count"] = len(schemas)

        # Look for extensions
        extension_pattern = re.compile(r"CREATE EXTENSION (?:IF NOT EXISTS )?([^\s;]+)")
        extensions = extension_pattern.findall(content)
        result["schema"]["extensions"] = extensions
        result["schema"]["extension_count"] = len(extensions)

        # Update the detected type
        result["format"]["detected_type"] = "postgresql"

        # Update summary
        if "database_name" in result["format"]:
            result["summary"] = (
                f"PostgreSQL dump of database '{result['format']['database_name']}' "
                f"with {result['schema']['table_count']} tables, "
                f"{result['schema']['view_count']} views"
            )
        else:
            result["summary"] = (
                f"PostgreSQL dump with {result['schema']['table_count']} tables, "
                f"{result['schema']['view_count']} views"
            )


# Register the extractor
MetadataExtractorRegistry.register(DatabaseMetadataExtractor)
