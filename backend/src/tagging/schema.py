"""
Database schema for tag management system.

This module defines the SQLite schema for storing tags, tag hierarchies,
and file-tag associations.
"""

import logging
from pathlib import Path

from backend.src.utils.sqlasync_io import AsyncSQL

logger = logging.getLogger(__name__)

# SQL statements for creating database tables
CREATE_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_TAG_HIERARCHY_TABLE = """
CREATE TABLE IF NOT EXISTS tag_hierarchy (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES tags (id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES tags (id) ON DELETE CASCADE,
    CHECK (parent_id != child_id)
);
"""

CREATE_FILE_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    source TEXT NOT NULL, -- 'manual', 'auto', 'suggested'
    confidence REAL DEFAULT 1.0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
    UNIQUE (file_path, tag_id)
);
"""

CREATE_TAG_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags (name);
"""

CREATE_FILE_TAGS_PATH_INDEX = """
CREATE INDEX IF NOT EXISTS idx_file_tags_path ON file_tags (file_path);
"""

CREATE_FILE_TAGS_TAG_INDEX = """
CREATE INDEX IF NOT EXISTS idx_file_tags_tag_id ON file_tags (tag_id);
"""

# Triggers to update modified_at timestamp
CREATE_TAGS_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_tags_modified_at
AFTER UPDATE ON tags
BEGIN
    UPDATE tags SET modified_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


class TagSchema:
    """
    Helper class for managing the tag database schema.

    This class provides methods for common database operations related
    to the tag management system.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the TagSchema with a database path.

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

            # Recreate tables
            await self.db.execute(CREATE_TAGS_TABLE, commit=True)
            await self.db.execute(CREATE_TAG_HIERARCHY_TABLE, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_TABLE, commit=True)

            # Recreate indexes
            await self.db.execute(CREATE_TAG_INDEX, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_PATH_INDEX, commit=True)
            await self.db.execute(CREATE_FILE_TAGS_TAG_INDEX, commit=True)

            # Recreate triggers
            await self.db.execute(CREATE_TAGS_UPDATE_TRIGGER, commit=True)

            logger.info("Reset tag database schema")

        except Exception as e:
            logger.error(f"Failed to reset tag database: {e}")
            raise
