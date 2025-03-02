import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from src.file_reader.file_metadata import FileMetadata
from src.utils import AsyncFileIO

try:
    import whoosh.analysis
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.index import create_in, open_dir
    from whoosh.qparser import QueryParser
except ImportError:
    raise ImportError("Whoosh is not installed. Run `pip install whoosh`.")

try:
    import rapidfuzz
except ImportError:
    raise ImportError("RapidFuzz is not installed. Run `pip install rapidfuzz`.")

logger = logging.getLogger(__name__)

SEARCH_DB = "search_index.sqlite"


class SearchEngine:
    """Handles filename, full-text, metadata, and fuzzy search."""

    def __init__(self, index_dir: Path, db_path: Path = Path(SEARCH_DB)):
        self.index_dir = index_dir
        self.db_path = db_path
        self.schema = Schema(
            path=ID(stored=True, unique=True),
            content=TEXT(stored=False, analyzer=whoosh.analysis.StemmingAnalyzer()),
        )

        self._initialize_index()
        self._initialize_database()

    def _initialize_index(self):
        """Ensure Whoosh full-text search index is initialized correctly."""
        try:
            if not self.index_dir.exists():
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.index = create_in(self.index_dir, self.schema)
            elif not any(self.index_dir.iterdir()):  # If folder exists but is empty
                self.index = create_in(self.index_dir, self.schema)
            else:
                self.index = open_dir(self.index_dir)
        except Exception as e:
            logger.error(f"Whoosh index is missing or corrupted: {e}")
            self.index = create_in(
                self.index_dir, self.schema
            )  # Force re-creation if corrupt

    def _initialize_database(self):
        """Initialize SQLite database for metadata and fuzzy search with indexing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                filename TEXT,
                extension TEXT,
                size INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_filename ON files(filename);"
        )  # ✅ Faster lookups
        conn.commit()
        conn.close()

    def add_to_index(self, file_metadata: FileMetadata):
        """Ensure files are indexed properly in both SQLite and Whoosh."""

        try:
            if not file_metadata.path.exists():
                logger.warning(f"Skipping non-existent file: {file_metadata.path}")
                return

            # Use AsyncFileIO for reading file content if preview is empty
            preview_content = file_metadata.preview
            if not preview_content and file_metadata.mime_type.startswith("text/"):
                # Run AsyncFileIO.read in a synchronous context
                preview_content = asyncio.run(AsyncFileIO.read(file_metadata.path))
                if preview_content.startswith("# "):  # Error message or skipped file
                    logger.warning(
                        f"Error reading content for indexing: {preview_content}"
                    )
                    preview_content = f"[File content error: {file_metadata.path}]"

            # ✅ Whoosh Full-Text Indexing with Force Commit
            writer = self.index.writer()
            writer.add_document(
                path=str(file_metadata.path), content=preview_content or ""
            )
            writer.commit(merge=False)  # ✅ Ensures immediate commit

            # ✅ SQLite Storage
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO files (path, filename, extension, size, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        str(file_metadata.path),
                        file_metadata.path.name,
                        file_metadata.extension,
                        file_metadata.size,
                    ),
                )
                conn.commit()  # ✅ Ensure DB changes persist
        except Exception as e:
            logger.error(f"Error indexing file {file_metadata.path}: {e}")

    def search_filename(self, query: str) -> List[str]:
        """Search for files by exact or partial filename match."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT path FROM files WHERE filename LIKE ?", (f"%{query}%",)
            )
            results = [Path(row[0]).as_posix() for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error searching filenames: {e}")
            return []

    def fuzzy_search(self, query: str, threshold: float = 80.0) -> List[str]:
        """Perform fuzzy search on filenames using RapidFuzz."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT filename, path FROM files")
            all_files = cursor.fetchall()
            conn.close()

            matches = rapidfuzz.process.extract(
                query,
                {filename: path for filename, path in all_files},
                score_cutoff=threshold,
            )
            return [match[2] for match in matches]
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []

    def full_text_search(self, query: str) -> List[str]:
        """Perform full-text search on file contents."""
        try:
            with self.index.searcher() as searcher:
                query_parser = QueryParser("content", schema=self.index.schema)
                search_query = query_parser.parse(query)
                results = searcher.search(search_query, limit=20)
                return [result["path"] for result in results]
        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            return []

    def metadata_search(self, filters: Optional[Dict] = None) -> List[str]:
        """
        Search by metadata filters such as size, extension, and date.

        :param filters: Dictionary with optional keys:
            - "extension": List of file extensions to filter
            - "size_min": Minimum file size in bytes
            - "size_max": Maximum file size in bytes
            - "date_after": Filter for files modified after YYYY-MM-DD
            - "date_before": Filter for files modified before YYYY-MM-DD

        :return: List of matching file paths.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT path FROM files WHERE 1=1"
            params = []

            if filters:
                if "extension" in filters:
                    query += " AND extension IN ({})".format(
                        ",".join("?" for _ in filters["extension"])
                    )
                    params.extend(filters["extension"])

                if "size_min" in filters:
                    query += " AND size >= ?"
                    params.append(filters["size_min"])

                if "size_max" in filters:
                    query += " AND size <= ?"
                    params.append(filters["size_max"])

                if "date_after" in filters:
                    query += " AND updated_at >= ?"
                    params.append(filters["date_after"])

                if "date_before" in filters:
                    query += " AND updated_at <= ?"
                    params.append(filters["date_before"])

            cursor.execute(query, params)
            results = [Path(row[0]).as_posix() for row in cursor.fetchall()]
            conn.close()
            return results

        except Exception as e:
            logger.error(f"Error in metadata search: {e}")
            return []


# Example Usage:
if __name__ == "__main__":
    search_engine = SearchEngine(index_dir=Path("search_index"))

    # Example file metadata for indexing
    file_metadata = FileMetadata(
        path=Path("/documents/example.txt"),
        mime_type="text/plain",
        size=1024,
        extension=".txt",
        preview="This is an example document containing searchable text.",
    )

    search_engine.add_to_index(file_metadata)

    # Perform searches
    print("Filename Search:", search_engine.search_filename("example"))
    print("Fuzzy Search:", search_engine.fuzzy_search("exmple"))
    print("Full-Text Search:", search_engine.full_text_search("searchable"))

    # Metadata-based search example
    metadata_filters = {"extension": [".txt"], "size_min": 500, "size_max": 2000}
    print("Metadata Search:", search_engine.metadata_search(metadata_filters))
