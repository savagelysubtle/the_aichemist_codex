"""
File versioning system for The Aichemist Codex.

This module provides functionality to manage file versions, including
storing, comparing, and restoring different versions of files.
"""

import asyncio
import difflib
import hashlib
import json
import logging
import os
import threading
import time
from enum import Enum
from pathlib import Path

from the_aichemist_codex.backend.config.loader.config_loader import config
from the_aichemist_codex.backend.file_manager.change_detector import ChangeDetector
from the_aichemist_codex.backend.rollback.rollback_manager import RollbackManager
from the_aichemist_codex.backend.utils.io.async_io import AsyncFileIO
from the_aichemist_codex.backend.utils.common.safety import SafeFileHandler

logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    """
    Get the data directory path dynamically to avoid circular imports.

    Returns:
        Path: The data directory path
    """
    # Check for environment variable first
    env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir).resolve()

    # Fallback to a relative path from the current file
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    return project_root / "data"


# Define default version storage location
VERSION_STORAGE_DIR = get_data_dir() / "versions"
VERSION_METADATA_DB = get_data_dir() / "version_metadata.json"

# Make sure version directories exist
VERSION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize other managers we'll need
rollback_manager = RollbackManager()


class VersioningPolicy(Enum):
    """Versioning policy options for different file types."""

    FULL_COPY = 1  # Store complete file copy for each version
    DIFF_BASED = 2  # Store only differences between versions for text files
    HYBRID = 3  # Use diff for text files, full copies for binary files


class VersionMetadata:
    """Metadata for a single file version."""

    def __init__(
        self,
        file_path: str,
        version_id: str,
        timestamp: float,
        policy: VersioningPolicy,
        storage_path: str,
        is_diff: bool = False,
        parent_version_id: str | None = None,
        author: str | None = None,
        change_reason: str | None = None,
        file_hash: str | None = None,
    ):
        """
        Initialize version metadata.

        Args:
            file_path: Path to the original file
            version_id: Unique identifier for this version
            timestamp: When the version was created
            policy: Versioning policy used for this version
            storage_path: Where this version is stored
            is_diff: Whether this is a diff or full file
            parent_version_id: ID of the parent version (for diffs)
            author: Who created this version
            change_reason: Why this version was created
            file_hash: Hash of the file content
        """
        self.file_path = file_path
        self.version_id = version_id
        self.timestamp = timestamp
        self.policy = policy
        self.storage_path = storage_path
        self.is_diff = is_diff
        self.parent_version_id = parent_version_id
        self.author = author
        self.change_reason = change_reason
        self.file_hash = file_hash

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "version_id": self.version_id,
            "timestamp": self.timestamp,
            "policy": self.policy.name,
            "storage_path": self.storage_path,
            "is_diff": self.is_diff,
            "parent_version_id": self.parent_version_id,
            "author": self.author,
            "change_reason": self.change_reason,
            "file_hash": self.file_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionMetadata":
        """Create from dictionary (for deserialization)."""
        # Convert string policy back to enum
        policy_str = data.get("policy", "HYBRID")
        try:
            policy = VersioningPolicy[policy_str]
        except (KeyError, TypeError):
            policy = VersioningPolicy.HYBRID

        return cls(
            file_path=data["file_path"],
            version_id=data["version_id"],
            timestamp=data["timestamp"],
            policy=policy,
            storage_path=data["storage_path"],
            is_diff=data.get("is_diff", False),
            parent_version_id=data.get("parent_version_id"),
            author=data.get("author"),
            change_reason=data.get("change_reason"),
            file_hash=data.get("file_hash"),
        )


class VersionManager:
    """
    Manages file versioning operations.

    Features:
    - Controls the versioning strategy based on file type and configuration
    - Maintains version history with metadata
    - Provides version comparison and restoration capabilities
    - Optimizes storage of versions with different strategies
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Ensure VersionManager is a singleton."""
        if cls._instance is None:
            cls._instance = super(VersionManager, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        storage_dir: Path = VERSION_STORAGE_DIR,
        metadata_path: Path = VERSION_METADATA_DB,
    ):
        """
        Initialize the version manager.

        Args:
            storage_dir: Directory to store version files
            metadata_path: Path to store version metadata
        """
        # Only initialize once due to singleton pattern
        if self._initialized:
            return

        self.storage_dir = storage_dir
        self.metadata_path = metadata_path
        self.version_metadata = {}
        self.change_detector = ChangeDetector()

        # Load existing metadata if it exists
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path) as f:
                    self.version_metadata = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Error loading version metadata: {e}")
                # Create backup of corrupted file
                if self.metadata_path.exists():
                    backup_path = self.metadata_path.with_suffix(
                        f".backup_{int(time.time())}"
                    )
                    self.metadata_path.rename(backup_path)
                    logger.info(f"Created backup of version metadata at {backup_path}")
                # Start with empty metadata
                self.version_metadata = {}

        # Get configuration
        self.default_policy = self._get_default_policy()
        self.max_versions_per_file = config.get("versioning", {}).get(
            "max_versions_per_file", 20
        )

        # Mark as initialized
        self._initialized = True
        logger.info(f"VersionManager initialized with storage at {self.storage_dir}")

    def _get_default_policy(self) -> VersioningPolicy:
        """Get the default versioning policy from configuration."""
        policy_str = (
            config.get("versioning", {}).get("default_policy", "hybrid").upper()
        )
        try:
            return VersioningPolicy[policy_str]
        except KeyError:
            logger.warning(f"Invalid versioning policy {policy_str}, using HYBRID")
            return VersioningPolicy.HYBRID

    async def create_version(
        self,
        file_path: Path,
        change_reason: str | None = None,
        author: str | None = None,
        policy: VersioningPolicy | None = None,
    ) -> str | None:
        """
        Create a new version of a file.

        Args:
            file_path: Path to the file to version
            change_reason: Reason for creating this version
            author: Who is creating the version
            policy: Specific policy to use (overrides default)

        Returns:
            Version ID if successful, None otherwise
        """
        file_path = Path(file_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            logger.error(
                f"Cannot create version: File {file_path} does not exist or is not a file"
            )
            return None

        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping versioning for ignored file: {file_path}")
            return None

        # Use provided policy or default
        policy = policy or self.default_policy

        # Generate unique version ID
        timestamp = time.time()
        version_id = (
            f"{hashlib.md5(str(file_path).encode()).hexdigest()}_{int(timestamp)}"
        )

        # Determine if this is a text file for hybrid policy
        is_text_file = await self._is_text_file(file_path)

        # Determine whether to use diff-based versioning
        use_diff = False
        parent_version_id = None

        if policy == VersioningPolicy.DIFF_BASED or (
            policy == VersioningPolicy.HYBRID and is_text_file
        ):
            # Find the most recent version to diff against
            versions = self._get_file_versions(file_path)
            if versions:
                latest_version = versions[0]  # Versions are ordered newest to oldest
                parent_version_id = latest_version.version_id
                use_diff = True

        # Create the storage path
        file_dir = self.storage_dir / str(
            hash(str(file_path)) % 100
        )  # Shard by hash to avoid too many files in one dir
        file_dir.mkdir(parents=True, exist_ok=True)

        storage_path = file_dir / f"{version_id}"
        if use_diff:
            storage_path = storage_path.with_suffix(".diff")

        # Create the version
        try:
            if use_diff and parent_version_id is not None:
                # Generate diff against parent version
                diff_content = await self._generate_diff(file_path, parent_version_id)
                success = await AsyncFileIO.write(storage_path, diff_content)
                if not success:
                    raise OSError(f"Failed to write diff to {storage_path}")
            else:
                # Full copy
                success = await AsyncFileIO.copy(file_path, storage_path)
                if not success:
                    raise OSError(f"Failed to copy file to {storage_path}")

            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)

            # Create and store metadata
            metadata = VersionMetadata(
                file_path=str(file_path),
                version_id=version_id,
                timestamp=timestamp,
                policy=policy,
                storage_path=str(storage_path),
                is_diff=use_diff,
                parent_version_id=parent_version_id,
                author=author,
                change_reason=change_reason,
                file_hash=file_hash,
            )

            # Add to metadata storage
            if str(file_path) not in self.version_metadata:
                self.version_metadata[str(file_path)] = []

            self.version_metadata[str(file_path)].insert(0, metadata.to_dict())

            # Limit the number of versions per file
            self._prune_old_versions(file_path)

            # Save metadata
            await self._save_metadata()

            logger.info(f"Created version {version_id} for {file_path}")
            return version_id

        except Exception as e:
            logger.error(f"Error creating version for {file_path}: {e}")
            # Clean up if necessary
            if storage_path.exists():
                storage_path.unlink()
            return None

    async def _save_metadata(self) -> bool:
        """Save version metadata to the metadata file."""
        try:
            # Write to a temporary file first to prevent corruption
            temp_path = self.metadata_path.with_suffix(".tmp")
            success = await AsyncFileIO.write_json(temp_path, self.version_metadata)
            if not success:
                logger.error(f"Failed to write metadata to {temp_path}")
                return False

            # Replace the original file
            if temp_path.exists():
                # On Windows, we need to remove the target file first
                if os.name == "nt" and self.metadata_path.exists():
                    self.metadata_path.unlink()
                temp_path.rename(self.metadata_path)
                return True
            return False

        except Exception as e:
            logger.error(f"Error saving version metadata: {e}")
            return False

    def _get_file_versions(self, file_path: Path) -> list[VersionMetadata]:
        """Get all versions for a file, ordered newest first."""
        file_path_str = str(file_path.resolve())
        versions_data = self.version_metadata.get(file_path_str, [])
        return [VersionMetadata.from_dict(v) for v in versions_data]

    def _prune_old_versions(self, file_path: Path) -> None:
        """Limit the number of versions stored for a file."""
        file_path_str = str(file_path.resolve())
        versions = self.version_metadata.get(file_path_str, [])

        if len(versions) <= self.max_versions_per_file:
            return

        # Keep the newest max_versions_per_file
        to_remove = versions[self.max_versions_per_file :]
        self.version_metadata[file_path_str] = versions[: self.max_versions_per_file]

        # Delete the old version files
        for version_data in to_remove:
            try:
                storage_path = Path(version_data["storage_path"])
                if storage_path.exists():
                    storage_path.unlink()
                logger.debug(f"Removed old version {version_data['version_id']}")
            except Exception as e:
                logger.error(
                    f"Error removing old version {version_data['version_id']}: {e}"
                )

    async def _is_text_file(self, file_path: Path) -> bool:
        """Determine if a file is a text file."""
        # Leverage the ChangeDetector's text file detection
        return await self.change_detector._is_text_file(file_path)

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate a hash of the file contents."""
        return await self.change_detector._calculate_file_hash(file_path)

    async def _generate_diff(self, file_path: Path, parent_version_id: str) -> str:
        """Generate a diff between the current file and a parent version."""
        # Get the parent version content
        parent_content = await self.get_version_content(parent_version_id)
        if parent_content is None:
            raise ValueError(
                f"Could not get content for parent version {parent_version_id}"
            )

        # Get the current file content
        current_content = await AsyncFileIO.read_text(file_path)

        # Generate the diff
        parent_lines = parent_content.splitlines(keepends=True)
        current_lines = current_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            parent_lines,
            current_lines,
            fromfile=f"{file_path}.{parent_version_id}",
            tofile=f"{file_path}.current",
            n=3,  # Context lines
        )

        return "".join(diff)

    async def get_version_content(self, version_id: str) -> str | None:
        """
        Get the content of a specific version.

        For diff-based versions, this reconstructs the full content
        by applying diffs to the original version.

        Args:
            version_id: ID of the version to retrieve

        Returns:
            Content of the version if available, None otherwise
        """
        # Find the version in metadata
        version_metadata = None
        file_path = None

        for file_versions in self.version_metadata.values():
            for version_data in file_versions:
                if version_data["version_id"] == version_id:
                    version_metadata = VersionMetadata.from_dict(version_data)
                    file_path = version_data["file_path"]
                    break
            if version_metadata:
                break

        if not version_metadata:
            logger.error(f"Version {version_id} not found in metadata")
            return None

        storage_path = Path(version_metadata.storage_path)
        if not storage_path.exists():
            logger.error(f"Version file {storage_path} does not exist")
            return None

        try:
            if not version_metadata.is_diff:
                # For full copies, just return the content
                return await AsyncFileIO.read_text(storage_path)
            else:
                # For diffs, we need to reconstruct by applying the diff chain
                return await self._reconstruct_from_diff_chain(version_metadata)

        except Exception as e:
            logger.error(f"Error retrieving version content: {e}")
            return None

    async def _reconstruct_from_diff_chain(
        self, version_metadata: VersionMetadata
    ) -> str | None:
        """Reconstruct file content by applying a chain of diffs."""
        # Start with this diff
        diffs_to_apply = []
        current_metadata = version_metadata

        # Collect all diffs in the chain
        while current_metadata.is_diff and current_metadata.parent_version_id:
            # Add this diff to the list
            diff_content = await AsyncFileIO.read_text(
                Path(current_metadata.storage_path)
            )
            diffs_to_apply.append(diff_content)

            # Find the parent version
            parent_found = False
            for file_versions in self.version_metadata.values():
                for version_data in file_versions:
                    if version_data["version_id"] == current_metadata.parent_version_id:
                        current_metadata = VersionMetadata.from_dict(version_data)
                        parent_found = True
                        break
                if parent_found:
                    break

            if not parent_found:
                logger.error(
                    f"Missing parent version {current_metadata.parent_version_id} in diff chain"
                )
                return None

        # Now we should have the base version
        if current_metadata.is_diff:
            logger.error("Could not find base version in diff chain")
            return None

        # Start with the base version content
        content = await AsyncFileIO.read_text(Path(current_metadata.storage_path))

        # Apply diffs in reverse order (newest diff first in our collection)
        for diff in reversed(diffs_to_apply):
            content = self._apply_diff(content, diff)

        return content

    def _apply_diff(self, content: str, diff: str) -> str:
        """Apply a unified diff to content."""
        # This is a simplified implementation
        # A full implementation would properly parse and apply unified diffs

        # For now, we'll use the external patch command if available
        # Otherwise, fallback to a simplified approach

        # TODO: Implement a proper unified diff parser and applicator
        # For now, this is a placeholder

        lines = content.splitlines()
        diff_lines = diff.splitlines()

        # Skip the diff header lines
        header_lines = 0
        for line in diff_lines:
            if line.startswith("@@"):
                header_lines += 1
                break
            header_lines += 1

        diff_lines = diff_lines[header_lines:]

        # Apply the changes
        result_lines = []
        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            if line.startswith(" "):
                # Context line - keep as is
                result_lines.append(line[1:])
            elif line.startswith("+"):
                # Added line
                result_lines.append(line[1:])
            elif line.startswith("-"):
                # Removed line - skip it
                pass
            else:
                # Other lines (shouldn't happen in a proper diff)
                result_lines.append(line)
            i += 1

        return "\n".join(result_lines)

    async def restore_version(self, file_path: Path, version_id: str) -> bool:
        """
        Restore a file to a previous version.

        Args:
            file_path: Path to the file to restore
            version_id: ID of the version to restore

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path).resolve()

        # Check if the version exists
        version_content = await self.get_version_content(version_id)
        if version_content is None:
            logger.error(f"Failed to get content for version {version_id}")
            return False

        # Create a new version of the current file before restoring
        # This allows us to undo the restoration if needed
        await self.create_version(
            file_path,
            change_reason="Auto-saved before version restoration",
            author="System",
        )

        # Write the version content to the file
        success = await AsyncFileIO.write(file_path, version_content)
        if not success:
            logger.error(f"Failed to write version content to {file_path}")
            return False

        logger.info(f"Restored {file_path} to version {version_id}")
        return True

    async def list_versions(self, file_path: Path) -> list[VersionMetadata]:
        """
        List all versions of a file.

        Args:
            file_path: Path to the file

        Returns:
            List of version metadata objects, ordered newest first
        """
        file_path = Path(file_path).resolve()
        return self._get_file_versions(file_path)

    async def get_version_info(self, version_id: str) -> VersionMetadata | None:
        """
        Get detailed information about a specific version.

        Args:
            version_id: ID of the version to get info for

        Returns:
            Version metadata if found, None otherwise
        """
        # Search for the version in all files
        for file_versions in self.version_metadata.values():
            for version_data in file_versions:
                if version_data["version_id"] == version_id:
                    return VersionMetadata.from_dict(version_data)

        logger.error(f"Version {version_id} not found")
        return None

    async def cleanup_old_versions(self, days: float | None = None) -> int:
        """
        Clean up versions older than the specified number of days.

        Args:
            days: Number of days to keep versions for (defaults to
                 version_retention_days in config)

        Returns:
            Number of versions removed
        """
        # Get retention period from config if not specified
        retention_days = days
        if retention_days is None:
            retention_days = config.get("versioning", {}).get(
                "version_retention_days", 30
            )

        # Calculate cutoff time
        cutoff_time = time.time() - (retention_days * 86400)  # 86400 seconds per day
        removed_count = 0

        # For each file, remove versions older than the cutoff
        for file_path, versions in list(self.version_metadata.items()):
            kept_versions = []

            for version_data in versions:
                if version_data["timestamp"] >= cutoff_time:
                    kept_versions.append(version_data)
                else:
                    # Remove the version file
                    try:
                        storage_path = Path(version_data["storage_path"])
                        if storage_path.exists():
                            storage_path.unlink()
                            removed_count += 1
                            logger.debug(
                                f"Removed old version {version_data['version_id']}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error removing old version {version_data['version_id']}: {e}"
                        )

            # Update the metadata
            if not kept_versions:
                # Remove the file entry if no versions remain
                del self.version_metadata[file_path]
            else:
                self.version_metadata[file_path] = kept_versions

        # Save the updated metadata
        await self._save_metadata()

        logger.info(f"Cleaned up {removed_count} old versions")
        return removed_count

    async def bulk_restore_versions(
        self, restore_map: dict[str, str]
    ) -> dict[str, bool]:
        """
        Restore multiple files to specific versions at once.

        Args:
            restore_map: Dictionary mapping file paths to version IDs

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}

        for file_path_str, version_id in restore_map.items():
            file_path = Path(file_path_str)
            success = await self.restore_version(file_path, version_id)
            results[file_path_str] = success

        return results


# Create a singleton instance
version_manager = VersionManager()


# Schedule periodic cleanup of old versions
def start_version_cleanup_scheduler():
    """
    Start a background thread to periodically clean up old versions.
    """

    def cleanup_task():
        """Run the cleanup task periodically."""
        while True:
            try:
                # Run cleanup
                asyncio.run(version_manager.cleanup_old_versions())

                # Sleep until next cleanup time
                # Get cleanup interval from config (default: once per day)
                cleanup_interval_hours = config.get("versioning", {}).get(
                    "cleanup_interval_hours", 24
                )
                time.sleep(cleanup_interval_hours * 3600)
            except Exception as e:
                logger.error(f"Error in version cleanup task: {e}")
                # Don't crash the thread, just wait and retry
                time.sleep(3600)  # Wait an hour and try again

    # Start the background thread
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Version cleanup scheduler started")


# Start the cleanup scheduler
start_version_cleanup_scheduler()
