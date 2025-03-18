"""
Database schema for relationship management system.

This module defines the SQLite schema for storing relationships between files,
including relationship types, strengths, and metadata.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SQL statements for creating database tables
CREATE_RELATIONSHIPS_TABLE = """
CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    strength REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE (source_path, target_path, rel_type)
);
"""

# Indexes for improving query performance
CREATE_RELATIONSHIPS_SOURCE_IDX = """
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_path);
"""

CREATE_RELATIONSHIPS_TARGET_IDX = """
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_path);
"""

CREATE_RELATIONSHIPS_TYPE_IDX = """
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(rel_type);
"""


class RelationshipSchema:
    """
    Manages the database schema for the relationship system.

    This class is responsible for creating and initializing the database
    tables for the relationship system.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the RelationshipSchema with a database path.

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
            cursor.execute(CREATE_RELATIONSHIPS_TABLE)

            # Create indexes
            cursor.execute(CREATE_RELATIONSHIPS_SOURCE_IDX)
            cursor.execute(CREATE_RELATIONSHIPS_TARGET_IDX)
            cursor.execute(CREATE_RELATIONSHIPS_TYPE_IDX)

            conn.commit()
            conn.close()

            logger.info(f"Initialized relationship database schema at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize relationship database schema: {e}")
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
            logger.error(f"Failed to connect to relationship database: {e}")
            raise

    @staticmethod
    def serialize_metadata(metadata: dict[str, Any]) -> str:
        """
        Serialize metadata to JSON string for storage.

        Args:
            metadata: Metadata dictionary

        Returns:
            JSON string representation of metadata
        """
        if metadata is None:
            return "{}"
        return json.dumps(metadata)

    @staticmethod
    def deserialize_metadata(json_str: str | None) -> dict[str, Any]:
        """
        Deserialize metadata from JSON string.

        Args:
            json_str: JSON string representation of metadata

        Returns:
            Metadata dictionary
        """
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to deserialize metadata: {json_str}")
            return {}
