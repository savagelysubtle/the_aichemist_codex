# FILE: src/the_aichemist_codex/domain/services/interfaces/tag_classifier.py
"""
Interface for Tag Classifier Service.

Defines the contract for services that automatically classify and suggest tags
for files based on their content and metadata.
"""

from typing import Any, Protocol

from the_aichemist_codex.domain.value_objects import FileDataForTagging


class TagClassifierInterface(Protocol):
    """Interface for services that classify files and suggest tags."""

    async def load_model(self: "TagClassifierInterface") -> bool:
        """Load a trained classification model."""
        ...

    async def classify(
        self: "TagClassifierInterface",
        tagging_data: FileDataForTagging,
        confidence_threshold: float = 0.6,
    ) -> list[tuple[str, float]]:
        """
        Classify a file and suggest tags with confidence scores.

        Args:
            tagging_data: Value object containing file data for tagging.
            confidence_threshold: Minimum confidence threshold for suggestions.

        Returns:
            List of (tag_name, confidence) tuples.
        """
        ...

    async def train(
        self: "TagClassifierInterface",
        training_data: list[tuple[FileDataForTagging, list[str]]],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """Train the classifier with labeled examples."""
        ...

    async def get_model_info(self: "TagClassifierInterface") -> dict[str, Any]:
        """Get information about the current model."""
        ...
