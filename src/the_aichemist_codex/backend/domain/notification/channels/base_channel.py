"""
Base notification channel implementation.

This module defines the base class for all notification channels, providing
common functionality and a standard interface.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseNotificationChannel(ABC):
    """
    Base class for notification channels.

    This abstract class defines the interface that all notification channels
    must implement for delivering notifications.
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Get the channel type identifier."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the notification channel.

        This method is called when the notification system starts up.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the notification channel.

        This method is called when the notification system shuts down.
        """
