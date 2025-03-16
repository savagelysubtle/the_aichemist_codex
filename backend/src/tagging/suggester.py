"""
Tag suggestion system for automated tagging based on file content.

This module provides functionality to suggest tags for files based on
their content, metadata, and similarity to previously tagged files.
"""

import logging
from pathlib import Path

from backend.src.file_reader.file_metadata import FileMetadata

from .classifier import TagClassifier
from .manager import TagManager

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
        tag_manager: TagManager,
        classifier: TagClassifier | None = None,
        model_dir: Path | None = None,
    ):
        """
        Initialize the tag suggester.

        Args:
            tag_manager: TagManager instance for accessing tag data
            classifier: Optional TagClassifier instance
            model_dir: Optional directory for model storage
        """
        self.tag_manager = tag_manager
        # Use a default model directory if none is provided
        default_model_dir = Path.home() / ".aichemist" / "models"
        self.classifier = classifier or TagClassifier(model_dir or default_model_dir)

    async def suggest_tags(
        self,
        file_metadata: FileMetadata,
        min_confidence: float = 0.6,
        max_suggestions: int = 10,
    ) -> list[tuple[str, float]]:
        """
        Suggest tags for a file using multiple strategies.

        Args:
            file_metadata: FileMetadata object
            min_confidence: Minimum confidence threshold for suggestions
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        suggestions = []

        # Get suggestions from classifier
        classifier_suggestions = await self._get_classifier_suggestions(
            file_metadata, min_confidence
        )

        # Get collaborative filtering suggestions
        if file_metadata.path:
            cf_suggestions = await self._get_collaborative_suggestions(
                Path(file_metadata.path), min_confidence
            )
        else:
            cf_suggestions = []

        # Get content-based suggestions
        content_suggestions = await self._get_content_based_suggestions(
            file_metadata, min_confidence
        )

        # Combine and deduplicate suggestions
        all_suggestions = {}

        # Add with different weights based on source
        for tag, conf in classifier_suggestions:
            all_suggestions[tag] = conf * 1.0  # Full weight for ML classifier

        for tag, conf in cf_suggestions:
            if tag in all_suggestions:
                # Take max confidence if already suggested
                all_suggestions[tag] = max(all_suggestions[tag], conf * 0.8)
            else:
                all_suggestions[tag] = (
                    conf * 0.8
                )  # 80% weight for collaborative filtering

        for tag, conf in content_suggestions:
            if tag in all_suggestions:
                all_suggestions[tag] = max(all_suggestions[tag], conf * 0.9)
            else:
                all_suggestions[tag] = conf * 0.9  # 90% weight for content-based

        # Sort by confidence
        suggestions = [
            (tag, conf)
            for tag, conf in all_suggestions.items()
            if conf >= min_confidence
        ]
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:max_suggestions]

    async def _get_classifier_suggestions(
        self, file_metadata: FileMetadata, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions from the classifier.

        Args:
            file_metadata: FileMetadata object
            min_confidence: Minimum confidence threshold

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        try:
            return await self.classifier.classify(
                file_metadata, confidence_threshold=min_confidence
            )
        except Exception as e:
            logger.error(f"Error getting classifier suggestions: {e}")
            return []

    async def _get_collaborative_suggestions(
        self, file_path: Path, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions based on similar files (collaborative filtering).

        Args:
            file_path: Path to the file
            min_confidence: Minimum confidence threshold

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        try:
            # Get suggestions from TagManager
            suggestions = await self.tag_manager.get_tag_suggestions(file_path)

            # Convert to required format
            return [
                (tag["name"], tag["score"])
                for tag in suggestions
                if tag["score"] >= min_confidence
            ]

        except Exception as e:
            logger.error(f"Error getting collaborative suggestions: {e}")
            return []

    async def _get_content_based_suggestions(
        self, file_metadata: FileMetadata, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get tag suggestions based on file content and metadata.

        This method analyzes the content and metadata of the file to
        suggest tags based on keywords, topics, entities, etc.

        Args:
            file_metadata: FileMetadata object
            min_confidence: Minimum confidence threshold

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        suggestions = []

        # Suggest tags based on file extension
        if file_metadata.path:
            path = Path(file_metadata.path)
            if path.suffix:
                extension = path.suffix.lstrip(".")
                suggestions.append((f"ext:{extension}", 0.9))

        # Suggest tags based on mime type
        if file_metadata.mime_type:
            mime_parts = file_metadata.mime_type.split("/")
            if len(mime_parts) == 2:
                main_type, sub_type = mime_parts
                suggestions.append((f"type:{main_type}", 0.9))
                if sub_type != "*":
                    suggestions.append((f"format:{sub_type}", 0.85))

        # Suggest tags based on extracted topics
        if hasattr(file_metadata, "topics") and file_metadata.topics:
            for topic_dict in file_metadata.topics:
                for topic, score in topic_dict.items():
                    if score >= min_confidence:
                        suggestions.append((f"topic:{topic}", float(score)))

        # Suggest tags based on keywords
        if hasattr(file_metadata, "keywords") and file_metadata.keywords:
            for keyword in file_metadata.keywords[:5]:  # Limit to top 5 keywords
                suggestions.append((keyword, 0.8))

        # Suggest tags based on language
        if hasattr(file_metadata, "language") and file_metadata.language:
            suggestions.append((f"lang:{file_metadata.language}", 0.95))

        # Suggest tags based on content type
        if hasattr(file_metadata, "content_type") and file_metadata.content_type:
            suggestions.append((f"content:{file_metadata.content_type}", 0.9))

        # Filter by confidence
        return [(tag, conf) for tag, conf in suggestions if conf >= min_confidence]

    async def analyze_directory(
        self,
        directory: Path,
        recursive: bool = True,
        min_confidence: float = 0.7,
        apply_tags: bool = False,
    ) -> dict[str, list[tuple[str, float]]]:
        """
        Analyze a directory and suggest tags for all files.

        Args:
            directory: Directory path
            recursive: Whether to recursively scan subdirectories
            min_confidence: Minimum confidence threshold
            apply_tags: Whether to apply suggested tags automatically

        Returns:
            Dict[str, List[Tuple[str, float]]]: Mapping of file paths to suggested tags
        """
        from backend.src.file_reader.file_reader import FileReader

        results = {}

        # Create a file reader
        file_reader = FileReader()

        # Scan the directory
        pattern = "**/*" if recursive else "*"
        files = list(directory.glob(pattern))

        # Process each file
        for file_path in files:
            if file_path.is_file():
                try:
                    # Process the file to get metadata
                    metadata = await file_reader.process_file(file_path)

                    # Get tag suggestions
                    suggestions = await self.suggest_tags(
                        metadata, min_confidence=min_confidence
                    )

                    if suggestions:
                        results[str(file_path)] = suggestions

                        # Apply tags if requested
                        if apply_tags and suggestions:
                            await self.tag_manager.add_file_tags(
                                file_path=file_path, tags=suggestions, source="auto"
                            )

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

        return results

    async def batch_suggest_tags(
        self,
        file_paths: list[Path],
        min_confidence: float = 0.7,
        apply_tags: bool = False,
    ) -> dict[str, list[tuple[str, float]]]:
        """
        Suggest tags for multiple files in batch.

        Args:
            file_paths: List of file paths
            min_confidence: Minimum confidence threshold
            apply_tags: Whether to apply suggested tags automatically

        Returns:
            Dict[str, List[Tuple[str, float]]]: Mapping of file paths to suggested tags
        """
        from backend.src.file_reader.file_reader import FileReader

        results = {}

        # Create a file reader
        file_reader = FileReader()

        # Process each file
        for file_path in file_paths:
            if file_path.is_file():
                try:
                    # Process the file to get metadata
                    metadata = await file_reader.process_file(file_path)

                    # Get tag suggestions
                    suggestions = await self.suggest_tags(
                        metadata, min_confidence=min_confidence
                    )

                    if suggestions:
                        results[str(file_path)] = suggestions

                        # Apply tags if requested
                        if apply_tags and suggestions:
                            await self.tag_manager.add_file_tags(
                                file_path=file_path, tags=suggestions, source="auto"
                            )

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

        return results
