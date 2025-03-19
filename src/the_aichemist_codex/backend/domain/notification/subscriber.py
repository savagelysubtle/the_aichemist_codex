"""
Subscriber management for the notification system.

This module provides functionality for managing notification subscribers,
including creation, storage, and retrieval.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...registry import Registry
from .models import Subscriber

logger = logging.getLogger(__name__)


class SubscriberManager:
    """
    Manager for notification subscribers.

    This class manages the storage and retrieval of notification subscribers.
    """

    def __init__(self):
        """Initialize the subscriber manager."""
        self._registry = Registry.get_instance()
        self._subscribers: dict[str, Subscriber] = {}
        self._subscribers_file: Path | None = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the subscriber manager."""
        if self._is_initialized:
            return

        # Set up subscribers file
        project_paths = self._registry.project_paths
        config_dir = project_paths.get_config_dir()
        self._subscribers_file = config_dir / "notification_subscribers.json"

        # Load subscribers
        await self._load_subscribers()

        self._is_initialized = True
        logger.info(
            f"Subscriber manager initialized with {len(self._subscribers)} subscribers"
        )

    async def close(self) -> None:
        """Close the subscriber manager."""
        if not self._is_initialized:
            return

        # Save subscribers before closing
        await self._save_subscribers()

        self._is_initialized = False
        logger.info("Subscriber manager closed")

    async def create_subscriber(
        self, name: str, channels: list[str] = None, preferences: dict[str, Any] = None
    ) -> Subscriber:
        """
        Create a new subscriber.

        Args:
            name: Name of the subscriber
            channels: List of notification channels
            preferences: Notification preferences

        Returns:
            The created subscriber

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Create subscriber
        subscriber = Subscriber(
            name=name,
            channels=channels or ["console"],
            notification_preferences=preferences or {},
        )

        # Add to subscribers
        self._subscribers[subscriber.id] = subscriber

        # Save subscribers
        await self._save_subscribers()

        logger.info(f"Created subscriber: {subscriber.id} ({name})")
        return subscriber

    async def get_subscriber(self, subscriber_id: str) -> Subscriber | None:
        """
        Get a subscriber by ID.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            The subscriber, or None if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()
        return self._subscribers.get(subscriber_id)

    async def update_subscriber(
        self,
        subscriber_id: str,
        name: str = None,
        channels: list[str] = None,
        preferences: dict[str, Any] = None,
        enabled: bool = None
    ) -> Subscriber | None:
        """
        Update a subscriber.

        Args:
            subscriber_id: ID of the subscriber
            name: New name (or None to keep current)
            channels: New channels (or None to keep current)
            preferences: New preferences (or None to keep current)
            enabled: New enabled status (or None to keep current)

        Returns:
            The updated subscriber, or None if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Get subscriber
        subscriber = await self.get_subscriber(subscriber_id)
        if not subscriber:
            logger.warning(f"Subscriber not found: {subscriber_id}")
            return None

        # Update fields
        if name is not None:
            subscriber.name = name

        if channels is not None:
            subscriber.channels = channels

        if preferences is not None:
            subscriber.notification_preferences = preferences

        if enabled is not None:
            subscriber.enabled = enabled

        # Save subscribers
        await self._save_subscribers()

        logger.info(f"Updated subscriber: {subscriber_id}")
        return subscriber

    async def delete_subscriber(self, subscriber_id: str) -> bool:
        """
        Delete a subscriber.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            True if subscriber was deleted, False if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Check if subscriber exists
        if subscriber_id not in self._subscribers:
            logger.warning(f"Subscriber not found: {subscriber_id}")
            return False

        # Remove subscriber
        del self._subscribers[subscriber_id]

        # Save subscribers
        await self._save_subscribers()

        logger.info(f"Deleted subscriber: {subscriber_id}")
        return True

    async def get_all_subscribers(self) -> list[Subscriber]:
        """
        Get all subscribers.

        Returns:
            List of all subscribers

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()
        return list(self._subscribers.values())

    async def get_subscribers_by_channel(self, channel_type: str) -> list[Subscriber]:
        """
        Get subscribers that use a specific channel.

        Args:
            channel_type: Type of channel

        Returns:
            List of subscribers that use the channel

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()
        return [s for s in self._subscribers.values() if channel_type in s.channels and s.enabled]

    async def _load_subscribers(self) -> None:
        """
        Load subscribers from storage.

        Raises:
            IOError: If loading fails
        """
        self._subscribers = {}

        # Check if subscribers file exists
        if not self._subscribers_file.exists():
            logger.info(f"Subscribers file does not exist: {self._subscribers_file}")
            return

        try:
            with open(self._subscribers_file, encoding="utf-8") as f:
                data = json.load(f)

            for subscriber_data in data:
                subscriber = Subscriber.from_dict(subscriber_data)
                self._subscribers[subscriber.id] = subscriber

            logger.info(f"Loaded {len(self._subscribers)} subscribers")

        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            raise OSError(f"Failed to load subscribers: {e}") from e

    async def _save_subscribers(self) -> None:
        """
        Save subscribers to storage.

        Raises:
            IOError: If saving fails
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._subscribers_file), exist_ok=True)

            # Convert subscribers to dicts
            data = [subscriber.to_dict() for subscriber in self._subscribers.values()]

            # Write to file
            with open(self._subscribers_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self._subscribers)} subscribers")

        except Exception as e:
            logger.error(f"Error saving subscribers: {e}")
            raise OSError(f"Failed to save subscribers: {e}") from e

    def _ensure_initialized(self) -> None:
        """
        Ensure that the manager is initialized.

        Raises:
            RuntimeError: If manager is not initialized
        """
        if not self._is_initialized:
            raise RuntimeError("Subscriber manager is not initialized")
