"""Database schema for the tag management system."""

import logging
from pathlib import Path

from the_aichemist_codex.infrastructure.utils.io.sqlasync_io import AsyncSQL

logger = logging.getLogger(__name__)

# SQL statements for table creation
CREATE_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_TAG_HIERARCHY_TABLE = """
CREATE TABLE IF NOT EXISTS tag_hierarchy (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES tags(id) ON DELETE CASCADE
)
"""

CREATE_FILE_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS file_tags (
    file_path TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    source TEXT DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (file_path, tag_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
)
"""

# Indexes for performance
CREATE_TAG_INDEX = "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)"
CREATE_FILE_TAGS_PATH_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_file_tags_path ON file_tags(file_path)"
)
CREATE_FILE_TAGS_TAG_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id)"
)

# Triggers
CREATE_TAGS_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_tags_modified_timestamp
AFTER UPDATE ON tags
FOR EACH ROW
BEGIN
    UPDATE tags SET modified_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END
"""


class TagSchema:
    """Manages the database schema for the tag management system."""

    def __init__(self, db_path: Path):
        """
        Initialize with database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db = AsyncSQL(db_path)
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the database schema.

        Raises:
            Exception: If database initialization fails
        """
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create tables
            await self.db.execute(CREATE_TAGS_TABLE, commit=True)
            await self.db.execute(CREATE_TAG_HIERARCHY_TABLE, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_TABLE, commit=True)

            # Create indexes
            await self.db.execute(CREATE_TAG_INDEX, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_PATH_INDEX, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_TAG_INDEX, commit=True)

            # Create triggers
            await self.db.execute(CREATE_TAGS_UPDATE_TRIGGER, commit=True)

            self._initialized = True
            logger.info(f"Initialized tag database at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize tag database: {e}")
            raise

    async def reset(self) -> None:
        """
        Reset the database by dropping and recreating all tables.

        This is primarily intended for testing.

        Raises:
            Exception: If reset fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Drop tables in reverse order of dependencies
            await self.db.execute("DROP TABLE IF EXISTS file_tags", commit=True)
            await self.db.execute("DROP TABLE IF EXISTS tag_hierarchy", commit=True)
            await self.db.execute("DROP TABLE IF EXISTS tags", commit=True)

            # Recreate the schema
            await self.initialize()
            logger.info("Reset tag database schema")

        except Exception as e:
            logger.error(f"Failed to reset tag database: {e}")
            raise
