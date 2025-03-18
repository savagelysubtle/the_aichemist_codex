"""
Implementation of the NotificationManager interface.

This module provides the concrete implementation of the notification
management system, responsible for sending and tracking notifications.
"""

import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from the_aichemist_codex.backend.core.exceptions import NotificationError
from the_aichemist_codex.backend.core.interfaces import (
    FileValidator,
    NotificationManager,
    ProjectPaths,
)
from the_aichemist_codex.backend.domain.notification.models import (
    Notification,
    NotificationLevel,
    Subscriber,
    SubscriptionChannel,
)
from the_aichemist_codex.backend.domain.notification.schema import NotificationSchema

logger = logging.getLogger(__name__)


class NotificationManagerImpl(NotificationManager):
    """
    Implementation of the NotificationManager interface.

    This class manages the notification system, including:
    - Subscriber registration and management
    - Sending notifications to subscribers
    - Tracking notification status (delivered/read)
    - Notification history management
    """

    def __init__(
        self,
        project_paths: ProjectPaths,
        file_validator: FileValidator,
    ):
        """
        Initialize the NotificationManager implementation.

        Args:
            project_paths: Service for accessing project paths
            file_validator: Service for validating file paths
        """
        self._project_paths = project_paths
        self._file_validator = file_validator
        self._initialized = False
        self._schema: NotificationSchema | None = None
        self._listeners: dict[NotificationLevel, set[callable]] = {
            level: set() for level in NotificationLevel
        }

    async def initialize(self) -> None:
        """
        Initialize the notification manager.

        Creates the necessary database schema and prepares the manager for use.

        Raises:
            NotificationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Get the data directory from project paths
            data_dir = Path(self._project_paths.get_data_dir())
            db_path = data_dir / "notifications.db"

            # Validate the path
            if not self._file_validator.is_path_safe(db_path):
                raise NotificationError(f"Invalid database path: {db_path}")

            # Create the schema manager
            self._schema = NotificationSchema(db_path)
            await self._schema.initialize()

            self._initialized = True
            logger.info("NotificationManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NotificationManager: {e}")
            raise NotificationError(
                f"Failed to initialize notification manager: {e}"
            ) from e

    def _ensure_initialized(self) -> None:
        """
        Ensure the manager is initialized before operations.

        Raises:
            NotificationError: If the manager is not initialized
        """
        if not self._initialized or self._schema is None:
            raise NotificationError("NotificationManager is not initialized")

    async def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.

        Returns:
            An SQLite connection object

        Raises:
            NotificationError: If connection cannot be established
        """
        self._ensure_initialized()
        try:
            assert self._schema is not None
            return await self._schema.get_connection()
        except Exception as e:
            raise NotificationError(
                f"Failed to connect to notification database: {e}"
            ) from e

    async def add_subscriber(
        self, name: str | None = None, channels: list[SubscriptionChannel] | None = None
    ) -> Subscriber:
        """
        Register a new notification subscriber.

        Args:
            name: Optional name for the subscriber
            channels: Optional list of notification channels

        Returns:
            A new Subscriber instance

        Raises:
            NotificationError: If registration fails
        """
        self._ensure_initialized()

        # Create subscriber with default channels if none specified
        subscriber = Subscriber(
            id=str(uuid.uuid4()),
            name=name,
            channels=channels or [SubscriptionChannel.IN_APP],
            created_at=datetime.now(),
        )

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Insert subscriber
            cursor.execute(
                "INSERT INTO subscribers (id, name, enabled, created_at) VALUES (?, ?, ?, ?)",
                (
                    subscriber.id,
                    subscriber.name,
                    subscriber.enabled,
                    subscriber.created_at.isoformat(),
                ),
            )

            # Insert channels
            for channel in subscriber.channels:
                cursor.execute(
                    "INSERT INTO subscriber_channels (subscriber_id, channel) VALUES (?, ?)",
                    (subscriber.id, channel.value),
                )

            conn.commit()
            conn.close()

            logger.debug(f"Added subscriber: {subscriber.id}")
            return subscriber

        except Exception as e:
            logger.error(f"Failed to add subscriber: {e}")
            raise NotificationError(f"Failed to add subscriber: {e}") from e

    async def remove_subscriber(self, subscriber_id: str) -> None:
        """
        Remove a notification subscriber.

        Args:
            subscriber_id: ID of the subscriber to remove

        Raises:
            NotificationError: If removal fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if subscriber exists
            cursor.execute("SELECT id FROM subscribers WHERE id = ?", (subscriber_id,))
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Delete subscriber (cascade will handle channels and deliveries)
            cursor.execute("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))

            conn.commit()
            conn.close()

            logger.debug(f"Removed subscriber: {subscriber_id}")

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to remove subscriber: {e}")
            raise NotificationError(f"Failed to remove subscriber: {e}") from e

    async def get_subscriber(self, subscriber_id: str) -> Subscriber:
        """
        Get a subscriber by ID.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            The subscriber details

        Raises:
            NotificationError: If subscriber not found or retrieval fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Get subscriber
            cursor.execute(
                "SELECT id, name, enabled, created_at, last_active FROM subscribers WHERE id = ?",
                (subscriber_id,),
            )

            row = cursor.fetchone()
            if row is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Get channels
            cursor.execute(
                "SELECT channel FROM subscriber_channels WHERE subscriber_id = ?",
                (subscriber_id,),
            )

            channel_rows = cursor.fetchall()
            channels = [SubscriptionChannel(row["channel"]) for row in channel_rows]

            conn.close()

            # Create subscriber object
            return Subscriber(
                id=row["id"],
                name=row["name"],
                channels=channels,
                enabled=bool(row["enabled"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                last_active=datetime.fromisoformat(row["last_active"])
                if row["last_active"]
                else None,
            )

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get subscriber: {e}")
            raise NotificationError(f"Failed to get subscriber: {e}") from e

    async def list_subscribers(self) -> list[Subscriber]:
        """
        List all notification subscribers.

        Returns:
            List of all subscribers

        Raises:
            NotificationError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Get all subscribers
            cursor.execute(
                "SELECT id, name, enabled, created_at, last_active FROM subscribers"
            )

            subscribers = []
            for row in cursor.fetchall():
                subscriber_id = row["id"]

                # Get channels for this subscriber
                channel_cursor = conn.cursor()
                channel_cursor.execute(
                    "SELECT channel FROM subscriber_channels WHERE subscriber_id = ?",
                    (subscriber_id,),
                )

                channel_rows = channel_cursor.fetchall()
                channels = [
                    SubscriptionChannel(channel_row["channel"])
                    for channel_row in channel_rows
                ]

                # Create subscriber object
                subscriber = Subscriber(
                    id=subscriber_id,
                    name=row["name"],
                    channels=channels,
                    enabled=bool(row["enabled"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_active=datetime.fromisoformat(row["last_active"])
                    if row["last_active"]
                    else None,
                )

                subscribers.append(subscriber)

            conn.close()
            return subscribers

        except Exception as e:
            logger.error(f"Failed to list subscribers: {e}")
            raise NotificationError(f"Failed to list subscribers: {e}") from e

    async def update_subscriber(
        self,
        subscriber_id: str,
        name: str | None = None,
        channels: list[SubscriptionChannel] | None = None,
        enabled: bool | None = None,
    ) -> Subscriber:
        """
        Update subscriber details.

        Args:
            subscriber_id: ID of the subscriber to update
            name: New name (or None to not change)
            channels: New list of channels (or None to not change)
            enabled: New enabled status (or None to not change)

        Returns:
            Updated subscriber

        Raises:
            NotificationError: If update fails
        """
        self._ensure_initialized()

        try:
            # First get the current subscriber data
            subscriber = await self.get_subscriber(subscriber_id)

            # Update fields if provided
            if name is not None:
                subscriber.name = name
            if enabled is not None:
                subscriber.enabled = enabled

            conn = await self._get_connection()
            cursor = conn.cursor()

            # Update subscriber record
            cursor.execute(
                "UPDATE subscribers SET name = ?, enabled = ?, last_active = ? WHERE id = ?",
                (
                    subscriber.name,
                    subscriber.enabled,
                    datetime.now().isoformat(),
                    subscriber_id,
                ),
            )

            # Update channels if provided
            if channels is not None:
                # Delete existing channels
                cursor.execute(
                    "DELETE FROM subscriber_channels WHERE subscriber_id = ?",
                    (subscriber_id,),
                )

                # Insert new channels
                for channel in channels:
                    cursor.execute(
                        "INSERT INTO subscriber_channels (subscriber_id, channel) VALUES (?, ?)",
                        (subscriber_id, channel.value),
                    )

                subscriber.channels = channels

            conn.commit()
            conn.close()

            logger.debug(f"Updated subscriber: {subscriber_id}")
            return subscriber

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update subscriber: {e}")
            raise NotificationError(f"Failed to update subscriber: {e}") from e

    async def send_notification(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        metadata: dict[str, Any] | None = None,
        sender_id: str | None = None,
        subscriber_ids: list[str] | None = None,
    ) -> Notification:
        """
        Send a notification to subscribers.

        Args:
            message: Notification message
            level: Notification severity level
            metadata: Additional data to include
            sender_id: ID of the sender (component/module)
            subscriber_ids: Optional list of specific subscribers to notify
                            (if None, will send to all subscribers)

        Returns:
            The created notification

        Raises:
            NotificationError: If sending fails
        """
        self._ensure_initialized()

        notification = Notification(
            message=message, level=level, metadata=metadata or {}, sender_id=sender_id
        )

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Create the notification
            cursor.execute(
                "INSERT INTO notifications (id, message, level, timestamp, metadata, sender_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    notification.id,
                    notification.message,
                    notification.level.value,
                    notification.timestamp.isoformat(),
                    self._schema.serialize_metadata(notification.metadata)
                    if self._schema
                    else "{}",
                    notification.sender_id,
                ),
            )

            # Determine which subscribers to send to
            if subscriber_ids is not None:
                # Send to specific subscribers
                for subscriber_id in subscriber_ids:
                    cursor.execute(
                        "SELECT id FROM subscribers WHERE id = ? AND enabled = 1",
                        (subscriber_id,),
                    )
                    if cursor.fetchone() is not None:
                        cursor.execute(
                            "INSERT INTO notification_delivery (notification_id, subscriber_id) VALUES (?, ?)",
                            (notification.id, subscriber_id),
                        )
            else:
                # Send to all enabled subscribers
                cursor.execute("SELECT id FROM subscribers WHERE enabled = 1")
                for row in cursor.fetchall():
                    cursor.execute(
                        "INSERT INTO notification_delivery (notification_id, subscriber_id) VALUES (?, ?)",
                        (notification.id, row["id"]),
                    )

            conn.commit()
            conn.close()

            logger.debug(f"Sent notification: {notification.id}")

            # Trigger any registered listeners for this notification level
            for listener in self._listeners.get(level, set()):
                try:
                    asyncio.create_task(listener(notification))
                except Exception as e:
                    logger.error(f"Error in notification listener: {e}")

            return notification

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise NotificationError(f"Failed to send notification: {e}") from e

    async def get_notification(self, notification_id: str) -> Notification:
        """
        Retrieve a notification by ID.

        Args:
            notification_id: ID of the notification

        Returns:
            The notification

        Raises:
            NotificationError: If notification not found or retrieval fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, message, level, timestamp, metadata, sender_id FROM notifications WHERE id = ?",
                (notification_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row is None:
                raise NotificationError(f"Notification not found: {notification_id}")

            # Create notification object
            return Notification(
                id=row["id"],
                message=row["message"],
                level=NotificationLevel(row["level"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                metadata=self._schema.deserialize_metadata(row["metadata"])
                if self._schema
                else {},
                sender_id=row["sender_id"],
            )

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get notification: {e}")
            raise NotificationError(f"Failed to get notification: {e}") from e

    async def get_notifications(
        self,
        subscriber_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """
        Get notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            List of notifications

        Raises:
            NotificationError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if subscriber exists
            cursor.execute("SELECT id FROM subscribers WHERE id = ?", (subscriber_id,))
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Get notifications for this subscriber
            query = """
            SELECT n.id, n.message, n.level, n.timestamp, n.metadata, n.sender_id,
                   nd.delivered, nd.read, nd.delivered_at, nd.read_at
            FROM notifications n
            JOIN notification_delivery nd ON n.id = nd.notification_id
            WHERE nd.subscriber_id = ?
            """

            params = [subscriber_id]

            if unread_only:
                query += " AND nd.read = 0"

            query += " ORDER BY n.timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            notifications = []
            for row in cursor.fetchall():
                notification = Notification(
                    id=row["id"],
                    message=row["message"],
                    level=NotificationLevel(row["level"]),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=self._schema.deserialize_metadata(row["metadata"])
                    if self._schema
                    else {},
                    sender_id=row["sender_id"],
                )
                notifications.append(notification)

            conn.close()
            return notifications

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            raise NotificationError(f"Failed to get notifications: {e}") from e

    async def mark_notification_read(
        self, notification_id: str, subscriber_id: str
    ) -> None:
        """
        Mark a notification as read for a specific subscriber.

        Args:
            notification_id: ID of the notification
            subscriber_id: ID of the subscriber

        Raises:
            NotificationError: If update fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if the notification delivery exists
            cursor.execute(
                "SELECT notification_id FROM notification_delivery WHERE notification_id = ? AND subscriber_id = ?",
                (notification_id, subscriber_id),
            )

            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(
                    f"Notification delivery not found for notification: {notification_id} and subscriber: {subscriber_id}"
                )

            # Mark as read
            cursor.execute(
                "UPDATE notification_delivery SET read = 1, read_at = ? WHERE notification_id = ? AND subscriber_id = ?",
                (datetime.now().isoformat(), notification_id, subscriber_id),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Marked notification {notification_id} as read for subscriber {subscriber_id}"
            )

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            raise NotificationError(f"Failed to mark notification as read: {e}") from e

    async def mark_all_read(self, subscriber_id: str) -> int:
        """
        Mark all notifications as read for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of notifications marked as read

        Raises:
            NotificationError: If update fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if subscriber exists
            cursor.execute("SELECT id FROM subscribers WHERE id = ?", (subscriber_id,))
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Count unread notifications
            cursor.execute(
                "SELECT COUNT(*) as count FROM notification_delivery WHERE subscriber_id = ? AND read = 0",
                (subscriber_id,),
            )
            row = cursor.fetchone()
            count = row["count"] if row else 0

            # Mark all as read
            cursor.execute(
                "UPDATE notification_delivery SET read = 1, read_at = ? WHERE subscriber_id = ? AND read = 0",
                (datetime.now().isoformat(), subscriber_id),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Marked {count} notifications as read for subscriber {subscriber_id}"
            )
            return count

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            raise NotificationError(
                f"Failed to mark all notifications as read: {e}"
            ) from e

    async def delete_notification(self, notification_id: str) -> None:
        """
        Delete a notification from the system.

        Args:
            notification_id: ID of the notification to delete

        Raises:
            NotificationError: If deletion fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if notification exists
            cursor.execute(
                "SELECT id FROM notifications WHERE id = ?", (notification_id,)
            )
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Notification not found: {notification_id}")

            # Delete notification (cascade will handle delivery records)
            cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))

            conn.commit()
            conn.close()

            logger.debug(f"Deleted notification: {notification_id}")

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            raise NotificationError(f"Failed to delete notification: {e}") from e

    async def delete_all_for_subscriber(self, subscriber_id: str) -> int:
        """
        Delete all notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of notifications deleted

        Raises:
            NotificationError: If deletion fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if subscriber exists
            cursor.execute("SELECT id FROM subscribers WHERE id = ?", (subscriber_id,))
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Count notifications
            cursor.execute(
                "SELECT COUNT(*) as count FROM notification_delivery WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            row = cursor.fetchone()
            count = row["count"] if row else 0

            # Delete notification delivery records
            cursor.execute(
                "DELETE FROM notification_delivery WHERE subscriber_id = ?",
                (subscriber_id,),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Deleted {count} notifications for subscriber {subscriber_id}"
            )
            return count

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete notifications for subscriber: {e}")
            raise NotificationError(
                f"Failed to delete notifications for subscriber: {e}"
            ) from e

    def add_listener(self, level: NotificationLevel, callback: callable) -> None:
        """
        Register a listener for notifications of a specific level.

        Args:
            level: Notification level to listen for
            callback: Async callback function to call with the notification
        """
        self._listeners.setdefault(level, set()).add(callback)
        logger.debug(f"Added notification listener for level: {level.value}")

    def remove_listener(self, level: NotificationLevel, callback: callable) -> None:
        """
        Remove a previously registered notification listener.

        Args:
            level: Notification level the listener was registered for
            callback: The callback function to remove
        """
        if level in self._listeners and callback in self._listeners[level]:
            self._listeners[level].remove(callback)
            logger.debug(f"Removed notification listener for level: {level.value}")

    async def get_unread_count(self, subscriber_id: str) -> int:
        """
        Get the count of unread notifications for a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            Number of unread notifications

        Raises:
            NotificationError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # Check if subscriber exists
            cursor.execute("SELECT id FROM subscribers WHERE id = ?", (subscriber_id,))
            if cursor.fetchone() is None:
                conn.close()
                raise NotificationError(f"Subscriber not found: {subscriber_id}")

            # Count unread notifications
            cursor.execute(
                "SELECT COUNT(*) as count FROM notification_delivery WHERE subscriber_id = ? AND read = 0",
                (subscriber_id,),
            )
            row = cursor.fetchone()
            count = row["count"] if row else 0

            conn.close()
            return count

        except NotificationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get unread notification count: {e}")
            raise NotificationError(
                f"Failed to get unread notification count: {e}"
            ) from e
