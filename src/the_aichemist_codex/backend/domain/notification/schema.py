"""
Database schema for notification system.

This module defines the SQLite schema for storing notifications,
subscribers, and notification delivery status.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SQL statements for creating database tables
CREATE_NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    message TEXT NOT NULL,
    level TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    sender_id TEXT
);
"""

CREATE_SUBSCRIBERS_TABLE = """
CREATE TABLE IF NOT EXISTS subscribers (
    id TEXT PRIMARY KEY,
    name TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);
"""

CREATE_SUBSCRIBER_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriber_channels (
    subscriber_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    PRIMARY KEY (subscriber_id, channel),
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
);
"""

CREATE_NOTIFICATION_DELIVERY_TABLE = """
CREATE TABLE IF NOT EXISTS notification_delivery (
    notification_id TEXT NOT NULL,
    subscriber_id TEXT NOT NULL,
    delivered BOOLEAN DEFAULT 0,
    read BOOLEAN DEFAULT 0,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    PRIMARY KEY (notification_id, subscriber_id),
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
);
"""

# Indexes for improving query performance
CREATE_NOTIFICATIONS_LEVEL_IDX = """
CREATE INDEX IF NOT EXISTS idx_notifications_level ON notifications(level);
"""

CREATE_NOTIFICATIONS_TIME_IDX = """
CREATE INDEX IF NOT EXISTS idx_notifications_time ON notifications(timestamp);
"""

CREATE_NOTIFICATION_DELIVERY_SUB_IDX = """
CREATE INDEX IF NOT EXISTS idx_delivery_subscriber ON notification_delivery(subscriber_id);
"""

CREATE_NOTIFICATION_DELIVERY_READ_IDX = """
CREATE INDEX IF NOT EXISTS idx_delivery_read ON notification_delivery(read);
"""


class NotificationSchema:
    """
    Manages the database schema for the notification system.

    This class is responsible for creating and initializing the database
    tables for storing notifications.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the NotificationSchema with a database path.

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
            cursor.execute(CREATE_NOTIFICATIONS_TABLE)
            cursor.execute(CREATE_SUBSCRIBERS_TABLE)
            cursor.execute(CREATE_SUBSCRIBER_CHANNELS_TABLE)
            cursor.execute(CREATE_NOTIFICATION_DELIVERY_TABLE)

            # Create indexes
            cursor.execute(CREATE_NOTIFICATIONS_LEVEL_IDX)
            cursor.execute(CREATE_NOTIFICATIONS_TIME_IDX)
            cursor.execute(CREATE_NOTIFICATION_DELIVERY_SUB_IDX)
            cursor.execute(CREATE_NOTIFICATION_DELIVERY_READ_IDX)

            conn.commit()
            conn.close()

            logger.info(f"Initialized notification database schema at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize notification database schema: {e}")
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
            logger.error(f"Failed to connect to notification database: {e}")
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
