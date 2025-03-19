"""
Analytics management functionality.

This module provides the AnalyticsManagerImpl class for tracking,
storing, and analyzing usage data within the application.
"""

import datetime
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from ....registry import Registry
from ...core.interfaces import AnalyticsManager as AnalyticsManagerInterface
from .schema import AnalyticsSchema

logger = logging.getLogger(__name__)


class AnalyticsManagerImpl(AnalyticsManagerInterface):
    """
    Implementation of the AnalyticsManager interface.

    This class provides methods for tracking and analyzing application
    usage, events, errors, and performance metrics.
    """

    def __init__(self):
        """Initialize the AnalyticsManagerImpl."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator

        # Get the path to the analytics database file
        self._db_path = self._paths.get_data_dir() / "analytics.db"
        self._schema = AnalyticsSchema(self._db_path)

        # Generate a session ID for this instance
        self._session_id = str(uuid.uuid4())

        # Track whether analytics is enabled (read from config later)
        self._enabled = True

        # Store a map of operation_id -> start_time for timing operations
        self._timing_operations = {}

    async def initialize(self) -> None:
        """
        Initialize the analytics manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        # Try to get analytics settings from config
        try:
            config = self._registry.config_provider
            self._enabled = config.get_config("analytics.enabled", True)
        except Exception as e:
            logger.warning(f"Could not read analytics config, using defaults: {e}")
            self._enabled = True

        if not self._enabled:
            logger.info("Analytics are disabled by configuration")
            return

        # Initialize the database schema
        await self._schema.initialize()
        logger.info(f"Initialized AnalyticsManager with session ID: {self._session_id}")

        # Track application start event
        try:
            await self.track_event(
                "app_start",
                {
                    "python_version": ".".join(map(str, os.sys.version_info[:3])),
                    "platform": os.sys.platform,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to track app_start event: {e}")

    async def close(self) -> None:
        """Close any resources used by the analytics manager."""
        if self._enabled:
            try:
                # Track application close event
                await self.track_event("app_close")
            except Exception as e:
                logger.warning(f"Failed to track app_close event: {e}")

        logger.debug("Closed AnalyticsManager")

    async def track_event(
        self, event_type: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Track an application event.

        Args:
            event_type: Type of event (e.g., "file_opened", "search_performed")
            metadata: Additional metadata about the event

        Returns:
            The ID of the tracked event

        Raises:
            Exception: If tracking fails
        """
        if not self._enabled:
            # Return a dummy ID when analytics are disabled
            return str(uuid.uuid4())

        try:
            event_id = str(uuid.uuid4())

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO events (id, event_type, timestamp, metadata, session_id)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """,
                    (
                        event_id,
                        event_type,
                        self._schema.serialize_metadata(metadata),
                        self._session_id,
                    ),
                )
                conn.commit()
                return event_id
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to track event {event_type}: {e}")
            raise

    async def track_error(
        self, error_type: str, message: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Track an application error.

        Args:
            error_type: Type of error
            message: Error message
            metadata: Additional metadata about the error

        Returns:
            The ID of the tracked error

        Raises:
            Exception: If tracking fails
        """
        if not self._enabled:
            # Return a dummy ID when analytics are disabled
            return str(uuid.uuid4())

        try:
            error_id = str(uuid.uuid4())

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO errors (id, error_type, message, timestamp, metadata, session_id)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """,
                    (
                        error_id,
                        error_type,
                        message,
                        self._schema.serialize_metadata(metadata),
                        self._session_id,
                    ),
                )
                conn.commit()
                return error_id
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to track error {error_type}: {e}")
            raise

    async def start_timer(self, operation: str, metric_type: str = "operation") -> str:
        """
        Start timing an operation.

        Args:
            operation: Name of the operation
            metric_type: Type of metric (e.g., "operation", "network", "database")

        Returns:
            Operation ID to be used with stop_timer
        """
        if not self._enabled:
            return str(uuid.uuid4())

        operation_id = str(uuid.uuid4())
        self._timing_operations[operation_id] = {
            "start_time": time.time(),
            "operation": operation,
            "metric_type": metric_type,
        }
        return operation_id

    async def stop_timer(
        self, operation_id: str, metadata: dict[str, Any] | None = None
    ) -> float:
        """
        Stop timing an operation and record the performance metric.

        Args:
            operation_id: Operation ID from start_timer
            metadata: Additional metadata about the operation

        Returns:
            Duration in milliseconds

        Raises:
            ValueError: If the operation ID is not found
        """
        if not self._enabled:
            return 0.0

        if operation_id not in self._timing_operations:
            raise ValueError(f"Operation ID not found: {operation_id}")

        op_data = self._timing_operations.pop(operation_id)
        duration_sec = time.time() - op_data["start_time"]
        duration_ms = duration_sec * 1000

        try:
            # Record performance metric
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO performance_metrics
                    (id, metric_type, operation, duration_ms, timestamp, metadata, session_id)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        op_data["metric_type"],
                        op_data["operation"],
                        duration_ms,
                        self._schema.serialize_metadata(metadata),
                        self._session_id,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            return duration_ms
        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")
            return duration_ms  # Still return the duration even if storage fails

    async def get_usage_statistics(
        self, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get usage statistics for a time period.

        Args:
            start_time: Start of the time period (None for all time)
            end_time: End of the time period (None for current time)

        Returns:
            Dictionary with usage statistics
        """
        if not self._enabled:
            return {"analytics_enabled": False}

        stats = {
            "analytics_enabled": True,
            "total_events": 0,
            "events_by_type": {},
            "total_errors": 0,
            "errors_by_type": {},
            "session_count": 0,
            "timespan": {"start": None, "end": None},
            "performance": {"average_durations": {}},
        }

        # Convert datetime objects to timestamps for SQLite comparison
        start_timestamp = start_time.timestamp() if start_time else None
        end_timestamp = end_time.timestamp() if end_time else None

        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()

                # Build query conditions for time filtering
                time_conditions = []
                params = []

                if start_timestamp:
                    time_conditions.append("timestamp >= ?")
                    params.append(start_timestamp)

                if end_timestamp:
                    time_conditions.append("timestamp <= ?")
                    params.append(end_timestamp)

                time_condition = (
                    f"WHERE {' AND '.join(time_conditions)}" if time_conditions else ""
                )

                # Get total event count
                cursor.execute(
                    f"SELECT COUNT(*) FROM events {time_condition}", tuple(params)
                )
                stats["total_events"] = cursor.fetchone()[0]

                # Get event counts by type
                cursor.execute(
                    f"SELECT event_type, COUNT(*) FROM events {time_condition} "
                    f"GROUP BY event_type ORDER BY COUNT(*) DESC",
                    tuple(params),
                )
                stats["events_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

                # Get total error count
                cursor.execute(
                    f"SELECT COUNT(*) FROM errors {time_condition}", tuple(params)
                )
                stats["total_errors"] = cursor.fetchone()[0]

                # Get error counts by type
                cursor.execute(
                    f"SELECT error_type, COUNT(*) FROM errors {time_condition} "
                    f"GROUP BY error_type ORDER BY COUNT(*) DESC",
                    tuple(params),
                )
                stats["errors_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

                # Get unique session count
                cursor.execute(
                    f"SELECT COUNT(DISTINCT session_id) FROM events {time_condition}",
                    tuple(params),
                )
                stats["session_count"] = cursor.fetchone()[0]

                # Get timespan
                if stats["total_events"] > 0:
                    cursor.execute(
                        f"SELECT MIN(timestamp), MAX(timestamp) FROM events {time_condition}",
                        tuple(params),
                    )
                    min_time, max_time = cursor.fetchone()
                    stats["timespan"]["start"] = datetime.fromtimestamp(
                        min_time
                    ).isoformat()
                    stats["timespan"]["end"] = datetime.fromtimestamp(
                        max_time
                    ).isoformat()

                # Get average durations for performance metrics
                cursor.execute(
                    f"SELECT operation, AVG(duration_ms) FROM performance_metrics {time_condition} "
                    f"GROUP BY operation ORDER BY AVG(duration_ms) DESC",
                    tuple(params),
                )
                stats["performance"]["average_durations"] = {
                    row[0]: row[1] for row in cursor.fetchall()
                }

                return stats
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {"error": str(e), "analytics_enabled": self._enabled}

    async def get_event_timeline(
        self, event_types: list[str] | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get a timeline of events.

        Args:
            event_types: Types of events to include (None for all)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        if not self._enabled:
            return []

        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()

                # Build query conditions for event type filtering
                conditions = []
                params = []

                if event_types:
                    placeholders = ", ".join("?" for _ in event_types)
                    conditions.append(f"event_type IN ({placeholders})")
                    params.extend(event_types)

                condition = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                # Get events ordered by timestamp
                cursor.execute(
                    f"""
                    SELECT id, event_type, timestamp, metadata, session_id
                    FROM events {condition}
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    tuple(params + [limit]),
                )

                # Process results
                timeline = []
                for row in cursor.fetchall():
                    event = dict(row)
                    event["metadata"] = self._schema.deserialize_metadata(
                        event["metadata"]
                    )
                    # Convert timestamp to ISO format
                    timestamp = float(event["timestamp"])
                    event["timestamp"] = datetime.fromtimestamp(timestamp).isoformat()
                    timeline.append(event)

                return timeline
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to get event timeline: {e}")
            return []

    async def get_frequent_errors(
        self, days: int = 7, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get most frequent errors in the given time period.

        Args:
            days: Number of days to look back
            limit: Maximum number of errors to return

        Returns:
            List of error dictionaries with count and frequency
        """
        if not self._enabled:
            return []

        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()

                # Calculate cutoff date
                cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

                # Get error counts by type and message
                cursor.execute(
                    """
                    SELECT error_type, message, COUNT(*) as count
                    FROM errors
                    WHERE timestamp >= ?
                    GROUP BY error_type, message
                    ORDER BY count DESC
                    LIMIT ?
                    """,
                    (cutoff_time, limit),
                )

                # Get total errors for calculating percentages
                cursor.execute(
                    "SELECT COUNT(*) FROM errors WHERE timestamp >= ?", (cutoff_time,)
                )
                total_errors = cursor.fetchone()[0] or 1  # Avoid division by zero

                # Process results
                frequent_errors = []
                for row in cursor.fetchall():
                    error_type, message, count = row
                    frequent_errors.append(
                        {
                            "error_type": error_type,
                            "message": message,
                            "count": count,
                            "percentage": round((count / total_errors) * 100, 2),
                        }
                    )

                return frequent_errors
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to get frequent errors: {e}")
            return []

    async def get_feature_usage(self) -> dict[str, Any]:
        """
        Get statistics about feature usage.

        Returns:
            Dictionary with feature usage statistics
        """
        if not self._enabled:
            return {"analytics_enabled": False}

        try:
            # Map event types to feature categories
            feature_mapping = {
                "file_opened": "file_operations",
                "file_saved": "file_operations",
                "file_deleted": "file_operations",
                "search_performed": "search",
                "search_advanced": "search",
                "tag_added": "tagging",
                "tag_removed": "tagging",
                "relationship_created": "relationships",
                "relationship_detected": "relationships",
                # Add more mappings as needed
            }

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()

                # Get all event counts by type
                cursor.execute(
                    "SELECT event_type, COUNT(*) FROM events GROUP BY event_type"
                )

                # Process results into feature categories
                event_counts = {row[0]: row[1] for row in cursor.fetchall()}

                # Aggregate into feature categories
                feature_usage = {"by_category": {}, "by_event": event_counts}

                for event_type, count in event_counts.items():
                    category = feature_mapping.get(event_type, "other")
                    if category not in feature_usage["by_category"]:
                        feature_usage["by_category"][category] = 0
                    feature_usage["by_category"][category] += count

                # Add total count
                feature_usage["total_events"] = sum(event_counts.values())

                return feature_usage
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to get feature usage: {e}")
            return {"error": str(e), "analytics_enabled": self._enabled}

    async def get_performance_metrics(
        self, metric_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get performance metrics for different operations.

        Args:
            metric_types: Types of metrics to include (None for all)

        Returns:
            Dictionary with performance metrics
        """
        if not self._enabled:
            return {"analytics_enabled": False}

        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()

                # Build query conditions for metric type filtering
                conditions = []
                params = []

                if metric_types:
                    placeholders = ", ".join("?" for _ in metric_types)
                    conditions.append(f"metric_type IN ({placeholders})")
                    params.extend(metric_types)

                condition = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                # Get various performance statistics
                performance = {"operations": {}, "by_metric_type": {}}

                # Get operation statistics
                cursor.execute(
                    f"""
                    SELECT operation,
                           COUNT(*) as count,
                           AVG(duration_ms) as avg_duration,
                           MIN(duration_ms) as min_duration,
                           MAX(duration_ms) as max_duration
                    FROM performance_metrics {condition}
                    GROUP BY operation
                    ORDER BY avg_duration DESC
                    """,
                    tuple(params),
                )

                for row in cursor.fetchall():
                    operation, count, avg, min_val, max_val = row
                    performance["operations"][operation] = {
                        "count": count,
                        "avg_duration_ms": avg,
                        "min_duration_ms": min_val,
                        "max_duration_ms": max_val,
                    }

                # Get metrics by type
                cursor.execute(
                    f"""
                    SELECT metric_type,
                           COUNT(*) as count,
                           AVG(duration_ms) as avg_duration
                    FROM performance_metrics {condition}
                    GROUP BY metric_type
                    """,
                    tuple(params),
                )

                for row in cursor.fetchall():
                    metric_type, count, avg = row
                    performance["by_metric_type"][metric_type] = {
                        "count": count,
                        "avg_duration_ms": avg,
                    }

                return performance
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e), "analytics_enabled": self._enabled}

    async def clear_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clear analytics data older than the specified number of days.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of records deleted
        """
        if not self._enabled:
            return 0

        try:
            # Calculate cutoff date
            cutoff_time = (datetime.now() - timedelta(days=days_to_keep)).timestamp()

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                total_deleted = 0

                # Delete old events
                cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time,))
                total_deleted += cursor.rowcount

                # Delete old errors
                cursor.execute("DELETE FROM errors WHERE timestamp < ?", (cutoff_time,))
                total_deleted += cursor.rowcount

                # Delete old performance metrics
                cursor.execute(
                    "DELETE FROM performance_metrics WHERE timestamp < ?",
                    (cutoff_time,),
                )
                total_deleted += cursor.rowcount

                conn.commit()
                logger.info(f"Cleared {total_deleted} old analytics records")
                return total_deleted
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to clear old analytics data: {e}")
            return 0


# Export symbols
__all__ = ["AnalyticsManagerImpl"]
