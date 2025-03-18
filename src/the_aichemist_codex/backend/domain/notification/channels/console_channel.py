"""
Console notification channel implementation.

This module provides a notification channel that outputs notifications to the console.
"""

import logging
import sys
from typing import Any

from ..models import Notification, NotificationLevel, Subscriber
from .base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class ConsoleNotificationChannel(BaseNotificationChannel):
    """
    Notification channel that outputs to the console.

    This channel sends notifications to the system console using color-coded
    output based on notification level.
    """

    # ANSI color codes
    COLORS = {
        NotificationLevel.DEBUG: "\033[37m",  # Light gray
        NotificationLevel.INFO: "\033[0m",  # Default
        NotificationLevel.WARNING: "\033[33m",  # Yellow
        NotificationLevel.ERROR: "\033[31m",  # Red
        NotificationLevel.CRITICAL: "\033[41m\033[37m",  # White on red background
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        """
        Initialize the console notification channel.

        Args:
            use_colors: Whether to use ANSI colors in output
        """
        self._use_colors = use_colors
        self._is_initialized = False

    @property
    def channel_type(self) -> str:
        """Get the channel type identifier."""
        return "console"

    async def initialize(self) -> None:
        """Initialize the console notification channel."""
        if self._is_initialized:
            return

        # Detect if colors should be disabled (e.g., non-TTY output)
        if self._use_colors and not sys.stdout.isatty():
            self._use_colors = False

        self._is_initialized = True
        logger.info("Console notification channel initialized")

    async def close(self) -> None:
        """Close the console notification channel."""
        if not self._is_initialized:
            return

        self._is_initialized = False
        logger.info("Console notification channel closed")

    async def send_notification(
        self,
        notification: Notification,
        subscriber: Subscriber,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a notification to the console.

        Args:
            notification: The notification to send
            subscriber: The subscriber (not used for console output)
            options: Optional channel-specific options
                - stream: Output stream ("stdout" or "stderr", default: based on level)
                - include_metadata: Whether to include metadata (default: False)

        Returns:
            True if notification was sent successfully
        """
        if not self._is_initialized:
            logger.warning("Console notification channel not initialized")
            return False

        # Check if we should send this notification
        if not self.should_send_notification(notification, subscriber):
            return False

        options = options or {}

        # Determine output stream
        stream_name = options.get("stream")
        if not stream_name:
            # Default to stderr for warnings and above
            if notification.level in (
                NotificationLevel.WARNING,
                NotificationLevel.ERROR,
                NotificationLevel.CRITICAL,
            ):
                stream_name = "stderr"
            else:
                stream_name = "stdout"

        stream = sys.stderr if stream_name == "stderr" else sys.stdout

        # Format the notification
        include_metadata = options.get("include_metadata", False)
        message = self._format_notification(notification, include_metadata)

        # Add colors if enabled
        if self._use_colors:
            color = self.COLORS.get(
                notification.level, self.COLORS[NotificationLevel.INFO]
            )
            message = f"{color}{message}{self.RESET}"

        # Write to the stream
        try:
            print(message, file=stream, flush=True)
            return True
        except Exception as e:
            logger.error(f"Error writing to console: {e}")
            return False

    @property
    def supports_read_receipts(self) -> bool:
        """
        Check if the channel supports read receipts.

        Returns:
            Always False for console channel
        """
        return False
