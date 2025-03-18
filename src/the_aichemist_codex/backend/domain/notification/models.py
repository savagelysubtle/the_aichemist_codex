"""
Models for the notification system.

This module defines the data structures used in the notification system,
including Notification and Subscriber classes.
"""

import datetime
import enum
import uuid
from dataclasses import dataclass, field
from typing import Any


class NotificationLevel(enum.Enum):
    """Enumeration of notification severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SubscriptionChannel(enum.Enum):
    """Enumeration of available notification channels."""

    IN_APP = "in_app"
    EMAIL = "email"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """
    Represents a single notification in the system.

    Attributes:
        id: Unique identifier for the notification
        message: The notification message text
        level: Severity level of the notification
        timestamp: When the notification was created
        metadata: Additional data associated with the notification
        sender_id: Identifier of the component that sent the notification
    """

    message: str
    level: NotificationLevel = NotificationLevel.INFO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    sender_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert notification to dictionary for storage or transmission."""
        return {
            "id": self.id,
            "message": self.message,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "sender_id": self.sender_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        """Create a Notification instance from a dictionary."""
        # Convert string timestamp to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.datetime.fromisoformat(data["timestamp"])

        # Convert string level to enum
        if isinstance(data.get("level"), str):
            data["level"] = NotificationLevel(data["level"])

        return cls(**data)


@dataclass
class Subscriber:
    """
    Represents a subscriber to notifications.

    Attributes:
        id: Unique identifier for the subscriber
        name: Name of the subscriber
        channels: List of channels the subscriber wants to receive notifications on
        enabled: Whether the subscriber is currently accepting notifications
        created_at: When the subscriber was created
        last_active: When the subscriber was last active
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str | None = None
    channels: list[SubscriptionChannel] = field(
        default_factory=lambda: [SubscriptionChannel.IN_APP]
    )
    enabled: bool = True
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_active: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert subscriber to dictionary for storage or transmission."""
        return {
            "id": self.id,
            "name": self.name,
            "channels": [channel.value for channel in self.channels],
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subscriber":
        """Create a Subscriber instance from a dictionary."""
        # Convert string timestamps to datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.datetime.fromisoformat(data["created_at"])

        if isinstance(data.get("last_active"), str) and data.get("last_active"):
            data["last_active"] = datetime.datetime.fromisoformat(data["last_active"])

        # Convert channel strings to enum values
        if "channels" in data and isinstance(data["channels"], list):
            data["channels"] = [
                SubscriptionChannel(channel) for channel in data["channels"]
            ]

        return cls(**data)


@dataclass
class NotificationDelivery:
    """
    Represents the delivery status of a notification to a subscriber.

    Attributes:
        notification_id: ID of the notification
        subscriber_id: ID of the subscriber
        delivered: Whether the notification has been delivered
        read: Whether the notification has been read
        delivered_at: When the notification was delivered
        read_at: When the notification was read
    """

    notification_id: str
    subscriber_id: str
    delivered: bool = False
    read: bool = False
    delivered_at: datetime.datetime | None = None
    read_at: datetime.datetime | None = None

    def mark_delivered(self) -> None:
        """Mark the notification as delivered."""
        self.delivered = True
        self.delivered_at = datetime.datetime.now()

    def mark_read(self) -> None:
        """Mark the notification as read."""
        self.read = True
        self.read_at = datetime.datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert notification delivery to dictionary for storage or transmission."""
        return {
            "notification_id": self.notification_id,
            "subscriber_id": self.subscriber_id,
            "delivered": self.delivered,
            "read": self.read,
            "delivered_at": self.delivered_at.isoformat()
            if self.delivered_at
            else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationDelivery":
        """Create a NotificationDelivery instance from a dictionary."""
        # Convert string timestamps to datetime
        if isinstance(data.get("delivered_at"), str) and data.get("delivered_at"):
            data["delivered_at"] = datetime.datetime.fromisoformat(data["delivered_at"])

        if isinstance(data.get("read_at"), str) and data.get("read_at"):
            data["read_at"] = datetime.datetime.fromisoformat(data["read_at"])

        return cls(**data)
