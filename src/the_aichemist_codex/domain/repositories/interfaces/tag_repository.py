# FILE: src/the_aichemist_codex/domain/repositories/interfaces/tag_repository.py
"""
Interface for Tag Repository.

Defines the contract for storing, retrieving, and managing Tags
and their associations with files.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass
class Tag:
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None


@dataclass
class FileTagAssociation:
    file_path: Path
    tag_id: int
    source: str
    confidence: float
    added_at: datetime | None = None


class TagRepositoryInterface(Protocol):
    """Interface for managing the persistence of Tags and FileTags."""

    async def initialize(self) -> None:
        """Initialize the repository (e.g., create tables)."""
        ...

    # Tag CRUD
    async def create_tag(self, name: str, description: str = "") -> Tag:
        """Create a new tag or return existing one."""
        ...

    async def get_tag(self, tag_id: int) -> Tag | None:
        """Get a tag by ID."""
        ...

    async def get_tag_by_name(self, name: str) -> Tag | None:
        """Get a tag by name (case insensitive)."""
        ...

    async def update_tag(
        self, tag_id: int, name: str | None = None, description: str | None = None
    ) -> bool:
        """Update a tag's name or description."""
        ...

    async def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag and its associations."""
        ...

    async def get_all_tags(self) -> list[Tag]:
        """Get all tags."""
        ...

    # File Tag Association Management
    async def add_file_tag(
        self,
        file_path: Path,
        tag_id: int,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> bool:
        """Add a tag association to a file."""
        ...

    async def add_file_tags_batch(self, file_tags: list[FileTagAssociation]) -> int:
        """Add multiple file-tag associations efficiently."""
        ...

    async def remove_file_tag(self, file_path: Path, tag_id: int) -> bool:
        """Remove a specific tag association from a file."""
        ...

    async def remove_all_tags_for_file(self, file_path: Path) -> int:
        """Remove all tag associations for a specific file."""
        ...

    async def get_tags_for_file(self, file_path: Path) -> list[FileTagAssociation]:
        """Get all tag associations for a specific file."""
        ...

    # Querying
    async def get_files_by_tag_id(self, tag_id: int) -> list[Path]:
        """Get all files associated with a specific tag ID."""
        ...

    async def get_files_by_tag_name(self, tag_name: str) -> list[Path]:
        """Get all files associated with a specific tag name."""
        ...

    async def get_files_by_tags(
        self, tag_ids: list[int], require_all: bool = False
    ) -> list[Path]:
        """Get files associated with multiple tags."""
        ...

    async def get_tag_counts(self) -> list[dict[str, Any]]:
        """Get all tags with their usage counts."""
        ...

    # Maintenance
    async def remove_tags_for_nonexistent_files(self) -> int:
        """Remove associations for files that no longer exist."""
        ...

    async def remove_orphaned_tags(self) -> int:
        """Remove tags that are not associated with any files."""
        ...
