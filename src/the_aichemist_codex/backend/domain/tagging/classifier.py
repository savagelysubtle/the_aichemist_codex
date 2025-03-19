"""
Tag classification module for automatic file tagging.

This module provides the TagClassifier class, which is responsible for
training and applying machine learning models to automatically tag files
based on their content and metadata.
"""

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class TagClassifier:
    """
    Machine learning classifier for automatic file tagging.

    This class provides methods for training and applying machine learning
    models to automatically tag files based on their content and metadata.

    Note: This is a simplified implementation that stores basic classification
    rules. A full implementation would integrate with scikit-learn or another
    ML library for more sophisticated classification.
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, model_dir: Path):
        """
        Initialize the TagClassifier with a model directory.

        Args:
            model_dir: Directory to store model files
        """
        self.model_dir = model_dir
        self.model_path = self.model_dir / "tag_classifier.pkl"
        self.metadata_path = self.model_dir / "tag_classifier_metadata.json"

        # Internal state
        self.tag_names: list[str] = []
        self.feature_names: np.ndarray | None = None
        self.training_metadata: dict[str, Any] = {}

        # Simple rule-based model (dict of patterns -> tags)
        self.rules: dict[str, list[tuple[str, float]]] = {}

    async def initialize(self) -> None:
        """
        Initialize the classifier, loading any existing model.

        Returns:
            None
        """
        # Ensure model directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Try to load existing model
        success = await self.load_model()
        if not success:
            logger.info("No existing model found, using default empty model")
            self._initialize_default_model()

    def _initialize_default_model(self) -> None:
        """Initialize the default model with basic rules."""
        self.rules = {
            # File extension patterns
            "*.py": [("python", 0.95), ("code", 0.9), ("script", 0.8)],
            "*.js": [("javascript", 0.95), ("code", 0.9), ("web", 0.7)],
            "*.html": [("html", 0.95), ("web", 0.9), ("markup", 0.8)],
            "*.css": [("css", 0.95), ("web", 0.9), ("style", 0.8)],
            "*.md": [("markdown", 0.95), ("documentation", 0.9), ("text", 0.8)],
            "*.json": [("json", 0.95), ("data", 0.9), ("config", 0.7)],
            "*.txt": [("text", 0.95), ("document", 0.7)],
            "*.pdf": [("pdf", 0.95), ("document", 0.9), ("reading", 0.7)],
            "*.jpg": [("image", 0.95), ("jpg", 0.9), ("photo", 0.8)],
            "*.png": [("image", 0.95), ("png", 0.9), ("graphic", 0.8)],

            # Content patterns (would be extracted from file content)
            "import": [("code", 0.8), ("dependency", 0.7)],
            "def": [("function", 0.8), ("python", 0.7)],
            "class": [("class", 0.8), ("object-oriented", 0.7)],
            "SELECT": [("sql", 0.8), ("database", 0.7), ("query", 0.7)],
            "function": [("function", 0.8), ("javascript", 0.6)],
            "<html>": [("html", 0.9), ("web", 0.8)],
            "<div>": [("html", 0.8), ("web", 0.7)],
        }

        # Extract unique tag names
        self.tag_names = sorted(set(tag for patterns in self.rules.values()
                               for tag, _ in patterns))

        # Set metadata
        self.training_metadata = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "num_patterns": len(self.rules),
            "num_tags": len(self.tag_names),
            "type": "rule-based",
        }

    async def load_model(self) -> bool:
        """
        Load a trained model from disk.

        Returns:
            bool: True if a model was loaded, False otherwise
        """
        try:
            # Check if model file exists
            if not self.model_path.exists():
                logger.info("No trained model found, using default model")
                return False

            # Load the model
            with open(self.model_path, "rb") as f:
                model_data = pickle.load(f)
                self.rules = model_data.get("rules", {})
                self.tag_names = model_data.get("tag_names", [])
                self.feature_names = model_data.get("feature_names")

            # Load metadata if it exists
            if self.metadata_path.exists():
                with open(self.metadata_path) as f:
                    self.training_metadata = json.load(f)

            logger.info(
                f"Loaded classifier model with {len(self.rules)} rules and "
                f"{len(self.tag_names)} tags"
            )
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    async def save_model(self) -> bool:
        """
        Save the current model to disk.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure model directory exists
            self.model_dir.mkdir(parents=True, exist_ok=True)

            # Update metadata
            self.training_metadata["updated_at"] = datetime.now().isoformat()
            self.training_metadata["num_patterns"] = len(self.rules)
            self.training_metadata["num_tags"] = len(self.tag_names)

            # Save the model
            with open(self.model_path, "wb") as f:
                pickle.dump(
                    {
                        "rules": self.rules,
                        "tag_names": self.tag_names,
                        "feature_names": self.feature_names,
                    },
                    f,
                )

            # Save metadata
            with open(self.metadata_path, "w") as f:
                json.dump(self.training_metadata, f, indent=2)

            logger.info(f"Saved classifier model to {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    async def add_rule(self, pattern: str, tags: list[tuple[str, float]]) -> bool:
        """
        Add a rule to the classifier.

        Args:
            pattern: String pattern to match
            tags: List of (tag_name, confidence) tuples

        Returns:
            bool: True if successful
        """
        try:
            self.rules[pattern] = tags

            # Update tag names
            new_tags = set(tag for tag, _ in tags)
            self.tag_names = sorted(set(self.tag_names) | new_tags)

            # Save the updated model
            await self.save_model()
            return True
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            return False

    async def remove_rule(self, pattern: str) -> bool:
        """
        Remove a rule from the classifier.

        Args:
            pattern: Pattern to remove

        Returns:
            bool: True if removed, False if not found
        """
        if pattern in self.rules:
            del self.rules[pattern]
            await self.save_model()
            return True
        return False

    async def classify_file(
        self, file_metadata: dict[str, Any], threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> list[tuple[str, float]]:
        """
        Classify a file and return predicted tags.

        Args:
            file_metadata: Dictionary with file metadata including 'path', 'content', etc.
            threshold: Minimum confidence threshold for tags

        Returns:
            List of (tag_name, confidence) tuples
        """
        try:
            if not file_metadata:
                return []

            # Initialize tag scores
            tag_scores: dict[str, float] = {}

            # Apply file extension rules
            file_path = file_metadata.get("path", "")
            if file_path:
                path = Path(file_path)
                extension = f"*.{path.suffix.lstrip('.')}" if path.suffix else ""

                if extension and extension in self.rules:
                    for tag, score in self.rules[extension]:
                        tag_scores[tag] = max(tag_scores.get(tag, 0), score)

            # Apply content-based rules if we have content
            content = file_metadata.get("content", "")
            if content and isinstance(content, str):
                # For each rule pattern, check if it's in the content
                for pattern, tags in self.rules.items():
                    # Skip extension patterns
                    if pattern.startswith("*."):
                        continue

                    if pattern in content:
                        for tag, score in tags:
                            # Take the max score if the tag is already there
                            tag_scores[tag] = max(tag_scores.get(tag, 0), score)

            # Convert scores to list of tuples and filter by threshold
            results = [
                (tag, score)
                for tag, score in tag_scores.items()
                if score >= threshold
            ]

            # Sort by confidence score descending
            results.sort(key=lambda x: x[1], reverse=True)

            return results

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return []