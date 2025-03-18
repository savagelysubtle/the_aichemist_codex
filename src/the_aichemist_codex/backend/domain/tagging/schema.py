"""
Database schema for tag management system.

This module defines the SQLite schema for storing tags, tag hierarchies,
and file-tag associations.
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

# Indexes for improving query performance
CREATE_FILE_TAGS_PATH_IDX = """
CREATE INDEX IF NOT EXISTS idx_file_tags_path ON file_tags(file_path);
"""

CREATE_FILE_TAGS_TAG_IDX = """
CREATE INDEX IF NOT EXISTS idx_file_tags_tag_id ON file_tags(tag_id);
"""


class TagSchema:
    """
    Manages the database schema for the tagging system.

    This class is responsible for creating and initializing the database
    tables for the tagging system.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the TagSchema with a database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    async def initialize(self) -> None:
        """
        Initialize the database schema.

        Creates the necessary tables and indexes if they don't exist.

        Raises:
            Exception: If initialization fails
        """
        try:
            # Ensure the parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create connection and execute schema creation statements
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create tables
            cursor.execute(CREATE_TAGS_TABLE)
            cursor.execute(CREATE_TAG_HIERARCHY_TABLE)
            cursor.execute(CREATE_FILE_TAGS_TABLE)

            # Create indexes
            cursor.execute(CREATE_FILE_TAGS_PATH_IDX)
            cursor.execute(CREATE_FILE_TAGS_TAG_IDX)

            conn.commit()
            conn.close()

            logger.info(f"Initialized tag database schema at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize tag database schema: {e}")
            raise

    async def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.

        Returns:
            An SQLite connection object

        Raises:
            Exception: If connection fails
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            return conn
        except Exception as e:
            logger.error(f"Failed to connect to tag database: {e}")
            raise
