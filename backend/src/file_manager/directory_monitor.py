"""
Enhanced directory monitoring for The Aichemist Codex.

This module provides advanced directory monitoring capabilities including:
- Priority-based monitoring for directories
- Resource throttling for high-change-rate directories
- Recursive directory discovery with customizable depth
- Dynamic directory registration and unregistration
"""

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from watchdog.observers import Observer

from backend.src.config.config_loader import config
from backend.src.file_manager.file_watcher import FileEventHandler

logger = logging.getLogger(__name__)


class DirectoryPriority(Enum):
    """Priority levels for monitored directories."""

    CRITICAL = 0  # Highest priority, always process immediately
    HIGH = 1  # Process with minimal delay
    NORMAL = 2  # Standard processing
    LOW = 3  # Process when resources available


@dataclass
class DirectoryConfig:
    """Configuration for a monitored directory."""

    path: Path
    priority: DirectoryPriority = DirectoryPriority.NORMAL
    recursive_depth: int = 3  # How deep to scan subdirectories (0 = no recursion)
    throttle: float = 1.0  # Seconds to wait between processing in high-activity dirs


class DirectoryMonitor:
    """
    Enhanced directory monitoring with priority-based processing and dynamic configuration.

    Features:
    - Priority-based monitoring for different directories
    - Resource throttling for high-change-rate directories
    - Recursive directory discovery with customizable depth
    - Dynamic directory registration/unregistration
    """

    def __init__(self):
        """Initialize the directory monitor."""
        self.directories: dict[str, DirectoryConfig] = {}
        self.observers: dict[str, Any] = {}  # Using Any for Observer type
        self.event_handlers: dict[str, Any] = {}  # Using Any for FileEventHandler type
        self.active = False
        self.discovery_thread = None
        self.discovery_stop_event = threading.Event()

        # Default settings
        self.default_priority = self._parse_priority(
            config.get("default_priority", "normal")
        )
        self.default_recursive_depth = config.get("default_recursive_depth", 3)
        self.default_throttle = config.get("default_throttle", 1.0)

        # Auto-discovery settings
        self.auto_discover = config.get("auto_discover_directories", False)
        self.auto_discover_parent_dirs = config.get("auto_discover_parent_dirs", [])
        self.auto_discover_interval = config.get("auto_discover_interval", 3600)
        self.auto_discover_depth = config.get("auto_discover_depth", 1)

    def start(self):
        """Start monitoring all configured directories."""
        if self.active:
            logger.warning("Directory monitor is already active")
            return

        # Load directories from config
        self._load_directories_from_config()

        # Start monitoring each directory
        for dir_path, dir_config in self.directories.items():
            self._start_monitoring_directory(dir_path, dir_config)

        # Start auto-discovery if enabled
        if self.auto_discover and self.auto_discover_parent_dirs:
            self._start_directory_discovery()

        self.active = True
        logger.info(
            f"Directory monitor started with {len(self.directories)} directories"
        )

    def stop(self):
        """Stop monitoring all directories."""
        if not self.active:
            logger.warning("Directory monitor is not active")
            return

        # Stop discovery thread if running
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_stop_event.set()
            self.discovery_thread.join(timeout=5)

        # Stop all observers
        for dir_path, observer in self.observers.items():
            logger.info(f"Stopping observer for {dir_path}")
            observer.stop()

        # Wait for all observers to stop
        for dir_path, observer in self.observers.items():
            observer.join()

        self.observers.clear()
        self.event_handlers.clear()
        self.active = False
        logger.info("Directory monitor stopped")

    def register_directory(self, dir_path: str | Path, **kwargs) -> bool:
        """
        Dynamically register a new directory for monitoring.

        Args:
            dir_path: Path to the directory to monitor
            **kwargs: Optional parameters (priority, recursive_depth, throttle)

        Returns:
            True if successfully registered, False otherwise
        """
        path = Path(dir_path).resolve()
        path_str = str(path)

        # Check if directory exists
        if not path.exists() or not path.is_dir():
            logger.error(f"Cannot register non-existent directory: {path}")
            return False

        # Check if already monitoring
        if path_str in self.directories:
            logger.warning(f"Already monitoring directory: {path}")
            return False

        # Create directory configuration
        dir_config = DirectoryConfig(
            path=path,
            priority=self._parse_priority(kwargs.get("priority", "normal")),
            recursive_depth=kwargs.get("recursive_depth", self.default_recursive_depth),
            throttle=kwargs.get("throttle", self.default_throttle),
        )

        # Add to directories
        self.directories[path_str] = dir_config

        # Start monitoring if active
        if self.active:
            self._start_monitoring_directory(path_str, dir_config)

        logger.info(
            f"Registered directory: {path} (Priority: {dir_config.priority.name}, "
            f"Depth: {dir_config.recursive_depth}, Throttle: {dir_config.throttle}s)"
        )
        return True

    def unregister_directory(self, dir_path: str | Path) -> bool:
        """
        Stop monitoring a directory and remove it from the registry.

        Args:
            dir_path: Path to the directory to stop monitoring

        Returns:
            True if successfully unregistered, False otherwise
        """
        path = Path(dir_path).resolve()
        path_str = str(path)

        # Check if directory is monitored
        if path_str not in self.directories:
            logger.warning(f"Directory not monitored: {path}")
            return False

        # Stop observer if active
        if path_str in self.observers:
            observer = self.observers[path_str]
            observer.stop()
            observer.join()
            del self.observers[path_str]

        # Remove event handler
        if path_str in self.event_handlers:
            del self.event_handlers[path_str]

        # Remove from directories
        del self.directories[path_str]

        logger.info(f"Unregistered directory: {path}")
        return True

    def update_directory_config(self, dir_path: str | Path, **kwargs) -> bool:
        """
        Update configuration for a monitored directory.

        Args:
            dir_path: Path to the directory
            **kwargs: Parameters to update (priority, recursive_depth, throttle)

        Returns:
            True if successfully updated, False otherwise
        """
        path = Path(dir_path).resolve()
        path_str = str(path)

        # Check if directory is monitored
        if path_str not in self.directories:
            logger.warning(f"Directory not monitored: {path}")
            return False

        # Get current config
        dir_config = self.directories[path_str]

        # Update config
        if "priority" in kwargs:
            dir_config.priority = self._parse_priority(kwargs["priority"])
        if "recursive_depth" in kwargs:
            dir_config.recursive_depth = kwargs["recursive_depth"]
        if "throttle" in kwargs:
            dir_config.throttle = kwargs["throttle"]

        # Restart monitoring if needed
        if self.active and path_str in self.observers:
            # Stop current observer
            observer = self.observers[path_str]
            observer.stop()
            observer.join()
            del self.observers[path_str]

            # Start new observer with updated config
            self._start_monitoring_directory(path_str, dir_config)

        logger.info(
            f"Updated directory config: {path} (Priority: {dir_config.priority.name}, "
            f"Depth: {dir_config.recursive_depth}, Throttle: {dir_config.throttle}s)"
        )
        return True

    def get_directory_config(self, dir_path: str | Path) -> DirectoryConfig | None:
        """
        Get the current configuration for a monitored directory.

        Args:
            dir_path: Path to the directory

        Returns:
            DirectoryConfig if found, None otherwise
        """
        path = Path(dir_path).resolve()
        path_str = str(path)

        return self.directories.get(path_str)

    def get_all_directories(self) -> dict[str, DirectoryConfig]:
        """
        Get all monitored directories and their configurations.

        Returns:
            Dictionary mapping directory paths to configurations
        """
        return self.directories.copy()

    def _load_directories_from_config(self):
        """Load directory configurations from the global config."""
        dirs_to_watch = config.get("directories_to_watch", [])

        for dir_entry in dirs_to_watch:
            try:
                # Handle different formats (string vs dict)
                if isinstance(dir_entry, str):
                    # Simple format - just a path string
                    self.register_directory(dir_entry)
                elif isinstance(dir_entry, dict):
                    # Advanced format with additional settings
                    path = dir_entry.get("path")
                    if not path:
                        logger.warning(
                            f"Skipping directory entry with no path: {dir_entry}"
                        )
                        continue

                    self.register_directory(
                        path,
                        priority=dir_entry.get("priority", "normal"),
                        recursive_depth=dir_entry.get(
                            "recursive_depth", self.default_recursive_depth
                        ),
                        throttle=dir_entry.get("throttle", self.default_throttle),
                    )
                else:
                    logger.warning(f"Unsupported directory entry format: {dir_entry}")
            except Exception as e:
                logger.error(f"Error registering directory from config: {e}")

    def _start_monitoring_directory(self, dir_path: str, dir_config: DirectoryConfig):
        """
        Start monitoring a specific directory with its configuration.

        Args:
            dir_path: String path to the directory
            dir_config: Configuration for the directory
        """
        try:
            # Create event handler with throttling based on priority
            event_handler = FileEventHandler(dir_config.path)
            # Convert float throttle to int for debounce_interval (rounded to nearest integer)
            throttle_value = self._get_throttle_for_priority(
                dir_config.priority, dir_config.throttle
            )
            event_handler.debounce_interval = int(round(throttle_value))

            # Create and start observer
            observer = Observer()

            # Schedule with recursive flag based on depth
            recursive = dir_config.recursive_depth != 0
            observer.schedule(event_handler, dir_path, recursive=recursive)

            # If recursive with limited depth, handle that specially
            if recursive and dir_config.recursive_depth > 0:
                self._handle_limited_depth_recursion(
                    dir_config.path, dir_config.recursive_depth, event_handler, observer
                )

            observer.start()

            # Store in dictionaries
            self.observers[dir_path] = observer
            self.event_handlers[dir_path] = event_handler

            logger.info(
                f"Started monitoring: {dir_path} (Priority: {dir_config.priority.name}, "
                f"Depth: {dir_config.recursive_depth}, Throttle: {event_handler.debounce_interval}s)"
            )
        except Exception as e:
            logger.error(f"Error starting monitoring for {dir_path}: {e}")

    def _handle_limited_depth_recursion(
        self,
        base_path: Path,
        max_depth: int,
        event_handler,
        observer,
    ):
        """
        Handle recursive monitoring with a limited depth.

        Args:
            base_path: Base directory path
            max_depth: Maximum recursion depth
            event_handler: Event handler to use
            observer: Observer to schedule with
        """
        # Get all subdirectories up to max_depth
        subdirs = []

        def collect_subdirs(path, current_depth=1):
            if current_depth > max_depth:
                return

            try:
                for item in path.iterdir():
                    if item.is_dir():
                        subdirs.append(item)
                        collect_subdirs(item, current_depth + 1)
            except (PermissionError, OSError) as e:
                logger.warning(f"Error accessing {path}: {e}")

        collect_subdirs(base_path)

        # Schedule each subdirectory individually to ensure they're monitored
        for subdir in subdirs:
            try:
                observer.schedule(event_handler, str(subdir), recursive=False)
            except Exception as e:
                logger.warning(f"Error scheduling {subdir}: {e}")

    def _start_directory_discovery(self):
        """Start the directory auto-discovery thread."""
        if self.discovery_thread and self.discovery_thread.is_alive():
            logger.warning("Directory discovery thread is already running")
            return

        # Reset stop event
        self.discovery_stop_event.clear()

        # Start thread
        self.discovery_thread = threading.Thread(
            target=self._directory_discovery_loop, daemon=True
        )
        self.discovery_thread.start()
        logger.info("Directory auto-discovery started")

    def _directory_discovery_loop(self):
        """Background thread for discovering new directories."""
        while not self.discovery_stop_event.is_set():
            try:
                self._discover_new_directories()
            except Exception as e:
                logger.error(f"Error during directory discovery: {e}")

            # Wait for next interval or until stopped
            self.discovery_stop_event.wait(self.auto_discover_interval)

    def _discover_new_directories(self):
        """Scan parent directories for new subdirectories to monitor."""
        # Get all parent directories to scan
        parent_dirs = [Path(p).resolve() for p in self.auto_discover_parent_dirs]

        # Get currently monitored directories
        monitored = set(self.directories.keys())

        # New directories to add
        new_dirs = set()

        # Scan each parent directory
        for parent in parent_dirs:
            if not parent.exists() or not parent.is_dir():
                logger.warning(f"Auto-discovery parent does not exist: {parent}")
                continue

            # Find subdirectories up to the configured depth
            def scan_dir(path, current_depth=1):
                if current_depth > self.auto_discover_depth:
                    return

                try:
                    for item in path.iterdir():
                        if item.is_dir():
                            new_dirs.add(str(item.resolve()))
                            scan_dir(item, current_depth + 1)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Error accessing {path} during discovery: {e}")

            scan_dir(parent)

        # Register new directories that aren't already monitored
        for dir_path in new_dirs:
            if dir_path not in monitored:
                self.register_directory(dir_path)

    def _parse_priority(self, priority_str: str) -> DirectoryPriority:
        """
        Parse a priority string to a DirectoryPriority enum.

        Args:
            priority_str: String representation of priority

        Returns:
            DirectoryPriority enum value
        """
        priority_map = {
            "critical": DirectoryPriority.CRITICAL,
            "high": DirectoryPriority.HIGH,
            "normal": DirectoryPriority.NORMAL,
            "low": DirectoryPriority.LOW,
        }

        return priority_map.get(priority_str.lower(), DirectoryPriority.NORMAL)

    def _get_throttle_for_priority(
        self, priority: DirectoryPriority, base_throttle: float
    ) -> float:
        """
        Calculate the appropriate throttle/debounce value based on priority.

        Args:
            priority: Directory priority level
            base_throttle: Base throttle value from config

        Returns:
            Adjusted throttle value in seconds
        """
        priority_multipliers = {
            DirectoryPriority.CRITICAL: 0.0,  # No throttling for critical
            DirectoryPriority.HIGH: 0.5,  # Half throttle for high
            DirectoryPriority.NORMAL: 1.0,  # Normal throttle
            DirectoryPriority.LOW: 2.0,  # Double throttle for low
        }

        return base_throttle * priority_multipliers.get(priority, 1.0)


# Create a singleton instance
directory_monitor = DirectoryMonitor()
