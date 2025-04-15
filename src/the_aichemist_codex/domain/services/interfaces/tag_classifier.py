# FILE: src/the_aichemist_codex/domain/services/interfaces/tag_classifier.py
"""
Interface for Tag Classifier Service.

Defines the contract for services that automatically classify and suggest tags
for files based on their content and metadata.
"""

from typing import Any, Protocol

# Assume FileMetadata is defined appropriately in the domain or a shared kernel
from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata


class TagClassifierInterface(Protocol):
    """Interface for services that classify files and suggest tags."""

    async def load_model(self) -> bool:
        """Load a trained classification model."""
        ...

    async def classify(
        self,
        file_metadata: FileMetadata,
        confidence_threshold: float = 0.6,
    ) -> list[tuple[str, float]]:
        """
        Classify a file and suggest tags with confidence scores.

        Args:
            file_metadata: FileMetadata object.
            confidence_threshold: Minimum confidence threshold for suggestions.

        Returns:
            List of (tag_name, confidence) tuples.
        """
        ...

    async def train(
        self,
        training_data: list[tuple[FileMetadata, list[str]]],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """Train the classifier with labeled examples."""
        ...

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        ...
