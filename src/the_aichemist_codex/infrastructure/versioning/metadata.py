"""Version metadata tracking for The Aichemist Codex.

This module defines the data structures and utilities for tracking version metadata,
including version IDs, timestamps, authors, and change descriptions.
"""

import datetime
import hashlib
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class VersionType(Enum):
    """Types of versions that can be created."""

    AUTOMATIC = "automatic"  # Created automatically by the system
    MANUAL = "manual"  # Created manually by the user
    SCHEDULED = "scheduled"  # Created by scheduled job
    SYSTEM = "system"  # Created by system operations
    ROLLBACK = "rollback"  # Created during a rollback operation


@dataclass
class VersionMetadata:
    """Metadata for a version of a file."""

    # Core identification
    version_id: str  # Unique identifier for this version
    file_path: Path  # Path to the original file
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    # Version details
    version_type: VersionType = VersionType.AUTOMATIC
    parent_version_id: str | None = None  # Previous version

    # Change information
    author: str = ""
    change_description: str = ""
    change_size_bytes: int = 0
    change_percentage: float = 0.0

    # Additional metadata
    tags: list[str] = field(default_factory=list)
    annotations: dict[str, Any] = field(default_factory=dict)

    # Storage details
    storage_path: Path | None = None  # Where this version is stored
    is_full_snapshot: bool = True  # If False, stored as diff from parent

    @classmethod
    def generate_version_id(
        cls, file_path: Path, timestamp: datetime.datetime | None = None
    ) -> str:
        """Generate a unique version ID based on file path and timestamp."""
        if timestamp is None:
            timestamp = datetime.datetime.now()

        # Combine file path, timestamp, and a random component
        timestamp_str = timestamp.isoformat()
        random_component = str(uuid.uuid4())[:8]

        # Create a hash from the combined data
        hash_input = f"{file_path}:{timestamp_str}:{random_component}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to a dictionary for storage."""
        result = asdict(self)

        # Convert Path objects to strings
        result["file_path"] = str(self.file_path)
        if self.storage_path:
            result["storage_path"] = str(self.storage_path)

        # Convert Enum to string
        result["version_type"] = self.version_type.value

        # Convert datetime to ISO format
        result["timestamp"] = self.timestamp.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionMetadata":
        """Create metadata from a dictionary."""
        # Copy the dictionary to avoid modifying the original
        data_copy = data.copy()

        # Convert string paths back to Path objects
        data_copy["file_path"] = Path(data_copy["file_path"])
        if data_copy.get("storage_path"):
            data_copy["storage_path"] = Path(data_copy["storage_path"])

        # Convert string version type back to enum
        data_copy["version_type"] = VersionType(data_copy["version_type"])

        # Convert ISO timestamp back to datetime
        data_copy["timestamp"] = datetime.datetime.fromisoformat(data_copy["timestamp"])

        return cls(**data_copy)

    def __str__(self) -> str:
        """Human-readable representation of version metadata."""
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"Version {self.version_id} of {self.file_path.name} "
            f"({time_str}, {self.version_type.value})"
        )


@dataclass
class VersionGraph:
    """Represents the version history graph for a file."""

    file_path: Path
    versions: dict[str, VersionMetadata] = field(default_factory=dict)
    branches: dict[str, list[str]] = field(default_factory=dict)

    def add_version(self, metadata: VersionMetadata) -> None:
        """Add a version to the graph."""
        self.versions[metadata.version_id] = metadata

        # Update branch information
        branch_name = "main"  # Default branch
        if metadata.parent_version_id:
            # Find which branch the parent is on
            for br_name, version_ids in self.branches.items():
                if metadata.parent_version_id in version_ids:
                    branch_name = br_name
                    break

        # Add this version to the appropriate branch
        if branch_name not in self.branches:
            self.branches[branch_name] = []
        self.branches[branch_name].append(metadata.version_id)

    def get_latest_version(self, branch: str = "main") -> VersionMetadata | None:
        """Get the latest version on the specified branch."""
        if branch not in self.branches or not self.branches[branch]:
            return None

        latest_version_id = self.branches[branch][-1]
        return self.versions.get(latest_version_id)

    def get_version_chain(self, version_id: str) -> list[VersionMetadata]:
        """Get the chain of versions leading to the specified version."""
        if version_id not in self.versions:
            return []

        result = []
        current_id = version_id

        # Follow the parent chain
        while current_id:
            if current_id not in self.versions:
                break

            current_version = self.versions[current_id]
            result.append(current_version)
            current_id = current_version.parent_version_id

        # Reverse to get chronological order
        return list(reversed(result))

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to a dictionary for storage."""
        return {
            "file_path": str(self.file_path),
            "versions": {k: v.to_dict() for k, v in self.versions.items()},
            "branches": self.branches,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionGraph":
        """Create graph from a dictionary."""
        graph = cls(Path(data["file_path"]))
        graph.branches = data["branches"]

        for version_id, version_data in data["versions"].items():
            graph.versions[version_id] = VersionMetadata.from_dict(version_data)

        return graph


@dataclass
class RollbackResult:
    """Result of a rollback operation."""

    success: bool
    file_path: Path
    target_version_id: str
    current_version_id: str | None = None
    error_message: str = ""
    affected_files: list[Path] = field(default_factory=list)
    created_backup: Path | None = None
