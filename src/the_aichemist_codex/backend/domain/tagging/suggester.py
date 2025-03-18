"""
Tag suggestion system for automated tagging based on file content.

This module provides functionality to suggest tags for files based on
their content, metadata, and similarity to previously tagged files.
"""

import logging
from pathlib import Path
from typing import Any

from .classifier import TagClassifier

logger = logging.getLogger(__name__)


class TagSuggester:
    """
    Suggests tags for files based on multiple strategies.

    This class combines multiple tag suggestion strategies, including
    machine learning classification, collaborative filtering, and
    content analysis, to provide comprehensive tag recommendations.
    """

    def __init__(
        self,
        tagging_manager,  # Circular import prevention
        classifier: TagClassifier | None = None,
        model_dir: Path | None = None,
    ):
        """
        Initialize the tag suggester.

        Args:
            tagging_manager: TaggingManager instance for accessing tag data
            classifier: Optional TagClassifier instance
            model_dir: Optional directory for model storage
        """
        self.tagging_manager = tagging_manager

        # Use default model directory if none provided
        if model_dir is None:
            model_dir = Path.home() / ".aichemist" / "models"

        # Create classifier if not provided
        self.classifier = classifier or TagClassifier(model_dir)

    async def initialize(self) -> None:
        """
        Initialize the tag suggester.

        Returns:
            None
        """
        await self.classifier.initialize()
        logger.info("Initialized TagSuggester")

    async def suggest_tags(
        self,
        file_metadata: dict[str, Any],
        min_confidence: float = 0.6,
        max_suggestions: int = 10,
    ) -> list[tuple[str, float]]:
        """
        Suggest tags for a file using multiple strategies.

        Args:
            file_metadata: Dictionary containing file metadata
            min_confidence: Minimum confidence threshold for suggestions
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        try:
            suggestions = {}  # Dict of tag_name -> score

            # Get suggestions from classifier
            classifier_suggestions = await self._get_classifier_suggestions(
                file_metadata, min_confidence
            )

            # Get collaborative filtering suggestions based on similar files
            if "path" in file_metadata and file_metadata["path"]:
                cf_suggestions = await self._get_collaborative_suggestions(
                    Path(file_metadata["path"]), min_confidence
                )
            else:
                cf_suggestions = []

            # Get content-based suggestions
            content_suggestions = await self._get_content_based_suggestions(
                file_metadata, min_confidence
            )

            # Combine with different weights for each source
            for tag, conf in classifier_suggestions:
                suggestions[tag] = conf * 1.0  # Full weight for ML classifier

            for tag, conf in cf_suggestions:
                if tag in suggestions:
                    # Take max confidence if already suggested
                    suggestions[tag] = max(suggestions[tag], conf * 0.8)
                else:
                    suggestions[tag] = conf * 0.8  # 80% weight for collaborative

            for tag, conf in content_suggestions:
                if tag in suggestions:
                    suggestions[tag] = max(suggestions[tag], conf * 0.7)
                else:
                    suggestions[tag] = conf * 0.7  # 70% weight for content-based

            # Filter by min confidence
            filtered_suggestions = {
                tag: conf for tag, conf in suggestions.items() if conf >= min_confidence
            }

            # Convert to sorted list
            result = [(tag, conf) for tag, conf in filtered_suggestions.items()]
            result.sort(key=lambda x: x[1], reverse=True)

            # Limit to max_suggestions
            return result[:max_suggestions]

        except Exception as e:
            logger.error(f"Error suggesting tags: {e}")
            return []

    async def _get_classifier_suggestions(
        self, file_metadata: dict[str, Any], min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions from the classifier.

        Args:
            file_metadata: Dictionary containing file metadata
            min_confidence: Minimum confidence threshold

        Returns:
            List of (tag_name, confidence) tuples
        """
        try:
            # Use the classifier to predict tags
            return await self.classifier.classify_file(file_metadata, min_confidence)
        except Exception as e:
            logger.error(f"Error getting classifier suggestions: {e}")
            return []

    async def _get_collaborative_suggestions(
        self, file_path: Path, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions based on similar files.

        This is a collaborative filtering approach that suggests tags
        based on what tags are commonly used with files in the same
        directory or with similar extensions.

        Args:
            file_path: Path to the file
            min_confidence: Minimum confidence threshold

        Returns:
            List of (tag_name, confidence) tuples
        """
        try:
            suggestions = []

            # Get suggestions from tagging manager based on location and file type
            tag_suggestions = await self.tagging_manager.get_tag_suggestions(file_path)

            # Convert to the right format
            for suggestion in tag_suggestions:
                if suggestion["score"] >= min_confidence:
                    suggestions.append((suggestion["name"], suggestion["score"]))

            return suggestions
        except Exception as e:
            logger.error(f"Error getting collaborative suggestions: {e}")
            return []

    async def _get_content_based_suggestions(
        self, file_metadata: dict[str, Any], min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions based on file content.

        Args:
            file_metadata: Dictionary containing file metadata
            min_confidence: Minimum confidence threshold

        Returns:
            List of (tag_name, confidence) tuples
        """
        try:
            suggestions = []
            content = file_metadata.get("content", "")

            # Skip if no content
            if not content or not isinstance(content, str):
                return []

            # Get common keywords from content
            keywords = self._extract_keywords(content)

            # Generate suggestions from keywords
            # This is a simplified approach - a more sophisticated approach would
            # use NLP techniques or pre-defined taxonomies
            common_tech_keywords = {
                "python": 0.85,
                "javascript": 0.85,
                "html": 0.85,
                "css": 0.85,
                "react": 0.8,
                "vue": 0.8,
                "angular": 0.8,
                "node": 0.8,
                "database": 0.75,
                "sql": 0.8,
                "nosql": 0.8,
                "mongodb": 0.8,
                "api": 0.75,
                "rest": 0.75,
                "graphql": 0.8,
                "docker": 0.85,
                "kubernetes": 0.85,
                "cloud": 0.7,
                "aws": 0.8,
                "azure": 0.8,
                "gcp": 0.8,
                "machine learning": 0.85,
                "ai": 0.75,
                "data science": 0.85,
                "backend": 0.7,
                "frontend": 0.7,
                "fullstack": 0.7,
                "devops": 0.8,
                "security": 0.75,
                "testing": 0.75,
                "ci/cd": 0.8,
            }

            for keyword in keywords:
                if keyword in common_tech_keywords:
                    confidence = common_tech_keywords[keyword]
                    if confidence >= min_confidence:
                        suggestions.append((keyword, confidence))

            return suggestions

        except Exception as e:
            logger.error(f"Error getting content-based suggestions: {e}")
            return []

    def _extract_keywords(self, content: str) -> set[str]:
        """
        Extract relevant keywords from file content.

        This is a simplified implementation that just looks for tech keywords.
        A real implementation would use NLP techniques like TF-IDF, keyword extraction,
        or entity recognition.

        Args:
            content: File content

        Returns:
            Set of keywords
        """
        # Simple approach: lowercase and split by whitespace
        words = set(content.lower().split())

        # Filter short words and common stop words
        stop_words = {
            "the",
            "and",
            "to",
            "of",
            "a",
            "in",
            "that",
            "it",
            "with",
            "for",
            "as",
            "be",
        }
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}

        return keywords
