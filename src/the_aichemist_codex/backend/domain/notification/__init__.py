"""
Notification system package.

This package provides a system for sending notifications to subscribers
through various channels.
"""

from .models import Notification, NotificationLevel, NotificationStatus, Subscriber
from .notification_manager import NotificationManagerImpl
from .channels import (
    BaseNotificationChannel,
    ConsoleNotificationChannel,
    FileNotificationChannel,
    EmailNotificationChannel
)

__all__ = [
    "Notification",
    "NotificationLevel",
    "NotificationStatus",
    "Subscriber",
    "NotificationManagerImpl",
    "BaseNotificationChannel",
    "ConsoleNotificationChannel",
    "FileNotificationChannel",
    "EmailNotificationChannel"
]
