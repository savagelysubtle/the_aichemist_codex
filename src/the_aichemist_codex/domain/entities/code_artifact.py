"""Code artifact entity for the AIchemist Codex domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from the_aichemist_codex.domain.exceptions.validation_exception import (
    ValidationException,
)


@dataclass
class CodeArtifact:
    """A code artifact entity that represents a file, module, class, or function.

    Attributes:
        id: The unique identifier of the artifact
        path: The file system path to the artifact
        name: The name of the artifact
        artifact_type: The type of artifact (file, module, class, function, etc.)
        content: The textual content of the artifact
        metadata: Additional metadata about the artifact
        is_valid: Whether the artifact is valid
    """

    path: Path
    name: str
    artifact_type: str = "file"
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    is_valid: bool = True

    def __post_init__(self) -> None:
        """Validate the entity after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the entity.

        Raises:
            ValidationException: If validation fails
        """
        errors = {}

        if self.path is None:
            errors["path"] = "path is required"

        if not self.name:
            errors["name"] = "name cannot be empty"

        if errors:
            self.is_valid = False
            raise ValidationException("Code artifact validation failed", errors)

    def __eq__(self, other: Any) -> bool:
        """Compare two code artifacts for equality.

        Args:
            other: Another object to compare with

        Returns:
            True if the objects are equal, False otherwise
        """
        if not isinstance(other, CodeArtifact):
            return False
        return self.id == other.id

    def __str__(self) -> str:
        """Return a string representation of the artifact.

        Returns:
            A string containing the artifact ID and name
        """
        return f"CodeArtifact(id={self.id}, name={self.name})"

    def update_metadata(self, new_metadata: dict[str, Any]) -> None:
        """Update the metadata with new values.

        Args:
            new_metadata: New metadata to add or update
        """
        self.metadata.update(new_metadata)

    def get_snippet(self, start_line: int, end_line: int) -> str:
        """Get a snippet of the content based on line numbers.

        Args:
            start_line: The starting line number (1-indexed)
            end_line: The ending line number (1-indexed, inclusive)

        Returns:
            The snippet of content

        Raises:
            ValueError: If the line numbers are invalid
        """
        if not self.content:
            raise ValueError("No content available")

        lines = self.content.split("\n")

        if start_line < 1:
            raise ValueError("start_line must be at least 1")

        if end_line > len(lines):
            raise ValueError("end_line exceeds content length")

        if start_line > end_line:
            raise ValueError("start_line cannot be greater than end_line")

        # Adjust for 0-indexed list
        return "\n".join(lines[start_line - 1 : end_line])

    def parse_content(self, content: str) -> None:
        """Parse the content and extract metadata.

        Args:
            content: The content to parse
        """
        self.content = content

        # Simple metadata extraction (this would be more complex in a real implementation)
        line_count = content.count("\n") + 1
        char_count = len(content)

        self.update_metadata(
            {"parsed": True, "loc": line_count, "char_count": char_count}
        )
