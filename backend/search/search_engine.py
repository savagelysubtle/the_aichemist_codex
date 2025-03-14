import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import rapidfuzz
import whoosh.analysis
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from backend.config.settings import FEATURES, REGEX_MAX_RESULTS, SIMILARITY_MAX_RESULTS
from backend.file_reader.file_metadata import FileMetadata
from backend.search.providers.regex_provider import RegexSearchProvider
from backend.search.providers.similarity_provider import SimilarityProvider
from backend.utils import AsyncFileIO
from backend.utils.batch_processor import BatchProcessor
from backend.utils.cache_manager import CacheManager
from backend.utils.sqlasync_io import AsyncSQL

# Import FAISS and SentenceTransformer for semantic search.
try:
    import faiss
except ImportError:
    raise ImportError("FAISS is not installed. Run `pip install faiss-cpu`.")
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers is not installed. Run `pip install sentence-transformers`."
    )

logger = logging.getLogger(__name__)
SEARCH_DB = "search_index.sqlite"


class SearchEngine:
    """Handles filename, full-text, metadata, fuzzy, and semantic search using asynchronous SQL operations.

    Semantic search is implemented using FAISS and sentence-transformers.
    """

    def __init__(
        self,
        index_dir: Path,
        db_path: Path = Path(SEARCH_DB),
        cache_manager: Optional[CacheManager] = None,
    ):
        self.index_dir = index_dir
        self.db_path = db_path
        self.schema = Schema(
            path=ID(stored=True, unique=True),
            content=TEXT(stored=False, analyzer=whoosh.analysis.StemmingAnalyzer()),
        )
        self._initialize_index()
        self._initialize_database_sync()
        self.async_db = AsyncSQL(db_path)  # Async SQL utility
        self.cache_manager = cache_manager

        # Initialize search providers
        if FEATURES.get("enable_regex_search", False):
            self.regex_provider = RegexSearchProvider(cache_manager=cache_manager)
        else:
            self.regex_provider = None

        # Initialize semantic search components.
        self.embedding_model = None
        self.semantic_index = None  # FAISS index instance.
        self.semantic_mapping: List[str] = []  # Maps vector IDs to file paths.

        # Only initialize embedding model if semantic search is enabled
        if FEATURES.get("enable_semantic_search", False):
            try:
                logger.info("Initializing embedding model for semantic search...")
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Embedding model initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize embedding model: {e}")
                logger.warning("Semantic search will be disabled.")

        # Initialize similarity provider if enabled
        if (
            FEATURES.get("enable_similarity_search", False)
            and self.embedding_model is not None
        ):
            self.similarity_provider = SimilarityProvider(
                embedding_model=self.embedding_model,
                vector_index=self.semantic_index,
                path_mapping=self.semantic_mapping,
                cache_manager=cache_manager,
            )
        else:
            self.similarity_provider = None

    def _initialize_index(self):
        """Ensure Whoosh full-text search index is initialized correctly."""
        try:
            if not self.index_dir.exists():
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.index = create_in(self.index_dir, self.schema)
            elif not any(self.index_dir.iterdir()):
                self.index = create_in(self.index_dir, self.schema)
            else:
                self.index = open_dir(self.index_dir)
        except Exception as e:
            logger.error(f"Whoosh index is missing or corrupted: {e}")
            self.index = create_in(self.index_dir, self.schema)

    def _initialize_database_sync(self):
        """Initialize SQLite database for metadata and fuzzy search synchronously."""
        import sqlite3

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
                updated_at TEXT,
                tags TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON files(filename);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON files(tags);")
        conn.commit()
        conn.close()

    async def add_to_index_async(self, file_metadata: FileMetadata):
        """Asynchronously index a file in Whoosh, SQLite, and the semantic search index."""
        try:
            if not file_metadata.path.exists():
                logger.warning(f"Skipping non-existent file: {file_metadata.path}")
                return

            # Use AsyncFileIO to read file content if preview is empty.
            preview_content = file_metadata.preview
            if not preview_content and file_metadata.mime_type.startswith("text/"):
                preview_content = await AsyncFileIO.read(file_metadata.path)
                if preview_content.startswith("# "):
                    logger.warning(
                        f"Error reading content for indexing: {preview_content}"
                    )
                    preview_content = f"[File content error: {file_metadata.path}]"

            # Whoosh indexing (run in a separate thread).
            def index_document():
                writer = self.index.writer()
                writer.add_document(
                    path=str(file_metadata.path), content=preview_content or ""
                )
                writer.commit(merge=False)

            await asyncio.to_thread(index_document)

            # Convert custom tags (if provided) into a comma-separated string.
            tags_str = ""
            if hasattr(file_metadata, "tags") and file_metadata.tags:
                tags_str = ",".join(file_metadata.tags)

            # Asynchronous SQLite insertion.
            sql = """
                    INSERT OR REPLACE INTO files (path, filename, extension, size, created_at, updated_at, tags)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?)
                    """
            params = (
                str(file_metadata.path),
                file_metadata.path.name,
                file_metadata.extension,
                file_metadata.size,
                tags_str,
            )
            await self.async_db.execute(sql, params, commit=True)

            # Semantic indexing: compute embedding and add to FAISS index.
            if file_metadata.mime_type.startswith("text") and preview_content:
                embedding = await asyncio.to_thread(
                    self.embedding_model.encode, preview_content
                )
                import numpy as np

                embedding = np.array(embedding, dtype="float32").reshape(1, -1)
                dim = embedding.shape[1]
                if self.semantic_index is None:
                    self.semantic_index = faiss.IndexFlatL2(dim)
                self.semantic_index.add(embedding)
                self.semantic_mapping.append(str(file_metadata.path))
        except Exception as e:
            logger.error(f"Error indexing file {file_metadata.path}: {e}")

    async def search_filename_async(self, query: str) -> List[str]:
        """Asynchronously search for files by exact or partial filename match."""
        sql = "SELECT path FROM files WHERE filename LIKE ?"
        rows = await self.async_db.fetchall(sql, (f"%{query}%",))
        return [Path(row[0]).as_posix() for row in rows]

    async def fuzzy_search_async(
        self, query: str, threshold: float = 80.0
    ) -> List[str]:
        """Asynchronously perform fuzzy search on filenames using RapidFuzz."""
        sql = "SELECT filename, path FROM files"
        all_files = await self.async_db.fetchall(sql)
        mapping = {filename: path for filename, path in all_files}
        matches = rapidfuzz.process.extract(query, mapping, score_cutoff=threshold)
        return [match[2] for match in matches]

    def full_text_search(self, query: str) -> List[str]:
        """Perform full-text search on file contents (synchronous)."""
        try:
            with self.index.searcher() as searcher:
                query_parser = QueryParser("content", schema=self.index.schema)
                search_query = query_parser.parse(query)
                results = searcher.search(search_query, limit=20)
                return [result["path"] for result in results]
        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            return []

    async def metadata_search_async(self, filters: Optional[Dict] = None) -> List[str]:
        """
        Asynchronously search by metadata filters (size, extension, timestamps, and custom tags).

        :param filters: Dictionary with keys: extension, size_min, size_max, date_after, date_before, tags.
        :return: List of matching file paths.
        """
        query_str = "SELECT path FROM files WHERE 1=1"
        params = []
        if filters:
            if "extension" in filters:
                query_str += (
                    " AND extension IN ("
                    + ",".join("?" for _ in filters["extension"])
                    + ")"
                )
                params.extend(filters["extension"])
            if "size_min" in filters:
                query_str += " AND size >= ?"
                params.append(filters["size_min"])
            if "size_max" in filters:
                query_str += " AND size <= ?"
                params.append(filters["size_max"])
            if "date_after" in filters:
                query_str += " AND updated_at >= ?"
                params.append(filters["date_after"])
            if "date_before" in filters:
                query_str += " AND updated_at <= ?"
                params.append(filters["date_before"])
            if "tags" in filters:
                tag_conditions = []
                for tag in filters["tags"]:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    query_str += " AND (" + " OR ".join(tag_conditions) + ")"
        rows = await self.async_db.fetchall(query_str, tuple(params))
        return [Path(row[0]).as_posix() for row in rows]

    async def semantic_search_async(self, query: str, top_k: int = 5) -> List[str]:
        """
        Asynchronously perform semantic search using FAISS and sentence-transformers.

        :param query: Query string to encode.
        :param top_k: Number of nearest neighbors to return.
        :return: List of file paths for the top matching documents.
        """
        if self.embedding_model is None:
            logger.warning(
                "Semantic search is disabled or model initialization failed. Cannot perform semantic search."
            )
            return []

        if self.semantic_index is None or self.semantic_index.ntotal == 0:
            logger.warning(
                "Semantic index is empty. No semantic search can be performed."
            )
            return []
        query_embedding = await asyncio.to_thread(self.embedding_model.encode, query)
        import numpy as np

        query_embedding = np.array(query_embedding, dtype="float32").reshape(1, -1)
        distances, indices = self.semantic_index.search(query_embedding, top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.semantic_mapping):
                results.append(self.semantic_mapping[idx])
        return results

    async def add_to_index_batch(
        self, file_metadata_list: List[FileMetadata], batch_size: int = 20
    ) -> List[Path]:
        """
        Add multiple files to the search index in batches.

        Args:
            file_metadata_list: List of file metadata objects to index
            batch_size: Number of files to process in each batch

        Returns:
            List of successfully indexed file paths
        """

        async def index_single_file(metadata: FileMetadata) -> Optional[Path]:
            try:
                await self.add_to_index_async(metadata)
                return metadata.path
            except Exception as e:
                logger.error(f"Error indexing file {metadata.path}: {e}")
                return None

        results = await BatchProcessor.process_batch(
            file_metadata_list, index_single_file, batch_size=batch_size
        )

        # Filter out None values from failed operations
        return [result for result in results if result is not None]

    async def regex_search_async(
        self,
        pattern: str,
        file_paths: List[Path] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
    ) -> List[str]:
        """
        Perform regex pattern search on file contents.

        Args:
            pattern: The regex pattern to search for
            file_paths: Optional list of file paths to search (if None, uses all indexed files)
            case_sensitive: Whether the search should be case sensitive
            whole_word: Whether to match whole words only

        Returns:
            List of file paths containing matches
        """
        if not FEATURES.get("enable_regex_search", False) or not self.regex_provider:
            logger.warning("Regex search is disabled or provider not initialized")
            return []

        if not pattern:
            return []

        # If no file paths provided, get all indexed files
        if file_paths is None:
            sql = "SELECT path FROM files"
            rows = await self.async_db.fetchall(sql)
            file_paths = [Path(row[0]) for row in rows]
            logger.info(
                f"Retrieved {len(file_paths)} files from the database for regex search"
            )

        logger.info(f"Performing regex search on {len(file_paths)} files")

        # Perform regex search
        try:
            results = await self.regex_provider.search(
                query=pattern,
                file_paths=file_paths,
                max_results=REGEX_MAX_RESULTS,
                case_sensitive=case_sensitive,
                whole_word=whole_word,
            )
            logger.info(f"Regex search for '{pattern}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in regex search: {e}")
            return []

    def search(
        self, query: str, method: str = "fulltext", case_sensitive: bool = False
    ) -> List[Dict]:
        """
        Unified search method that dispatches to the appropriate search function based on method.

        Args:
            query: The search query
            method: The search method to use (filename, fulltext, fuzzy, regex)
            case_sensitive: Whether the search should be case sensitive (for fulltext)

        Returns:
            List of dictionaries containing search results with path and score
        """
        if not query:
            return []

        try:
            if method == "filename":
                # Run filename search asynchronously
                paths = asyncio.run(self.search_filename_async(query))
                return [{"path": path, "score": 1.0} for path in paths]

            elif method == "fuzzy":
                # Run fuzzy search asynchronously
                paths = asyncio.run(self.fuzzy_search_async(query))
                return [{"path": path, "score": 0.8} for path in paths]

            elif method == "fulltext":
                # Fulltext search is synchronous
                # TODO: Add case sensitivity support to fulltext search
                paths = self.full_text_search(query)
                return [{"path": path, "score": 0.9} for path in paths]

            else:
                logger.warning(f"Unsupported search method: {method}")
                return []

        except Exception as e:
            logger.error(f"Error in search ({method}): {e}")
            return []

    async def find_similar_files_async(
        self,
        file_path: Path,
        threshold: float = None,
        max_results: int = SIMILARITY_MAX_RESULTS,
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Find files that are similar to the given file using vector embeddings.

        Args:
            file_path: The file to find similar files for
            threshold: Minimum similarity score (0.0-1.0), defaults to settings.SIMILARITY_THRESHOLD
            max_results: Maximum number of results to return

        Returns:
            List of dictionaries containing paths and similarity scores
        """
        if (
            not FEATURES.get("enable_similarity_search", False)
            or not self.similarity_provider
        ):
            logger.warning("Similarity search is disabled or provider not initialized")
            return []

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []

        try:
            # Find similar files
            similar_files = await self.similarity_provider.find_similar_files(
                file_path=file_path, threshold=threshold, max_results=max_results
            )

            # Format results
            results = [
                {"path": path, "similarity": score} for path, score in similar_files
            ]

            logger.debug(f"Found {len(results)} files similar to {file_path}")
            return results
        except Exception as e:
            logger.error(f"Error finding similar files: {e}")
            return []

    async def find_file_groups_async(
        self,
        file_paths: Optional[List[Path]] = None,
        threshold: float = None,
        min_group_size: int = None,
    ) -> List[List[str]]:
        """
        Find groups of similar files using hierarchical clustering.

        Args:
            file_paths: List of file paths to group (if None, uses all indexed files)
            threshold: Similarity threshold for group membership
            min_group_size: Minimum number of files to form a group

        Returns:
            List of file path groups where each group contains similar files
        """
        if (
            not FEATURES.get("enable_similarity_search", False)
            or not self.similarity_provider
        ):
            logger.warning("Similarity search is disabled or provider not initialized")
            return []

        try:
            # Find file groups
            groups = await self.similarity_provider.find_file_groups(
                file_paths=file_paths,
                threshold=threshold,
                min_group_size=min_group_size,
            )

            logger.debug(f"Found {len(groups)} groups of similar files")
            return groups
        except Exception as e:
            logger.error(f"Error finding file groups: {e}")
            return []


# Example Usage:
if __name__ == "__main__":

    async def main():
        search_engine = SearchEngine(index_dir=Path("search_index"))
        # Example file metadata with custom tags.
        file_metadata = FileMetadata(
            path=Path("/documents/example.txt"),
            mime_type="text/plain",
            size=1024,
            extension=".txt",
            preview="This is an example document containing searchable text.",
        )
        file_metadata.tags = ["important", "example"]
        await search_engine.add_to_index_async(file_metadata)
        filename_results = await search_engine.search_filename_async("example")
        fuzzy_results = await search_engine.fuzzy_search_async("exmple")
        full_text_results = search_engine.full_text_search("searchable")
        metadata_filters = {
            "extension": [".txt"],
            "size_min": 500,
            "size_max": 2000,
            "tags": ["important"],
        }
        metadata_results = await search_engine.metadata_search_async(metadata_filters)
        semantic_results = await search_engine.semantic_search_async("document text")
        print("Filename Search:", filename_results)
        print("Fuzzy Search:", fuzzy_results)
        print("Full-Text Search:", full_text_results)
        print("Metadata Search:", metadata_results)
        print("Semantic Search:", semantic_results)

    asyncio.run(main())
