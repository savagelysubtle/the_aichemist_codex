"""
Database schema for tag management system.

This module defines the SQLite schema for storing tags, tag hierarchies,
and file-tag associations. It provides functions for creating and initializing
the database tables.
"""

import logging
import sqlite3
from pathlib import Path

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


async def init_db(db_path: Path) -> sqlite3.Connection:
    """
    Initialize the database and create necessary tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection object

    Raises:
        sqlite3.Error: If database initialization fails
    """
    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create database connection
        conn = sqlite3.connect(str(db_path))

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create tables
        conn.execute(CREATE_TAGS_TABLE)
        conn.execute(CREATE_TAG_HIERARCHY_TABLE)
        conn.execute(CREATE_FILE_TAGS_TABLE)

        # Create indexes
        conn.execute(CREATE_TAG_INDEX)
        conn.execute(CREATE_FILE_TAGS_PATH_INDEX)
        conn.execute(CREATE_FILE_TAGS_TAG_INDEX)

        # Create triggers
        conn.execute(CREATE_TAGS_UPDATE_TRIGGER)

        # Commit changes
        conn.commit()

        logger.info(f"Initialized tag database at {db_path}")
        return conn

    except sqlite3.Error as e:
        logger.error(f"Failed to initialize tag database: {e}")
        raise


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
        self.conn = None

    async def initialize(self) -> None:
        """
        Initialize the database schema.

        Raises:
            sqlite3.Error: If initialization fails
        """
        self.conn = await init_db(self.db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    async def reset(self) -> None:
        """
        Reset the database by dropping and recreating all tables.

        This is primarily intended for testing.

        Raises:
            sqlite3.Error: If reset fails
        """
        if not self.conn:
            await self.initialize()

        try:
            # Drop tables in reverse order of dependencies
            self.conn.execute("DROP TABLE IF EXISTS file_tags")
            self.conn.execute("DROP TABLE IF EXISTS tag_hierarchy")
            self.conn.execute("DROP TABLE IF EXISTS tags")

            # Recreate tables
            self.conn.execute(CREATE_TAGS_TABLE)
            self.conn.execute(CREATE_TAG_HIERARCHY_TABLE)
            self.conn.execute(CREATE_FILE_TAGS_TABLE)

            # Recreate indexes
            self.conn.execute(CREATE_TAG_INDEX)
            self.conn.execute(CREATE_FILE_TAGS_PATH_INDEX)
            self.conn.execute(CREATE_FILE_TAGS_TAG_INDEX)

            # Recreate triggers
            self.conn.execute(CREATE_TAGS_UPDATE_TRIGGER)

            # Commit changes
            self.conn.commit()

            logger.info("Reset tag database schema")

        except sqlite3.Error as e:
            logger.error(f"Failed to reset tag database: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """
        Get the database connection.

        Returns:
            sqlite3.Connection: Database connection

        Raises:
            RuntimeError: If the connection is not initialized
        """
        if not self.conn:
            raise RuntimeError(
                "Database connection not initialized. Call initialize() first."
            )
        return self.conn
