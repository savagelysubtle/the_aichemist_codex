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
from pathlib import Path

from watchdog.observers import Observer

from backend.src.config.config_loader import config

# Import from common module instead of file_watcher
from backend.src.file_manager.common import DirectoryPriority

logger = logging.getLogger(__name__)


@dataclass
class DirectoryConfig:
    """Configuration for a monitored directory."""

    path: Path
    priority: DirectoryPriority = DirectoryPriority.NORMAL
    recursive_depth: int = 3  # How deep to scan subdirectories (0 = no recursion)
    throttle: float = 1.0  # Seconds to wait between processing in high-activity dirs


class DirectoryMonitor:
    """
    Enhanced directory monitoring with priority-based processing.

    This class provides advanced directory monitoring capabilities with
    configurable priorities, throttling, and recursive depth.
    """

    def __init__(self):
        """Initialize the directory monitor."""
        self.observers = {}  # Dictionary mapping path to Observer
        self.directory_configs = {}  # Dictionary mapping path to DirectoryConfig
        self.discovery_thread = None  # Directory discovery thread
        self.discovery_interval = config.get(
            "file_manager.directory_discovery_interval", 300
        )  # 5 minutes default
        self.discovery_running = False
        self.discovery_lock = threading.Lock()
        self.base_throttle = config.get("file_manager.base_throttle", 1.0)
        self._load_directories_from_config()

    def start(self):
        """Start monitoring all registered directories."""
        logger.info("Starting directory monitoring")
        for dir_path, dir_config in self.directory_configs.items():
            self._start_monitoring_directory(dir_path, dir_config)

        # Start directory discovery if enabled
        if config.get("file_manager.enable_directory_discovery", False):
            self._start_directory_discovery()

    def stop(self):
        """Stop monitoring all directories."""
        logger.info("Stopping directory monitoring")
        # Stop discovery thread
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_running = False
            self.discovery_thread.join(timeout=5.0)
            if self.discovery_thread.is_alive():
                logger.warning(
                    "Directory discovery thread did not terminate gracefully"
                )

        # Stop all observers
        for observer in self.observers.values():
            if observer.is_alive():
                observer.stop()
                observer.join(timeout=5.0)
                if observer.is_alive():
                    logger.warning(
                        "Observer did not terminate gracefully, some resources may not be released"
                    )

        self.observers.clear()

    def register_directory(
        self,
        dir_path: str | Path,
        priority: DirectoryPriority | str | None = None,
        recursive_depth: int | None = None,
        throttle: float | None = None,
    ) -> bool:
        """
        Register a directory for monitoring.

        Args:
            dir_path: Path to the directory to monitor
            priority: DirectoryPriority enum value or string name
            recursive_depth: How deep to scan subdirectories
            throttle: Seconds to wait between processing in high-activity dirs

        Returns:
            bool: True if registration was successful, False otherwise
        """
        path = Path(dir_path).resolve()
        if not path.exists() or not path.is_dir():
            logger.error(f"Cannot register non-existent directory: {path}")
            return False

        # Convert string priority to enum if needed
        if priority is not None and isinstance(priority, str):
            priority = self._parse_priority(priority)

        # Create directory config
        dir_config = DirectoryConfig(
            path=path,
            priority=priority if priority is not None else DirectoryPriority.NORMAL,
            recursive_depth=recursive_depth if recursive_depth is not None else 3,
            throttle=throttle if throttle is not None else self.base_throttle,
        )

        # Store the config
        str_path = str(path)
        self.directory_configs[str_path] = dir_config

        # Start monitoring if we're already running
        if self.observers:
            self._start_monitoring_directory(str_path, dir_config)

        logger.info(
            f"Registered directory: {path} (Priority: {dir_config.priority.name}, "
            f"Depth: {dir_config.recursive_depth}, Throttle: {dir_config.throttle}s)"
        )
        return True

    def unregister_directory(self, dir_path: str | Path) -> bool:
        """
        Unregister a directory from monitoring.

        Args:
            dir_path: Path to the directory to stop monitoring

        Returns:
            bool: True if unregistration was successful, False otherwise
        """
        path = Path(dir_path).resolve()
        str_path = str(path)

        if str_path not in self.directory_configs:
            logger.warning(f"Directory not registered: {path}")
            return False

        # Stop and remove the observer
        if str_path in self.observers:
            observer = self.observers[str_path]
            if observer.is_alive():
                observer.stop()
                observer.join(timeout=5.0)
                if observer.is_alive():
                    logger.warning(f"Observer for {path} did not terminate gracefully")
            del self.observers[str_path]

        # Remove the config
        del self.directory_configs[str_path]
        logger.info(f"Unregistered directory: {path}")
        return True

    def update_directory_config(self, dir_path: str | Path, **kwargs) -> bool:
        """
        Update configuration for a monitored directory.

        Args:
            dir_path: Path to the directory to update
            **kwargs: Configuration options to update:
                - priority: DirectoryPriority enum value or string name
                - recursive_depth: How deep to scan subdirectories
                - throttle: Seconds to wait between processing in high-activity dirs

        Returns:
            bool: True if update was successful, False otherwise
        """
        path = Path(dir_path).resolve()
        str_path = str(path)

        if str_path not in self.directory_configs:
            logger.warning(f"Cannot update non-registered directory: {path}")
            return False

        # Get current config
        dir_config = self.directory_configs[str_path]

        # Update config values
        if "priority" in kwargs:
            priority = kwargs["priority"]
            if isinstance(priority, str):
                priority = self._parse_priority(priority)
            dir_config.priority = priority

        if "recursive_depth" in kwargs:
            dir_config.recursive_depth = int(kwargs["recursive_depth"])

        if "throttle" in kwargs:
            dir_config.throttle = float(kwargs["throttle"])

        # Restart monitoring with new config if we're already running
        if str_path in self.observers:
            # Stop current observer
            observer = self.observers[str_path]
            if observer.is_alive():
                observer.stop()
                observer.join(timeout=5.0)
                if observer.is_alive():
                    logger.warning(
                        f"Observer for {path} did not terminate gracefully during update"
                    )
            del self.observers[str_path]

            # Start with new config
            self._start_monitoring_directory(str_path, dir_config)

        logger.info(
            f"Updated directory config: {path} (Priority: {dir_config.priority.name}, "
            f"Depth: {dir_config.recursive_depth}, Throttle: {dir_config.throttle}s)"
        )
        return True

    def get_directory_config(self, dir_path: str | Path) -> DirectoryConfig | None:
        """
        Get configuration for a monitored directory.

        Args:
            dir_path: Path to the directory

        Returns:
            DirectoryConfig or None: Configuration for the directory, or None if not registered
        """
        path = Path(dir_path).resolve()
        str_path = str(path)
        return self.directory_configs.get(str_path)

    def get_all_directories(self) -> dict[str, DirectoryConfig]:
        """
        Get all monitored directories and their configurations.

        Returns:
            dict: Dictionary mapping directory paths to their configurations
        """
        return self.directory_configs.copy()

    def _load_directories_from_config(self):
        """Load directories from configuration."""
        dirs_config = config.get("file_manager.monitored_directories", [])
        if not dirs_config:
            logger.info("No directories configured for monitoring")
            return

        for dir_config in dirs_config:
            if not isinstance(dir_config, dict) or "path" not in dir_config:
                logger.warning(f"Invalid directory configuration: {dir_config}")
                continue

            path = dir_config["path"]
            kwargs = {}

            if "priority" in dir_config:
                kwargs["priority"] = dir_config["priority"]

            if "recursive_depth" in dir_config:
                kwargs["recursive_depth"] = int(dir_config["recursive_depth"])

            if "throttle" in dir_config:
                kwargs["throttle"] = float(dir_config["throttle"])

            try:
                self.register_directory(path, **kwargs)
            except Exception as e:
                logger.error(f"Error registering directory {path}: {e}")

    def _start_monitoring_directory(self, dir_path: str, dir_config: DirectoryConfig):
        """
        Start monitoring a directory.

        Args:
            dir_path: String path to the directory
            dir_config: Configuration for the directory
        """
        # Import here to avoid circular import
        from backend.src.file_manager.file_watcher import FileEventHandler

        if dir_path in self.observers and self.observers[dir_path].is_alive():
            logger.warning(f"Directory already being monitored: {dir_path}")
            return

        try:
            # Create observer and event handler
            observer = Observer()
            event_handler = FileEventHandler(dir_config.path)

            # Schedule the observer
            if dir_config.recursive_depth > 0:
                # Handle limited-depth recursion
                self._handle_limited_depth_recursion(
                    dir_config.path,
                    dir_config.recursive_depth,
                    event_handler,
                    observer,
                )
            else:
                # Non-recursive monitoring
                observer.schedule(event_handler, dir_path, recursive=False)

            # Start the observer
            observer.start()
            self.observers[dir_path] = observer

            logger.info(
                f"Started monitoring directory: {dir_path} "
                f"(Priority: {dir_config.priority.name}, Depth: {dir_config.recursive_depth})"
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
        Handle limited-depth recursion for directory monitoring.

        Args:
            base_path: Base directory path
            max_depth: Maximum recursion depth
            event_handler: Event handler to use
            observer: Observer to schedule
        """
        # Schedule the base directory
        observer.schedule(event_handler, str(base_path), recursive=False)

        # Collect subdirectories up to max_depth
        subdirs = []

        def collect_subdirs(path, current_depth=1):
            if current_depth > max_depth:
                return

            try:
                for item in path.iterdir():
                    if item.is_dir():
                        subdirs.append(item)
                        collect_subdirs(item, current_depth + 1)
            except PermissionError:
                logger.warning(f"Permission denied accessing directory: {path}")
            except Exception as e:
                logger.error(f"Error scanning directory {path}: {e}")

        # Collect subdirectories
        collect_subdirs(base_path)

        # Schedule each subdirectory non-recursively
        for subdir in subdirs:
            try:
                observer.schedule(event_handler, str(subdir), recursive=False)
            except Exception as e:
                logger.error(f"Error scheduling observer for {subdir}: {e}")

    def _start_directory_discovery(self):
        """Start the directory discovery thread."""
        if self.discovery_thread and self.discovery_thread.is_alive():
            logger.warning("Directory discovery already running")
            return

        self.discovery_running = True
        self.discovery_thread = threading.Thread(
            target=self._directory_discovery_loop,
            daemon=True,
            name="DirectoryDiscoveryThread",
        )
        self.discovery_thread.start()
        logger.info("Started directory discovery thread")

    def _directory_discovery_loop(self):
        """Run the directory discovery loop."""
        while self.discovery_running:
            try:
                self._discover_new_directories()
            except Exception as e:
                logger.error(f"Error in directory discovery: {e}")

            # Sleep for the discovery interval
            for _ in range(int(self.discovery_interval)):
                if not self.discovery_running:
                    break
                threading.Event().wait(1)

    def _discover_new_directories(self):
        """Discover new directories to monitor."""
        with self.discovery_lock:
            # Get base directories to scan
            base_dirs = config.get("file_manager.discovery_base_directories", [])
            if not base_dirs:
                return

            # Get discovery depth
            max_depth = config.get("file_manager.discovery_max_depth", 3)

            # Get patterns to include/exclude
            include_patterns = config.get("file_manager.discovery_include_patterns", [])
            exclude_patterns = config.get("file_manager.discovery_exclude_patterns", [])

            # Scan directories
            new_dirs = set()

            def scan_dir(path, current_depth=1):
                if current_depth > max_depth:
                    return

                try:
                    for item in Path(path).iterdir():
                        if not item.is_dir():
                            continue

                        # Check if this directory should be included
                        dir_name = item.name.lower()
                        if include_patterns and not any(
                            pattern.lower() in dir_name for pattern in include_patterns
                        ):
                            continue

                        # Check if this directory should be excluded
                        if any(
                            pattern.lower() in dir_name for pattern in exclude_patterns
                        ):
                            continue

                        # Add to new directories
                        new_dirs.add(item)

                        # Scan subdirectories
                        scan_dir(item, current_depth + 1)
                except Exception as e:
                    logger.error(f"Error scanning directory {path}: {e}")

            # Scan all base directories
            for base_dir in base_dirs:
                try:
                    base_path = Path(base_dir)
                    if base_path.exists() and base_path.is_dir():
                        scan_dir(base_path)
                except Exception as e:
                    logger.error(f"Error scanning base directory {base_dir}: {e}")

            # Register new directories
            for new_dir in new_dirs:
                str_path = str(new_dir)
                if str_path not in self.directory_configs:
                    self.register_directory(new_dir)

    def _parse_priority(self, priority_str: str) -> DirectoryPriority:
        """
        Parse a priority string into a DirectoryPriority enum value.

        Args:
            priority_str: Priority string (case-insensitive)

        Returns:
            DirectoryPriority: Corresponding enum value
        """
        priority_map = {
            "critical": DirectoryPriority.CRITICAL,
            "high": DirectoryPriority.HIGH,
            "normal": DirectoryPriority.NORMAL,
            "low": DirectoryPriority.LOW,
        }

        priority_str = priority_str.lower()
        if priority_str in priority_map:
            return priority_map[priority_str]
        else:
            logger.warning(f"Unknown priority: {priority_str}, defaulting to NORMAL")
            return DirectoryPriority.NORMAL


# Create a singleton instance
directory_monitor = DirectoryMonitor()
