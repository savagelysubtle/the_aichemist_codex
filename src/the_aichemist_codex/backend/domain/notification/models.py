"""
Notification data models.

This module defines data models for the notification system, including notifications,
notification levels, and delivery status tracking.
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union


class NotificationLevel(enum.Enum):
    """Enumeration of notification severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @staticmethod
    def from_string(level_str: str) -> "NotificationLevel":
        """
        Convert a string to a NotificationLevel.

        Args:
            level_str: String representation of the level

        Returns:
            NotificationLevel enum value

        Raises:
            ValueError: If the string is not a valid level
        """
        level_str = level_str.lower()
        for level in NotificationLevel:
            if level.value == level_str:
                return level
        raise ValueError(f"Invalid notification level: {level_str}")


class NotificationStatus(enum.Enum):
    """Enumeration of notification delivery statuses."""

    PENDING = "pending"  # Not yet processed
    DELIVERED = "delivered"  # Successfully delivered
    READ = "read"  # Marked as read by recipient
    FAILED = "failed"  # Delivery failed
    CANCELED = "canceled"  # Delivery canceled


@dataclass
class NotificationDelivery:
    """Represents the delivery status of a notification to a subscriber."""

    subscriber_id: str
    status: NotificationStatus = NotificationStatus.PENDING
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def mark_delivered(self) -> None:
        """Mark the notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()

    def mark_read(self) -> None:
        """Mark the notification as read."""
        if self.status != NotificationStatus.DELIVERED:
            self.mark_delivered()
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark the notification as failed.

        Args:
            error_message: Error message describing the failure
        """
        self.status = NotificationStatus.FAILED
        self.error_message = error_message


@dataclass
class Notification:
    """Represents a notification in the system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = ""
    level: NotificationLevel = NotificationLevel.INFO
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sender_id: Optional[str] = None
    deliveries: Dict[str, NotificationDelivery] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the notification to a dictionary.

        Returns:
            Dictionary representation of the notification
        """
        return {
            "id": self.id,
            "message": self.message,
            "level": self.level.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "sender_id": self.sender_id,
            "deliveries": {
                subscriber_id: {
                    "status": delivery.status.value,
                    "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
                    "read_at": delivery.read_at.isoformat() if delivery.read_at else None,
                    "error_message": delivery.error_message
                }
                for subscriber_id, delivery in self.deliveries.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """
        Create a notification from a dictionary.

        Args:
            data: Dictionary representation of a notification

        Returns:
            Notification object
        """
        notification = cls(
            id=data.get("id", str(uuid.uuid4())),
            message=data.get("message", ""),
            level=NotificationLevel.from_string(data.get("level", "info")),
            sender_id=data.get("sender_id")
        )

        # Set created_at if present
        if "created_at" in data:
            notification.created_at = datetime.fromisoformat(data["created_at"])

        # Set metadata if present
        if "metadata" in data:
            notification.metadata = data["metadata"]

        # Set deliveries if present
        if "deliveries" in data:
            for subscriber_id, delivery_data in data["deliveries"].items():
                delivery = NotificationDelivery(subscriber_id=subscriber_id)

                # Set status
                if "status" in delivery_data:
                    delivery.status = NotificationStatus(delivery_data["status"])

                # Set delivered_at
                if delivery_data.get("delivered_at"):
                    delivery.delivered_at = datetime.fromisoformat(delivery_data["delivered_at"])

                # Set read_at
                if delivery_data.get("read_at"):
                    delivery.read_at = datetime.fromisoformat(delivery_data["read_at"])

                # Set error_message
                delivery.error_message = delivery_data.get("error_message")

                # Add to deliveries
                notification.deliveries[subscriber_id] = delivery

        return notification


@dataclass
class Subscriber:
    """Represents a notification subscriber."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    channels: List[str] = field(default_factory=list)
    enabled: bool = True
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the subscriber to a dictionary.

        Returns:
            Dictionary representation of the subscriber
        """
        return {
            "id": self.id,
            "name": self.name,
            "channels": self.channels,
            "enabled": self.enabled,
            "notification_preferences": self.notification_preferences,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subscriber":
        """
        Create a subscriber from a dictionary.

        Args:
            data: Dictionary representation of a subscriber

        Returns:
            Subscriber object
        """
        subscriber = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            enabled=data.get("enabled", True)
        )

        # Set channels if present
        if "channels" in data:
            subscriber.channels = data["channels"]

        # Set preferences if present
        if "notification_preferences" in data:
            subscriber.notification_preferences = data["notification_preferences"]

        # Set created_at if present
        if "created_at" in data:
            subscriber.created_at = datetime.fromisoformat(data["created_at"])

        return subscriber
