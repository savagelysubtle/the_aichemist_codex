"""
Database schema for analytics system.

This module defines the SQLite schema for storing usage analytics,
events, errors, and performance metrics.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SQL statements for creating database tables
CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    session_id TEXT
);
"""

CREATE_ERRORS_TABLE = """
CREATE TABLE IF NOT EXISTS errors (
    id TEXT PRIMARY KEY,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    session_id TEXT
);
"""

CREATE_PERFORMANCE_TABLE = """
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY,
    metric_type TEXT NOT NULL,
    operation TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    session_id TEXT
);
"""

# Indexes for improving query performance
CREATE_EVENTS_TYPE_IDX = """
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
"""

CREATE_EVENTS_TIME_IDX = """
CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp);
"""

CREATE_ERRORS_TYPE_IDX = """
CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type);
"""

CREATE_ERRORS_TIME_IDX = """
CREATE INDEX IF NOT EXISTS idx_errors_time ON errors(timestamp);
"""

CREATE_PERFORMANCE_TYPE_IDX = """
CREATE INDEX IF NOT EXISTS idx_perf_type ON performance_metrics(metric_type);
"""

CREATE_PERFORMANCE_OP_IDX = """
CREATE INDEX IF NOT EXISTS idx_perf_operation ON performance_metrics(operation);
"""


class AnalyticsSchema:
    """
    Manages the database schema for the analytics system.

    This class is responsible for creating and initializing the database
    tables for storing analytics data.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the AnalyticsSchema with a database path.

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
            cursor.execute(CREATE_EVENTS_TABLE)
            cursor.execute(CREATE_ERRORS_TABLE)
            cursor.execute(CREATE_PERFORMANCE_TABLE)

            # Create indexes
            cursor.execute(CREATE_EVENTS_TYPE_IDX)
            cursor.execute(CREATE_EVENTS_TIME_IDX)
            cursor.execute(CREATE_ERRORS_TYPE_IDX)
            cursor.execute(CREATE_ERRORS_TIME_IDX)
            cursor.execute(CREATE_PERFORMANCE_TYPE_IDX)
            cursor.execute(CREATE_PERFORMANCE_OP_IDX)

            conn.commit()
            conn.close()

            logger.info(f"Initialized analytics database schema at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize analytics database schema: {e}")
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
            logger.error(f"Failed to connect to analytics database: {e}")
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
