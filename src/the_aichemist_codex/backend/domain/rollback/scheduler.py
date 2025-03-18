"""
Version scheduler for automatic versioning.

This module provides functionality for scheduling automatic version creation
based on configurable policies.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class VersionScheduler:
    """
    Scheduler for creating automatic versions.

    This class provides functionality for automatically creating versions
    of files based on configured schedules and policies.
    """

    def __init__(self, rollback_manager):
        """
        Initialize the version scheduler.

        Args:
            rollback_manager: The rollback manager to use for versioning
        """
        self._rollback_manager = rollback_manager
        self._registry = rollback_manager._registry
        self._task = None
        self._running = False
        self._watched_paths: set[Path] = set()
        self._last_run_times: dict[str, datetime] = {}
        self._interval = 3600  # Default: 1 hour in seconds

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        # Get configuration
        config = self._registry.config_provider
        self._interval = config.get_config(
            "rollback.auto_version_interval_seconds", 3600
        )

        # Get watched paths from config
        watched_paths = config.get_config("rollback.watched_paths", [])
        for path_str in watched_paths:
            path = Path(path_str)
            if path.exists():
                self._watched_paths.add(path)

        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Version scheduler started with interval {self._interval}s")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running or self._task is None:
            return

        self._running = False
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

        self._task = None
        logger.info("Version scheduler stopped")

    async def add_watched_path(self, path: Path) -> None:
        """Add a path to watch for automatic versioning."""
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        self._watched_paths.add(path)
        logger.info(f"Added path to version scheduler: {path}")

    async def remove_watched_path(self, path: Path) -> None:
        """Remove a path from automatic versioning."""
        if path in self._watched_paths:
            self._watched_paths.remove(path)
            logger.info(f"Removed path from version scheduler: {path}")

    async def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        logger.info("Starting versioning scheduler loop")

        while self._running:
            try:
                # Check for files that need versioning
                await self._check_watched_paths()

                # Sleep until next check
                await asyncio.sleep(self._interval)

            except asyncio.CancelledError:
                # Scheduler is being stopped
                break
            except Exception as e:
                logger.error(f"Error in version scheduler: {e}")
                # Continue running despite errors
                await asyncio.sleep(60)  # Sleep briefly before retrying

        logger.info("Versioning scheduler loop terminated")

    async def _check_watched_paths(self) -> None:
        """Check all watched paths for files that need versioning."""
        now = datetime.now()
        config = self._registry.config_provider

        # Get configuration
        min_age_hours = config.get_config("rollback.min_version_age_hours", 24)
        min_age = timedelta(hours=min_age_hours)

        # Get file patterns to watch
        patterns = config.get_config(
            "rollback.watched_patterns", ["*.py", "*.md", "*.txt"]
        )

        for path in self._watched_paths:
            try:
                if not path.exists():
                    logger.warning(f"Watched path no longer exists: {path}")
                    continue

                if path.is_file():
                    # Single file watch
                    await self._check_file_for_versioning(path, now, min_age)
                else:
                    # Directory watch
                    for pattern in patterns:
                        for file_path in path.glob(pattern):
                            if file_path.is_file():
                                await self._check_file_for_versioning(
                                    file_path, now, min_age
                                )

            except Exception as e:
                logger.error(f"Error checking path {path} for versioning: {e}")

    async def _check_file_for_versioning(
        self, file_path: Path, now: datetime, min_age: timedelta
    ) -> None:
        """
        Check if a file needs versioning.

        Args:
            file_path: Path to the file
            now: Current time
            min_age: Minimum age between versions
        """
        file_path_str = str(file_path)

        try:
            # Check if file has been modified since last version
            if file_path_str in self._last_run_times:
                last_run = self._last_run_times[file_path_str]
                if now - last_run < min_age:
                    # Too soon for another version
                    return

            # Check modified time
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Get most recent version
            versions = await self._rollback_manager.get_file_versions(
                file_path, limit=1
            )

            if versions:
                # Check if file has been modified since last version
                last_version_time = datetime.fromisoformat(
                    versions[0].get("timestamp", "")
                )

                if modified_time <= last_version_time:
                    # File hasn't been modified since last version
                    return

                # Check if enough time has passed since last version
                if now - last_version_time < min_age:
                    # Too soon for another version
                    return

            # Create a new version
            await self._rollback_manager.create_version(
                file_path,
                version_name=f"Auto_{now.strftime('%Y%m%d_%H%M%S')}",
                tags=["auto"],
                metadata={"source": "scheduler"},
            )

            # Update last run time
            self._last_run_times[file_path_str] = now

            logger.info(f"Created automatic version for {file_path}")

        except Exception as e:
            logger.error(f"Error creating automatic version for {file_path}: {e}")
