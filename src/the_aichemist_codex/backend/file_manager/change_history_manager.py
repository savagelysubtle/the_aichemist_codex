"""
Change history storage and management for The Aichemist Codex.

This module provides functionality to store, retrieve, and manage
file change history in a SQLite database.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from the_aichemist_codex.backend.config.config_loader import config
from the_aichemist_codex.backend.config.settings import DATA_DIR
from the_aichemist_codex.backend.file_manager.change_detector import (
    ChangeInfo,
    ChangeSeverity,
    ChangeType,
)

logger = logging.getLogger(__name__)

# Default location for the change history database
CHANGE_HISTORY_DB = DATA_DIR / "change_history.db"


class ChangeHistoryManager:
    """
    Manages storage and retrieval of file change history.

    Features:
    - Maintains a SQLite database of file changes
    - Stores metadata about each change (timestamp, type, severity, etc.)
    - Provides querying by file, time range, change type, etc.
    - Implements cleanup policies for old records
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChangeHistoryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: Path = CHANGE_HISTORY_DB):
        """
        Initialize the change history manager.

        Args:
            db_path: Path to the SQLite database file
        """
        # Only initialize once (singleton pattern)
        if ChangeHistoryManager._initialized:
            return

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = config.get("change_history_retention_days", 30)
        self._init_db()

        ChangeHistoryManager._initialized = True

    def _init_db(self) -> None:
        """Initialize the SQLite database with necessary tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create changes table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    details TEXT,
                    old_path TEXT
                )
                """)

                # Create indexes for efficient querying
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_path ON changes(file_path)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON changes(timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_change_type ON changes(change_type)"
                )

                conn.commit()
                logger.info(f"Change history database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing change history database: {e}")

    async def record_change(self, change_info: ChangeInfo) -> bool:
        """
        Record a file change in the database.

        Args:
            change_info: Information about the detected change

        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            # Serialize details dictionary to JSON
            details_json = json.dumps(change_info.details)
            old_path = str(change_info.old_path) if change_info.old_path else None

            # Run the database operation in a thread to avoid blocking
            return await asyncio.to_thread(
                self._insert_change,
                str(change_info.file_path),
                change_info.change_type.name,
                change_info.severity.name,
                change_info.timestamp,
                details_json,
                old_path,
            )
        except Exception as e:
            logger.error(f"Error recording change: {e}")
            return False

    def _insert_change(
        self,
        file_path: str,
        change_type: str,
        severity: str,
        timestamp: float,
        details_json: str,
        old_path: str | None,
    ) -> bool:
        """
        Insert a change record into the database (synchronous).

        Args:
            file_path: Path to the changed file
            change_type: Type of change (CREATE, MODIFY, etc.)
            severity: Severity level (MINOR, MAJOR, etc.)
            timestamp: Unix timestamp of the change
            details_json: JSON string of change details
            old_path: Previous path for moved/renamed files

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO changes
                    (file_path, change_type, severity, timestamp, details, old_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_path,
                        change_type,
                        severity,
                        timestamp,
                        details_json,
                        old_path,
                    ),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error recording change: {e}")
            return False

    async def get_changes_by_file(
        self, file_path: Path, limit: int = 100
    ) -> list[ChangeInfo]:
        """
        Retrieve change history for a specific file.

        Args:
            file_path: Path to the file
            limit: Maximum number of records to return

        Returns:
            List of ChangeInfo objects, newest first
        """
        return await self._query_changes(
            "WHERE file_path = ? OR old_path = ? ORDER BY timestamp DESC LIMIT ?",
            (str(file_path), str(file_path), limit),
        )

    async def get_changes_by_time_range(
        self, start_time: float, end_time: float | None = None, limit: int = 100
    ) -> list[ChangeInfo]:
        """
        Retrieve changes that occurred within a specific time range.

        Args:
            start_time: Start timestamp (Unix time)
            end_time: End timestamp (defaults to now)
            limit: Maximum number of records to return

        Returns:
            List of ChangeInfo objects
        """
        end_time = end_time or time.time()
        return await self._query_changes(
            "WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT ?",
            (start_time, end_time, limit),
        )

    async def get_changes_by_type(
        self, change_type: ChangeType, limit: int = 100
    ) -> list[ChangeInfo]:
        """
        Retrieve changes of a specific type.

        Args:
            change_type: Type of change to filter by
            limit: Maximum number of records to return

        Returns:
            List of ChangeInfo objects
        """
        return await self._query_changes(
            "WHERE change_type = ? ORDER BY timestamp DESC LIMIT ?",
            (change_type.name, limit),
        )

    async def get_changes_by_severity(
        self, min_severity: ChangeSeverity, limit: int = 100
    ) -> list[ChangeInfo]:
        """
        Retrieve changes with at least the specified severity.

        Args:
            min_severity: Minimum severity level
            limit: Maximum number of records to return

        Returns:
            List of ChangeInfo objects
        """
        # Convert severity enum to a list of severity names to include
        severity_levels = [
            level.name for level in ChangeSeverity if level.value >= min_severity.value
        ]

        placeholders = ",".join(["?"] * len(severity_levels))
        query = f"WHERE severity IN ({placeholders}) ORDER BY timestamp DESC LIMIT ?"
        params = (*severity_levels, limit)

        return await self._query_changes(query, params)

    async def _query_changes(
        self, where_clause: str, params: tuple
    ) -> list[ChangeInfo]:
        """
        Execute a database query and return results as ChangeInfo objects.

        Args:
            where_clause: SQL WHERE clause
            params: Query parameters

        Returns:
            List of ChangeInfo objects
        """
        try:
            # Run in a thread to avoid blocking
            rows = await asyncio.to_thread(self._execute_query, where_clause, params)

            # Convert rows to ChangeInfo objects
            changes = []
            for row in rows:
                (
                    change_id,
                    file_path,
                    change_type,
                    severity,
                    timestamp,
                    details_json,
                    old_path,
                ) = row

                try:
                    details = json.loads(details_json) if details_json else {}
                except json.JSONDecodeError:
                    details = {}

                changes.append(
                    ChangeInfo(
                        file_path=Path(file_path),
                        change_type=ChangeType[change_type],
                        severity=ChangeSeverity[severity],
                        timestamp=timestamp,
                        details=details,
                        old_path=Path(old_path) if old_path else None,
                    )
                )

            return changes
        except Exception as e:
            logger.error(f"Error querying changes: {e}")
            return []

    def _execute_query(self, where_clause: str, params: tuple) -> list[tuple]:
        """
        Execute a database query synchronously.

        Args:
            where_clause: SQL WHERE clause
            params: Query parameters

        Returns:
            List of result rows
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT id, file_path, change_type, severity, timestamp, details, old_path "
                    f"FROM changes {where_clause}",
                    params,
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error executing query: {e}")
            return []

    async def cleanup_old_records(self, days: float | None = None) -> int:
        """
        Remove change records older than the specified number of days.

        Args:
            days: Number of days to keep (defaults to configured retention period)

        Returns:
            Number of records removed
        """
        retention_days = days if days is not None else self.retention_days
        cutoff_time = time.time() - (retention_days * 86400)  # Convert days to seconds

        try:
            return await asyncio.to_thread(self._delete_old_records, cutoff_time)
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0

    def _delete_old_records(self, cutoff_time: float) -> int:
        """
        Delete records older than the cutoff time (synchronous).

        Args:
            cutoff_time: Timestamp threshold for deletion

        Returns:
            Number of records deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM changes WHERE timestamp < ?", (cutoff_time,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Removed {deleted_count} old change records")
                return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Database error deleting old records: {e}")
            return 0

    async def get_statistics(self) -> dict:
        """
        Get statistics about the change history.

        Returns:
            Dictionary with statistics like total changes, changes by type, etc.
        """
        try:
            return await asyncio.to_thread(self._gather_statistics)
        except Exception as e:
            logger.error(f"Error gathering statistics: {e}")
            return {}

    def _gather_statistics(self) -> dict:
        """
        Gather statistics from the database (synchronous).

        Returns:
            Dictionary with various statistics
        """
        stats = {
            "total_changes": 0,
            "changes_by_type": {},
            "changes_by_severity": {},
            "recent_changes": 0,  # Last 24 hours
            "oldest_record": None,
            "newest_record": None,
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute("SELECT COUNT(*) FROM changes")
                stats["total_changes"] = cursor.fetchone()[0]

                # Counts by type
                cursor.execute(
                    "SELECT change_type, COUNT(*) FROM changes GROUP BY change_type"
                )
                stats["changes_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

                # Counts by severity
                cursor.execute(
                    "SELECT severity, COUNT(*) FROM changes GROUP BY severity"
                )
                stats["changes_by_severity"] = {
                    row[0]: row[1] for row in cursor.fetchall()
                }

                # Recent changes (last 24 hours)
                recent_cutoff = time.time() - 86400
                cursor.execute(
                    "SELECT COUNT(*) FROM changes WHERE timestamp > ?", (recent_cutoff,)
                )
                stats["recent_changes"] = cursor.fetchone()[0]

                # Oldest and newest timestamps
                if stats["total_changes"] > 0:
                    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM changes")
                    oldest, newest = cursor.fetchone()
                    stats["oldest_record"] = datetime.fromtimestamp(oldest).isoformat()
                    stats["newest_record"] = datetime.fromtimestamp(newest).isoformat()

                return stats
        except sqlite3.Error as e:
            logger.error(f"Database error gathering statistics: {e}")
            return stats


# Create a singleton instance
change_history_manager = ChangeHistoryManager()
