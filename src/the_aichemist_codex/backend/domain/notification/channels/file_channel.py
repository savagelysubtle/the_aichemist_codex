"""
File notification channel implementation.

This module provides a notification channel that logs notifications to files.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ....registry import Registry
from ..models import Notification, Subscriber
from .base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class FileNotificationChannel(BaseNotificationChannel):
    """
    Notification channel that logs to files.

    This channel sends notifications to log files organized by date and level.
    """

    def __init__(self, log_dir: Path | None = None):
        """
        Initialize the file notification channel.

        Args:
            log_dir: Directory to store notification logs (default: app logs dir)
        """
        self._registry = Registry.get_instance()
        self._log_dir = log_dir
        self._is_initialized = False

    @property
    def channel_type(self) -> str:
        """Get the channel type identifier."""
        return "file"

    async def initialize(self) -> None:
        """Initialize the file notification channel."""
        if self._is_initialized:
            return

        # If log directory not specified, use default
        if not self._log_dir:
            project_paths = self._registry.project_paths
            self._log_dir = project_paths.get_logs_dir() / "notifications"

        # Ensure log directory exists
        os.makedirs(self._log_dir, exist_ok=True)

        self._is_initialized = True
        logger.info(
            f"File notification channel initialized with log directory: {self._log_dir}"
        )

    async def close(self) -> None:
        """Close the file notification channel."""
        if not self._is_initialized:
            return

        self._is_initialized = False
        logger.info("File notification channel closed")

    async def send_notification(
        self,
        notification: Notification,
        subscriber: Subscriber,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a notification to a log file.

        Args:
            notification: The notification to send
            subscriber: The subscriber (used for filtering)
            options: Optional channel-specific options
                - log_file: Custom log file path (default: based on date and level)
                - include_metadata: Whether to include metadata (default: True)
                - append_timestamp: Whether to prepend timestamp (default: True)

        Returns:
            True if notification was sent successfully
        """
        if not self._is_initialized:
            logger.warning("File notification channel not initialized")
            return False

        # Check if we should send this notification
        if not self.should_send_notification(notification, subscriber):
            return False

        options = options or {}
        include_metadata = options.get("include_metadata", True)
        append_timestamp = options.get("append_timestamp", True)

        # Determine log file path
        log_file = options.get("log_file")
        if not log_file:
            # Generate default log file based on date and level
            today = datetime.now().strftime("%Y-%m-%d")
            level = notification.level.value
            log_file = self._log_dir / f"{today}_{level}.log"

        # Ensure log file directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Format the notification
        message = self._format_notification(notification, include_metadata)

        # Add timestamp if requested
        if append_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{timestamp}] {message}"

        # Write to the log file
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
            return True
        except Exception as e:
            logger.error(f"Error writing to log file {log_file}: {e}")
            return False

    @property
    def supports_read_receipts(self) -> bool:
        """
        Check if the channel supports read receipts.

        Returns:
            Always False for file channel
        """
        return False
