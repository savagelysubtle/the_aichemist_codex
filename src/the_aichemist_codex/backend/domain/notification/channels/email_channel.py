"""
Email notification channel implementation.

This module provides a notification channel that sends notifications via email.
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Any

from ....registry import Registry
from ..models import Notification, NotificationLevel, Subscriber
from .base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class EmailNotificationChannel(BaseNotificationChannel):
    """
    Notification channel that sends via email.

    This channel sends notifications as emails to subscribers.
    """

    def __init__(self):
        """Initialize the email notification channel."""
        self._registry = Registry.get_instance()
        self._is_initialized = False
        self._smtp_host = "localhost"
        self._smtp_port = 25
        self._smtp_user = None
        self._smtp_password = None
        self._use_ssl = False
        self._from_address = "notifications@aichemist.codex"

    @property
    def channel_type(self) -> str:
        """Get the channel type identifier."""
        return "email"

    async def initialize(self) -> None:
        """Initialize the email notification channel."""
        if self._is_initialized:
            return

        # Load configuration
        config = self._registry.config_provider
        self._smtp_host = config.get_config("notification.email.smtp_host", "localhost")
        self._smtp_port = config.get_config("notification.email.smtp_port", 25)
        self._smtp_user = config.get_config("notification.email.smtp_user")
        self._smtp_password = config.get_config("notification.email.smtp_password")
        self._use_ssl = config.get_config("notification.email.use_ssl", False)
        self._from_address = config.get_config(
            "notification.email.from_address", "notifications@aichemist.codex"
        )

        self._is_initialized = True
        logger.info(
            f"Email notification channel initialized with SMTP host: {self._smtp_host}"
        )

    async def close(self) -> None:
        """Close the email notification channel."""
        if not self._is_initialized:
            return

        self._is_initialized = False
        logger.info("Email notification channel closed")

    async def send_notification(
        self,
        notification: Notification,
        subscriber: Subscriber,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a notification via email.

        Args:
            notification: The notification to send
            subscriber: The subscriber to send to
            options: Optional channel-specific options
                - to: Email address to send to (default: from subscriber preferences)
                - subject_prefix: Prefix for the email subject (default: "[AIChemist]")
                - include_metadata: Whether to include metadata (default: True)
                - html_format: Whether to send as HTML (default: False)

        Returns:
            True if notification was sent successfully
        """
        if not self._is_initialized:
            logger.warning("Email notification channel not initialized")
            return False

        # Check if we should send this notification
        if not self.should_send_notification(notification, subscriber):
            return False

        options = options or {}

        # Get email address from subscriber preferences or options
        to_email = options.get("to")
        if not to_email:
            to_email = subscriber.notification_preferences.get("email")

        if not to_email:
            logger.warning(f"No email address for subscriber {subscriber.id}")
            return False

        # Get other options
        subject_prefix = options.get("subject_prefix", "[AIChemist]")
        include_metadata = options.get("include_metadata", True)
        html_format = options.get("html_format", False)

        # Create email message
        msg = EmailMessage()
        msg["From"] = self._from_address
        msg["To"] = to_email

        # Set subject based on notification level and message
        level_prefix = (
            f"[{notification.level.value.upper()}]"
            if notification.level != NotificationLevel.INFO
            else ""
        )
        subject = f"{subject_prefix} {level_prefix} {notification.message[:50]}"
        if len(notification.message) > 50:
            subject += "..."
        msg["Subject"] = subject

        # Format the notification body
        body = self._format_email_body(notification, include_metadata, html_format)

        # Set the message content
        if html_format:
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        # Send the email
        try:
            self._send_email(msg)
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    @property
    def supports_read_receipts(self) -> bool:
        """
        Check if the channel supports read receipts.

        Returns:
            Always False for email channel (could be extended)
        """
        return False

    def _send_email(self, msg: EmailMessage) -> None:
        """
        Send an email message.

        Args:
            msg: The email message to send

        Raises:
            Exception: If sending fails
        """
        if self._use_ssl:
            with smtplib.SMTP_SSL(self._smtp_host, self._smtp_port) as smtp:
                if self._smtp_user and self._smtp_password:
                    smtp.login(self._smtp_user, self._smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as smtp:
                if self._smtp_user and self._smtp_password:
                    smtp.starttls()
                    smtp.login(self._smtp_user, self._smtp_password)
                smtp.send_message(msg)

    def _format_email_body(
        self, notification: Notification, include_metadata: bool, html_format: bool
    ) -> str:
        """
        Format a notification as an email body.

        Args:
            notification: The notification to format
            include_metadata: Whether to include metadata
            html_format: Whether to format as HTML

        Returns:
            Formatted email body
        """
        if html_format:
            # HTML format
            body = (
                f"<h2>{notification.level.value.upper()}: {notification.message}</h2>"
            )

            if include_metadata and notification.metadata:
                body += "<h3>Metadata:</h3><ul>"
                for key, value in notification.metadata.items():
                    body += f"<li><strong>{key}:</strong> {value}</li>"
                body += "</ul>"

            # Add styling
            color = self._get_level_color(notification.level)
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    h2 {{ color: {color}; }}
                    ul {{ margin-top: 10px; }}
                </style>
            </head>
            <body>
                {body}
                <p><small>Sent at {notification.created_at.strftime("%Y-%m-%d %H:%M:%S")}</small></p>
            </body>
            </html>
            """
        else:
            # Plain text format
            body = f"{notification.level.value.upper()}: {notification.message}\n\n"

            if include_metadata and notification.metadata:
                body += "Metadata:\n"
                for key, value in notification.metadata.items():
                    body += f"  {key}: {value}\n"
                body += "\n"

            body += f"Sent at {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

        return body

    def _get_level_color(self, level: NotificationLevel) -> str:
        """
        Get a color for a notification level.

        Args:
            level: The notification level

        Returns:
            HTML color code
        """
        colors = {
            NotificationLevel.DEBUG: "#999999",  # Gray
            NotificationLevel.INFO: "#000000",  # Black
            NotificationLevel.WARNING: "#FF9900",  # Orange
            NotificationLevel.ERROR: "#CC0000",  # Red
            NotificationLevel.CRITICAL: "#990000",  # Dark red
        }
        return colors.get(level, "#000000")
